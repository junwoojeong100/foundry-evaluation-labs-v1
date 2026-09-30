from contextlib import ExitStack, nullcontext
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from lab.config import LabError, load_config
from lab.http import CloudRequestError
from lab.sft import deploy_tuned_model


ROOT = Path(__file__).resolve().parents[1]


class SftDeploymentTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config(ROOT / ".env.example")
        self.state = {"job": {"id": "ftjob-fixture", "status": "succeeded",
                              "terminal_verified": True, "fine_tuned_model": "gpt-4.1-mini-2025-04-14.ft-fixture"}}
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch("lab.sft._locked", return_value=nullcontext()))
        self.stack.enter_context(patch("lab.sft._load_state", return_value=self.state))
        self.stack.enter_context(patch("lab.sft._client"))
        self.stack.enter_context(patch("lab.sft._observe_job"))
        self.stack.enter_context(patch("lab.sft._verify_account"))
        self.stack.enter_context(patch("lab.sft.credential_for"))
        self.ownership = self.stack.enter_context(patch("lab.sft.require_owned_scope"))
        self.persist = self.stack.enter_context(patch("lab.sft._persist"))
        self.az = self.stack.enter_context(patch("lab.sft.az_json", return_value={"value": [
            {"name": {"value": "OpenAI.Standard.gpt4.1-mini-finetune"}, "limit": 100, "currentValue": 0},
        ]}))
        self.http = self.stack.enter_context(patch("lab.sft.JsonHttp")).return_value

    def test_confirm_and_succeeded_are_required(self):
        with self.assertRaises(LabError):
            deploy_tuned_model(self.config, "ft-fixture")
        self.state["job"]["status"] = "running"
        with self.assertRaises(LabError):
            deploy_tuned_model(self.config, "ft-fixture", confirm=True)
        self.http.request.assert_not_called()

    def test_new_submission_journals_intent_and_retains_real_response(self):
        calls = []

        def request(method, url, payload=None, **kwargs):
            calls.append(method)
            if method == "GET":
                raise CloudRequestError(404, "fixture not found")
            self.assertEqual(self.state["deployments"]["ft-fixture"]["status"], "SUBMITTING")
            self.persist.assert_called()
            self.assertTrue(kwargs["create_only"])
            return SimpleNamespace(status=202, body={"properties": {"provisioningState": "Creating"}})

        self.http.request.side_effect = request
        record = deploy_tuned_model(self.config, "ft-fixture", confirm=True)
        self.assertEqual(calls, ["GET", "PUT"])
        self.assertEqual(record["status"], "Creating")
        self.assertEqual(record["cost"]["status"], "NOT_OBSERVED")
        self.assertTrue(record["cost"]["ongoing_hosting"])

    def test_existing_unowned_deployment_is_not_adopted(self):
        self.http.request.return_value = SimpleNamespace(body={"properties": {}})
        with self.assertRaises(LabError):
            deploy_tuned_model(self.config, "someone-else", confirm=True)
        self.assertEqual(self.http.request.call_count, 1)
        self.az.assert_not_called()

    def test_unknown_submission_cannot_be_replayed(self):
        request = {
            "sku": {"name": "Standard", "capacity": 10},
            "properties": {
                "model": {"format": "OpenAI", "name": self.state["job"]["fine_tuned_model"], "version": "1"},
                "versionUpgradeOption": "NoAutoUpgrade",
            },
        }
        self.state["deployments"] = {"ft-fixture": {"request": request, "status": "SUBMITTING"}}
        self.http.request.side_effect = CloudRequestError(404, "fixture not found")
        with self.assertRaises(LabError):
            deploy_tuned_model(self.config, "ft-fixture", confirm=True)
        self.assertEqual(self.http.request.call_count, 1)
        self.az.assert_not_called()

    def test_unavailable_quota_prevents_put(self):
        self.http.request.side_effect = CloudRequestError(404, "fixture not found")
        self.az.return_value = {"value": []}
        with self.assertRaises(LabError):
            deploy_tuned_model(self.config, "ft-fixture", confirm=True)
        self.assertEqual(self.http.request.call_count, 1)

    def test_matching_sft_state_does_not_authorize_a_legacy_shared_account(self):
        self.ownership.side_effect = LabError("missing new-resource creation proof")
        with self.assertRaises(LabError):
            deploy_tuned_model(self.config, "ft-fixture", confirm=True)
        self.http.request.assert_not_called()
        self.persist.assert_not_called()

    def test_owned_remote_provider_metadata_does_not_require_resubmission(self):
        request = {
            "sku": {"name": "Standard", "capacity": 10},
            "properties": {
                "model": {"format": "OpenAI", "name": self.state["job"]["fine_tuned_model"], "version": "1"},
                "versionUpgradeOption": "NoAutoUpgrade",
            },
        }
        self.state["deployments"] = {"ft-fixture": {"request": request, "status": "Creating"}}
        self.http.request.return_value = SimpleNamespace(body={
            "sku": {**request["sku"], "family": None, "tier": None},
            "properties": {"model": {**request["properties"]["model"], "publisher": None},
                           "provisioningState": "Succeeded"},
        })
        result = deploy_tuned_model(self.config, "ft-fixture", confirm=True)
        self.assertEqual(result["status"], "Succeeded")
        self.assertEqual(self.http.request.call_count, 1)
        self.az.assert_not_called()


if __name__ == "__main__":
    unittest.main()
