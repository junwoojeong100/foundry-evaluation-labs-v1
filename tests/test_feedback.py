from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from lab.config import LabError
from lab.feedback import prepare_feedback
from lab.files import sha256_file, write_jsonl
from lab.preflight import save_json


class FeedbackTests(unittest.TestCase):
    def test_real_dev_failures_stay_review_only_and_preserve_response_id(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            run = root / "runs/dev-run"
            dataset = root / "dev.jsonl"
            write_jsonl(dataset, [{"id": "case-1", "group_id": "group-1", "query": "synthetic query"}])
            write_jsonl(run / "outputs.jsonl", [{"id": "case-1", "raw_output": "actual synthetic response", "response_id": "resp-fixture"}])
            save_json(run / "metadata.json", {
                "source_split": "dev", "split": "dev", "dataset_sha256": sha256_file(dataset),
                "outputs_sha256": sha256_file(run / "outputs.jsonl"),
            })
            save_json(run / "summary.json", {"rows": [{
                "id": "case-1", "rule_failures": ["route"], "api_error": None, "judge": None,
            }]})
            with patch("lab.files.ARTIFACTS", root), patch("lab.feedback.ARTIFACTS", root), \
                    patch("lab.batch.dataset_for_metadata", return_value=dataset):
                result = prepare_feedback("dev-run", "feedback-1")
                self.assertEqual(result["candidate_count"], 1)
                self.assertEqual(result["candidates"][0]["response_id"], "resp-fixture")
                self.assertIsNone(result["candidates"][0]["ground_truth"])
                self.assertFalse(result["automatic_dataset_promotion"])
                with self.assertRaises(LabError):
                    prepare_feedback("dev-run", "feedback-1")

    def test_final_holdout_cannot_be_converted_to_training_feedback(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            save_json(root / "runs/final/metadata.json", {"source_split": "test", "split": "test", "freeze_id": "frozen"})
            with patch("lab.files.ARTIFACTS", root), patch("lab.feedback.ARTIFACTS", root), self.assertRaises(LabError):
                prepare_feedback("final", "feedback-1")
            self.assertFalse((root / "feedback").exists())


if __name__ == "__main__":
    unittest.main()
