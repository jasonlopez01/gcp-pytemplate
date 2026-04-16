from example_cli_job.cli.commands import app
from example_cli_job.config.app_config import APP_CONFIG
from example_cli_job.config.logging_config import configure_logging, get_logger


def main() -> None:
    configure_logging(APP_CONFIG.LOG_LEVEL, APP_CONFIG.APP_ENV)
    logger = get_logger(__name__)
    logger.info(f"starting; service={APP_CONFIG.APP_NAME}; env={APP_CONFIG.APP_ENV}; log_level={APP_CONFIG.LOG_LEVEL}")
    app()


if __name__ == "__main__":
    main()