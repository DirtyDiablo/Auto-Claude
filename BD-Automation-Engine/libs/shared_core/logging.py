"""
Structlog configuration helper.

Provides a single ``configure_logging`` call that sets up structlog with
consistent formatting across all engines, and a ``get_logger`` shortcut.

Usage::

    from libs.shared_core.logging import configure_logging, get_logger

    configure_logging(level="DEBUG", json_output=True)
    logger = get_logger("my_engine")
    logger.info("pipeline.started", stage=3)
"""

import logging
import sys

import structlog


_CONFIGURED = False


def configure_logging(
    level: str = "INFO",
    json_output: bool = False,
) -> None:
    """Configure structlog with consistent formatting across all engines.

    Parameters
    ----------
    level:
        Python logging level name (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    json_output:
        If ``True``, emit JSON lines; otherwise use human-readable console output.
    """
    global _CONFIGURED

    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Shared processors applied to every log event
    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_output:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Also configure the stdlib root so that structlog events emitted via
    # structlog.stdlib go through a ProcessorFormatter.
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(numeric_level)

    _CONFIGURED = True


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a structlog bound logger.

    If ``configure_logging`` has not been called yet, a minimal default
    configuration is applied automatically.
    """
    if not _CONFIGURED:
        configure_logging()
    return structlog.get_logger(name)
