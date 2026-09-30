from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from lab.config import LabError, load_config
from lab.optimizer import collect_prompt
from lab.preflight import save_json


ROOT = Path(__file__).resolve().parents[1]


class OptimizerResultTests(unittest.TestCase):
    def test_response_import_does_not_claim_evaluation_or_fabricate_job_id(self):
        config = load_config(ROOT / ".env.example")
        with TemporaryDirectory() as temporary, patch("lab.optimizer.ARTIFACTS", Path(temporary)):
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
        with TemporaryDirectory() as temporary, patch("lab.optimizer.ARTIFACTS", Path(temporary)):
            request, response = Path(temporary) / "request.json", Path(temporary) / "response.json"
            save_json(request, {"query": "optimizePromptResolver", "params": {"resourceId": "other", "payload": {"developer_message": "original"}}})
            save_json(response, {"new_developer_message": "candidate", "comments": []})
            with self.assertRaises(LabError):
                collect_prompt(config, request, response)
            self.assertFalse((Path(temporary) / "prompt-optimizer").exists())


if __name__ == "__main__":
    unittest.main()
