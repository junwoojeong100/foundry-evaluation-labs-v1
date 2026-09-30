"""SDK-free, approval-bound bootstrap for a new, isolated Azure lab."""

from __future__ import annotations

import argparse
from collections import defaultdict
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from fnmatch import fnmatchcase
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any, Callable
from urllib.parse import urlencode
from uuid import UUID, uuid4, uuid5


REGION = "northcentralus"
TEMPLATE = Path(__file__).resolve().parents[1] / "infra" / "bootstrap.json"
ARM = "https://management.azure.com"
SCHEMA_VERSION = 1
TRACE_ROUTING_KEY = "ApplicationInsightsConnectionString"
TRACE_ROUTING_EXPRESSION = "[reference(resourceId('Microsoft.Insights/components', parameters('names').insights), '2020-02-02').ConnectionString]"
AWAITING_APPROVAL = "BLOCKED_AWAITING_APPROVAL"
SEARCH_BASIC_PRICE = {
    "currency": "USD", "amount": 0.101, "unit": "hour", "region": REGION,
    "as_of": "2026-09-30", "source": "https://azure.microsoft.com/pricing/details/search/",
    "evidence": "Coordinator-provided read-only Azure Retail Prices verification; not a spending approval.",
    "indicative_24_hours": 2.424, "indicative_730_hours": 73.73,
}
ROLE_IDS = {
    "ai_developer": "64702f94-c441-49e6-a78b-ef80e0188fee",
    "foundry_user": "53ca6127-db72-4b80-b1b0-d745d6d5456d",
    "openai_user": "5e0bd9bd-7b93-4f28-af87-19fc36ad61bd",
    "cognitive_user": "a97b65f3-24c7-4388-baec-2e87135dc908",
    "search_service": "7ca78c08-252a-4471-8644-bb5ff32d4ba0",
    "search_data": "8ebe5a00-799e-43f5-93ac-243d3dce84a7",
    "search_reader": "1407120a-92aa-4202-b7e9-c0e197c71c8f",
    "monitor_reader": "43d0d8ad-25c7-4714-9337-8ba259a9fe05",
    "monitor_publisher": "3913510d-42f4-4e42-8a64-420c390055eb",
}
RESOURCE_TYPES = {
    "account": ("Microsoft.CognitiveServices/accounts", "2025-06-01"),
    "project": ("Microsoft.CognitiveServices/accounts/projects", "2025-06-01"),
    "search": ("Microsoft.Search/searchServices", "2025-05-01"),
    "workspace": ("Microsoft.OperationalInsights/workspaces", "2023-09-01"),
    "insights": ("Microsoft.Insights/components", "2020-02-02"),
}
DEFAULT_MODELS = (
    {"roles": ["agent"], "name": "gpt-4.1-mini", "version": "2025-04-14", "sku": "Standard", "capacity": 20},
    {"roles": ["judge"], "name": "gpt-5.4-mini", "version": "2026-03-17", "capacity": 20},
    {"roles": ["planner", "optimizer"], "name": "gpt-5.5", "version": "2026-04-24", "capacity": 20},
    {"roles": ["embedding"], "name": "text-embedding-3-small", "version": "1", "capacity": 10},
)
Run = Callable[[list[str]], Any]


class BootstrapError(Exception):
    """A fail-closed error that does not expose local identities."""


class ApprovalError(BootstrapError):
    """A missing, invalid, expired, or incomplete authorization record."""

    def __init__(self, message: str):
        self.mutations_performed: bool | None = False
        super().__init__(message)


class AzureCommandError(BootstrapError):
    def __init__(
        self, code: str, *, stderr: str = "", stdout: str = "",
        command: list[str] | None = None, message: str = "", payload: Any = None,
    ):
        self.code = code
        self.stderr = stderr
        self.stdout = stdout
        self.command = command
        self.raw_message = message
        self.payload = payload
        self.safe_message = _scrub_azure_message(message)
        guidance = {
            "ServiceModelDeprecated": "Provider rejected the pinned model/version as deprecated. Select a supported replacement explicitly; catalog/quota do not override this error.",
            "AuthorizationFailed": "Verify existing resource-scoped permissions; do not escalate or change subscriptions automatically.",
            "CliTimeout": "Remote submission outcome is unknown. Inspect the recorded deployment before any retry.",
        }.get(code, "Inspect the private failure record; no automatic retry, model/region fallback, or cleanup.")
        detail = f" {self.safe_message}" if self.safe_message else ""
        super().__init__(f"Azure CLI failed ({code}).{detail} {guidance}")


