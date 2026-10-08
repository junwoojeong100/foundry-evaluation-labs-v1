from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from lab.config import LabError, load_config
from lab.optimizer import check_native_pair, collect_prompt, native_answer
from lab.files import read_jsonl
from lab.preflight import save_json


ROOT = Path(__file__).resolve().parents[1]


class OptimizerResultTests(unittest.TestCase):
    def test_native_parser_preserves_invalid_prose_instead_of_cherry_picking_json(self):
        self.assertEqual(native_answer([
            {"role": "assistant", "content": json.dumps([{"type": "tool_call", "name": "knowledge_base_retrieve", "tool_call_id": "call-fixture"}])},
            {"role": "assistant", "content": json.dumps([
                {"type": "output_text", "text": "outside JSON"}, {"type": "output_text", "text": '{"answer":"fixture"}'},
            ])},
        ]), 'outside JSON\n{"answer":"fixture"}')
        with self.assertRaises(LabError):
            native_answer([{"role": "assistant", "content": '[{"type":"tool_call","name":"delete_records","tool_call_id":"bad"}]'}])

    def test_full_native_pair_is_joined_by_query_without_new_inference(self):
        cases = read_jsonl(ROOT / "data/splits/dev.jsonl")
        with TemporaryDirectory() as temporary, patch("lab.optimizer.artifacts_dir", return_value=Path(temporary)):
            root = Path(temporary)
            save_json(root / "agents/iq.json", {
                "model_deployment": "unit-model", "knowledge_sha256": "a" * 64, "prompt_sha256": "b" * 64,
            })
            save_json(root / "optimizer/selected-candidate.json", {"candidate_prompt_sha256": "c" * 64})
            paths = []
            for arm in ("baseline", "candidate"):
                items = [{
                    "id": str(i), "run_id": f"run-{arm}", "eval_id": "eval-fixture", "status": "completed",
                    "datasource_item": {"query": case["query"]},
                    "sample": {"input": [{"role": "user", "content": case["query"]}],
                               "output": [{"role": "assistant", "content": json.dumps([{"type": "output_text", "text": case["ground_truth"]}])}]},
                } for i, case in enumerate(reversed(cases))]
                path = root / f"{arm}.json"
                save_json(path, {"items": items})
                paths.append(path)
            result = check_native_pair(*paths)
            self.assertEqual(result["new_model_calls"], 0)
            self.assertEqual(result["arms"]["candidate"]["sample_count"], 12)
            self.assertEqual(result["arms"]["candidate"]["metrics"]["format_pass_rate"], 1.0)

    def test_response_import_does_not_claim_evaluation_or_fabricate_job_id(self):
        config = load_config(ROOT / ".env.example")
        with TemporaryDirectory() as temporary, patch("lab.optimizer.artifacts_dir", return_value=Path(temporary)):
            request, response = Path(temporary) / "request.json", Path(temporary) / "response.json"
            save_json(request, {"query": "optimizePromptResolver", "params": {
                "resourceId": config.project_id, "payload": {"developer_message": "original", "model_deployment_name": config.model},
            }})
            save_json(response, {"new_developer_message": "candidate", "comments": [], "new_messages": []})
            record = collect_prompt(config, request, response)
            self.assertEqual(record["status"], "CANDIDATE_CAPTURED_NOT_EVALUATED")
            self.assertIsNone(record["remote_job_id"])
            self.assertEqual(record, collect_prompt(config, request, response))
            (Path(temporary) / "prompt-optimizer/candidate.txt").write_text("changed", encoding="utf-8")
            with self.assertRaises(LabError):
                collect_prompt(config, request, response)

    def test_different_project_cannot_be_imported_as_this_run(self):
        config = load_config(ROOT / ".env.example")
        with TemporaryDirectory() as temporary, patch("lab.optimizer.artifacts_dir", return_value=Path(temporary)):
            request, response = Path(temporary) / "request.json", Path(temporary) / "response.json"
            save_json(request, {"query": "optimizePromptResolver", "params": {"resourceId": "other", "payload": {"developer_message": "original"}}})
            save_json(response, {"new_developer_message": "candidate", "comments": []})
            with self.assertRaises(LabError):
                collect_prompt(config, request, response)
            self.assertFalse((Path(temporary) / "prompt-optimizer").exists())


if __name__ == "__main__":
    unittest.main()
import json
