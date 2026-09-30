from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit
from uuid import UUID, uuid4, uuid5

from lab import bootstrap as b


ROOT = Path(__file__).resolve().parents[1]
SUB = "11111111-1111-4111-8111-111111111111"
TENANT = "22222222-2222-4222-8222-222222222222"
OPERATOR = "33333333-3333-4333-8333-333333333333"
USER = "operator@example.invalid"
DEPRECATED_ERROR = {
    "code": "InvalidTemplateDeployment",
    "message": "The template deployment failed validation.",
    "details": [{
        "code": "ServiceModelDeprecated",
        "message": (
            "Model gpt-4o-mini version 2024-07-18 is deprecated since 03/31/2026. "
            f"Operator {USER}; scope /subscriptions/{SUB}/resourceGroups/private-group. "
            "Authorization: Bearer secret-token; api-key=private-key"
        ),
    }],
}


class FakeAzure:
    def __init__(self, config_path):
        self.path = Path(config_path)
        self.config = json.loads(self.path.read_text())
        self.calls = []
        self.mutations = []
        self.remote = {}
        self.catalog = []
        self.usage = []
        self.account = {
            "id": SUB, "tenantId": TENANT, "state": "Enabled",
            "user": {"name": USER, "type": "user"},
        }
        self.user = {"id": OPERATOR, "userPrincipalName": USER}
        self.permissions = {"value": [{"actions": ["*"], "notActions": []}]}
        self.provider_state = "Registered"
        self.fail_submit = False
        self.fail_group = False
        self.fail_after_submit = False
        self.fail_terminal = False
        self.validation_error = None
        self.validation_result = {"properties": {"provisioningState": "Succeeded"}, "error": None}
        self.operations = []
        self.running = False
        for model in self.config["models"]:
            quota_model = "gpt4.1-mini" if model["name"] == "gpt-4.1-mini" else model["name"]
            key = f"OpenAI.{model['sku']}.{quota_model}"
            self.catalog.append({
                "kind": "AIServices",
                "model": {
                    "format": "OpenAI", "name": model["name"], "version": model["version"],
                    "lifecycleStatus": "Legacy" if model["name"] == "gpt-4.1-mini" else "GenerallyAvailable",
                    "capabilities": {"fineTune": "true"},
                    "skus": [{
                        "name": model["sku"], "usageName": key,
                        "capacity": {"default": 10, "maximum": 10000, "minimum": None, "step": None},
                        "rateLimits": [{"count": 1, "renewalPeriod": 60}, {"count": 1000, "renewalPeriod": 60}],
                    }],
                },
            })
            if not any(row["name"]["value"] == key for row in self.usage):
                self.usage.append({"name": {"value": key}, "limit": 100, "currentValue": 0, "unit": "Count"})

    def manifest(self):
        return json.loads((self.path.parent / "manifest.json").read_text())

    def _receipt(self, resource_id):
        manifest = self.manifest()
        assert any(resource_id in attempt["pending_ids"] for attempt in manifest["attempts"])
        assert any(r["id"] == resource_id and r["status"] != "planned" for r in manifest["resources"].values())

    def _populate(self, parameters):
        config = self.config
        specs = b._resources(config)
        for key, spec in specs.items():
            if key == "resource_group":
                continue
            self._receipt(spec["id"])
            row = {
                "id": spec["id"], "type": spec["type"],
                "properties": {"provisioningState": "Succeeded"},
            }
            props = row["properties"]
            if spec["taggable"]:
                row["tags"] = b._tags(config)
            if key in b.RESOURCE_TYPES:
                row["location"] = b.REGION
            if key in {"account", "project", "search"}:
                row["identity"] = {
                    "type": "SystemAssigned",
                    "principalId": str(uuid5(UUID(OPERATOR), key)),
                }
            if key == "account":
                row.update(kind="AIServices", sku={"name": "S0"})
                props.update(disableLocalAuth=True, allowProjectManagement=True)
            elif key == "search":
                row["sku"] = {"name": "basic"}
                props.update(provisioningState="succeeded", status="running", disableLocalAuth=True,
                             partitionCount=1, replicaCount=1, semanticSearch="free")
            elif key == "workspace":
                props.update(
                    sku={"name": "PerGB2018"}, retentionInDays=config["retention_days"],
                    features={"disableLocalAuth": True}, workspaceCapping={"dailyQuotaGb": 1},
                )
            elif key == "insights":
                props.update(
                    WorkspaceResourceId=specs["workspace"]["id"], DisableLocalAuth=True,
                    ConnectionString="InstrumentationKey=fixture;IngestionEndpoint=https://example.invalid",
                )
            elif key.startswith("model:"):
                row["sku"] = spec["sku"]
                props.update(
                    model={"format": "OpenAI", "name": spec["model"]["name"], "version": spec["model"]["version"]},
                    versionUpgradeOption="NoAutoUpgrade",
                )
            elif key == "search_connection":
                props.update(
                    metadata={"lab_instance": config["instance_id"]}, authType="AAD",
                    target=f"https://{config['names']['search']}.search.windows.net",
                )
            elif key == "insights_connection":
                props.update(
                    category="AppInsights", authType="ProjectManagedIdentity",
                    target=specs["insights"]["id"], isSharedToAll=False,
                    metadata={
                        "ResourceId": specs["insights"]["id"], "lab_instance": config["instance_id"],
                        "ApplicationInsightsConnectionString": "InstrumentationKey=fixture;IngestionEndpoint=https://example.invalid",
                    },
                )
            elif key.startswith("role:"):
                role = spec["role"]
                props.update(
                    principalId=OPERATOR if role["principal"] == "operator" else str(uuid5(UUID(OPERATOR), role["principal"])),
                    roleDefinitionId=f"/subscriptions/{SUB}/providers/Microsoft.Authorization/roleDefinitions/{role['role_id']}",
                    scope=role["scope"], description=role["description"],
                )
            elif key == "arm_deployment":
                props.update(
                    provisioningState="Running" if self.running else "Succeeded",
                    mode="Incremental", parameters=parameters["parameters"],
                )
            self.remote[spec["id"].lower()] = row

    def __call__(self, args):
        self.calls.append(args)
        if args[:2] == ["account", "show"]:
            return deepcopy(self.account)
        if args[:5] == [
            "rest", "--method", "GET", "--url", "https://graph.microsoft.com/v1.0/me?$select=id,userPrincipalName",
        ]:
            assert args[5:] == ["--resource", "https://graph.microsoft.com", "--subscription", self.config["subscription_id"]]
            return deepcopy(self.user)
        if args[:2] == ["provider", "show"]:
            return {"registrationState": self.provider_state}
        if args[:3] == ["cognitiveservices", "model", "list"]:
            return deepcopy(self.catalog)
        if args[:3] == ["cognitiveservices", "usage", "list"]:
            return deepcopy(self.usage)
        if args[:2] == ["resource", "list"]:
            return [r for r in deepcopy(self.remote).values() if r.get("type") != "Microsoft.Resources/resourceGroups"]
        if args[:4] == ["deployment", "operation", "group", "list"]:
            return deepcopy(self.operations)
        if args[:3] == ["deployment", "group", "validate"]:
            assert args[args.index("--validation-level") + 1] == "Provider"
            assert args[args.index("--mode") + 1] == "Incremental"
            assert Path(args[args.index("--template-file") + 1]).name == "template.json"
            if self.validation_error:
                raise b._azure_error("ERROR: " + json.dumps(self.validation_error), "", args)
            return deepcopy(self.validation_result)
        if args[:3] == ["deployment", "group", "create"]:
            self.mutations.append(args)
            assert args[args.index("--mode") + 1] == "Incremental"
            assert args[args.index("--subscription") + 1] == SUB
            assert args[args.index("--resource-group") + 1] == self.config["names"]["resource_group"]
            assert "--no-wait" in args
            if self.fail_submit:
                self.fail_submit = False
                raise b.AzureCommandError("DeploymentFailed")
            path = Path(args[args.index("--parameters") + 1].removeprefix("@"))
            self._populate(json.loads(path.read_text()))
            if self.fail_terminal:
                self.fail_terminal = False
                spec = b._resources(self.config)["arm_deployment"]
                self.remote[spec["id"].lower()]["properties"].update(
                    provisioningState="Failed",
                    error={"code": "DeploymentFailed", "message": "Provider failed this attempt."},
                )
            if self.fail_after_submit:
                self.fail_after_submit = False
                raise b.BootstrapError("Submission result unknown")
            return None
        if args[:3] == ["deployment", "group", "what-if"]:
            return {"changes": []}
        if args[0] == "rest":
            url = args[args.index("--url") + 1]
            parsed = urlsplit(url)
            method = args[args.index("--method") + 1]
            if method == "GET":
                if parsed.path.endswith("/permissions"):
                    return deepcopy(self.permissions)
                if parsed.path.endswith("/modelCapacities"):
                    query = parse_qs(parsed.query)
                    selected = {
                        m["sku"] for m in self.config["models"]
                        if m["name"] == query["modelName"][0] and m["version"] == query["modelVersion"][0]
                    }
                    return {"value": [{"properties": {
                        "skuName": sku, "availableCapacity": 100,
                        "model": {"name": query["modelName"][0], "version": query["modelVersion"][0]},
                    }} for sku in selected]}
                if parsed.path.lower() not in self.remote:
                    if "/providers/Microsoft.Resources/deployments/" in parsed.path:
                        raise b.AzureCommandError("DeploymentNotFound")
                    if "/projects/" in parsed.path or "/deployments/" in parsed.path:
                        raise b.AzureCommandError("ParentResourceNotFound")
                    raise b.AzureCommandError("ResourceNotFound")
                return deepcopy(self.remote[parsed.path.lower()])
            if method == "PUT":
                self.mutations.append(args)
                self._receipt(parsed.path)
                assert "If-None-Match=*" in args
                if self.fail_group:
                    self.fail_group = False
                    raise b.AzureCommandError("CliTimeout", command=args, stderr="Group submission unknown")
                if parsed.path.lower() in self.remote:
                    raise b.AzureCommandError("PreconditionFailed")
                row = json.loads(args[args.index("--body") + 1])
                row.update(id=parsed.path, type="Microsoft.Resources/resourceGroups", properties={"provisioningState": "Succeeded"})
                self.remote[parsed.path.lower()] = row
                return deepcopy(row)
        raise AssertionError(f"Unexpected command: {args}")


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.root = ROOT / "tests" / f".bootstrap-test-{uuid4().hex}"
        self.addCleanup(lambda: shutil.rmtree(self.root) if self.root.exists() else None)
        planned = b.plan(
            subscription_id=SUB, tenant_id=TENANT, expected_user=USER,
            environment="lab-unit", root=self.root,
        )
        self.path = Path(planned["config_path"])
        self.config = json.loads(self.path.read_text())
        self.azure = FakeAzure(self.path)

    def approve(self, **changes):
        now = datetime.now(timezone.utc)
        approval = b.approval_template(self.config)
        approval.update(
            approved=True, approved_by=USER, currency="USD", budget_amount=10,
            approved_at=(now - timedelta(minutes=1)).isoformat(),
            expires_at=(now + timedelta(minutes=30)).isoformat(),
            max_hosting_hours=1, max_wait_seconds=60, max_calls=20, max_candidates=2,
            allow_global_inference=True, acknowledge_continuous_hosting=True,
            allow_resource_creation=True, allow_rbac_assignments=True,
            acknowledge_unknown_cost=True, accept_deprecated_models=True,
        )
        approval.update(changes)
        path = self.path.parent / f"approval-{uuid4().hex}.json"
        path.write_text(json.dumps(approval))
        return path

    def apply(self, **kwargs):
        return b.apply(self.path, self.approve(), run=self.azure, **kwargs)

    def test_plan_is_local_private_and_does_not_write_runtime_env(self):
        self.assertEqual(self.azure.calls, [])
        self.assertFalse((self.path.parent / ".env").exists())
        self.assertTrue((self.path.parent / "artifacts").is_dir())
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)
        manifest = self.azure.manifest()
        self.assertTrue(all(r["status"] == "planned" for r in manifest["resources"].values()))
        self.assertRegex(self.config["names"]["resource_group"], r"^rg-foundry-eval-v11-\d{8}-[a-f0-9]{8}$")
        self.assertFalse(json.loads((self.path.parent / "approval.example.json").read_text())["approved"])

    def test_plan_never_overwrites_an_environment_or_existing_dotenv(self):
        (self.root / ".env").write_text("unrelated")
        with self.assertRaises(b.BootstrapError):
            b.plan(subscription_id=SUB, tenant_id=TENANT, expected_user=USER, environment="lab-unit", root=self.root)
        self.assertEqual((self.root / ".env").read_text(), "unrelated")

    def test_standalone_help_works_without_site_packages(self):
        result = subprocess.run(
            [sys.executable, "-S", "-m", "lab.bootstrap", "--help"],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("preflight", result.stdout)

    def test_preflight_has_no_resource_dependency_or_cloud_mutation(self):
        report = b.preflight(self.path, run=self.azure)
        self.assertEqual(report["status"], "BLOCKED_AWAITING_APPROVAL", report)
        self.assertEqual(report["readiness_status"], "READY")
        self.assertEqual(report["approval_status"], "MISSING")
        self.assertEqual(report["live_status"], "NOT_VERIFIED")
        self.assertEqual(report["owned_resource_count"], 0)
        self.assertEqual(self.azure.mutations, [])
        model_index = next(i for i, a in enumerate(self.azure.calls) if a[:3] == ["cognitiveservices", "model", "list"])
        group_index = next(i for i, a in enumerate(self.azure.calls) if any(self.config["names"]["resource_group"] in s for s in a))
        self.assertLess(model_index, group_index)
        for identity in (SUB, TENANT, OPERATOR, USER):
            self.assertNotIn(identity, json.dumps(report))
        self.assertEqual(report["models"][0]["free_available_units"], 100)
        self.assertFalse(report["models"][0]["deprecated"])
        self.assertEqual(report["models"][0]["lifecycle"], ["Legacy"])
        self.assertIn("model-specific", report["models"][0]["capacity_unit"])

    def test_wrong_active_identity_stops_before_resource_queries(self):
        self.azure.account["tenantId"] = str(uuid4())
        self.assertEqual(b.preflight(self.path, run=self.azure)["status"], "BLOCKED")
        self.assertEqual(len(self.azure.calls), 1)

    def test_graph_identity_mismatch_is_not_inferred_from_subscription(self):
        self.azure.user["userPrincipalName"] = "someone-else@example.invalid"
        self.assertEqual(b.preflight(self.path, run=self.azure)["status"], "BLOCKED")
        self.assertEqual(len(self.azure.calls), 2)

    def test_provider_and_permission_failures_never_register_or_escalate(self):
        self.azure.provider_state = "NotRegistered"
        self.assertEqual(b.preflight(self.path, run=self.azure)["status"], "BLOCKED")
        self.assertEqual(self.azure.mutations, [])
        self.azure.provider_state = "Registered"
        self.azure.permissions = {"value": [{"actions": ["*"], "notActions": ["Microsoft.Authorization/*/write"]}]}
        self.assertEqual(b.preflight(self.path, run=self.azure)["status"], "BLOCKED")
        self.assertEqual(self.azure.mutations, [])

    def test_missing_exact_version_and_quota_fail_closed(self):
        self.azure.catalog[0]["model"]["version"] = "a-different-version"
        self.assertEqual(b.preflight(self.path, run=self.azure)["status"], "BLOCKED")
        self.azure = FakeAzure(self.path)
        self.azure.usage[0]["name"]["value"] += "-finetune"
        self.assertEqual(b.preflight(self.path, run=self.azure)["status"], "BLOCKED")

    def test_finetuned_sku_is_not_confused_with_base_sku(self):
        fine = deepcopy(self.azure.catalog[0]["model"]["skus"][0])
        fine["usageName"] += "-finetune"
        fine["capacity"]["default"] = 50
        self.azure.catalog[0]["model"]["skus"].append(fine)
        self.assertEqual(b.preflight(self.path, run=self.azure)["readiness_status"], "READY")

    def test_explicit_standard_agent_plan_preserves_model_family_and_other_roles(self):
        planned = b.plan(
            subscription_id=SUB, tenant_id=TENANT, expected_user=USER,
            environment="lab-standard", root=self.root, agent_sku="Standard",
        )
        path = Path(planned["config_path"])
        config = json.loads(path.read_text())
        agent = next(model for model in config["models"] if "agent" in model["roles"])
        self.assertEqual((agent["name"], agent["version"], agent["sku"]), ("gpt-4.1-mini", "2025-04-14", "Standard"))
        self.assertTrue(all(m["sku"] == "GlobalStandard" for m in config["models"] if "agent" not in m["roles"]))
        fake = FakeAzure(path)
        report = b.preflight(path, run=fake)
        self.assertEqual(report["readiness_status"], "READY")
        selected = next(m for m in report["models"] if "agent" in m["roles"])
        self.assertEqual(selected["usage_name"], "OpenAI.Standard.gpt4.1-mini")
        fake.usage[0]["name"]["value"] = "OpenAI.Standard.gpt-4.1-mini"
        self.assertEqual(b.preflight(path, run=fake)["status"], "BLOCKED")
        self.assertEqual(self.config["models"][0]["sku"], "Standard")
        self.assertNotEqual(config["scope_sha256"], self.config["scope_sha256"])
        self.assertEqual(fake.mutations, [])

    def test_explicit_catalog_quota_pin_preserves_non_model_name_spelling(self):
        models = deepcopy(list(b.DEFAULT_MODELS))
        models[0]["usage_name"] = "OpenAI.Standard.gpt4.1-mini"
        planned = b.plan(
            subscription_id=SUB, tenant_id=TENANT, expected_user=USER, root=self.root,
            environment="lab-quota-pin", models=models,
        )
        fake = FakeAzure(planned["config_path"])
        report = b.preflight(planned["config_path"], run=fake)
        self.assertEqual(report["readiness_status"], "READY")
        self.assertEqual(report["models"][0]["usage_name"], "OpenAI.Standard.gpt4.1-mini")
        self.assertEqual(fake.mutations, [])

    def test_invented_quota_pin_and_finetune_quota_are_not_accepted_as_base(self):
        models = deepcopy(list(b.DEFAULT_MODELS))
        models[0]["usage_name"] = "OpenAI.Standard.gpt-4.1-mini"
        planned = b.plan(
            subscription_id=SUB, tenant_id=TENANT, expected_user=USER, root=self.root,
            environment="lab-bad-pin", models=models,
        )
        self.assertEqual(b.preflight(planned["config_path"], run=FakeAzure(planned["config_path"]))["status"], "BLOCKED")
        models[0]["usage_name"] = "OpenAI.Standard.gpt4.1-mini-finetune"
        with self.assertRaises(b.BootstrapError):
            b.plan(
                subscription_id=SUB, tenant_id=TENANT, expected_user=USER, root=self.root,
                environment="lab-ft-pin", models=models,
            )

    def test_ambiguous_catalog_quota_requires_an_explicit_pin(self):
        alternate = deepcopy(self.azure.catalog[0]["model"]["skus"][0])
        alternate["usageName"] = "OpenAI.Standard.another-base-quota"
        self.azure.catalog[0]["model"]["skus"].append(alternate)
        self.assertEqual(b.preflight(self.path, run=self.azure)["status"], "BLOCKED")
        self.assertEqual(self.azure.mutations, [])

    def test_available_quota_is_limit_minus_used_not_limit(self):
        self.azure.usage[0]["currentValue"] = 90
        self.assertEqual(b.preflight(self.path, run=self.azure)["status"], "BLOCKED")
        self.assertEqual(self.azure.mutations, [])

    def test_combined_deployments_cannot_double_spend_one_quota_family(self):
        models = deepcopy(list(b.DEFAULT_MODELS))
        for model in models[:3]:
            model["name"], model["version"], model["sku"] = "gpt-4.1-mini", "2025-04-14", "Standard"
        planned = b.plan(
            subscription_id=SUB, tenant_id=TENANT, expected_user=USER, environment="lab-shared",
            root=self.root, models=models,
        )
        fake = FakeAzure(planned["config_path"])
        fake.usage[0]["limit"] = 50
        # Deduplicate catalog entries like the real regional catalog, preserving one lifecycle.
        fake.catalog[1]["model"]["lifecycleStatus"] = "Legacy"
        fake.catalog[2]["model"]["lifecycleStatus"] = "Legacy"
        report = b.preflight(planned["config_path"], run=fake)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("all requested", report["reason"])

    def test_model_capacity_constraints_are_live_not_universal_tpm(self):
        bounds = self.azure.catalog[0]["model"]["skus"][0]["capacity"]
        bounds.update(minimum=1, step=3)
        self.assertEqual(b.preflight(self.path, run=self.azure)["status"], "BLOCKED")
        bounds.update(minimum=None, step=None, allowedValues=[10, 20])
        self.assertEqual(b.preflight(self.path, run=self.azure)["readiness_status"], "READY")

    def test_group_collision_refuses_even_with_copied_ownership_tags(self):
        group_id = b._ids(self.config)["resource_group"]
        self.azure.remote[group_id.lower()] = {
            "id": group_id, "tags": b._tags(self.config), "location": b.REGION,
        }
        report = b.preflight(self.path, run=self.azure)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertIn("collision", report["reason"])
        self.assertEqual(self.azure.mutations, [])

    def test_absent_approval_blocks_before_any_azure_call(self):
        with self.assertRaises(b.BootstrapError):
            b.apply(self.path, run=self.azure)
        self.assertEqual(self.azure.calls, [])

    def test_invalid_approvals_block_before_any_azure_call(self):
        cases = (
            {"approved": False}, {"budget_amount": 0}, {"budget_amount": float("inf")},
            {"budget_amount": True}, {"currency": None}, {"scope_sha256": "wrong"},
            {"models": []}, {"approved_by": "other@example.invalid"}, {"max_wait_seconds": 0},
            {"max_calls": -1}, {"max_candidates": True}, {"max_epochs": 1},
            {"allow_training": True}, {"allow_global_training": True}, {"allow_training": "false"},
            {"max_hosting_hours": 0}, {"retention_days": 90}, {"allow_global_inference": False},
            {"acknowledge_continuous_hosting": False}, {"acknowledge_unknown_cost": False},
            {"allow_resource_creation": False}, {"allow_rbac_assignments": False},
            {"expires_at": "2020-01-01T00:00:00+00:00"}, {"expires_at": "2999-01-01T00:00:00+00:00"},
            {"expires_at": "2026-01-01T00:00:00"},
            {"max_provisioning_retries": -1}, {"max_provisioning_retries": True},
            {"max_provisioning_retries": None},
        )
        for changes in cases:
            with self.subTest(changes=changes):
                with self.assertRaises(b.BootstrapError):
                    b.apply(self.path, self.approve(**changes), run=self.azure)
        self.assertEqual(self.azure.calls, [])

    def test_changed_config_invalidates_scope_before_remote_calls(self):
        config = deepcopy(self.config)
        config["location"] = "eastus"
        self.path.write_text(json.dumps(config))
        with self.assertRaises(b.BootstrapError):
            b.preflight(self.path, run=self.azure)
        self.assertEqual(self.azure.calls, [])

    def test_deprecating_model_requires_explicit_acceptance(self):
        self.azure.catalog[0]["model"]["lifecycleStatus"] = "Deprecating"
        with self.assertRaises(b.BootstrapError):
            b.apply(self.path, self.approve(accept_deprecated_models=False), run=self.azure)
        self.assertEqual(self.azure.mutations, [])

    def test_success_persists_pending_ids_incremental_scope_and_isolated_env(self):
        result = self.apply()
        self.assertEqual(result["status"], "APPLIED")
        self.assertEqual(len(self.azure.mutations), 2)
        manifest = self.azure.manifest()
        self.assertEqual(manifest["phase"], "succeeded")
        self.assertTrue(all(r["status"] == "succeeded" for r in manifest["resources"].values()))
        env = (self.path.parent / ".env").read_text()
        self.assertIn("LAB_ARTIFACTS_DIR=", env)
        self.assertIn(str(self.path.parent / "artifacts"), env)
        self.assertIn("Authorization=AAD", env)
        self.assertIn("EMBEDDING_DEPLOYMENT=", env)
        self.assertEqual((self.path.parent / ".env").stat().st_mode & 0o777, 0o600)

    def test_generated_env_preserves_paths_outside_repository_without_relative_to(self):
        config = deepcopy(self.config)
        config["environment_dir"] = "/standalone-foundry-environment/lab-unit"
        content = b._env(config, {}, self.path.parent / "approval.json")
        values = {
            key: json.loads(value) for key, value in (line.split("=", 1) for line in content.splitlines())
        }
        self.assertEqual(values["LAB_ARTIFACTS_DIR"], "/standalone-foundry-environment/lab-unit/artifacts")
        self.assertEqual(values["LAB_BOOTSTRAP_CONFIG"], "/standalone-foundry-environment/lab-unit/config.json")
        self.assertEqual(values["BOOTSTRAP_CONFIG"], values["LAB_BOOTSTRAP_CONFIG"])
        embedding = next(model for model in config["models"] if "embedding" in model["roles"])
        self.assertEqual(values["EMBEDDING_DEPLOYMENT"], embedding["deployment"])

    def test_successful_apply_is_readonly_on_resume_even_with_zero_free_quota(self):
        self.apply()
        old_env = (self.path.parent / ".env").read_bytes()
        artifact = self.path.parent / "artifacts" / "keep.txt"
        artifact.write_text("evidence")
        self.azure.mutations.clear()
        for row in self.azure.usage:
            row["currentValue"] = row["limit"]
        result = self.apply()
        self.assertEqual(result["status"], "APPLIED")
        self.assertEqual(self.azure.mutations, [])
        self.assertEqual((self.path.parent / ".env").read_bytes(), old_env)
        self.assertEqual(artifact.read_text(), "evidence")

    def test_failed_submission_without_remote_deployment_is_not_blindly_repeated(self):
        self.azure.fail_submit = True
        with self.assertRaises(b.BootstrapError):
            self.apply()
        manifest = self.azure.manifest()
        self.assertEqual(manifest["phase"], "interrupted")
        self.assertEqual(manifest["resources"]["account"]["status"], "pending")
        old_ids = {v["id"] for v in manifest["resources"].values()}
        self.azure.mutations.clear()
        for retry in (False, True):
            with self.subTest(retry=retry):
                with self.assertRaises(b.ProvisioningRetryError) as caught:
                    b.apply(self.path, self.approve(max_provisioning_retries=1), run=self.azure, retry=retry)
                self.assertEqual(caught.exception.code, "UNKNOWN_SUBMISSION")
        self.assertEqual(old_ids, {v["id"] for v in self.azure.manifest()["resources"].values()})
        self.assertEqual(self.azure.mutations, [])

    def test_unknown_submission_result_reconciles_without_redeployment(self):
        self.azure.fail_after_submit = True
        with self.assertRaises(b.BootstrapError):
            self.apply()
        self.azure.mutations.clear()
        self.assertEqual(self.apply()["status"], "APPLIED")
        self.assertEqual(self.azure.mutations, [])

    def test_resume_refuses_unknown_resources_foreign_tags_or_role_scope(self):
        self.apply()
        ids = b._ids(self.config)
        key = ids["search"].lower()
        original = deepcopy(self.azure.remote[key])
        self.azure.remote[key]["tags"]["lab_instance"] = "foreign"
        self.azure.mutations.clear()
        with self.assertRaises(b.BootstrapError):
            self.apply()
        self.azure.remote[key] = original
        unknown = f"{ids['resource_group']}/providers/Microsoft.Storage/storageAccounts/not-ours"
        self.azure.remote[unknown.lower()] = {"id": unknown}
        with self.assertRaises(b.BootstrapError):
            self.apply()
        del self.azure.remote[unknown.lower()]
        role_id = next(r["id"].lower() for k, r in self.azure.manifest()["resources"].items() if k.startswith("role:"))
        self.azure.remote[role_id]["properties"]["scope"] = f"/subscriptions/{SUB}"
        with self.assertRaises(b.BootstrapError):
            self.apply()
        self.assertEqual(self.azure.mutations, [])

    def test_missing_previously_owned_group_is_not_automatically_restored(self):
        self.apply()
        self.azure.remote.clear()
        self.azure.mutations.clear()
        with self.assertRaisesRegex(b.BootstrapError, "restore"):
            self.apply()
        self.assertEqual(self.azure.mutations, [])

    def test_unknown_existing_env_blocks_before_remote_calls(self):
        (self.path.parent / ".env").write_text("do not overwrite")
        with self.assertRaises(b.BootstrapError):
            self.apply()
        self.assertEqual(self.azure.calls, [])
        self.assertEqual((self.path.parent / ".env").read_text(), "do not overwrite")

    def test_status_is_readonly_and_redacts_identifiers(self):
        self.apply()
        self.azure.mutations.clear()
        report = b.status(self.path, run=self.azure)
        self.assertEqual(report["status"], "BLOCKED_AWAITING_APPROVAL")
        self.assertEqual(report["observation_status"], "OBSERVED")
        self.assertTrue(all(r["present"] for r in report["resources"].values()))
        self.assertEqual(self.azure.mutations, [])
        for identity in (SUB, TENANT, OPERATOR, USER):
            self.assertNotIn(identity, json.dumps(report))

    def test_what_if_requires_owned_group_but_not_cost_approval(self):
        with self.assertRaises(b.BootstrapError):
            b.apply(self.path, run=self.azure, what_if=True)
        self.assertEqual(self.azure.mutations, [])
        self.apply()
        self.azure.mutations.clear()
        self.assertEqual(b.apply(self.path, run=self.azure, what_if=True)["status"], "WHAT_IF_ONLY")
        self.assertEqual(self.azure.mutations, [])

    def test_wait_is_bounded_and_leaves_remote_deployment_alone(self):
        current = [0]
        self.azure.running = True
        with self.assertRaises(b.BootstrapError):
            b.apply(
                self.path, self.approve(max_wait_seconds=1), run=self.azure,
                sleep=lambda value: current.__setitem__(0, current[0] + value), clock=lambda: current[0],
            )
        self.assertEqual(current[0], 1)
        self.assertEqual(self.azure.manifest()["phase"], "interrupted")
        self.assertTrue(self.azure.remote)
        self.assertFalse(any("delete" in args for args in self.azure.calls))

    def test_cost_ledger_never_labels_unknown_cost_free(self):
        self.apply()
        ledger = json.loads((self.path.parent / "cost-ledger.json").read_text())
        self.assertEqual(ledger["currency"], "USD")
        self.assertTrue(all(row["estimated_cost"] is None for row in ledger["entries"]))
        search = next(row for row in ledger["entries"] if row["key"] == "search")
        self.assertEqual(search["sku"], {"name": "basic", "replicas": 1, "partitions": 1})
        self.assertIn("continuous", search["billing"])
        self.assertEqual(search["reference_unit_price"]["amount"], 0.101)
        self.assertEqual(search["reference_unit_price"]["currency"], "USD")
        self.assertEqual(search["reference_unit_price"]["indicative_24_hours"], 2.424)
        self.assertEqual(search["reference_unit_price"]["indicative_730_hours"], 73.73)
        self.assertEqual(len([row for row in ledger["entries"] if row["key"].startswith("fine_tun")]), 2)

    def test_all_role_bindings_are_scoped_to_new_specific_resources(self):
        ids = b._ids(self.config)
        for role in b._roles(self.config):
            self.assertIn(role["scope"], [ids[key] for key in b.RESOURCE_TYPES])
            self.assertNotEqual(role["scope"], ids["resource_group"])
            self.assertNotEqual(role["scope"], f"/subscriptions/{SUB}")
            self.assertNotIn(role["role_id"], {
                "8e3af657-a8ff-443c-a75c-2fe8c4bcb635",  # Owner
                "b24988ac-6180-42a0-ab88-20f7382dd24c",  # Contributor
            })

    def test_template_keyless_identity_pins_and_scope_contract(self):
        template = json.loads(b.TEMPLATE.read_text())
        resources = {r["type"]: r for r in template["resources"]}
        for key in ("account", "project", "search"):
            resource = resources[b.RESOURCE_TYPES[key][0]]
            self.assertEqual(resource["identity"]["type"], "SystemAssigned")
            self.assertEqual(resource["tags"], "[parameters('tags')]")
        search = resources["Microsoft.Search/searchServices"]["properties"]
        self.assertTrue(search["disableLocalAuth"])
        self.assertNotIn("authOptions", search)
        self.assertEqual((search["partitionCount"], search["replicaCount"]), (1, 1))
        self.assertEqual(resources["Microsoft.CognitiveServices/accounts/deployments"]["properties"]["versionUpgradeOption"], "NoAutoUpgrade")
        connections = [r for r in template["resources"] if r["type"] == "Microsoft.CognitiveServices/accounts/projects/connections"]
        search_connection = next(r for r in connections if r["properties"]["category"] == "CognitiveSearch")
        self.assertEqual(search_connection["properties"]["authType"], "AAD")
        self.assertNotIn("Microsoft.Resources/deployments", resources)
        self.assertEqual(template["parameters"]["location"]["allowedValues"], [b.REGION])

    def test_trace_connection_uses_published_project_identity_contract_and_publisher_role(self):
        template = json.loads(b.TEMPLATE.read_text())
        connections = [
            r for r in template["resources"]
            if r["type"] == "Microsoft.CognitiveServices/accounts/projects/connections"
            and r["properties"]["category"] == "AppInsights"
        ]
        self.assertEqual(len(connections), 1)
        connection = connections[0]
        self.assertEqual(connection["apiVersion"], "2026-07-01")
        self.assertEqual(connection["properties"]["authType"], "ProjectManagedIdentity")
        self.assertEqual(connection["properties"]["target"], "[resourceId('Microsoft.Insights/components', parameters('names').insights)]")
        self.assertEqual(connection["properties"]["metadata"]["ResourceId"], connection["properties"]["target"])
        self.assertEqual(connection["properties"]["metadata"][b.TRACE_ROUTING_KEY], b.TRACE_ROUTING_EXPRESSION)
        self.assertNotIn("credentials", connection["properties"])
        self.assertNotIn("useWorkspaceManagedIdentity", connection["properties"])
        self.assertIn("labRoleAssignments", connection["dependsOn"])
        roles = b._roles(self.config)
        publisher = next(role for role in roles if role["key"] == "project-telemetry")
        self.assertEqual(publisher["principal"], "project")
        self.assertEqual(publisher["role_id"], b.ROLE_IDS["monitor_publisher"])
        self.assertEqual(publisher["scope"], b._ids(self.config)["insights"])
        spec = self.azure.manifest()["resources"]["insights_connection"]
        self.assertTrue(spec["id"].endswith("/connections/lab-appinsights"))
        self.assertEqual(spec["api_version"], "2026-07-01")
        self.assertFalse(spec["taggable"])

    def test_project_models_and_connections_are_explicitly_serialized(self):
        resources = json.loads(b.TEMPLATE.read_text())["resources"]
        models = next(r for r in resources if r.get("copy", {}).get("name") == "modelDeployments")
        project_id = "[resourceId('Microsoft.CognitiveServices/accounts/projects', parameters('names').account, parameters('names').project)]"
        self.assertIn(project_id, models["dependsOn"])
        search = next(r for r in resources if r.get("properties", {}).get("category") == "CognitiveSearch")
        insights = next(r for r in resources if r.get("properties", {}).get("category") == "AppInsights")
        self.assertIn("modelDeployments", search["dependsOn"])
        self.assertIn("modelDeployments", insights["dependsOn"])
        self.assertIn(
            "[resourceId('Microsoft.CognitiveServices/accounts/projects/connections', parameters('names').account, parameters('names').project, 'lab-search')]",
            insights["dependsOn"],
        )

    def dependency_repair_fixture(self):
        original = json.loads(b.TEMPLATE.read_text())
        for resource in original["resources"]:
            if resource.get("copy", {}).get("name") == "modelDeployments":
                resource["dependsOn"] = ["[resourceId('Microsoft.CognitiveServices/accounts', parameters('names').account)]"]
            if resource.get("properties", {}).get("category") in {"CognitiveSearch", "AppInsights"}:
                resource["dependsOn"] = [
                    dependency for dependency in resource["dependsOn"]
                    if dependency != "modelDeployments"
                    and "accounts/projects/connections" not in dependency
                ]
        original_path = self.root / "old-template.json"
        original_path.write_text(json.dumps(original, indent=3) + "\n")
        with patch.object(b, "TEMPLATE", original_path):
            result = b.plan(
                subscription_id=SUB, tenant_id=TENANT, expected_user=USER,
                root=self.root, environment="lab-repair",
            )
            self.path = Path(result["config_path"])
            self.config = b._read(self.path)
            self.azure = FakeAzure(self.path)
            approval = self.approve()
            self.azure.fail_terminal = True
            with self.assertRaises(b.AzureCommandError):
                b.apply(self.path, approval, run=self.azure)
        resources = b._resources(self.config)
        for key in ("project", "search_connection", "insights_connection"):
            self.azure.remote.pop(resources[key]["id"].lower(), None)
        for key, spec in resources.items():
            if key.startswith("role:"):
                self.azure.remote.pop(spec["id"].lower(), None)
        deployment = self.azure.remote[resources["arm_deployment"]["id"].lower()]
        deployment["properties"]["correlationId"] = str(uuid4())
        deployment["properties"]["error"] = {
            "code": "DeploymentFailed", "details": [{"code": "RequestConflict", "message": "Another account write is in progress."}],
        }
        for value in deployment["properties"]["parameters"].values():
            value["type"] = "Object"
        operations = [{
            "id": deployment["id"] + "/operations/project-create",
            "properties": {
                "provisioningState": "Failed", "targetResource": {"id": resources["project"]["id"]},
                "statusMessage": {"error": {"code": "RequestConflict", "message": "Another operation is in progress."}},
            },
        }]
        b._write(self.path.parent / "evidence" / "first-apply-failed-deployment.local.json", deployment)
        b._write(self.path.parent / "evidence" / "first-apply-operations.local.json", operations)
        self.azure.mutations.clear()
        self.azure.calls.clear()
        return approval

    def test_dependency_only_repair_archives_exact_bytes_and_retains_same_scope_resources(self):
        approval = self.dependency_repair_fixture()
        originals = {
            name: (self.path.parent / name).read_bytes()
            for name in ("config.json", "template.json", "manifest.json", "cost-ledger.json")
        }
        approval_bytes = approval.read_bytes()
        failure = self.path.parent / "evidence" / "first-apply-failed-deployment.local.json"
        failure_bytes = failure.read_bytes()
        with self.assertRaises(b.BootstrapError):
            b.preflight(self.path, run=self.azure)
        result = b.repair_dependencies(self.path, approval, max_provisioning_retries=2, run=self.azure)
        self.assertEqual(result["status"], "DEPENDENCY_REPAIR_READY")
        self.assertEqual(self.azure.mutations, [])
        archive = Path(result["archive_path"]) / "original"
        for name, content in originals.items():
            self.assertEqual((archive / name).read_bytes(), content)
            self.assertEqual((archive / name).stat().st_mode & 0o777, 0o600)
        self.assertEqual((archive / "approval.original.json").read_bytes(), approval_bytes)
        self.assertEqual(approval.read_bytes(), approval_bytes)
        self.assertEqual((archive / "evidence" / failure.name).read_bytes(), failure_bytes)
        self.assertEqual(failure.read_bytes(), failure_bytes)
        _, current, manifest = b._load(self.path)
        self.assertEqual(current["instance_id"], self.config["instance_id"])
        self.assertEqual(b._resources(current), b._resources(self.config))
        self.assertNotEqual(current["scope_sha256"], self.config["scope_sha256"])
        self.assertEqual(manifest["attempts"], json.loads(originals["manifest.json"])["attempts"])
        bound = b._read(Path(result["approval_path"]))
        self.assertEqual(bound["max_provisioning_retries"], 2)
        self.assertEqual(bound["models"], self.config["models"])
        self.assertEqual(b.repair_dependencies(self.path, approval, max_provisioning_retries=2, run=self.azure)["status"], "DEPENDENCY_REPAIR_ALREADY_APPLIED")
        with self.assertRaises(b.ProvisioningRetryError):
            b.apply(self.path, result["approval_path"], run=self.azure)
        self.assertEqual(b.apply(self.path, result["approval_path"], run=self.azure, retry=True)["status"], "APPLIED")
        self.assertEqual(len(self.azure.mutations), 1)
        self.assertEqual(self.azure.mutations[0][:3], ["deployment", "group", "create"])

    def test_dependency_repair_rejects_non_dependency_changes_before_azure(self):
        approval = self.dependency_repair_fixture()
        changed = json.loads(b.TEMPLATE.read_text())
        search = next(r for r in changed["resources"] if r["type"] == "Microsoft.Search/searchServices")
        search["sku"]["name"] = "standard"
        candidate = self.root / "unsafe-template.json"
        candidate.write_text(json.dumps(changed))
        original = self.path.read_bytes()
        with patch.object(b, "TEMPLATE", candidate):
            with self.assertRaisesRegex(b.BootstrapError, "semantic change"):
                b.repair_dependencies(self.path, approval, max_provisioning_retries=2, run=self.azure)
        self.assertEqual(self.azure.calls, [])
        self.assertEqual(self.path.read_bytes(), original)

    def test_dependency_repair_blocks_unknown_outcome_and_wrong_failure_proof(self):
        approval = self.dependency_repair_fixture()
        arm = b._resources(self.config)["arm_deployment"]["id"].lower()
        self.azure.remote[arm]["properties"]["provisioningState"] = "Running"
        with self.assertRaises(b.BootstrapError):
            b.repair_dependencies(self.path, approval, max_provisioning_retries=2, run=self.azure)
        self.azure.remote[arm]["properties"]["provisioningState"] = "Failed"
        operation_file = self.path.parent / "evidence" / "first-apply-operations.local.json"
        operations = json.loads(operation_file.read_text())
        operations[0]["properties"]["targetResource"]["id"] = b._ids(self.config)["account"]
        operation_file.write_text(json.dumps(operations))
        with self.assertRaises(b.BootstrapError):
            b.repair_dependencies(self.path, approval, max_provisioning_retries=2, run=self.azure)
        self.assertEqual(self.azure.mutations, [])

    def test_dependency_repair_rejects_expanded_retry_allowance(self):
        approval = self.dependency_repair_fixture()
        for count in (0, 3, True, None):
            with self.subTest(count=count):
                with self.assertRaises(b.ApprovalError):
                    b.repair_dependencies(self.path, approval, max_provisioning_retries=count, run=self.azure)
        self.assertEqual(self.azure.calls, [])

    def test_dependency_repair_validation_failure_leaves_original_plan_and_evidence_intact(self):
        approval = self.dependency_repair_fixture()
        originals = {name: (self.path.parent / name).read_bytes() for name in ("config.json", "template.json", "manifest.json")}
        self.azure.validation_error = {"code": "ValidationFailed", "message": "Fixture rejection"}
        with self.assertRaises(b.AzureCommandError):
            b.repair_dependencies(self.path, approval, max_provisioning_retries=2, run=self.azure)
        self.assertEqual({name: (self.path.parent / name).read_bytes() for name in originals}, originals)
        self.assertTrue(list((self.path.parent / ".repairs").glob("*/original/manifest.json")))
        self.assertFalse((self.path.parent / "dependency-repair.pending.json").exists())
        self.assertEqual(self.azure.mutations, [])

    def test_dependency_repair_partial_local_write_rolls_back_without_touching_azure(self):
        approval = self.dependency_repair_fixture()
        names = ("config.json", "template.json", "manifest.json", "cost-ledger.json")
        originals = {name: (self.path.parent / name).read_bytes() for name in names}
        write = b._write_bytes
        raised = [False]

        def fail_once(path, content, *, replace=False):
            if path == self.path.parent / "template.json" and replace and content != originals["template.json"] and not raised[0]:
                raised[0] = True
                raise OSError("Simulated local write interruption")
            return write(path, content, replace=replace)

        with patch.object(b, "_write_bytes", side_effect=fail_once):
            with self.assertRaises(OSError):
                b.repair_dependencies(self.path, approval, max_provisioning_retries=2, run=self.azure)
        self.assertTrue(raised[0])
        self.assertEqual({name: (self.path.parent / name).read_bytes() for name in names}, originals)
        self.assertFalse((self.path.parent / "dependency-repair.pending.json").exists())
        self.assertEqual(self.azure.mutations, [])

    def trace_routing_repair_fixture(self):
        original = json.loads(b.TEMPLATE.read_text())
        trace = next(r for r in original["resources"] if r.get("properties", {}).get("category") == "AppInsights")
        trace["properties"]["metadata"].pop(b.TRACE_ROUTING_KEY)
        original_path = self.root / "missing-routing-template.json"
        original_path.write_text(json.dumps(original, indent=2) + "\n")
        with patch.object(b, "TEMPLATE", original_path):
            planned = b.plan(
                subscription_id=SUB, tenant_id=TENANT, expected_user=USER,
                root=self.root, environment="lab-routing",
            )
            self.path = Path(planned["config_path"])
            self.config = b._read(self.path)
            self.azure = FakeAzure(self.path)
            approval = self.approve(max_provisioning_retries=2)
            for retry in (False, True):
                self.azure.fail_terminal = True
                with self.assertRaises(b.AzureCommandError):
                    b.apply(self.path, approval, run=self.azure, retry=retry)
        specs = b._resources(self.config)
        self.azure.remote.pop(specs["insights_connection"]["id"].lower())
        deployment = self.azure.remote[specs["arm_deployment"]["id"].lower()]
        deployment["properties"]["correlationId"] = str(uuid4())
        error = {"code": "ValidationError", "message": "Required metadata property ApplicationInsightsConnectionString is missing"}
        deployment["properties"]["error"] = {"code": "DeploymentFailed", "details": [error]}
        self.azure.operations = [{
            "id": deployment["id"] + "/operations/trace",
            "properties": {
                "provisioningState": "Failed", "targetResource": {"id": specs["insights_connection"]["id"]},
                "statusMessage": {"error": error},
            },
        }]
        summary = [{
            "resource": f"{self.config['names']['account']}/{self.config['names']['project']}/lab-appinsights",
            "state": "Failed", "error": {"error": error, "status": "Failed"},
        }]
        b._write(self.path.parent / "evidence" / "retry1-failed-deployment.local.json", deployment)
        b._write(self.path.parent / "evidence" / "retry1-operations.local.json", summary)
        self.azure.calls.clear()
        self.azure.mutations.clear()
        return approval

    def test_trace_routing_repair_is_separately_audited_and_does_not_reset_retry_budget(self):
        approval = self.trace_routing_repair_fixture()
        original = {name: (self.path.parent / name).read_bytes() for name in ("config.json", "template.json", "manifest.json")}
        approval_bytes = approval.read_bytes()
        attempts = deepcopy(self.azure.manifest()["attempts"])
        result = b.repair_trace_routing(self.path, approval, run=self.azure)
        self.assertEqual(result["status"], "TRACE_ROUTING_REPAIR_READY")
        self.assertEqual(self.azure.mutations, [])
        archive = Path(result["archive_path"]) / "original"
        for name, content in original.items():
            self.assertEqual((archive / name).read_bytes(), content)
        self.assertEqual((archive / "approval.original.json").read_bytes(), approval_bytes)
        self.assertEqual(approval.read_bytes(), approval_bytes)
        self.assertTrue((archive / "live-operations.snapshot.json").is_file())
        _, repaired, manifest = b._load(self.path)
        self.assertEqual(repaired["instance_id"], self.config["instance_id"])
        self.assertEqual(b._resources(repaired), b._resources(self.config))
        self.assertEqual(manifest["attempts"], attempts)
        self.assertEqual(manifest["phase"], "trace_routing_repair_ready")
        record = manifest["trace_routing_repairs"][-1]
        self.assertFalse(record["dependsOn_only"])
        self.assertEqual(record["repair_kind"], "trace-routing")
        bound = b._read(Path(result["approval_path"]))
        self.assertEqual(bound["max_provisioning_retries"], 2)
        self.assertEqual(b.repair_trace_routing(self.path, approval, run=self.azure)["status"], "TRACE_ROUTING_REPAIR_ALREADY_APPLIED")
        with self.assertRaises(b.ProvisioningRetryError):
            b.apply(self.path, result["approval_path"], run=self.azure)
        self.assertEqual(b.apply(self.path, result["approval_path"], run=self.azure, retry=True)["status"], "APPLIED")
        self.assertEqual(len(self.azure.mutations), 1)
        self.assertEqual(len([a for a in self.azure.manifest()["attempts"] if a["phase"] == "deploying"]), 3)

    def test_trace_routing_repair_rejects_literal_foreign_auth_and_unrelated_changes(self):
        approval = self.trace_routing_repair_fixture()
        original = json.loads(b.TEMPLATE.read_text())
        for change in ("literal", "foreign", "auth", "local-auth", "roles", "dependency"):
            with self.subTest(change=change):
                template = deepcopy(original)
                trace = next(r for r in template["resources"] if r.get("properties", {}).get("category") == "AppInsights")
                if change == "literal":
                    trace["properties"]["metadata"][b.TRACE_ROUTING_KEY] = "InstrumentationKey=literal"
                elif change == "foreign":
                    trace["properties"]["metadata"][b.TRACE_ROUTING_KEY] = "[reference('/unowned/resource', '2020-02-02').ConnectionString]"
                elif change == "auth":
                    trace["properties"]["authType"] = "ApiKey"
                    trace["properties"]["credentials"] = {"key": "literal"}
                elif change == "local-auth":
                    next(r for r in template["resources"] if r["type"] == "Microsoft.Insights/components")["properties"]["DisableLocalAuth"] = False
                elif change == "roles":
                    next(r for r in template["resources"] if r["type"] == "Microsoft.Authorization/roleAssignments")["properties"]["principalType"] = "User"
                else:
                    trace["dependsOn"] = []
                candidate = self.root / f"routing-{change}.json"
                candidate.write_text(json.dumps(template))
                with patch.object(b, "TEMPLATE", candidate):
                    with self.assertRaises(b.BootstrapError):
                        b.repair_trace_routing(self.path, approval, run=self.azure)
        self.assertEqual(self.azure.calls, [])
        self.assertEqual(self.azure.mutations, [])

    def test_trace_routing_repair_requires_live_exact_operation_proof(self):
        approval = self.trace_routing_repair_fixture()
        self.azure.operations[0]["properties"]["targetResource"]["id"] = b._ids(self.config)["project"]
        with self.assertRaises(b.BootstrapError):
            b.repair_trace_routing(self.path, approval, run=self.azure)
        self.assertEqual(self.azure.mutations, [])

    def test_trace_routing_repair_cannot_grant_or_replenish_retries(self):
        approval = self.trace_routing_repair_fixture()
        reduced = b._read(approval)
        reduced["max_provisioning_retries"] = 1
        approval.write_text(json.dumps(reduced))
        with self.assertRaises(b.ApprovalError):
            b.repair_trace_routing(self.path, approval, run=self.azure)
        self.assertEqual(self.azure.calls, [])
        reduced["max_provisioning_retries"] = 2
        approval.write_text(json.dumps(reduced))
        manifest = self.azure.manifest()
        manifest["attempts"].append(deepcopy(next(a for a in manifest["attempts"] if a["phase"] == "deploying")))
        (self.path.parent / "manifest.json").write_text(json.dumps(manifest))
        with self.assertRaises(b.ApprovalError):
            b.repair_trace_routing(self.path, approval, run=self.azure)
        self.assertEqual(self.azure.mutations, [])

    def test_success_cannot_hide_missing_trace_routing_and_foreign_route_is_blocked(self):
        self.apply()
        spec = b._resources(self.config)["insights_connection"]
        connection = self.azure.remote[spec["id"].lower()]
        connection["properties"]["metadata"][b.TRACE_ROUTING_KEY] = "InstrumentationKey=foreign"
        self.azure.mutations.clear()
        with self.assertRaises(b.BootstrapError):
            self.apply()
        del connection["properties"]["metadata"][b.TRACE_ROUTING_KEY]
        with self.assertRaises(b.BootstrapError):
            self.apply()
        self.assertEqual(self.azure.mutations, [])

    def test_trace_connection_is_owned_but_not_claimed_as_observed_ingestion(self):
        result = self.apply()
        self.assertEqual(result["server_side_trace_connection"], "CONFIGURED_PROJECT_MANAGED_IDENTITY")
        self.assertFalse(result["trace_ingestion_verified"])
        self.assertEqual(self.azure.manifest()["resources"]["insights_connection"]["status"], "succeeded")
        spec = self.azure.manifest()["resources"]["insights_connection"]
        self.azure.remote[spec["id"].lower()]["properties"]["authType"] = "ApiKey"
        self.azure.mutations.clear()
        with self.assertRaises(b.BootstrapError):
            self.apply()
        self.assertEqual(self.azure.mutations, [])

    def test_trace_connection_target_or_marker_drift_blocks_before_arm_mutation(self):
        self.apply()
        spec = self.azure.manifest()["resources"]["insights_connection"]
        original = deepcopy(self.azure.remote[spec["id"].lower()])
        self.azure.mutations.clear()
        for field, value in (("target", "/unowned/insights"), ("category", "CognitiveSearch")):
            with self.subTest(field=field):
                self.azure.remote[spec["id"].lower()] = deepcopy(original)
                self.azure.remote[spec["id"].lower()]["properties"][field] = value
                with self.assertRaises(b.BootstrapError):
                    self.apply()
        self.azure.remote[spec["id"].lower()] = deepcopy(original)
        self.azure.remote[spec["id"].lower()]["properties"]["metadata"]["lab_instance"] = "foreign"
        with self.assertRaises(b.BootstrapError):
            self.apply()
        self.assertEqual(self.azure.mutations, [])

    def test_cli_errors_do_not_echo_credentials_or_private_azure_output(self):
        fake = subprocess.CompletedProcess([], 1, "", f"ERROR: (AuthorizationFailed) {USER} {SUB} sensitive")
        with patch.object(b.subprocess, "run", return_value=fake):
            with self.assertRaises(b.AzureCommandError) as caught:
                b.az_json(["account", "show"])
        self.assertNotIn(USER, str(caught.exception))
        self.assertNotIn(SUB, str(caught.exception))
        self.assertIn("AuthorizationFailed", str(caught.exception))

    def test_rest_json_not_found_is_parsed_without_hiding_permission_failures(self):
        for code in ("ResourceGroupNotFound", "ParentResourceNotFound", "DeploymentNotFound", "AuthorizationFailed"):
            with self.subTest(code=code):
                stderr = "ERROR: Not Found(" + json.dumps({"error": {"code": code, "message": f"{USER} {SUB}"}}) + ")"
                fake = subprocess.CompletedProcess([], 1, "", stderr)
                with patch.object(b.subprocess, "run", return_value=fake):
                    with self.assertRaises(b.AzureCommandError) as caught:
                        b.az_json(["rest", "--method", "GET"])
                self.assertEqual(caught.exception.code, code)
                self.assertNotIn(USER, str(caught.exception))
                self.assertEqual(caught.exception.stderr, stderr)

    def test_nested_provider_deprecation_overrides_wrapper_and_scrubs_public_message(self):
        bodies = (
            DEPRECATED_ERROR,
            {"error": DEPRECATED_ERROR},
            {"error": {"code": "DeploymentFailed", "message": json.dumps(DEPRECATED_ERROR)}},
            json.dumps({"error": DEPRECATED_ERROR}),
        )
        for body in bodies:
            for output in ("stderr", "stdout"):
                with self.subTest(body=body.get("code", "wrapped") if isinstance(body, dict) else "encoded", output=output):
                    text = "ERROR: " + json.dumps(body)
                    fake = subprocess.CompletedProcess(
                        [], 1, text if output == "stdout" else "", text if output == "stderr" else "",
                    )
                    with patch.object(b.subprocess, "run", return_value=fake):
                        with self.assertRaises(b.AzureCommandError) as caught:
                            b.az_json(["deployment", "group", "validate"])
                    exc = caught.exception
                    self.assertEqual(exc.code, "ServiceModelDeprecated")
                    self.assertIn("gpt-4o-mini", str(exc))
                    self.assertIn("03/31/2026", str(exc))
                    for private in (SUB, USER, "private-group", "secret-token", "private-key"):
                        self.assertNotIn(private, str(exc))
                    self.assertIn(USER, exc.raw_message)
                    self.assertEqual(getattr(exc, output), text)

    def test_real_validation_failure_shape_blocks_preflight_and_preserves_original_locally(self):
        intent, created, _ = self.coordinator_receipts()
        b.bind_created_group(self.path, intent, created, run=self.azure)
        self.azure.validation_error = deepcopy(DEPRECATED_ERROR)
        report = b.preflight(self.path, run=self.azure, approval_path=self.approve())
        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual(report["error_code"], "ServiceModelDeprecated")
        self.assertEqual(report["arm_validation_status"], "FAILED")
        self.assertEqual(report["live_status"], "BLOCKED_PROVIDER_VALIDATION")
        self.assertEqual(report["approval_status"], "APPROVED")
        self.assertNotIn(USER, json.dumps(report))
        records = list((self.path.parent / "evidence").glob("validation-*.local.json"))
        failures = [json.loads(path.read_text()) for path in records if not path.name.startswith("validation-parameters")]
        self.assertEqual(failures[-1]["status"], "FAILED")
        self.assertIn(USER, failures[-1]["failure"]["stderr"])
        self.assertEqual(self.azure.mutations, [])

    def test_provider_validation_must_pass_before_any_child_creation(self):
        intent, created, _ = self.coordinator_receipts()
        b.bind_created_group(self.path, intent, created, run=self.azure)
        self.azure.validation_error = deepcopy(DEPRECATED_ERROR)
        with self.assertRaises(b.AzureCommandError) as caught:
            self.apply()
        self.assertEqual(caught.exception.code, "ServiceModelDeprecated")
        self.assertEqual(self.azure.mutations, [])
        manifest = self.azure.manifest()
        self.assertFalse(any(item["phase"] == "deploying" for item in manifest["attempts"]))
        self.assertTrue(all(r["status"] == "planned" for k, r in manifest["resources"].items() if k != "resource_group"))
        self.assertEqual(manifest["last_validation"]["status"], "FAILED")
        failure = self.path.parent / "evidence" / manifest["last_error_evidence_file"]
        self.assertEqual(failure.stat().st_mode & 0o777, 0o600)
        self.assertIn(USER, json.loads(failure.read_text())["stderr"])
        self.assertNotIn(USER, manifest["last_error"])

    def test_empty_or_failed_validation_response_is_not_success(self):
        intent, created, _ = self.coordinator_receipts()
        b.bind_created_group(self.path, intent, created, run=self.azure)
        for response in (
            None, {}, {"properties": None}, {"error": DEPRECATED_ERROR},
            DEPRECATED_ERROR, {"properties": {"provisioningState": "Failed"}},
        ):
            with self.subTest(response=response):
                self.azure.validation_result = response
                with self.assertRaises(b.BootstrapError):
                    self.apply()
        self.assertEqual(self.azure.mutations, [])

    def test_create_uses_the_exact_provider_validated_parameters(self):
        self.apply()
        validation = next(args for args in self.azure.calls if args[:3] == ["deployment", "group", "validate"])
        create = next(args for args in self.azure.calls if args[:3] == ["deployment", "group", "create"])
        self.assertLess(self.azure.calls.index(validation), self.azure.calls.index(create))
        self.assertEqual(validation[validation.index("--parameters") + 1], create[create.index("--parameters") + 1])
        self.assertEqual(validation[validation.index("--template-file") + 1], create[create.index("--template-file") + 1])

    def test_verified_failed_deployment_requires_explicit_flag_and_retry_allowance(self):
        self.azure.fail_terminal = True
        with self.assertRaises(b.AzureCommandError):
            self.apply()
        self.azure.mutations.clear()
        for retry, budget, code in (
            (False, 1, "RETRY_REQUIRED"), (True, 0, "RETRY_BUDGET_EXHAUSTED"),
        ):
            with self.subTest(retry=retry, budget=budget):
                with self.assertRaises(b.ProvisioningRetryError) as caught:
                    b.apply(self.path, self.approve(max_provisioning_retries=budget), run=self.azure, retry=retry)
                self.assertEqual(caught.exception.code, code)
        self.assertEqual(self.azure.mutations, [])
        result = b.apply(self.path, self.approve(max_provisioning_retries=1), run=self.azure, retry=True)
        self.assertEqual(result["status"], "APPLIED")
        self.assertEqual(len(self.azure.mutations), 1)
        self.assertEqual(self.azure.mutations[0][:3], ["deployment", "group", "create"])

    def test_retry_allowance_is_consumed_by_recorded_arm_create_attempts(self):
        approval = self.approve(max_provisioning_retries=1)
        for retry in (False, True):
            self.azure.fail_terminal = True
            with self.assertRaises(b.AzureCommandError):
                b.apply(self.path, approval, run=self.azure, retry=retry)
        self.azure.mutations.clear()
        with self.assertRaises(b.ProvisioningRetryError) as caught:
            b.apply(self.path, approval, run=self.azure, retry=True)
        self.assertEqual(caught.exception.code, "RETRY_BUDGET_EXHAUSTED")
        self.assertEqual(self.azure.mutations, [])
        self.assertEqual(len([item for item in self.azure.manifest()["attempts"] if item["phase"] == "deploying"]), 2)
        self.assertEqual(len(self.azure.manifest()["failures"]), 3)
        self.assertTrue(all(
            (self.path.parent / "evidence" / failure["evidence_file"]).is_file()
            for failure in self.azure.manifest()["failures"]
        ))

    def test_arm_terminal_failure_payload_is_preserved_not_just_summary(self):
        self.azure.fail_terminal = True
        with self.assertRaises(b.AzureCommandError):
            self.apply()
        manifest = self.azure.manifest()
        record = json.loads((self.path.parent / "evidence" / manifest["last_error_evidence_file"]).read_text())
        payload = json.loads(record["stdout"])
        self.assertEqual(payload["properties"]["provisioningState"], "Failed")
        self.assertEqual(payload["properties"]["error"]["code"], "DeploymentFailed")
        self.assertIn(SUB, payload["id"])
        self.assertNotIn(SUB, record["error"])

    def test_cli_timeout_keeps_original_output_without_assuming_submission_failed(self):
        timeout = subprocess.TimeoutExpired(["az"], 1, output=f"scope {SUB}".encode(), stderr=b"still waiting")
        with patch.object(b.subprocess, "run", side_effect=timeout):
            with self.assertRaises(b.AzureCommandError) as caught:
                b.az_json(["deployment", "group", "create"], timeout=1)
        self.assertEqual(caught.exception.code, "CliTimeout")
        self.assertIn(SUB, caught.exception.stdout)
        self.assertNotIn(SUB, str(caught.exception))

    def test_auth_failure_is_never_reclassified_as_nested_not_found(self):
        payload = {
            "code": "AuthorizationFailed", "message": "Access denied.",
            "details": [{"code": "ResourceNotFound", "message": "Hidden resource."}],
        }
        error = b._azure_error(json.dumps(payload), "", ["rest", "--method", "GET"])
        self.assertEqual(error.code, "AuthorizationFailed")

    def test_unknown_group_submission_is_not_retried_even_with_retry_allowance(self):
        self.azure.fail_group = True
        with self.assertRaises(b.AzureCommandError):
            self.apply()
        self.assertEqual(self.azure.manifest()["resources"]["resource_group"]["status"], "pending")
        self.azure.mutations.clear()
        with self.assertRaises(b.ProvisioningRetryError) as caught:
            b.apply(self.path, self.approve(max_provisioning_retries=1), run=self.azure, retry=True)
        self.assertEqual(caught.exception.code, "UNKNOWN_GROUP_SUBMISSION")
        self.assertEqual(self.azure.mutations, [])

    def test_changed_pinned_template_blocks_before_azure_calls(self):
        (self.path.parent / "template.json").write_text("{}")
        with self.assertRaises(b.BootstrapError):
            b.preflight(self.path, run=self.azure)
        self.assertEqual(self.azure.calls, [])

    def test_no_symlinked_artifacts_or_foreign_lock_is_overwritten(self):
        artifact_dir = self.path.parent / "artifacts"
        artifact_dir.rmdir()
        artifact_dir.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(b.BootstrapError):
            self.apply()
        self.assertEqual(self.azure.calls, [])
        artifact_dir.unlink()
        artifact_dir.mkdir()
        lock = self.path.parent / ".bootstrap.lock"
        lock.write_text("another operator is running")
        with self.assertRaises(b.BootstrapError):
            self.apply()
        self.assertEqual(lock.read_text(), "another operator is running")

    def test_creation_state_without_pending_receipt_cannot_adopt_existing_resources(self):
        manifest = self.azure.manifest()
        manifest["resources"]["resource_group"]["status"] = "present"
        (self.path.parent / "manifest.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(b.BootstrapError, "creation attempt"):
            b.preflight(self.path, run=self.azure)
        self.assertEqual(self.azure.calls, [])

    def test_malformed_models_fail_before_creating_local_or_remote_state(self):
        for models in ([None], [{"roles": []}], [{"roles": None}]):
            with self.subTest(models=models):
                with self.assertRaises(b.BootstrapError):
                    b.plan(
                        subscription_id=SUB, tenant_id=TENANT, expected_user=USER,
                        environment="lab-invalid", root=self.root, models=models,
                    )
        self.assertFalse((self.root / "lab-invalid").exists())

    def test_readonly_readiness_with_valid_approval_is_not_live_success(self):
        report = b.preflight(self.path, run=self.azure, approval_path=self.approve())
        self.assertEqual(report["status"], "READY_FOR_APPROVED_APPLY")
        self.assertEqual(report["readiness_status"], "READY")
        self.assertEqual(report["live_status"], "PENDING_EXECUTION")
        self.assertEqual(self.azure.mutations, [])
        status = b.status(self.path, run=self.azure, approval_path=self.approve())
        self.assertEqual(status["status"], "OBSERVED_APPROVAL_VALID")
        self.assertEqual(status["readiness_status"], "NOT_CHECKED_BY_STATUS")
        self.assertTrue(all(not r["present"] for r in status["resources"].values()))

    def test_unapproved_and_expired_records_do_not_turn_ready_readiness_into_authorization(self):
        for changes in ({"approved": False}, {"expires_at": "2020-01-01T00:00:00+00:00"}):
            with self.subTest(changes=changes):
                report = b.preflight(self.path, run=self.azure, approval_path=self.approve(**changes))
                self.assertEqual(report["status"], "BLOCKED_AWAITING_APPROVAL")
                self.assertEqual(report["readiness_status"], "READY")
                self.assertEqual(report["approval_status"], "INVALID")
        self.assertEqual(self.azure.mutations, [])

    def test_no_approval_cli_returns_machine_readable_blocked_status_without_azure(self):
        result = subprocess.run(
            [sys.executable, "-S", "-m", "lab.bootstrap", "apply", "--config", str(self.path)],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "BLOCKED_AWAITING_APPROVAL")
        self.assertFalse(report["mutations_performed"])
        self.assertEqual(report["live_status"], "NOT_VERIFIED")
        self.assertEqual(self.azure.manifest()["phase"], "planned")

    def authorize_group(self, **changes):
        authorization = b.group_authorization_template(self.config)
        authorization.update(
            authorized=True, authorized_by=USER, authorized_at=b._stamp(),
            request_evidence="Explicit user request to create only the new resource group.",
        )
        authorization.update(changes)
        path = self.path.parent / f"group-authorization-{uuid4().hex}.json"
        path.write_text(json.dumps(authorization))
        return path

    def simulate_group_creation(self, contract):
        self.azure.remote[contract["resource_group_id"].lower()] = {
            "id": contract["resource_group_id"], "type": "Microsoft.Resources/resourceGroups",
            **deepcopy(contract["body"]), "properties": {"provisioningState": "Succeeded"},
        }

    def test_explicit_six_character_group_suffix_is_planned_without_adopting(self):
        planned = b.plan(
            subscription_id=SUB, tenant_id=TENANT, expected_user=USER, root=self.root,
            environment="lab-explicit", resource_group="rg-foundry-eval-v11-20260930-abc123",
        )
        config = json.loads(Path(planned["config_path"]).read_text())
        self.assertEqual(config["names"]["resource_group"], "rg-foundry-eval-v11-20260930-abc123")
        self.assertEqual(planned["status"], "BLOCKED_AWAITING_APPROVAL")

    def test_group_only_preparation_is_readonly_and_records_only_group_intent(self):
        authorization = self.authorize_group()
        contract = b.prepare_group_creation(self.path, authorization, run=self.azure)
        self.assertEqual(self.azure.mutations, [])
        self.assertEqual(contract["group_creation_status"], "AUTHORIZED_EXTERNAL_CREATE_PENDING")
        self.assertEqual(contract["status"], "BLOCKED_AWAITING_APPROVAL")
        self.assertEqual(contract["headers"], {"If-None-Match": "*"})
        self.assertEqual(contract["body"]["tags"], b._tags(self.config))
        manifest = self.azure.manifest()
        self.assertEqual(manifest["resources"]["resource_group"]["status"], "pending")
        self.assertTrue(all(r["status"] == "planned" for k, r in manifest["resources"].items() if k != "resource_group"))
        self.assertEqual(manifest["attempts"][0]["pending_ids"], [contract["resource_group_id"]])
        self.assertEqual(manifest["attempts"][0]["authorization_kind"], "resource_group_only")
        self.assertEqual(b.prepare_group_creation(self.path, authorization, run=self.azure), contract)
        with self.assertRaises(b.ApprovalError):
            b.apply(self.path, authorization, run=self.azure)
        self.assertEqual(self.azure.mutations, [])

    def test_group_confirmation_is_readonly_keeps_paid_apply_blocked_and_can_resume_later(self):
        contract = b.prepare_group_creation(self.path, self.authorize_group(), run=self.azure)
        self.simulate_group_creation(contract)
        report = b.confirm_group_creation(self.path, run=self.azure)
        self.assertEqual(report["status"], "BLOCKED_AWAITING_APPROVAL")
        self.assertEqual(report["group_creation_status"], "CONFIRMED_CREATED")
        self.assertTrue(report["preserve_group"])
        self.assertEqual(self.azure.manifest()["phase"], "group_created_awaiting_approval")
        self.assertEqual(self.azure.mutations, [])
        with self.assertRaises(b.ApprovalError):
            b.apply(self.path, run=self.azure)
        self.assertEqual(b.preflight(self.path, run=self.azure)["owned_resource_count"], 1)
        self.assertEqual(self.apply()["status"], "APPLIED")
        self.assertTrue(all(a[0] != "rest" for a in self.azure.mutations))

    def test_group_preparation_never_adopts_an_existing_group(self):
        group_id = b._ids(self.config)["resource_group"]
        self.azure.remote[group_id.lower()] = {"id": group_id, "tags": b._tags(self.config), "location": b.REGION}
        with self.assertRaises(b.BootstrapError):
            b.prepare_group_creation(self.path, self.authorize_group(), run=self.azure)
        self.assertEqual(self.azure.manifest()["resources"]["resource_group"]["status"], "planned")
        self.assertEqual(self.azure.mutations, [])

    def test_group_only_authorization_rejects_broad_or_missing_consent_before_azure(self):
        for changes in (
            {"authorized": False}, {"paid_resources_approved": True}, {"rbac_approved": True},
            {"deletion_approved": True}, {"preserve_group": False}, {"request_evidence": ""},
            {"resource_group_id": "/wrong"}, {"allowed_operations": ["*"]},
            {"authorized_at": None},
        ):
            with self.subTest(changes=changes):
                with self.assertRaises(b.ApprovalError):
                    b.prepare_group_creation(self.path, self.authorize_group(**changes), run=self.azure)
        self.assertEqual(self.azure.calls, [])

    def test_group_confirmation_refuses_foreign_tags_or_any_child_resource(self):
        contract = b.prepare_group_creation(self.path, self.authorize_group(), run=self.azure)
        self.simulate_group_creation(contract)
        group = self.azure.remote[contract["resource_group_id"].lower()]
        group["tags"]["lab_instance"] = "foreign"
        with self.assertRaises(b.BootstrapError):
            b.confirm_group_creation(self.path, run=self.azure)
        group["tags"] = b._tags(self.config)
        self.azure.remote["/unknown"] = {"id": "/unknown"}
        with self.assertRaises(b.BootstrapError):
            b.confirm_group_creation(self.path, run=self.azure)
        self.assertEqual(self.azure.mutations, [])

    def test_published_schemas_match_generated_plan_and_approval_fields(self):
        schema = json.loads((ROOT / "infra" / "plan.schema.json").read_text())
        approval_schema = json.loads((ROOT / "infra" / "approval.schema.json").read_text())
        self.assertEqual(set(schema["required"]), set(self.config))
        self.assertEqual(set(approval_schema["required"]), set(b.approval_template(self.config)))
        self.assertEqual(schema["properties"]["location"]["const"], b.REGION)
        self.assertEqual(approval_schema["properties"]["allow_rbac_assignments"]["const"], True)
        for file in (ROOT / "infra").glob("*.schema.json"):
            text = file.read_text()
            for identity in (SUB, TENANT, OPERATOR, USER):
                self.assertNotIn(identity, text)

    def test_private_runtime_bounds_are_preserved_and_never_create_execution_evidence(self):
        bounds = {
            "prompt_optimizer_jobs": 1, "agent_optimizer_jobs": 1, "candidates_per_optimizer_job": 2,
            "training_rows": 56, "validation_rows": 12, "fresh_holdout_rows": 12,
            "max_wait_seconds_per_job": 60, "synthetic_data_only": True,
            "allow_global_or_developer_training": True, "preserve_resource_group": True,
            "allow_deletion": False,
        }
        report = b.preflight(self.path, run=self.azure, approval_path=self.approve(
            budget_amount=50, max_calls=300, allow_training=True, allow_global_training=True,
            max_training_jobs=1, max_epochs=1, runtime_bounds=bounds,
        ))
        self.assertEqual(report["approval_status"], "APPROVED")
        self.assertEqual(report["live_status"], "PENDING_EXECUTION")
        self.assertEqual(self.azure.mutations, [])
        for changes in (
            {"allow_deletion": True}, {"preserve_resource_group": False},
            {"agent_optimizer_jobs": -1}, {"candidates_per_optimizer_job": 3},
            {"synthetic_data_only": False}, {"max_wait_seconds_per_job": 61},
        ):
            with self.subTest(changes=changes):
                with self.assertRaises(b.ApprovalError):
                    b.apply(self.path, self.approve(runtime_bounds={**bounds, **changes}), run=self.azure)
        self.assertEqual(self.azure.mutations, [])

    def coordinator_receipts(self):
        group = self.config["names"]["resource_group"]
        intent = {
            "kind": "explicitly-authorized-resource-group-creation", "status": "INTENT_RECORDED_BEFORE_CREATE",
            "resource_group": group, "location": b.REGION, "subscription_id": SUB, "tenant_id": TENANT,
            "ownership_id": str(uuid4()), "source_commit": "a" * 40,
            "user_authorization": "Create the new isolated resource group and preserve it.",
        }
        created = {
            "id": b._ids(self.config)["resource_group"], "type": "Microsoft.Resources/resourceGroups",
            "name": group, "location": b.REGION, "properties": {"provisioningState": "Succeeded"},
            "tags": {
                "lab": "foundry-learning-loop-v1.1", "lab-environment": group.removeprefix("rg-foundry-eval-v11-"),
                "lab-ownership": intent["ownership_id"], "managed-by": "foundry-evaluation-labs-v1.1",
                "source-commit": "a" * 7, "retention": "review-no-auto-delete",
            },
        }
        intent_path, created_path = self.root / "parent-intent.json", self.root / "parent-created.json"
        intent_path.write_text(json.dumps(intent))
        created_path.write_text(json.dumps(created))
        self.azure.remote[created["id"].lower()] = deepcopy(created)
        return intent_path, created_path, created

    def test_coordinator_receipt_binding_preserves_tags_scope_and_later_apply_skips_rg_create(self):
        intent, created, original = self.coordinator_receipts()
        before_hash = self.config["scope_sha256"]
        report = b.bind_created_group(self.path, intent, created, run=self.azure)
        self.assertEqual(report["status"], "GROUP_OWNERSHIP_BOUND")
        self.assertEqual(report["scope_sha256"], before_hash)
        self.assertFalse(report["mutations_performed"])
        self.assertEqual(self.azure.mutations, [])
        self.assertEqual(self.azure.manifest()["resources"]["resource_group"]["status"], "present")
        self.assertTrue(all(r["status"] == "planned" for k, r in self.azure.manifest()["resources"].items() if k != "resource_group"))
        self.assertEqual(b.bind_created_group(self.path, intent, created, run=self.azure)["status"], "GROUP_OWNERSHIP_BOUND")
        self.assertEqual(len(self.azure.manifest()["attempts"]), 1)
        self.assertEqual(b.preflight(self.path, run=self.azure)["owned_resource_count"], 1)
        self.assertEqual(self.apply()["status"], "APPLIED")
        self.assertEqual(self.azure.remote[original["id"].lower()]["tags"], original["tags"])
        self.assertTrue(all(args[0] != "rest" for args in self.azure.mutations))

    def test_coordinator_binding_rejects_wrong_intent_scope_before_azure(self):
        intent_path, created, _ = self.coordinator_receipts()
        intent = json.loads(intent_path.read_text())
        intent["tenant_id"] = str(uuid4())
        intent_path.write_text(json.dumps(intent))
        with self.assertRaises(b.BootstrapError):
            b.bind_created_group(self.path, intent_path, created, run=self.azure)
        self.assertEqual(self.azure.calls, [])

    def test_coordinator_binding_refuses_nonempty_or_changed_live_group(self):
        intent, created, original = self.coordinator_receipts()
        live = self.azure.remote[original["id"].lower()]
        live["tags"]["lab-ownership"] = str(uuid4())
        with self.assertRaises(b.BootstrapError):
            b.bind_created_group(self.path, intent, created, run=self.azure)
        live["tags"] = deepcopy(original["tags"])
        self.azure.remote["/unknown"] = {"id": "/unknown"}
        with self.assertRaises(b.BootstrapError):
            b.bind_created_group(self.path, intent, created, run=self.azure)
        self.assertEqual(self.azure.manifest()["resources"]["resource_group"]["status"], "planned")
        self.assertEqual(self.azure.mutations, [])

    def test_coordinator_binding_receipts_cannot_be_changed_after_verification(self):
        intent, created, _ = self.coordinator_receipts()
        b.bind_created_group(self.path, intent, created, run=self.azure)
        binding = self.azure.manifest()["external_group_binding"]
        receipt = self.path.parent / "evidence" / binding["created_file"]
        content = json.loads(receipt.read_text())
        content["properties"]["provisioningState"] = "Failed"
        receipt.write_text(json.dumps(content))
        self.azure.calls.clear()
        with self.assertRaises(b.BootstrapError):
            b.status(self.path, run=self.azure)
        self.assertEqual(self.azure.calls, [])
        self.assertEqual(self.azure.mutations, [])

    def test_public_ownership_guard_verifies_completed_plan_and_is_readonly(self):
        self.apply()
        self.azure.calls.clear()
        self.azure.mutations.clear()
        account = b._ids(self.config)["account"]
        # Later caller-owned deployments are not part of the original bootstrap inventory.
        extra = account + "/deployments/caller-owned-fine-tuned-model"
        self.azure.remote[extra.lower()] = {"id": extra}
        before = (self.path.parent / "manifest.json").read_bytes()
        report = b.require_owned_resources(self.path, account, run=self.azure)
        self.assertEqual(report["status"], "OWNED_BOOTSTRAP_SCOPE_VERIFIED")
        self.assertEqual(report["account_id"], account)
        self.assertFalse(report["authorization_verified"])
        self.assertEqual(self.azure.mutations, [])
        self.assertEqual((self.path.parent / "manifest.json").read_bytes(), before)
        self.assertFalse(any(args[:2] == ["resource", "list"] for args in self.azure.calls))
        self.assertEqual(len([args for args in self.azure.calls if args[0] == "rest"]), 4)

    def test_public_ownership_guard_rejects_unrelated_or_unfinished_scope_before_azure(self):
        account = b._ids(self.config)["account"]
        for requested in (account, account + "-foreign", account + "/deployments/not-an-account"):
            with self.subTest(requested=requested):
                with self.assertRaises(b.BootstrapError):
                    b.require_owned_resources(self.path, requested, run=self.azure)
        self.assertEqual(self.azure.calls, [])
        self.apply()
        self.azure.calls.clear()
        with self.assertRaises(b.BootstrapError):
            b.require_owned_resources(self.path, account + "-foreign", run=self.azure)
        self.assertEqual(self.azure.calls, [])

    def test_public_ownership_guard_refuses_remote_tag_identity_state_or_deployment_drift(self):
        self.apply()
        original = deepcopy(self.azure.remote)
        ids = b._ids(self.config)
        deployment = self.azure.manifest()["resources"]["arm_deployment"]["id"]
        corruptions = (
            (ids["resource_group"], lambda row: row["tags"].update(lab_instance="foreign")),
            (ids["account"], lambda row: row["tags"].update(lab_instance="foreign")),
            (ids["account"], lambda row: row.update(id=ids["account"] + "-foreign")),
            (ids["account"], lambda row: row["properties"].update(provisioningState="Updating")),
            (ids["account"], lambda row: row["properties"].update(disableLocalAuth=False)),
            (deployment, lambda row: row["properties"].update(mode="Complete")),
        )
        self.azure.mutations.clear()
        for resource_id, corrupt in corruptions:
            with self.subTest(resource_id=resource_id):
                self.azure.remote = deepcopy(original)
                corrupt(self.azure.remote[resource_id.lower()])
                with self.assertRaises(b.BootstrapError):
                    b.require_owned_resources(self.path, ids["account"], run=self.azure)
        self.azure.remote = deepcopy(original)
        del self.azure.remote[ids["account"].lower()]
        with self.assertRaises(b.BootstrapError):
            b.require_owned_resources(self.path, ids["account"], run=self.azure)
        self.assertEqual(self.azure.mutations, [])

    def test_public_ownership_guard_accepts_original_coordinator_tags_only_after_completed_apply(self):
        intent, created, _ = self.coordinator_receipts()
        b.bind_created_group(self.path, intent, created, run=self.azure)
        account = b._ids(self.config)["account"]
        with self.assertRaises(b.BootstrapError):
            b.require_owned_resources(self.path, account, run=self.azure)
        self.apply()
        self.azure.mutations.clear()
        self.assertEqual(
            b.require_owned_resources(self.path, account, run=self.azure)["status"],
            "OWNED_BOOTSTRAP_SCOPE_VERIFIED",
        )
        self.assertEqual(self.azure.mutations, [])

    def test_no_cap_requires_explicit_original_authorization_and_keeps_operational_bounds(self):
        valid = {
            "budget_policy": "NO_MONETARY_CAP_EXPLICITLY_APPROVED",
            "budget_amount": None, "acknowledge_no_monetary_cap": True,
            "request_evidence": "Private explicit user authorization waiving the monetary cap; call/job limits unchanged.",
        }
        report = b.preflight(self.path, run=self.azure, approval_path=self.approve(**valid))
        self.assertEqual(report["approval_status"], "APPROVED")
        self.assertEqual(report["live_status"], "PENDING_EXECUTION")
        for invalid in (
            {"acknowledge_no_monetary_cap": False}, {"request_evidence": ""},
            {"budget_amount": 50}, {"max_calls": None}, {"max_wait_seconds": None},
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaises(b.ApprovalError):
                    b.apply(self.path, self.approve(**{**valid, **invalid}), run=self.azure)
        self.assertEqual(self.azure.mutations, [])

    def test_permission_errors_are_not_treated_as_resource_absence(self):
        original = self.azure

        def denied(args):
            if args[0] == "rest" and any("/resourceGroups/" in value for value in args):
                raise b.AzureCommandError("AuthorizationFailed")
            return original(args)

        report = b.preflight(self.path, run=denied)
        self.assertEqual(report["status"], "BLOCKED")
        self.assertEqual(self.azure.mutations, [])


if __name__ == "__main__":
    unittest.main()
