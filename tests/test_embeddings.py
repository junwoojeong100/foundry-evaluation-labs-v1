import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from azure.core.exceptions import AzureError

from lab.config import LabError, load_config
from lab.embeddings import DIMENSIONS, embed, validate_vectors

ROOT = Path(__file__).resolve().parents[1]


class EmbeddingTests(unittest.TestCase):
    def test_preserves_response_order_by_index(self):
        result = validate_vectors({"data": [
            {"index": 1, "embedding": [0.2] * DIMENSIONS},
            {"index": 0, "embedding": [0.1] * DIMENSIONS},
        ]}, 2)
        self.assertEqual([row[0] for row in result], [0.1, 0.2])

    def test_rejects_missing_duplicate_fake_and_nonfinite_vectors(self):
        samples = (
            [],
            [0.0] * DIMENSIONS,
            [float("nan")] * DIMENSIONS,
            [float("inf")] * DIMENSIONS,
            [True] * DIMENSIONS,
            [0.1] * (DIMENSIONS - 1),
        )
        for sample in samples:
            with self.subTest(length=len(sample)), self.assertRaises(LabError):
                validate_vectors({"data": [{"index": 0, "embedding": sample}]}, 1)
        with self.assertRaises(LabError):
            validate_vectors({"data": [{"index": 0}, {"index": 0}]}, 2)

    def test_failed_request_blocks_the_same_record_until_it_is_set_aside(self):
        config = load_config(ROOT / ".env.example")
        response = SimpleNamespace(
            model_dump=lambda **_: {"data": [{"index": 0, "embedding": [0.1] * DIMENSIONS}], "usage": {}},
            _request_id="request-fixture",
        )
        with TemporaryDirectory() as directory, \
                patch("lab.embeddings.model_snapshot", return_value={"model": {"name": "text-embedding-3-large"}}), \
                patch("lab.auth.credential_for"), patch("azure.identity.get_bearer_token_provider"), \
                patch("openai.OpenAI") as client_class:
            client = client_class.return_value.__enter__.return_value
            client.embeddings.create.side_effect = [AzureError("403 before the roles apply"), response]
            record = Path(directory) / "knowledge" / "document-embeddings.json"
            with self.assertRaises(AzureError):
                embed(config, ["policy"], record)
            self.assertEqual(json.loads(record.read_text())["status"], "failed_or_unknown")
            with self.assertRaises(LabError):
                embed(config, ["policy"], record)
            record.rename(record.with_name(record.name + ".failed-1"))
            self.assertEqual(embed(config, ["policy"], record)["status"], "completed")
            self.assertEqual(client.embeddings.create.call_count, 2)
            self.assertTrue(record.with_name(record.name + ".failed-1").is_file())


if __name__ == "__main__":
    unittest.main()
