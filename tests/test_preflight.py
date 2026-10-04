from copy import deepcopy
import json
from pathlib import Path
import unittest
from urllib.parse import unquote, urlsplit

from lab.config import LabError, load_config
from lab.preflight import LAB_MINIMUM_TPM, _tokens_per_minute, model_snapshot, run_preflight


ROOT = Path(__file__).resolve().parents[1]


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config(ROOT / ".env.example")

    def fake_az(self, *, region="North Central US", missing_model=False, limits=None, raw_limits=None, calls=None):
        c = self.config
        names = [c.model, c.judge] if missing_model else [c.model, c.judge, c.optimizer, c.embedding]
        deployments = [{
            "id": f"{c.account_id}/deployments/{name}",
            "name": name,
            "properties": {
                "provisioningState": "Succeeded",
                "model": {"name": "gpt-5.5" if name == c.planner else "text-embedding-3-small" if name == c.embedding else "fixture-model"},
                "rateLimits": (limits or {}).get(name, [
                    {"key": "request", "count": 100, "renewalPeriod": 60},
                    {"key": "token", "count": 10_000 if name == c.embedding else 100_000, "renewalPeriod": 60},
                ]),
            },
            "sku": {"name": "GlobalStandard", "capacity": 10 if name == c.embedding else 100},
        } for name in names]

        def run(args):
            if calls is not None:
                calls.append(args)
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
                return deepcopy(deployments)
            if args[:3] == ["rest", "--method", "GET"]:
                name = unquote(urlsplit(args[args.index("--url") + 1]).path.rsplit("/", 1)[-1])
                deployment = deepcopy(next(item for item in deployments if item["name"] == name))
                if raw_limits is not None and name in raw_limits:
                    deployment["properties"]["rateLimits"] = raw_limits[name]
                return deployment
            raise AssertionError(f"Unexpected command: {args}")

        return run

    def test_readonly_pass_keeps_unverified_features_explicit(self):
        result = run_preflight(self.config, run=self.fake_az())
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(any("Frontier" in item for item in result["not_verified"]))
        for role, minimum in LAB_MINIMUM_TPM.items():
            check = next(item for item in result["checks"] if item["name"] == f"{role}_tpm")
            self.assertEqual((check["status"], check["observed"], check["expected"]), ("PASS", minimum, minimum))

    def test_each_role_blocks_below_its_minimum_without_rounding_up(self):
        for role, name in (
            ("agent", self.config.model), ("judge", self.config.judge),
            ("optimizer", self.config.optimizer), ("iq_planner", self.config.planner),
            ("embedding", self.config.embedding),
        ):
            with self.subTest(role=role):
                minimum = LAB_MINIMUM_TPM[role]
                for actual in (0, minimum - 1, minimum - .1):
                    limits = {name: [{"key": "token", "count": actual, "renewalPeriod": 60}]}
                    result = run_preflight(self.config, run=self.fake_az(limits=limits))
                    self.assertEqual(result["status"], "BLOCKED")
                    check = next(item for item in result["checks"] if item["name"] == f"{role}_tpm")
                    self.assertEqual(check["status"], "BLOCKED")
                    self.assertLess(check["observed"], check["expected"])

    def test_token_limits_are_not_multiplied_by_sku_capacity(self):
        limits = {self.config.model: [{"key": "token", "count": 20_000, "renewalPeriod": 60}]}
        result = run_preflight(self.config, run=self.fake_az(limits=limits))
        check = next(item for item in result["checks"] if item["name"] == "agent_tpm")
        self.assertEqual((check["status"], check["observed"]), ("BLOCKED", 20_000))
        self.assertEqual(result["models"]["agent"]["sku"]["capacity"], 100)

    def test_raw_arm_recovers_omitted_cli_labels_once_per_shared_deployment(self):
        calls = []
        unlabeled = [{"count": 100, "renewalPeriod": 60}, {"count": 100_000, "renewalPeriod": 60}]
        result = run_preflight(self.config, run=self.fake_az(
            limits={self.config.optimizer: unlabeled},
            raw_limits={self.config.optimizer: [{"key": "token", "count": 100_000, "renewalPeriod": 60}]},
            calls=calls,
        ))
        self.assertEqual(result["status"], "PASS")
        requests = [args for args in calls if args[0] == "rest"]
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0][1:3], ["--method", "GET"])
        self.assertEqual(result["models"]["optimizer"]["rate_limit_source"], "Raw ARM deployment metadata")
        self.assertEqual(result["models"]["iq_planner"]["tokens_per_minute"], result["models"]["optimizer"]["tokens_per_minute"])

    def test_missing_malformed_or_request_only_metadata_never_passes_as_tpm(self):
        cases = [
            None, [], "invalid", [None], [{"key": "request", "count": 1_000_000, "renewalPeriod": 60}],
            [{"count": 1_000_000, "renewalPeriod": 60}],
        ]
        for field, value in (
            ("count", None), ("count", True), ("count", -1), ("count", "100000"),
            ("count", float("nan")), ("count", float("inf")), ("count", 10 ** 400),
            ("count", 1e308),
            ("renewalPeriod", 0), ("renewalPeriod", -1), ("renewalPeriod", True),
            ("renewalPeriod", "60"), ("renewalPeriod", float("nan")), ("renewalPeriod", float("inf")),
            ("renewalPeriod", 10 ** 400),
        ):
            limit = {"key": "token", "count": 100_000, "renewalPeriod": 60}
            limit[field] = value
            cases.append([limit])
        for limits in cases:
            with self.subTest(limits=limits):
                result = run_preflight(self.config, run=self.fake_az(limits={self.config.model: limits}))
                check = next(item for item in result["checks"] if item["name"] == "agent_tpm")
                self.assertEqual((result["status"], check["status"]), ("BLOCKED", "BLOCKED"))
                self.assertIsNone(check["observed"])
                self.assertTrue(check["reason"])
                json.dumps(result, allow_nan=False)

    def test_token_periods_are_normalized_and_all_windows_respected(self):
        limits = [
            {"key": "request", "count": 600, "renewalPeriod": 60},
            {"key": "token", "count": 50_000.0, "renewalPeriod": 30.0},
            {"key": "token", "count": 2_000, "renewalPeriod": 1},
        ]
        self.assertEqual(_tokens_per_minute(limits), 100_000)
        limits.append({"key": "token", "count": 15_000, "renewalPeriod": 10})
        self.assertEqual(_tokens_per_minute(limits), 90_000)
        limits[1]["count"] = None
        with self.assertRaises(ValueError):
            _tokens_per_minute(limits)

    def test_raw_arm_failure_or_wrong_resource_does_not_become_a_pass(self):
        original = self.fake_az(limits={self.config.model: []})
        for failure in ("permission", "wrong_resource", "invalid_properties"):
            def failed(args):
                if args[0] == "rest":
                    if failure == "permission":
                        raise LabError("Forbidden")
                    if failure == "invalid_properties":
                        return {
                            "name": self.config.model,
                            "id": f"{self.config.account_id}/deployments/{self.config.model}",
                            "properties": None,
                        }
                    return {"name": self.config.model, "id": "/foreign/deployment"}
                return original(args)
            with self.subTest(failure=failure), self.assertRaises(LabError):
                run_preflight(self.config, run=failed)

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
