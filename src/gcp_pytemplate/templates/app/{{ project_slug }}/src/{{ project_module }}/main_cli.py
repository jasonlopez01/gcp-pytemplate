from {{ project_module }}.cli.commands import app
from {{ project_module }}.config.app_config import APP_CONFIG
from {{ project_module }}.config.logging_config import configure_logging, get_logger


def main() -> None:
    configure_logging(APP_CONFIG.LOG_LEVEL, APP_CONFIG.APP_ENV, service=APP_CONFIG.APP_NAME)
    logger = get_logger(__name__)
    logger.info("starting", log_level=APP_CONFIG.LOG_LEVEL)
    app()


if __name__ == "__main__":
    main()
