"""Runtime app configuration — constants and settings loaded from a .env file in config/app_envs/.

Set the APP_CONFIG_FILE environment variable to the filename of the env file to load, e.g.:
    export APP_CONFIG_FILE=local.env  # resolved from config/app_configs/

For deployment configuration (Cloud Run, Cloud Batch, etc.), see config/deploy_configs/ and scripts/.
"""

import os
from enum import StrEnum
from typing import Annotated

from pydantic import Field, StringConstraints
from pydantic_settings import BaseSettings, SettingsConfigDict

CONFIG_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


class LogLevel(StrEnum):
    """Log level options"""

    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"


class AppConfigModel(BaseSettings):
    """Runtime app configuration — values loaded from a .env file at startup."""

    model_config = SettingsConfigDict(
        str_strip_whitespace=True, extra="ignore", env_file_encoding="utf-8"
    )

    # App
    APP_NAME: str = Field(description="Application name.")
    APP_ENV: Annotated[str, StringConstraints(to_lower=True)] = Field(description="Application environment (ex. `prod`, `dev`, `local`, etc.).")
    HEALTH_CHECK_ROUTE: str = Field(description="API route to use as health check.", default="/healthcheck")
    LOG_LEVEL: LogLevel = Field(default=LogLevel.INFO)

    # Can add other project-specific runtime constants below


# Load app config from a .env file in config/app_envs/, specified by filename via APP_CONFIG_FILE.
if "APP_CONFIG_FILE" not in os.environ:
    raise FileNotFoundError(
        "Missing environment variable APP_CONFIG_FILE. Set it to a filename in config/app_configs/, e.g. export APP_CONFIG_FILE=local.env"
    )

APP_CONFIG_FILE = os.path.join(CONFIG_ROOT_DIR, "app_configs", os.environ["APP_CONFIG_FILE"])

if not os.path.isfile(APP_CONFIG_FILE):
    raise FileNotFoundError(f"App config file was not found at {APP_CONFIG_FILE}")


# Create app config model instance so it can be imported and referenced from the app logic
APP_CONFIG = AppConfigModel(_env_file=APP_CONFIG_FILE)
