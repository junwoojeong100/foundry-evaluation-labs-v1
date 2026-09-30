import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.summarize_live import summarize


class LiveSummaryTests(unittest.TestCase):
    def test_private_identity_and_original_approvals_are_not_exported(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "config.json").write_text(json.dumps({
                "names": {"resource_group": "rg-fixture"}, "location": "northcentralus",
                "expected_user": "PRIVATE_USER", "tenant_id": "PRIVATE_TENANT", "subscription_id": "PRIVATE_SUBSCRIPTION",
            }))
            (root / "manifest.json").write_text(json.dumps({
                "phase": "succeeded", "operator_principal_id": "PRIVATE_PRINCIPAL",
                "approval": "PRIVATE_APPROVAL",
                "resources": {"account": {"id": "/subscriptions/PRIVATE_SUBSCRIPTION/resourceGroups/rg-fixture/providers/fixture/account",
                                           "type": "fixture", "status": "succeeded", "sku": None}},
            }))
            (root / "cost-management-response.local.json").write_text(json.dumps({
                "properties": {"columns": [{"name": "Cost", "type": "Number"}], "rows": []},
            }))
            result = summarize(root)
            text = json.dumps(result)
            self.assertNotIn("PRIVATE_", text)
            self.assertIsNone(result["cost"]["actual_invoice"])
            self.assertEqual(result["cost"]["cost_management_observation"]["reported_rows"], [])
            self.assertEqual(result["human_operational_approval"], "NOT_GRANTED")
            self.assertEqual(result["sft"]["status"], "NOT_SUBMITTED")


if __name__ == "__main__":
    unittest.main()
