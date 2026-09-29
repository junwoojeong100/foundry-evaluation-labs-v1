from pathlib import Path
import unittest

from lab.config import LabError, load_config
from lab.preflight import model_snapshot, run_preflight


ROOT = Path(__file__).resolve().parents[1]


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config(ROOT / ".env.example")

    def fake_az(self, *, region="North Central US", missing_model=False):
        c = self.config

        def run(args):
            if args[:2] == ["account", "show"]:
                return {
                    "id": c.subscription_id, "tenantId": c.tenant_id,
                    "state": "Enabled", "user": {"name": c.expected_user},
                }
            if args[:3] == ["cognitiveservices", "account", "show"]:
                return {"location": "northcentralus", "properties": {"publicNetworkAccess": "Enabled"}}
            if args[:2] == ["resource", "show"]:
                return {"location": "northcentralus", "properties": {"endpoints": {"AI Foundry API": c.project_endpoint}}}
            if args[:3] == ["search", "service", "show"]:
                return {"location": region}
            if args[:4] == ["cognitiveservices", "account", "deployment", "list"]:
                names = [c.model, c.judge] if missing_model else [c.model, c.judge, c.optimizer, c.embedding]
                return [{
                    "name": n,
                    "properties": {
                        "provisioningState": "Succeeded",
                        "model": {"name": "gpt-5.5" if n == c.planner else "text-embedding-3-small" if n == c.embedding else "fixture-model"},
                    },
                    "sku": {"name": "GlobalStandard"},
                } for n in names]
            raise AssertionError(f"Unexpected command: {args}")

        return run

    def test_readonly_pass_keeps_unverified_features_explicit(self):
        result = run_preflight(self.config, run=self.fake_az())
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(any("Frontier" in item for item in result["not_verified"]))

    def test_region_mismatch_blocks_instead_of_fallback(self):
        result = run_preflight(self.config, run=self.fake_az(region="eastus"))
        self.assertEqual(result["status"], "BLOCKED")

    def test_missing_deployment_is_not_success(self):
        result = run_preflight(self.config, run=self.fake_az(missing_model=True))
        self.assertEqual(result["status"], "BLOCKED")

    def test_wrong_account_stops_before_resource_lookups(self):
        calls = []

        def wrong_user(args):
            calls.append(args)
            return {"id": self.config.subscription_id, "tenantId": "wrong", "user": {"name": "other"}}

        with self.assertRaises(LabError):
            run_preflight(self.config, run=wrong_user)
        self.assertEqual(len(calls), 1)

    def test_wrong_planner_model_is_blocked_before_the_iq_chapter(self):
        original = self.fake_az()

        def wrong_planner(args):
            result = original(args)
            if args[:4] == ["cognitiveservices", "account", "deployment", "list"]:
                for deployment in result:
                    deployment["properties"]["model"]["name"] = "different-model"
            return result

        report = run_preflight(self.config, run=wrong_planner)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertTrue(any(c["name"] == "iq_planner_supported_model" and c["status"] == "BLOCKED" for c in report["checks"]))

    def test_snapshot_records_backing_model_not_only_deployment_alias(self):
        raw = {
            "name": self.config.model, "sku": {"name": "GlobalStandard", "capacity": 10},
            "properties": {
                "provisioningState": "Succeeded", "model": {"name": "fixture", "version": "2026-01-01"},
                "versionUpgradeOption": "NoAutoUpgrade",
            },
        }
        snapshot = model_snapshot(self.config, self.config.model, run=lambda args: raw)
        self.assertEqual(snapshot["model"]["version"], "2026-01-01")

    def test_snapshot_without_model_revision_is_not_accepted(self):
        with self.assertRaises(LabError):
            model_snapshot(self.config, self.config.model, run=lambda args: {"name": self.config.model, "properties": {}})


if __name__ == "__main__":
    unittest.main()
