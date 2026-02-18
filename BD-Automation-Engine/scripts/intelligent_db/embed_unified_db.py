"""
Embed unified database records into Qdrant vector store.
Reuses BDKnowledgeStore from Engine8_Knowledge for embedding and storage.
"""
import json
import os
import sqlite3
import sys
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

DB_PATH = PROJECT_ROOT / "data" / "unified_federal_contracts.db"
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
BATCH_SIZE = 100

logger = logging.getLogger(__name__)

# What to embed per collection
COLLECTION_QUERIES = {
    "contacts": {
        "query": """
            SELECT id, full_name, first_name, last_name, title, company,
                   email, program, tier, bd_priority, notes, linkedin,
                   inferred_role_level, clearances, source_db
            FROM contacts WHERE full_name IS NOT NULL
        """,
        "text_fn": lambda r: " | ".join(filter(None, [
            r["full_name"], r["title"], r["company"], r["program"], r["notes"]
        ])),
        "payload_keys": ["full_name", "title", "company", "tier", "bd_priority",
                         "program", "email", "inferred_role_level", "source_db"],
    },
    "programs": {
        "query": """
            SELECT id, program_name, acronym, agency_owner, prime_contractor,
                   total_contract_value, description, technical_stack,
                   keywords_signals, functional_areas, clearance_requirements,
                   priority_level, domain_tags
            FROM programs WHERE program_name IS NOT NULL
        """,
        "text_fn": lambda r: " | ".join(filter(None, [
            r["program_name"], r["acronym"], r["agency_owner"], r["prime_contractor"],
            r["description"], r["technical_stack"], r["keywords_signals"]
        ])),
        "payload_keys": ["program_name", "acronym", "agency_owner", "prime_contractor",
                         "total_contract_value", "priority_level", "clearance_requirements",
                         "domain_tags"],
    },
    "activities": {
        "query": """
            SELECT id, activity_type, action, about, activity_date, actor,
                   note_text, comments, programs_mentioned, primes_mentioned,
                   sentiment_score, has_hiring_signal, priority
            FROM activities WHERE note_text IS NOT NULL AND TRIM(note_text) != ''
        """,
        "text_fn": lambda r: " | ".join(filter(None, [
            r["about"], r["action"], r["note_text"], r["comments"]
        ])),
        "payload_keys": ["activity_type", "about", "activity_date", "actor",
                         "programs_mentioned", "sentiment_score", "has_hiring_signal", "priority"],
    },
    "intelligence_reports": {
        "query": """
            SELECT id, intel_type, program_name, company_name, piid,
                   bd_score, description, narrative, awarding_agency,
                   lifecycle_phase, priority_tier, competitors
            FROM intelligence WHERE description IS NOT NULL AND TRIM(description) != ''
        """,
        "text_fn": lambda r: " | ".join(filter(None, [
            r["program_name"], r["company_name"], r["description"],
            r["narrative"], r["piid"]
        ])),
        "payload_keys": ["intel_type", "program_name", "company_name", "bd_score",
                         "awarding_agency", "lifecycle_phase", "priority_tier"],
    },
    "federal_contracts": {
        "query": """
            SELECT id, piid, program_name, recipient_name, award_amount,
                   description, awarding_agency, naics_code, psc_code,
                   start_date, end_date, fiscal_year
            FROM contracts WHERE description IS NOT NULL AND TRIM(description) != ''
        """,
        "text_fn": lambda r: " | ".join(filter(None, [
            r["program_name"], r["recipient_name"], r["description"],
            r["awarding_agency"], r["piid"]
        ])),
        "payload_keys": ["piid", "program_name", "recipient_name", "award_amount",
                         "awarding_agency", "naics_code", "fiscal_year"],
    },
}


def embed_collection(store, conn, collection_name, config):
    """Embed records for a single collection."""
    cursor = conn.cursor()
    cursor.row_factory = sqlite3.Row

    try:
        cursor.execute(config["query"])
    except sqlite3.OperationalError as e:
        logger.warning(f"  {collection_name}: query failed ({e}), skipping")
        return 0

    rows = cursor.fetchall()
    if not rows:
        logger.info(f"  {collection_name}: no records to embed")
        return 0

    print(f"  {collection_name}: embedding {len(rows)} records...")

    embedded = 0
    batch_texts = []
    batch_ids = []
    batch_payloads = []

    for row in rows:
        row_dict = dict(row)
        text = config["text_fn"](row_dict)
        if not text or len(text.strip()) < 10:
            continue

        payload = {k: row_dict.get(k) for k in config["payload_keys"]}
        payload = {k: v for k, v in payload.items() if v is not None}
        payload["_text"] = text[:500]  # Store truncated text for debugging

        batch_texts.append(text)
        batch_ids.append(row_dict["id"])
        batch_payloads.append(payload)

        if len(batch_texts) >= BATCH_SIZE:
            count = _upsert_batch(store, collection_name, batch_texts, batch_ids, batch_payloads)
            embedded += count
            batch_texts, batch_ids, batch_payloads = [], [], []

    # Final batch
    if batch_texts:
        count = _upsert_batch(store, collection_name, batch_texts, batch_ids, batch_payloads)
        embedded += count

    print(f"  {collection_name}: {embedded} vectors upserted")
    return embedded


def _upsert_batch(store, collection_name, texts, ids, payloads):
    """Embed and upsert a batch of texts."""
    try:
        from qdrant_client.models import PointStruct

        # Get embeddings
        response = store.openai_client.embeddings.create(
            model=store.model_name,
            input=texts,
        )
        vectors = [item.embedding for item in response.data]

        # Build points
        points = [
            PointStruct(id=uid, vector=vec, payload=pay)
            for uid, vec, pay in zip(ids, vectors, payloads)
        ]

        # Upsert - use string IDs by hashing
        import hashlib
        points_with_int_ids = []
        for uid, vec, pay in zip(ids, vectors, payloads):
            int_id = int(hashlib.sha256(uid.encode()).hexdigest()[:15], 16)
            pay["_original_id"] = uid
            points_with_int_ids.append(PointStruct(id=int_id, vector=vec, payload=pay))

        store.client.upsert(
            collection_name=collection_name,
            points=points_with_int_ids,
        )
        return len(points_with_int_ids)
    except Exception as e:
        logger.error(f"  Batch upsert failed for {collection_name}: {e}")
        return 0


def run(db_path=None, qdrant_url=None):
    """Run embedding pipeline."""
    db_path = db_path or DB_PATH
    qdrant_url = qdrant_url or QDRANT_URL

    print("Unified DB Embedding Pipeline")
    print(f"  Database: {db_path}")
    print(f"  Qdrant: {qdrant_url}")

    try:
        from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore
    except ImportError:
        print("  ERROR: Could not import BDKnowledgeStore. Ensure Engine8_Knowledge is available.")
        return

    store = BDKnowledgeStore(url=qdrant_url)
    store.initialize_collections(force_recreate=False)

    conn = sqlite3.connect(str(db_path))
    total = 0

    try:
        for coll_name, config in COLLECTION_QUERIES.items():
            count = embed_collection(store, conn, coll_name, config)
            total += count
    finally:
        conn.close()

    print(f"  Total vectors embedded: {total}")


if __name__ == "__main__":
    run()
