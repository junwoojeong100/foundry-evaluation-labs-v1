"""Native Foundry run submission tests use mocks, never actual cloud scores."""

from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, MagicMock, patch

from scripts.add_foundry_eval_run import candidate_source, evaluation_contract, submit_or_resume, verify_agent_execution
from lab.config import LabError, load_config
from lab.managed_eval import list_native_evaluations


def evaluation():
    return {"testing_criteria": [
        {
            "name": name,
            "type": "azure_ai_evaluator",
            "evaluator_name": evaluator,
            "initialization_parameters": {"threshold": threshold, "deployment_name": "unit-judge"},
            "data_mapping": {"query": "{{item.query}}", "response": response},
        }
        for name, evaluator, threshold, response in (
            ("Relevance", "builtin.relevance", 4, "{{sample.output_text}}"),
            ("TaskAdherence", "builtin.task_adherence", 1, "{{sample.output_items}}"),
        )
    ]}


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
    def test_portal_id_lookup_is_read_only_and_filters_exact_names(self):
        config = load_config(Path(__file__).resolve().parents[1] / ".env.example")
        client = MagicMock()
        client.evals.list.return_value = [
            SimpleNamespace(id="eval-other", name="other"),
            SimpleNamespace(id="eval-unit", name="lab-ko-learning-loop"),
        ]
        run = SimpleNamespace(
            id="evalrun-unit", name="baseline-v1", status="completed",
            model_dump=lambda **_: {
                "data_source": {"target": {"name": "lab-ko-iq", "version": "1"}},
                "result_counts": {"total": 12},
            },
        )
        client.evals.runs.list.return_value = [run]
        with patch("lab.managed_eval.credential_for"), patch("lab.managed_eval.AIProjectClient") as factory:
            factory.return_value.__enter__.return_value.get_openai_client.return_value.__enter__.return_value = client
            result = list_native_evaluations(config, "lab-ko-learning-loop")
            self.assertEqual(result["mode"], "READ_ONLY")
            self.assertEqual(result["evaluations"][0]["evaluation_id"], "eval-unit")
            self.assertEqual(result["evaluations"][0]["runs"][0]["agent_version"], "1")
            client.evals.runs.list.assert_called_once_with(eval_id="eval-unit", limit=100)
            client.evals.create.assert_not_called()
            client.evals.runs.create.assert_not_called()
            with self.assertRaisesRegex(LabError, "No evaluation"):
                list_native_evaluations(config, "missing")

    def test_only_the_explicit_agent_version_changes(self):
        original = baseline()
        snapshot = deepcopy(original)
        source = candidate_source(original, evaluation_id="eval-unit-only", version="2")
        self.assertEqual(original, snapshot)
        self.assertEqual(source["target"]["version"], "2")
        source["target"]["version"] = "1"
        self.assertEqual(source, original["data_source"])

    def test_explicit_drafts_do_not_require_incrementing_release_versions(self):
        result = candidate_source(baseline(), evaluation_id="eval-unit-only", version="draft-1790810207613")
        self.assertEqual(result["target"]["version"], "draft-1790810207613")
        for version in ("draft-latest", "draft-0", "draft-../2"):
            with self.subTest(version=version), self.assertRaises(ValueError):
                candidate_source(baseline(), evaluation_id="eval-unit-only", version=version)

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
            retrieve=Mock(return_value=evaluation()),
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
            self.assertEqual(result["evaluation_contract"]["judge_deployment"], "unit-judge")
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

    def test_remote_judge_is_authoritative_even_when_local_defaults_differ(self):
        record = evaluation()
        for criterion in record["testing_criteria"]:
                criterion["initialization_parameters"]["deployment_name"] = "remote-luna-judge"
        contract = evaluation_contract(record)
        self.assertEqual(contract["judge_deployment"], "remote-luna-judge")
        self.assertEqual(contract["thresholds"], {"Relevance": 4, "TaskAdherence": 1})

    def test_current_instruction_pair_does_not_embed_dataset_answers(self):
        root = Path(__file__).resolve().parents[1]
        for name in ("baseline.txt", "optimized.txt"):
            instructions = (root / "prompts/en" / name).read_text(encoding="utf-8")
            with self.subTest(prompt=name):
                self.assertLessEqual(len(instructions), 6000)
                self.assertTrue(instructions.isascii())
                self.assertNotRegex(instructions, r"\b20\d{2}\b|\d+(?:\.\d+)?%|ATLAS-[A-Z]+-\d+")
                for field in ("answer", "citations", "route", "needs_human", "knowledge_base_retrieve"):
                    self.assertIn(field, instructions)
                for line in (root / "data/en/optimizer/dev.jsonl").read_text().splitlines():
                    row = json.loads(line)
                    self.assertNotIn(row["query"], instructions)
                    self.assertNotIn(row["ground_truth"], instructions)

    def test_actual_output_attests_the_requested_version_and_instructions(self):
        items = [{"datasource_item": {
            "agent_name": "unit-agent", "agent_version": "3",
            "sample.output_items": [{"role": "system", "content": "Frozen instructions"}],
        }}]
        result = verify_agent_execution(
            items, agent_name="unit-agent", version="3", instructions="Frozen instructions",
        )
        self.assertEqual(result["items_verified"], 1)
        self.assertEqual(result["agent_version"], "3")

    def test_requested_version_metadata_alone_is_not_execution_proof(self):
        sources = [
            {"agent_name": "other-agent", "agent_version": "3"},
            {"agent_name": "unit-agent", "agent_version": "1"},
            {"agent_name": "unit-agent", "agent_version": "3", "sample.output_items": []},
            {"agent_name": "unit-agent", "agent_version": "3", "sample.output_items": [
                {"role": "system", "content": "Different instructions"},
            ]},
        ]
        for source in sources:
            with self.subTest(source=source), self.assertRaises(ValueError):
                verify_agent_execution(
                    [{"datasource_item": source}], agent_name="unit-agent", version="3",
                    instructions="Frozen instructions",
                )
        with self.assertRaises(ValueError):
            verify_agent_execution([], agent_name="unit-agent", version="3", instructions="Frozen instructions")

    def test_changed_threshold_or_mapping_blocks_paid_submission(self):
        for field, value in (("threshold", 4), ("threshold", True), ("response", "{{sample.output_text}}")):
                with TemporaryDirectory() as directory, self.subTest(field=field, value=value):
                    project, client, _, _ = self.clients()
                    criteria = evaluation()
                    task = criteria["testing_criteria"][1]
                    target = task["initialization_parameters"] if field == "threshold" else task["data_mapping"]
                    target[field] = value
                    client.evals.retrieve.return_value = criteria
                    path = Path(directory) / "receipt.json"
                    with self.assertRaisesRegex(ValueError, "TaskAdherence"):
                        self.submit(project, client, path)
                    client.evals.runs.create.assert_not_called()
                    self.assertFalse(path.exists())

    def test_missing_mixed_duplicate_or_extra_evaluators_are_rejected(self):
        missing_judge = evaluation()
        del missing_judge["testing_criteria"][0]["initialization_parameters"]["deployment_name"]
        mixed_judge = evaluation()
        mixed_judge["testing_criteria"][1]["initialization_parameters"]["deployment_name"] = "different-judge"
        duplicate = evaluation()
        duplicate["testing_criteria"][1] = deepcopy(duplicate["testing_criteria"][0])
        extra = evaluation()
        extra["testing_criteria"].append(deepcopy(extra["testing_criteria"][0]))
        missing = evaluation()
        missing["testing_criteria"].pop()
        malformed = evaluation()
        malformed["testing_criteria"][0]["initialization_parameters"] = ["not", "an", "object"]
        for record in (missing_judge, mixed_judge, duplicate, extra, missing, malformed):
                with self.subTest(record=record), self.assertRaises(ValueError):
                    evaluation_contract(record)

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
