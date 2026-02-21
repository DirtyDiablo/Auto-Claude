"""
BD Automation Engine - Shared Core Library.

Centralised configuration, logging, base models, exceptions, and constants
used across all 8 engines.
"""

__version__ = "0.1.0"

from libs.shared_core.config import BDConfig
from libs.shared_core.exceptions import (
    AuthError,
    BDError,
    ConfigError,
    DataError,
    ExternalServiceError,
    NotFoundError,
)
from libs.shared_core.logging import configure_logging, get_logger
from libs.shared_core.models import (
    ErrorResponse,
    PaginatedResponse,
    SearchResult,
    StatusResponse,
)

__all__ = [
    "BDConfig",
    "configure_logging",
    "get_logger",
    "SearchResult",
    "PaginatedResponse",
    "StatusResponse",
    "ErrorResponse",
    "BDError",
    "ConfigError",
    "AuthError",
    "DataError",
    "ExternalServiceError",
    "NotFoundError",
]
