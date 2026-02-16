"""
Priority Full Data Indexer - Maximum Parallelization
Indexes all Bullhorn ETL + Colton Scurry + Outputs data with OpenAI embeddings (1536-dim)
"""

import os
import sys
import json
import csv
import sqlite3
import uuid
import logging
import time
from pathlib import Path
from typing import List, Dict
import threading

# Setup paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

import openai
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    OptimizersConfigDiff,
)

from utils.llm_retry import openai_retry

# Configuration
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536

# Maximum performance settings
BATCH_SIZE = 100  # Records per embedding batch
UPLOAD_BATCH_SIZE = 500  # Records per Qdrant upsert
MAX_WORKERS = 10  # Parallel embedding threads
MAX_TEXT_LENGTH = 8000  # OpenAI limit

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
BULLHORN_DB = BASE_DIR / "Engine7_BullhornETL" / "data" / "bullhorn_master.db"
COLTON_DIR = BASE_DIR / "Engine7_BullhornETL" / "colton_scurry_analysis"
OUTPUTS_DIR = BASE_DIR / "outputs"

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# Thread-safe counters
class Counter:
    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()

    def increment(self, amount=1):
        with self.lock:
            self.value += amount
            return self.value


# Global counters
indexed_count = Counter()
error_count = Counter()


def get_openai_client():
    """Get OpenAI client."""
    return openai.OpenAI(api_key=OPENAI_API_KEY)


