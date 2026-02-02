"""
Structured logging configuration using structlog.

Usage:
    from utils.logging_config import setup_logging, get_logger

    # Setup at application entry point
    setup_logging(log_level="INFO")

    # Get logger in any module
    logger = get_logger(__name__)
    logger.info("processing_started", item_count=100)
    logger.error("processing_failed", error=str(e), item_id=42)
"""

import structlog
import logging
import sys
from typing import Optional


def setup_logging(log_level: str = "INFO", json_output: bool = False):
    """
    Configure structured logging for the entire application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_output: If True, always output JSON. If False, use console rendering in TTY.
    """
    # Determine output format
    if json_output or not sys.stderr.isatty():
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            # Add contextvars for request-scoped context
            structlog.contextvars.merge_contextvars,
            # Add log level
            structlog.processors.add_log_level,
            # Add timestamp
            structlog.processors.TimeStamper(fmt="iso"),
            # Add stack info for exceptions
            structlog.processors.StackInfoRenderer(),
            # Format exceptions
            structlog.dev.set_exc_info,
            # Format the final output
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Also configure standard logging to use structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """
    Get a structlog logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured structlog BoundLogger

    Usage:
        logger = get_logger(__name__)
        logger.info("event_name", key="value", count=42)
    """
    return structlog.get_logger(name)


# Auto-initialize with defaults on import
try:
    setup_logging()
except Exception:
    pass  # Ignore if already configured
