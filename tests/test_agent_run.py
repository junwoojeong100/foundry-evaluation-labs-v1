from contextlib import nullcontext, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from lab.batch import run_batch
from lab.config import LabError, load_config
from lab.files import ROOT, read_jsonl


class AgentRunTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config(ROOT / ".env.example")
        self.case = read_jsonl(ROOT / "data/splits/dev.jsonl")[0]
        self.snapshot = {"model": {"name": "fixture", "version": "1"}}
        self.agent = {
            "name": self.config.agent_name("baseline"), "version": "1",
            "workspace_id": "fixture-workspace",
            "model_deployment": self.config.model,
            "model_snapshot": self.snapshot,
            "prompt_sha256": "a" * 64,
            "prompt_source": "test-fixture",
            "prompt_snapshot": "prompts/baseline.txt",
            "knowledge_sha256": hashlib.sha256(b"").hexdigest(),
        }

    def _project(self):
        response = Mock()
        response.id = "resp_fixture"
        response.output_text = self.case["ground_truth"]
        response.model_dump.return_value = {
            "id": response.id, "status": "completed", "output": [],
            "usage": {"input_tokens": 10, "output_tokens": 20, "total_tokens": 30},
        }
        client = Mock()
        client.responses.create.return_value = response
        project = SimpleNamespace(
            agents=SimpleNamespace(get_version=lambda **kwargs: SimpleNamespace(
                definition=SimpleNamespace(model=self.config.model),
            )),
            get_openai_client=lambda **kwargs: nullcontext(client),
        )
        return project, client

    def test_model_drift_blocks_paid_calls_before_capture(self):
        project, client = self._project()
        with tempfile.TemporaryDirectory() as directory, \
             patch("lab.files.ARTIFACTS", Path(directory)), \
             patch("lab.batch.load_agent", return_value=self.agent), \
             patch("lab.batch.credential_for", return_value=nullcontext(None)), \
             patch("lab.batch.AIProjectClient", return_value=nullcontext(project)), \
             patch("lab.batch.model_snapshot", return_value={"model": {"version": "changed"}}):
            with self.assertRaises(LabError):
                run_batch(self.config, "baseline", "dev", "fixture", limit=1)
        client.responses.create.assert_not_called()

    def test_mid_run_model_drift_preserves_capture_but_invalidates_comparison(self):
        project, client = self._project()
        with tempfile.TemporaryDirectory() as directory, \
             patch("lab.files.ARTIFACTS", Path(directory)), \
             patch("lab.batch.load_agent", return_value=self.agent), \
             patch("lab.batch.credential_for", return_value=nullcontext(None)), \
             patch("lab.batch.AIProjectClient", return_value=nullcontext(project)), \
             patch("lab.batch.model_snapshot", side_effect=[self.snapshot, {"model": {"version": "2"}}]), \
             redirect_stdout(io.StringIO()):
            with self.assertRaises(LabError):
                run_batch(self.config, "baseline", "dev", "fixture", limit=1)
            location = Path(directory) / "runs/fixture"
            metadata = json.loads((location / "metadata.json").read_text())
            self.assertEqual(metadata["status"], "invalid_model_drift")
            self.assertTrue((location / "outputs.jsonl").exists())
        client.responses.create.assert_called_once()

    def test_complete_run_exports_plain_answers_and_versioned_evidence(self):
        project, client = self._project()
        with tempfile.TemporaryDirectory() as directory, \
             patch("lab.files.ARTIFACTS", Path(directory)), \
             patch("lab.batch.load_agent", return_value=self.agent), \
             patch("lab.batch.credential_for", return_value=nullcontext(None)), \
             patch("lab.batch.AIProjectClient", return_value=nullcontext(project)), \
             patch("lab.batch.model_snapshot", return_value=self.snapshot), \
             redirect_stdout(io.StringIO()):
            metadata = run_batch(self.config, "baseline", "dev", "fixture", limit=1)
            self.assertEqual(metadata["status"], "completed")
            self.assertEqual(metadata["split"], "smoke")
            exported = read_jsonl(Path(directory) / "runs/fixture/foundry-eval.jsonl")
            self.assertEqual(exported[0]["response"], json.loads(self.case["ground_truth"])["answer"])
            self.assertEqual(metadata["model_snapshot"], self.snapshot)
        request = client.responses.create.call_args.kwargs
        self.assertEqual(request["input"], self.case["query"])
        self.assertNotIn(self.case["ground_truth"], request["input"])
        self.assertEqual(request["extra_body"]["agent_reference"]["version"], "1")


if __name__ == "__main__":
    unittest.main()

