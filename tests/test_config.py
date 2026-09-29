from dataclasses import replace
from pathlib import Path
import unittest

from lab.config import LabError, load_config
from lab.preflight import check_identity


ROOT = Path(__file__).resolve().parents[1]


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config(ROOT / ".env.example")

    def test_profile_is_explicit_ncus(self):
        self.assertEqual(self.config.location, "northcentralus")
        self.assertTrue(self.config.project_id.endswith("/projects/mf15-project"))

    def test_wrong_region_is_not_silently_replaced(self):
        with self.assertRaises(LabError):
            replace(self.config, location="eastus").validate()

    def test_endpoint_cannot_send_data_elsewhere(self):
        with self.assertRaises(LabError):
            replace(self.config, project_endpoint="https://example.org").validate()

    def test_prefix_does_not_allow_path_escape(self):
        with self.assertRaises(LabError):
            replace(self.config, prefix="../another-user").validate()

    def test_wrong_identity_stops(self):
        response = {
            "id": self.config.subscription_id,
            "tenantId": self.config.tenant_id,
            "state": "Enabled",
            "user": {"name": "other@example.org"},
        }
        with self.assertRaises(LabError):
            check_identity(self.config, lambda args: response)

    def test_correct_identity_succeeds(self):
        response = {
            "id": self.config.subscription_id,
            "tenantId": self.config.tenant_id,
            "state": "Enabled",
            "user": {"name": self.config.expected_user},
        }
        self.assertEqual(check_identity(self.config, lambda args: response)["user"], self.config.expected_user)


if __name__ == "__main__":
    unittest.main()

