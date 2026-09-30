from pathlib import Path
import unittest

from lab.batch import _case_inputs, dataset_for_metadata
from lab.config import LabError
from lab.evidence import validate_case
from lab.files import read_jsonl


ROOT = Path(__file__).resolve().parents[1]


class DialogueDataTests(unittest.TestCase):
    def test_supplemental_dialogue_keeps_agent_input_label_free(self):
        row = read_jsonl(ROOT / "data/dialogue/dev.jsonl")[0]
        validate_case(row)
        messages = _case_inputs(row)
        self.assertEqual(messages, [row["query"], row["follow_up"]])
        for label in ("ground_truth", "expected_route", "required_citations"):
            self.assertNotIn(label, "".join(messages))
        self.assertIn("not a real customer", row["scripted_user_source"])
        original_ids = {case["id"] for case in read_jsonl(ROOT / "data/cases.jsonl")}
        self.assertNotIn(row["id"], original_ids)
        self.assertEqual(len(original_ids), 100)

    def test_dialogue_cannot_impersonate_final_holdout(self):
        self.assertEqual(dataset_for_metadata({"dialogue_diagnostic": True, "source_split": "dev"}), ROOT / "data/dialogue/dev.jsonl")
        with self.assertRaises(LabError):
            dataset_for_metadata({"dialogue_diagnostic": True, "source_split": "test", "freeze_id": "frozen"})


if __name__ == "__main__":
    unittest.main()
