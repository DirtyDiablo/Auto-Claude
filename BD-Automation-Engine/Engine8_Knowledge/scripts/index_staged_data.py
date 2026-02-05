#!/usr/bin/env python3
"""
Index all staged data from Data-Scraper and N8N-Builder into Qdrant.

Handles:
- data/from_data_scraper/*.csv, *.json
- data/from_n8n_builder/contacts/*.csv
- data/from_n8n_builder/documents/processed_docs.json
- data/from_n8n_builder/bullhorn/*.csv, *.json

Dedup strategy: deterministic UUIDs from content keys.
For contacts: UUID from normalized(name + company).
"""

import os
import sys
import csv
import json
import uuid
import time
import logging
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# Setup
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(str(PROJECT_ROOT))

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from dotenv import load_dotenv
# Load .env LAST so it wins (has valid OpenAI key)
load_dotenv(PROJECT_ROOT / "BD-Automation-Engine.env")
load_dotenv(PROJECT_ROOT / ".env", override=True)

import openai
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger('StagedDataIndexer')

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
NAMESPACE = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')

DS_DIR = PROJECT_ROOT / "data" / "from_data_scraper"
N8N_DIR = PROJECT_ROOT / "data" / "from_n8n_builder"

# Track stats
stats = defaultdict(lambda: {"indexed": 0, "skipped": 0, "errors": 0})

oai_client = openai.OpenAI(api_key=OPENAI_API_KEY)


# ── File-to-Collection mapping ────────────────────────────────────────────

CONTACTS_FILES = [
    "CONTACTS_INTELLIGENCE.csv",
    "CONTACT_INTELLIGENCE_DETAILED.csv",
    "bullhorn_contacts_master.csv",
    "PHASE1_FAIR_GAME_CONTACTS.csv",
    "PHASE1_CLAIMED_CONTACTS.csv",
    "ORG_CHART_DATA.csv",
    "colton_scurry_contacts.csv",
    "colton_scurry_contact_handoff.csv",
    "ZOOMINFO_L3HARRIS.csv",
]

JOBS_FILES = [
    "JOBS_ENRICHED.csv",
    "JOBS_INTELLIGENCE_MAPPED.csv",
    "bd_top_program_jobs_detail.csv",
    "colton_scurry_jobs.csv",
    "hub_jobs_2026-01-26.json",
    "standardized_jobs_2026-01-26.json",
]

PROGRAMS_FILES = [
    "MASTER_PROGRAMS_ENRICHED.csv",
    "PROGRAMS_CLEAN.csv",
    "PROGRAMS_FROM_NOTES.csv",
    "GAP_PROGRAMS.csv",
    "PROGRAM_INTELLIGENCE_DETAILED.csv",
]

# Everything else goes to documents
SKIP_FILES = [
    "bullhorn_programs_master.csv",   # dupe of MASTER_PROGRAMS_ENRICHED
    "bullhorn_primes_master.csv",     # dupe of MASTER_PRIMES_ENRICHED
]


# ── Helpers ───────────────────────────────────────────────────────────────

def make_id(collection: str, *parts) -> str:
    """Deterministic UUID from collection + key parts."""
    content = f"{collection}:" + "|".join(str(p).strip().lower() for p in parts if p)
    return str(uuid.uuid5(NAMESPACE, content))


EMBED_BATCH_SIZE = 200        # ~100K tokens/batch, fits 1M TPM with pacing
UPSERT_BATCH_SIZE = 500       # Qdrant comfortable batch size
FILE_WORKERS = 1              # Sequential files (API is the bottleneck)
BATCH_SLEEP = 3               # Seconds between embed batches (pace TPM)


