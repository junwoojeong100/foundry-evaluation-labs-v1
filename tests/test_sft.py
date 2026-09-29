"""Offline SFT contract tests. Every cloud response below is an explicit fixture."""

from contextlib import ExitStack, redirect_stderr, redirect_stdout
from copy import deepcopy
from dataclasses import replace
import io
import json
from pathlib import Path
import shutil
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from uuid import uuid4

from openai import APIConnectionError, APIStatusError

from lab import sft
from lab.batch import score_run
from lab.config import LabError, load_config
from lab.files import read_json, read_jsonl, sha256_file, write_jsonl
from lab.preflight import save_json
from scripts.build_datasets import render_user_message


ROOT = Path(__file__).resolve().parents[1]
ANSWER = '{"answer":"MOCK 답변","citations":["DOC"],"route":"answer","needs_human":false}'
TUNED_MODEL = f"{sft.BASE_MODEL}.ft-mock-training-job"


def connection_error():
    return APIConnectionError(request=SimpleNamespace(url="https://example.invalid/mock"))


def rejected_error():
    return APIStatusError(
        "MOCK rejected",
        response=SimpleNamespace(
            status_code=400, request=SimpleNamespace(url="https://example.invalid/mock"),
            headers={"x-request-id": "mock-request"},
        ),
        body={"error": {"code": "MockBadRequest", "message": "mock rejection"}},
    )


