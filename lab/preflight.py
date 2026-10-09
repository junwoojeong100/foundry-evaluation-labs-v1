"""Read-only management-plane checks. A pass is not a paid inference test."""

from datetime import datetime, timezone
import json
import math
from pathlib import Path
import subprocess
from typing import Callable
from urllib.parse import quote

from lab import azcli
from lab.config import Config, LabError
from lab.content import text


LAB_MINIMUM_TPM = {
    "agent": 100_000,
    "judge": 100_000,
    "optimizer": 100_000,
    "iq_planner": 100_000,
    "embedding": 10_000,
}


def _tokens_per_minute(rate_limits: object) -> float:
    if not isinstance(rate_limits, list) or any(not isinstance(limit, dict) for limit in rate_limits):
        raise ValueError("Deployment rateLimits must be a list of named limits.")
    token_limits = [limit for limit in rate_limits if limit.get("key") == "token"]
    if not token_limits:
        raise ValueError("No named token limit; TPM cannot be inferred from SKU capacity or request limits.")
    values = []
    for limit in token_limits:
        count, period = limit.get("count"), limit.get("renewalPeriod")
        if (
            type(count) not in (int, float) or type(period) not in (int, float)
            or count < 0 or period <= 0
        ):
            raise ValueError("Token limit count/renewalPeriod is missing or invalid.")
        try:
            finite = math.isfinite(count) and math.isfinite(period)
            value = count * 60 / period
        except OverflowError as exc:
            raise ValueError("Token limit is outside the supported numeric range.") from exc
        if not finite or not math.isfinite(value):
            raise ValueError("Token limit cannot be normalized to a finite TPM value.")
        values.append(value)
    return min(values)


def az_json(args: list[str]) -> object:
    try:
        result = azcli.run([*args, "--only-show-errors", "--output", "json"], timeout=90)
    except FileNotFoundError as exc:
        raise LabError(text(
            "Azure CLI(az)가 없습니다. 가이드 01의 설치 절차를 먼저 진행해야 합니다.",
            "Azure CLI (az) was not found. Complete the installation steps in guide 01 first.",
        )) from exc
    except azcli.AzureCliLaunchError as exc:
        raise LabError(text(
            "이 Azure CLI는 Windows 배치 파일로 시작되어 & | 따옴표 같은 특수 문자를 안전하게 전달할 수 없습니다. "
            "Microsoft 설치 관리자(WinGet 또는 MSI)로 Azure CLI를 다시 설치하거나 GitHub Codespaces 또는 WSL2에서 실행해야 합니다.",
            str(exc),
        )) from exc
    except subprocess.TimeoutExpired as exc:
        raise LabError(text(
            "Azure CLI 조회가 90초를 초과했습니다. 네트워크와 로그인을 확인해야 합니다.",
            "The Azure CLI query exceeded 90 seconds. Check your network connection and sign-in.",
        )) from exc
    if result.returncode:
        raise LabError(text("Azure CLI 조회 실패: ", "Azure CLI query failed: ") + result.stderr.strip())
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise LabError(text(
            "Azure CLI 응답이 JSON이 아닙니다. az 버전과 로그인을 확인해야 합니다.",
            "The Azure CLI response is not JSON. Check your az version and sign-in.",
        )) from exc


def check_identity(config: Config, run: Callable = az_json) -> dict:
    account = run(["account", "show", "--subscription", config.subscription_id])
    if not isinstance(account, dict):
        raise LabError(text(
            "az account show 응답 형식이 올바르지 않습니다.",
            "The az account show response has an unexpected format.",
        ))
    actual_user = account.get("user", {}).get("name", "")
    checks = {
        "subscription": account.get("id") == config.subscription_id,
        "tenant": account.get("tenantId") == config.tenant_id,
        "user": actual_user.lower() == config.expected_user.lower(),
        "enabled": account.get("state") == "Enabled",
    }
    if not all(checks.values()):
        failed = ", ".join(key for key, ok in checks.items() if not ok)
        raise LabError(text(
            f"로그인 환경 불일치({failed}). 작업을 중단했습니다. "
            f"az login --tenant {config.tenant_id} 후 지정 계정으로 로그인해야 합니다. "
            "SDK는 다른 환경 자격 증명으로 자동 전환하지 않습니다.",
            f"The sign-in environment does not match ({failed}). Work stopped. "
            f"Run az login --tenant {config.tenant_id} and sign in with the designated account. "
            "The SDK never switches to another environment's credentials automatically.",
            language=config.language,
        ))
    return {"user": actual_user, "subscription": account["id"], "tenant": account["tenantId"]}