def _embed_one_batch(batch_texts: list[str]) -> list:
    """Embed a single batch with retries + adaptive splitting."""
    truncated = [t[:8000] for t in batch_texts]

    for attempt in range(5):
        try:
            resp = oai_client.embeddings.create(model=EMBEDDING_MODEL, input=truncated)
            return [d.embedding for d in resp.data]
        except openai.BadRequestError as e:
            # Token limit exceeded - split batch in half and recurse
            if 'max_tokens_per_request' in str(e) and len(truncated) > 10:
                mid = len(truncated) // 2
                logger.info("Splitting batch %d -> %d + %d (token limit)",
                            len(truncated), mid, len(truncated) - mid)
                left = _embed_one_batch(batch_texts[:mid])
                time.sleep(1)
                right = _embed_one_batch(batch_texts[mid:])
                return left + right
            logger.error("BadRequest (not splittable): %s", e)
            return [None] * len(truncated)
        except openai.RateLimitError as e:
            wait = min(30, 5 * (attempt + 1))
            logger.info("Rate limited, waiting %ds (attempt %d/5)...", wait, attempt + 1)
            time.sleep(wait)
        except Exception as e:
            if attempt < 4:
                wait = 2 ** (attempt + 1)
                logger.warning("Embed retry %d/5 after %ds: %s", attempt + 1, wait, e)
                time.sleep(wait)
            else:
                logger.error("Embed failed after 5 attempts (%d texts): %s",
                             len(truncated), e)
                return [None] * len(truncated)
    return [None] * len(truncated)


def batch_embed(texts: list[str], batch_size: int = EMBED_BATCH_SIZE) -> list[list[float]]:
    """Batch-embed texts via OpenAI API. Sequential with large batches for max TPM."""
    if not texts:
        return []

    all_embeddings = []
    total_batches = (len(texts) + batch_size - 1) // batch_size
    for batch_num, i in enumerate(range(0, len(texts), batch_size)):
        batch = texts[i:i + batch_size]
        result = _embed_one_batch(batch)
        all_embeddings.extend(result)
        done = min(i + batch_size, len(texts))
        if done % 1000 < batch_size or done == len(texts):
            logger.info("  Embedded %d/%d texts (batch %d/%d)",
                        done, len(texts), batch_num + 1, total_batches)
        # Pace between batches to stay under TPM limit
        if batch_num < total_batches - 1:
            time.sleep(BATCH_SLEEP)
    return all_embeddings


def read_csv_rows(filepath: Path) -> list[dict]:
    """Read CSV file into list of dicts."""
    rows = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Clean BOM from first key
                cleaned = {}
                for k, v in row.items():
                    clean_k = k.lstrip('\ufeff').strip('"').strip()
                    cleaned[clean_k] = (v or '').strip()
                rows.append(cleaned)
    except Exception as e:
        logger.error("Failed to read %s: %s", filepath.name, e)
    return rows


def make_text_from_row(row: dict, key_fields: list[str] = None) -> str:
    """Generate embedding text from row fields."""
    if key_fields:
        parts = [f"{k}: {row.get(k, '')}" for k in key_fields if row.get(k)]
    else:
        parts = [f"{k}: {v}" for k, v in row.items()
                 if v and not k.startswith('_') and len(str(v)) < 2000]
    return " | ".join(parts)[:8000]


def upsert_batch(client: QdrantClient, collection: str,
                 points: list[PointStruct]):
    """Upsert a batch of points to Qdrant."""
    if not points:
        return
    try:
        client.upsert(collection_name=collection, points=points)
        stats[collection]["indexed"] += len(points)
    except Exception as e:
        logger.error("Upsert failed for %s: %s", collection, e)
        stats[collection]["errors"] += len(points)


def ensure_collection(client: QdrantClient, name: str):
    """Create collection if it doesn't exist."""
    existing = [c.name for c in client.get_collections().collections]
    if name not in existing:
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE)
        )
        logger.info("Created collection: %s", name)


# ── Indexers ──────────────────────────────────────────────────────────────

