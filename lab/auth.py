"""Use only the verified Azure CLI identity for this interactive workshop."""

from azure.identity import AzureCliCredential

from lab.config import Config
from lab.preflight import check_identity


def credential_for(config: Config) -> AzureCliCredential:
    check_identity(config)
    # Azure CLI rejects get-access-token when both tenant and subscription are
    # supplied. The identity check above binds the subscription to the tenant.
    return AzureCliCredential(subscription=config.subscription_id, process_timeout=30)

