"""
Centralised configuration with env var loading and validation.

Usage::

    from libs.shared_core.config import BDConfig

    cfg = BDConfig()                          # loads .env from project root
    cfg = BDConfig(env_file="path/to/.env")   # explicit path

    key = cfg.anthropic_api_key               # property access (returns None if unset)
    key = cfg.require("ANTHROPIC_API_KEY")    # raises ConfigError if missing
    val = cfg.get("CUSTOM_VAR", "default")    # dict-style with default
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from libs.shared_core.exceptions import ConfigError


class BDConfig:
    """Centralised configuration with env var loading and validation."""

    def __init__(self, env_file: Optional[str] = None) -> None:
        if env_file is not None:
            load_dotenv(env_file, override=False)
        else:
            # Walk up from CWD looking for .env
            candidate = Path.cwd() / ".env"
            if candidate.exists():
                load_dotenv(str(candidate), override=False)

    # -----------------------------------------------------------------
    # Generic accessors
    # -----------------------------------------------------------------

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Return an env var value, or *default* if unset/empty."""
        val = os.environ.get(key, "")
        return val if val else default

    def require(self, key: str) -> str:
        """Return an env var value, raising :class:`ConfigError` if missing."""
        val = os.environ.get(key, "")
        if not val:
            raise ConfigError(f"Required environment variable '{key}' is not set")
        return val

    # -----------------------------------------------------------------
    # API key properties
    # -----------------------------------------------------------------

    @property
    def anthropic_api_key(self) -> Optional[str]:
        return self.get("ANTHROPIC_API_KEY")

    @property
    def openai_api_key(self) -> Optional[str]:
        return self.get("OPENAI_API_KEY")

    @property
    def notion_token(self) -> Optional[str]:
        return self.get("NOTION_TOKEN")

    @property
    def apify_api_token(self) -> Optional[str]:
        return self.get("APIFY_API_TOKEN")

    @property
    def sam_api_key(self) -> Optional[str]:
        return self.get("SAM_API_KEY")

    # -----------------------------------------------------------------
    # Infrastructure properties
    # -----------------------------------------------------------------

    @property
    def qdrant_url(self) -> str:
        return self.get("QDRANT_URL", "http://localhost:6333")

    @property
    def database_url(self) -> Optional[str]:
        return self.get("DATABASE_URL")

    @property
    def redis_url(self) -> Optional[str]:
        return self.get("REDIS_URL")

    # -----------------------------------------------------------------
    # Bullhorn CRM properties
    # -----------------------------------------------------------------

    @property
    def bullhorn_api_url(self) -> str:
        return self.get("BULLHORN_API_URL", "https://rest.bullhornstaffing.com")

    @property
    def bullhorn_client_id(self) -> Optional[str]:
        return self.get("BULLHORN_CLIENT_ID")

    @property
    def bullhorn_client_secret(self) -> Optional[str]:
        return self.get("BULLHORN_CLIENT_SECRET")

    # -----------------------------------------------------------------
    # BD scoring thresholds
    # -----------------------------------------------------------------

    @property
    def hot_threshold(self) -> int:
        return int(self.get("BD_TIER_HOT_MIN", "80"))

    @property
    def warm_threshold(self) -> int:
        return int(self.get("BD_TIER_WARM_MIN", "50"))

    # -----------------------------------------------------------------
    # Logging
    # -----------------------------------------------------------------

    @property
    def log_level(self) -> str:
        return self.get("LOG_LEVEL", "INFO")

    @property
    def log_file(self) -> Optional[str]:
        return self.get("LOG_FILE")