def index_csv_to_collection(client: QdrantClient, filepath: Path,
                            collection: str, id_fields: list[str],
                            key_fields: list[str] = None,
                            source_type: str = None):
    """Index a CSV file into a Qdrant collection."""
    rows = read_csv_rows(filepath)
    if not rows:
        logger.warning("No rows in %s", filepath.name)
        return

    logger.info("Indexing %s -> %s (%d rows)", filepath.name, collection, len(rows))

    # Prepare texts and IDs
    texts = []
    ids = []
    payloads = []

    for row in rows:
        # Generate ID from key fields
        id_parts = [row.get(f, '') for f in id_fields]
        if not any(id_parts):
            # Fallback: use all row content for ID
            id_parts = [filepath.name, json.dumps(row, sort_keys=True)[:200]]

        point_id = make_id(collection, *id_parts)
        text = make_text_from_row(row, key_fields)
        if not text.strip():
            stats[collection]["skipped"] += 1
            continue

        payload = {
            **row,
            "_source": filepath.name,
            "_indexed_at": datetime.now().isoformat(),
            "_embedding_model": EMBEDDING_MODEL,
        }
        if source_type:
            payload["_source_type"] = source_type

        texts.append(text)
        ids.append(point_id)
        payloads.append(payload)

    if not texts:
        return

    # Batch embed
    embeddings = batch_embed(texts)

    # Build and upsert points
    batch = []
    for point_id, embedding, payload in zip(ids, embeddings, payloads):
        if embedding is None:
            stats[collection]["errors"] += 1
            continue
        batch.append(PointStruct(id=point_id, vector=embedding, payload=payload))
        if len(batch) >= UPSERT_BATCH_SIZE:
            upsert_batch(client, collection, batch)
            batch = []

    upsert_batch(client, collection, batch)
    logger.info("  Done: %s -> %s (+%d)", filepath.name, collection,
                len([e for e in embeddings if e is not None]))


