from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import hashlib
from itertools import repeat
import json
from pathlib import Path
import shutil
from threading import Barrier
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

from azure.ai.projects.models import EvaluatorVersion
from azure.core.exceptions import HttpResponseError
from openai import APIError, OpenAI
from openai.types.evals.run_create_response import RunCreateResponse
from openai.types.evals.run_retrieve_response import ResultCounts, RunRetrieveResponse
from openai.types.evals.runs.output_item_list_response import OutputItemListResponse, Result

from lab import calibration, managed_eval
from lab.config import Config, LabError
from lab.files import ROOT as REPOSITORY_ROOT, read_jsonl, sha256_file, write_jsonl
from lab.preflight import save_json


class ManagedEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.root = Path("artifacts") / f"test-managed-eval-{uuid4().hex}"
        self.root.mkdir(parents=True)
        self.addCleanup(shutil.rmtree, self.root)
        self.config = Config(
            subscription_id="00000000-0000-0000-0000-000000000001",
            tenant_id="00000000-0000-0000-0000-000000000002",
            expected_user="fixture@example.invalid",
            location="northcentralus",
            resource_group="fixture-rg", account="fixture-account", project="fixture-project",
            project_endpoint="https://fixture-account.services.ai.azure.com/api/projects/fixture-project",
            openai_endpoint="https://fixture-account.openai.azure.com",
            search_service="fixture-search", search_endpoint="https://fixture-search.search.windows.net",
            model="fixture-agent-model", judge="fixture-judge", optimizer="fixture-optimizer",
            prefix="fixture",
        )
        self.cases = [
            {
                "id": f"case-{letter}",
                "group_id": f"group-{letter}",
                "split": "dev",
                "query": f"질문 {letter}?",
                "context": f"고정 참조 정책 {letter}",
                "ground_truth": self.response_json(f"참조 답변 {letter}"),
                "expected_route": "answer", "required_citations": ["policy-fixture"], "tags": [],
            }
            for letter in ("a", "b", "c")
        ]
        self.records = [
            {
                "id": case["id"],
                "raw_output": "" if case["id"] == "case-c" else self.response_json(f"캡처 응답 {case['id']}"),
                "retrieved_context": f"실제 MCP 원문 {case['id']}",
                "error": "fixture capture error" if case["id"] == "case-c" else None,
            }
            for case in self.cases
        ]
        self.rows = [
            {
                "case_id": case["id"], "query": case["query"],
                "response": json.loads(record["raw_output"])["answer"], "context": case["context"],
                "ground_truth": json.loads(case["ground_truth"])["answer"],
                "retrieved_context": record["retrieved_context"],
            }
            for case, record in zip(self.cases, self.records, strict=True) if record["error"] is None
        ]
        self.dataset_path = self.root / "data/splits/dev.jsonl"
        write_jsonl(self.dataset_path, self.cases)
        save_json(self.root / "data/knowledge/documents.json", [{
            "id": "policy-fixture", "title": "fixture", "content": "고정 정책 본문",
            "effective_date": "2026-09-01",
        }])
        self.directory = self.root / "runs/local-run"
        self.metadata = self.seed_run("local-run")
        self.versions = [
            {"name": "builtin.groundedness", "version": "7", "id": "fixture-groundedness-version"},
            {"name": "builtin.relevance", "version": "3", "id": "fixture-relevance-version"},
        ]
        self.deployment = {
            "id": f"{self.config.account_id}/deployments/{self.config.judge}",
            "name": self.config.judge,
            "properties": {
                "provisioningState": "Succeeded",
                "model": {"format": "OpenAI", "name": "fixture-backing-model", "version": "2026-08-01"},
                "versionUpgradeOption": "OnceNewDefaultVersionAvailable",
            },
            "sku": {"name": "GlobalStandard", "capacity": 1},
            "etag": "fixture-volatile-etag",
        }
        self.credential = MagicMock()
        self.credential.__enter__.return_value = self.credential
        self.project = MagicMock()
        self.project.__enter__.return_value = self.project
        self.project.beta.evaluators.list.return_value = self.versions
        self.client = MagicMock()
        self.client.__enter__.return_value = self.client
        self.project.get_openai_client.return_value = self.client
        self.client.evals.create.return_value = {"id": "eval-fixture", "object": "eval"}
        self.client.evals.runs.create.return_value = RunCreateResponse.model_construct(
            id="run-fixture", eval_id="eval-fixture", status="queued",
            report_url="https://example.invalid/evaluation-report",
        )
        self.client.evals.runs.retrieve.return_value = self.run_response()
        self.items = [
            self.output_item(self.rows[1], groundedness=2, relevance=3, wrapped=True),
            self.output_item(self.rows[0], groundedness=4, relevance=5),
        ]
        self.client.evals.runs.output_items.list.side_effect = lambda **kwargs: iter(self.items)
        self.auth = self.start_patch("lab.managed_eval.credential_for", return_value=self.credential)
        self.management = self.start_patch("lab.managed_eval.az_json", return_value=[self.deployment])
        self.factory = self.start_patch("lab.managed_eval.AIProjectClient", return_value=self.project)
        self.start_patch("lab.managed_eval.ROOT", self.root)
        self.start_patch("lab.files.artifacts_dir", return_value=self.root)

    def start_patch(self, target, *args, **kwargs):
        patcher = patch(target, *args, **kwargs)
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    @staticmethod
    def response_json(answer, **fields):
        response = {
            "answer": answer, "route": "answer",
            "citations": ["policy-fixture"], "needs_human": False,
        }
        response.update(fields)
        return json.dumps(response, ensure_ascii=False)

    def seed_run(self, run_id, *, stage="baseline", split="dev"):
        directory = self.root / "runs" / run_id
        metadata = {
            "run_id": run_id, "source_split": split, "split": split, "stage": stage,
            "model_deployment": self.config.model,
            "prompt_sha256": hashlib.sha256(stage.encode()).hexdigest(),
            "knowledge_sha256": hashlib.sha256(b"").hexdigest(),
            "dataset_sha256": sha256_file(self.dataset_path),
            "row_ids": [case["id"] for case in self.cases],
            "project_endpoint": self.config.project_endpoint,
            "status": "completed_with_errors" if any(record["error"] for record in self.records) else "completed",
            "judge": None,
            "parameters": {"max_output_tokens": 4096},
        }
        save_json(directory / "metadata.json", metadata)
        write_jsonl(directory / "outputs.jsonl", self.records)
        write_jsonl(directory / "foundry-eval.jsonl", self.rows)
        return metadata

    @staticmethod
    def run_response(status="completed", *, counts=None, error=None):
        return RunRetrieveResponse.model_construct(
            id="run-fixture", eval_id="eval-fixture", status=status,
            report_url="https://example.invalid/evaluation-report", error=error,
            result_counts=counts or ResultCounts(total=2, passed=1, failed=1, errored=0),
        )

    @staticmethod
    def output_item(row, *, groundedness=4, relevance=4, wrapped=False):
        results = []
        for metric, score in (("groundedness", groundedness), ("relevance", relevance)):
            results.append(Result(
                name=metric.title(), metric=metric, type="azure_ai_evaluator",
                score=score, passed=score >= 4, threshold=4,
                label="pass" if score >= 4 else "fail", reason=f"실제 {metric} 평가 이유 (mock)",
            ))
        return OutputItemListResponse.model_construct(
            id=f"output-{row['case_id']}", eval_id="eval-fixture", run_id="run-fixture",
            datasource_item={"item": deepcopy(row)} if wrapped else deepcopy(row),
            datasource_item_id=999, status="pass" if min(groundedness, relevance) >= 4 else "fail",
            results=results, sample=None,
        )

    def read(self, name):
        return json.loads((self.directory / name).read_text(encoding="utf-8"))

    def submit(self):
        return managed_eval.submit_evaluation(self.config, "local-run")

    def collect(self):
        return managed_eval.collect_evaluation(self.config, "local-run")

    def export_with_parent(self):
        from lab.batch import export_evaluation

        with patch("lab.batch.ROOT", self.root):
            export_evaluation(self.directory, self.cases, self.records)
        self.rows = read_jsonl(self.directory / "foundry-eval.jsonl")
        self.items = [self.output_item(row) for row in reversed(self.rows)]
        self.client.evals.runs.retrieve.return_value = self.run_response(
            counts=ResultCounts(total=len(self.rows), passed=len(self.rows), failed=0, errored=0),
        )

    def assert_no_paid_requests(self):
        self.client.evals.create.assert_not_called()
        self.client.evals.runs.create.assert_not_called()
        self.client.responses.create.assert_not_called()

    def prepare_business_judge(self):
        shutil.copytree(REPOSITORY_ROOT / "config/evaluators", self.root / "config/evaluators")
        self.start_patch("lab.calibration.ROOT", self.root)
        self.start_patch("lab.batch.ROOT", self.root)
        auth = self.start_patch("lab.calibration.credential_for", return_value=self.credential)
        self.start_patch("lab.calibration.AIProjectClient", return_value=self.project)
        self.start_patch("lab.calibration.model_snapshot", return_value={
            "deployment": self.config.judge, "model": {"name": "unit-only-model", "version": "1"},
        })

        def create(**kwargs):
            value = (
                {"policy_correctness": 5, "relevance": 5, "critical_failure": False, "reason": "unit-only mock"}
                if kwargs["text"]["format"]["name"] == "atlas_policy_v1"
                else {"groundedness": 5, "reason": "unit-only mock"}
            )
            identifier = f"unit-judge-{self.client.responses.create.call_count}"
            return SimpleNamespace(
                id=identifier, output_text=json.dumps(value),
                model_dump=lambda **kwargs: {"id": identifier, "status": "completed", "output": []},
            )

        self.client.responses.create.side_effect = create
        return auth

    def test_submit_strips_reference_labels_and_maps_only_actual_retrieval(self):
        original = self.read("metadata.json")
        result = self.submit()
        definition = self.client.evals.create.call_args.kwargs
        source = self.client.evals.runs.create.call_args.kwargs["data_source"]
        self.assertEqual(source["type"], "jsonl")
        self.assertEqual(source["source"]["type"], "file_content")
        self.assertEqual(source["source"]["content"], [
            {"item": {key: row[key] for key in managed_eval.SERVICE_FIELDS}} for row in self.rows
        ])
        self.assertEqual(source["source"]["content"][0]["item"]["response"], "캡처 응답 case-a")
        self.assertNotIn("ground_truth", source["source"]["content"][0]["item"])
        self.assertNotIn("context", source["source"]["content"][0]["item"])
        self.assertNotIn("참조 답변 a", json.dumps(source, ensure_ascii=False))
        self.assertNotIn("case-c", json.dumps(source))
        self.assertNotIn("target", source)
        self.assertNotIn("input_messages", source)
        self.assertFalse(definition["data_source_config"]["include_sample_schema"])
        self.assertEqual(set(definition["data_source_config"]["item_schema"]["required"]), set(managed_eval.SERVICE_FIELDS))
        criteria = {item["name"]: item for item in definition["testing_criteria"]}
        self.assertEqual(criteria["groundedness"]["data_mapping"], {
            "query": "{{item.query}}", "response": "{{item.response}}", "context": "{{item.retrieved_context}}",
        })
        self.assertEqual(criteria["relevance"]["data_mapping"], {
            "query": "{{item.query}}", "response": "{{item.response}}",
        })
        for metric, evaluator_version in (("groundedness", "7"), ("relevance", "3")):
            self.assertEqual(criteria[metric]["evaluator_name"], f"builtin.{metric}")
            self.assertEqual(criteria[metric]["evaluator_version"], evaluator_version)
            self.assertEqual(criteria[metric]["initialization_parameters"], {
                "deployment_name": self.config.judge, "threshold": 4,
            })
        self.assertNotIn("sample.", json.dumps(definition))
        self.client.responses.create.assert_not_called()
        self.assertEqual(self.project.agents.mock_calls, [])
        self.project.datasets.upload_file.assert_not_called()
        self.client.evals.runs.retrieve.assert_not_called()
        self.project.get_openai_client.assert_called_once_with(max_retries=0, timeout=120.0)
        self.auth.assert_called_once_with(self.config)
        self.management.assert_called_once_with([
            "cognitiveservices", "account", "deployment", "list",
            "--subscription", self.config.subscription_id,
            "--resource-group", self.config.resource_group, "--name", self.config.account,
        ])
        self.factory.assert_called_once_with(endpoint=self.config.project_endpoint, credential=self.credential)
        self.assertEqual(result["status"], "queued")
        self.assertIn("evaluate collect --run-id local-run", result["next_step"])
        updated = self.read("metadata.json")
        self.assertEqual(original, {
            key: value for key, value in updated.items() if key != managed_eval.MANAGED_METADATA
        })
        self.assertEqual(updated[managed_eval.MANAGED_METADATA], {
            "eval_id": result["eval_id"], "run_id": result["run_id"], "report_url": result["report_url"],
        })
        self.assertIsNone(updated["judge"])

    def test_pinned_openai_sdk_serializes_azure_extensions_and_inline_rows(self):
        self.submit()
        definition = self.client.evals.create.call_args.kwargs
        request = self.client.evals.runs.create.call_args.kwargs
        with OpenAI(api_key="mock-only-not-a-credential", base_url="https://example.invalid") as client:
            with patch.object(client.evals, "_post") as post:
                client.evals.create(**definition)
                self.assertEqual(post.call_args.kwargs["body"]["testing_criteria"], definition["testing_criteria"])
                self.assertFalse(post.call_args.kwargs["body"]["data_source_config"]["include_sample_schema"])
            with patch.object(client.evals.runs, "_post") as post:
                client.evals.runs.create(**request)
                body = post.call_args.kwargs["body"]
                self.assertEqual(body["data_source"], request["data_source"])
                self.assertNotIn("azure_ai_agent", json.dumps(body))
        self.assertEqual(self.read(managed_eval.CONTRACT)["sdk_versions"], {
            "azure-ai-projects": "2.7.0", "openai": "3.20.0",
        })

    def test_cli_rejects_paid_submit_without_confirmation(self):
        from lab.cli import execute, parser

        args = parser().parse_args(["evaluate", "submit", "--run-id", "local-run"])
        with patch("lab.cli.load_config", return_value=self.config), patch(
            "lab.managed_eval.submit_evaluation"
        ) as submit:
            with self.assertRaisesRegex(LabError, "--confirm"):
                execute(args)
            submit.assert_not_called()
        self.assert_no_paid_requests()

    def test_ids_are_persisted_before_next_operation_and_no_submit_polling(self):
        run = self.client.evals.runs.create.return_value

        def create_run(**kwargs):
            ledger = self.read(managed_eval.LEDGER)
            self.assertEqual(ledger["eval_id"], "eval-fixture")
            self.assertIsNone(ledger["run_id"])
            registered = self.read("metadata.json")[managed_eval.MANAGED_METADATA]
            self.assertEqual(registered["eval_id"], "eval-fixture")
            self.assertIsNone(registered["run_id"])
            return run

        self.client.evals.runs.create.side_effect = create_run
        self.submit()
        ledger = self.read(managed_eval.LEDGER)
        self.assertEqual(ledger["run_id"], "run-fixture")
        self.assertEqual(ledger["report_url"], run.report_url)
        self.assertEqual(self.read("metadata.json")[managed_eval.MANAGED_METADATA], {
            "eval_id": "eval-fixture", "run_id": "run-fixture", "report_url": run.report_url,
        })
        self.client.evals.runs.retrieve.assert_not_called()

    def test_duplicate_submit_is_blocked_before_authentication(self):
        self.submit()
        self.auth.reset_mock()
        with self.assertRaisesRegex(LabError, "중복"):
            self.submit()
        self.auth.assert_not_called()
        self.assertEqual(self.client.evals.create.call_count, 1)
        self.assertEqual(self.client.evals.runs.create.call_count, 1)

    def test_legacy_unfinished_business_judge_blocks_switching_to_managed_submission(self):
        save_json(self.directory / "business-judge/raw/case-a.json", {
            "id": "case-a", "requests": {"policy": {"status": "submitting", "response_id": None}},
        })
        with self.assertRaisesRegex(LabError, "business-judge|Judge attempt"):
            self.submit()
        self.auth.assert_not_called()
        self.assert_no_paid_requests()

    def test_interrupted_unknown_business_post_retains_shared_claim_and_blocks_managed(self):
        self.prepare_business_judge()
        self.client.responses.create.side_effect = KeyboardInterrupt("unit-only interruption after POST intent")
        with self.assertRaises(KeyboardInterrupt):
            calibration.score_captured_run(self.config, "local-run", confirm=True)
        self.assertFalse((self.directory / "judge-scores.json").exists())
        self.assertIsNone(self.read("metadata.json")["judge"])
        saved = self.read("business-judge/raw/case-a.json")
        self.assertEqual(saved["requests"]["policy"]["status"], "submitting")
        self.assertIsNone(saved["requests"]["policy"]["response_id"])
        claim_path = self.directory / calibration.JUDGE_ATTEMPT_CLAIM
        original_claim = claim_path.read_bytes()
        claim = self.read(calibration.JUDGE_ATTEMPT_CLAIM)
        self.assertEqual(claim["evaluation_path"], "business-judge")
        self.assertEqual(claim["run_directory"], str(self.directory.resolve()))
        self.assertEqual(claim["evaluator_contract_sha256"], calibration.digest(self.read("business-judge/contract.json")))
        with self.assertRaisesRegex(LabError, "Judge attempt"):
            self.submit()
        with self.assertRaisesRegex(LabError, "Judge attempt"):
            calibration.score_captured_run(self.config, "local-run", confirm=True)
        self.assertEqual(claim_path.read_bytes(), original_claim)
        self.auth.assert_not_called()
        self.management.assert_not_called()
        self.client.responses.create.assert_called_once()
        self.client.evals.create.assert_not_called()
        self.client.evals.runs.create.assert_not_called()

    def test_unknown_managed_post_blocks_business_path_without_claim_takeover(self):
        business_auth = self.prepare_business_judge()
        self.client.evals.runs.create.side_effect = APIError("unit-only unknown outcome", request=Mock(), body=None)
        with self.assertLogs("lab.managed_eval", level="ERROR"), self.assertRaises(APIError):
            self.submit()
        claim_path = self.directory / calibration.JUDGE_ATTEMPT_CLAIM
        original_claim = claim_path.read_bytes()
        self.assertEqual(self.read(calibration.JUDGE_ATTEMPT_CLAIM)["evaluation_path"], "managed-eval")
        with self.assertRaisesRegex(LabError, "Judge attempt"):
            calibration.score_captured_run(self.config, "local-run", confirm=True)
        business_auth.assert_not_called()
        self.client.responses.create.assert_not_called()
        self.assertEqual(claim_path.read_bytes(), original_claim)

    def test_concurrent_managed_and_business_paths_allow_only_one_paid_judge_attempt(self):
        self.prepare_business_judge()
        barrier = Barrier(2)
        original_claim = calibration.claim_judge_attempt

        def synchronized_claim(*args, **kwargs):
            barrier.wait(timeout=10)
            return original_claim(*args, **kwargs)

        self.start_patch("lab.calibration.claim_judge_attempt", side_effect=synchronized_claim)
        self.start_patch("lab.managed_eval.claim_judge_attempt", side_effect=synchronized_claim)

        def submit(path):
            try:
                result = (
                    calibration.score_captured_run(self.config, "local-run", confirm=True)
                    if path == "business-judge" else self.submit()
                )
                return path, result, None
            except LabError as exc:
                return path, None, str(exc)

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(submit, path) for path in ("business-judge", "managed-eval")]
            results = [future.result(timeout=20) for future in futures]
        winners = [result for result in results if result[2] is None]
        self.assertEqual(len(winners), 1, results)
        winner = winners[0][0]
        claim = self.read(calibration.JUDGE_ATTEMPT_CLAIM)
        self.assertEqual(claim["evaluation_path"], winner)
        self.assertEqual(claim["evaluator_contract_sha256"], calibration.digest(claim["evaluator_contract"]))
        self.assertEqual(claim["outputs_sha256"], sha256_file(self.directory / "outputs.jsonl"))
        if winner == "business-judge":
            self.assertEqual(self.client.responses.create.call_count, 4)
            self.client.evals.create.assert_not_called()
            self.client.evals.runs.create.assert_not_called()
            self.assertFalse((self.directory / managed_eval.LEDGER).exists())
        else:
            self.client.evals.create.assert_called_once()
            self.client.evals.runs.create.assert_called_once()
            self.client.responses.create.assert_not_called()
            self.assertFalse((self.directory / "business-judge").exists())
            self.assertEqual(self.collect()["collection_status"], "collected")

    def test_shared_claim_never_prevents_managed_read_only_collection_or_legacy_collection(self):
        self.submit()
        claim_path = self.directory / calibration.JUDGE_ATTEMPT_CLAIM
        original_claim = claim_path.read_bytes()
        self.client.evals.runs.retrieve.return_value = self.run_response(status="queued")
        self.assertEqual(self.collect()["status"], "queued")
        self.assertEqual(claim_path.read_bytes(), original_claim)
        self.client.evals.runs.retrieve.return_value = self.run_response()
        self.assertEqual(self.collect()["collection_status"], "collected")
        self.assertEqual(claim_path.read_bytes(), original_claim)
        claim_path.unlink()
        self.assertEqual(self.collect()["collection_status"], "collected")
        self.assertFalse(claim_path.exists())
        self.client.evals.create.assert_called_once()
        self.client.evals.runs.create.assert_called_once()
        self.client.responses.create.assert_not_called()

    def test_existing_claim_cannot_be_overwritten_or_collected_under_another_path(self):
        self.submit()
        path = self.directory / calibration.JUDGE_ATTEMPT_CLAIM
        original = path.read_bytes()
        for evaluation_path in ("business-judge", "managed-eval"):
            with self.subTest(path=evaluation_path), self.assertRaisesRegex(LabError, "Judge attempt"):
                calibration.claim_judge_attempt(
                    self.directory, "local-run", project_endpoint=self.config.project_endpoint,
                    evaluation_path=evaluation_path, contract={"version": "replacement"},
                )
        with self.assertRaisesRegex(LabError, "take over"):
            calibration.validate_judge_claim(
                self.directory, "local-run", project_endpoint=self.config.project_endpoint,
                evaluation_path="business-judge", contract=self.read(managed_eval.CONTRACT),
            )
        self.assertEqual(path.read_bytes(), original)

    def test_observed_drift_rejects_managed_judgment_before_auth_even_if_marked_completed(self):
        metadata = self.read("metadata.json")
        metadata.update(model_snapshot={"version": "A"}, model_snapshot_after={"version": "B"})
        save_json(self.directory / "metadata.json", metadata)
        with self.assertRaisesRegex(LabError, "observed model drift"):
            self.submit()
        self.auth.assert_not_called()
        self.assert_no_paid_requests()

    def test_metadata_ids_prevent_resubmission_when_the_ledger_is_missing(self):
        self.submit()
        (self.directory / managed_eval.LEDGER).unlink()
        self.auth.reset_mock()
        with self.assertRaisesRegex(LabError, "기존 평가 기록"):
            self.submit()
        self.auth.assert_not_called()
        self.assertEqual(self.client.evals.create.call_count, 1)
        self.assertEqual(self.client.evals.runs.create.call_count, 1)

    def test_run_submission_sdk_error_preserves_orphan_and_propagates(self):
        error = APIError("fixture submission failure", request=Mock(), body=None)
        self.client.evals.runs.create.side_effect = error
        with self.assertLogs("lab.managed_eval", level="ERROR"), self.assertRaises(APIError) as caught:
            self.submit()
        self.assertIs(caught.exception, error)
        ledger = self.read(managed_eval.LEDGER)
        self.assertEqual(ledger["eval_id"], "eval-fixture")
        self.assertIsNone(ledger["run_id"])
        self.assertEqual(ledger["status"], "creating_run_unknown")
        self.assertEqual(self.read("metadata.json")[managed_eval.MANAGED_METADATA], {
            "eval_id": "eval-fixture", "run_id": None, "report_url": None,
        })
        self.assertIn("기록을 삭제하거나 재제출하지", error.__notes__[0])
        with self.assertRaisesRegex(LabError, "eval-fixture"):
            self.submit()
        with self.assertRaisesRegex(LabError, "불완전"):
            self.collect()
        self.client.evals.runs.retrieve.assert_not_called()

    def test_eval_submission_uncertainty_never_automatically_retries(self):
        self.client.evals.create.side_effect = APIError("fixture timeout", request=Mock(), body=None)
        with self.assertLogs("lab.managed_eval", level="ERROR"), self.assertRaises(APIError):
            self.submit()
        self.assertEqual(self.read(managed_eval.LEDGER)["status"], "creating_evaluation_unknown")
        with self.assertRaises(LabError):
            self.submit()
        self.assertEqual(self.client.evals.create.call_count, 1)
        self.client.evals.runs.create.assert_not_called()

    def test_non_sdk_errors_are_not_broadly_caught(self):
        self.client.evals.runs.create.side_effect = RuntimeError("fixture coding error")
        with self.assertRaisesRegex(RuntimeError, "coding error"):
            self.submit()
        self.assertEqual(self.read(managed_eval.LEDGER)["eval_id"], "eval-fixture")

    def test_missing_created_id_preserves_recovery_record(self):
        self.client.evals.create.return_value = {"object": "eval"}
        with self.assertRaisesRegex(LabError, "evaluation.id"):
            self.submit()
        self.assertTrue((self.directory / managed_eval.LEDGER).is_file())
        self.client.evals.runs.create.assert_not_called()

    def test_failed_submit_response_keeps_ids_and_report(self):
        self.client.evals.runs.create.return_value = self.run_response(
            "failed", error={"code": "fixture", "message": "fixture service failure"},
        )
        with self.assertRaisesRegex(LabError, "failed"):
            self.submit()
        ledger = self.read(managed_eval.LEDGER)
        self.assertEqual(ledger["run_id"], "run-fixture")
        self.assertEqual(ledger["eval_id"], "eval-fixture")
        self.assertEqual(ledger["status"], "failed")
        self.assertIsNotNone(ledger["report_url"])

    def test_ambiguous_or_invalid_catalog_versions_fail_before_any_paid_request(self):
        invalid_catalogs = [
            [*self.versions, self.versions[0]],
            [{**self.versions[0], "version": 7}, self.versions[1]],
            [{**self.versions[0], "version": ""}, self.versions[1]],
            ["invalid catalog item"],
        ]
        for catalog in invalid_catalogs:
            with self.subTest(catalog=catalog):
                self.project.beta.evaluators.list.return_value = catalog
                with self.assertRaises(LabError):
                    self.submit()
                self.assert_no_paid_requests()

    def test_absent_catalog_versions_stay_explicitly_service_managed_and_unpinned(self):
        catalogs = [
            [], self.versions[:1],
            [{**self.versions[0], "version": None}, self.versions[1]],
            [{**self.versions[0], "version": "latest"}, self.versions[1]],
        ]
        for index, catalog in enumerate(catalogs):
            with self.subTest(catalog=catalog):
                run_id = f"unreported-version-{index}"
                self.seed_run(run_id)
                self.project.beta.evaluators.list.return_value = catalog
                managed_eval.submit_evaluation(self.config, run_id)
                managed_eval.collect_evaluation(self.config, run_id)
                directory = self.root / "runs" / run_id
                metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
                judge = metadata["judge"]
                self.assertEqual(judge["version"], "service-managed/unpinned")
                self.assertIs(judge["service_version_pinned"], False)
                self.assertIs(judge["provenance"]["service_version_pinned"], False)
                self.assertIn("private managed rubric/runtime", judge["provenance"]["limitation"])
                self.assertIn("Canonical public evaluator configuration", judge["provenance"]["hash_scope"])
                for criterion in judge["settings"]["testing_criteria"]:
                    entry = judge["settings"]["evaluators"][criterion["evaluator_name"]]
                    if entry["version"] is None:
                        self.assertNotIn("evaluator_version", criterion)
                        self.assertEqual(entry["version_source"], "not_exposed")
                    else:
                        self.assertEqual(criterion["evaluator_version"], entry["reported_version"])

    def test_runtime_reported_version_does_not_become_an_invented_requested_pin(self):
        self.project.beta.evaluators.list.return_value = []
        self.submit()
        self.items = [item.model_dump(mode="json", exclude_unset=True) for item in self.items]
        for item in self.items:
            for result in item["results"]:
                result["evaluator_version"] = "fixture-service-reported-version"
        self.collect()
        judge = self.read("metadata.json")["judge"]
        self.assertEqual(judge["version"], "service-managed/unpinned")
        self.assertIs(judge["service_version_pinned"], False)
        self.assertTrue(all(entry["version"] is None for entry in judge["settings"]["evaluators"].values()))
        self.assertIn(
            "fixture-service-reported-version",
            json.dumps(self.read("managed-eval-output-items.json")),
        )

    def test_catalog_permission_errors_propagate_instead_of_fabricating_versions(self):
        self.project.beta.evaluators.list.side_effect = HttpResponseError("fixture catalog permission denied")
        with self.assertRaisesRegex(HttpResponseError, "permission denied"):
            self.submit()
        self.assert_no_paid_requests()

    def test_judge_model_snapshot_is_read_before_any_submission_and_not_refreshed_on_collect(self):
        def lookup(args):
            self.auth.assert_called_once_with(self.config)
            self.factory.assert_not_called()
            self.assert_no_paid_requests()
            return [self.deployment]

        self.management.side_effect = lookup
        self.submit()
        self.management.side_effect = AssertionError("collect must use the saved submission-time snapshot")
        self.collect()
        judge = self.read("metadata.json")["judge"]
        snapshot = judge["settings"]["judge_deployment"]
        self.assertEqual(snapshot["model"], self.deployment["properties"]["model"])
        self.assertEqual(snapshot["resource_id"], self.deployment["id"])
        self.assertEqual(snapshot["version_upgrade_option"], "OnceNewDefaultVersionAvailable")
        self.assertNotIn("etag", snapshot)
        self.assertEqual(judge["version"], "service-managed/unpinned")
        self.assertNotEqual(judge["version"], judge["settings"]["sdk_versions"]["azure-ai-projects"])
        self.assertNotEqual(judge["version"], judge["settings"]["contract_version"])
        self.assertIs(judge["service_version_pinned"], False)
        self.assertIn("submission-time", judge["provenance"]["limitation"])
        self.assertIn("auto-upgrades", judge["provenance"]["limitation"])
        self.assertEqual(self.management.call_count, 1)

    def test_missing_deployment_model_version_stays_unknown_not_an_sdk_version(self):
        del self.deployment["properties"]["model"]["version"]
        self.submit()
        self.collect()
        judge = self.read("metadata.json")["judge"]
        self.assertIsNone(judge["settings"]["judge_deployment"]["model"]["version"])
        self.assertEqual(judge["version"], "service-managed/unpinned")
        self.assertIs(judge["service_version_pinned"], False)

    def test_wrong_missing_or_unready_judge_deployment_blocks_paid_submission(self):
        responses = [
            {}, [], [self.deployment, self.deployment],
            [{**self.deployment, "id": "/subscriptions/another/deployment"}],
            [{**self.deployment, "properties": {"provisioningState": "Updating"}}],
            [{**self.deployment, "properties": {"provisioningState": "Succeeded", "model": {}}}],
        ]
        for response in responses:
            with self.subTest(response=response):
                self.management.return_value = response
                with self.assertRaises(LabError):
                    self.submit()
                self.assert_no_paid_requests()
        self.factory.assert_not_called()

    def test_management_read_failure_is_not_bypassed_with_a_fabricated_model(self):
        self.management.side_effect = LabError("fixture deployment read denied")
        with self.assertRaisesRegex(LabError, "read denied"):
            self.submit()
        self.assert_no_paid_requests()
        self.factory.assert_not_called()

    def test_real_azure_catalog_models_with_nested_definitions_are_supported(self):
        self.project.beta.evaluators.list.return_value = [
            EvaluatorVersion({
                **item,
                "created_at": "2026-09-29T00:00:00Z",
                "definition": {
                    "type": "prompt", "data_schema": {"type": "object"},
                    "prompt_text": "fixture-private-rubric-not-to-be-hashed",
                },
            })
            for item in self.versions
        ]
        self.submit()
        contract = self.read(managed_eval.CONTRACT)
        self.assertEqual(contract["evaluators"]["builtin.groundedness"]["version"], "7")
        self.assertNotIn("created_at", json.dumps(contract))
        self.assertNotIn("fixture-private-rubric-not-to-be-hashed", json.dumps(contract))
        self.assertNotIn("definition", contract["evaluators"]["builtin.groundedness"])

    def test_catalog_iteration_is_bounded(self):
        self.project.beta.evaluators.list.return_value = repeat({"name": "unrelated"})
        with self.assertRaisesRegex(LabError, "500"):
            self.submit()
        self.assert_no_paid_requests()

    def test_invalid_capture_metadata_is_rejected_locally(self):
        changes = [
            {"status": "running"}, {"status": {}}, {"source_split": "../test"},
            {"source_split": {}}, {"split": "train"}, {"run_id": "another-run"},
            {"project_endpoint": "https://another.invalid"},
            {"row_ids": ["case-a", "case-a"]}, {"row_ids": ["case-a"]},
            {"row_ids": [None]}, {"dataset_sha256": "0" * 64},
            {"knowledge_sha256": "not-a-hash"}, {"model_deployment": None},
        ]
        for change in changes:
            with self.subTest(change=change):
                save_json(self.directory / "metadata.json", {**self.metadata, **change})
                with self.assertRaises(LabError):
                    self.submit()
                self.auth.assert_not_called()
                self.assert_no_paid_requests()

    def test_duplicate_json_keys_and_nonfinite_input_fail_closed(self):
        original = (self.directory / "metadata.json").read_text(encoding="utf-8")
        for invalid in (
            original.replace('"stage": "baseline"', '"stage": "other", "stage": "baseline"'),
            original.replace('"stage": "baseline"', '"stage": NaN'),
        ):
            with self.subTest(invalid=invalid[:40]):
                (self.directory / "metadata.json").write_text(invalid, encoding="utf-8")
                with self.assertRaisesRegex(LabError, "JSON"):
                    self.submit()
        self.auth.assert_not_called()

    def test_export_duplicate_missing_unknown_and_failed_case_ids_rejected(self):
        for rows in (
            [self.rows[0], self.rows[0]], self.rows[:1],
            [self.rows[0], {**self.rows[1], "case_id": "unknown"}],
            [*self.rows, {**self.rows[0], "case_id": "case-c"}],
        ):
            with self.subTest(ids=[row["case_id"] for row in rows]):
                write_jsonl(self.directory / "foundry-eval.jsonl", rows)
                with self.assertRaises(LabError):
                    self.submit()
                self.auth.assert_not_called()

    def test_policy_reference_cannot_be_replaced_with_mcp_output(self):
        rows = deepcopy(self.rows)
        rows[0]["context"] = rows[0]["retrieved_context"]
        write_jsonl(self.directory / "foundry-eval.jsonl", rows)
        with self.assertRaisesRegex(LabError, "고정 참조"):
            self.submit()
        self.assert_no_paid_requests()

    def test_no_capture_failures_are_silently_removed(self):
        for records in (self.records[:2], [*self.records, self.records[0]]):
            with self.subTest(ids=[record["id"] for record in records]):
                write_jsonl(self.directory / "outputs.jsonl", records)
                with self.assertRaises(LabError):
                    self.submit()
                self.auth.assert_not_called()

    def test_all_capture_errors_block_submission(self):
        records = [{**record, "error": "fixture failure"} for record in self.records]
        write_jsonl(self.directory / "outputs.jsonl", records)
        with self.assertRaisesRegex(LabError, "성공적으로 캡처"):
            self.submit()
        self.assert_no_paid_requests()

    def test_schema_errors_in_export_are_not_repaired(self):
        invalid_rows = [
            {key: value for key, value in self.rows[0].items() if key != "query"},
            {**self.rows[0], "response": None},
            {**self.rows[0], "unexpected": "field"},
            {**self.rows[0], "response": "newly generated response, not the capture"},
        ]
        for invalid in invalid_rows:
            with self.subTest(invalid=invalid):
                write_jsonl(self.directory / "foundry-eval.jsonl", [invalid, self.rows[1]])
                with self.assertRaises(LabError):
                    self.submit()
                self.auth.assert_not_called()

    def test_parent_export_answer_projection_keeps_api_and_format_failures_in_denominator(self):
        from lab.evidence import evaluate_gates, load_gates, score_row, summarize

        self.cases.append({**self.cases[0], "id": "case-d", "group_id": "group-d"})
        self.records.append({
            "id": "case-d", "raw_output": '{"answer": "missing routing/schema fields"}',
            "retrieved_context": "", "error": None,
        })
        write_jsonl(self.dataset_path, self.cases)
        self.seed_run("local-run")
        original_outputs = (self.directory / "outputs.jsonl").read_bytes()
        self.export_with_parent()
        notes = self.read("export-notes.json")
        self.assertEqual(notes["exported_rows"], 2)
        self.assertEqual(notes["failed_rows"], 2)
        self.assertEqual(notes["format_invalid_rows"], 1)
        self.submit()
        result = self.collect()
        self.assertEqual(result["unscored_capture_ids"], ["case-c", "case-d"])
        scores = self.read("judge-scores.json")
        self.assertEqual(set(scores), {"case-a", "case-b"})
        self.assertEqual(original_outputs, (self.directory / "outputs.jsonl").read_bytes())
        metadata = self.read("metadata.json")
        self.assertEqual(metadata["row_ids"], ["case-a", "case-b", "case-c", "case-d"])
        records = {record["id"]: record for record in self.records}
        scored = [
            score_row(
                case, records[case["id"]]["raw_output"], known_citations={"policy-fixture"},
                error=records[case["id"]]["error"], judge=scores.get(case["id"]),
            )
            for case in self.cases
        ]
        summary = summarize(scored, metadata=metadata)
        for metric in managed_eval.METRICS:
            self.assertEqual(summary["metrics"]["judge"][metric]["scored_count"], 2)
            self.assertEqual(summary["metrics"]["judge"][metric]["missing_count"], 2)
        self.assertEqual(evaluate_gates(summary, load_gates())["outcome"], "HOLD")

    def test_format_failure_without_api_error_does_not_rewrite_completed_capture_status(self):
        self.records[2]["error"] = None
        self.seed_run("local-run")
        self.export_with_parent()
        self.assertEqual(self.read("metadata.json")["status"], "completed")
        self.assertEqual(self.read("export-notes.json")["format_invalid_rows"], 1)
        self.submit()
        result = self.collect()
        self.assertEqual(result["unscored_capture_ids"], ["case-c"])
        self.assertEqual(self.read("metadata.json")["status"], "completed")
        self.assertNotIn("case-c", self.read("judge-scores.json"))

    def test_all_format_failures_block_paid_submission_even_without_export_file(self):
        from lab.batch import export_evaluation

        for record in self.records:
            record.update(error=None, raw_output="not response JSON")
        self.seed_run("local-run")
        (self.directory / "foundry-eval.jsonl").unlink()
        with patch("lab.batch.ROOT", self.root):
            export_evaluation(self.directory, self.cases, self.records)
        self.assertFalse((self.directory / "foundry-eval.jsonl").exists())
        self.assertEqual(self.read("export-notes.json")["format_invalid_rows"], 3)
        with self.assertRaisesRegex(LabError, "JSON 형식 유효"):
            self.submit()
        self.auth.assert_not_called()
        self.assert_no_paid_requests()

    def test_format_invalid_capture_cannot_be_smuggled_into_the_export(self):
        self.records[1]["raw_output"] = "a repaired answer is not an original schema-valid response"
        write_jsonl(self.directory / "outputs.jsonl", self.records)
        with self.assertRaisesRegex(LabError, "JSON 형식 유효 캡처 ID"):
            self.submit()
        self.assert_no_paid_requests()

    def test_schema_valid_rule_failures_remain_eligible_instead_of_cherry_picking_passes(self):
        self.records[0]["raw_output"] = self.response_json(
            "캡처 응답 case-a", route="escalate", citations=["unknown-policy"], needs_human=True,
        )
        self.seed_run("local-run")
        self.export_with_parent()
        self.submit()
        self.collect()
        self.assertEqual(set(self.read("judge-scores.json")), {"case-a", "case-b"})
        request_rows = self.client.evals.runs.create.call_args.kwargs["data_source"]["source"]["content"]
        self.assertEqual(request_rows[0]["item"]["response"], "캡처 응답 case-a")
        self.assertNotIn("route", request_rows[0]["item"])
        self.assertNotIn("citations", request_rows[0]["item"])

    def test_projected_json_looking_answers_are_never_json_parsed_again(self):
        answer = '{"answer":"이 문자열 자체가 답변입니다","route":"not-a-routing-label"}'
        reference = '{"answer":"이 문자열 자체가 참조 답변입니다"}'
        self.records[0]["raw_output"] = self.response_json(answer)
        self.cases[0]["ground_truth"] = self.response_json(reference)
        write_jsonl(self.dataset_path, self.cases)
        self.seed_run("local-run")
        self.export_with_parent()
        self.submit()
        self.collect()
        uploaded = self.client.evals.runs.create.call_args.kwargs["data_source"]["source"]["content"][0]["item"]
        self.assertEqual(uploaded["response"], answer)
        self.assertNotIn("ground_truth", uploaded)
        self.assertEqual(self.rows[0]["ground_truth"], reference)
        self.assertNotEqual(uploaded["response"], json.loads(answer)["answer"])
        self.assertEqual(self.read("judge-scores.json")["case-a"]["groundedness"], 4.0)

    def test_full_raw_response_or_reference_json_cannot_replace_answer_projection(self):
        for field, full_json in (
            ("response", self.records[0]["raw_output"]),
            ("ground_truth", self.cases[0]["ground_truth"]),
        ):
            with self.subTest(field=field):
                rows = deepcopy(self.rows)
                rows[0][field] = full_json
                write_jsonl(self.directory / "foundry-eval.jsonl", rows)
                with self.assertRaisesRegex(LabError, "answer 투영"):
                    self.submit()
                self.assert_no_paid_requests()

    def test_invalid_master_reference_json_is_not_confused_with_projected_plain_reference(self):
        self.cases[0]["ground_truth"] = self.rows[0]["ground_truth"]
        write_jsonl(self.dataset_path, self.cases)
        self.seed_run("local-run")
        with self.assertRaisesRegex(LabError, "원본 ground_truth"):
            self.submit()
        self.assert_no_paid_requests()

    def test_running_collection_returns_actual_status_and_retry_without_scores(self):
        self.submit()
        for status in ("queued", "in_progress", "running", "canceling"):
            with self.subTest(status=status):
                self.client.evals.runs.retrieve.return_value = self.run_response(status)
                result = self.collect()
                self.assertEqual(result["status"], status)
                self.assertEqual(result["next_step"], "python -m lab evaluate collect --run-id local-run")
                self.assertNotEqual(result["collection_status"], "collected")
        self.assertEqual(self.client.evals.runs.retrieve.call_count, 4)
        self.client.evals.runs.output_items.list.assert_not_called()
        self.assertFalse((self.directory / "judge-scores.json").exists())
        self.assertIsNone(self.read("metadata.json")["judge"])

    def test_failed_or_cancelled_collection_raises_with_actual_state(self):
        self.submit()
        for status in ("failed", "canceled", "cancelled"):
            with self.subTest(status=status):
                self.client.evals.runs.retrieve.return_value = self.run_response(status)
                with self.assertRaisesRegex(LabError, status):
                    self.collect()
                self.assertEqual(self.read(managed_eval.LEDGER)["status"], status)
        self.client.evals.runs.output_items.list.assert_not_called()
        self.assertFalse((self.directory / "judge-scores.json").exists())

    def test_completed_scores_join_case_ids_not_positions_and_keep_capture_gaps(self):
        self.submit()
        result = self.collect()
        scores = self.read("judge-scores.json")
        self.assertEqual(scores, {
            "case-a": {"groundedness": 4.0, "relevance": 5.0, "error": None},
            "case-b": {"groundedness": 2.0, "relevance": 3.0, "error": None},
        })
        self.assertTrue(all(
            type(values[metric]) is float for values in scores.values() for metric in managed_eval.METRICS
        ))
        self.assertNotIn("case-c", scores)
        self.assertEqual(result["collection_status"], "collected")
        self.assertEqual(result["unscored_capture_ids"], ["case-c"])
        self.assertEqual(result["scored_rows"], 2)
        self.assertNotIn("next_step", result)
        metadata = self.read("metadata.json")
        self.assertEqual({key: value for key, value in metadata.items() if key not in {"judge", managed_eval.MANAGED_METADATA}},
                         {key: value for key, value in self.metadata.items() if key != "judge"})
        judge = metadata["judge"]
        contract = self.read(managed_eval.CONTRACT)
        canonical = json.dumps(contract, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        self.assertEqual(judge["prompt_sha256"], hashlib.sha256(canonical.encode()).hexdigest())
        self.assertEqual(judge["model_deployment"], self.config.judge)
        self.assertEqual(judge["scale"], [1, 5])
        self.assertEqual(judge["settings"]["testing_criteria"], contract["testing_criteria"])
        self.assertEqual(judge["version"], "service-managed/unpinned")
        self.assertIs(judge["service_version_pinned"], False)
        self.assertEqual(judge["settings"]["evaluators"]["builtin.groundedness"]["version"], "7")
        self.assertEqual(judge["provenance"]["source_artifact"], managed_eval.CONTRACT)
        self.assertIn("not the private managed prompt", judge["provenance"]["hash_scope"])
        self.assertNotIn("eval-fixture", json.dumps(judge))
        self.assertNotIn("run-fixture", json.dumps(judge))
        self.assertIn("not evidence of agent retrieval", contract["context_definition"])
        self.assertIn("Only answer from schema-valid", contract["response_projection"])
        raw = self.read("managed-eval-output-items.json")
        self.assertIn("reason", raw["items"][0]["results"][0])
        self.assertEqual(self.client.evals.create.call_count, 1)
        self.assertEqual(self.client.evals.runs.create.call_count, 1)
        self.client.responses.create.assert_not_called()

    def test_same_judge_contract_is_exact_across_baseline_and_candidate(self):
        self.seed_run("candidate-run", stage="optimized")
        self.submit()
        self.collect()
        baseline_contract = (self.directory / managed_eval.CONTRACT).read_bytes()
        baseline_judge = self.read("metadata.json")["judge"]
        managed_eval.submit_evaluation(self.config, "candidate-run")
        managed_eval.collect_evaluation(self.config, "candidate-run")
        candidate_dir = self.root / "runs/candidate-run"
        self.assertEqual(baseline_contract, (candidate_dir / managed_eval.CONTRACT).read_bytes())
        self.assertEqual(
            baseline_judge, json.loads((candidate_dir / "metadata.json").read_text(encoding="utf-8"))["judge"],
        )

    def test_evidence_import_and_iq_optimized_pairing_keep_capture_gaps_on_hold(self):
        from lab.evidence import compare_runs, load_gates, score_row, summarize

        for case in self.cases:
            case.update(
                group_id=f"group-{case['id']}", split="test", expected_route="answer",
                required_citations=["policy-fixture"], tags=["critical"] if case["id"] == "case-a" else [],
            )
        for record in self.records:
            record["raw_output"] = "" if record["error"] else json.dumps({
                "answer": "고정 정책에 근거한 fixture 응답", "route": "answer",
                "citations": ["policy-fixture"], "needs_human": False,
            }, ensure_ascii=False)
        records = {record["id"]: record for record in self.records}
        self.rows = [
            {
                "case_id": case["id"], "query": case["query"], "context": case["context"],
                "ground_truth": json.loads(case["ground_truth"])["answer"],
                "response": json.loads(records[case["id"]]["raw_output"])["answer"],
                "retrieved_context": records[case["id"]]["retrieved_context"],
            }
            for case in self.cases if records[case["id"]]["error"] is None
        ]
        self.dataset_path = self.root / "data/splits/test.jsonl"
        write_jsonl(self.dataset_path, self.cases)
        summaries = []
        for local_run, stage in (("iq-test", "iq"), ("optimized-test", "optimized")):
            self.seed_run(local_run, stage=stage, split="test")
            eval_id, job_id = f"eval-{local_run}", f"job-{local_run}"
            report_url = f"https://example.invalid/report/{local_run}"
            self.client.evals.create.return_value = {"id": eval_id}
            self.client.evals.runs.create.return_value = RunCreateResponse.model_construct(
                id=job_id, eval_id=eval_id, status="queued", report_url=report_url,
            )
            self.client.evals.runs.retrieve.return_value = self.run_response(
                counts=ResultCounts(total=2, passed=2, failed=0, errored=0),
            ).model_copy(update={"id": job_id, "eval_id": eval_id, "report_url": report_url})
            self.items = [
                self.output_item(row, wrapped=True).model_copy(update={"eval_id": eval_id, "run_id": job_id})
                for row in reversed(self.rows)
            ]
            managed_eval.submit_evaluation(self.config, local_run)
            managed_eval.collect_evaluation(self.config, local_run)
            directory = self.root / "runs" / local_run
            metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
            scores = json.loads((directory / "judge-scores.json").read_text(encoding="utf-8"))
            scored_rows = [
                score_row(
                    case, records[case["id"]]["raw_output"], known_citations={"policy-fixture"},
                    error=records[case["id"]]["error"], judge=scores.get(case["id"]),
                )
                for case in self.cases
            ]
            summary = summarize(scored_rows, metadata=metadata)
            self.assertEqual(summary["metadata"]["row_ids"], ["case-a", "case-b", "case-c"])
            for metric in managed_eval.METRICS:
                self.assertEqual(summary["metrics"]["judge"][metric]["scored_count"], 2)
                self.assertEqual(summary["metrics"]["judge"][metric]["missing_count"], 1)
                self.assertEqual(summary["metrics"]["judge"][metric]["scale"], [1, 5])
            self.assertEqual(scores["case-a"]["error"], None)
            self.assertNotIn("case-c", scores)
            summaries.append(summary)
        baseline, candidate = summaries
        self.assertEqual(baseline["metadata"]["judge"], candidate["metadata"]["judge"])
        self.assertNotEqual(
            baseline["metadata"][managed_eval.MANAGED_METADATA],
            candidate["metadata"][managed_eval.MANAGED_METADATA],
        )
        decision = compare_runs(baseline, candidate, load_gates())
        self.assertEqual(decision["outcome"], "HOLD")
        self.assertTrue(decision["judge_comparison"]["comparable"])
        for metric in managed_eval.METRICS:
            check = next(
                item for item in decision["candidate_gate"]["checks"] if item["name"] == f"{metric}_all_rows"
            )
            self.assertFalse(check["passed"])

    def test_report_url_updates_stay_outside_canonical_judge_metadata(self):
        self.submit()
        report_url = "https://example.invalid/report/completed"
        self.client.evals.runs.retrieve.return_value = self.run_response().model_copy(
            update={"report_url": report_url},
        )
        self.collect()
        metadata = self.read("metadata.json")
        self.assertEqual(metadata[managed_eval.MANAGED_METADATA]["report_url"], report_url)
        self.assertEqual(self.read(managed_eval.LEDGER)["report_url"], report_url)
        self.assertNotIn(report_url, json.dumps(metadata["judge"]))

    def test_source_artifacts_and_judge_contract_are_immutable_after_submission(self):
        self.submit()
        original = (self.directory / "outputs.jsonl").read_bytes()
        records = deepcopy(self.records)
        records[2]["error"] = "changed capture failure"
        write_jsonl(self.directory / "outputs.jsonl", records)
        self.auth.reset_mock()
        with self.assertRaisesRegex(LabError, "제출 이후"):
            self.collect()
        self.auth.assert_not_called()
        (self.directory / "outputs.jsonl").write_bytes(original)
        contract = self.read(managed_eval.CONTRACT)
        contract["testing_criteria"][0]["initialization_parameters"]["threshold"] = 3
        save_json(self.directory / managed_eval.CONTRACT, contract)
        with self.assertRaisesRegex(LabError, "계약/배포"):
            self.collect()
        self.auth.assert_not_called()

    def test_changed_judge_deployment_cannot_relabel_old_scores(self):
        self.submit()
        with self.assertRaisesRegex(LabError, "JUDGE_DEPLOYMENT"):
            managed_eval.collect_evaluation(replace(self.config, judge="different-model"), "local-run")
        self.client.evals.runs.retrieve.assert_not_called()

    def test_collection_sdk_errors_propagate_without_scores(self):
        self.submit()
        self.client.evals.runs.output_items.list.side_effect = APIError(
            "fixture collection error", request=Mock(), body=None,
        )
        with self.assertRaisesRegex(APIError, "collection error"):
            self.collect()
        self.assertFalse((self.directory / "judge-scores.json").exists())
        self.assertEqual(self.read(managed_eval.LEDGER)["status"], "completed")

    def test_repeated_successful_collection_does_not_change_judge_evidence(self):
        self.submit()
        self.collect()
        scores = (self.directory / "judge-scores.json").read_bytes()
        contract = (self.directory / managed_eval.CONTRACT).read_bytes()
        metadata = (self.directory / "metadata.json").read_bytes()
        self.collect()
        self.assertEqual(scores, (self.directory / "judge-scores.json").read_bytes())
        self.assertEqual(contract, (self.directory / managed_eval.CONTRACT).read_bytes())
        self.assertEqual(metadata, (self.directory / "metadata.json").read_bytes())
        self.assertEqual(self.client.evals.runs.create.call_count, 1)

    def test_different_results_never_overwrite_collected_scores(self):
        self.submit()
        self.collect()
        original = (self.directory / "judge-scores.json").read_bytes()
        self.items[1] = self.output_item(self.rows[0], groundedness=5, relevance=5)
        with self.assertRaisesRegex(LabError, "덮어쓰지"):
            self.collect()
        self.assertEqual(original, (self.directory / "judge-scores.json").read_bytes())

    def assert_invalid_items(self, payloads):
        self.items = payloads
        with self.assertRaises(LabError):
            self.collect()
        self.assertFalse((self.directory / "judge-scores.json").exists())
        self.assertIsNone(self.read("metadata.json")["judge"])
        self.assertEqual(self.read(managed_eval.LEDGER)["collection_status"], "invalid_results")

    def test_output_items_duplicate_missing_unknown_or_ambiguous_ids_fail_closed(self):
        self.submit()
        first, second = [item.model_dump(mode="json", exclude_unset=True) for item in self.items]
        cases = [
            [first], [],
            [first, first], [first, {**second, "id": first["id"]}],
            [first, {**second, "datasource_item": {**second["datasource_item"], "case_id": "unknown"}}],
            [first, {**second, "datasource_item": {"query": "missing case id"}}],
            [first, {**second, "datasource_item": {"item": second["datasource_item"], "case_id": "case-a"}}],
            [first, {**second, "eval_id": "different-eval"}],
            [first, {**second, "run_id": "different-run"}],
            [first, second, self.output_item(self.rows[0])],
        ]
        for payload in cases:
            with self.subTest(payload_count=len(payload)):
                self.assert_invalid_items(payload)

    def test_numeric_datasource_item_id_is_never_a_fallback_join_key(self):
        self.submit()
        first, second = [item.model_dump(mode="json", exclude_unset=True) for item in self.items]
        second["datasource_item_id"] = 0
        del second["datasource_item"]["case_id"]
        self.assert_invalid_items([first, second])

    def test_changed_service_input_is_rejected(self):
        self.submit()
        first, second = [item.model_dump(mode="json", exclude_unset=True) for item in self.items]
        second["datasource_item"]["response"] = "another generated response"
        self.assert_invalid_items([first, second])

    def test_incomplete_duplicate_unknown_or_wrong_evaluator_results_fail_closed(self):
        self.submit()
        original = [item.model_dump(mode="json", exclude_unset=True) for item in self.items]
        result = original[1]["results"][0]
        variants = [
            [], [result], [result, result],
            [{**result, "metric": "unexpected"}, original[1]["results"][1]],
            [{**result, "name": "relevance"}, original[1]["results"][1]],
            [{**result, "type": "score_model"}, original[1]["results"][1]],
            [{**result, "evaluator_version": "different"}, original[1]["results"][1]],
            [{**result, "evaluator_name": "builtin.coherence"}, original[1]["results"][1]],
        ]
        for results in variants:
            with self.subTest(results=results):
                items = deepcopy(original)
                items[1]["results"] = results
                self.assert_invalid_items(items)

    def test_invalid_scores_are_never_coerced_or_invented(self):
        self.submit()
        original = [item.model_dump(mode="json", exclude_unset=True) for item in self.items]
        for value in (None, True, "5", 0, 6, float("nan"), float("inf"), -(10 ** 300)):
            with self.subTest(score=value):
                items = deepcopy(original)
                items[1]["results"][0]["score"] = value
                self.assert_invalid_items(items)
        items = deepcopy(original)
        del items[1]["results"][0]["score"]
        self.assert_invalid_items(items)

    def test_threshold_labels_and_pass_flags_cannot_override_numeric_score(self):
        self.submit()
        original = [item.model_dump(mode="json", exclude_unset=True) for item in self.items]
        for changes in (
            {"threshold": 3}, {"threshold": True}, {"passed": False}, {"passed": 1},
            {"label": "fail"}, {"reason": {"not": "text"}},
        ):
            with self.subTest(changes=changes):
                items = deepcopy(original)
                items[1]["results"][0].update(changes)
                self.assert_invalid_items(items)

    def test_service_error_rows_and_evaluator_errors_cannot_grant_scores(self):
        self.submit()
        original = [item.model_dump(mode="json", exclude_unset=True) for item in self.items]
        for changes in (
            {"status": "error"}, {"status": "running"},
            {"error": {"code": "fixture", "message": "error"}},
            {"sample": {"error": {"code": "fixture", "message": "error"}}},
            {"sample": "invalid"},
        ):
            with self.subTest(changes=changes):
                items = deepcopy(original)
                items[1].update(changes)
                self.assert_invalid_items(items)
        for changes in (
            {"error": {"code": "fixture", "message": "error"}},
            {"sample": {"error": {"code": "fixture", "message": "error"}}},
        ):
            with self.subTest(result_changes=changes):
                items = deepcopy(original)
                items[1]["results"][0].update(changes)
                self.assert_invalid_items(items)

    def test_error_counts_missing_totals_and_count_mismatch_fail_closed(self):
        self.submit()
        for counts in (
            {}, {"total": 1}, {"total": True}, {"total": 2, "errored": 1},
            {"total": 2, "errored": False},
            {"total": 2, "passed": 1, "failed": 0, "errored": 0},
        ):
            with self.subTest(counts=counts):
                run = self.run_response().model_dump(mode="json", exclude_unset=True)
                run["result_counts"] = counts
                self.client.evals.runs.retrieve.return_value = run
                with self.assertRaises(LabError):
                    self.collect()
                self.assertFalse((self.directory / "judge-scores.json").exists())

    def test_documented_basic_sdk_metric_names_without_optional_fields(self):
        self.submit()
        items = [item.model_dump(mode="json", exclude_unset=True) for item in self.items]
        for item in items:
            item["results"] = [
                {key: value for key, value in result.items() if key in {"name", "type", "score", "passed"}}
                for result in item["results"]
            ]
        self.items = items
        self.collect()
        self.assertEqual(self.read("judge-scores.json")["case-a"]["groundedness"], 4.0)

    def test_iterator_reads_all_pages_and_does_not_only_use_first_page_data(self):
        self.submit()

        class PagedItems:
            data = [self.items[0]]

            def __iter__(page):
                yield from page.data
                yield self.items[1]

        self.client.evals.runs.output_items.list.side_effect = None
        self.client.evals.runs.output_items.list.return_value = PagedItems()
        self.collect()
        self.assertEqual(len(self.read("judge-scores.json")), 2)

    def test_output_item_iteration_is_bounded_by_expected_rows(self):
        self.submit()
        self.client.evals.runs.output_items.list.side_effect = None
        self.client.evals.runs.output_items.list.return_value = repeat(self.items[0])
        with self.assertRaisesRegex(LabError, "중복"):
            self.collect()
        self.assertFalse((self.directory / "judge-scores.json").exists())

    def test_numeric_five_without_observed_retrieval_is_unavailable_not_policy_grounding(self):
        self.records[0]["retrieved_context"] = ""
        self.rows[0]["retrieved_context"] = ""
        write_jsonl(self.directory / "outputs.jsonl", self.records)
        write_jsonl(self.directory / "foundry-eval.jsonl", self.rows)
        self.items = [self.output_item(row, groundedness=5) for row in self.rows]
        self.submit()
        self.collect()
        score = self.read("judge-scores.json")["case-a"]
        self.assertIsNone(score["groundedness"])
        self.assertEqual(score["relevance"], 4)
        self.assertEqual(score["metric_errors"]["groundedness"], "retrieval_not_observed")
        request = self.client.evals.runs.create.call_args.kwargs["data_source"]["source"]["content"][0]["item"]
        self.assertEqual(request["retrieved_context"], "")
        self.assertNotIn("context", request)
        self.assertNotIn("ground_truth", request)

    def test_missing_scores_keep_full_capture_denominator_and_diagnostic_error(self):
        self.submit()
        self.items = [self.items[0]]
        with self.assertRaisesRegex(LabError, "누락"):
            self.collect()
        self.assertFalse((self.directory / "judge-scores.json").exists())
        diagnostics = self.read("judge-diagnostics.json")
        self.assertEqual(diagnostics["total_attempted_captures"], 3)
        self.assertEqual(diagnostics["accepted_score_count"], 0)
        self.assertEqual(diagnostics["capture_ids"], ["case-a", "case-b", "case-c"])
        self.assertTrue((self.directory / "managed-eval-output-items.json").is_file())

    def test_old_policy_grounding_contract_cannot_be_silently_reinterpreted(self):
        self.submit()
        contract = self.read(managed_eval.CONTRACT)
        contract["contract_version"] = "foundry-policy-reference-v3"
        save_json(self.directory / managed_eval.CONTRACT, contract)
        self.auth.reset_mock()
        with self.assertRaisesRegex(LabError, "Legacy policy-reference"):
            self.collect()
        self.auth.assert_not_called()

    def test_governed_final_holdout_cannot_use_unversioned_builtin_judge_instead(self):
        metadata = self.read("metadata.json")
        metadata["freeze_id"] = "unit-test-freeze"
        save_json(self.directory / "metadata.json", metadata)
        with self.assertRaisesRegex(LabError, "calibrated versioned"):
            self.submit()
        self.auth.assert_not_called()
        self.assert_no_paid_requests()


if __name__ == "__main__":
    unittest.main()
