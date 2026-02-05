"""
Index Engine1 Scraper Data + Dashboard Public Jobs
All scraped jobs from Apify + enriched job data
"""
import os
import sys
import json
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

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
BATCH_SIZE = 100

BASE_DIR = Path(__file__).parent.parent.parent
ENGINE1_DIR = BASE_DIR / "engine_data" / "Engine1_Scraper"
DASHBOARD_DIR = BASE_DIR / "engine_data" / "dashboard_public"

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

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

def load_json(path: Path) -> list:
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return [data]
    except Exception as e:
        logger.error(f"Error loading {path}: {e}")
    return []

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

def build_job_text(r: dict) -> str:
    parts = []
    for field in ['title', 'Title', 'jobTitle', 'Job Title', 'name', 'Name',
                  'description', 'Description', 'requirements', 'Requirements',
                  'skills', 'Skills', 'qualifications', 'Qualifications',
                  'location', 'Location', 'city', 'state', 'company', 'Company',
                  'client', 'Client', 'program', 'Program', 'prime', 'Prime',
                  'clearance', 'Clearance', 'securityClearance',
                  'salary', 'Salary', 'compensation', 'benefits',
                  'notes', 'Notes', 'summary', 'Summary', 'url', 'link']:
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
    logger.info("ENGINE1 SCRAPER + JOBS INDEXER")
    logger.info("=" * 60)

    qdrant = QdrantClient(url=QDRANT_URL)
    ensure_collection(qdrant, "jobs")

    total = 0

    # Engine1 Scraper JSON files
    if ENGINE1_DIR.exists():
        for json_file in ENGINE1_DIR.glob("*.json"):
            records = load_json(json_file)
            total += index_records(qdrant, records, "jobs", build_job_text, json_file.name)

        # CSV files
        for csv_file in ENGINE1_DIR.glob("*.csv"):
            records = load_csv(csv_file)
            total += index_records(qdrant, records, "jobs", build_job_text, csv_file.name)

    # Dashboard public jobs
    if DASHBOARD_DIR.exists():
        jobs_json = DASHBOARD_DIR / "jobs.json"
        if jobs_json.exists():
            records = load_json(jobs_json)
            total += index_records(qdrant, records, "jobs", build_job_text, "dashboard_jobs.json")

        jobs_enriched = DASHBOARD_DIR / "jobs_enriched.json"
        if jobs_enriched.exists():
            data = load_json(jobs_enriched)
            if data and isinstance(data[0], dict) and 'data' in data[0]:
                records = data[0].get('data', [])
            else:
                records = data
            total += index_records(qdrant, records, "jobs", build_job_text, "dashboard_jobs_enriched.json")

    # Engine2 Job CSVs
    engine2_dir = BASE_DIR / "Engine2_ProgramMapping" / "data"
    job_files = [
        "GDIT Jobs 2.csv", "GDIT Jobs 2All.csv",
        "Insight Global Jobs - Program Mapped (Dec 2025).csv",
        "Insight Global Jobs - Program Mapped (Dec 2025) All.csv",
    ]
    for fname in job_files:
        path = engine2_dir / fname
        if path.exists():
            records = load_csv(path)
            total += index_records(qdrant, records, "jobs", build_job_text, fname)

    logger.info(f"\nTotal indexed: {total}")

    # Show stats
    for coll in qdrant.get_collections().collections:
        info = qdrant.get_collection(coll.name)
        logger.info(f"{coll.name}: {info.points_count} points")

if __name__ == "__main__":
    main()
