"""
Index Engine2 Program Mapping Data
Federal Programs, Contractors, Contract Vehicles, BD Opportunities
"""
import os
import sys
import csv
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
ENGINE2_DIR = BASE_DIR / "Engine2_ProgramMapping" / "data"
ENGINE2_DATA = BASE_DIR / "engine_data" / "Engine2_ProgramMapping"

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

@openai_retry
def get_embedding(text: str) -> list:
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=text[:8000])
    return response.data[0].embedding

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
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE)
        )
        logger.info(f"Created collection: {name}")

def load_csv(path: Path) -> list:
    records = []
    try:
        with open(path, encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(dict(row))
    except Exception as e:
        logger.error(f"Error loading {path}: {e}")
    return records

def build_program_text(r: dict) -> str:
    parts = []
    for field in ['Name', 'name', 'Program Name', 'Acronym', 'acronym', 'Description', 'description',
                  'Prime Contractor', 'prime_contractor', 'Prime', 'Agency', 'Branch', 'Service',
                  'Location', 'location', 'Mission Area', 'mission_area', 'Contract Value',
                  'Notes', 'notes', 'Status', 'status', 'Category']:
        val = r.get(field)
        if val and isinstance(val, str) and val.strip():
            parts.append(f"{field}: {val}")
    return " | ".join(parts)

def build_contractor_text(r: dict) -> str:
    parts = []
    for field in ['Name', 'name', 'Company', 'Description', 'Specialties', 'Programs',
                  'Contracts', 'Locations', 'Size', 'Revenue', 'Notes']:
        val = r.get(field)
        if val and isinstance(val, str) and val.strip():
            parts.append(f"{field}: {val}")
    return " | ".join(parts)

def build_opportunity_text(r: dict) -> str:
    parts = []
    for field in ['Name', 'Title', 'Description', 'Agency', 'Value', 'Status',
                  'Due Date', 'Contract Type', 'NAICS', 'Notes', 'Requirements']:
        val = r.get(field)
        if val and isinstance(val, str) and val.strip():
            parts.append(f"{field}: {val}")
    return " | ".join(parts)

def build_vehicle_text(r: dict) -> str:
    parts = []
    for field in ['Name', 'Vehicle Name', 'Contract Number', 'Agency', 'Description',
                  'Ceiling', 'Period', 'Prime Holders', 'NAICS Codes', 'Notes']:
        val = r.get(field)
        if val and isinstance(val, str) and val.strip():
            parts.append(f"{field}: {val}")
    return " | ".join(parts)

def index_records(qdrant: QdrantClient, records: list, collection: str, text_builder, source: str):
    logger.info(f"Indexing {len(records)} records to {collection} from {source}")
    if not records:
        return 0

    indexed = 0
    points = []

    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i+BATCH_SIZE]
        texts = [text_builder(r) for r in batch]
        texts = [t if t.strip() else "empty" for t in texts]

        try:
            embeddings = get_embeddings_batch(texts)
            for r, emb, txt in zip(batch, embeddings, texts):
                points.append(PointStruct(
                    id=str(uuid.uuid4()),
                    vector=emb,
                    payload={**r, "content": txt, "_source": source}
                ))
            indexed += len(batch)

            if len(points) >= 500:
                qdrant.upsert(collection_name=collection, points=points, wait=False)
                logger.info(f"  Uploaded {len(points)} points")
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
    logger.info("ENGINE2 PROGRAM MAPPING INDEXER")
    logger.info("=" * 60)

    qdrant = QdrantClient(url=QDRANT_URL)
    ensure_collection(qdrant, "programs")
    ensure_collection(qdrant, "documents")

    total = 0

    # Federal Programs CSVs
    program_files = [
        "Federal Programs MASTER ENRICHED.csv",
        "Federal Programs MASTER V4.csv",
        "Federal Programs ACTIVE ENRICHED V3.csv",
        "Federal Programs TANGO ENRICHED.csv",
        "Programs_KBAll.csv",
        "Federal ProgramsAll.csv",
    ]

    for fname in program_files:
        for dir in [ENGINE2_DIR, ENGINE2_DATA]:
            path = dir / fname
            if path.exists():
                records = load_csv(path)
                total += index_records(qdrant, records, "programs", build_program_text, fname)
                break

    # Contractors
    contractor_files = ["Contractors Database All.csv", "Contractors.csv", "Contractors Database.csv"]
    for fname in contractor_files:
        for dir in [ENGINE2_DIR, ENGINE2_DATA]:
            path = dir / fname
            if path.exists():
                records = load_csv(path)
                total += index_records(qdrant, records, "documents", build_contractor_text, fname)
                break

    # Contract Vehicles
    vehicle_files = ["Contract_VehiclesAll.csv", "Contract_Vehicles.csv"]
    for fname in vehicle_files:
        for dir in [ENGINE2_DIR, ENGINE2_DATA]:
            path = dir / fname
            if path.exists():
                records = load_csv(path)
                total += index_records(qdrant, records, "documents", build_vehicle_text, fname)
                break

    # BD Opportunities
    opp_files = ["BD OpportunitiesAll.csv", "BD Opportunities.csv"]
    for fname in opp_files:
        for dir in [ENGINE2_DIR, ENGINE2_DATA]:
            path = dir / fname
            if path.exists():
                records = load_csv(path)
                total += index_records(qdrant, records, "documents", build_opportunity_text, fname)
                break

    # Program Mapping Hub
    hub_files = ["Program Mapping Intelligence Hub All.csv", "Program Mapping Intelligence Hub.csv"]
    for fname in hub_files:
        for dir in [ENGINE2_DIR, ENGINE2_DATA]:
            path = dir / fname
            if path.exists():
                records = load_csv(path)
                total += index_records(qdrant, records, "programs", build_program_text, fname)
                break

    logger.info(f"\nTotal indexed: {total}")

    # Show stats
    for coll in qdrant.get_collections().collections:
        info = qdrant.get_collection(coll.name)
        logger.info(f"{coll.name}: {info.points_count} points")

if __name__ == "__main__":
    main()
