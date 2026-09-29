import unittest

from lab.config import LabError
from lab.embeddings import DIMENSIONS, validate_vectors


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


if __name__ == "__main__":
    unittest.main()
