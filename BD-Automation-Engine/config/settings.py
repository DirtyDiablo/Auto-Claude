"""
Centralized settings management using pydantic-settings.

All modules should import settings from here:
    from config.settings import get_settings
    settings = get_settings()

This ensures:
- All API keys come from environment variables
- Type validation on all settings
- Centralized configuration with defaults
- No hardcoded secrets anywhere
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ===========================================
    # LLM API KEYS
    # ===========================================
    anthropic_api_key: str = Field(..., description="Anthropic Claude API key")
    openai_api_key: str = Field(..., description="OpenAI API key for embeddings")

    # LLM Configuration
    default_llm_model: str = Field(
        default="claude-sonnet-4-20250514", description="Default Claude model to use"
    )
    default_embedding_model: str = Field(
        default="text-embedding-3-small", description="Default OpenAI embedding model"
    )
    embedding_dimensions: int = Field(
        default=1536, description="Embedding vector dimensions"
    )

    # ===========================================
    # VECTOR DATABASE (Qdrant)
    # ===========================================
    qdrant_url: str = Field(
        default="http://localhost:6333", description="Qdrant server URL"
    )
    qdrant_api_key: str = Field(
        default="", description="Qdrant API key (optional for local)"
    )

    # ===========================================
    # REDIS CACHE
    # ===========================================
    redis_url: str = Field(
        default="redis://localhost:6379", description="Redis connection URL"
    )

    # ===========================================
    # NOTION
    # ===========================================
    notion_token: str = Field(
        default="", alias="NOTION_TOKEN", description="Notion API integration token"
    )
    notion_api_key: str = Field(default="", description="Alias for notion_token")

    # Notion Database IDs
    notion_db_dcgs_contacts: str = Field(
        default="2ccdef65-baa5-8087-a53b-000ba596128e",
        description="DCGS Contacts database ID",
    )
    notion_db_federal_programs: str = Field(
        default="06cd9b22-5d6b-4d37-b0d3-ba99da4971fa",
        description="Federal Programs database ID",
    )
    notion_db_bd_opportunities: str = Field(
        default="2bcdef65-baa5-80ed-bd95-000b2f898e17",
        description="BD Opportunities database ID",
    )
    notion_db_program_mapping_hub: str = Field(
        default="f57792c1-605b-424c-8830-23ab41c47137",
        description="Program Mapping Hub database ID",
    )
    notion_db_gdit_jobs: str = Field(
        default="2563119e7914442cbe0fb86904a957a1", description="GDIT Jobs database ID"
    )

    # ===========================================
    # APIFY (Web Scraping)
    # ===========================================
    apify_api_token: str = Field(
        default="", description="Apify API token for web scraping"
    )

    # ===========================================
    # HUB API
    # ===========================================
    hub_api_url: str = Field(
        default="http://localhost:8100", description="Hub API base URL"
    )
    hub_api_key: str = Field(default="", description="Hub API authentication key")

    # ===========================================
    # N8N ORCHESTRATION
    # ===========================================
    n8n_webhook_url: str = Field(
        default="", description="n8n webhook URL for job intake"
    )
    n8n_api_key: str = Field(default="", description="n8n API key")
    n8n_api_url: str = Field(default="", description="n8n API base URL")

    # ===========================================
    # CONTACT ENRICHMENT
    # ===========================================
    proxycurl_api_key: str = Field(
        default="", description="ProxyCurl API key for LinkedIn enrichment"
    )
    reacher_api_key: str = Field(
        default="", description="Reacher API key for email verification"
    )

    # ===========================================
    # DIFY INTEGRATION
    # ===========================================
    dify_api_url: str = Field(
        default="http://localhost:3000", description="Dify instance URL"
    )
    dify_api_key: str = Field(default="", description="Dify API key")

    # ===========================================
    # RAGFLOW INTEGRATION
    # ===========================================
    ragflow_api_key: str = Field(default="", description="RAGflow API key")
    ragflow_base_url: str = Field(
        default="http://localhost", description="RAGflow base URL"
    )

    # ===========================================
    # BD SCORING THRESHOLDS
    # ===========================================
    high_confidence_threshold: float = Field(
        default=0.70, description="High confidence match threshold"
    )
    medium_confidence_threshold: float = Field(
        default=0.50, description="Medium confidence match threshold"
    )
    bd_tier_hot_min: int = Field(
        default=80, description="Minimum score for Hot BD tier"
    )
    bd_tier_warm_min: int = Field(
        default=50, description="Minimum score for Warm BD tier"
    )

    # ===========================================
    # LOGGING
    # ===========================================
    log_level: str = Field(
        default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )
    log_file: str = Field(
        default="data/state/logs/bd_automation.log", description="Log file path"
    )

    # ===========================================
    # PROCESSING SETTINGS
    # ===========================================
    batch_size: int = Field(default=10, description="Default batch processing size")
    process_interval_minutes: int = Field(
        default=15, description="Processing interval in minutes"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Usage:
        from config.settings import get_settings
        settings = get_settings()
        print(settings.qdrant_url)
    """
    return Settings()


# Convenience function for quick access
def reload_settings() -> Settings:
    """Force reload settings (clears cache)."""
    get_settings.cache_clear()
    return get_settings()
