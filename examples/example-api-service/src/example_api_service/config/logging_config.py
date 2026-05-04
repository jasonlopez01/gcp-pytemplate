"""Logging configuration using structlog.

Renders human-readable colored output locally and structured JSON in all other
environments so that Google Cloud Logging can parse severity and fields correctly.

Usage:
    from example_api_service.config.logging_config import configure_logging, get_logger
    configure_logging(log_level="INFO", app_env="local")
    logger = get_logger(__name__)
    logger.info("started", app="my-app")
"""

import logging
import sys

import structlog


def configure_logging(log_level: str, app_env: str) -> None:
    """Configure structlog and stdlib logging bridge. Call once at application startup."""
    log_level_int = logging.getLevelName(log_level.upper())

    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if app_env == "local":
        renderer = structlog.dev.ConsoleRenderer()
        structlog.configure(
            processors=shared_processors + [renderer],
            wrapper_class=structlog.make_filtering_bound_logger(log_level_int),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                foreign_pre_chain=list(shared_processors),
                processors=[structlog.stdlib.ProcessorFormatter.remove_processors_meta, renderer],
            )
        )
    else:
        # add_logger_name requires a stdlib-backed logger — only valid with LoggerFactory, not PrintLoggerFactory
        shared_processors.insert(1, structlog.stdlib.add_logger_name)
        # GCP Cloud Logging parses 'severity' for log level — rename before rendering
        shared_processors.append(_rename_level_to_severity)
        renderer = structlog.processors.JSONRenderer()
        structlog.configure(
            processors=list(shared_processors) + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
            wrapper_class=structlog.make_filtering_bound_logger(log_level_int),
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                foreign_pre_chain=list(shared_processors),
                processors=[structlog.stdlib.ProcessorFormatter.remove_processors_meta, renderer],
            )
        )

    _configure_stdlib_handler(handler, log_level_int)


def _configure_stdlib_handler(handler: logging.Handler, log_level_int: int) -> None:
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(log_level_int)
    logging.getLogger("uvicorn.access").propagate = False  # replaced by request logging middleware


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    return structlog.get_logger(name)


def _rename_level_to_severity(
    logger: object, method: str, event_dict: structlog.types.EventDict
) -> structlog.types.EventDict:
    event_dict["severity"] = event_dict.pop("level", method).upper()
    return event_dict