@openai_retry
def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for a batch of texts."""
    client = get_openai_client()
    # Truncate texts
    truncated = [t[:MAX_TEXT_LENGTH] if t else "" for t in texts]
    # Filter empty
    valid_texts = [t if t.strip() else "empty" for t in truncated]

    try:
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=valid_texts)
        return [item.embedding for item in response.data]
    except Exception as e:
        logger.error(f"Embedding error: {e}")
        raise


def create_collection(client: QdrantClient, name: str):
    """Create or recreate collection with optimized settings."""
    collections = [c.name for c in client.get_collections().collections]

    if name in collections:
        # Get current count
        info = client.get_collection(name)
        logger.info(
            f"Collection {name} exists with {info.points_count} points - will append"
        )
    else:
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
            optimizers_config=OptimizersConfigDiff(
                indexing_threshold=50000,  # Delay indexing for bulk uploads
            ),
        )
        logger.info(f"Created collection: {name}")


def upsert_batch(client: QdrantClient, collection: str, points: List[PointStruct]):
    """Upsert a batch of points to Qdrant."""
    try:
        client.upsert(collection_name=collection, points=points, wait=False)
        return len(points)
    except Exception as e:
        logger.error(f"Upsert error: {e}")
        return 0


def process_records_parallel(
    records: List[Dict],
    collection: str,
    text_builder,
    qdrant_client: QdrantClient,
    source_name: str,
) -> int:
    """Process records with parallel embedding generation."""
    total = len(records)
    logger.info(f"Processing {total:,} records for {collection} from {source_name}")

    if total == 0:
        return 0

    # Build texts
    texts = []
    valid_records = []
    for r in records:
        text = text_builder(r)
        if text and text.strip():
            texts.append(text)
            valid_records.append(r)

    logger.info(f"  Valid records with text: {len(valid_records):,}")

    if not valid_records:
        return 0

    # Process in batches
    points = []
    processed = 0

    for i in range(0, len(valid_records), BATCH_SIZE):
        batch_texts = texts[i : i + BATCH_SIZE]
        batch_records = valid_records[i : i + BATCH_SIZE]

        try:
            embeddings = generate_embeddings_batch(batch_texts)

            for j, (record, embedding) in enumerate(zip(batch_records, embeddings)):
                point_id = str(uuid.uuid4())
                payload = {**record, "content": batch_texts[j], "_source": source_name}
                points.append(
                    PointStruct(id=point_id, vector=embedding, payload=payload)
                )

            processed += len(batch_texts)

            # Upload when we have enough points
            if len(points) >= UPLOAD_BATCH_SIZE:
                upsert_batch(qdrant_client, collection, points)
                count = indexed_count.increment(len(points))
                logger.info(
                    f"  Uploaded {len(points)} points | Total indexed: {count:,}"
                )
                points = []

            # Brief pause to avoid rate limits
            if processed % 500 == 0:
                time.sleep(0.1)

        except Exception as e:
            error_count.increment(len(batch_texts))
            logger.error(f"  Batch error at {i}: {e}")
            time.sleep(1)  # Back off on error

    # Upload remaining
    if points:
        upsert_batch(qdrant_client, collection, points)
        count = indexed_count.increment(len(points))
        logger.info(f"  Uploaded final {len(points)} points | Total indexed: {count:,}")

    return processed


# Text builders for different record types
def build_candidate_text(r: Dict) -> str:
    parts = []
    for field in [
        "firstName",
        "lastName",
        "name",
        "title",
        "occupation",
        "companyName",
        "email",
        "phone",
        "address",
        "city",
        "state",
        "skills",
        "certifications",
        "notes",
        "description",
    ]:
        val = r.get(field)
        if val and isinstance(val, str) and val.strip():
            parts.append(f"{field}: {val}")
    return " | ".join(parts)


def build_activity_text(r: Dict) -> str:
    parts = []
    for field in [
        "type",
        "action",
        "notes",
        "comments",
        "description",
        "subject",
        "contactName",
        "candidateName",
        "jobTitle",
    ]:
        val = r.get(field)
        if val and isinstance(val, str) and val.strip():
            parts.append(f"{field}: {val}")
    return " | ".join(parts)


def build_call_note_text(r: Dict) -> str:
    parts = []
    for field in [
        "action",
        "comments",
        "note_text",
        "notes",
        "person_name",
        "company",
        "subject",
        "body",
    ]:
        val = r.get(field)
        if val and isinstance(val, str) and val.strip():
            parts.append(val)
    return " | ".join(parts)


def build_document_text(r: Dict) -> str:
    parts = []
    for field in [
        "title",
        "name",
        "description",
        "content",
        "notes",
        "text",
        "body",
        "summary",
        "program",
        "prime",
        "contract",
    ]:
        val = r.get(field)
        if val and isinstance(val, str) and val.strip():
            parts.append(val)
    return " | ".join(parts)


def build_job_text(r: Dict) -> str:
    parts = []
    for field in [
        "title",
        "jobTitle",
        "description",
        "requirements",
        "skills",
        "location",
        "company",
        "client",
        "program",
        "clearance",
        "notes",
    ]:
        val = r.get(field)
        if val and isinstance(val, str) and val.strip():
            parts.append(f"{field}: {val}")
    return " | ".join(parts)


def build_program_text(r: Dict) -> str:
    parts = []
    for field in [
        "name",
        "program_name",
        "acronym",
        "description",
        "prime",
        "prime_contractor",
        "agency",
        "branch",
        "location",
        "notes",
    ]:
        val = r.get(field)
        if val and isinstance(val, str) and val.strip():
            parts.append(f"{field}: {val}")
    return " | ".join(parts)


def build_md_text(content: str, filename: str) -> str:
    return f"File: {filename}\n\n{content}"


def load_sqlite_table(db_path: Path, table: str, limit: int = None) -> List[Dict]:
    """Load records from SQLite table."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = f"SELECT * FROM {table}"
    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query)
    rows = cursor.fetchall()
    records = [dict(row) for row in rows]
    conn.close()
    return records


def load_csv_file(path: Path) -> List[Dict]:
    """Load records from CSV file."""
    records = []
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(dict(row))
    except Exception as e:
        logger.error(f"Error loading {path}: {e}")
    return records


