"""Explicit, tenant-bound configuration; no ambient credential fallback."""

from dataclasses import dataclass
from pathlib import Path
import re
from uuid import UUID

from dotenv import dotenv_values


class LabError(Exception):
    """An actionable workshop error that is safe to show on the CLI."""


@dataclass(frozen=True)
class Config:
    subscription_id: str
    tenant_id: str
    expected_user: str
    location: str
    resource_group: str
    account: str
    project: str
    project_endpoint: str
    openai_endpoint: str
    search_service: str
    search_endpoint: str
    model: str
    judge: str
    optimizer: str
    prefix: str
    planner: str = ""
    tuned_model: str = ""

    @property
    def account_id(self) -> str:
        return (
            f"/subscriptions/{self.subscription_id}/resourceGroups/"
            f"{self.resource_group}/providers/Microsoft.CognitiveServices/"
            f"accounts/{self.account}"
        )

    @property
    def project_id(self) -> str:
        return f"{self.account_id}/projects/{self.project}"

    @property
    def search_id(self) -> str:
        return (
            f"/subscriptions/{self.subscription_id}/resourceGroups/"
            f"{self.resource_group}/providers/Microsoft.Search/"
            f"searchServices/{self.search_service}"
        )

    def agent_name(self, stage: str) -> str:
        if stage not in {"baseline", "iq", "optimized", "tuned"}:
            raise LabError(f"지원하지 않는 단계: {stage}")
        return f"{self.prefix}-{stage}"

    def validate(self) -> None:
        for name, value in (
            ("AZURE_SUBSCRIPTION_ID", self.subscription_id),
            ("AZURE_TENANT_ID", self.tenant_id),
        ):
            try:
                UUID(value)
            except ValueError as exc:
                raise LabError(f"{name}은 UUID여야 합니다.") from exc
        if self.location != "northcentralus":
            raise LabError("이 실습은 northcentralus 전용입니다. 리전을 자동 변경하지 않습니다.")
        if "@" not in self.expected_user or any(c.isspace() for c in self.expected_user):
            raise LabError("EXPECTED_AZURE_USER에 실습용 로그인 계정을 지정하세요.")
        if not re.fullmatch(r"[a-z][a-z0-9-]{2,23}", self.prefix):
            raise LabError("LAB_PREFIX: 소문자로 시작하는 3~24자의 소문자·숫자·하이픈.")
        for name, value in (
            ("account", self.account),
            ("project", self.project),
            ("search_service", self.search_service),
            ("resource_group", self.resource_group),
        ):
            if not re.fullmatch(r"[A-Za-z0-9_.()-]+", value):
                raise LabError(f"{name}에 지원하지 않는 문자가 있습니다.")
        expected_endpoints = {
            "AZURE_AI_PROJECT_ENDPOINT": (
                self.project_endpoint,
                f"https://{self.account}.services.ai.azure.com/api/projects/{self.project}",
            ),
            "AZURE_OPENAI_ENDPOINT": (
                self.openai_endpoint,
                f"https://{self.account}.openai.azure.com",
            ),
            "AZURE_SEARCH_ENDPOINT": (
                self.search_endpoint,
                f"https://{self.search_service}.search.windows.net",
            ),
        }
        for name, (actual, expected) in expected_endpoints.items():
            if actual.rstrip("/") != expected:
                raise LabError(f"{name}이 지정된 리소스와 다릅니다. 예상: {expected}")
        for name, value in (("model", self.model), ("judge", self.judge), ("optimizer", self.optimizer), ("planner", self.planner)):
            if not re.fullmatch(r"[A-Za-z0-9_.-]+", value):
                raise LabError(f"{name}에 실제 모델 배포 이름을 지정하세요.")


def load_config(path: Path) -> Config:
    if not path.is_file():
        raise LabError(f"설정 파일이 없습니다: {path}. 먼저 cp .env.example .env 를 실행하세요.")
    values = dotenv_values(path, interpolate=False)
    names = {
        "subscription_id": "AZURE_SUBSCRIPTION_ID",
        "tenant_id": "AZURE_TENANT_ID",
        "expected_user": "EXPECTED_AZURE_USER",
        "location": "AZURE_LOCATION",
        "resource_group": "AZURE_RESOURCE_GROUP",
        "account": "AZURE_AI_ACCOUNT_NAME",
        "project": "AZURE_AI_PROJECT_NAME",
        "project_endpoint": "AZURE_AI_PROJECT_ENDPOINT",
        "openai_endpoint": "AZURE_OPENAI_ENDPOINT",
        "search_service": "AZURE_SEARCH_SERVICE",
        "search_endpoint": "AZURE_SEARCH_ENDPOINT",
        "model": "MODEL_DEPLOYMENT",
        "judge": "JUDGE_DEPLOYMENT",
        "optimizer": "OPTIMIZER_DEPLOYMENT",
        "prefix": "LAB_PREFIX",
        "planner": "IQ_PLANNER_DEPLOYMENT",
    }
    missing = [env for env in names.values() if not values.get(env)]
    if missing:
        raise LabError("설정값 누락: " + ", ".join(missing))
    kwargs = {field: str(values[env]).strip() for field, env in names.items()}
    config = Config(
        **kwargs,
        tuned_model=(values.get("TUNED_MODEL_DEPLOYMENT") or "").strip(),
    )
    config.validate()
    return config
