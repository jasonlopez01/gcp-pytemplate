"""Logging configuration using structlog.

Renders human-readable colored output locally and structured JSON in all other
environments so that Google Cloud Logging can parse severity and fields correctly.

Usage:
    from example_cli_job.config.logging_config import configure_logging, get_logger
    configure_logging(log_level="INFO", app_env="local")
    logger = get_logger(__name__)
    logger.info("started", app="my-app")
"""

import logging

import structlog


def configure_logging(log_level: str, app_env: str) -> None:
    """Configure structlog. Call once at application startup."""

    shared_processors: list = [
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.contextvars.merge_contextvars,
    ]

    if app_env == "local":
        renderer = structlog.dev.ConsoleRenderer()
    else:
        # GCP Cloud Logging parses 'severity' for log level — rename before rendering
        shared_processors.append(_rename_level_to_severity)
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    return structlog.get_logger(name)


def _rename_level_to_severity(
    logger: object, method: str, event_dict: structlog.types.EventDict
) -> structlog.types.EventDict:
    event_dict["severity"] = event_dict.pop("level", method).upper()
    return event_dict