"""
Pathway Configuration for BD Streaming Pipeline.

Centralized configuration for Kafka, PostgreSQL, S3, and embedding settings.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
import os


@dataclass
class PathwayConfig:
    """Configuration for Pathway streaming pipeline."""

    # Kafka settings
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_security_protocol: str = "PLAINTEXT"
    kafka_sasl_mechanism: Optional[str] = None
    kafka_sasl_username: Optional[str] = None
    kafka_sasl_password: Optional[str] = None

    # PostgreSQL settings
    postgres_connection: str = "postgresql://localhost:5432/bd_intelligence"
    postgres_user: str = "postgres"
    postgres_password: str = ""
    postgres_database: str = "bd_intelligence"

    # S3 settings
    s3_bucket: str = "bd-intelligence-data"
    s3_region: str = "us-east-1"
    s3_access_key: Optional[str] = None
    s3_secret_key: Optional[str] = None

    # OpenAI/Embedding settings
    openai_api_key: Optional[str] = None
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536

    # Pipeline settings
    batch_size: int = 100
    checkpoint_interval_ms: int = 30000
    max_parallelism: int = 4

    # Alert settings
    webhook_url: Optional[str] = None
    alert_cooldown_seconds: int = 300

    def __post_init__(self):
        """Load settings from environment variables if not provided."""
        if not self.openai_api_key:
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.postgres_password:
            self.postgres_password = os.getenv("POSTGRES_PASSWORD", "")
        if not self.s3_access_key:
            self.s3_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        if not self.s3_secret_key:
            self.s3_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        if not self.webhook_url:
            self.webhook_url = os.getenv("BD_ALERT_WEBHOOK_URL")

    def get_kafka_settings(self) -> Dict[str, Any]:
        """Get Kafka connection settings as a dictionary."""
        settings = {
            "bootstrap.servers": self.kafka_bootstrap_servers,
            "security.protocol": self.kafka_security_protocol,
        }

        if self.kafka_sasl_mechanism:
            settings["sasl.mechanism"] = self.kafka_sasl_mechanism
        if self.kafka_sasl_username:
            settings["sasl.username"] = self.kafka_sasl_username
        if self.kafka_sasl_password:
            settings["sasl.password"] = self.kafka_sasl_password

        return settings

    def get_postgres_settings(self) -> Dict[str, Any]:
        """Get PostgreSQL connection settings."""
        return {
            "host": self.postgres_connection.split("://")[1].split(":")[0] if "://" in self.postgres_connection else "localhost",
            "port": 5432,
            "user": self.postgres_user,
            "password": self.postgres_password,
            "database": self.postgres_database,
        }

    def get_s3_settings(self) -> Dict[str, Any]:
        """Get S3 connection settings."""
        return {
            "bucket": self.s3_bucket,
            "region": self.s3_region,
            "access_key": self.s3_access_key,
            "secret_key": self.s3_secret_key,
        }


def load_config_from_env() -> PathwayConfig:
    """Load configuration from environment variables."""
    return PathwayConfig(
        kafka_bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        kafka_security_protocol=os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
        postgres_connection=os.getenv("POSTGRES_CONNECTION", "postgresql://localhost:5432/bd_intelligence"),
        postgres_user=os.getenv("POSTGRES_USER", "postgres"),
        postgres_password=os.getenv("POSTGRES_PASSWORD", ""),
        postgres_database=os.getenv("POSTGRES_DATABASE", "bd_intelligence"),
        s3_bucket=os.getenv("S3_BUCKET", "bd-intelligence-data"),
        s3_region=os.getenv("S3_REGION", "us-east-1"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
        batch_size=int(os.getenv("PATHWAY_BATCH_SIZE", "100")),
        checkpoint_interval_ms=int(os.getenv("PATHWAY_CHECKPOINT_INTERVAL_MS", "30000")),
        webhook_url=os.getenv("BD_ALERT_WEBHOOK_URL"),
    )
