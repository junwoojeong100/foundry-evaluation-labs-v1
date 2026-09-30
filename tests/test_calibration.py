"""Synthetic local mocks only: these are not LIVE Judge calibration results."""

from contextlib import nullcontext
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

from lab import calibration
from lab.config import LabError
from lab.files import ROOT as SOURCE_ROOT, sha256_file, write_jsonl


class CalibrationTests(unittest.TestCase):
    def test_judge_conversation_excludes_nested_api_and_tool_envelopes(self):
        fixture = calibration.load_fixtures()[0]
        payload = calibration.judge_payloads(
            fixture["case"], fixture["raw_output"], fixture["retrieved_context"],
            conversation=[{
                "input": "explicit customer follow-up", "input_source": "scripted_user",
                "raw_output": fixture["raw_output"],
                "response": {"nested_api_envelope": "must-not-enter-policy-judge"},
                "retrieved_context": "duplicate-full-tool-response",
                "usage": {"input_tokens": 999},
            }],
        )
        self.assertEqual(payload["policy"]["conversation"], [
            {"role": "user", "content": "explicit customer follow-up", "source": "scripted_user"},
            {"role": "assistant", "content": fixture["raw_output"]},
        ])
        self.assertNotIn("nested_api_envelope", json.dumps(payload["policy"]))
        self.assertNotIn("conversation", payload["retrieval"])

    def setUp(self):
        self.root = Path("artifacts") / f"test-calibration-{uuid4().hex}"
        self.root.mkdir(parents=True)
        self.addCleanup(shutil.rmtree, self.root)
        self.patch("lab.calibration.ARTIFACTS", self.root)
        self.fixtures = calibration.load_fixtures()
        self.contract = calibration.evaluator_contract()
        self.config = SimpleNamespace(
            judge="mock-judge", project_endpoint="https://fixture.invalid/project",
            expected_user="fixture@example.invalid", tenant_id="mock-tenant", subscription_id="mock-subscription",
        )
        self.snapshot = {"deployment": "mock-judge", "model": {"name": "mock-only", "version": "1"}}
        self.requests = []

        def create(**kwargs):
            self.requests.append(kwargs)
            self.assertTrue(all(message.get("type") == "message" for message in kwargs["input"]))
            payload = json.loads(kwargs["input"][1]["content"])
            fixture = next(row for row in self.fixtures if row["raw_output"] == payload["response"])
            kind = "policy" if "authoritative_policy" in payload else "retrieval"
            labels = fixture["reference_labels"]
            if kind == "policy":
                value = {
                    "policy_correctness": 5 if labels["policy_correctness"] else 2,
                    "relevance": 5 if labels["relevance"] else 2,
                    "critical_failure": "critical" in fixture["tags"] and not labels["policy_correctness"],
                    "reason": "Unit-test mock, not a live judgment.",
                }
            else:
                value = {"groundedness": 5 if labels["groundedness"] else 2, "reason": "Mock observed context."}
            return self.response(value, len(self.requests))

        self.client = SimpleNamespace(responses=SimpleNamespace(create=Mock(side_effect=create)))
        self.project = SimpleNamespace(get_openai_client=Mock(return_value=nullcontext(self.client)))
        self.auth = self.patch("lab.calibration.credential_for", return_value=nullcontext("mock-credential"))
        self.factory = self.patch("lab.calibration.AIProjectClient", return_value=nullcontext(self.project))
        self.model = self.patch("lab.calibration.model_snapshot", return_value=self.snapshot)

    def patch(self, target, *args, **kwargs):
        patcher = patch(target, *args, **kwargs)
        value = patcher.start()
        self.addCleanup(patcher.stop)
        return value

    @staticmethod
    def response(value, identifier=1):
        raw = json.dumps(value) if not isinstance(value, str) else value
        return SimpleNamespace(
            id=f"resp-mock-{identifier}", output_text=raw,
            model_dump=lambda **kwargs: {"id": f"resp-mock-{identifier}", "status": "completed", "output": []},
        )

    def test_authored_references_are_diverse_and_not_human_reviews(self):
        self.assertGreaterEqual(len(self.fixtures), 10)
        self.assertEqual({row["reference_labels"]["policy_correctness"] for row in self.fixtures}, {True, False})
        self.assertEqual(len({row["id"] for row in self.fixtures}), len(self.fixtures))
        self.assertTrue(all(row["human_review_state"] == "not_reviewed" for row in self.fixtures))
        self.assertTrue(any(
            row["reference_labels"]["groundedness"] is True and row["reference_labels"]["policy_correctness"] is False
            for row in self.fixtures
        ))

    def test_calibration_pacing_is_recorded_and_does_not_add_requests(self):
        sleep = self.patch("lab.calibration.time.sleep")
        report = calibration.run_calibration(self.config, "paced", confirm=True, interval_seconds=65)
        self.assertEqual(report["metadata"]["interval_seconds"], 65)
        self.assertEqual(sleep.call_count, len(self.fixtures) - 1)
        sleep.assert_called_with(65)
        self.assertEqual(len(self.requests), 31)
        self.assertEqual(report["execution_status"], "completed")

    def test_invalid_calibration_pacing_does_not_claim_an_attempt(self):
        for value in (-1, 121, True, float("nan")):
            with self.subTest(value=value), self.assertRaises(LabError):
                calibration.run_calibration(self.config, "invalid-pacing", confirm=True, interval_seconds=value)
        self.assertFalse((self.root / "calibration/invalid-pacing").exists())
        self.assertEqual(self.requests, [])

    def test_independent_payloads_do_not_leak_reference_labels_or_policy_into_retrieval(self):
        fixture = self.fixtures[0]
        case = {**fixture["case"], "reference_labels": "DO_NOT_SEND", "label": "SECRET_LABEL"}
        payload = calibration.judge_payloads(case, fixture["raw_output"], "ACTUAL_MCP_CONTEXT")
        self.assertEqual(set(payload["retrieval"]), {"query", "response", "retrieved_context"})
        self.assertEqual(payload["retrieval"]["retrieved_context"], "ACTUAL_MCP_CONTEXT")
        self.assertNotIn("DO_NOT_SEND", str(payload))
        self.assertNotIn("SECRET_LABEL", str(payload))
        self.assertEqual(payload["policy"]["authoritative_policy"], case["context"])
        self.assertNotIn("retrieved_context", payload["policy"])

    def test_strict_json_and_score_ranges_never_repair_or_coerce(self):
        good = {"policy_correctness": 4, "relevance": 5, "critical_failure": False, "reason": "mock"}
        self.assertEqual(calibration.parse_judgment(json.dumps(good), "policy"), good)
        for value in (True, None, 0, 6, 4.0, "5", float("nan")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                calibration.parse_judgment(json.dumps({**good, "policy_correctness": value}), "policy")
        for raw in (
            "```json\n" + json.dumps(good) + "\n```", '{"groundedness":5,"groundedness":1,"reason":"x"}',
            '{"groundedness":5,"reason":" "}', '{"groundedness":5,"reason":"x","extra":true}',
        ):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                calibration.parse_judgment(raw, "retrieval")

    def test_missing_retrieval_is_unavailable_without_a_paid_grounding_call(self):
        fixture = next(row for row in self.fixtures if not row["retrieved_context"])
        result = calibration.judge_case(
            self.client, self.config.judge, fixture["case"], fixture["raw_output"], "", contract=self.contract,
        )
        self.assertEqual(len(self.requests), 1)
        self.assertIsNone(result["judge"]["groundedness"])
        self.assertEqual(result["judge"]["metric_errors"]["groundedness"], "retrieval_not_observed")
        self.assertNotIn("retrieval", [request["text"]["format"]["name"] for request in self.requests])

    def test_callable_real_execution_path_uses_verified_config_and_preserves_all_rows(self):
        report = calibration.run_calibration(self.config, "mock-calibration", confirm=True)
        self.auth.assert_called_once_with(self.config)
        self.factory.assert_called_once_with(endpoint=self.config.project_endpoint, credential="mock-credential", retry_total=0)
        self.project.get_openai_client.assert_called_once_with(max_retries=0, timeout=120.0)
        self.assertEqual(self.model.call_count, 2)
        self.assertEqual(report["sample_count"], 16)
        self.assertEqual(report["quality_status"], "PASS")
        self.assertEqual(report["metrics"]["groundedness"]["not_applicable_count"], 1)
        self.assertEqual(report["metrics"]["policy_correctness"]["agreement_rate"], 1.0)
        self.assertEqual(report["critical_false_accept_count"], 0)
        self.assertEqual(report["human_review_state"], "not_reviewed")
        self.assertEqual(report["manual_operational_approval"], "not_granted")
        self.assertTrue(all(request["model"] == self.config.judge for request in self.requests))
        self.assertTrue(all(request["text"]["format"]["strict"] for request in self.requests))
        self.assertTrue((self.root / "calibration/mock-calibration/report.json").is_file())
        with self.assertRaisesRegex(LabError, "already attempted"):
            calibration.run_calibration(self.config, "mock-calibration", confirm=True)
        self.assertEqual(len(self.requests), 31)

    def test_paid_entrypoint_rejects_unconfirmed_call_before_auth(self):
        with self.assertRaisesRegex(LabError, "--confirm"):
            calibration.run_calibration(self.config, "unconfirmed")
        self.auth.assert_not_called()
        self.client.responses.create.assert_not_called()

    def test_remote_id_checkpoint_precedes_response_parsing(self):
        fixture, saved = self.fixtures[0], []
        response = self.response({"policy_correctness": 5, "relevance": 5, "critical_failure": False, "reason": "mock"})

        def dump(**kwargs):
            self.assertEqual(saved[-1]["requests"]["policy"]["response_id"], response.id)
            return {"status": "completed"}

        response.model_dump = dump
        self.client.responses.create.side_effect = [response, self.response({"groundedness": 5, "reason": "mock"}, 2)]
        calibration.judge_case(
            self.client, self.config.judge, fixture["case"], fixture["raw_output"], fixture["retrieved_context"],
            contract=self.contract, checkpoint=saved.append,
        )
        self.assertEqual(saved[0]["requests"]["policy"]["status"], "submitting")
        self.assertIsNone(saved[0]["requests"]["policy"]["response_id"])

    def test_full_denominator_and_critical_false_accept_cannot_be_hidden(self):
        rows = []
        for fixture in self.fixtures:
            labels = fixture["reference_labels"]
            rows.append({
                "id": fixture["id"], "judge": {
                    **{key: None if value is None else 5 if value else 2 for key, value in labels.items()},
                    "critical_failure": "critical" in fixture["tags"] and not labels["policy_correctness"],
                    "error": None, "metric_errors": {},
                },
            })
        bad = next(row for row in rows if row["id"] == "cal-refund-approved-bad")
        bad["judge"]["policy_correctness"] = 5
        missing_id = rows.pop()["id"]
        result = calibration.summarize_calibration(self.fixtures, rows)
        self.assertEqual(result["sample_count"], 16)
        self.assertEqual(result["metrics"]["policy_correctness"]["missing_count"], 1)
        self.assertEqual(result["metrics"]["policy_correctness"]["agreement_rate"], 14 / 16)
        self.assertEqual(result["critical_false_accept_ids"], ["cal-refund-approved-bad"])
        self.assertIn(missing_id, result["disagreement_ids"])
        self.assertEqual(result["quality_status"], "HOLD")

    def test_transport_errors_are_preserved_and_never_turned_into_zero_or_success(self):
        self.client.responses.create.side_effect = RuntimeError("unit-only transport failure")
        report = calibration.run_calibration(self.config, "mock-errors", confirm=True)
        self.assertEqual(report["execution_status"], "blocked_unknown_outcome")
        self.assertEqual(report["quality_status"], "HOLD")
        self.assertEqual(report["metrics"]["policy_correctness"]["scored_count"], 0)
        self.assertEqual(report["metrics"]["policy_correctness"]["missing_count"], 16)
        self.assertEqual(report["metrics"]["policy_correctness"]["agreement_rate"], 0.0)
        self.assertIn("unit-only transport failure", str(report))
        self.assertTrue(all(row["judge"]["policy_correctness"] is None for row in report["rows"]))

    def test_model_drift_and_access_blocker_remain_separate_from_quality(self):
        self.model.side_effect = [self.snapshot, {"model": {"version": "changed"}}]
        report = calibration.run_calibration(self.config, "mock-drift", confirm=True)
        self.assertEqual(report["execution_status"], "invalid_model_drift")
        self.assertEqual(report["quality_status"], "HOLD")
        self.assertEqual(report["access_blockers"], [])
        self.auth.side_effect = LabError("unit-only identity denied")
        report = calibration.run_calibration(self.config, "mock-access", confirm=True)
        self.assertEqual(report["execution_status"], "blocked_access")
        self.assertEqual(report["quality_status"], "HOLD")
        self.assertEqual(report["metrics"]["policy_correctness"]["missing_count"], 16)
        self.assertIn("identity denied", report["access_blockers"][0])

    def test_local_modules_do_not_import_azure_or_openai(self):
        code = """
import importlib.abc, sys
class DenySDK(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name.split('.')[0] in {'azure','openai'}:
            raise RuntimeError('SDK imported eagerly: ' + name)
sys.meta_path.insert(0, DenySDK())
import lab.calibration, lab.governance, lab.batch, lab.managed_eval
assert len(lab.calibration.load_fixtures()) >= 10
"""
        completed = subprocess.run([sys.executable, "-c", code], text=True, capture_output=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def seed_captured_run(self):
        package = self.root / "package"
        shutil.copytree(SOURCE_ROOT / "config", package / "config")
        shutil.copytree(SOURCE_ROOT / "data", package / "data")
        self.patch("lab.calibration.ROOT", package)
        self.patch("lab.batch.ROOT", package)
        self.patch("lab.files.ARTIFACTS", self.root)
        path = package / "data/splits/dev.jsonl"
        cases = calibration.read_jsonl(path)[:3]
        records = [
            {
                "id": case["id"], "raw_output": case["ground_truth"] if index == 0 else "invalid JSON" if index == 1 else "",
                "retrieved_context": "Unit-test actual retrieval stand-in.",
                "error": "unit-only agent failure" if index == 2 else None,
                "latency_ms": None, "usage": None, "response": None,
            } for index, case in enumerate(cases)
        ]
        directory = self.root / "runs/captured"
        write_jsonl(directory / "outputs.jsonl", records)
        metadata = {
            "run_id": "captured", "stage": "baseline", "split": "smoke", "source_split": "dev",
            "status": "completed_with_errors", "project_endpoint": self.config.project_endpoint,
            "model_deployment": "mock-agent-model", "dataset_sha256": sha256_file(path),
            "prompt_sha256": "a" * 64, "knowledge_sha256": "b" * 64,
            "row_ids": [case["id"] for case in cases], "judge": None,
            "outputs_sha256": sha256_file(directory / "outputs.jsonl"),
            "evaluation_contract_version": calibration.CONTRACT_VERSION,
        }
        calibration.save_json(directory / "metadata.json", metadata)
        self.client.responses.create.side_effect = [
            self.response({"policy_correctness": 5, "relevance": 5, "critical_failure": False, "reason": "Unit-only mock"}, 1),
            self.response({"groundedness": 5, "reason": "Unit-only mock"}, 2),
        ]
        return directory, metadata

    def test_captured_judge_path_keeps_api_and_format_failures_without_paid_resubmission(self):
        from lab.batch import score_run

        directory, metadata = self.seed_captured_run()
        original = (directory / "outputs.jsonl").read_bytes()
        report = calibration.score_captured_run(self.config, "captured", confirm=True)
        self.assertEqual(report["sample_count"], 3)
        self.assertEqual(report["scored_count"], 1)
        self.assertEqual(report["execution_status"], "completed_with_errors")
        self.assertEqual(self.client.responses.create.call_count, 2)
        self.assertEqual((directory / "outputs.jsonl").read_bytes(), original)
        scores = calibration.read_json(directory / "judge-scores.json")
        self.assertEqual(set(scores), set(metadata["row_ids"]))
        self.assertIn("capture_schema_invalid", scores[metadata["row_ids"][1]]["error"])
        self.assertIn("unit-only agent failure", scores[metadata["row_ids"][2]]["error"])
        summary = score_run("captured")
        self.assertEqual(summary["metrics"]["business_policy"]["scored_count"], 1)
        self.assertEqual(summary["metrics"]["business_policy"]["missing_count"], 2)
        self.assertEqual(summary["metrics"]["judge"]["groundedness"]["coverage"], 1 / 3)
        self.auth.reset_mock()
        with self.assertRaisesRegex(LabError, "already has a Judge attempt"):
            calibration.score_captured_run(self.config, "captured", confirm=True)
        self.auth.assert_not_called()
        self.assertEqual(self.client.responses.create.call_count, 2)

    def test_captured_judge_persists_blocker_without_inventing_execution_success(self):
        directory, metadata = self.seed_captured_run()
        self.auth.side_effect = LabError("unit-only identity rejected")
        report = calibration.score_captured_run(self.config, "captured", confirm=True)
        self.assertEqual(report["execution_status"], "blocked_access")
        self.assertEqual(report["scored_count"], 0)
        self.assertEqual(report["manual_operational_approval"], "not_granted")
        self.client.responses.create.assert_not_called()
        scores = calibration.read_json(directory / "judge-scores.json")
        self.assertEqual(len(scores), 3)
        self.assertTrue(all(row["policy_correctness"] is None for row in scores.values()))
        stored = calibration.read_json(directory / "metadata.json")
        self.assertEqual(stored["status"], metadata["status"])
        self.assertEqual(stored["judge_execution_status"], "blocked_access")

    def test_captured_judge_rejects_restored_but_drifted_capture_before_any_claim_or_auth(self):
        directory, metadata = self.seed_captured_run()
        metadata.update(model_snapshot={"version": "A"}, model_snapshot_after={"version": "B"})
        calibration.save_json(directory / "metadata.json", metadata)
        with self.assertRaisesRegex(LabError, "observed model drift"):
            calibration.score_captured_run(self.config, "captured", confirm=True)
        self.auth.assert_not_called()
        self.client.responses.create.assert_not_called()
        self.assertFalse((directory / calibration.JUDGE_ATTEMPT_CLAIM).exists())

    def test_legacy_unfinished_managed_evaluation_blocks_business_claim_before_auth(self):
        directory, _ = self.seed_captured_run()
        calibration.save_json(directory / "managed-eval.json", {
            "status": "creating_run_unknown", "eval_id": "unit-only-eval", "run_id": None,
        })
        with self.assertRaisesRegex(LabError, "Judge attempt"):
            calibration.score_captured_run(self.config, "captured", confirm=True)
        self.assertFalse((directory / calibration.JUDGE_ATTEMPT_CLAIM).exists())
        self.auth.assert_not_called()
        self.client.responses.create.assert_not_called()

    def test_claim_binds_exact_run_directory_and_project(self):
        directory, _ = self.seed_captured_run()
        for run_id, endpoint in (
            ("other-run", self.config.project_endpoint),
            ("captured", "https://other.invalid/project"),
        ):
            with self.subTest(run_id=run_id, endpoint=endpoint), self.assertRaisesRegex(LabError, "identity|directory"):
                calibration.claim_judge_attempt(
                    directory, run_id, project_endpoint=endpoint,
                    evaluation_path="business-judge", contract=self.contract,
                )
        self.assertFalse((directory / calibration.JUDGE_ATTEMPT_CLAIM).exists())

    def test_existing_sft_utf8_bom_is_still_accepted_by_strict_jsonl_reader(self):
        path = self.root / "unit-only-sft.jsonl"
        row = {"messages": [{"role": "user", "content": "Unit-only fixture, not training execution."}]}
        path.write_text("\ufeff" + json.dumps(row) + "\n", encoding="utf-8")
        self.assertEqual(calibration.read_jsonl(path), [row])


if __name__ == "__main__":
    unittest.main()
