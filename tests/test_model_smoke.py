from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from lab.agents import smoke_model
from lab.config import LabError, load_config


ROOT = Path(__file__).resolve().parents[1]


class ModelSmokeTests(unittest.TestCase):
    def test_completed_response_is_persisted_and_not_repeated(self):
        config = load_config(ROOT / ".env.example")
        response = SimpleNamespace(
            id="resp-fixture", output_text="READY",
            model_dump=lambda **_: {"id": "resp-fixture", "status": "completed", "usage": {"input_tokens": 4, "output_tokens": 1}},
        )
        with TemporaryDirectory() as directory, patch("lab.files.ARTIFACTS", Path(directory)), \
                patch("lab.agents.model_snapshot", return_value={"model": {"name": "fixture", "version": "1"}}), \
                patch("lab.agents.credential_for"), patch("lab.agents.AIProjectClient") as project:
            client = project.return_value.__enter__.return_value.get_openai_client.return_value.__enter__.return_value
            client.responses.create.return_value = response
            first = smoke_model(config, "fixture")
            second = smoke_model(config, "fixture")
            self.assertEqual(first, second)
            self.assertEqual(client.responses.create.call_count, 1)
            self.assertEqual(first["kind"], "LIVE_MODEL_SMOKE_NOT_QUALITY_EVALUATION")
            self.assertEqual(first["cost"]["status"], "NOT_OBSERVED")

    def test_unknown_submission_is_not_resubmitted(self):
        config = load_config(ROOT / ".env.example")
        with TemporaryDirectory() as directory, patch("lab.files.ARTIFACTS", Path(directory)), \
                patch("lab.agents.model_snapshot", return_value={"model": {"name": "fixture", "version": "1"}}), \
                patch("lab.agents.credential_for"), patch("lab.agents.AIProjectClient") as project:
            client = project.return_value.__enter__.return_value.get_openai_client.return_value.__enter__.return_value
            client.responses.create.side_effect = OSError("fixture disconnect after submission")
            with self.assertRaises(OSError):
                smoke_model(config, "fixture")
            with self.assertRaises(LabError):
                smoke_model(config, "fixture")
            self.assertEqual(client.responses.create.call_count, 1)


if __name__ == "__main__":
    unittest.main()