class ProvisioningRetryError(BootstrapError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


def _scrub_azure_message(message: str) -> str:
    text = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", str(message))
    text = re.sub(r"(?i)\bBearer\s+\S+", "<redacted-token>", text)
    text = re.sub(
        r"""(?ix)\b(api[-_ ]?key|client[-_ ]?secret|access[-_ ]?token|connection[-_ ]?string|authorization)
        \s*[:=]\s*("[^"]*"|'[^']*'|[^,;\s]+)""",
        r"\1=<redacted>", text,
    )
    text = re.sub(r"https?://[^\s'\"<>]+", "<url>", text, flags=re.I)
    text = re.sub(r"/subscriptions/[^\s'\"<>]+", "<resource-scope>", text, flags=re.I)
    text = re.sub(r"(?i)\b[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b", "<uuid>", text)
    text = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+", "<identity>", text)
    text = re.sub(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b", "<redacted-token>", text)
    return " ".join(text.split())[:1000]


def _azure_error(stderr: str, stdout: str, args: list[str]) -> AzureCommandError:
    payloads, errors = [], []
    decoder = json.JSONDecoder()

    def collect(value: Any, depth: int = 0) -> None:
        if depth > 12:
            return
        if isinstance(value, dict):
            code = value.get("code")
            if isinstance(code, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9]{0,127}", code):
                errors.append((depth, code, str(value.get("message", ""))))
            for key in ("error", "details", "innererror", "innerError", "properties", "message"):
                if key in value:
                    collect(value[key], depth + 1)
        elif isinstance(value, list):
            for item in value:
                collect(item, depth + 1)
        elif isinstance(value, str):
            start = value.find("{")
            if start >= 0:
                try:
                    parsed, _ = decoder.raw_decode(value[start:])
                    collect(parsed, depth + 1)
                except (json.JSONDecodeError, RecursionError):
                    pass

    for text in (stderr, stdout):
        try:
            parsed = json.loads(text.removeprefix("ERROR:").strip())
            payloads.append(parsed)
            collect(parsed)
        except (json.JSONDecodeError, RecursionError):
            pass
        for match in list(re.finditer(r"\{", text))[:100]:
            try:
                parsed, _ = decoder.raw_decode(text[match.start():])
            except (json.JSONDecodeError, RecursionError):
                continue
            payloads.append(parsed)
            collect(parsed)
    wrappers = {"DeploymentFailed", "InvalidTemplateDeployment", "ResourceDeploymentFailure", "BadRequest"}
    authentication_errors = {
        "AuthorizationFailed", "AuthenticationFailed", "InvalidAuthenticationToken",
        "ExpiredAuthenticationToken", "Forbidden", "Unauthorized",
    }
    actionable = (
        [item for item in errors if item[1] in authentication_errors]
        or [item for item in errors if item[1] not in wrappers] or errors
    )
    if actionable:
        _, code, message = max(actionable, key=lambda item: item[0])
    else:
        match = re.search(r"\(([A-Za-z][A-Za-z0-9]+)\)", stderr)
        if match is None:
            match = re.search(r"""(?i)["']?code["']?\s*[:=]\s*["']?([A-Za-z][A-Za-z0-9]+)""", stderr)
        code, message = (match.group(1), "") if match else ("UnclassifiedError", "")
    return AzureCommandError(
        code, stderr=stderr, stdout=stdout, command=args, message=message, payload=payloads,
    )


def az_json(args: list[str], *, timeout: float = 120) -> Any:
    """Invoke Azure CLI without shell expansion, credential switching, or SDK imports."""
    try:
        result = subprocess.run(
            ["az", *args, "--only-show-errors", "--output", "json"],
            capture_output=True, text=True, check=False, timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise BootstrapError("Azure CLI is required; install it separately and sign in explicitly.") from exc
    except subprocess.TimeoutExpired as exc:
        def decoded(value: Any) -> str:
            return value.decode(errors="replace") if isinstance(value, bytes) else (value or "")
        raise AzureCommandError(
            "CliTimeout", command=args, stdout=decoded(exc.stdout), stderr=decoded(exc.stderr),
            message="Azure CLI timed out; remote submission may still be running.",
        ) from exc
    if result.returncode:
        raise _azure_error(result.stderr, result.stdout, args)
    try:
        return json.loads(result.stdout) if result.stdout.strip() else None
    except json.JSONDecodeError as exc:
        raise AzureCommandError(
            "InvalidCliResponse", command=args, stdout=result.stdout, stderr=result.stderr,
            message="Azure CLI returned invalid JSON; submission outcome cannot be inferred.",
        ) from exc


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _stamp(value: datetime | None = None) -> str:
    return (value or _now()).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"


def _digest(value: Any) -> str:
    return hashlib.sha256(_json(value).encode()).hexdigest()


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, value: Any, *, replace: bool = False, text: bool = False) -> None:
    """Write privately and durably, using a same-directory staging file for owned state."""
    content = value if text else _json(value)
    _write_bytes(path, content.encode("utf-8"), replace=replace)


def _write_bytes(path: Path, content: bytes, *, replace: bool = False) -> None:
    if path.is_symlink():
        raise BootstrapError("Refusing a symlink in bootstrap state.")
    target = path.with_name(f".{path.name}.{uuid4().hex}.pending") if replace else path
    try:
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if replace:
            os.replace(target, path)
        if hasattr(os, "O_DIRECTORY"):
            directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    except FileExistsError as exc:
        raise BootstrapError("Local output already exists; refusing to overwrite it.") from exc
    finally:
        if replace and target.exists():
            target.unlink()


def _read(path: Path) -> dict:
    if path.is_symlink():
        raise BootstrapError("Refusing a symlink in bootstrap state.")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise BootstrapError("Required local JSON is absent or invalid.") from exc
    if not isinstance(value, dict):
        raise BootstrapError("Expected a JSON object.")
    return value


def _integer(value: Any, minimum: int = 0) -> bool:
    return type(value) is int and value >= minimum


def _number(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def _uuid(value: Any) -> bool:
    try:
        return isinstance(value, str) and str(UUID(value)) == value.lower()
    except ValueError:
        return False


def _scope(config: dict) -> str:
    return _digest({key: value for key, value in config.items() if key != "scope_sha256"})


def _validate(config: dict, *, template_path: Path | None = None) -> None:
    if config.get("schema_version") != SCHEMA_VERSION or config.get("location") != REGION:
        raise BootstrapError("Only this schema and northcentralus are supported; no region fallback.")
    if not all(_uuid(config.get(k)) for k in ("subscription_id", "tenant_id", "instance_id")):
        raise BootstrapError("Subscription, tenant, and instance must be explicit UUIDs.")
    user = config.get("expected_user", "")
    if not re.fullmatch(r"[A-Za-z0-9._+-]+@[A-Za-z0-9.-]+", user):
        raise BootstrapError("An explicit expected Azure user principal name is required.")
    if not re.fullmatch(r"[a-z][a-z0-9-]{2,23}", config.get("environment", "")):
        raise BootstrapError("Environment must be a lowercase 3–24 character lab prefix.")
    names = config.get("names", {})
    if not re.fullmatch(r"rg-foundry-eval-v11-\d{8}-[a-f0-9]{6,12}", names.get("resource_group", "")):
        raise BootstrapError("The resource group must be a newly generated lab resource group.")
    for key in RESOURCE_TYPES:
        if not re.fullmatch(r"[a-z][a-z0-9-]{2,59}", names.get(key, "")):
            raise BootstrapError("Invalid generated resource name.")
    if not _integer(config.get("retention_days"), 30) or config["retention_days"] > 730:
        raise BootstrapError("Log Analytics retention must be 30–730 days.")
    models = config.get("models")
    if not isinstance(models, list) or not models:
        raise BootstrapError("Select and pin the four model deployments.")
    roles, deployments = [], []
    for model in models:
        if not isinstance(model, dict):
            raise BootstrapError("Each selected model must be a JSON object.")
        for key in ("name", "version", "deployment"):
            if not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", model.get(key, "")):
                raise BootstrapError("Model name, version, and deployment must be pinned explicitly.")
        if model["version"].lower() in {"latest", "default"}:
            raise BootstrapError("Floating model versions are not reproducible.")
        if model.get("sku") not in {"GlobalStandard", "Standard"} or not _integer(model.get("capacity"), 1):
            raise BootstrapError("This bootstrap supports explicit positive Standard/GlobalStandard capacity units only.")
        if "usage_name" in model and (
            not isinstance(model["usage_name"], str)
            or not re.fullmatch(r"OpenAI\.(Standard|GlobalStandard)\.[A-Za-z0-9_.-]+", model["usage_name"])
            or not model["usage_name"].startswith(f"OpenAI.{model['sku']}.")
            or model["usage_name"].endswith("-finetune")
        ):
            raise BootstrapError("An optional usage_name must pin the selected base-model SKU quota, not fine-tuning quota.")
        if not isinstance(model.get("roles"), list) or not all(isinstance(role, str) for role in model["roles"]):
            raise BootstrapError("Each deployment needs its explicit lab roles.")
        roles.extend(model["roles"])
        deployments.append(model["deployment"])
    if sorted(roles) != ["agent", "embedding", "judge", "optimizer", "planner"]:
        raise BootstrapError("Each agent/judge/planner/optimizer/embedding role must be selected exactly once.")
    if len(set(deployments)) != len(deployments):
        raise BootstrapError("Duplicate model deployment names.")
    if config.get("scope_sha256") != _scope(config):
        raise BootstrapError("Configuration changed; create a new plan and obtain new approval.")
    if config.get("template_sha256") != _file_digest(template_path or TEMPLATE):
        raise BootstrapError("Infrastructure template changed; re-plan and obtain new approval.")


def _ids(config: dict) -> dict[str, str]:
    group = f"/subscriptions/{config['subscription_id']}/resourceGroups/{config['names']['resource_group']}"
    result = {"resource_group": group}
    for key, (kind, _) in RESOURCE_TYPES.items():
        if key != "project":
            result[key] = f"{group}/providers/{kind}/{config['names'][key]}"
    result["project"] = f"{result['account']}/projects/{config['names']['project']}"
    return result


def _tags(config: dict) -> dict[str, str]:
    return {
        "lab": "foundry-eval-v11",
        "lab_environment": config["environment"],
        "lab_instance": config["instance_id"],
        "managed_by": "lab.bootstrap",
    }


def _roles(config: dict) -> list[dict]:
    ids = _ids(config)
    bindings = (
        ("operator-ai", "operator", "account", "ai_developer"),
        ("operator-openai", "operator", "account", "openai_user"),
        ("operator-project", "operator", "project", "foundry_user"),
        ("operator-search-schema", "operator", "search", "search_service"),
        ("operator-search-data", "operator", "search", "search_data"),
        ("project-search", "project", "search", "search_reader"),
        ("project-openai", "project", "account", "openai_user"),
        ("search-models", "search", "account", "cognitive_user"),
        ("operator-telemetry-read", "operator", "insights", "monitor_reader"),
        ("operator-telemetry-write", "operator", "insights", "monitor_publisher"),
        ("project-telemetry", "project", "insights", "monitor_publisher"),
        ("operator-workspace-read", "operator", "workspace", "monitor_reader"),
    )
    return [{
        "key": key, "principal": principal, "scope": ids[target], "role_id": ROLE_IDS[role],
        "arm_scope": ids[target].split("/providers/", 1)[1],
        "assignment_name": str(uuid5(UUID(config["instance_id"]), key)),
        "principal_resource_id": ids.get(principal, ids["project"]),
        "principal_api_version": RESOURCE_TYPES.get(principal, RESOURCE_TYPES["project"])[1],
        "description": f"foundry-eval-v11:{config['instance_id']}:{key}",
    } for key, principal, target, role in bindings]


def _resources(config: dict) -> dict[str, dict]:
    ids = _ids(config)
    skus = {
        "account": {"name": "S0"}, "project": None,
        "search": {"name": "basic", "replicas": 1, "partitions": 1},
        "workspace": {"name": "PerGB2018"}, "insights": {"name": "workspace-based"},
    }
    result = {
        "resource_group": {
            "id": ids["resource_group"], "type": "Microsoft.Resources/resourceGroups",
            "api_version": "2021-04-01", "taggable": True, "sku": None, "status": "planned",
        }
    }
    for key, (kind, version) in RESOURCE_TYPES.items():
        result[key] = {
            "id": ids[key], "type": kind, "api_version": version,
            "taggable": True, "sku": skus[key], "status": "planned",
        }
    for model in config["models"]:
        result[f"model:{model['deployment']}"] = {
            "id": f"{ids['account']}/deployments/{model['deployment']}",
            "type": "Microsoft.CognitiveServices/accounts/deployments",
            "api_version": "2025-06-01", "taggable": True, "status": "planned",
            "sku": {"name": model["sku"], "capacity": model["capacity"]}, "model": model,
        }
    result["search_connection"] = {
        "id": f"{ids['project']}/connections/lab-search",
        "type": "Microsoft.CognitiveServices/accounts/projects/connections",
        "api_version": "2025-06-01", "taggable": False, "sku": None, "status": "planned",
    }
    result["insights_connection"] = {
        "id": f"{ids['project']}/connections/lab-appinsights",
        "type": "Microsoft.CognitiveServices/accounts/projects/connections",
        "api_version": "2026-07-01", "taggable": False, "sku": None, "status": "planned",
    }
    for role in _roles(config):
        result[f"role:{role['key']}"] = {
            "id": f"{role['scope']}/providers/Microsoft.Authorization/roleAssignments/{role['assignment_name']}",
            "type": "Microsoft.Authorization/roleAssignments", "api_version": "2022-04-01",
            "taggable": False, "sku": None, "status": "planned", "role": role,
        }
    result["arm_deployment"] = {
        "id": f"{ids['resource_group']}/providers/Microsoft.Resources/deployments/{config['deployment_name']}",
        "type": "Microsoft.Resources/deployments", "api_version": "2022-09-01",
        "taggable": False, "sku": None, "status": "planned",
    }
    return result


def _load(path: Path | str, *, _pinned_template: bool = False) -> tuple[Path, dict, dict]:
    path = Path(path)
    if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
        raise BootstrapError("Bootstrap paths must not traverse symlinks.")
    path = path.resolve()
    if any((path.parent / name).exists() for name in (
        "dependency-repair.pending.json", "trace-routing-repair.pending.json",
    )):
        raise BootstrapError("A local template repair is incomplete; rerun its repair command before any Azure operation.")
    config = _read(path)
    _validate(config, template_path=path.parent / "template.json" if _pinned_template else None)
    if str(path.parent) != config.get("environment_dir"):
        raise BootstrapError("Environment path changed; do not reuse another environment's state.")
    template_path = path.parent / "template.json"
    if template_path.is_symlink() or _file_digest(template_path) != config["template_sha256"]:
        raise BootstrapError("The pinned local infrastructure template changed.")
    manifest = _read(path.parent / "manifest.json")
    if manifest.get("scope_sha256") != config["scope_sha256"]:
        raise BootstrapError("Manifest belongs to another plan.")
    expected = _resources(config)
    if set(manifest.get("resources", {})) != set(expected):
        raise BootstrapError("Manifest resource inventory changed.")
    for key, resource in expected.items():
        actual = manifest["resources"][key]
        if any(actual.get(field) != value for field, value in resource.items() if field != "status"):
            raise BootstrapError("Manifest contains an unexpected resource or scope.")
        if actual.get("status") not in {"planned", "pending", "present", "succeeded"}:
            raise BootstrapError("Manifest contains an invalid resource state.")
        if actual["status"] != "planned" and not any(
            actual["id"] in attempt.get("pending_ids", []) for attempt in manifest.get("attempts", [])
        ):
            raise BootstrapError("Ownership state has no recorded creation attempt.")
    binding = manifest.get("external_group_binding")
    if binding:
        if binding.get("kind") != "coordinator-created-empty-group":
            raise BootstrapError("Unrecognized external group ownership binding.")
        for field in ("intent_file", "created_file"):
            if not re.fullmatch(r"group-binding-[a-f0-9]{32}\.(intent|created)\.local\.json", binding.get(field, "")):
                raise BootstrapError("External group evidence must be a private local receipt.")
        intent = _read(path.parent / "evidence" / binding["intent_file"])
        created = _read(path.parent / "evidence" / binding["created_file"])
        tags = _coordinator_group_tags(config, intent, created)
        if (
            _digest(intent) != binding.get("intent_sha256")
            or _digest(created) != binding.get("created_sha256")
            or tags != binding.get("tags")
        ):
            raise BootstrapError("Coordinator group creation evidence changed.")
    return path.parent, config, manifest


def _save(directory: Path, manifest: dict) -> None:
    manifest["updated_at"] = _stamp()
    _write(directory / "manifest.json", manifest, replace=True)
    _write(directory / "cost-ledger.json", cost_ledger(manifest), replace=True)


def cost_ledger(manifest: dict) -> dict:
    entries = []
    for key, resource in manifest["resources"].items():
        billing = "control_plane_or_service_dependent"
        if key == "search":
            billing = "continuous_hosting_while_provisioned"
        elif key.startswith("model:"):
            billing = "metered_inference_not_a_token_spend_cap"
        elif key == "workspace":
            billing = "log_ingestion_and_retention"
        elif key == "insights":
            billing = "workspace_billing_do_not_double_count"
        entries.append({
            "key": key, "resource_id": resource["id"], "sku": resource["sku"],
            "state": resource["status"], "billing": billing, "estimated_cost": None,
            "cost_status": "UNKNOWN_NOT_ZERO",
        })
        if key == "search":
            entries[-1]["reference_unit_price"] = deepcopy(SEARCH_BASIC_PRICE)
    for key, billing in (
        ("fine_tuning_training", "separately_approved_training_tokens"),
        ("fine_tuned_model_hosting", "separate_continuous_hosting_even_when_idle"),
    ):
        entries.append({
            "key": key, "resource_id": None, "sku": None, "state": "not_created_by_bootstrap",
            "billing": billing, "estimated_cost": None, "cost_status": "UNKNOWN_NOT_ZERO",
        })
    return {
        "schema_version": SCHEMA_VERSION, "scope_sha256": manifest["scope_sha256"],
        "currency": manifest.get("approved_currency"), "budget_amount": manifest.get("approved_budget"),
        "budget_policy": manifest.get("approved_budget_policy"),
        "entries": entries,
        "spending_authorization": "REQUIRES_SEPARATE_CURRENT_APPROVAL",
        "warning": "Approval is not an Azure spending cap. Search continues billing after expiry; no auto-delete.",
    }


def approval_template(config: dict) -> dict:
    return {
        "schema_version": SCHEMA_VERSION, "approved": False,
        "scope_sha256": config["scope_sha256"], "approved_by": "",
        "approved_at": None, "expires_at": None, "currency": None, "budget_amount": None,
        "budget_policy": "BOUNDED", "acknowledge_no_monetary_cap": False,
        "retention_days": config["retention_days"], "max_hosting_hours": None,
        "allow_global_inference": False, "allow_training": False, "allow_global_training": False,
        "allow_resource_creation": False, "allow_rbac_assignments": False,
        "max_calls": 0, "max_candidates": 0, "max_epochs": 0, "max_training_jobs": 0,
        "max_wait_seconds": None, "accept_deprecated_models": False,
        "acknowledge_continuous_hosting": False, "acknowledge_unknown_cost": False,
        "models": deepcopy(config["models"]),
    }


def validate_approval(config: dict, approval: dict, *, now: datetime | None = None) -> None:
    """Validate authorization bounds, not an independent signature or Azure spend cap."""
    if approval.get("schema_version") != SCHEMA_VERSION or approval.get("approved") is not True:
        raise BootstrapError("An explicit bounded cost approval is required before apply.")
    if approval.get("scope_sha256") != config["scope_sha256"] or approval.get("models") != config["models"]:
        raise BootstrapError("Approval does not cover this exact scope, template, and model selection.")
    if str(approval.get("approved_by", "")).casefold() != config["expected_user"].casefold():
        raise BootstrapError("Approval must identify the expected operator.")
    if not re.fullmatch(r"[A-Z]{3}", str(approval.get("currency", ""))):
        raise BootstrapError("Approval requires a three-letter currency.")
    budget_policy = approval.get("budget_policy", "BOUNDED")
    if budget_policy == "BOUNDED":
        if not _number(approval.get("budget_amount")) or approval["budget_amount"] <= 0:
            raise BootstrapError("Bounded approval requires a finite, positive budget amount.")
        if approval.get("acknowledge_no_monetary_cap", False) is not False:
            raise BootstrapError("A bounded approval cannot also waive its monetary ceiling.")
    elif budget_policy == "NO_MONETARY_CAP_EXPLICITLY_APPROVED":
        if (
            approval.get("budget_amount") is not None
            or approval.get("acknowledge_no_monetary_cap") is not True
            or not isinstance(approval.get("request_evidence"), str)
            or not approval["request_evidence"].strip()
        ):
            raise BootstrapError("No-cap approval requires an explicit policy, acknowledgment, and private original authorization evidence.")
    else:
        raise BootstrapError("Unsupported monetary approval policy.")
    if approval.get("retention_days") != config["retention_days"]:
        raise BootstrapError("Approval retention differs from the planned retention.")
    for field in ("max_calls", "max_candidates", "max_epochs", "max_training_jobs"):
        if not _integer(approval.get(field)):
            raise BootstrapError("Approval requires nonnegative integer call, candidate, epoch, and job limits.")
    if not _integer(approval.get("max_provisioning_retries", 0)):
        raise BootstrapError("Optional max_provisioning_retries must be a nonnegative integer; omitted means zero.")
    for field in ("max_wait_seconds", "max_hosting_hours"):
        if not _integer(approval.get(field), 1):
            raise BootstrapError("Approval requires bounded positive wait and hosting durations.")
    for field in ("allow_training", "allow_global_training", "accept_deprecated_models"):
        if type(approval.get(field)) is not bool:
            raise BootstrapError("Training, global training, and deprecation approvals must be explicit booleans.")
    for field in (
        "allow_global_inference", "allow_resource_creation", "allow_rbac_assignments",
        "acknowledge_continuous_hosting", "acknowledge_unknown_cost",
    ):
        if approval.get(field) is not True:
            raise BootstrapError("Resource creation, RBAC, global inference, continuous hosting, and unknown costs need explicit approval.")
    if approval["allow_training"]:
        if not approval["max_epochs"] or not approval["max_training_jobs"]:
            raise BootstrapError("Training approval requires positive epoch and job bounds.")
    elif approval["max_epochs"] or approval["max_training_jobs"] or approval["allow_global_training"]:
        raise BootstrapError("Disabled training must have zero training bounds and no global-training approval.")
    if "runtime_bounds" in approval:
        bounds = approval["runtime_bounds"]
        if not isinstance(bounds, dict):
            raise BootstrapError("Runtime bounds must be an explicit object.")
        counts = (
            "prompt_optimizer_jobs", "agent_optimizer_jobs", "candidates_per_optimizer_job",
            "training_rows", "validation_rows", "fresh_holdout_rows",
        )
        if any(key in bounds and not _integer(bounds[key]) for key in counts):
            raise BootstrapError("Runtime job/candidate/row limits must be nonnegative integers.")
        if bounds.get("preserve_resource_group") is not True or bounds.get("allow_deletion") is not False:
            raise BootstrapError("Runtime bounds must preserve the group and explicitly forbid deletion.")
        if "synthetic_data_only" in bounds and bounds["synthetic_data_only"] is not True:
            raise BootstrapError("This learning-loop approval covers synthetic data only.")
        if "max_wait_seconds_per_job" in bounds and (
            not _integer(bounds["max_wait_seconds_per_job"], 1)
            or bounds["max_wait_seconds_per_job"] > approval["max_wait_seconds"]
        ):
            raise BootstrapError("Runtime per-job wait cannot exceed the approved wait bound.")
        if bounds.get("candidates_per_optimizer_job", 0) > approval["max_candidates"]:
            raise BootstrapError("Runtime candidate limit exceeds the approved candidate bound.")
    try:
        start = datetime.fromisoformat(approval["approved_at"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(approval["expires_at"].replace("Z", "+00:00"))
        current = now or _now()
        if start.utcoffset() is None or end.utcoffset() is None or not start <= current < end:
            raise ValueError
        if end - start > timedelta(hours=approval["max_hosting_hours"]):
            raise ValueError
    except (AttributeError, TypeError, ValueError, OverflowError) as exc:
        raise BootstrapError("Approval must be currently valid, timezone-aware, and expire within the hosting bound.") from exc


def _approved_record(config: dict, path: Path | str | None) -> dict:
    if path is None:
        raise ApprovalError("No bounded approval supplied; resource creation, RBAC, and paid operations remain blocked.")
    try:
        approval = _read(Path(path))
        validate_approval(config, approval)
    except BootstrapError as exc:
        raise ApprovalError(str(exc)) from exc
    return approval


def _authorization(config: dict, path: Path | str | None, *, deprecated: bool = False) -> dict:
    try:
        approval = _approved_record(config, path)
        if deprecated and not approval["accept_deprecated_models"]:
            raise ApprovalError("The selected deprecating model still requires explicit acceptance.")
    except ApprovalError as exc:
        return {
            "status": AWAITING_APPROVAL, "approval_status": "MISSING" if path is None else "INVALID",
            "approval_reason": str(exc),
        }
    return {
        "status": "READY_FOR_APPROVED_APPLY", "approval_status": "APPROVED",
        "approval_sha256": _digest(approval),
    }


def plan(
    *, subscription_id: str, tenant_id: str, expected_user: str,
    environment: str | None = None, root: Path | str = Path(".lab"),
    location: str = REGION, retention_days: int = 30, models: list[dict] | None = None,
    resource_group: str | None = None, agent_sku: str | None = None,
) -> dict:
    """Create a private local plan only; never query Azure or overwrite .env/artifacts."""
    instance = uuid4()
    suffix = instance.hex[:8]
    date = _now().strftime("%Y%m%d")
    environment = environment or f"lab-{date}-{suffix}"
    root = Path(root)
    if root.is_symlink() or any(parent.is_symlink() for parent in root.parents):
        raise BootstrapError("Environment root must not traverse symlinks.")
    directory = root.resolve() / environment
    selected = deepcopy(list(DEFAULT_MODELS) if models is None else models)
    if agent_sku is not None and agent_sku not in {"Standard", "GlobalStandard"}:
        raise BootstrapError("Explicit agent SKU must be Standard or GlobalStandard.")
    for model in selected:
        if not isinstance(model, dict) or not isinstance(model.get("roles"), list) or not model["roles"]:
            raise BootstrapError("Each model requires a nonempty roles array.")
        model.setdefault("sku", "GlobalStandard")
        if agent_sku is not None and "agent" in model["roles"]:
            model["sku"] = agent_sku
        model.setdefault("deployment", f"lab-{model.get('roles', ['model'])[0]}-{suffix}")
    config = {
        "schema_version": SCHEMA_VERSION, "instance_id": str(instance), "created_at": _stamp(),
        "environment": environment, "environment_dir": str(directory),
        "subscription_id": subscription_id, "tenant_id": tenant_id, "expected_user": expected_user,
        "location": location, "retention_days": retention_days, "models": selected,
        "deployment_name": f"lab-bootstrap-{suffix}",
        "template_sha256": _file_digest(TEMPLATE),
        "names": {
            "resource_group": resource_group or f"rg-foundry-eval-v11-{date}-{suffix}",
            "account": f"ai-fev11-{date}-{suffix}", "project": f"proj-fev11-{suffix}",
            "search": f"srch-fev11-{date}-{suffix}", "workspace": f"log-fev11-{date}-{suffix}",
            "insights": f"appi-fev11-{date}-{suffix}",
        },
    }
    config["scope_sha256"] = _scope(config)
    _validate(config)
    try:
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        directory.mkdir(mode=0o700)
    except FileExistsError as exc:
        raise BootstrapError("Environment already exists; use its config to inspect/resume, never overwrite it.") from exc
    _write(directory / ".gitignore", "*\n", text=True)
    (directory / "artifacts").mkdir(mode=0o700)
    (directory / "evidence").mkdir(mode=0o700)
    manifest = {
        "schema_version": SCHEMA_VERSION, "scope_sha256": config["scope_sha256"],
        "phase": "planned", "created_at": _stamp(), "resources": _resources(config),
        "attempts": [], "operator_principal_id": None, "env_sha256": None,
    }
    _write(directory / "config.json", config)
    _write(directory / "template.json", TEMPLATE.read_text(encoding="utf-8"), text=True)
    _write(directory / "approval.example.json", approval_template(config))
    _write(directory / "group-authorization.example.json", group_authorization_template(config))
    _write(directory / "manifest.json", manifest)
    _write(directory / "cost-ledger.json", cost_ledger(manifest))
    return {
        "status": AWAITING_APPROVAL, "plan_status": "CREATED_LOCAL_ONLY",
        "approval_status": "MISSING", "live_status": "NOT_RUN", "mutations_performed": False,
        "scope_sha256": config["scope_sha256"],
        "config_path": str(directory / "config.json"),
        "approval_example_path": str(directory / "approval.example.json"),
        "env_path": str(directory / ".env"), "artifacts_dir": str(directory / "artifacts"),
        "models": selected,
        "warning": "No Azure calls made. Candidate versions/SKUs/quota require fresh preflight and explicit approval.",
    }


def group_authorization_template(config: dict) -> dict:
    """A separate, initially unauthorized request for the empty resource group only."""
    return {
        "schema_version": SCHEMA_VERSION, "authorized": False,
        "scope_sha256": config["scope_sha256"], "resource_group_id": _ids(config)["resource_group"],
        "allowed_operations": ["resource_group.create"], "authorized_by": "",
        "authorized_at": None, "request_evidence": "",
        "paid_resources_approved": False, "rbac_approved": False, "deletion_approved": False,
        "preserve_group": True,
    }


def _validate_group_authorization(config: dict, authorization: dict) -> None:
    if (
        authorization.get("schema_version") != SCHEMA_VERSION
        or authorization.get("authorized") is not True
        or authorization.get("scope_sha256") != config["scope_sha256"]
        or authorization.get("resource_group_id") != _ids(config)["resource_group"]
        or authorization.get("allowed_operations") != ["resource_group.create"]
        or authorization.get("authorized_by", "").casefold() != config["expected_user"].casefold()
        or not isinstance(authorization.get("request_evidence"), str)
        or not authorization["request_evidence"].strip()
        or authorization.get("preserve_group") is not True
        or any(authorization.get(key) is not False for key in (
            "paid_resources_approved", "rbac_approved", "deletion_approved",
        ))
    ):
        raise ApprovalError("Group-only authorization must explicitly cover this empty group and nothing else.")
    try:
        when = datetime.fromisoformat(authorization["authorized_at"].replace("Z", "+00:00"))
        if when.utcoffset() is None or when > _now():
            raise ValueError
    except (AttributeError, TypeError, ValueError) as exc:
        raise ApprovalError("Group-only authorization requires a valid, timezone-aware past timestamp.") from exc


def prepare_group_creation(
    config_path: Path | str, authorization_path: Path | str, *, run: Run = az_json,
) -> dict:
    """Persist a group-only intent and external creation contract; never mutate Azure."""
    directory, config, _ = _load(config_path)
    authorization = _read(Path(authorization_path))
    _validate_group_authorization(config, authorization)
    with _lock(directory):
        directory, config, manifest = _load(config_path)
        identity = _identity(config, manifest, run)
        group = manifest["resources"]["resource_group"]
        if _get(group, run) is not None:
            raise BootstrapError("The proposed group already exists; this preparation never adopts resources.")
        if group["status"] not in {"planned", "pending"}:
            raise BootstrapError("A previously created group is missing; no automatic restoration.")
        previous = manifest.get("group_only_authorization_sha256")
        authorization_hash = _digest(authorization)
        if previous not in {None, authorization_hash}:
            raise BootstrapError("Group creation is already pending under a different authorization.")
        if previous is None:
            evidence = directory / "evidence" / f"group-authorization-{uuid4().hex}.local.json"
            _write(evidence, authorization)
            manifest["operator_principal_id"] = identity["user"]["id"]
            manifest["group_only_authorization_sha256"] = authorization_hash
            manifest["group_only_authorization_path"] = str(evidence)
            group["status"] = "pending"
            manifest["phase"] = "group_only_creation_pending"
            manifest["attempts"].append({
                "phase": "group_only_creation_pending", "at": _stamp(),
                "authorization_sha256": authorization_hash, "authorization_kind": "resource_group_only",
                "pending_ids": [group["id"]],
            })
            _save(directory, manifest)
        contract = {
            "status": AWAITING_APPROVAL, "group_creation_status": "AUTHORIZED_EXTERNAL_CREATE_PENDING",
            "paid_resources_status": AWAITING_APPROVAL, "rbac_status": AWAITING_APPROVAL,
            "live_status": "NOT_VERIFIED", "mutations_performed": False,
            "scope_sha256": config["scope_sha256"], "authorization_sha256": authorization_hash,
            "config_path": str(directory / "config.json"), "resource_group_id": group["id"],
            "subscription_id": config["subscription_id"], "tenant_id": config["tenant_id"],
            "resource_group": config["names"]["resource_group"], "location": REGION,
            "method": "PUT", "url": f"{ARM}{group['id']}?api-version={group['api_version']}",
            "headers": {"If-None-Match": "*"}, "body": {"location": REGION, "tags": _tags(config)},
            "preserve_group": True, "allowed_operations": ["resource_group.create"],
            "warning": "Recheck absence immediately before external conditional PUT. No role/billed-resource/deletion authorization.",
        }
        contract_path = directory / "group-create-contract.local.json"
        if contract_path.exists():
            if _read(contract_path) != contract:
                raise BootstrapError("Existing group creation contract differs; refusing overwrite.")
        else:
            _write(contract_path, contract)
        return contract


def confirm_group_creation(config_path: Path | str, *, run: Run = az_json) -> dict:
    """Read-only Azure confirmation of an externally created, previously recorded empty group."""
    directory, config, _ = _load(config_path)
    with _lock(directory):
        directory, config, manifest = _load(config_path)
        if not manifest.get("group_only_authorization_sha256"):
            raise BootstrapError("No pre-existing group-only creation intent; never adopt an existing group.")
        _identity(config, manifest, run)
        group = manifest["resources"]["resource_group"]
        remote = _get(group, run)
        if remote is None:
            raise BootstrapError("Authorized group creation is not yet observable; do not repeat blindly.")
        _owned(config, "resource_group", group, remote, manifest, {})
        if remote.get("properties", {}).get("provisioningState") != "Succeeded":
            raise BootstrapError("The group's provisioning state is not Succeeded.")
        listed = run(["resource", "list", "--subscription", config["subscription_id"],
                      "--resource-group", config["names"]["resource_group"]])
        if listed != []:
            raise BootstrapError("Group-only authorization cannot confirm a nonempty group.")
        group["status"] = "present"
        manifest["phase"] = "group_created_awaiting_approval"
        manifest["group_confirmed_at"] = _stamp()
        _save(directory, manifest)
        _write(directory / "evidence" / f"group-observed-{uuid4().hex}.local.json", remote)
        return {
            "status": AWAITING_APPROVAL, "group_creation_status": "CONFIRMED_CREATED",
            "paid_resources_status": AWAITING_APPROVAL, "rbac_status": AWAITING_APPROVAL,
            "scope_sha256": config["scope_sha256"], "preserve_group": True,
            "live_status": "NOT_VERIFIED", "mutations_performed": False,
            "observed_resource_count": 1,
        }


def _coordinator_group_tags(config: dict, intent: dict, created: dict) -> dict:
    if (
        intent.get("kind") != "explicitly-authorized-resource-group-creation"
        or intent.get("status") != "INTENT_RECORDED_BEFORE_CREATE"
        or intent.get("resource_group") != config["names"]["resource_group"]
        or intent.get("subscription_id") != config["subscription_id"]
        or intent.get("tenant_id") != config["tenant_id"]
        or intent.get("location") != REGION
        or not _uuid(intent.get("ownership_id"))
        or not isinstance(intent.get("user_authorization"), str)
        or not intent["user_authorization"].strip()
        or not re.fullmatch(r"[a-f0-9]{40}", intent.get("source_commit", ""))
    ):
        raise BootstrapError("Coordinator intent must precede creation and match this exact new lab scope.")
    tags = {
        "lab": "foundry-learning-loop-v1.1",
        "lab-environment": config["names"]["resource_group"].removeprefix("rg-foundry-eval-v11-"),
        "lab-ownership": intent["ownership_id"], "managed-by": "foundry-evaluation-labs-v1.1",
        "source-commit": intent["source_commit"][:7], "retention": "review-no-auto-delete",
    }
    if (
        str(created.get("id", "")).lower() != _ids(config)["resource_group"].lower()
        or created.get("name") != config["names"]["resource_group"]
        or created.get("location", "").replace(" ", "").lower() != REGION
        or created.get("type", "").lower() != "microsoft.resources/resourcegroups"
        or created.get("properties", {}).get("provisioningState") != "Succeeded"
        or created.get("tags") != tags
    ):
        raise BootstrapError("Creation response does not match the coordinator's exact ownership/retention tags.")
    return tags


def bind_created_group(
    config_path: Path | str, intent_path: Path | str, created_path: Path | str, *,
    run: Run = az_json,
) -> dict:
    """Bind a coordinator-created empty lab RG using original intent/creation receipts; no Azure writes."""
    directory, config, _ = _load(config_path)
    intent, created = _read(Path(intent_path)), _read(Path(created_path))
    tags = _coordinator_group_tags(config, intent, created)
    with _lock(directory):
        directory, config, manifest = _load(config_path)
        identity = _identity(config, manifest, run)
        group = manifest["resources"]["resource_group"]
        if any(spec["status"] != "planned" for key, spec in manifest["resources"].items() if key != "resource_group"):
            raise BootstrapError("Cannot change ownership bindings after child-resource provisioning has started.")
        existing = manifest.get("external_group_binding")
        if existing and (
            existing["intent_sha256"] != _digest(intent) or existing["created_sha256"] != _digest(created)
        ):
            raise BootstrapError("The group is already bound to different creation receipts.")
        remote = _get(group, run)
        if remote is None or _coordinator_group_tags(config, intent, remote) != tags:
            raise BootstrapError("The coordinator-created group is absent or its ownership changed.")
        listed = run(["resource", "list", "--subscription", config["subscription_id"],
                      "--resource-group", config["names"]["resource_group"]])
        if listed != []:
            raise BootstrapError("Receipt-based reconciliation permits only the coordinator's empty new group.")
        if existing is None:
            token = uuid4().hex
            intent_file = f"group-binding-{token}.intent.local.json"
            created_file = f"group-binding-{token}.created.local.json"
            _write(directory / "evidence" / intent_file, intent)
            _write(directory / "evidence" / created_file, created)
            manifest["external_group_binding"] = {
                "kind": "coordinator-created-empty-group", "bound_at": _stamp(), "tags": tags,
                "intent_file": intent_file, "created_file": created_file,
                "intent_sha256": _digest(intent), "created_sha256": _digest(created),
            }
            manifest["operator_principal_id"] = identity["user"]["id"]
            manifest["attempts"].append({
                "phase": "coordinator_group_created", "at": _stamp(),
                "authorization_kind": "coordinator_intent_and_creation_receipts",
                "intent_sha256": _digest(intent), "created_sha256": _digest(created),
                "pending_ids": [group["id"]],
            })
            group["status"] = "present"
            manifest["phase"] = "coordinator_group_bound"
            _save(directory, manifest)
        return {
            "status": "GROUP_OWNERSHIP_BOUND", "scope_sha256": config["scope_sha256"],
            "existing_tags_preserved": True, "mutations_performed": False,
            "child_resources_created": False, "live_status": "PENDING_EXECUTION",
            "warning": "Binding is not cost approval; apply still validates the exact bounded approval record.",
        }


def _get(resource: dict, run: Run) -> dict | None:
    try:
        value = run(["rest", "--method", "GET", "--url",
                     f"{ARM}{resource['id']}?api-version={resource['api_version']}"])
    except AzureCommandError as exc:
        if exc.code in {
            "ResourceNotFound", "ResourceGroupNotFound", "ParentResourceNotFound",
            "DeploymentNotFound", "RoleAssignmentNotFound", "NotFound", "NotFoundError",
        }:
            return None
        raise
    if not isinstance(value, dict):
        raise BootstrapError("Resource lookup did not return an object.")
    return value


def require_owned_resources(
    config_path: Path | str, account_id: str, *, run: Run = az_json,
) -> dict:
    """Verify completed bootstrap ownership before a caller's new mutation; never write Azure."""
    _, config, manifest = _load(config_path)
    ids = _ids(config)
    if not isinstance(account_id, str) or account_id.lower() != ids["account"].lower():
        raise BootstrapError("Requested account is outside the immutable bootstrap plan.")
    keys = ("resource_group", "account", "arm_deployment")
    if manifest.get("phase") != "succeeded" or any(
        manifest["resources"][key]["status"] != "succeeded" for key in keys
    ):
        raise BootstrapError("Complete and verify this bootstrap before creating any additional billed resource.")
    _identity(config, manifest, run)
    observed = {}
    for key in keys:
        spec = manifest["resources"][key]
        remote = _get(spec, run)
        if remote is None:
            raise BootstrapError(f"Required owned bootstrap resource is missing: {key}.")
        _owned(config, key, spec, remote, manifest, observed)
        if remote.get("properties", {}).get("provisioningState") != "Succeeded":
            raise BootstrapError(f"Owned bootstrap resource is not ready: {key}.")
        observed[key] = remote
    return {
        "status": "OWNED_BOOTSTRAP_SCOPE_VERIFIED",
        "scope_sha256": config["scope_sha256"],
        "resource_group_id": ids["resource_group"], "account_id": ids["account"],
        "location": REGION, "mutations_performed": False,
        "authorization_verified": False,
        "warning": "Private scope evidence only; caller must separately enforce current cost/processing/job approval.",
    }


def _identity(config: dict, manifest: dict, run: Run) -> dict:
    account = run(["account", "show"])
    if (
        not isinstance(account, dict)
        or account.get("id", "").lower() != config["subscription_id"].lower()
        or account.get("tenantId", "").lower() != config["tenant_id"].lower()
        or account.get("state") != "Enabled"
        or account.get("user", {}).get("type", "").lower() != "user"
        or account.get("user", {}).get("name", "").casefold() != config["expected_user"].casefold()
    ):
        raise BootstrapError("Active Azure CLI subscription/tenant/user differs; no automatic account switch.")
    user = run([
        "rest", "--method", "GET", "--url", "https://graph.microsoft.com/v1.0/me?$select=id,userPrincipalName",
        "--resource", "https://graph.microsoft.com", "--subscription", config["subscription_id"],
    ])
    if (
        not isinstance(user, dict) or not _uuid(user.get("id"))
        or user.get("userPrincipalName", "").casefold() != config["expected_user"].casefold()
        or manifest.get("operator_principal_id") not in {None, user.get("id")}
    ):
        raise BootstrapError("The signed-in principal is not independently verified for this environment.")
    return {"account": account, "user": user}


def _owned(config: dict, key: str, spec: dict, remote: dict, manifest: dict, observed: dict) -> None:
    if str(remote.get("id", "")).lower() != spec["id"].lower():
        raise BootstrapError(f"Resource identity mismatch: {key}.")
    if spec["status"] == "planned":
        raise BootstrapError(f"Resource collision before a recorded creation attempt: {key}.")
    ownership_tags = (
        manifest.get("external_group_binding", {}).get("tags", _tags(config))
        if key == "resource_group" else _tags(config)
    )
    if spec["taggable"] and any(remote.get("tags", {}).get(k) != v for k, v in ownership_tags.items()):
        raise BootstrapError(f"Ownership tag mismatch: {key}; no adoption or overwrite.")
    if key in {"resource_group", *RESOURCE_TYPES}:
        if remote.get("location", "").replace(" ", "").lower() != REGION:
            raise BootstrapError(f"Region mismatch: {key}; no fallback.")
    props = remote.get("properties", {})
    if key == "search_connection":
        if props.get("metadata", {}).get("lab_instance") != config["instance_id"]:
            raise BootstrapError("Unknown Search connection; no overwrite.")
        if props.get("authType") != "AAD" or props.get("target", "").rstrip("/") != f"https://{config['names']['search']}.search.windows.net":
            raise BootstrapError("Search connection authentication/target changed.")
    if key == "insights_connection":
        metadata = props.get("metadata", {})
        target = _ids(config)["insights"].lower()
        if (
            props.get("authType") != "ProjectManagedIdentity"
            or props.get("category") != "AppInsights"
            or str(props.get("target", "")).lower() != target
            or str(metadata.get("ResourceId", "")).lower() != target
            or metadata.get("lab_instance") != config["instance_id"]
        ):
            raise BootstrapError("Application Insights connection must use this project's managed identity and owned telemetry resource.")
        if TRACE_ROUTING_KEY in metadata:
            expected = observed.get("insights", {}).get("properties", {}).get("ConnectionString")
            if not expected or metadata[TRACE_ROUTING_KEY] != expected:
                raise BootstrapError("Application Insights routing metadata differs from the owned component.")
    if key.startswith("role:"):
        role = spec["role"]
        principal = manifest.get("operator_principal_id") if role["principal"] == "operator" else (
            observed.get(role["principal"], {}).get("identity", {}).get("principalId")
        )
        if (
            not principal or props.get("principalId", "").lower() != principal.lower()
            or props.get("scope", "").lower() != role["scope"].lower()
            or not props.get("roleDefinitionId", "").lower().endswith("/" + role["role_id"])
            or props.get("description") != role["description"]
        ):
            raise BootstrapError(f"Role binding mismatch: {key}; never restore broad permissions.")
    if key.startswith("model:"):
        desired = spec["model"]
        model = props.get("model", {})
        if (
            any(model.get(k) != desired[k] for k in ("name", "version"))
            or model.get("format") != "OpenAI"
            or remote.get("sku", {}).get("name") != desired["sku"]
            or remote.get("sku", {}).get("capacity") != desired["capacity"]
            or props.get("versionUpgradeOption") != "NoAutoUpgrade"
        ):
            raise BootstrapError(f"Model deployment drift: {key}; create a newly approved plan.")
    if key == "account" and (remote.get("kind") != "AIServices" or props.get("disableLocalAuth") is not True):
        raise BootstrapError("Foundry account kind/local authentication differs from the plan.")
    if key == "search" and (
        remote.get("sku", {}).get("name", "").lower() != "basic"
        or props.get("disableLocalAuth") is not True
        or props.get("partitionCount") != 1 or props.get("replicaCount") != 1
    ):
        raise BootstrapError("Search SKU/capacity/keyless configuration drifted.")
    if key in {"account", "project", "search"} and (
        "SystemAssigned" not in remote.get("identity", {}).get("type", "")
        or not _uuid(remote.get("identity", {}).get("principalId"))
    ):
        raise BootstrapError(f"System-assigned identity is not ready: {key}.")
    if key == "workspace" and (
        props.get("sku", {}).get("name") != "PerGB2018"
        or props.get("retentionInDays") != config["retention_days"]
        or props.get("features", {}).get("disableLocalAuth") is not True
    ):
        raise BootstrapError("Log Analytics SKU/retention/keyless configuration drifted.")
    if key == "insights" and (
        str(props.get("WorkspaceResourceId", "")).lower() != _ids(config)["workspace"].lower()
        or props.get("DisableLocalAuth") is not True
    ):
        raise BootstrapError("Application Insights must be workspace-based and Entra-only.")
    if key == "arm_deployment" and (
        props.get("mode") != "Incremental"
        or props.get("parameters", {}).get("tags", {}).get("value") != _tags(config)
        or props.get("parameters", {}).get("names", {}).get("value") != config["names"]
    ):
        raise BootstrapError("ARM deployment record is not bound to this isolated plan.")


def _inspect(config: dict, manifest: dict, run: Run) -> dict:
    observed = {}
    # JSON object order is not a dependency contract: verify the group and MI owners first.
    for key in _resources(config):
        spec = manifest["resources"][key]
        if key != "resource_group" and "resource_group" not in observed:
            break
        remote = _get(spec, run)
        if remote is None:
            continue
        _owned(config, key, spec, remote, manifest, observed)
        observed[key] = remote
    if "resource_group" in observed:
        listed = run(["resource", "list", "--subscription", config["subscription_id"],
                      "--resource-group", config["names"]["resource_group"]])
        allowed = {r["id"].lower() for r in manifest["resources"].values()}
        if not isinstance(listed, list) or any(str(row.get("id", "")).lower() not in allowed for row in listed):
            raise BootstrapError("The lab group contains an unknown resource; incremental apply is blocked.")
    return observed


def _allows(permissions: list[dict], action: str) -> bool:
    action = action.lower()
    return any(
        any(fnmatchcase(action, p.lower()) for p in entry.get("actions", []))
        and not any(fnmatchcase(action, p.lower()) for p in entry.get("notActions", []))
        for entry in permissions
    )


def _prerequisites(config: dict, run: Run) -> dict:
    for provider in ("Microsoft.CognitiveServices", "Microsoft.Search", "Microsoft.OperationalInsights", "Microsoft.Insights"):
        response = run(["provider", "show", "--namespace", provider, "--subscription", config["subscription_id"]])
        if response.get("registrationState") != "Registered":
            raise BootstrapError(f"Provider {provider} is not registered; bootstrap never registers providers.")
    permissions = run(["rest", "--method", "GET", "--url",
                       f"{ARM}/subscriptions/{config['subscription_id']}/providers/Microsoft.Authorization/permissions?api-version=2022-04-01"])
    needed = [
        "Microsoft.Resources/subscriptions/resourceGroups/write",
        "Microsoft.Resources/deployments/write", "Microsoft.Authorization/roleAssignments/write",
        *(f"{kind}/write" for kind, _ in RESOURCE_TYPES.values()),
        "Microsoft.CognitiveServices/accounts/deployments/write",
        "Microsoft.CognitiveServices/accounts/projects/connections/write",
    ]
    if not all(_allows(permissions.get("value", []), action) for action in needed):
        raise BootstrapError("Existing permissions do not cover provisioning plus scoped role assignment; no role escalation.")
    return {"providers_registered": True, "provisioning_permissions_verified": True}


def _model_checks(config: dict, catalog: list, usage: list, capacities: dict, observed: dict) -> list[dict]:
    required = defaultdict(int)
    regional_required = defaultdict(int)
    regional_limits = {}
    selected, quota = [], {}
    for model in config["models"]:
        matches = [
            item.get("model", item) for item in catalog
            if item.get("kind", "AIServices") == "AIServices"
            and all(item.get("model", item).get(k) == model[k] for k in ("name", "version"))
            and item.get("model", item).get("format") == "OpenAI"
        ]
        if not matches:
            raise BootstrapError(f"Exact regional model/version unavailable: {model['name']}.")
        skus = [sku for item in matches for sku in item.get("skus", [])
                if sku.get("name") == model["sku"]
                and isinstance(sku.get("usageName"), str)
                and sku["usageName"].startswith(f"OpenAI.{model['sku']}.")
                and not sku["usageName"].endswith("-finetune")
                and (model.get("usage_name") is None or sku["usageName"] == model["usage_name"])]
        unique = {_digest(sku): sku for sku in skus}
        if len(unique) != 1:
            raise BootstrapError(f"Model SKU/quota mapping is absent or ambiguous: {model['name']}.")
        sku = next(iter(unique.values()))
        usage_name = sku["usageName"]
        bounds = sku.get("capacity") or {}
        capacity = model["capacity"]
        low, high, step, allowed = (bounds.get(k) for k in ("minimum", "maximum", "step", "allowedValues"))
        if (
            any(value is not None and not _number(value) for value in (low, high, step))
            or allowed is not None and (
                not isinstance(allowed, list) or any(not _number(value) for value in allowed)
            )
        ):
            raise BootstrapError(f"Invalid live capacity constraints: {model['name']}.")
        if (
            low is not None and capacity < low or high is not None and capacity > high
            or step is not None and (not _number(step) or step <= 0 or (capacity - (low or 0)) % step)
            or allowed and capacity not in allowed
        ):
            raise BootstrapError(f"Capacity violates live SKU constraints: {model['name']}.")
        usages = [row for row in usage if row.get("name", {}).get("value") == usage_name]
        if len(usages) != 1 or not all(_number(usages[0].get(k)) for k in ("limit", "currentValue")):
            raise BootstrapError(f"Free quota cannot be verified: {model['name']}; no inferred allocation.")
        row = usages[0]
        available = row["limit"] - row["currentValue"]
        if available < 0 or row["currentValue"] < 0:
            raise BootstrapError(f"Quota is overdrawn or invalid: {model['name']}.")
        current = observed.get(f"model:{model['deployment']}", {}).get("sku", {}).get("capacity", 0)
        additional = max(0, capacity - current)
        required[usage_name] += additional
        quota[usage_name] = available
        regional = [
            row["properties"] for row in capacities[model["deployment"]].get("value", [])
            if row.get("properties", {}).get("skuName") == model["sku"]
            and row.get("properties", {}).get("model", {}).get("name") == model["name"]
            and row.get("properties", {}).get("model", {}).get("version") == model["version"]
        ]
        if not regional or not all(_number(r.get("availableCapacity")) for r in regional):
            raise BootstrapError(f"Regional model capacity could not be verified: {model['name']}.")
        regional_free = min(r["availableCapacity"] for r in regional)
        regional_key = (model["name"], model["version"], model["sku"])
        regional_required[regional_key] += additional
        regional_limits[regional_key] = min(regional_free, regional_limits.get(regional_key, regional_free))
        if regional_free < additional:
            raise BootstrapError(f"Insufficient regional model capacity: {model['name']}; no alternate region.")
        lifecycle = {item.get("lifecycleStatus", "Unknown") for item in matches}
        if lifecycle & {"Retired", "Disabled", "Deleted"}:
            raise BootstrapError(f"Model lifecycle does not permit deployment: {model['name']}.")
        selected.append({
            **model, "usage_name": usage_name, "quota_limit": row["limit"],
            "quota_used": row["currentValue"], "free_available_units": available,
            "required_additional_units": additional, "regional_available_units": regional_free,
            "capacity_unit": "ARM SKU units; model-specific, not a universal TPM multiplier",
            "capacity_constraints": bounds, "rate_limits": sku.get("rateLimits"),
            "lifecycle": sorted(lifecycle),
            "deprecated": bool(lifecycle & {"Deprecating", "Deprecated"}),
            "fine_tune_capability": any(str(item.get("capabilities", {}).get("fineTune")).lower() == "true" for item in matches),
        })
    for name, additional in required.items():
        if additional > quota[name]:
            raise BootstrapError(f"Insufficient unallocated quota for all requested deployments: {name}.")
    for key, additional in regional_required.items():
        if additional > regional_limits[key]:
            raise BootstrapError(f"Insufficient regional capacity for all requested deployments: {key[0]}.")
    return selected


def _preflight(config: dict, manifest: dict, run: Run) -> tuple[dict, dict, dict]:
    identity = _identity(config, manifest, run)
    prerequisites = _prerequisites(config, run)
    args = ["--location", REGION, "--subscription", config["subscription_id"]]
    catalog = run(["cognitiveservices", "model", "list", *args])
    usage = run(["cognitiveservices", "usage", "list", *args])
    if not isinstance(catalog, list) or not isinstance(usage, list):
        raise BootstrapError("Regional model catalog/quota response is invalid.")
    capacities = {}
    for model in config["models"]:
        query = urlencode({
            "api-version": "2024-10-01", "modelFormat": "OpenAI",
            "modelName": model["name"], "modelVersion": model["version"],
        })
        capacities[model["deployment"]] = run([
            "rest", "--method", "GET", "--url",
            f"{ARM}/subscriptions/{config['subscription_id']}/providers/Microsoft.CognitiveServices/locations/{REGION}/modelCapacities?{query}",
        ])
    observed = _inspect(config, manifest, run)
    checks = _model_checks(config, catalog, usage, capacities, observed)
    report = {
        "status": "READY", "scope_sha256": config["scope_sha256"], "checked_at": _stamp(),
        "region": REGION, "identity_verified": True, **prerequisites, "models": checks,
        "owned_resource_count": len(observed), "mutations_performed": False,
        "not_verified": [
            "No paid inference, training, runtime data-plane access, or RBAC propagation tested.",
            "MCP principal is not inferred from matching subscription/tenant.",
            "Available quota is unallocated capacity, not free pricing or a spend cap.",
            "Fine-tuning region, training quota, deployment availability, and cost require separate preflight/approval.",
        ],
    }
    raw = {"identity": identity, "catalog": catalog, "usage": usage, "capacities": capacities, "observed": observed}
    return report, raw, observed


def preflight(
    config_path: Path | str, *, run: Run = az_json, persist: bool = True,
    approval_path: Path | str | None = None,
) -> dict:
    """Read-only Azure preflight, independent of the existence of a Foundry account."""
    directory, config, manifest = _load(config_path)
    try:
        report, raw, observed = _preflight(config, manifest, run)
        if "resource_group" in observed:
            validation = _validate_arm(directory, config, raw["identity"]["user"]["id"], run)
            report["arm_validation_status"] = "PASSED"
            raw["arm_validation"] = validation
        else:
            report["arm_validation_status"] = "DEFERRED_RESOURCE_GROUP_ABSENT"
            report["not_verified"].append("Provider validation requires the new owned resource group and must pass before any child-resource create.")
    except BootstrapError as exc:
        report = {"status": "BLOCKED", "scope_sha256": config["scope_sha256"],
                  "region": REGION, "reason": str(exc), "error_code": getattr(exc, "code", None),
                  "arm_validation_status": "FAILED" if getattr(exc, "validation_evidence_file", None) else "NOT_RUN",
                  "mutations_performed": False}
        raw = _error_record(exc)
    report["readiness_status"] = report["status"]
    authorization = _authorization(
        config, approval_path, deprecated=any(model["deprecated"] for model in report.get("models", [])),
    )
    if report["readiness_status"] == "READY":
        report.update(authorization)
    else:
        report.update({key: value for key, value in authorization.items() if key != "status"})
    report["live_status"] = "PENDING_EXECUTION" if report["approval_status"] == "APPROVED" else "NOT_VERIFIED"
    if report.get("arm_validation_status") == "FAILED":
        report["live_status"] = "BLOCKED_PROVIDER_VALIDATION"
    if persist:
        token = uuid4().hex
        _write(directory / "evidence" / f"preflight-{token}.local.json", raw)
        _write(directory / "evidence" / f"preflight-{token}.redacted.json", report)
    return report


@contextmanager
def _lock(directory: Path):
    path = directory / ".bootstrap.lock"
    _write(path, {"pid": os.getpid(), "started_at": _stamp()})
    try:
        yield
    finally:
        path.unlink()


def _parameters(config: dict, principal: str) -> dict:
    return {
        "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
        "contentVersion": "1.0.0.0",
        "parameters": {key: {"value": value} for key, value in {
            "location": REGION, "names": config["names"], "tags": _tags(config),
            "models": config["models"], "roles": _roles(config),
            "operatorPrincipalId": principal, "retentionDays": config["retention_days"],
        }.items()},
    }


def _error_record(exc: BootstrapError) -> dict:
    return {
        "error": str(exc), "error_code": getattr(exc, "code", None),
        "original_message": getattr(exc, "raw_message", ""),
        "stdout": getattr(exc, "stdout", ""), "stderr": getattr(exc, "stderr", ""),
        "command": getattr(exc, "command", None), "error_payload": getattr(exc, "payload", None),
    }


def _record_failure(directory: Path, stage: str, exc: BootstrapError, *, command: list[str] | None = None) -> str:
    name = f"failure-{stage}-{uuid4().hex}.local.json"
    _write(directory / "evidence" / name, {
        "recorded_at": _stamp(), "stage": stage, **_error_record(exc),
        "command": getattr(exc, "command", None) or command,
    })
    return name


def _validate_arm(directory: Path, config: dict, principal: str, run: Run) -> dict:
    """Provider validation is read-only; catalog lifecycle and free quota cannot replace it."""
    token = uuid4().hex
    parameter_path = directory / "evidence" / f"validation-parameters-{token}.local.json"
    _write(parameter_path, _parameters(config, principal))
    command = [
        "deployment", "group", "validate", "--subscription", config["subscription_id"],
        "--resource-group", config["names"]["resource_group"], "--name", config["deployment_name"],
        "--template-file", str(directory / "template.json"), "--parameters", f"@{parameter_path}",
        "--mode", "Incremental", "--validation-level", "Provider",
    ]
    evidence = directory / "evidence" / f"validation-{token}.local.json"
    record = {
        "requested_at": _stamp(), "status": "PENDING_READ_ONLY_VALIDATION",
        "template_sha256": config["template_sha256"], "command": command,
    }
    _write(evidence, record)
    try:
        result = run(command)
        record["result"] = result
        if not isinstance(result, dict):
            raise BootstrapError("ARM provider validation returned no verifiable JSON result; child creation is blocked.")
        properties = result.get("properties")
        error = result.get("error") or (properties.get("error") if isinstance(properties, dict) else None)
        if not error and result.get("code") and result.get("message"):
            error = result
        if error:
            raise _azure_error("", _json({"error": error}), command)
        if not isinstance(properties, dict):
            raise BootstrapError("ARM provider validation returned no properties; child creation is blocked.")
        if properties.get("provisioningState") not in {None, "Succeeded"}:
            raise AzureCommandError(
                "ArmValidationFailed", command=command, stdout=_json(result), payload=result,
                message="ARM provider validation did not succeed.",
            )
        record.update(status="PASSED", result=result, completed_at=_stamp())
        _write(evidence, record, replace=True)
        return {"status": "PASSED", "parameters_path": str(parameter_path), "evidence_file": evidence.name}
    except BootstrapError as exc:
        if getattr(exc, "command", None) is None:
            exc.command = command
        record.update(status="FAILED", completed_at=_stamp(), failure=_error_record(exc))
        _write(evidence, record, replace=True)
        exc.validation_evidence_file = evidence.name
        raise


def _submission_required(manifest: dict, observed: dict, approval: dict, retry: bool) -> bool:
    attempts = [item for item in manifest["attempts"] if item.get("phase") == "deploying"]
    deployment = observed.get("arm_deployment")
    if deployment is None:
        if attempts:
            raise ProvisioningRetryError(
                "UNKNOWN_SUBMISSION",
                "A prior ARM create attempt exists but its deployment is absent. Submission is unresolved; "
                "inspect the private failure/activity records. Even --retry does not permit blind resubmission.",
            )
        return True
    state = deployment.get("properties", {}).get("provisioningState")
    if state in {"Succeeded", "Running", "Accepted", "Creating", "Updating"}:
        return False
    if state not in {"Failed", "Canceled", "Cancelled"} or not attempts:
        raise ProvisioningRetryError("UNRESOLVED_DEPLOYMENT_STATE", "Cannot prove a terminal owned deployment failure; do not resubmit.")
    if retry is not True:
        raise ProvisioningRetryError("RETRY_REQUIRED", "The owned deployment failed. Retry requires explicit --retry and a current approved max_provisioning_retries allowance.")
    used = max(0, len(attempts) - 1)
    if used >= approval.get("max_provisioning_retries", 0):
        raise ProvisioningRetryError("RETRY_BUDGET_EXHAUSTED", "No approved provisioning retry remains; monetary no-cap permission does not authorize unbounded retries.")
    return True


def _dependency_only_change(original: dict, revised: dict) -> None:
    old, new = deepcopy(original), deepcopy(revised)

    def strip(resources: list[dict]) -> None:
        for resource in resources:
            dependencies = resource.pop("dependsOn", [])
            if not isinstance(dependencies, list) or any(not isinstance(value, str) for value in dependencies):
                raise BootstrapError("Dependency repair requires ordinary resource dependsOn arrays.")
            strip(resource.get("resources", []))

    strip(old.get("resources", []))
    strip(new.get("resources", []))
    if old != new:
        raise BootstrapError("Dependency repair rejects every semantic change outside resource dependsOn.")
    for before, after in zip(original.get("resources", []), revised.get("resources", [])):
        if not set(before.get("dependsOn", [])).issubset(after.get("dependsOn", [])):
            raise BootstrapError("Dependency repair may add ordering, not remove an existing prerequisite.")


def _trace_routing_only_change(original: dict, revised: dict) -> None:
    before, after = deepcopy(original), deepcopy(revised)
    target = "[resourceId('Microsoft.Insights/components', parameters('names').insights)]"
    for template in (before, after):
        connections = [
            resource for resource in template.get("resources", [])
            if resource.get("type") == "Microsoft.CognitiveServices/accounts/projects/connections"
            and resource.get("properties", {}).get("category") == "AppInsights"
        ]
        if len(connections) != 1:
            raise BootstrapError("Routing repair requires exactly the planned App Insights connection.")
        properties = connections[0]["properties"]
        if (
            properties.get("authType") != "ProjectManagedIdentity"
            or properties.get("target") != target
            or properties.get("metadata", {}).get("ResourceId") != target
            or "credentials" in properties
        ):
            raise BootstrapError("Routing repair cannot change authentication or target another component.")
        metadata = properties["metadata"]
        if template is after and metadata.get(TRACE_ROUTING_KEY) != TRACE_ROUTING_EXPRESSION:
            raise BootstrapError("Routing metadata must reference the SAME owned component's ConnectionString; literal values are forbidden.")
        if TRACE_ROUTING_KEY in metadata and metadata.pop(TRACE_ROUTING_KEY) != TRACE_ROUTING_EXPRESSION:
            raise BootstrapError("Routing repair only adds the missing owned-component reference, not a replacement route.")
    if before != after:
        raise BootstrapError("Routing repair allows ONLY metadata.ApplicationInsightsConnectionString; every other template value must remain identical.")


def _verify_failed_deployment(config: dict, manifest: dict, deployment: dict, correlation: str) -> None:
    spec = manifest["resources"]["arm_deployment"]
    _owned(config, "arm_deployment", spec, deployment, manifest, {})
    properties = deployment.get("properties", {})
    actual_parameters = properties.get("parameters", {})
    expected_parameters = _parameters(config, manifest["operator_principal_id"])["parameters"]
    if (
        properties.get("provisioningState") != "Failed"
        or properties.get("correlationId") != correlation
        or set(actual_parameters) != set(expected_parameters)
        or any(actual_parameters[key].get("value") != value["value"] for key, value in expected_parameters.items())
    ):
        raise BootstrapError("Template repair requires the same terminal failed deployment and unchanged parameters.")


def _recover_dependency_transaction(
    directory: Path, config_path: Path, approval_path: Path, *,
    pending_name: str = "dependency-repair.pending.json",
) -> None:
    pending = directory / pending_name
    if not pending.exists():
        return
    transaction = _read(pending)
    repair_id = transaction.get("repair_id", "")
    if (
        not re.fullmatch(r"[a-f0-9]{32}", repair_id)
        or transaction.get("config_path") != str(config_path)
        or transaction.get("original_approval_path") != str(approval_path)
    ):
        raise BootstrapError("Incomplete template repair belongs to different inputs.")
    archive = directory / ".repairs" / repair_id
    if archive.is_symlink() or archive.parent.is_symlink():
        raise BootstrapError("Refusing a symlink in dependency repair history.")
    targets = {
        "config.json": config_path, "template.json": directory / "template.json",
        "manifest.json": directory / "manifest.json", "cost-ledger.json": directory / "cost-ledger.json",
    }
    originals = {}
    for name, target in targets.items():
        source = archive / "original" / name
        if source.is_symlink() or target.is_symlink():
            raise BootstrapError("Refusing a symlink in dependency repair inputs.")
        content = source.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        if digest != transaction["original_hashes"].get(name):
            raise BootstrapError("Dependency repair archive changed; cannot restore local state.")
        if _file_digest(target) not in {digest, transaction["proposed_hashes"].get(name)}:
            raise BootstrapError("Live local state changed outside the repair; refusing overwrite.")
        originals[name] = content
    for name, target in targets.items():
        _write_bytes(target, originals[name], replace=True)
    os.replace(pending, archive / f"recovered-{uuid4().hex}.transaction.json")


def repair_dependencies(
    config_path: Path | str, approval_path: Path | str, *, max_provisioning_retries: int,
    failed_deployment_path: Path | str | None = None,
    failed_operations_path: Path | str | None = None, run: Run = az_json,
) -> dict:
    """Archive and rebind an additive dependsOn-only repair of a verified failed owned deployment."""
    return _repair_template(
        config_path, approval_path, repair_kind="dependencies", max_provisioning_retries=max_provisioning_retries,
        failed_deployment_path=failed_deployment_path, failed_operations_path=failed_operations_path, run=run,
    )


def repair_trace_routing(
    config_path: Path | str, approval_path: Path | str, *,
    failed_deployment_path: Path | str | None = None,
    failed_operations_path: Path | str | None = None, run: Run = az_json,
) -> dict:
    """Add only the owned-component trace routing reference, preserving the existing two-retry ceiling."""
    return _repair_template(
        config_path, approval_path, repair_kind="trace-routing", max_provisioning_retries=2,
        failed_deployment_path=failed_deployment_path, failed_operations_path=failed_operations_path, run=run,
    )


def _repair_template(
    config_path: Path | str, approval_path: Path | str, *, repair_kind: str, max_provisioning_retries: int,
    failed_deployment_path: Path | str | None, failed_operations_path: Path | str | None, run: Run,
) -> dict:
    if repair_kind not in {"dependencies", "trace-routing"}:
        raise BootstrapError("Unsupported template repair kind.")
    routing = repair_kind == "trace-routing"
    prefix = "TRACE_ROUTING" if routing else "DEPENDENCY"
    history_key = "trace_routing_repairs" if routing else "dependency_repairs"
    pending_name = "trace-routing-repair.pending.json" if routing else "dependency-repair.pending.json"
    change_guard = _trace_routing_only_change if routing else _dependency_only_change
    if type(max_provisioning_retries) is not int or max_provisioning_retries not in {1, 2}:
        raise ApprovalError("Template recovery permits one or two total provisioning retries, never unbounded retries.")
    config_path, approval_path = Path(config_path), Path(approval_path)
    for path in (config_path, approval_path):
        if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
            raise BootstrapError("Repair input paths must not traverse symlinks.")
    config_path, approval_path = config_path.resolve(), approval_path.resolve()
    directory = config_path.parent
    with _lock(directory):
        _recover_dependency_transaction(directory, config_path, approval_path, pending_name=pending_name)
        _, config, manifest = _load(config_path, _pinned_template=True)
        original_template_bytes = (directory / "template.json").read_bytes()
        revised_template_bytes = TEMPLATE.read_bytes()
        old_template, new_template = json.loads(original_template_bytes), json.loads(revised_template_bytes)
        change_guard(old_template, new_template)
        if original_template_bytes == revised_template_bytes:
            repairs = manifest.get(history_key, [])
            if repairs:
                prior = repairs[-1]
                rebound = _approved_record(config, prior["approval_path"])
                original_snapshot = Path(prior["archive_path"]) / "original" / "approval.original.json"
                if (
                    max_provisioning_retries != rebound.get("max_provisioning_retries")
                    or _file_digest(approval_path) not in {
                        _file_digest(Path(prior["approval_path"])), _file_digest(original_snapshot),
                    }
                ):
                    raise ApprovalError("An existing repair cannot silently change its original consent or retry allowance.")
                return {
                    "status": f"{prefix}_REPAIR_ALREADY_APPLIED", "config_path": str(config_path),
                    "approval_path": repairs[-1]["approval_path"], "scope_sha256": config["scope_sha256"],
                    "mutations_performed": False, "retry_required": manifest.get("phase") != "succeeded",
                }
            raise BootstrapError("No matching narrow template revision is available.")
        original_approval = _approved_record(config, approval_path)
        if routing and original_approval.get("max_provisioning_retries", 0) != 2:
            raise ApprovalError("Trace routing repair preserves an already-approved total retry ceiling of two; it cannot grant or reset retries.")
        _check_outputs(directory, manifest)
        if (directory / ".env").exists():
            raise BootstrapError("This repair is only for failed initial provisioning; an existing runtime .env is never overwritten.")
        identity = _identity(config, manifest, run)
        if identity["user"]["id"] != manifest["operator_principal_id"]:
            raise BootstrapError("Repair principal differs from the recorded provisioner.")
        failure_prefix = "retry1" if routing else "first-apply"
        failed_deployment_path = Path(failed_deployment_path or directory / "evidence" / f"{failure_prefix}-failed-deployment.local.json")
        failed_operations_path = Path(failed_operations_path or directory / "evidence" / f"{failure_prefix}-operations.local.json")
        if failed_deployment_path.is_symlink() or failed_operations_path.is_symlink():
            raise BootstrapError("Failure evidence cannot be a symlink.")
        failed = _read(failed_deployment_path)
        try:
            operations = json.loads(failed_operations_path.read_bytes())
        except (OSError, ValueError) as exc:
            raise BootstrapError("Original failed operation evidence is missing or invalid.") from exc
        correlation = failed.get("properties", {}).get("correlationId")
        if not _uuid(correlation):
            raise BootstrapError("Original failure evidence must include its correlation ID.")
        _verify_failed_deployment(config, manifest, failed, correlation)
        rows = operations.get("value", []) if isinstance(operations, dict) else operations
        if not isinstance(rows, list):
            raise BootstrapError("Expected the original ARM operation list.")
        arm_id = manifest["resources"]["arm_deployment"]["id"]
        target_id = manifest["resources"]["insights_connection"]["id"] if routing else _ids(config)["project"]

        def matches_failure(row: dict, *, allow_summary: bool = False) -> bool:
            properties = row.get("properties", {})
            full = (
                str(row.get("id", "")).lower().startswith(arm_id.lower() + "/operations/")
                and properties.get("provisioningState") == "Failed"
                and str(properties.get("targetResource", {}).get("id", "")).lower() == target_id.lower()
            )
            summary = routing and allow_summary and row.get("state") == "Failed" and row.get("resource") == (
                f"{config['names']['account']}/{config['names']['project']}/lab-appinsights"
            )
            if not (full or summary):
                return False
            error = _azure_error(_json(properties.get("statusMessage") if full else row.get("error")), "", [])
            if not routing:
                return error.code == "RequestConflict"
            return (
                error.code == "ValidationError" and TRACE_ROUTING_KEY in error.raw_message
                and "missing" in error.raw_message.lower()
            )

        if not any(matches_failure(row, allow_summary=routing) for row in rows):
            raise BootstrapError("The original operation evidence does not match this narrowly permitted repair.")
        live_operations = None
        if routing:
            live_operations = run([
                "deployment", "operation", "group", "list", "--subscription", config["subscription_id"],
                "--resource-group", config["names"]["resource_group"], "--name", config["deployment_name"],
            ])
            live_rows = live_operations.get("value", []) if isinstance(live_operations, dict) else live_operations
            if not isinstance(live_rows, list) or not any(matches_failure(row) for row in live_rows):
                raise BootstrapError("Live scoped ARM operations do not confirm the same missing routing metadata failure.")
        observed = _inspect(config, manifest, run)
        if "resource_group" not in observed or "account" not in observed or "arm_deployment" not in observed:
            raise BootstrapError("Owned RG/account and original failed deployment must still be observable; unknown outcomes cannot be repaired.")
        _verify_failed_deployment(config, manifest, observed["arm_deployment"], correlation)
        prior_attempts = [item for item in manifest["attempts"] if item.get("phase") == "deploying"]
        if not prior_attempts or max(0, len(prior_attempts) - 1) >= max_provisioning_retries:
            raise ApprovalError("The requested total retry allowance is absent or already exhausted.")

        repair_id = uuid4().hex
        repairs_root = directory / ".repairs"
        if repairs_root.is_symlink():
            raise BootstrapError("Repair history must remain inside this environment.")
        repairs_root.mkdir(exist_ok=True, mode=0o700)
        archive = repairs_root / repair_id
        archive.mkdir(mode=0o700)
        original_dir, proposed_dir = archive / "original", archive / "proposed"
        original_dir.mkdir(mode=0o700)
        proposed_dir.mkdir(mode=0o700)
        (proposed_dir / "evidence").mkdir(mode=0o700)
        original_files = {
            "config.json": config_path.read_bytes(), "template.json": original_template_bytes,
            "manifest.json": (directory / "manifest.json").read_bytes(),
            "approval.original.json": approval_path.read_bytes(),
            "cost-ledger.json": (directory / "cost-ledger.json").read_bytes(),
            "failed-deployment.original.json": failed_deployment_path.read_bytes(),
            "failed-operations.original.json": failed_operations_path.read_bytes(),
        }
        if live_operations is not None:
            original_files["live-operations.snapshot.json"] = _json(live_operations).encode()
        for path in (directory / "evidence").rglob("*"):
            if path.is_symlink():
                raise BootstrapError("Refusing to archive a symlink in failure evidence.")
            if path.is_file():
                original_files["evidence/" + path.relative_to(directory / "evidence").as_posix()] = path.read_bytes()
        for name, content in original_files.items():
            target = original_dir / name
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            _write_bytes(target, content)

        revised = deepcopy(config)
        revised["template_sha256"] = hashlib.sha256(revised_template_bytes).hexdigest()
        revised["scope_sha256"] = _scope(revised)
        _validate(revised)
        if _resources(revised) != _resources(config) or _ids(revised) != _ids(config):
            raise BootstrapError("Narrow repair must not change any resource ID, role, name, SKU, or model.")
        approval = deepcopy(original_approval)
        approval["scope_sha256"] = revised["scope_sha256"]
        approval["max_provisioning_retries"] = max_provisioning_retries
        approval["request_evidence"] = _json({
            "original_request_evidence": original_approval.get("request_evidence", ""),
            "original_approval_sha256": _digest(original_approval),
            "repair_kind": repair_kind,
            "repair_authorization": (
                "Coordinator explicitly authorized only the missing ApplicationInsightsConnectionString metadata reference to the SAME owned component, retaining ProjectManagedIdentity, disabled local auth, and the existing total ceiling of two retries; --retry remains mandatory."
                if routing else
                "Coordinator explicitly authorized additive resource ordering only and up to two same-scope provisioning retries; --retry remains mandatory."
            ),
            "old_scope_sha256": config["scope_sha256"], "new_scope_sha256": revised["scope_sha256"],
            "failed_correlation_id": correlation, "resource_ids_names_skus_roles_processing_unchanged": True,
            "allowed_change": f"metadata.{TRACE_ROUTING_KEY} same-component reference" if routing else "additive dependsOn only",
        })
        validate_approval(revised, approval)
        new_approval_path = directory / f"approval.{repair_kind}-{repair_id[:8]}.local.json"
        revision = {
            "repair_id": repair_id, "recorded_at": _stamp(), "instance_id": config["instance_id"],
            "old_scope_sha256": config["scope_sha256"], "new_scope_sha256": revised["scope_sha256"],
            "old_template_sha256": config["template_sha256"], "new_template_sha256": revised["template_sha256"],
            "archive_path": str(archive), "approval_path": str(new_approval_path),
            "failed_correlation_id": correlation, "repair_kind": repair_kind, "dependsOn_only": not routing,
            "allowed_change": f"metadata.{TRACE_ROUTING_KEY} owned-component reference only" if routing else "additive dependsOn only",
            "max_provisioning_retries": max_provisioning_retries,
        }
        new_manifest = deepcopy(manifest)
        new_manifest.update(
            scope_sha256=revised["scope_sha256"],
            phase="trace_routing_repair_ready" if routing else "dependency_repair_ready", updated_at=_stamp(),
        )
        new_manifest.setdefault(history_key, []).append(revision)
        proposed_files = {
            "config.json": _json(revised).encode(), "template.json": revised_template_bytes,
            "manifest.json": _json(new_manifest).encode(),
            "cost-ledger.json": _json(cost_ledger(new_manifest)).encode(),
        }
        for name, content in proposed_files.items():
            _write_bytes(proposed_dir / name, content)
        _write(proposed_dir / "approval.json", approval)
        _write(archive / "revision.json", {
            **revision, "original_hashes": {name: hashlib.sha256(value).hexdigest() for name, value in original_files.items()},
        })
        validation = _validate_arm(proposed_dir, revised, identity["user"]["id"], run)
        latest = _get(manifest["resources"]["arm_deployment"], run)
        if latest is None:
            raise BootstrapError("Original deployment disappeared during repair; no local revision was installed.")
        _verify_failed_deployment(config, manifest, latest, correlation)
        if TEMPLATE.read_bytes() != revised_template_bytes:
            raise BootstrapError("Candidate template changed during validation; no revision was installed.")
        live_targets = {
            "config.json": config_path, "template.json": directory / "template.json",
            "manifest.json": directory / "manifest.json", "cost-ledger.json": directory / "cost-ledger.json",
        }
        if approval_path.read_bytes() != original_files["approval.original.json"] or any(
            target.read_bytes() != original_files[name] for name, target in live_targets.items()
        ):
            raise BootstrapError("Original local state changed during repair; refusing overwrite.")
        transaction = {
            "repair_id": repair_id, "config_path": str(config_path), "original_approval_path": str(approval_path),
            "original_hashes": {name: hashlib.sha256(original_files[name]).hexdigest() for name in live_targets},
            "proposed_hashes": {name: hashlib.sha256(proposed_files[name]).hexdigest() for name in live_targets},
        }
        pending = directory / pending_name
        _write(pending, transaction)
        try:
            _write(new_approval_path, approval)
            for name, target in live_targets.items():
                _write_bytes(target, proposed_files[name], replace=True)
            os.replace(pending, archive / "completed.transaction.json")
        except BaseException:
            _recover_dependency_transaction(directory, config_path, approval_path, pending_name=pending_name)
            raise
        _load(config_path)
        return {
            "status": f"{prefix}_REPAIR_READY", "config_path": str(config_path),
            "approval_path": str(new_approval_path), "archive_path": str(archive),
            "scope_sha256": revised["scope_sha256"], "instance_id": revised["instance_id"],
            "resource_ids_models_skus_roles_processing_unchanged": True,
            **({"resource_ids_settings_unchanged": True} if not routing else {}),
            "allowed_change": revision["allowed_change"], "max_provisioning_retries": max_provisioning_retries,
            "arm_validation_status": validation["status"], "retry_required": True, "mutations_performed": False,
        }


def _env(config: dict, insights: dict, approval_path: Path | str) -> str:
    ids, names = _ids(config), config["names"]
    models = {role: m["deployment"] for m in config["models"] for role in m["roles"]}
    values = {
        "AZURE_SUBSCRIPTION_ID": config["subscription_id"], "AZURE_TENANT_ID": config["tenant_id"],
        "EXPECTED_AZURE_USER": config["expected_user"], "AZURE_LOCATION": REGION,
        "AZURE_RESOURCE_GROUP": names["resource_group"], "AZURE_AI_ACCOUNT_NAME": names["account"],
        "AZURE_AI_PROJECT_NAME": names["project"], "AZURE_AI_PROJECT_ID": ids["project"],
        "AZURE_AI_PROJECT_ENDPOINT": f"https://{names['account']}.services.ai.azure.com/api/projects/{names['project']}",
        "AZURE_OPENAI_ENDPOINT": f"https://{names['account']}.openai.azure.com",
        "AZURE_SEARCH_SERVICE": names["search"], "AZURE_SEARCH_ENDPOINT": f"https://{names['search']}.search.windows.net",
        "MODEL_DEPLOYMENT": models["agent"], "JUDGE_DEPLOYMENT": models["judge"],
        "OPTIMIZER_DEPLOYMENT": models["optimizer"], "IQ_PLANNER_DEPLOYMENT": models["planner"],
        "EMBEDDING_DEPLOYMENT": models["embedding"], "LAB_PREFIX": config["environment"],
        "LAB_ARTIFACTS_DIR": str(Path(config["environment_dir"]) / "artifacts"),
        "LAB_BOOTSTRAP_CONFIG": str(Path(config["environment_dir"]) / "config.json"),
        "BOOTSTRAP_CONFIG": str(Path(config["environment_dir"]) / "config.json"),
        "LAB_COST_APPROVAL_FILE": str(Path(approval_path).resolve()),
        "APPLICATIONINSIGHTS_RESOURCE_ID": ids["insights"], "LOG_ANALYTICS_WORKSPACE_ID": ids["workspace"],
        "APPLICATIONINSIGHTS_AUTHENTICATION_STRING": "Authorization=AAD",
        "APPLICATIONINSIGHTS_CONNECTION_STRING": insights.get("properties", {}).get("ConnectionString", ""),
    }
    # JSON quoting is compatible with dotenv; no shell script is generated or executed.
    return "".join(f"{key}={json.dumps(value)}\n" for key, value in values.items())


def _check_outputs(directory: Path, manifest: dict) -> None:
    env = directory / ".env"
    if env.is_symlink() or (env.exists() and _file_digest(env) != manifest.get("env_sha256")):
        raise BootstrapError("Existing .env is not this bootstrap's output; refusing to overwrite it.")
    for name in ("artifacts", "evidence"):
        path = directory / name
        if path.is_symlink() or not path.is_dir():
            raise BootstrapError("Environment artifact/evidence directory is missing or unsafe.")


def _pending(directory: Path, manifest: dict, keys: list[str], phase: str, approval: dict) -> None:
    for key in keys:
        if manifest["resources"][key]["status"] == "planned":
            manifest["resources"][key]["status"] = "pending"
    manifest["phase"] = phase
    manifest["attempts"].append({
        "phase": phase, "at": _stamp(), "approval_sha256": _digest(approval),
        "pending_ids": [manifest["resources"][key]["id"] for key in keys],
    })
    _save(directory, manifest)


def apply(
    config_path: Path | str, approval_path: Path | str | None = None, *,
    run: Run = az_json, what_if: bool = False, retry: bool = False,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> dict:
    """Provision only this plan's owned scope. Calling this function can incur cost."""
    directory, config, manifest = _load(config_path)
    if what_if and retry:
        raise BootstrapError("--retry cannot be combined with read-only --what-if.")
    if not what_if:
        approval = _approved_record(config, approval_path)
    else:
        approval = {}
    with _lock(directory):
        directory, config, manifest = _load(config_path)
        _check_outputs(directory, manifest)
        try:
            report, raw, observed = _preflight(config, manifest, run)
        except BootstrapError as exc:
            _record_failure(directory, "pre-apply", exc)
            raise
        _write(directory / "evidence" / f"pre-apply-{uuid4().hex}.local.json", raw)
        if what_if:
            if "resource_group" not in observed:
                raise BootstrapError("Read-only group what-if needs the already-owned group; it never creates a group.")
        elif any(m["deprecated"] for m in report["models"]) and not approval["accept_deprecated_models"]:
            raise ApprovalError("A selected model is deprecating; explicit acceptance or a newly approved plan is required.")
        principal = raw["identity"]["user"]["id"]
        if what_if:
            path = directory / "evidence" / f"what-if-parameters-{uuid4().hex}.local.json"
            _write(path, _parameters(config, principal))
            result = run([
                "deployment", "group", "what-if", "--subscription", config["subscription_id"],
                "--resource-group", config["names"]["resource_group"], "--name", config["deployment_name"],
                "--template-file", str(directory / "template.json"), "--parameters", f"@{path}", "--mode", "Incremental",
                "--no-pretty-print",
            ])
            _write(directory / "evidence" / f"what-if-{uuid4().hex}.local.json", {"result": result})
            return {"status": "WHAT_IF_ONLY", "scope_sha256": config["scope_sha256"], "mutations_performed": False}
        start = clock()
        deadline = start + approval["max_wait_seconds"]

        def bounded(args: list[str]) -> Any:
            try:
                validate_approval(config, approval)
            except BootstrapError as exc:
                raise ApprovalError(str(exc)) from exc
            remaining = deadline - clock()
            if remaining <= 0:
                raise BootstrapError("Approved wait exhausted; inspect status and resume, never delete or recreate blindly.")
            return az_json(args, timeout=min(remaining, 120)) if run is az_json else run(args)

        manifest["operator_principal_id"] = principal
        manifest["approved_currency"] = approval["currency"]
        manifest["approved_budget"] = approval["budget_amount"]
        manifest["approved_budget_policy"] = approval.get("budget_policy", "BOUNDED")
        initial_attempts = len(manifest["attempts"])
        stage = "ownership"
        active_command = None
        submitted_attempt = None
        try:
            if "resource_group" not in observed:
                if manifest["resources"]["resource_group"]["status"] not in {"planned", "pending"}:
                    raise BootstrapError("Previously owned resource group is missing; automatic restore/recreation is forbidden.")
                if manifest["resources"]["resource_group"]["status"] == "pending":
                    raise ProvisioningRetryError(
                        "UNKNOWN_GROUP_SUBMISSION",
                        "A pending resource-group creation intent exists but the group is absent. "
                        "Inspect original submission/activity evidence; do not issue another create blindly.",
                    )
                # Recheck immediately before conditional create; az group create would silently upsert.
                if _get(manifest["resources"]["resource_group"], bounded) is not None:
                    raise BootstrapError("Resource group name collision; no adoption or overwrite.")
                _pending(directory, manifest, ["resource_group"], "creating_group", approval)
                group = manifest["resources"]["resource_group"]
                stage = "group-create"
                active_command = [
                    "rest", "--method", "PUT", "--url", f"{ARM}{group['id']}?api-version={group['api_version']}",
                    "--headers", "If-None-Match=*", "--body", _json({"location": REGION, "tags": _tags(config)}),
                ]
                bounded(active_command)
                remote = _get(group, bounded)
                if remote is None:
                    raise BootstrapError("Group creation is not yet observable; use status before resume.")
                _owned(config, "resource_group", group, remote, manifest, {})
                manifest["resources"]["resource_group"]["status"] = "present"
                _save(directory, manifest)
            observed = _inspect(config, manifest, bounded)
            if "resource_group" not in observed:
                raise BootstrapError("Owned group must exist before any ARM deployment.")
            arm = observed.get("arm_deployment", {}).get("properties", {}).get("provisioningState")
            stage, active_command = "arm-retry-check", None
            if _submission_required(manifest, observed, approval, retry):
                stage = "arm-validation"
                validation = _validate_arm(directory, config, principal, bounded)
                manifest["last_validation"] = validation
                parameter_path = Path(validation["parameters_path"])
                observed = _inspect(config, manifest, bounded)
                if not _submission_required(manifest, observed, approval, retry):
                    raise BootstrapError("Deployment state changed during validation; inspect status instead of issuing another create.")
                _pending(directory, manifest, [k for k in manifest["resources"] if k != "resource_group"], "deploying", approval)
                submitted_attempt = manifest["attempts"][-1]
                submitted_attempt.update(
                    submission_outcome="pending", retry_requested=retry,
                    validation_evidence_file=validation["evidence_file"],
                )
                _save(directory, manifest)
                stage = "arm-create"
                active_command = [
                    "deployment", "group", "create", "--subscription", config["subscription_id"],
                    "--resource-group", config["names"]["resource_group"], "--name", config["deployment_name"],
                    "--template-file", str(directory / "template.json"), "--parameters", f"@{parameter_path}",
                    "--mode", "Incremental", "--no-wait",
                ]
                response = bounded(active_command)
                submitted_attempt["submission_outcome"] = "submitted"
                _save(directory, manifest)
                _write(directory / "evidence" / f"create-{uuid4().hex}.local.json", {
                    "command": active_command, "response": response, "recorded_at": _stamp(),
                    "status": "SUBMITTED_NOT_VERIFIED",
                })
                arm = None
            stage = "arm-status"
            while arm != "Succeeded":
                deployment = _get(manifest["resources"]["arm_deployment"], bounded)
                arm = (deployment or {}).get("properties", {}).get("provisioningState")
                if arm in {"Failed", "Canceled", "Cancelled"}:
                    payload = (deployment or {}).get("properties", {}).get("error")
                    if payload:
                        spec = manifest["resources"]["arm_deployment"]
                        raise _azure_error("", _json(deployment), [
                            "rest", "--method", "GET", "--url",
                            f"{ARM}{spec['id']}?api-version={spec['api_version']}",
                        ])
                    raise AzureCommandError("DeploymentFailed", payload=deployment, message="ARM deployment failed; inspect saved results before an explicitly budgeted retry.")
                if arm != "Succeeded":
                    remaining = deadline - clock()
                    if remaining <= 0:
                        raise BootstrapError("Approved wait exhausted; deployment may still run. Inspect status.")
                    sleep(min(5, remaining))
            observed = _inspect(config, manifest, bounded)
            if set(observed) != set(manifest["resources"]):
                raise BootstrapError("ARM succeeded but the complete owned inventory is not observable; do not claim success.")
            routing = observed["insights_connection"].get("properties", {}).get("metadata", {}).get(TRACE_ROUTING_KEY)
            expected_routing = observed["insights"].get("properties", {}).get("ConnectionString")
            if not expected_routing or routing != expected_routing:
                raise BootstrapError("ARM success is insufficient: trace routing metadata must match the owned component's ConnectionString.")
            for key, remote in observed.items():
                state = remote.get("properties", {}).get("provisioningState")
                if state is not None and str(state).lower() != "succeeded":
                    raise BootstrapError(f"Resource is not ready: {key}.")
                if state is None and (key in RESOURCE_TYPES or key.startswith("model:")):
                    raise BootstrapError(f"Resource readiness is missing: {key}.")
                manifest["resources"][key]["status"] = "succeeded"
            content = _env(config, observed["insights"], approval_path)
            if not (directory / ".env").exists():
                manifest["env_sha256"] = hashlib.sha256(content.encode()).hexdigest()
                manifest["phase"] = "writing_env"
                _save(directory, manifest)
                _write(directory / ".env", content, text=True)
            manifest["env_sha256"] = _file_digest(directory / ".env")
            manifest["phase"] = "succeeded"
            _save(directory, manifest)
            return {
                "status": "APPLIED", "scope_sha256": config["scope_sha256"],
                "env_path": str(directory / ".env"), "artifacts_dir": str(directory / "artifacts"),
                "resource_count": len(observed), "data_plane_verified": False,
                "live_status": "NOT_VERIFIED",
                "server_side_trace_connection": "CONFIGURED_PROJECT_MANAGED_IDENTITY",
                "trace_ingestion_verified": False,
            }
        except BootstrapError as exc:
            if submitted_attempt is not None and submitted_attempt.get("submission_outcome") == "pending":
                submitted_attempt["submission_outcome"] = "unknown"
            evidence_file = _record_failure(directory, stage, exc, command=active_command)
            if submitted_attempt is not None:
                submitted_attempt["failure_evidence_file"] = evidence_file
            manifest.setdefault("failures", []).append({
                "recorded_at": _stamp(), "stage": stage, "error_code": getattr(exc, "code", None),
                "evidence_file": evidence_file,
            })
            if isinstance(exc, ApprovalError) and len(manifest["attempts"]) > initial_attempts:
                exc.mutations_performed = None
            manifest["phase"] = "interrupted"
            manifest["last_error"] = str(exc)
            manifest["last_error_code"] = getattr(exc, "code", None)
            manifest["last_error_evidence_file"] = evidence_file
            if getattr(exc, "validation_evidence_file", None):
                manifest["last_validation"] = {"status": "FAILED", "evidence_file": exc.validation_evidence_file}
            _save(directory, manifest)
            raise


def status(
    config_path: Path | str, *, run: Run = az_json, approval_path: Path | str | None = None,
) -> dict:
    """Inspect only declared resources; no deletes, provider registration, or permission repair."""
    directory, config, manifest = _load(config_path)
    _identity(config, manifest, run)
    try:
        observed = _inspect(config, manifest, run)
    except BootstrapError as exc:
        return {"status": "BLOCKED", "scope_sha256": config["scope_sha256"], "reason": str(exc)}
    result = {
        **_authorization(config, approval_path),
        "observation_status": "OBSERVED", "live_status": "NOT_VERIFIED",
        "scope_sha256": config["scope_sha256"], "phase": manifest["phase"],
        "resources": {key: {
            "present": key in observed,
            "provisioning_state": observed.get(key, {}).get("properties", {}).get("provisioningState", "UNKNOWN"),
            "recorded_state": spec["status"], "sku": spec["sku"],
        } for key, spec in manifest["resources"].items()},
        "mutations_performed": False,
        "warning": "Search and any separately deployed fine-tuned model may still incur continuous hosting costs.",
    }
    if result["approval_status"] == "APPROVED":
        result["status"] = "OBSERVED_APPROVAL_VALID"
        result["live_status"] = "PENDING_EXECUTION"
    result["readiness_status"] = "NOT_CHECKED_BY_STATUS"
    _write(directory / "evidence" / f"status-{uuid4().hex}.local.json", {"observed": observed, "summary": result})
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("plan", help="Local, SDK-free plan; no Azure calls")
    create.add_argument("--subscription", required=True)
    create.add_argument("--tenant", required=True)
    create.add_argument("--expected-user", required=True)
    create.add_argument("--environment")
    create.add_argument("--resource-group", help="Explicit unused lab RG name; does not permit adopting a group")
    create.add_argument("--agent-sku", choices=["Standard", "GlobalStandard"], help="Explicit base-agent deployment SKU; no automatic fallback")
    create.add_argument("--root", type=Path, default=Path(".lab"))
    create.add_argument("--location", default=REGION, choices=[REGION])
    create.add_argument("--retention-days", type=int, default=30)
    create.add_argument("--models-json", type=Path, help="JSON object with an explicit models array")
    for command in ("preflight", "apply", "status"):
        sub = commands.add_parser(command)
        sub.add_argument("--config", type=Path, required=True)
        sub.add_argument("--approval", type=Path)
        if command == "apply":
            sub.add_argument("--what-if", action="store_true")
            sub.add_argument("--retry", action="store_true", help="Retry a verified terminal owned failure only within an explicit approval retry allowance")
    group_prepare = commands.add_parser("prepare-group", help="Read-only checks + local intent before external RG-only creation")
    group_prepare.add_argument("--config", type=Path, required=True)
    group_prepare.add_argument("--authorization", type=Path, required=True)
    group_confirm = commands.add_parser("confirm-group", help="Read-only confirmation of the pre-recorded external RG creation")
    group_confirm.add_argument("--config", type=Path, required=True)
    group_bind = commands.add_parser("bind-group", help="Read-only verification of coordinator-created empty RG receipts")
    group_bind.add_argument("--config", type=Path, required=True)
    group_bind.add_argument("--intent", type=Path, required=True)
    group_bind.add_argument("--created", type=Path, required=True)
    repair = commands.add_parser("repair-dependencies", help="Archive and locally rebind a verified dependsOn-only recovery; never writes Azure")
    repair.add_argument("--config", type=Path, required=True)
    repair.add_argument("--approval", type=Path, required=True)
    repair.add_argument("--max-provisioning-retries", type=int, choices=[1, 2], required=True)
    repair.add_argument("--failed-deployment", type=Path)
    repair.add_argument("--failed-operations", type=Path)
    trace_repair = commands.add_parser("repair-trace-routing", help="Archive and rebind ONLY the owned App Insights routing metadata; never writes Azure or resets retry budget")
    trace_repair.add_argument("--config", type=Path, required=True)
    trace_repair.add_argument("--approval", type=Path, required=True)
    trace_repair.add_argument("--failed-deployment", type=Path)
    trace_repair.add_argument("--failed-operations", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "plan":
            result = plan(
                subscription_id=args.subscription, tenant_id=args.tenant, expected_user=args.expected_user,
                environment=args.environment, root=args.root, location=args.location,
                resource_group=args.resource_group,
                agent_sku=args.agent_sku,
                retention_days=args.retention_days,
                models=_read(args.models_json).get("models") if args.models_json else None,
            )
        elif args.command == "apply":
            result = apply(args.config, args.approval, what_if=args.what_if, retry=args.retry)
        elif args.command == "prepare-group":
            result = prepare_group_creation(args.config, args.authorization)
        elif args.command == "confirm-group":
            result = confirm_group_creation(args.config)
        elif args.command == "bind-group":
            result = bind_created_group(args.config, args.intent, args.created)
        elif args.command == "repair-dependencies":
            result = repair_dependencies(
                args.config, args.approval, max_provisioning_retries=args.max_provisioning_retries,
                failed_deployment_path=args.failed_deployment, failed_operations_path=args.failed_operations,
            )
        elif args.command == "repair-trace-routing":
            result = repair_trace_routing(
                args.config, args.approval, failed_deployment_path=args.failed_deployment,
                failed_operations_path=args.failed_operations,
            )
        else:
            result = {"preflight": preflight, "status": status}[args.command](args.config, approval_path=args.approval)
        print(_json(result), end="")
        return 2 if result["status"].startswith("BLOCKED") and args.command not in {"plan", "prepare-group", "confirm-group"} else 0
    except ApprovalError as exc:
        print(_json({
            "status": AWAITING_APPROVAL, "reason": str(exc),
            "live_status": "NOT_VERIFIED", "mutations_performed": exc.mutations_performed,
        }), end="")
        return 2
    except (AzureCommandError, ProvisioningRetryError) as exc:
        print(_json({
            "status": "BLOCKED", "error_code": exc.code, "reason": str(exc),
            "live_status": "NOT_VERIFIED", "mutations_performed": None,
        }), end="")
        return 2
    except (BootstrapError, OSError) as exc:
        print(f"Bootstrap blocked: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
