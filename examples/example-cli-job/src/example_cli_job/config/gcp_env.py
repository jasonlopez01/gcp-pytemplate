"""File to load in deployed environment values"""

import os
import urllib.request
from functools import lru_cache

from pydantic import BaseModel, ConfigDict, Field

DEAULT_STR_VALUE = "not-set"

GCP_METADATA_BASE = "http://metadata.google.internal/computeMetadata/v1"
GCP_METADATA_HEADERS = {"Metadata-Flavor": "Google"}
GCP_METADATA_TIMEOUT = 5


def _fetch_metadata(path: str) -> str:
    req = urllib.request.Request(f"{GCP_METADATA_BASE}/{path}", headers=GCP_METADATA_HEADERS)
    with urllib.request.urlopen(req, timeout=GCP_METADATA_TIMEOUT) as resp:
        return resp.read().decode("utf-8")


class DeployedEnvData(BaseModel):
    """Class with deployed envrionment data"""

    model_config = ConfigDict(str_strip_whitespace=True)

    IS_DEPLOYED: bool = Field(description="True if in a deployed environment (not local)", default=False)

    GCP_PROJECT: str = Field(description="GCP Project from env", default=DEAULT_STR_VALUE)
    GCP_REGION: str = Field(description="GCP Region from env", default=DEAULT_STR_VALUE)
    SERVICE_ID: str = Field(description="Service ID from env", default=DEAULT_STR_VALUE)
    SERVICE_VERSION: str = Field(description="Service version from env", default=DEAULT_STR_VALUE)
    SERVICE_ACCOUNT_EMAIL: str = Field(description="Serivce Accountfrom env", default=DEAULT_STR_VALUE)


@lru_cache
def load_deployed_env_data() -> DeployedEnvData:
    """Load deployed GCP envrionment data, from env vars and fetched from metadata server."""

    # Determine deployed GCP env values. Accoutning for GKE, Cloud Run, Cloud Functions, and App Engine environments.
    service_id = os.environ.get("K_SERVICE") or os.environ.get("GAE_SERVICE") or os.environ.get("FUNCTION_NAME")
    service_version = (
        os.environ.get("K_REVISION") or os.environ.get("GAE_VERSION") or os.environ.get("X_GOOGLE_FUNCTION_VERSION")
    )

    # If service ID is present, consider deployed env and load other values
    if not service_id:
        return DeployedEnvData(IS_DEPLOYED=False)

    return DeployedEnvData(
        IS_DEPLOYED=True,
        SERVICE_ID=service_id,
        SERVICE_VERSION=service_version,
        GCP_PROJECT=_fetch_metadata("project/project-id"),
        GCP_REGION=_fetch_metadata("instance/region"),
        SERVICE_ACCOUNT_EMAIL=_fetch_metadata("instance/service-accounts/default/email"),
    )


# Load in GCP env data if deployed and export values as env variables
GCP_ENV_DATA = load_deployed_env_data()

os.environ.update({k: str(v) for k, v in GCP_ENV_DATA.model_dump(exclude_none=True).items()})