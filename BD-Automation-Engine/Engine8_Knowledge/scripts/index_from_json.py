"""
Index data from JSON files into Qdrant with OpenAI embeddings.
"""
import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")

import openai
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import logging
import uuid

from utils.llm_retry import openai_retry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536

DATA_DIR = Path(__file__).parent.parent.parent / "engine_data" / "dashboard_public"

@openai_retry
def generate_embedding(text: str) -> list:
    """Generate embedding using OpenAI API."""
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text[:8000]  # Limit text length
    )
    return response.data[0].embedding

def create_collection(client: QdrantClient, name: str):
    """Create collection if it doesn't exist."""
    collections = [c.name for c in client.get_collections().collections]
    if name not in collections:
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE)
        )
        logger.info(f"Created collection: {name}")
    else:
        logger.info(f"Collection exists: {name}")

def build_contact_text(record: dict) -> str:
    """Build searchable text from contact record."""
    parts = []
    for field in ["name", "first_name", "last_name", "title", "company", "program", "notes", "email"]:
        val = record.get(field, "")
        if val and isinstance(val, str):
            parts.append(val)
    return " | ".join(parts) if parts else ""

def build_program_text(record: dict) -> str:
    """Build searchable text from program record."""
    parts = []
    for field in ["name", "prime_contractor", "location", "mission_area", "notes", "description"]:
        val = record.get(field, "")
        if val and isinstance(val, str):
            parts.append(val)
    return " | ".join(parts) if parts else ""

def index_contacts(client: QdrantClient, limit: int = None):
    """Index contacts from JSON."""
    json_path = DATA_DIR / "contacts.json"
    if not json_path.exists():
        logger.error(f"File not found: {json_path}")
        return 0

    with open(json_path) as f:
        records = json.load(f)

    if limit:
        records = records[:limit]

    logger.info(f"Indexing {len(records)} contacts...")
    create_collection(client, "contacts")

    indexed = 0
    for i, record in enumerate(records):
        text = build_contact_text(record)
        if not text.strip():
            continue

        try:
            embedding = generate_embedding(text)
            # Always use UUID for Qdrant compatibility
            point_id = str(uuid.uuid4())

            # Store content for search display
            record["content"] = text
            record["_embedding_model"] = EMBEDDING_MODEL

            client.upsert(
                collection_name="contacts",
                points=[PointStruct(id=point_id, vector=embedding, payload=record)]
            )
            indexed += 1
            if indexed % 10 == 0:
                logger.info(f"  Indexed {indexed}/{len(records)} contacts")
        except Exception as e:
            logger.error(f"Error indexing contact {i}: {e}")

    logger.info(f"Indexed {indexed} contacts")
    return indexed

def index_programs(client: QdrantClient, limit: int = None):
    """Index programs from JSON."""
    json_path = DATA_DIR / "programs.json"
    if not json_path.exists():
        logger.error(f"File not found: {json_path}")
        return 0

    with open(json_path) as f:
        records = json.load(f)

    if limit:
        records = records[:limit]

    logger.info(f"Indexing {len(records)} programs...")
    create_collection(client, "programs")

    indexed = 0
    for i, record in enumerate(records):
        text = build_program_text(record)
        if not text.strip():
            continue

        try:
            embedding = generate_embedding(text)
            # Always use UUID for Qdrant compatibility
            point_id = str(uuid.uuid4())

            record["content"] = text
            record["_embedding_model"] = EMBEDDING_MODEL

            client.upsert(
                collection_name="programs",
                points=[PointStruct(id=point_id, vector=embedding, payload=record)]
            )
            indexed += 1
            if indexed % 10 == 0:
                logger.info(f"  Indexed {indexed}/{len(records)} programs")
        except Exception as e:
            logger.error(f"Error indexing program {i}: {e}")

    logger.info(f"Indexed {indexed} programs")
    return indexed

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--collection", default="contacts", choices=["contacts", "programs", "all"])
    parser.add_argument("--limit", type=int, default=None, help="Limit records (for testing)")
    args = parser.parse_args()

    if not OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY not set in .env")
        sys.exit(1)

    logger.info(f"Connecting to Qdrant at {QDRANT_URL}")
    client = QdrantClient(url=QDRANT_URL)

    if args.collection in ["contacts", "all"]:
        index_contacts(client, args.limit)
    if args.collection in ["programs", "all"]:
        index_programs(client, args.limit)

    # Show final stats
    for coll in client.get_collections().collections:
        info = client.get_collection(coll.name)
        logger.info(f"{coll.name}: {info.points_count} points")