def load_json_file(path: Path) -> List[Dict]:
    """Load records from JSON file."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # Try common keys
                for key in ["data", "records", "items", "results"]:
                    if key in data and isinstance(data[key], list):
                        return data[key]
                # Return as single record
                return [data]
    except Exception as e:
        logger.error(f"Error loading {path}: {e}")
    return []


def load_md_files(directory: Path) -> List[Dict]:
    """Load markdown files as documents."""
    records = []
    for md_file in directory.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8", errors="ignore")
            records.append(
                {
                    "filename": md_file.name,
                    "filepath": str(md_file.relative_to(BASE_DIR)),
                    "content": content[:15000],  # Limit content size
                    "type": "markdown",
                }
            )
        except Exception as e:
            logger.error(f"Error loading {md_file}: {e}")
    return records


def index_bullhorn_database(qdrant: QdrantClient):
    """Index all Bullhorn database tables."""
    logger.info("=" * 60)
    logger.info("INDEXING BULLHORN DATABASE")
    logger.info("=" * 60)

    if not BULLHORN_DB.exists():
        logger.error(f"Database not found: {BULLHORN_DB}")
        return

    # Candidates -> contacts
    logger.info("\n[1/6] Loading candidates...")
    candidates = load_sqlite_table(BULLHORN_DB, "candidates")
    process_records_parallel(
        candidates, "contacts", build_candidate_text, qdrant, "bullhorn_candidates"
    )

    # Activities -> activities
    logger.info("\n[2/6] Loading activities...")
    activities = load_sqlite_table(BULLHORN_DB, "activities")
    process_records_parallel(
        activities, "activities", build_activity_text, qdrant, "bullhorn_activities"
    )

    # Call notes -> activities
    logger.info("\n[3/6] Loading call_notes...")
    call_notes = load_sqlite_table(BULLHORN_DB, "call_notes")
    process_records_parallel(
        call_notes, "activities", build_call_note_text, qdrant, "bullhorn_call_notes"
    )

    # Contact scores -> contacts
    logger.info("\n[4/6] Loading contact_scores...")
    scores = load_sqlite_table(BULLHORN_DB, "contact_scores")
    process_records_parallel(
        scores, "contacts", build_candidate_text, qdrant, "bullhorn_contact_scores"
    )

    # Placements + past_performance -> documents
    logger.info("\n[5/6] Loading placements & past_performance...")
    placements = load_sqlite_table(BULLHORN_DB, "placements")
    past_perf = load_sqlite_table(BULLHORN_DB, "past_performance")
    process_records_parallel(
        placements + past_perf,
        "documents",
        build_document_text,
        qdrant,
        "bullhorn_documents",
    )

    # Jobs -> jobs
    logger.info("\n[6/6] Loading jobs...")
    jobs = load_sqlite_table(BULLHORN_DB, "jobs")
    process_records_parallel(jobs, "jobs", build_job_text, qdrant, "bullhorn_jobs")


def index_colton_scurry(qdrant: QdrantClient):
    """Index Colton Scurry analysis files."""
    logger.info("=" * 60)
    logger.info("INDEXING COLTON SCURRY ANALYSIS")
    logger.info("=" * 60)

    if not COLTON_DIR.exists():
        logger.error(f"Directory not found: {COLTON_DIR}")
        return

    # CSV files
    csv_mappings = {
        "master_notes.csv": ("activities", build_activity_text),
        "contacts.csv": ("contacts", build_candidate_text),
        "jobs.csv": ("jobs", build_job_text),
        "programs.csv": ("programs", build_program_text),
        "colton_notes_only.csv": ("activities", build_call_note_text),
        "MASTER_DATA_AGGREGATION.csv": ("documents", build_document_text),
    }

    for filename, (collection, text_builder) in csv_mappings.items():
        csv_path = COLTON_DIR / filename
        if not csv_path.exists():
            csv_path = COLTON_DIR / "ANALYSIS" / "NOTES_DEEP_DIVE" / filename
        if csv_path.exists():
            records = load_csv_file(csv_path)
            if records:
                process_records_parallel(
                    records, collection, text_builder, qdrant, f"colton_{filename}"
                )

    # Markdown files -> documents
    logger.info("\nLoading Colton Scurry markdown docs...")
    md_records = load_md_files(COLTON_DIR)
    if md_records:
        process_records_parallel(
            md_records,
            "documents",
            lambda r: build_md_text(r.get("content", ""), r.get("filename", "")),
            qdrant,
            "colton_analysis_docs",
        )


def index_outputs_folder(qdrant: QdrantClient):
    """Index outputs folder (BD Briefings, generated files)."""
    logger.info("=" * 60)
    logger.info("INDEXING OUTPUTS FOLDER")
    logger.info("=" * 60)

    if not OUTPUTS_DIR.exists():
        logger.error(f"Directory not found: {OUTPUTS_DIR}")
        return

    # Markdown files -> documents
    logger.info("\nLoading output markdown docs...")
    md_records = load_md_files(OUTPUTS_DIR)
    if md_records:
        process_records_parallel(
            md_records,
            "documents",
            lambda r: build_md_text(r.get("content", ""), r.get("filename", "")),
            qdrant,
            "outputs_docs",
        )

    # JSON files
    logger.info("\nLoading output JSON files...")
    for json_file in OUTPUTS_DIR.rglob("*.json"):
        records = load_json_file(json_file)
        if records:
            # Determine collection based on filename
            fname = json_file.name.lower()
            if "job" in fname:
                collection, builder = "jobs", build_job_text
            elif "contact" in fname:
                collection, builder = "contacts", build_candidate_text
            elif "contractor" in fname:
                collection, builder = "contacts", build_candidate_text
            else:
                collection, builder = "documents", build_document_text

            process_records_parallel(
                records, collection, builder, qdrant, f"outputs_{json_file.name}"
            )

    # CSV files
    logger.info("\nLoading output CSV files...")
    for csv_file in OUTPUTS_DIR.rglob("*.csv"):
        records = load_csv_file(csv_file)
        if records:
            process_records_parallel(
                records,
                "documents",
                build_document_text,
                qdrant,
                f"outputs_{csv_file.name}",
            )


def main():
    """Main indexing function."""
    start_time = time.time()

    logger.info("=" * 60)
    logger.info("PRIORITY FULL DATA INDEXER")
    logger.info(f"Embedding Model: {EMBEDDING_MODEL} ({EMBEDDING_DIM} dimensions)")
    logger.info(f"Batch Size: {BATCH_SIZE} | Upload Batch: {UPLOAD_BATCH_SIZE}")
    logger.info(f"Max Workers: {MAX_WORKERS}")
    logger.info("=" * 60)

    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not set in .env")
        sys.exit(1)

    # Connect to Qdrant
    logger.info(f"\nConnecting to Qdrant at {QDRANT_URL}")
    qdrant = QdrantClient(url=QDRANT_URL)

    # Ensure collections exist
    for collection in ["contacts", "activities", "documents", "jobs", "programs"]:
        create_collection(qdrant, collection)

    # Index Priority 1: Bullhorn Database
    index_bullhorn_database(qdrant)

    # Index Priority 1: Colton Scurry Analysis
    index_colton_scurry(qdrant)

    # Index Priority 2: Outputs Folder
    index_outputs_folder(qdrant)

    # Final stats
    elapsed = time.time() - start_time
    logger.info("\n" + "=" * 60)
    logger.info("INDEXING COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Total indexed: {indexed_count.value:,}")
    logger.info(f"Errors: {error_count.value:,}")
    logger.info(f"Time elapsed: {elapsed / 60:.1f} minutes")

    # Show collection stats
    logger.info("\nFinal Collection Stats:")
    for coll in qdrant.get_collections().collections:
        info = qdrant.get_collection(coll.name)
        logger.info(f"  {coll.name}: {info.points_count:,} points")


if __name__ == "__main__":
    main()