def run_preflight(config: Config, *, run: Callable = az_json) -> dict:
    identity = check_identity(config, run)
    account = run([
        "cognitiveservices", "account", "show", "--subscription", config.subscription_id,
        "--resource-group", config.resource_group, "--name", config.account,
    ])
    project = run([
        "resource", "show", "--ids", config.project_id, "--api-version", "2025-06-01",
    ])
    search = run([
        "search", "service", "show", "--subscription", config.subscription_id,
        "--resource-group", config.resource_group, "--name", config.search_service,
    ])
    deployments = run([
        "cognitiveservices", "account", "deployment", "list",
        "--subscription", config.subscription_id, "--resource-group", config.resource_group,
        "--name", config.account,
    ])
    checks: list[dict] = []
    for name, resource in (("foundry", account), ("project", project), ("search", search)):
        region = str(resource.get("location", "")).lower().replace(" ", "")
        checks.append({
            "name": f"{name}_region",
            "status": "PASS" if region == config.location else "BLOCKED",
            "observed": region,
            "expected": config.location,
        })
    endpoint = project.get("properties", {}).get("endpoints", {}).get("AI Foundry API")
    checks.append({
        "name": "project_endpoint",
        "status": "PASS" if endpoint == config.project_endpoint else "BLOCKED",
        "observed": endpoint,
    })
    deployment_map = {d["name"]: d for d in deployments}
    model_evidence = {}
    roles = (
        ("agent", config.model), ("judge", config.judge), ("optimizer", config.optimizer),
        ("iq_planner", config.planner), ("embedding", config.embedding),
    )
    rate_limit_sources = {}
    for name in dict.fromkeys(name for _, name in roles):
        deployment = deployment_map.get(name)
        if not deployment:
            continue
        limits = deployment.get("properties", {}).get("rateLimits")
        source = "Azure CLI deployment metadata"
        if not isinstance(limits, list) or not any(
            isinstance(limit, dict) and limit.get("key") == "token" for limit in limits
        ):
            # Use raw ARM when CLI metadata lacks token/request labels instead of inferring TPM.
            identifier = f"{config.account_id}/deployments/{quote(name, safe='')}"
            deployment = run([
                "rest", "--method", "GET", "--url",
                f"https://management.azure.com{identifier}?api-version=2025-06-01",
            ])
            if (
                not isinstance(deployment, dict) or deployment.get("name") != name
                or str(deployment.get("id", "")).lower() != identifier.lower()
                or not isinstance(deployment.get("properties"), dict)
            ):
                raise LabError(text(
                    "TPM 조회 응답이 요청한 모델 배포와 다릅니다.",
                    "The TPM lookup response does not match the requested model deployment.",
                ))
            deployment_map[name] = deployment
            source = "Raw ARM deployment metadata"
        rate_limit_sources[name] = source
    for role, name in roles:
        deployment = deployment_map.get(name)
        ready = deployment and deployment.get("properties", {}).get("provisioningState") == "Succeeded"
        checks.append({
            "name": f"{role}_deployment", "status": "PASS" if ready else "BLOCKED",
            "observed": name,
        })
        if deployment:
            limits = deployment.get("properties", {}).get("rateLimits")
            minimum_tpm = LAB_MINIMUM_TPM[role]
            try:
                observed_tpm = _tokens_per_minute(limits)
                sufficient = observed_tpm >= minimum_tpm
                reason = (
                    "Meets the lab starting TPM requirement; RPM and shared load still apply."
                    if sufficient else
                    f"Allocate at least {minimum_tpm:,} TPM with operator approval, then rerun preflight."
                )
            except ValueError as exc:
                observed_tpm, sufficient, reason = None, False, str(exc)
            checks.append({
                "name": f"{role}_tpm", "status": "PASS" if sufficient else "BLOCKED",
                "observed": observed_tpm, "expected": minimum_tpm, "reason": reason,
            })
            model_evidence[role] = {
                "deployment": name,
                "model": deployment.get("properties", {}).get("model"),
                "sku": deployment.get("sku"),
                "tokens_per_minute": observed_tpm,
                "rate_limit_source": rate_limit_sources[name],
            }
        if role == "iq_planner":
            observed_model = (deployment or {}).get("properties", {}).get("model", {}).get("name")
            checks.append({
                "name": "iq_planner_supported_model",
                "status": "PASS" if observed_model == "gpt-5.5" else "BLOCKED",
                "observed": observed_model,
                "expected": "gpt-5.5",
            })
        if role == "embedding":
            observed_model = (deployment or {}).get("properties", {}).get("model", {}).get("name")
            checks.append({
                "name": "embedding_supported_model",
                "status": "PASS" if observed_model == "text-embedding-3-small" else "BLOCKED",
                "observed": observed_model, "expected": "text-embedding-3-small",
            })
    public_access = account.get("properties", {}).get("publicNetworkAccess")
    if public_access == "Disabled":
        checks.append({
            "name": "network", "status": "BLOCKED",
            "observed": text(
                "PublicNetworkAccess=Disabled: 승인된 VNet 연결 환경에서 실행해야 합니다.",
                "PublicNetworkAccess=Disabled: run from an approved VNet-connected environment.",
            ),
        })
    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "kind": "read-only-management-preflight",
        "status": "PASS" if all(c["status"] == "PASS" for c in checks) else "BLOCKED",
        "identity": identity,
        "checks": checks,
        "models": model_evidence,
        "identities": {
            "foundry_project_managed_identity": project.get("identity", {}).get("principalId"),
            "search_managed_identity": search.get("identity", {}).get("principalId"),
        },
        "not_verified": [
            text("데이터 평면 RBAC와 모델 추론 성공", "Data-plane RBAC and successful model inference"),
            text("Foundry IQ 지식 베이스 생성·검색 권한", "Foundry IQ knowledge-base creation and retrieval permissions"),
            text(
                "Prompt Optimizer 및 Frontier Tuning 테넌트 접근 권한",
                "Tenant access to Prompt Optimizer and Frontier Tuning",
            ),
            text(
                "GlobalStandard는 North Central US 내부 처리를 보장하지 않습니다.",
                "GlobalStandard does not guarantee processing inside North Central US.",
            ),
            text(
                "TPM 충족은 남은 토큰, 공유 부하, RPM·버스트 제한 또는 429 없는 실행을 보장하지 않습니다.",
                "Meeting the TPM minimum does not guarantee remaining tokens, absence of shared load, "
                "RPM or burst limits, or a run without 429 errors.",
            ),
        ],
    }


