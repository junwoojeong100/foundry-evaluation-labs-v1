from contextlib import nullcontext, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import shutil
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

from lab.batch import capture_case, export_evaluation, response_context, retrieval_observation, run_batch, score_run
from lab.config import LabError
from lab.files import ROOT, read_jsonl


class ResponseStub:
    id = "resp_test_fixture"
    output_text = '{"answer":"test fixture","route":"answer","citations":[],"needs_human":false}'

    def model_dump(self, **kwargs):
        return {
            "id": self.id, "status": "completed", "output": [],
            "usage": {"input_tokens": 10, "output_tokens": 20, "total_tokens": 30},
        }


class BatchTests(unittest.TestCase):
    def test_agent_input_contains_no_answer_key(self):
        requests = []

        def create(**kwargs):
            requests.append(kwargs)
            return ResponseStub()

        client = SimpleNamespace(responses=SimpleNamespace(create=create))
        case = {
            "id": "fixture-001", "query": "What is allowed?",
            "ground_truth": "SECRET_TEST_ANSWER_KEY", "expected_route": "answer",
        }
        result = capture_case(client, {"name": "fixture-agent", "version": "7", "workspace_id": "fixture-workspace"}, case)
        self.assertEqual(requests[0]["input"], case["query"])
        self.assertNotIn("SECRET_TEST_ANSWER_KEY", str(requests[0]))
        self.assertEqual(requests[0]["extra_body"]["agent_reference"]["version"], "7")
        self.assertIsNone(result["error"])

    def test_only_actual_mcp_output_is_retrieved_context(self):
        payload = {"output": [
            {"type": "message", "output": "not retrieved"},
            {"type": "mcp_call", "name": "knowledge_base_retrieve", "output": "actual tool fixture"},
        ]}
        self.assertEqual(response_context(payload), "actual tool fixture")
        self.assertEqual(response_context({"output": []}), "")

    def test_failed_or_unrelated_tool_output_cannot_become_retrieved_context(self):
        payload = {"output": [
            {"type": "mcp_call", "name": "knowledge_base_retrieve", "output": '{"isError":true,"content":"policy fallback"}'},
            {"type": "mcp_call", "name": "knowledge_base_retrieve", "output": "denied", "error": "403"},
            {"type": "mcp_call", "name": "send_email", "output": "not retrieval"},
            {"type": "mcp_call", "output": "unnamed tool is not identified retrieval"},
        ]}
        self.assertEqual(response_context(payload), "")

    def test_export_rejects_misaligned_rows(self):
        from pathlib import Path

        with self.assertRaises(LabError):
            export_evaluation(Path("unused"), [{"id": "a"}], [{"id": "b"}])

    def test_no_tool_call_is_not_reported_as_retrieval_success(self):
        result = retrieval_observation([{"id": "a", "response": {"output": []}}])
        self.assertEqual(result["rows_with_tool_output"], 0)

    def test_mcp_error_payload_is_not_a_successful_search(self):
        result = retrieval_observation([{
            "id": "a",
            "response": {"output": [{
                "type": "mcp_call", "name": "knowledge_base_retrieve", "error": None,
                "output": '{"isError":true,"content":[{"type":"text","text":"forbidden"}]}',
            }]},
        }])
        self.assertEqual(result["tool_error_calls"], 1)
        self.assertEqual(result["rows_with_tool_output"], 0)

    def test_real_tool_output_is_counted_separately(self):
        result = retrieval_observation([{
            "id": "a",
            "response": {"output": [{
                "type": "mcp_call", "name": "knowledge_base_retrieve",
                "output": '[{"content":"synthetic policy","ref_id":"0"}]',
            }]},
        }])
        self.assertEqual(result["rows_with_tool_output"], 1)
        self.assertEqual(result["row_ids_with_tool_output"], ["a"])


class BatchRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.root = Path("artifacts") / f"test-batch-{uuid4().hex}"
        self.root.mkdir(parents=True)
        self.addCleanup(shutil.rmtree, self.root)
        self.patch("lab.files.ARTIFACTS", self.root)
        self.cases = read_jsonl(ROOT / "data/splits/dev.jsonl")
        self.config = SimpleNamespace(project_endpoint="https://mock.invalid/project")
        self.snapshot = {"model": {"name": "unit-only-model", "version": "1"}}
        self.agent = {
            "name": "mock-agent", "version": "1", "workspace_id": "mock-workspace",
            "model_deployment": "unit-only-model", "model_snapshot": self.snapshot,
            "prompt_sha256": "a" * 64, "prompt_source": "unit-test-only",
            "prompt_snapshot": "prompts/baseline.txt",
            "knowledge_sha256": hashlib.sha256(b"").hexdigest(),
        }
        self.load = self.patch("lab.batch.load_agent", return_value=self.agent)
        self.auth = self.patch("lab.batch.credential_for", return_value=nullcontext("mock-credential"))
        self.model = self.patch("lab.batch.model_snapshot", return_value=self.snapshot)
        self.client = SimpleNamespace(responses=SimpleNamespace(
            create=Mock(side_effect=lambda **kwargs: self.response(kwargs["metadata"]["lab_case"])),
            retrieve=Mock(),
        ))
        self.project = SimpleNamespace(
            agents=SimpleNamespace(get_version=Mock(return_value=SimpleNamespace(
                definition=SimpleNamespace(model=self.agent["model_deployment"]),
            ))),
            get_openai_client=Mock(return_value=nullcontext(self.client)),
        )
        self.factory = self.patch("lab.batch.AIProjectClient", return_value=nullcontext(self.project))

    def patch(self, target, *args, **kwargs):
        patcher = patch(target, *args, **kwargs)
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    def response(self, case_id, *, status="completed", raw=None, identifier=None, output=None):
        response_id = identifier or f"resp-{case_id}"
        case = next((row for row in self.cases if row["id"] == case_id), self.cases[0])
        return SimpleNamespace(
            id=response_id, output_text=case["ground_truth"] if raw is None else raw,
            model_dump=lambda **kwargs: {
                "id": response_id, "status": status, "output": output or [],
                "metadata": {"lab_case": case_id, "lab_agent": self.agent["name"],
                             "lab_workspace": self.agent["workspace_id"], "lab_turn": "0"},
                "usage": {"input_tokens": 5, "output_tokens": 10, "total_tokens": 15},
            },
        )

    def run_capture(self, **kwargs):
        with redirect_stdout(io.StringIO()):
            return run_batch(self.config, "baseline", "dev", "mock-run", **kwargs)

    def test_limit_rejects_boolean_fraction_string_and_out_of_range_before_auth(self):
        for limit in (True, False, 1.5, "1", 0, -1, len(self.cases) + 1):
            with self.subTest(limit=limit), self.assertRaisesRegex(LabError, "limit"):
                self.run_capture(limit=limit)
        self.auth.assert_not_called()
        self.load.assert_not_called()
        self.client.responses.create.assert_not_called()

    def test_completed_resume_reuses_verified_capture_without_any_remote_call(self):
        result = self.run_capture(limit=2)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(self.client.responses.create.call_count, 2)
        self.auth.reset_mock()
        self.model.reset_mock()
        self.factory.reset_mock()
        reused = self.run_capture(limit=2, resume=True)
        self.assertEqual(result, reused)
        self.auth.assert_not_called()
        self.model.assert_not_called()
        self.factory.assert_not_called()
        self.assertEqual(self.client.responses.create.call_count, 2)
        self.assertEqual(len(read_jsonl(self.root / "runs/mock-run/outputs.jsonl")), 2)

    def test_unknown_outcome_persists_intent_and_blocks_blind_resubmit(self):
        self.client.responses.create.side_effect = [
            self.response(self.cases[0]["id"]), TimeoutError("unit-only unknown outcome"),
        ]
        result = self.run_capture(limit=2)
        self.assertEqual(result["status"], "blocked_unknown_outcome")
        path = self.root / "runs/mock-run/raw" / f"{self.cases[1]['id']}.json"
        saved = json.loads(path.read_text())
        self.assertEqual(saved["turns"][0]["state"], "unknown_outcome")
        self.assertIsNone(saved["response_id"])
        self.assertIn("unknown outcome", saved["error"])
        self.auth.reset_mock()
        with self.assertRaisesRegex(LabError, "no blind"):
            self.run_capture(limit=2, resume=True)
        self.auth.assert_not_called()
        self.assertEqual(self.client.responses.create.call_count, 2)

    def test_pending_remote_id_is_saved_and_resume_only_retrieves_that_response(self):
        case_id = self.cases[0]["id"]
        self.client.responses.create.return_value = self.response(case_id, status="in_progress")
        self.client.responses.create.side_effect = None
        pending = self.run_capture(limit=1)
        self.assertEqual(pending["status"], "pending_response")
        path = self.root / "runs/mock-run/raw" / f"{case_id}.json"
        self.assertEqual(json.loads(path.read_text())["response_id"], f"resp-{case_id}")
        self.client.responses.retrieve.return_value = self.response(case_id)
        completed = self.run_capture(limit=1, resume=True)
        self.assertEqual(completed["status"], "completed")
        self.client.responses.create.assert_called_once()
        self.client.responses.retrieve.assert_called_once_with(f"resp-{case_id}")
        self.assertIsNone(read_jsonl(self.root / "runs/mock-run/outputs.jsonl")[0]["latency_ms"])

    def test_resume_rejects_changed_contract_and_tampered_completed_output(self):
        self.run_capture(limit=1)
        self.auth.reset_mock()
        with self.assertRaisesRegex(LabError, "contract changed"):
            self.run_capture(limit=2, resume=True)
        path = self.root / "runs/mock-run/outputs.jsonl"
        path.write_text(path.read_text() + " ", encoding="utf-8")
        with self.assertRaisesRegex(LabError, "hash changed"):
            self.run_capture(limit=1, resume=True)
        self.auth.assert_not_called()

    def test_observed_model_drift_is_terminal_even_after_original_model_is_restored(self):
        changed = {"model": {"name": "unit-only-model", "version": "2"}}
        self.model.side_effect = [self.snapshot, changed]
        with self.assertRaises(LabError):
            self.run_capture(limit=1)
        directory = self.root / "runs/mock-run"
        original_metadata = (directory / "metadata.json").read_bytes()
        original_outputs = (directory / "outputs.jsonl").read_bytes()
        self.assertEqual(json.loads(original_metadata)["model_snapshot_after"], changed)
        self.model.side_effect = None
        self.model.return_value = self.snapshot
        self.model.reset_mock()
        self.auth.reset_mock()
        with self.assertRaisesRegex(LabError, "terminal|observed model drift"):
            self.run_capture(limit=1, resume=True)
        self.auth.assert_not_called()
        self.model.assert_not_called()
        self.client.responses.create.assert_called_once()
        self.assertEqual((directory / "metadata.json").read_bytes(), original_metadata)
        self.assertEqual((directory / "outputs.jsonl").read_bytes(), original_outputs)

    def test_legacy_completed_label_cannot_hide_contradictory_model_snapshots(self):
        self.model.side_effect = [self.snapshot, {"model": {"name": "unit-only-model", "version": "2"}}]
        with self.assertRaises(LabError):
            self.run_capture(limit=1)
        metadata_path = self.root / "runs/mock-run/metadata.json"
        metadata = json.loads(metadata_path.read_text())
        metadata["status"] = "completed"
        metadata.pop("model_drift_detected", None)
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
        self.model.side_effect = None
        self.model.return_value = self.snapshot
        self.auth.reset_mock()
        with self.assertRaisesRegex(LabError, "terminal|observed model drift"):
            self.run_capture(limit=1, resume=True)
        with self.assertRaisesRegex(LabError, "terminal|observed model drift"):
            score_run("mock-run")
        self.auth.assert_not_called()
        self.client.responses.create.assert_called_once()

    def test_model_drift_observed_while_resuming_a_partial_capture_is_also_terminal(self):
        case_id = self.cases[0]["id"]
        self.client.responses.create.side_effect = None
        self.client.responses.create.return_value = self.response(case_id, status="in_progress")
        self.assertEqual(self.run_capture(limit=1)["status"], "pending_response")
        raw = self.root / "runs/mock-run/raw" / f"{case_id}.json"
        original_raw = raw.read_bytes()
        self.model.return_value = {"model": {"name": "unit-only-model", "version": "2"}}
        with self.assertRaises(LabError):
            self.run_capture(limit=1, resume=True)
        self.model.return_value = self.snapshot
        self.client.responses.retrieve.return_value = self.response(case_id)
        self.auth.reset_mock()
        with self.assertRaisesRegex(LabError, "observed model drift"):
            self.run_capture(limit=1, resume=True)
        self.auth.assert_not_called()
        self.client.responses.retrieve.assert_not_called()
        self.client.responses.create.assert_called_once()
        self.assertEqual(raw.read_bytes(), original_raw)

    def test_scripted_clarification_followup_final_preserves_provenance_and_no_labels(self):
        case = {
            **self.cases[0], "follow_up": "Explicitly authored missing information.",
            "scripted_user_source": "unit-test-script",
            "ground_truth": "SECRET_REFERENCE_ONLY", "expected_route": "answer",
        }
        initial = json.dumps({"answer": "Please clarify.", "route": "clarify", "citations": [], "needs_human": False})
        final = json.dumps({"answer": "Final response.", "route": "answer", "citations": [], "needs_human": False})
        self.client.responses.create.side_effect = [
            self.response(case["id"], raw=initial, identifier="resp-initial", output=[
                {"type": "mcp_call", "name": "knowledge_base_retrieve", "output": "Actual first-turn context"},
            ]),
            self.response(case["id"], raw=final, identifier="resp-final"),
        ]
        checkpoints = []
        result = capture_case(self.client, self.agent, case, checkpoint=checkpoints.append)
        requests = [call.kwargs for call in self.client.responses.create.call_args_list]
        self.assertEqual(requests[0]["input"], case["query"])
        self.assertEqual(requests[1]["input"], case["follow_up"])
        self.assertEqual(requests[1]["previous_response_id"], "resp-initial")
        self.assertNotIn("SECRET_REFERENCE_ONLY", str(requests))
        self.assertNotIn("expected_route", str(requests))
        self.assertEqual(result["raw_output"], final)
        self.assertEqual(result["turns"][0]["raw_output"], initial)
        self.assertEqual(result["turns"][1]["input_source"], "scripted_user")
        self.assertEqual(result["manual_operational_approval"], "not_granted")
        self.assertEqual(result["retrieved_context"], "Actual first-turn context")
        self.assertEqual(retrieval_observation([result])["knowledge_tool_calls"], 1)
        self.assertIsNone(checkpoints[0]["response_id"])
        self.assertTrue(any(row["response_id"] == "resp-initial" and row["turns"][0]["state"] == "received" for row in checkpoints))

    def test_script_requires_explicit_provenance_and_actual_initial_clarification(self):
        case = {**self.cases[0], "follow_up": "Explicit user reply"}
        with self.assertRaisesRegex(LabError, "scripted-user source"):
            capture_case(self.client, self.agent, case)
        self.client.responses.create.assert_not_called()
        case["scripted_user_source"] = "unit-test"
        self.client.responses.create.side_effect = lambda **kwargs: self.response(
            case["id"], raw='{"answer":"No clarification","route":"answer","citations":[],"needs_human":false}',
        )
        result = capture_case(self.client, self.agent, case)
        self.assertIn("initial response", result["error"])
        self.client.responses.create.assert_called_once()


if __name__ == "__main__":
    unittest.main()