def index_json_to_collection(client: QdrantClient, filepath: Path,
                             collection: str, id_fields: list[str],
                             key_fields: list[str] = None,
                             source_type: str = None):
    """Index a JSON file (array or dict) into a Qdrant collection."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        logger.error("Failed to read %s: %s", filepath.name, e)
        return

    if isinstance(data, dict):
        # For processed_docs.json: dict of path->doc
        records = []
        for key, val in data.items():
            if isinstance(val, dict):
                val["_doc_key"] = key
                records.append(val)
        data = records
    elif not isinstance(data, list):
        logger.warning("Unexpected JSON format in %s", filepath.name)
        return

    logger.info("Indexing %s -> %s (%d records)", filepath.name, collection, len(data))

    texts, ids, payloads = [], [], []
    for record in data:
        if not isinstance(record, dict):
            continue

        id_parts = [record.get(f, '') for f in id_fields]
        if not any(id_parts):
            id_parts = [filepath.name, json.dumps(record, sort_keys=True)[:200]]

        point_id = make_id(collection, *id_parts)

        if key_fields:
            text = " | ".join(f"{k}: {record.get(k, '')}" for k in key_fields if record.get(k))
        else:
            text = " | ".join(f"{k}: {str(v)[:500]}" for k, v in record.items()
                              if v and not k.startswith('_') and k != 'content')
            # Add content last (it can be long)
            content = record.get('content', '')
            if content:
                text = text + " | " + str(content)[:4000]

        text = text[:8000]
        if not text.strip():
            stats[collection]["skipped"] += 1
            continue

        payload = {}
        for k, v in record.items():
            if isinstance(v, (str, int, float, bool)) or v is None:
                payload[k] = v
            elif isinstance(v, (list, dict)):
                payload[k] = json.dumps(v)[:1000]
        payload["_source"] = filepath.name
        payload["_indexed_at"] = datetime.now().isoformat()
        payload["_embedding_model"] = EMBEDDING_MODEL
        if source_type:
            payload["_source_type"] = source_type

        texts.append(text)
        ids.append(point_id)
        payloads.append(payload)

    if not texts:
        return

    embeddings = batch_embed(texts)

    batch = []
    for point_id, embedding, payload in zip(ids, embeddings, payloads):
        if embedding is None:
            stats[collection]["errors"] += 1
            continue
        batch.append(PointStruct(id=point_id, vector=embedding, payload=payload))
        if len(batch) >= UPSERT_BATCH_SIZE:
            upsert_batch(client, collection, batch)
            batch = []

    upsert_batch(client, collection, batch)
    logger.info("  Done: %s -> %s (+%d)", filepath.name, collection,
                len([e for e in embeddings if e is not None]))


def parallel_index_csvs(client, filepaths, collection, id_fields,
                        key_fields=None, source_type=None):
    """Index multiple CSV files concurrently."""
    existing = [fp for fp in filepaths if fp.exists()]
    if not existing:
        return
    if len(existing) == 1:
        index_csv_to_collection(client, existing[0], collection,
                                id_fields, key_fields, source_type)
        return

    with ThreadPoolExecutor(max_workers=FILE_WORKERS) as executor:
        futures = {
            executor.submit(index_csv_to_collection, client, fp, collection,
                            id_fields, key_fields, source_type): fp
            for fp in existing
        }
        for future in as_completed(futures):
            fp = futures[future]
            try:
                future.result()
            except Exception as e:
                logger.error("Failed indexing %s: %s", fp.name, e)


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("STAGED DATA INDEXER")
    print(f"Qdrant: {QDRANT_URL}")
    print(f"Embedding: {EMBEDDING_MODEL} ({EMBEDDING_DIM}d)")
    print("=" * 70)

    client = QdrantClient(url=QDRANT_URL, timeout=600)

    # Ensure all collections exist
    for coll in ["contacts", "programs", "jobs", "documents", "activities"]:
        ensure_collection(client, coll)

    # Get baseline counts
    baseline = {}
    for coll in ["contacts", "programs", "jobs", "documents", "activities"]:
        info = client.get_collection(coll)
        baseline[coll] = info.points_count
        print(f"  Baseline {coll}: {info.points_count:,}")
    print()

    # ── PHASE 1: Contracts & Opportunities -> documents ────────────────
    print("\n" + "=" * 50)
    print("PHASE 1: CONTRACTS & OPPORTUNITIES -> documents")
    print("=" * 50)

    contract_files = [
        "FULL_OPPORTUNITIES.csv",
        "FULL_PROGRAM_CONTRACTS.csv",
        "MASTER_CONTRACTS_COMBINED.csv",
        "PHASE2_PROGRAM_PIIDS_FULL.csv",
        "PHASE5_RECENT_ACTIVE_CONTRACTS.csv",
        "db1_dod_prime_contracts_100m.csv",
        "db2_subawards_tango.csv",
        "db3_dod_it_opportunities.csv",
        "db3_dod_opportunities_all.csv",
        "db3_dod_solicitations.csv",
        "phase3_opportunities_tango.csv",
        "phase3_solicitations_only.csv",
        "L3Harris_GBS_PROGRAM_CONTRACTS.csv",
        "L3Harris_SATCOM_RF_CONTRACTS.csv",
        "navy_subaward_N00019.csv",
        "sam_data_elements.csv",
        "size_billion_1b_5b.csv",
        "size_giant_5b_10b.csv",
        "size_large_500m_1b.csv",
        "size_mega_10b_plus.csv",
        "agency_Department_of_Defense.csv",
    ]

    parallel_index_csvs(
        client, [DS_DIR / f for f in contract_files], "documents",
        id_fields=["piid", "notice_id", "contract_id", "award_id", "title"],
        source_type="contract"
    )

    # ── PHASE 2: BD Targets -> documents ──────────────────────────────
    print("\n" + "=" * 50)
    print("PHASE 2: BD TARGETS -> documents")
    print("=" * 50)

    target_files = [
        "master_bd_targets.csv",
        "master_bd_targets_contract_enriched.csv",
        "master_bd_targets_fpds_enriched.csv",
        "db6_bd_targets_all.csv",
        "db6_bd_targets_priority.csv",
        "tier1_high_priority_targets.csv",
        "tier2_medium_priority_targets.csv",
        "tier3_standard_targets.csv",
        "it_services_all_targets.csv",
    ]

    parallel_index_csvs(
        client, [DS_DIR / f for f in target_files], "documents",
        id_fields=["award_id", "contract_id", "piid", "recipient", "title"],
        source_type="bd_target"
    )

    # ── PHASE 3: Primes Intelligence -> documents ─────────────────────
    print("\n" + "=" * 50)
    print("PHASE 3: PRIMES INTELLIGENCE -> documents")
    print("=" * 50)

    prime_files = [
        "MASTER_PRIMES_ENRICHED.csv",
        "PRIMES_FROM_NOTES.csv",
        "PRIME_INTELLIGENCE_DETAILED.csv",
        "FULL_PRIME_ENRICHMENT.csv",
        "primes_usaspending_enriched.csv",
        "high_subcontract_activity.csv",
    ]

    parallel_index_csvs(
        client, [DS_DIR / f for f in prime_files], "documents",
        id_fields=["prime_name", "recipient", "company", "name", "title"],
        source_type="prime_intel"
    )

    # ── PHASE 4: Contacts from Data-Scraper -> contacts (dedup) ───────
    print("\n" + "=" * 50)
    print("PHASE 4: CONTACTS (Data-Scraper) -> contacts")
    print("=" * 50)

    parallel_index_csvs(
        client, [DS_DIR / f for f in CONTACTS_FILES], "contacts",
        id_fields=["contact_name", "name", "first_name", "company",
                   "email", "linkedin"],
        key_fields=["contact_name", "name", "first_name", "last_name",
                    "title", "company", "program", "tier", "clearance",
                    "email", "phone", "linkedin", "programs", "primes"],
        source_type="data_scraper"
    )

    # ── PHASE 5: Contacts from N8N -> contacts (enriched only, dedup) ─
    print("\n" + "=" * 50)
    print("PHASE 5: CONTACTS (N8N-Builder) -> contacts")
    print("=" * 50)

    n8n_contacts_dir = N8N_DIR / "contacts"
    if n8n_contacts_dir.exists():
        # Prefer enriched files; skip base if enriched exists
        enriched = {f.name.replace("_Enriched", ""): f
                    for f in n8n_contacts_dir.glob("*_Enriched.csv")}
        base_files = {f.name: f for f in n8n_contacts_dir.glob("*.csv")
                      if "_Enriched" not in f.name
                      and f.name != "Contacts_TEMPLATE.csv"}

        # Index enriched versions
        for fname, fp in sorted(enriched.items()):
            index_csv_to_collection(
                client, fp, "contacts",
                id_fields=["Full Name", "Name", "First Name", "name",
                           "Company", "company", "Email", "email", "LinkedIn"],
                key_fields=["Full Name", "Name", "First Name", "Last Name",
                            "Title", "Company", "Location", "Email",
                            "LinkedIn", "Programs", "Clearance",
                            "name", "title", "company"],
                source_type="n8n_contacts"
            )

        # Index base files only if no enriched counterpart
        for fname, fp in sorted(base_files.items()):
            if fname not in enriched:
                index_csv_to_collection(
                    client, fp, "contacts",
                    id_fields=["Full Name", "Name", "First Name", "name",
                               "Company", "company", "Email", "email"],
                    key_fields=["Full Name", "Name", "First Name", "Last Name",
                                "Title", "Company", "Location", "Email",
                                "LinkedIn", "name", "title", "company"],
                    source_type="n8n_contacts"
                )

    # ── PHASE 6: Jobs -> jobs ─────────────────────────────────────────
    print("\n" + "=" * 50)
    print("PHASE 6: JOBS -> jobs")
    print("=" * 50)

    # Jobs: split CSV vs JSON, then parallel
    jobs_csvs = [DS_DIR / f for f in JOBS_FILES if f.endswith('.csv')]
    jobs_jsons = [DS_DIR / f for f in JOBS_FILES if f.endswith('.json')]

    def _index_jobs():
        parallel_index_csvs(
            client, jobs_csvs, "jobs",
            id_fields=["title", "job_number", "job_id", "url",
                       "Job Title", "Job Number"],
            key_fields=["title", "job_number", "owner", "contact",
                        "employment_type", "status", "pay_rate",
                        "client_bill_rate", "company", "location",
                        "Job Title", "Job Location", "Security Clearance"],
            source_type="data_scraper"
        )
        for fp in jobs_jsons:
            if fp.exists():
                index_json_to_collection(
                    client, fp, "jobs",
                    id_fields=["title", "job_number", "job_id", "url"],
                    key_fields=["title", "company", "location", "clearance",
                                "employment_type", "pay_rate", "program"],
                    source_type="data_scraper"
                )
    _index_jobs()

    # ── PHASE 7: Programs -> programs ─────────────────────────────────
    print("\n" + "=" * 50)
    print("PHASE 7: PROGRAMS -> programs")
    print("=" * 50)

    parallel_index_csvs(
        client, [DS_DIR / f for f in PROGRAMS_FILES], "programs",
        id_fields=["Program Name", "program_name", "Acronym", "name"],
        key_fields=["Program Name", "Acronym", "Agency", "Agency Owner",
                    "Prime Contractor", "Contract Value", "Contract Number",
                    "Clearance Requirements", "Keywords/Signals",
                    "program_name", "agency", "prime"],
        source_type="data_scraper"
    )

    # ── PHASE 8: N8N Processed Documents -> documents ─────────────────
    print("\n" + "=" * 50)
    print("PHASE 8: N8N DOCUMENTS -> documents")
    print("=" * 50)

    docs_file = N8N_DIR / "documents" / "processed_docs.json"
    if docs_file.exists():
        index_json_to_collection(
            client, docs_file, "documents",
            id_fields=["_doc_key", "path", "title"],
            key_fields=["title", "file_type", "content"],
            source_type="n8n_processed_docs"
        )

    # ── PHASE 9: N8N Bullhorn Activity -> activities ──────────────────
    print("\n" + "=" * 50)
    print("PHASE 9: N8N BULLHORN -> activities")
    print("=" * 50)

    bullhorn_dir = N8N_DIR / "bullhorn"
    if bullhorn_dir.exists():
        # Index JSON summaries first
        for fp in sorted(bullhorn_dir.glob("*.json")):
            index_json_to_collection(
                client, fp, "activities",
                id_fields=["title", "name", "type"],
                source_type="n8n_bullhorn"
            )
        # Index CSV data files in parallel (skip very small ones)
        bh_csvs = [fp for fp in sorted(bullhorn_dir.glob("*.csv"))
                    if fp.stat().st_size > 100]
        parallel_index_csvs(
            client, bh_csvs, "activities",
            id_fields=["Date", "date", "Name", "name",
                       "Type", "Candidate", "Job Title"],
            source_type="n8n_bullhorn"
        )

    # ── FINAL REPORT ──────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("INDEXING COMPLETE")
    print("=" * 70)

    print(f"\n{'Collection':<15} {'Before':>10} {'After':>10} {'Net':>10} {'Errors':>8}")
    print("-" * 58)

    for coll in ["contacts", "programs", "jobs", "documents", "activities"]:
        info = client.get_collection(coll)
        after = info.points_count
        before = baseline[coll]
        net = after - before
        errs = stats[coll]["errors"]
        print(f"{coll:<15} {before:>10,} {after:>10,} {'+' if net >= 0 else ''}{net:>9,} {errs:>8}")

    print()
    for coll, s in stats.items():
        print(f"  {coll}: indexed={s['indexed']:,}, skipped={s['skipped']:,}, errors={s['errors']:,}")


if __name__ == "__main__":
    start = time.time()
    main()
    elapsed = time.time() - start
    print(f"\nTotal time: {elapsed/60:.1f} minutes")
