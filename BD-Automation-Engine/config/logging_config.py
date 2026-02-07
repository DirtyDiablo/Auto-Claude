"""
Structlog configuration for BD-Automation-Engine.

Usage:
    from config.logging_config import setup_logging, get_logger
    setup_logging()
    logger = get_logger("my_module")
    logger.info("event_happened", user="alice", count=42)
"""

import logging
import sys
import uuid
from contextvars import ContextVar

import structlog

# Per-request context
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def add_request_id(logger, method_name, event_dict):
    """Inject request_id from context var into every log entry."""
    rid = request_id_var.get()
    if rid:
        event_dict["request_id"] = rid
    return event_dict


def setup_logging(log_level: str = "INFO", json_output: bool = False):
    """
    Configure structlog + stdlib logging integration.

    Args:
        log_level: Logging level string (DEBUG, INFO, WARNING, ERROR).
        json_output: If True, emit JSON lines; otherwise, colored console output.
    """
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        add_request_id,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_output:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty())

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Quiet noisy third-party loggers
    for name in ("uvicorn.access", "httpx", "httpcore", "openai"):
        logging.getLogger(name).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structlog logger bound to the given name."""
    return structlog.get_logger(name)


def generate_request_id() -> str:
    """Generate a short request ID for tracing."""
    return uuid.uuid4().hex[:12]
