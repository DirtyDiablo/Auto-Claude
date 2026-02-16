"""
Index Dashboard Public Data
Contacts, Programs, Activities, Documents from dashboard_public
"""

import os
import sys
import json
import uuid
import logging
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

import openai
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from utils.llm_retry import openai_retry

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
BATCH_SIZE = 100

BASE_DIR = Path(__file__).parent.parent.parent
DASHBOARD_DIR = BASE_DIR / "engine_data" / "dashboard_public"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


@openai_retry
def get_embeddings_batch(texts: list) -> list:
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    truncated = [t[:8000] if t else "empty" for t in texts]
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=truncated)
    return [item.embedding for item in response.data]


def ensure_collection(client: QdrantClient, name: str):
    collections = [c.name for c in client.get_collections().collections]
    if name not in collections:
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )
        logger.info(f"Created collection: {name}")


def load_json(path: Path) -> list:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                for key in ["data", "records", "items", "results"]:
                    if key in data and isinstance(data[key], list):
                        return data[key]
                return [data]
    except Exception as e:
        logger.error(f"Error loading {path}: {e}")
    return []


def build_text(r: dict) -> str:
    parts = []
    for key, val in r.items():
        if val and isinstance(val, str) and val.strip() and len(val) < 5000:
            parts.append(f"{key}: {val}")
    return " | ".join(parts)


def index_records(qdrant: QdrantClient, records: list, collection: str, source: str):
    logger.info(f"Indexing {len(records)} records to {collection} from {source}")
    if not records:
        return 0

    indexed = 0
    points = []

    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i : i + BATCH_SIZE]
        texts = [build_text(r) for r in batch]
        texts = [t if t.strip() else "empty" for t in texts]

        try:
            embeddings = get_embeddings_batch(texts)
            for r, emb, txt in zip(batch, embeddings, texts):
                points.append(
                    PointStruct(
                        id=str(uuid.uuid4()),
                        vector=emb,
                        payload={**r, "content": txt, "_source": source},
                    )
                )
            indexed += len(batch)

            if len(points) >= 500:
                qdrant.upsert(collection_name=collection, points=points, wait=False)
                logger.info(f"  Uploaded {len(points)} points | Total: {indexed}")
                points = []

            time.sleep(0.1)
        except Exception as e:
            logger.error(f"Batch error: {e}")
            time.sleep(1)

    if points:
        qdrant.upsert(collection_name=collection, points=points, wait=False)
        logger.info(f"  Uploaded final {len(points)} points")

    return indexed


def main():
    logger.info("=" * 60)
    logger.info("DASHBOARD PUBLIC DATA INDEXER")
    logger.info("=" * 60)

    if not DASHBOARD_DIR.exists():
        logger.error(f"Directory not found: {DASHBOARD_DIR}")
        return

    qdrant = QdrantClient(url=QDRANT_URL)
    for coll in ["contacts", "programs", "activities", "documents"]:
        ensure_collection(qdrant, coll)

    total = 0

    # File to collection mapping
    file_mappings = {
        # Contacts
        "contacts.json": "contacts",
        "contacts_classified.json": "contacts",
        "contact_org_chart.json": "contacts",
        # Programs
        "programs.json": "programs",
        "programs_enriched.json": "programs",
        "program_org_chart.json": "programs",
        "prime_org_chart.json": "programs",
        # Activities
        "call_notes_contacts.json": "activities",
        "call_notes_primes.json": "activities",
        "call_notes_programs.json": "activities",
        "call_notes_locations.json": "activities",
        # Documents
        "past_performance.json": "documents",
        "placements.json": "documents",
        "contractors_enriched.json": "documents",
        "correlation_summary.json": "documents",
        "correlation_summary_enriched.json": "documents",
        "referral_network.json": "documents",
        "scurry_takeover.json": "documents",
        "summary.json": "documents",
        "data_freshness.json": "documents",
    }

    for filename, collection in file_mappings.items():
        path = DASHBOARD_DIR / filename
        if path.exists():
            records = load_json(path)
            if records:
                total += index_records(qdrant, records, collection, filename)

    logger.info(f"\nTotal indexed: {total}")

    # Show stats
    for coll in qdrant.get_collections().collections:
        info = qdrant.get_collection(coll.name)
        logger.info(f"{coll.name}: {info.points_count} points")


if __name__ == "__main__":
    main()
