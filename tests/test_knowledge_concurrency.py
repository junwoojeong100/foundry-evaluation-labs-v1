from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from lab.config import LabError, load_config
from lab.files import write_once_json
from lab.knowledge import probe_knowledge


ROOT = Path(__file__).resolve().parents[1]


class KnowledgeConcurrencyTests(unittest.TestCase):
    def test_identical_concurrent_probes_submit_only_one_paid_request(self):
        config = load_config(ROOT / ".env.example")
        barrier = Barrier(2)
        setup = {"names": {"base": "fixture-kb", "source": "fixture-source"}}
        response = {"response": [{"text": "fixture"}], "references": [{"id": "fixture"}],
                    "activity": [{"type": "searchIndex"}]}

        def claim(path, payload):
            barrier.wait(timeout=5)
            write_once_json(path, payload)

        def attempt():
            try:
                return probe_knowledge(config, "authored concurrency fixture")
            except LabError as exc:
                return exc

        with TemporaryDirectory() as directory, \
                patch("lab.knowledge.artifacts_dir", return_value=Path(directory)), \
                patch("lab.knowledge.load_knowledge", side_effect=lambda _: deepcopy(setup)), \
                patch("lab.knowledge.credential_for"), \
                patch("lab.knowledge.JsonHttp") as http, \
                patch("lab.knowledge.write_once_json", side_effect=claim):
            http.return_value.request.return_value = SimpleNamespace(body=response)
            with ThreadPoolExecutor(max_workers=2) as pool:
                outcomes = list(pool.map(lambda _: attempt(), range(2)))
            self.assertEqual(http.return_value.request.call_count, 1)
            self.assertEqual(sum(isinstance(value, LabError) for value in outcomes), 1)
            self.assertEqual(sum(isinstance(value, dict) for value in outcomes), 1)


if __name__ == "__main__":
    unittest.main()