def completion(*, content=ANSWER, finish_reason="stop", refusal=None):
    return {
        "id": "chatcmpl-mock", "model": "mock-model",
        "choices": [{"message": {"content": content, "refusal": refusal}, "finish_reason": finish_reason}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
    }


class SftTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config(ROOT / ".env.example")
        self.relative = Path("tests") / f".sft-fixture-{uuid4().hex}"
        self.relative.mkdir()
        self.root = self.relative.resolve()
        self.addCleanup(shutil.rmtree, self.relative)
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(redirect_stdout(io.StringIO()))
        for name, value in (
            ("lab.sft.ROOT", self.root), ("lab.sft.ARTIFACTS", self.root / "artifacts"),
            ("lab.files.ARTIFACTS", self.root / "artifacts"), ("lab.batch.ROOT", self.root),
        ):
            self.stack.enter_context(patch(name, value))
        self.validation = self.stack.enter_context(patch("lab.sft.validate_generated_data"))
        self.auth = self.stack.enter_context(patch("lab.sft.credential_for"))
        self.stack.enter_context(patch("lab.sft.require_owned_scope"))
        self.project_class = self.stack.enter_context(patch("lab.sft.AIProjectClient"))
        self.credential = self.auth.return_value.__enter__.return_value
        self.project = self.project_class.return_value.__enter__.return_value
        self.client = self.project.get_openai_client.return_value.__enter__.return_value
        self.arm = self.stack.enter_context(patch("lab.sft.az_json", side_effect=self.arm_response))
        self.client.files.create.side_effect = self.file_upload
        self.client.files.retrieve.side_effect = self.file_response
        self.client.fine_tuning.jobs.create.side_effect = self.job_create
        self.client.fine_tuning.jobs.retrieve.return_value = self.job_response("succeeded")
        self.client.fine_tuning.jobs.cancel.return_value = self.job_response("cancelled")
        self.client.chat.completions.create.return_value = completion()
        self.directory = self.root / "artifacts/tuning/sft"
        self.directory.mkdir(parents=True)
        (self.root / "prompts").mkdir()
        (self.root / "prompts/tuning-system.txt").write_text("MOCK_SYSTEM\n", encoding="utf-8")
        save_json(self.root / "data/knowledge/documents.json", [
            {"id": "DOC", "title": "MOCK policy", "content": "MOCK reference", "effective_date": "2026-09-01"},
        ])
        manifest = {
            "kind": "sft-preparation", "status": "PREPARED_NOT_SUBMITTED",
            "region_requested": "northcentralus", "test_data_included": False, "files": {},
        }
        for split, count in (("train", 56), ("validation", 12), ("dev", 12), ("test", 20)):
            cases = [{
                "id": f"mock-{split}-{i}", "group_id": f"mock-{split}-{i}", "split": split,
                "query": f"MOCK {split} query {i}", "context": "[DOC]\nMOCK reference",
                "ground_truth": ANSWER, "expected_route": "answer",
                "required_citations": ["DOC"], "tags": ["fixture"],
            } for i in range(count)]
            write_jsonl(self.root / "data/splits" / f"{split}.jsonl", cases)
            if split not in ("train", "validation"):
                continue
            rows = [{
                "messages": sft.model_messages(case, "MOCK_SYSTEM") + [{"role": "assistant", "content": ANSWER}],
            } for case in cases]
            name = f"sft-{split}.jsonl"
            source = self.root / "data/tuning" / name
            write_jsonl(source, rows)
            target = self.directory / name
            target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8-sig")
            manifest["files"][name] = {"rows": count, "bytes": target.stat().st_size, "sha256": sha256_file(target)}
        save_json(self.directory / "manifest.json", manifest)

    def state(self):
        return read_json(self.directory / sft.STATE_FILE)

    def file_response(self, file_id):
        split = file_id.removeprefix("file-")
        return {
            "id": file_id, "purpose": "fine-tune", "status": "processed",
            "bytes": (self.directory / f"sft-{split}.jsonl").stat().st_size,
            "filename": f"sft-{split}.jsonl",
        }

    def file_upload(self, *, file, purpose):
        self.assertEqual(purpose, "fine-tune")
        self.assertTrue(file.read().startswith(b"\xef\xbb\xbf"))
        split = "validation" if "validation" in file.name else "train"
        persisted = self.state()
        self.assertEqual(persisted["files"][split]["phase"], "uploading")
        if split == "validation":
            self.assertEqual(persisted["files"]["train"]["id"], "file-train")
        return self.file_response(f"file-{split}")

    def job_response(self, status="queued", **overrides):
        return {
            "id": "ftjob-mock", "model": sft.BASE_MODEL, "status": status,
            "training_file": "file-train", "validation_file": "file-validation",
            "seed": 105, "method": {"type": "supervised", "supervised": {"hyperparameters": {"n_epochs": 1}}},
            "trainingType": "Standard", "fine_tuned_model": TUNED_MODEL if status == "succeeded" else None,
            "result_files": ["file-mock-results"] if status == "succeeded" else [],
            **overrides,
        }

    def job_create(self, **kwargs):
        self.assertEqual(self.state()["job"]["phase"], "submitting")
        self.assertEqual(self.state()["job"]["request"], kwargs)
        self.assertEqual(self.state()["baseline"]["phase"], "completed")
        self.assertEqual(self.state()["job"]["baseline_run_id"], self.state()["baseline"]["run_id"])
        return self.job_response()

    def arm_response(self, args):
        if args[:3] == ["cognitiveservices", "account", "show"]:
            return {"id": self.config.account_id, "location": "northcentralus"}
        self.assertEqual(args[:4], ["cognitiveservices", "account", "deployment", "show"])
        self.assertIn(self.config.subscription_id, args)
        self.assertIn(self.config.resource_group, args)
        self.assertIn(self.config.account, args)
        name = args[args.index("--deployment-name") + 1]
        base = name == "mock-base"
        return {
            "id": f"{self.config.account_id}/deployments/{name}", "name": name,
            "sku": {"name": "Standard", "capacity": 1},
            "properties": {
                "provisioningState": "Succeeded",
                "model": {
                    "format": "OpenAI", "name": "gpt-4.1-mini" if base else TUNED_MODEL,
                    "version": "2025-04-14" if base else "1",
                },
            },
        }

    def baseline(self, run_id="mock-pretrain"):
        return sft.run_baseline(self.config, "mock-base", run_id, confirm=True)

    def prepare_submission(self):
        self.baseline()
        sft.upload_files(self.config, confirm=True)
        self.client.chat.completions.create.reset_mock()
        self.arm.reset_mock()

    def prime_job(self):
        self.prepare_submission()
        sft.submit_job(self.config, confirm=True)
        self.arm.reset_mock()

    def run_pair(self, prefix="mock-dev"):
        return sft.run_pair(self.config, "mock-base", "mock-tuned", "dev", prefix, confirm=True)

    def test_cli_help_and_confirmation_do_not_need_credentials(self):
        self.assertIn("NOT Frontier Tuning", sft.parser().format_help())
        for command in ("baseline", "upload", "submit", "cancel", "run-pair"):
            args = ["--config", "nonexistent-config", command]
            if command == "baseline":
                args += ["--base-deployment", "mock-base", "--run-id", "mock-pretrain"]
            elif command == "run-pair":
                args += ["--base-deployment", "mock-base", "--tuned-deployment", "mock-tuned",
                         "--split", "dev", "--run-prefix", "mock"]
            stderr = io.StringIO()
            with self.subTest(command=command), redirect_stderr(stderr):
                self.assertEqual(sft.main(args), 1)
            self.assertIn("--confirm", stderr.getvalue())
        self.auth.assert_not_called()
        self.assertFalse((self.directory / sft.STATE_FILE).exists())

    def test_public_mutations_also_require_confirmation(self):
        for function in (sft.upload_files, sft.submit_job, sft.cancel_job):
            with self.subTest(function=function.__name__), self.assertRaises(LabError):
                function(self.config)
        with self.assertRaises(LabError):
            sft.run_pair(self.config, "mock-base", "mock-tuned", "dev", "mock")
        with self.assertRaises(LabError):
            sft.run_baseline(self.config, "mock-base", "mock-pretrain")
        self.auth.assert_not_called()

    def test_baseline_captures_only_full_dev_without_labels_and_locally_scores(self):
        state = self.baseline()
        self.assertEqual(state["baseline"]["phase"], "completed")
        self.assertEqual(state["job"]["phase"], "not_submitted")
        self.client.files.create.assert_not_called()
        self.client.fine_tuning.jobs.create.assert_not_called()
        self.auth.assert_called_once_with(self.config)
        requests = [call.kwargs for call in self.client.chat.completions.create.call_args_list]
        cases = read_jsonl(self.root / "data/splits/dev.jsonl")
        self.assertEqual(len(requests), 12)
        for case, request in zip(cases, requests, strict=True):
            self.assertEqual(request["model"], "mock-base")
            self.assertEqual(request["messages"][0], {"role": "system", "content": "MOCK_SYSTEM"})
            user = request["messages"][1]["content"]
            self.assertEqual(user, render_user_message(case))
            self.assertEqual(set(json.loads(user)), {"query", "context"})
            self.assertNotIn("MOCK 답변", user)
            self.assertNotIn("expected_route", user)
            self.assertNotIn("MOCK test", user)
        directory = self.root / "artifacts/runs/mock-pretrain"
        metadata = read_json(directory / "metadata.json")
        self.assertIsNone(metadata["training_job_id"])
        self.assertEqual(metadata["experiment_phase"], "pretraining-baseline")
        self.assertEqual(metadata["target_type"], "model")
        self.assertEqual(metadata["technique"], "Foundry SFT")
        self.assertEqual(metadata["row_ids"], [case["id"] for case in cases])
        summary = read_json(directory / "summary.json")
        self.assertEqual(len(summary["rows"]), 12)
        self.assertTrue((directory / "report.md").is_file())
        score_run("mock-pretrain")
        self.assertEqual(sft._baseline_evidence(self.state())["run_id"], "mock-pretrain")

    def test_baseline_rejects_wrong_model_and_sku_before_paid_capture(self):
        for mismatch in ("model", "sku"):
            def arm(args):
                result = self.arm_response(args)
                if args[:4] == ["cognitiveservices", "account", "deployment", "show"]:
                    if mismatch == "model":
                        result["properties"]["model"]["version"] = "wrong-version"
                    else:
                        result["sku"]["name"] = "GlobalStandard"
                return result

            self.arm.side_effect = arm
            with self.subTest(mismatch=mismatch), self.assertRaises(LabError):
                self.baseline(run_id=f"mock-pretrain-{mismatch}")
        self.client.chat.completions.create.assert_not_called()
        self.assertFalse((self.directory / sft.STATE_FILE).exists())

    def test_baseline_cannot_overwrite_or_run_after_training_request(self):
        self.prime_job()
        for run_id in ("mock-pretrain", "mock-too-late"):
            with self.subTest(run_id=run_id), self.assertRaises(LabError):
                self.baseline(run_id=run_id)
        self.client.chat.completions.create.assert_not_called()

    def test_baseline_requires_all_twelve_dev_rows_not_a_partial_or_test_split(self):
        path = self.root / "data/splits/dev.jsonl"
        rows = read_jsonl(path)
        for invalid in (rows[:11], [{**case, "split": "test"} for case in rows]):
            write_jsonl(path, invalid)
            with self.subTest(rows=len(invalid)), self.assertRaises(LabError):
                self.baseline()
        self.auth.assert_not_called()
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            sft.parser().parse_args([
                "baseline", "--base-deployment", "mock-base", "--run-id", "mock", "--split", "test",
            ])

    def test_submit_requires_a_recorded_pretraining_baseline_before_cloud_reads(self):
        sft.upload_files(self.config, confirm=True)
        self.auth.reset_mock()
        with self.assertRaisesRegex(LabError, "baseline"):
            sft.submit_job(self.config, confirm=True)
        self.auth.assert_not_called()
        self.client.files.retrieve.assert_not_called()
        self.client.fine_tuning.jobs.create.assert_not_called()

    def test_submit_blocks_missing_and_tampered_baseline_artifacts(self):
        self.prepare_submission()
        self.auth.reset_mock()
        directory = self.root / "artifacts/runs/mock-pretrain"
        for name in (*sft.BASELINE_ARTIFACTS, "raw/mock-dev-0.json"):
            path = directory / name
            original = path.read_bytes()
            for change in ("missing", "tampered"):
                with self.subTest(name=name, change=change):
                    if change == "missing":
                        path.unlink()
                    else:
                        path.write_bytes(original + b"\nMOCK TAMPER")
                    with self.assertRaises(LabError):
                        sft.submit_job(self.config, confirm=True)
                    path.write_bytes(original)
        self.auth.assert_not_called()
        self.client.fine_tuning.jobs.create.assert_not_called()

    def test_submit_blocks_stale_dev_data_and_prompt(self):
        self.prepare_submission()
        self.auth.reset_mock()
        for relative in ("data/splits/dev.jsonl", "prompts/tuning-system.txt"):
            path = self.root / relative
            original = path.read_bytes()
            if relative.endswith(".jsonl"):
                rows = read_jsonl(path)
                rows[0]["query"] = "MOCK changed dev input"
                write_jsonl(path, rows)
            else:
                path.write_text("MOCK changed system", encoding="utf-8")
            with self.subTest(path=relative), self.assertRaises(LabError):
                sft.submit_job(self.config, confirm=True)
            path.write_bytes(original)
        self.auth.assert_not_called()
        self.client.fine_tuning.jobs.create.assert_not_called()

    def test_submit_revalidates_live_baseline_deployment_settings(self):
        self.prepare_submission()
        for mismatch in ("capacity", "rai_policy", "upgrade_policy", "model"):
            def arm(args):
                result = self.arm_response(args)
                if args[:4] == ["cognitiveservices", "account", "deployment", "show"]:
                    if mismatch == "capacity":
                        result["sku"]["capacity"] = 2
                    elif mismatch == "rai_policy":
                        result["properties"]["raiPolicyName"] = "MOCK changed policy"
                    elif mismatch == "upgrade_policy":
                        result["properties"]["versionUpgradeOption"] = "OnceNewDefaultVersionAvailable"
                    else:
                        result["properties"]["model"]["version"] = "MOCK wrong version"
                return result

            self.arm.side_effect = arm
            with self.subTest(mismatch=mismatch), self.assertRaises(LabError):
                sft.submit_job(self.config, confirm=True)
            self.assertEqual(self.state()["job"]["phase"], "not_submitted")
        self.client.fine_tuning.jobs.create.assert_not_called()

    def test_posttraining_or_test_metadata_cannot_be_adopted_as_baseline(self):
        self.prepare_submission()
        self.auth.reset_mock()
        path = self.root / "artifacts/runs/mock-pretrain/metadata.json"
        original = read_json(path)
        for changes in (
            {"experiment_phase": "posttraining-pair"},
            {"training_job_id": "ftjob-mock"},
            {"split": "test", "source_split": "test"},
        ):
            save_json(path, {**original, **changes})
            state = self.state()
            state["baseline"]["artifacts_sha256"]["metadata.json"] = sha256_file(path)
            sft._persist(state)
            with self.subTest(changes=changes), self.assertRaises(LabError):
                sft.submit_job(self.config, confirm=True)
        self.auth.assert_not_called()
        self.client.fine_tuning.jobs.create.assert_not_called()

    def test_interrupted_baseline_blocks_submit_but_new_explicit_run_keeps_history(self):
        self.client.chat.completions.create.side_effect = [completion(), KeyboardInterrupt()]
        with self.assertRaises(KeyboardInterrupt):
            self.baseline()
        self.assertEqual(self.state()["baseline"]["phase"], "interrupted")
        sft.upload_files(self.config, confirm=True)
        with self.assertRaises(LabError):
            sft.submit_job(self.config, confirm=True)
        self.client.fine_tuning.jobs.create.assert_not_called()
        self.client.chat.completions.create.side_effect = None
        self.baseline("mock-pretrain-retry")
        state = self.state()
        self.assertEqual(state["baseline_history"][0]["run_id"], "mock-pretrain")
        self.assertEqual(state["baseline_history"][0]["phase"], "interrupted")
        self.assertEqual(state["baseline"]["run_id"], "mock-pretrain-retry")
        sft.submit_job(self.config, confirm=True)
        self.assertEqual(self.state()["job"]["baseline_run_id"], "mock-pretrain-retry")

    def test_baseline_failures_and_zero_quality_do_not_require_a_high_score_to_train(self):
        self.client.chat.completions.create.side_effect = [
            connection_error(), *[completion(content="MOCK non-JSON answer") for _ in range(11)],
        ]
        self.baseline()
        self.assertEqual(self.state()["baseline"]["status"], "completed_with_errors")
        summary = read_json(self.root / "artifacts/runs/mock-pretrain/summary.json")
        self.assertEqual(len(summary["rows"]), 12)
        self.assertEqual(summary["metrics"]["route_accuracy"], 0.0)
        sft.upload_files(self.config, confirm=True)
        sft.submit_job(self.config, confirm=True)
        self.client.fine_tuning.jobs.create.assert_called_once()

    def test_status_before_upload_does_not_create_state_or_contact_cloud(self):
        summary = sft.status_summary(sft.job_status(self.config))
        self.assertEqual(summary["workflow_status"], "PREPARED_NOT_SUBMITTED")
        self.assertIsNone(summary["job_id"])
        self.assertNotIn("fine_tuned_model", summary)
        self.assertFalse((self.directory / sft.STATE_FILE).exists())
        self.auth.assert_not_called()

    def test_upload_uses_verified_token_helper_and_persists_each_id_once(self):
        original_manifest = (self.directory / "manifest.json").read_bytes()
        state = sft.upload_files(self.config, confirm=True)
        sft.upload_files(self.config, confirm=True)
        self.assertEqual(self.client.files.create.call_count, 2)
        self.auth.assert_called_once_with(self.config)
        self.project_class.assert_called_once_with(endpoint=self.config.project_endpoint, credential=self.credential)
        self.project.get_openai_client.assert_called_once_with(max_retries=0, timeout=120.0)
        self.assertEqual(state["files"]["validation"]["id"], "file-validation")
        self.assertEqual(original_manifest, (self.directory / "manifest.json").read_bytes())
        self.assertFalse((self.directory / "operation.lock").exists())

    def test_known_partial_upload_failure_reuses_first_file(self):
        attempts = []

        def upload(**kwargs):
            attempts.append(Path(kwargs["file"].name).name)
            if len(attempts) == 2:
                raise rejected_error()
            return self.file_upload(**kwargs)

        self.client.files.create.side_effect = upload
        with self.assertRaises(LabError):
            sft.upload_files(self.config, confirm=True)
        state = self.state()
        self.assertEqual(state["files"]["train"]["id"], "file-train")
        self.assertEqual(state["files"]["validation"]["phase"], "rejected")
        sft.upload_files(self.config, confirm=True)
        self.assertEqual(attempts, ["sft-train.jsonl", "sft-validation.jsonl", "sft-validation.jsonl"])

    def test_ambiguous_upload_is_not_retried(self):
        self.client.files.create.side_effect = [self.file_response("file-train"), connection_error()]
        with self.assertRaises(LabError):
            sft.upload_files(self.config, confirm=True)
        self.assertEqual(self.state()["files"]["train"]["id"], "file-train")
        self.assertEqual(self.state()["files"]["validation"]["phase"], "unknown")
        with self.assertRaises(LabError):
            sft.upload_files(self.config, confirm=True)
        self.assertEqual(self.client.files.create.call_count, 2)

    def test_bom_hash_and_split_integrity_block_upload(self):
        path = self.directory / "sft-train.jsonl"
        path.write_text(path.read_text(encoding="utf-8-sig"), encoding="utf-8")
        with self.assertRaises(LabError):
            sft.upload_files(self.config, confirm=True)
        self.auth.assert_not_called()

    def test_prepared_holdout_substitution_is_rejected_even_with_updated_hash(self):
        source = self.root / "data/tuning/sft-train.jsonl"
        rows = read_jsonl(source)
        rows[0]["messages"][1]["content"] = '{"context":"MOCK reference","query":"MOCK test query 0"}'
        write_jsonl(source, rows)
        target = self.directory / source.name
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8-sig")
        manifest = read_json(self.directory / "manifest.json")
        manifest["files"][source.name].update(bytes=target.stat().st_size, sha256=sha256_file(target))
        save_json(self.directory / "manifest.json", manifest)
        with self.assertRaises(LabError):
            sft.upload_files(self.config, confirm=True)
        self.auth.assert_not_called()

    def test_namespace_mismatch_stops_before_cloud_reads_or_mutations(self):
        sft.upload_files(self.config, confirm=True)
        self.auth.reset_mock()
        for config in (
            replace(self.config, prefix="different-prefix"),
            replace(self.config, project="other", project_endpoint=f"https://{self.config.account}.services.ai.azure.com/api/projects/other"),
            replace(self.config, tenant_id="11111111-1111-1111-1111-111111111111"),
        ):
            with self.subTest(config=config.prefix), self.assertRaises(LabError):
                sft.job_status(config)
        self.auth.assert_not_called()

    def test_operation_lock_blocks_concurrent_submission(self):
        (self.directory / "operation.lock").write_text("MOCK other process", encoding="utf-8")
        with self.assertRaises(LabError):
            sft.upload_files(self.config, confirm=True)
        self.client.files.create.assert_not_called()

    def test_both_files_must_be_processed_before_submit(self):
        self.prepare_submission()
        for status in ("uploaded", "error"):
            def retrieve(file_id):
                result = self.file_response(file_id)
                if file_id == "file-validation":
                    result["status"] = status
                return result

            self.client.files.retrieve.side_effect = retrieve
            with self.subTest(status=status), self.assertRaises(LabError):
                sft.submit_job(self.config, confirm=True)
            self.assertEqual(self.state()["job"]["phase"], "not_submitted")
        self.client.fine_tuning.jobs.create.assert_not_called()
        self.assertEqual(self.client.files.retrieve.call_count, 4)

    def test_submission_contract_is_standard_supervised_one_epoch_and_once(self):
        self.prime_job()
        self.client.fine_tuning.jobs.create.assert_called_once_with(
            model="gpt-4.1-mini-2025-04-14", training_file="file-train", validation_file="file-validation",
            seed=105, method={"type": "supervised", "supervised": {"hyperparameters": {"n_epochs": 1}}},
            extra_body={"trainingType": "Standard"},
        )
        self.assertEqual(self.state()["job"]["id"], "ftjob-mock")
        with self.assertRaises(LabError):
            sft.submit_job(self.config, confirm=True)
        self.assertEqual(self.client.fine_tuning.jobs.create.call_count, 1)

    def test_unknown_submission_never_reposts_or_claims_a_model(self):
        self.prepare_submission()
        self.client.fine_tuning.jobs.create.side_effect = connection_error()
        with self.assertRaises(LabError):
            sft.submit_job(self.config, confirm=True)
        self.assertEqual(self.state()["job"]["phase"], "submission_unknown")
        with self.assertRaises(LabError):
            sft.submit_job(self.config, confirm=True)
        result = sft.status_summary(sft.job_status(self.config))
        self.assertIsNone(result["actual_status"])
        self.assertNotIn("fine_tuned_model", result)
        self.assertEqual(self.client.fine_tuning.jobs.create.call_count, 1)
        self.client.fine_tuning.jobs.retrieve.assert_not_called()

    def test_interrupted_submission_retains_pre_request_guard(self):
        self.prepare_submission()
        self.client.fine_tuning.jobs.create.side_effect = KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            sft.submit_job(self.config, confirm=True)
        self.assertEqual(self.state()["job"]["phase"], "submitting")
        self.assertFalse((self.directory / "operation.lock").exists())
        with self.assertRaises(LabError):
            sft.submit_job(self.config, confirm=True)
        self.assertEqual(self.client.fine_tuning.jobs.create.call_count, 1)

    def test_rejected_submission_keeps_raw_error_and_never_falls_back(self):
        self.prepare_submission()
        self.client.fine_tuning.jobs.create.side_effect = rejected_error()
        with self.assertRaises(LabError):
            sft.submit_job(self.config, confirm=True)
        state = self.state()
        self.assertEqual(state["job"]["phase"], "submission_rejected")
        self.assertEqual(state["job"]["error"]["body"]["error"]["code"], "MockBadRequest")
        self.assertEqual(state["job"]["request"]["extra_body"], {"trainingType": "Standard"})
        with self.assertRaises(LabError):
            sft.submit_job(self.config, confirm=True)
        self.assertEqual(self.client.fine_tuning.jobs.create.call_count, 1)

    def test_status_is_bounded_and_reports_only_actual_success_model(self):
        self.prime_job()
        self.client.fine_tuning.jobs.retrieve.return_value = self.job_response("failed", fine_tuned_model="MOCK premature model")
        summary = sft.status_summary(sft.job_status(self.config))
        self.assertEqual(summary["actual_status"], "failed")
        self.assertTrue(summary["terminal_verified_by_retrieve"])
        self.assertNotIn("fine_tuned_model", summary)
        self.assertIsNone(self.state()["job"]["fine_tuned_model"])
        self.client.fine_tuning.jobs.retrieve.assert_called_once_with("ftjob-mock")
        self.client.fine_tuning.jobs.retrieve.return_value = self.job_response("succeeded")
        summary = sft.status_summary(sft.job_status(self.config))
        self.assertEqual(summary["fine_tuned_model"], TUNED_MODEL)
        self.assertEqual(self.client.fine_tuning.jobs.create.call_count, 1)

    def test_success_without_model_id_is_recorded_but_cannot_run(self):
        self.prime_job()
        self.client.fine_tuning.jobs.retrieve.return_value = self.job_response("succeeded", fine_tuned_model=None)
        with self.assertRaises(LabError):
            sft.job_status(self.config)
        self.assertEqual(self.state()["job"]["status"], "succeeded")
        self.assertIsNone(self.state()["job"]["fine_tuned_model"])
        with self.assertRaises(LabError):
            self.run_pair()
        self.client.chat.completions.create.assert_not_called()

    def test_remote_job_file_or_training_type_mismatch_blocks_use(self):
        self.prime_job()
        for overrides in ({"training_file": "file-unrelated"}, {"trainingType": "GlobalStandard"}):
            self.client.fine_tuning.jobs.retrieve.return_value = self.job_response("running", **overrides)
            with self.subTest(overrides=overrides), self.assertRaises(LabError):
                sft.cancel_job(self.config, confirm=True)
        self.client.fine_tuning.jobs.cancel.assert_not_called()

    def test_cancel_scopes_recorded_job_and_requires_separate_terminal_read(self):
        self.prime_job()
        self.client.fine_tuning.jobs.retrieve.return_value = self.job_response("running")
        result = sft.cancel_job(self.config, confirm=True)
        self.client.fine_tuning.jobs.cancel.assert_called_once_with("ftjob-mock")
        self.assertFalse(result["job"]["terminal_verified"])
        self.assertEqual(result["job"]["cancellation"]["phase"], "requested")
        with self.assertRaises(LabError):
            sft.cancel_job(self.config, confirm=True)
        self.client.fine_tuning.jobs.retrieve.return_value = self.job_response("cancelled")
        self.assertTrue(sft.job_status(self.config)["job"]["terminal_verified"])
        self.assertEqual(self.client.fine_tuning.jobs.cancel.call_count, 1)

    def test_terminal_job_is_not_cancelled_again(self):
        self.prime_job()
        sft.cancel_job(self.config, confirm=True)
        self.client.fine_tuning.jobs.cancel.assert_not_called()

    def test_uncertain_cancel_is_preserved_without_automatic_retry(self):
        self.prime_job()
        self.client.fine_tuning.jobs.retrieve.return_value = self.job_response("running")
        self.client.fine_tuning.jobs.cancel.side_effect = connection_error()
        with self.assertRaises(LabError):
            sft.cancel_job(self.config, confirm=True)
        self.assertEqual(self.state()["job"]["cancellation"]["phase"], "unknown")
        with self.assertRaises(LabError):
            sft.cancel_job(self.config, confirm=True)
        self.assertEqual(self.client.fine_tuning.jobs.cancel.call_count, 1)

    def test_pair_matches_training_input_excludes_labels_and_exports_scoreable_evidence(self):
        self.prime_job()
        metadata = self.run_pair()
        requests = [call.kwargs for call in self.client.chat.completions.create.call_args_list]
        self.assertEqual([request["model"] for request in requests], ["mock-base", "mock-tuned"] * 12)
        cases = read_jsonl(self.root / "data/splits/dev.jsonl")
        for i, case in enumerate(cases):
            self.assertEqual(requests[2 * i]["messages"], requests[2 * i + 1]["messages"])
            user = requests[2 * i]["messages"][1]["content"]
            self.assertEqual(user, render_user_message(case))
            self.assertEqual(set(json.loads(user)), {"query", "context"})
            self.assertNotIn("MOCK 답변", user)
            self.assertNotIn("expected_route", user)
            self.assertEqual(requests[2 * i]["messages"][0]["content"], "MOCK_SYSTEM")
        for arm, stage in (("base", "candidate"), ("tuned", "tuned")):
            info = metadata[arm]
            self.assertEqual(info["stage"], stage)
            self.assertEqual(info["target_type"], "model")
            self.assertEqual(info["technique"], "Foundry SFT")
            self.assertEqual(info["source_split"], "dev")
            self.assertIsNone(info["judge"])
            self.assertEqual(info["status"], "completed")
            directory = self.root / "artifacts/runs" / info["run_id"]
            exported = read_jsonl(directory / "foundry-eval.jsonl")
            self.assertEqual(exported[0]["response"], "MOCK 답변")
            self.assertEqual(exported[0]["retrieved_context"], "")
            self.assertEqual(sha256_file(self.root / info["prompt_snapshot"]), info["prompt_sha256"])
            summary = score_run(info["run_id"])
            self.assertEqual(len(summary["rows"]), 12)
            self.assertEqual(summary["metrics"]["route_accuracy"], 1.0)
        self.assertEqual(metadata["base"]["parameters"], metadata["tuned"]["parameters"])
        self.assertEqual(metadata["base"]["dataset_sha256"], metadata["tuned"]["dataset_sha256"])

    def test_pair_preserves_api_errors_in_original_denominator(self):
        self.prime_job()
        self.client.chat.completions.create.side_effect = [connection_error(), *[completion() for _ in range(23)]]
        metadata = self.run_pair()
        self.assertEqual(metadata["base"]["status"], "completed_with_errors")
        directory = self.root / "artifacts/runs/mock-dev-base"
        rows = read_jsonl(directory / "outputs.jsonl")
        self.assertEqual(len(rows), 12)
        self.assertEqual(rows[0]["error_details"]["type"], "APIConnectionError")
        self.assertIsNone(rows[0]["response"])
        self.assertEqual(rows[0]["raw_output"], "")
        self.assertEqual(len(read_jsonl(directory / "foundry-eval.jsonl")), 11)
        summary = score_run("mock-dev-base")
        self.assertEqual(len(summary["rows"]), 12)
        self.assertEqual(summary["metrics"]["route_accuracy"], 11 / 12)
        self.assertEqual(self.client.chat.completions.create.call_count, 24)

    def test_pair_never_overwrites_either_arm(self):
        self.prime_job()
        self.run_pair()
        with self.assertRaises(LabError):
            self.run_pair()
        self.assertEqual(self.client.chat.completions.create.call_count, 24)

    def test_pair_checks_account_base_tuned_and_standard_sku_before_inference(self):
        self.prime_job()
        for mismatch in ("account", "base", "tuned", "sku"):
            def arm(args):
                result = deepcopy(self.arm_response(args))
                if args[:3] == ["cognitiveservices", "account", "show"]:
                    return result
                if mismatch == "account":
                    result["id"] = result["id"].replace(self.config.account, "unrelated-account")
                elif mismatch == "base" and result["name"] == "mock-base":
                    result["properties"]["model"] = {"format": "OpenAI", "name": "gpt-6", "version": "mock"}
                elif mismatch == "tuned" and result["name"] == "mock-tuned":
                    result["properties"]["model"]["name"] = "unrelated-fine-tuned-model"
                elif mismatch == "sku":
                    result["sku"]["name"] = "GlobalStandard"
                return result

            self.arm.side_effect = arm
            with self.subTest(mismatch=mismatch), self.assertRaises(LabError):
                self.run_pair(prefix=f"mock-{mismatch}")
        self.client.chat.completions.create.assert_not_called()

    def test_pair_requires_live_succeeded_job_not_just_stale_local_model(self):
        self.prime_job()
        self.client.fine_tuning.jobs.retrieve.return_value = self.job_response("failed")
        with self.assertRaises(LabError):
            self.run_pair()
        self.client.chat.completions.create.assert_not_called()
        self.arm.assert_not_called()

    def test_pair_rejects_train_split_and_same_deployment_without_cloud_calls(self):
        for split, tuned in (("train", "mock-tuned"), ("dev", "mock-base")):
            with self.subTest(split=split, tuned=tuned), self.assertRaises(LabError):
                sft.run_pair(self.config, "mock-base", tuned, split, "mock", confirm=True)
        self.auth.assert_not_called()

    def test_incomplete_refused_or_empty_completions_are_failures_without_fallback(self):
        case = read_jsonl(self.root / "data/splits/dev.jsonl")[0]
        for response in (
            completion(content="MOCK partial", finish_reason="length"),
            completion(content=None, refusal="MOCK refusal"), completion(content=""),
        ):
            self.client.chat.completions.create.return_value = response
            with self.subTest(response=response):
                record = sft.capture_model(self.client, "mock-base", case, "MOCK_SYSTEM")
                self.assertTrue(record["error"])
                self.assertEqual(record["response"], response)
        self.assertEqual(self.client.chat.completions.create.call_count, 3)


if __name__ == "__main__":
    unittest.main()
