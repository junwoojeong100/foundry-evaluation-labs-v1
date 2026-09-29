import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from lab.config import LabError
from lab.demo import run_demo


ROOT = Path(__file__).resolve().parents[1]


class DemoTests(unittest.TestCase):
    def test_demo_without_site_packages_credentials_or_network(self):
        code = (
            "import socket,runpy,sys;"
            "socket.socket=lambda *a,**k:(_ for _ in ()).throw(AssertionError('network forbidden'));"
            "sys.argv=['lab','--config','nonexistent.env','demo'];"
            "runpy.run_module('lab',run_name='__main__')"
        )
        env = {key: value for key, value in os.environ.items() if not key.startswith(("AZURE", "OPENAI", "LAB_"))}
        process = subprocess.run(
            [sys.executable, "-S", "-c", code], cwd=ROOT, env=env,
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(process.returncode, 0, process.stderr)
        result = json.loads(process.stdout)
        self.assertEqual(result["kind"], "AUTHORED_DEMO_NOT_LIVE")
        self.assertEqual(result["author_type"], "ai")
        self.assertEqual(result["network_calls"], 0)
        self.assertEqual(result["states"]["human_review"], "PENDING")

    def test_labels_do_not_turn_into_cloud_evidence(self):
        result = run_demo()
        stale = result["examples"][1]
        self.assertEqual(stale["retrieval_groundedness"]["wrong"], 1)
        self.assertEqual(stale["policy_task_correctness"]["wrong"], 0)
        self.assertEqual(result["conversation"][2]["source"], "scripted_followup_not_human_approval")

    def test_existing_demo_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "demo.json"
            run_demo(path)
            content = path.read_bytes()
            with self.assertRaises(LabError):
                run_demo(path)
            self.assertEqual(path.read_bytes(), content)


if __name__ == "__main__":
    unittest.main()
