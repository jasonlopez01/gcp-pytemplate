"""Logging configuration using structlog.

Renders human-readable colored output locally and structured JSON in all other
environments so that Google Cloud Logging can parse severity and fields correctly.

Usage:
    from example_api_service.config.logging_config import configure_logging, get_logger
    configure_logging(log_level="INFO", app_env="local", service="my-app")
    logger = get_logger(__name__)
    logger.info("started")
"""

import logging
import sys

import structlog
from structlog.typing import EventDict, FilteringBoundLogger, Processor


def configure_logging(log_level: str, app_env: str, service: str | None = None) -> None:
    """Configure structlog and the stdlib logging bridge. Call once at application startup."""
    log_level_int = logging.getLevelNamesMapping()[log_level.upper()]

    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    if service is not None:
        processors.append(_add_service_context(service, app_env))

    if app_env == "local":
        renderer: Processor = structlog.dev.ConsoleRenderer()
    else:
        # GCP Cloud Logging reads 'severity' for the level and 'time' for the entry timestamp.
        processors.append(_rename_for_gcp)
        renderer = structlog.processors.JSONRenderer()

    # Route both structlog-native and stdlib (uvicorn, etc.) records through one
    # ProcessorFormatter so all output shares the same processor chain and renderer.
    structlog.configure(
        processors=[*processors, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        wrapper_class=structlog.make_filtering_bound_logger(log_level_int),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=processors,
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


def get_logger(name: str | None = None) -> FilteringBoundLogger:
    return structlog.get_logger(name)


def _add_service_context(service: str, env: str) -> Processor:
    """Build a processor that attaches service and env to every log entry."""

    def processor(logger: object, method: str, event_dict: EventDict) -> EventDict:
        event_dict.setdefault("service", service)
        event_dict.setdefault("env", env)
        return event_dict

    return processor


def _rename_for_gcp(logger: object, method: str, event_dict: EventDict) -> EventDict:
    """Map structlog fields to the keys Cloud Logging reads: 'severity' and 'time'."""
    event_dict["severity"] = event_dict.pop("level", method).upper()
    if "timestamp" in event_dict:
        event_dict["time"] = event_dict.pop("timestamp")
    return event_dict
