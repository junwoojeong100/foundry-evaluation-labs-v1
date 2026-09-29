"""Use only the verified Azure CLI identity for this interactive workshop."""

from pathlib import Path

from azure.identity import AzureCliCredential

from lab.config import Config, LabError
from lab.preflight import check_identity


def credential_for(config: Config) -> AzureCliCredential:
    check_identity(config)
    # Azure CLI rejects get-access-token when both tenant and subscription are
    # supplied. The identity check above binds the subscription to the tenant.
    return AzureCliCredential(subscription=config.subscription_id, process_timeout=30)


def require_owned_scope(config: Config) -> dict:
    if not config.bootstrap_config:
        raise LabError("BOOTSTRAP_CONFIG가 없습니다. 새 실습 RG의 완료된 bootstrap 소유 기록이 필요합니다.")
    from lab.bootstrap import BootstrapError, require_owned_resources

    try:
        return require_owned_resources(Path(config.bootstrap_config), config.account_id)
    except BootstrapError as exc:
        raise LabError(f"신규 실습 자원 소유권 확인 실패: {exc}") from exc
