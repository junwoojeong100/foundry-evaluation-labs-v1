from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from lab.config import LabError
from lab.files import ROOT, read_json, read_jsonl, sha256_file
from lab.handoffs import prepare_optimizer, prepare_tuning
from lab.preflight import save_json


class HandoffTests(unittest.TestCase):
    def test_frontier_preparation_does_not_claim_training_or_include_holdout(self):
        with tempfile.TemporaryDirectory() as directory, patch("lab.handoffs.artifacts_dir", return_value=Path(directory)):
            target = prepare_tuning("frontier")
            manifest = read_json(target / "manifest.json")
            self.assertEqual(manifest["status"], "PREPARED_NOT_SUBMITTED")
            self.assertEqual(manifest["frontier_entitlement"], "NOT_VERIFIED")
            self.assertIsNone(manifest["training_job_id"])
            self.assertFalse(manifest["test_data_included"])
            self.assertEqual(len(read_jsonl(target / "train.jsonl")), 56)
            self.assertFalse((target / "test.jsonl").exists())

    def test_sft_upload_bundle_has_bom_and_never_overwrites_an_experiment(self):
        with tempfile.TemporaryDirectory() as directory, patch("lab.handoffs.artifacts_dir", return_value=Path(directory)):
            target = prepare_tuning("sft")
            train = target / "sft-train.jsonl"
            self.assertTrue(train.read_bytes().startswith(b"\xef\xbb\xbf"))
            self.assertEqual(len(read_jsonl(train)), 56)
            self.assertEqual(len(read_jsonl(target / "sft-validation.jsonl")), 12)
            with self.assertRaises(LabError):
                prepare_tuning("sft")

    def _metadata(self, *, retrieval=12, split="dev"):
        return {
            "stage": "iq", "split": split, "status": "completed",
            "dataset_sha256": sha256_file(ROOT / "data/splits/dev.jsonl"),
            "prompt_snapshot": "prompts/baseline.txt",
            "prompt_sha256": sha256_file(ROOT / "prompts/baseline.txt"),
            "agent_name": "fixture-iq", "agent_version": "1",
            "retrieval": {"rows_with_tool_output": retrieval},
        }

    def test_optimizer_preparation_requires_observed_iq_use(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch("lab.handoffs.artifacts_dir", return_value=Path(directory)), \
             patch("lab.files.artifacts_dir", return_value=Path(directory)):
            save_json(Path(directory) / "runs/fixture/metadata.json", self._metadata(retrieval=0))
            with self.assertRaisesRegex(LabError, "실제 IQ"):
                prepare_optimizer("fixture")

    def test_optimizer_preparation_rejects_holdout(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch("lab.handoffs.artifacts_dir", return_value=Path(directory)), \
             patch("lab.files.artifacts_dir", return_value=Path(directory)):
            save_json(Path(directory) / "runs/fixture/metadata.json", self._metadata(split="test"))
            with self.assertRaises(LabError):
                prepare_optimizer("fixture")

    def test_optimizer_bundle_is_prepared_only_and_matches_portal_columns(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch("lab.handoffs.artifacts_dir", return_value=Path(directory)), \
             patch("lab.files.artifacts_dir", return_value=Path(directory)):
            save_json(Path(directory) / "runs/fixture/metadata.json", self._metadata())
            target = prepare_optimizer("fixture")
            state = read_json(target / "handoff.json")
            self.assertEqual(state["status"], "PREPARED_NOT_SUBMITTED")
            self.assertIn("guide/handbook.md#optimize (step 05)", state["next"])
            self.assertIn("agent optimizer", state["next"])
            rows = read_jsonl(target / "dev-upload.jsonl")
            self.assertEqual(len(rows), 12)
            self.assertEqual(set(rows[0]), {"query", "context", "ground_truth"})


if __name__ == "__main__":
    unittest.main()
