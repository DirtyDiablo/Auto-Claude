"""
Bidirectional sync between Notion databases and Qdrant unified collections.

Usage:
    from services.notion_qdrant_sync import NotionQdrantSync

    sync = NotionQdrantSync()
    sync.sync_contacts_to_qdrant(notion_records, source_db="dcgs_contacts")
    status = sync.get_sync_status()
"""

import os
import hashlib
import json
from datetime import datetime
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv

load_dotenv()

# Import retry utilities
try:
    from utils.llm_retry import openai_retry, api_retry
    from utils.logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    def openai_retry(func):
        return func
    def api_retry(func):
        return func

# Qdrant
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    logger.warning("qdrant-client not installed")

# OpenAI for embeddings
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("openai not installed")


# Notion Database IDs (from CLAUDE.md)
NOTION_DATABASES = {
    "dcgs_contacts": "2ccdef65-baa5-8087-a53b-000ba596128e",
    "gdit_other": "70ea1c94-211d-40e6-a994-e8d7c4807434",
    "gdit_jobs": "2ccdef65-baa5-80b0-9a80-000bd2745f63",
    "program_mapping": "f57792c1-605b-424c-8830-23ab41c47137",
    "federal_programs": "06cd9b22-5d6b-4d37-b0d3-ba99da4971fa",
    "bd_opportunities": "2bcdef65-baa5-80ed-bd95-000b2f898e17",
}

# Mapping from Notion DB to Qdrant collection
QDRANT_COLLECTION_MAP = {
    "dcgs_contacts": "contacts",
    "gdit_other": "contacts",
    "gdit_jobs": "jobs",
    "program_mapping": "jobs",
    "federal_programs": "programs",
    "bd_opportunities": "opportunities",
}


class NotionQdrantSync:
    """Bidirectional sync between Notion and Qdrant."""

    def __init__(
        self,
        qdrant_url: str = None,
        openai_api_key: str = None,
        notion_token: str = None,
    ):
        self.qdrant_url = qdrant_url or os.environ.get("QDRANT_URL", "http://localhost:6333")
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        self.notion_token = notion_token or os.environ.get("NOTION_TOKEN")

        if QDRANT_AVAILABLE:
            self.qdrant = QdrantClient(url=self.qdrant_url)
        else:
            self.qdrant = None

        if OPENAI_AVAILABLE and self.openai_api_key:
            self.openai = OpenAI(api_key=self.openai_api_key)
        else:
            self.openai = None

    @openai_retry
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using OpenAI."""
        if not self.openai:
            raise ValueError("OpenAI client not configured")

        response = self.openai.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding

    def content_hash(self, data: dict) -> str:
        """Generate hash for deduplication."""
        return hashlib.md5(
            json.dumps(data, sort_keys=True, default=str).encode()
        ).hexdigest()

    def build_contact_text(self, props: dict) -> str:
        """Build searchable text from contact properties."""
        parts = []
        name = f"{props.get('first_name', '')} {props.get('last_name', '')}".strip()
        if name:
            parts.append(f"Name: {name}")
        if props.get('job_title'):
            parts.append(f"Title: {props['job_title']}")
        if props.get('company'):
            parts.append(f"Company: {props['company']}")
        if props.get('program'):
            parts.append(f"Program: {props['program']}")
        if props.get('city'):
            parts.append(f"Location: {props['city']}, {props.get('state', '')}")
        if props.get('hierarchy_tier'):
            parts.append(f"Tier: {props['hierarchy_tier']}")
        return ". ".join(parts)

    def build_program_text(self, props: dict) -> str:
        """Build searchable text from program properties."""
        parts = []
        if props.get('program_name'):
            parts.append(f"Program: {props['program_name']}")
        if props.get('acronym'):
            parts.append(f"Acronym: {props['acronym']}")
        if props.get('agency_owner'):
            parts.append(f"Agency: {props['agency_owner']}")
        if props.get('prime_contractor'):
            parts.append(f"Prime: {props['prime_contractor']}")
        if props.get('keywords'):
            parts.append(f"Keywords: {', '.join(props['keywords'])}")
        return ". ".join(parts)

    def build_job_text(self, props: dict) -> str:
        """Build searchable text from job properties."""
        parts = []
        if props.get('title'):
            parts.append(f"Job: {props['title']}")
        if props.get('company'):
            parts.append(f"Company: {props['company']}")
        if props.get('location'):
            parts.append(f"Location: {props['location']}")
        if props.get('detected_clearance'):
            parts.append(f"Clearance: {props['detected_clearance']}")
        if props.get('mapped_program'):
            parts.append(f"Program: {props['mapped_program']}")
        return ". ".join(parts)

    def sync_records_to_qdrant(
        self,
        records: List[dict],
        source_db: str,
        batch_size: int = 50,
    ) -> Dict[str, Any]:
        """
        Sync records from Notion to Qdrant.

        Args:
            records: List of record dictionaries
            source_db: Source database name (key in NOTION_DATABASES)
            batch_size: Number of records per batch

        Returns:
            Sync result with counts
        """
        if not self.qdrant:
            raise ValueError("Qdrant client not configured")

        collection = QDRANT_COLLECTION_MAP.get(source_db)
        if not collection:
            raise ValueError(f"Unknown source database: {source_db}")

        # Determine text builder based on collection
        if collection == "contacts":
            build_text = self.build_contact_text
        elif collection == "programs":
            build_text = self.build_program_text
        else:
            build_text = self.build_job_text

        batch = []
        synced_count = 0
        error_count = 0

        for record in records:
            try:
                text = build_text(record)
                if not text.strip():
                    continue

                embedding = self.get_embedding(text)

                payload = {
                    **record,
                    "content": text,
                    "source_project": "bd_engine",
                    "source_type": f"notion_{source_db}",
                    "content_hash": self.content_hash(record),
                    "embedding_model": "text-embedding-3-small",
                    "synced_at": datetime.utcnow().isoformat(),
                }

                point_id = record.get("notion_page_id") or record.get("id") or self.content_hash(record)

                batch.append(PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload,
                ))

                if len(batch) >= batch_size:
                    self.qdrant.upsert(collection_name=collection, points=batch)
                    synced_count += len(batch)
                    logger.info("sync_batch", collection=collection, count=len(batch))
                    batch = []

            except Exception as e:
                logger.error("sync_record_failed", error=str(e))
                error_count += 1

        # Final batch
        if batch:
            self.qdrant.upsert(collection_name=collection, points=batch)
            synced_count += len(batch)

        logger.info(
            "sync_complete",
            source=source_db,
            collection=collection,
            synced=synced_count,
            errors=error_count,
        )

        return {
            "source_db": source_db,
            "collection": collection,
            "synced_count": synced_count,
            "error_count": error_count,
        }

    def get_sync_status(self) -> Dict[str, Any]:
        """Get sync status for all collections."""
        if not self.qdrant:
            return {"error": "Qdrant client not configured"}

        status = {}
        for collection in set(QDRANT_COLLECTION_MAP.values()):
            try:
                info = self.qdrant.get_collection(collection)
                status[collection] = {
                    "vectors": info.points_count,
                    "status": str(info.status),
                }
            except Exception as e:
                status[collection] = {"vectors": 0, "error": str(e)}

        return status


# CLI usage
if __name__ == "__main__":
    sync = NotionQdrantSync()
    print(json.dumps(sync.get_sync_status(), indent=2))
