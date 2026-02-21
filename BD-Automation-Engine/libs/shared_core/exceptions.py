"""
Shared exception hierarchy for BD Automation Engine.

All engines should raise these instead of bare ``Exception`` so that
callers can catch at the appropriate granularity.
"""


class BDError(Exception):
    """Base exception for BD Automation Engine."""


class ConfigError(BDError):
    """Configuration error — missing or invalid env vars / config files."""


class AuthError(BDError):
    """Authentication or authorisation error."""


class DataError(BDError):
    """Data validation or processing error."""


class ExternalServiceError(BDError):
    """External service (API, database, message broker) error."""


class NotFoundError(BDError):
    """Resource not found."""
