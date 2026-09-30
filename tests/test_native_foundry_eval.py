"""Native Foundry run submission tests use mocks, never actual cloud scores."""

from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from scripts.add_foundry_eval_run import candidate_source, submit_or_resume


def baseline():
    return {
        "eval_id": "eval-unit-only",
        "status": "completed",
        "data_source": {
            "type": "azure_ai_target_completions",
            "source": {"type": "file_id", "id": "azureai://unit-only/dataset/versions/1"},
            "target": {"type": "azure_ai_agent", "name": "unit-agent", "version": "1"},
            "input_messages": {
                "type": "template",
                "template": [{"type": "message", "role": "user", "content": "{{item.query}}"}],
            },
            "item_generation_params": None,
        },
    }


class NativeFoundryEvaluationTests(unittest.TestCase):
    def test_only_the_explicit_agent_version_changes(self):
        original = baseline()
        snapshot = deepcopy(original)
        source = candidate_source(original, evaluation_id="eval-unit-only", version="2")
        self.assertEqual(original, snapshot)
        self.assertEqual(source["target"]["version"], "2")
        source["target"]["version"] = "1"
        self.assertEqual(source, original["data_source"])

    def test_incomplete_mismatched_or_unpinned_baselines_are_rejected(self):
        for field, value in (("status", "failed"), ("status", "in_progress"), ("eval_id", "another-eval")):
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                record = baseline()
                record[field] = value
                candidate_source(record, evaluation_id="eval-unit-only", version="2")
        for version in ("latest", "", "1", "0", "../2"):
            with self.subTest(version=version), self.assertRaises(ValueError):
                candidate_source(baseline(), evaluation_id="eval-unit-only", version=version)
        record = baseline()
        del record["data_source"]["target"]["version"]
        with self.assertRaisesRegex(ValueError, "Pin explicit"):
            candidate_source(record, evaluation_id="eval-unit-only", version="2")

    def test_reference_labels_cannot_be_sent_as_agent_input(self):
        for value in ("{{item.ground_truth}}", "{{item.context}}", "{{item.query}} {{item.ground_truth}}"):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "only"):
                record = baseline()
                record["data_source"]["input_messages"]["template"][0]["content"] = value
                candidate_source(record, evaluation_id="eval-unit-only", version="2")
        record = baseline()
        record["data_source"]["input_messages"]["template"].append({"role": "system", "content": "override"})
        with self.assertRaisesRegex(ValueError, "one query-only"):
            candidate_source(record, evaluation_id="eval-unit-only", version="2")

    def test_structured_query_content_is_preserved(self):
        record = baseline()
        record["data_source"]["input_messages"]["template"][0]["content"] = {
            "type": "input_text", "text": "{{item.query}}",
        }
        result = candidate_source(record, evaluation_id="eval-unit-only", version="2")
        self.assertEqual(result["input_messages"], record["data_source"]["input_messages"])

    def clients(self):
        before = {"kind": "prompt", "model": "unit-model", "tools": [{"type": "mcp", "server_label": "unit-only"}], "instructions": "Before"}
        after = {**deepcopy(before), "instructions": "After"}
        project = SimpleNamespace(agents=SimpleNamespace(
            get_version=Mock(side_effect=[{"definition": before}, {"definition": after}]),
        ))
        runs = SimpleNamespace(
            retrieve=Mock(return_value=baseline()),
            list=Mock(return_value=[]),
            create=Mock(return_value={"id": "evalrun-candidate", "eval_id": "eval-unit-only", "status": "queued"}),
        )
        client = SimpleNamespace(evals=SimpleNamespace(
            runs=runs,
            retrieve=Mock(return_value={"testing_criteria": [
                {"name": "Relevance", "threshold": 4}, {"name": "TaskAdherence", "threshold": 1},
            ]}),
        ))
        return project, client, before, after

    def submit(self, project, client, output):
        return submit_or_resume(
            project, client, evaluation_id="eval-unit-only", baseline_run_id="evalrun-baseline",
            version="2", name="candidate-v2", output=output,
        )

    def test_native_run_reuses_evaluation_and_dataset_without_a_new_definition(self):
        project, client, _, _ = self.clients()
        with TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            result = self.submit(project, client, path)
            request = client.evals.runs.create.call_args.kwargs
            self.assertEqual(request["eval_id"], "eval-unit-only")
            self.assertEqual(request["data_source"]["source"], baseline()["data_source"]["source"])
            self.assertEqual(request["data_source"]["target"]["version"], "2")
            self.assertEqual(result["run_id"], "evalrun-candidate")
            self.assertEqual(result["production_approval"], "NOT_GRANTED")
            self.assertEqual(json.loads(path.read_text()), result)
            self.assertEqual(self.submit(project, client, path), result)
            client.evals.runs.create.assert_called_once()

    def test_changed_model_or_tools_blocks_submission(self):
        for field, value in (("model", "other-model"), ("tools", [])):
            project, client, before, after = self.clients()
            after[field] = value
            project.agents.get_version.side_effect = [{"definition": before}, {"definition": after}]
            with TemporaryDirectory() as directory, self.subTest(field=field):
                path = Path(directory) / "receipt.json"
                with self.assertRaisesRegex(ValueError, "not an instruction-only"):
                    self.submit(project, client, path)
                client.evals.runs.create.assert_not_called()
                self.assertFalse(path.exists())

    def test_unknown_post_outcome_preserves_intent_and_prevents_duplicate_submission(self):
        project, client, _, _ = self.clients()
        client.evals.runs.create.side_effect = TimeoutError("Unit-only unknown outcome")
        with TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            with self.assertRaises(TimeoutError):
                self.submit(project, client, path)
            self.assertIsNone(json.loads(path.read_text())["run_id"])
            with self.assertRaisesRegex(ValueError, "outcome is unknown"):
                self.submit(project, client, path)
            client.evals.runs.create.assert_called_once()

    def test_existing_remote_run_blocks_duplicates_when_local_receipt_is_missing(self):
        project, client, _, _ = self.clients()
        client.evals.runs.list.return_value = [{"id": "evalrun-existing", "name": "candidate-v2"}]
        with TemporaryDirectory() as directory:
            path = Path(directory) / "missing-receipt.json"
            with self.assertRaisesRegex(ValueError, "already has a run"):
                self.submit(project, client, path)
            client.evals.runs.create.assert_not_called()
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