def save_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def model_snapshot(config: Config, deployment_name: str, *, run: Callable = az_json) -> dict:
    value = run([
        "cognitiveservices", "account", "deployment", "show",
        "--subscription", config.subscription_id, "--resource-group", config.resource_group,
        "--name", config.account, "--deployment-name", deployment_name,
    ])
    if not isinstance(value, dict):
        raise LabError(text(
            "모델 배포 메타데이터가 JSON 객체가 아닙니다.", "The model deployment metadata is not a JSON object.",
        ))
    properties = value.get("properties", {})
    model = properties.get("model", {})
    if properties.get("provisioningState") != "Succeeded" or not model.get("name") or not model.get("version"):
        raise LabError(text(
            "준비된 모델의 실제 이름/버전을 확인하지 못했습니다.",
            "Could not confirm the actual name and version of the prepared model.",
        ))
    if value.get("name") != deployment_name:
        raise LabError(text(
            "조회된 모델 배포 이름이 요청과 다릅니다.", "The returned model deployment name differs from the request.",
        ))
    return {
        "deployment": deployment_name,
        "model": model,
        "sku": value.get("sku"),
        "version_upgrade_option": properties.get("versionUpgradeOption"),
        "observation": "Read-only management-plane snapshot, not runtime attestation.",
    }
