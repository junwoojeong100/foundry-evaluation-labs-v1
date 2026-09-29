from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from lab.cleanup import cleanup, cleanup_plan
from lab.config import LabError, load_config


class CleanupTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config(Path(__file__).resolve().parents[1] / ".env.example")
        self.state = {"workspace_id": "12345678-1234-1234-1234-123456789012", "created": []}

    def test_plan_does_not_authenticate_or_delete_cloud_resources(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch("lab.cleanup.ARTIFACTS", Path(directory)), \
             patch("lab.cleanup.workspace", return_value=self.state), \
             patch("lab.cleanup.credential_for") as credential:
            result = cleanup(self.config)
        credential.assert_not_called()
        self.assertEqual(result["mode"], "LOCAL_PLAN_ONLY")
        self.assertIn("resource group", result["never_deleted"])

    def test_mismatched_confirmation_blocks_before_auth(self):
        with patch("lab.cleanup.workspace", return_value=self.state), \
             patch("lab.cleanup.credential_for") as credential:
            with self.assertRaises(LabError):
                cleanup(self.config, confirm_prefix="someone-else")
        credential.assert_not_called()

    def test_foreign_resource_url_cannot_be_deleted(self):
        self.state["created"] = [{
            "kind": "search_index", "name": "production", "url": "https://other.search.windows.net/indexes/production",
        }]
        with patch("lab.cleanup.workspace", return_value=self.state):
            with self.assertRaises(LabError):
                cleanup_plan(self.config)

    def test_other_agent_prefix_cannot_be_deleted(self):
        self.state["created"] = [{"kind": "agent_version", "name": "another-user-agent", "version": "1"}]
        with patch("lab.cleanup.workspace", return_value=self.state):
            with self.assertRaises(LabError):
                cleanup_plan(self.config)


if __name__ == "__main__":
    unittest.main()

