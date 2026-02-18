#!/usr/bin/env python3
"""
Enrich Qdrant vectors with metadata tags + index new staged analytical files.

Three phases in one pass:
  Phase A: Enrich ALL existing vectors with intel metadata tags (+ fix any zero vectors)
  Phase B: Index newly staged files from Terminals B & C
  Phase C: Run 6 benchmark queries for search quality verification

Usage:
  python Engine8_Knowledge/scripts/enrich_reindex_all.py              # All phases
  python Engine8_Knowledge/scripts/enrich_reindex_all.py --phase a    # Enrich only
  python Engine8_Knowledge/scripts/enrich_reindex_all.py --phase b    # Index only
  python Engine8_Knowledge/scripts/enrich_reindex_all.py --phase c    # Benchmark only
  python Engine8_Knowledge/scripts/enrich_reindex_all.py --dry-run    # Report only
"""

import os
import sys
import csv
import json
import uuid
import time
import re
import logging
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# ── Setup ────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(str(PROJECT_ROOT))

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / "BD-Automation-Engine.env")
load_dotenv(PROJECT_ROOT / ".env", override=True)

import openai
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from utils.llm_retry import openai_retry

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("EnrichReindex")

# Suppress noisy HTTP logging from httpx/httpcore
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

# ── Constants ────────────────────────────────────────────────────────────
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

EMBED_BATCH_SIZE = 200
UPSERT_BATCH_SIZE = 500
BATCH_SLEEP = 3

# Post-reorganization: data is now under data/enriched/, data/reference/, etc.
# Keep backward-compat aliases for any remaining references
DS_DIR = PROJECT_ROOT / "data" / "enriched" / "intelligence"
N8N_OUTPUTS_DIR = PROJECT_ROOT / "data" / "reference" / "mcp_extracts"
REGISTRY_PATH = (
    PROJECT_ROOT / "Engine8_Knowledge" / "data" / "bd_file_metadata_registry.json"
)

COLLECTIONS = ["contacts", "programs", "jobs", "documents", "activities"]

oai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
stats = defaultdict(
    lambda: {
        "indexed": 0,
        "skipped": 0,
        "errors": 0,
        "metadata_added": 0,
        "zeros_fixed": 0,
    }
)


# ══════════════════════════════════════════════════════════════════════════
# CORE EMBEDDING FUNCTIONS (proven from index_staged_data.py)
# ══════════════════════════════════════════════════════════════════════════


def make_id(collection: str, *parts) -> str:
    content = f"{collection}:" + "|".join(str(p).strip().lower() for p in parts if p)
    return str(uuid.uuid5(NAMESPACE, content))


@openai_retry
def _embed_one_batch(batch_texts: list[str]) -> list:
    truncated = [t[:8000] for t in batch_texts]
    for attempt in range(5):
        try:
            resp = oai_client.embeddings.create(model=EMBEDDING_MODEL, input=truncated)
            return [d.embedding for d in resp.data]
        except openai.BadRequestError as e:
            if "max_tokens_per_request" in str(e) and len(truncated) > 10:
                mid = len(truncated) // 2
                logger.info(
                    "Splitting batch %d -> %d + %d (token limit)",
                    len(truncated),
                    mid,
                    len(truncated) - mid,
                )
                left = _embed_one_batch(batch_texts[:mid])
                time.sleep(1)
                right = _embed_one_batch(batch_texts[mid:])
                return left + right
            logger.error("BadRequest (not splittable): %s", e)
            return [None] * len(truncated)
        except openai.RateLimitError:
            wait = min(30, 5 * (attempt + 1))
            logger.info(
                "Rate limited, waiting %ds (attempt %d/5)...", wait, attempt + 1
            )
            time.sleep(wait)
        except Exception as e:
            if attempt < 4:
                wait = 2 ** (attempt + 1)
                logger.warning("Embed retry %d/5 after %ds: %s", attempt + 1, wait, e)
                time.sleep(wait)
            else:
                logger.error("Embed failed after 5 attempts: %s", e)
                return [None] * len(truncated)
    return [None] * len(truncated)


def batch_embed(texts: list[str], batch_size: int = EMBED_BATCH_SIZE) -> list:
    if not texts:
        return []
    all_embeddings = []
    total_batches = (len(texts) + batch_size - 1) // batch_size
    for batch_num, i in enumerate(range(0, len(texts), batch_size)):
        batch = texts[i : i + batch_size]
        result = _embed_one_batch(batch)
        all_embeddings.extend(result)
        done = min(i + batch_size, len(texts))
        if done % 1000 < batch_size or done == len(texts):
            logger.info(
                "  Embedded %d/%d texts (batch %d/%d)",
                done,
                len(texts),
                batch_num + 1,
                total_batches,
            )
        if batch_num < total_batches - 1:
            time.sleep(BATCH_SLEEP)
    return all_embeddings


def read_csv_rows(filepath: Path) -> list[dict]:
    rows = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cleaned = {}
                for k, v in row.items():
                    if k is None:
                        continue
                    clean_k = k.lstrip("\ufeff").strip('"').strip()
                    cleaned[clean_k] = (v or "").strip()
                rows.append(cleaned)
    except Exception as e:
        logger.error("Failed to read %s: %s", filepath.name, e)
    return rows


def make_text_from_row(row: dict, key_fields: list[str] = None) -> str:
    if key_fields:
        parts = [f"{k}: {row.get(k, '')}" for k in key_fields if row.get(k)]
    else:
        parts = [
            f"{k}: {v}"
            for k, v in row.items()
            if v and not k.startswith("_") and len(str(v)) < 2000
        ]
    return " | ".join(parts)[:8000]


def ensure_collection(client: QdrantClient, name: str):
    existing = [c.name for c in client.get_collections().collections]
    if name not in existing:
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )
        logger.info("Created collection: %s", name)


# ══════════════════════════════════════════════════════════════════════════
# METADATA REGISTRY
# ══════════════════════════════════════════════════════════════════════════


def load_registry() -> dict:
    if not REGISTRY_PATH.exists():
        logger.warning("Registry not found at %s", REGISTRY_PATH)
        return {}
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def build_metadata_index(registry: dict) -> tuple[dict, list]:
    """Build file-level and directory-level metadata lookup tables."""
    file_index = {}
    for f in registry.get("files", []):
        fname = f.get("filename", "").lower()
        if fname:
            file_index[fname] = {
                "intel_category": f.get("intelligence_category", []),
                "search_tags": f.get("search_tags", []),
                "priority": f.get("priority", "MEDIUM"),
                "source_project": f.get("source_project", "bd-automation-engine"),
                "qdrant_collection": f.get("qdrant_collection", "documents"),
            }

    dir_index = []
    for d in registry.get("directories", []):
        path = d.get("path", "").replace("\\", "/").rstrip("/")
        if path:
            dir_index.append(
                (
                    path.lower(),
                    {
                        "intel_category": d.get("intelligence_category", []),
                        "search_tags": d.get("search_tags", []),
                        "priority": d.get("priority", "MEDIUM"),
                        "qdrant_collection": d.get("qdrant_collection", "documents"),
                    },
                )
            )
    # Sort longest prefix first for greedy matching
    dir_index.sort(key=lambda x: -len(x[0]))

    return file_index, dir_index


# ── Filename-based heuristic metadata resolution ──

FILENAME_RULES = [
    # (pattern, intel_category, priority, source_project_hint)
    (r"_dossier\.md$", ["COMPETITIVE_INTEL", "CONTACT_INTEL"], "HIGH", "data-scraper"),
    (r"_past_performance\.md$", ["PAST_PERFORMANCE"], "HIGH", "data-scraper"),
    (r"HUMINT|humint", ["HUMINT", "BD_STRATEGY"], "CRITICAL", None),
    (
        r"colton.?scurry|account.?takeover",
        ["HUMINT", "BD_STRATEGY", "CONTACT_INTEL"],
        "CRITICAL",
        None,
    ),
    (r"playbook|PLAYBOOK", ["BD_STRATEGY"], "HIGH", None),
    (
        r"call.?list|call.?sheet|CALL_LIST|CALL_SHEET",
        ["BD_STRATEGY", "CONTACT_INTEL"],
        "HIGH",
        None,
    ),
    (
        r"bd_target|BD_TARGET|bd_scored|bd_priority|bd_master|MASTER_TARGET",
        ["BD_STRATEGY", "CONTRACT_INTEL"],
        "HIGH",
        None,
    ),
    (r"competitor|COMPETITOR|scorecard|SCORECARD", ["COMPETITIVE_INTEL"], "HIGH", None),
    (r"past.?performance|PAST_PERFORMANCE", ["PAST_PERFORMANCE"], "HIGH", None),
    (
        r"FPDS|fpds|subaward|SUBAWARD|solicitation|SOLICITATION|opportunity|OPPORTUNITY",
        ["CONTRACT_INTEL", "FINANCIAL_INTEL"],
        "HIGH",
        None,
    ),
    (
        r"PIID|piid|contract.*value|CONTRACT.*VALUE",
        ["CONTRACT_INTEL", "FINANCIAL_INTEL"],
        "HIGH",
        None,
    ),
    (r"PHASE\d|phase\d", ["CONTRACT_INTEL", "BD_STRATEGY"], "MEDIUM", None),
    (
        r"contact|CONTACT|org.?chart|ORG.?CHART|hierarchy|HIERARCHY",
        ["CONTACT_INTEL"],
        "HIGH",
        None,
    ),
    (
        r"program|PROGRAM|federal.*program|Federal.*Program",
        ["PROGRAM_INTEL"],
        "HIGH",
        None,
    ),
    (r"job|JOB|hiring|HIRING|requisition", ["JOB_INTEL"], "MEDIUM", None),
    (r"intelligence|INTELLIGENCE|enriched|ENRICHED", ["BD_STRATEGY"], "HIGH", None),
    (
        r"briefing|BRIEFING|report|REPORT|dashboard|DASHBOARD",
        ["BD_STRATEGY"],
        "MEDIUM",
        None,
    ),
    (r"prime|PRIME|contractor|CONTRACTOR", ["COMPETITIVE_INTEL"], "HIGH", None),
    (r"workflow|WORKFLOW|pipeline|automation", ["ARCHITECTURE"], "LOW", None),
    (r"notes|NOTES|activity|ACTIVITY", ["HUMINT"], "MEDIUM", None),
]


def resolve_metadata(
    source_filename: str,
    source_type: str = None,
    file_index: dict = None,
    dir_index: list = None,
) -> dict:
    """Resolve metadata tags for a given source filename."""
    fname_lower = (source_filename or "").lower()

    # 1. Exact file match
    if file_index and fname_lower in file_index:
        return file_index[fname_lower]

    # 2. Directory prefix match (for files with path info in _source)
    if dir_index and "/" in fname_lower:
        for prefix, meta in dir_index:
            if fname_lower.startswith(prefix):
                return meta

    # 3. Filename heuristic rules
    intel_cats = []
    priority = "MEDIUM"
    source_project = "bd-automation-engine"

    for pattern, cats, prio, src_hint in FILENAME_RULES:
        if re.search(pattern, source_filename or ""):
            intel_cats.extend(cats)
            if prio == "CRITICAL" or (prio == "HIGH" and priority != "CRITICAL"):
                priority = prio
            if src_hint:
                source_project = src_hint
            break  # Use first match

    if not intel_cats:
        intel_cats = ["BD_STRATEGY"]

    # Deduplicate
    intel_cats = list(dict.fromkeys(intel_cats))

    # Generate search tags from filename
    tags = []
    clean_name = re.sub(r"[_\-.]", " ", Path(source_filename or "unknown").stem)
    tags = [t.strip().lower() for t in clean_name.split() if len(t.strip()) > 2]

    # Detect source project from path hints
    if source_type:
        if (
            "data_scraper" in source_type
            or "scraper" in (source_filename or "").lower()
        ):
            source_project = "data-scraper"
        elif "n8n" in source_type:
            source_project = "n8n-builder"

    return {
        "intel_category": intel_cats,
        "search_tags": tags[:15],
        "priority": priority,
        "source_project": source_project,
    }


# ══════════════════════════════════════════════════════════════════════════
# PHASE A: ENRICH EXISTING VECTORS + FIX ZEROS
# ══════════════════════════════════════════════════════════════════════════


def create_text_for_reembed(payload: dict, collection: str) -> str:
    """Construct embedding text from payload for zero-vector re-embedding."""
    if collection == "contacts":
        fields = [
            "name",
            "Name",
            "first_name",
            "First Name",
            "last_name",
            "Last Name",
            "title",
            "Title",
            "company",
            "Company",
            "program",
            "Programs",
            "tier",
            "clearance",
            "Clearances",
            "email",
            "Email",
            "linkedin",
            "LinkedIn",
            "Primes",
            "content",
        ]
    elif collection == "programs":
        fields = [
            "Program Name",
            "name",
            "Acronym",
            "Agency Owner",
            "agency",
            "Prime Contractor",
            "prime_contractor",
            "Contract Value",
            "description",
            "content",
            "Keywords/Signals",
            "Clearance Requirements",
        ]
    elif collection == "jobs":
        fields = [
            "title",
            "company",
            "location",
            "clearance",
            "description",
            "requirements",
            "program",
            "employment_type",
            "content",
        ]
    elif collection == "documents":
        fields = [
            "title",
            "content",
            "text",
            "summary",
            "description",
            "_source_type",
            "prime_name",
            "recipient",
            "company",
        ]
    elif collection == "activities":
        fields = [
            "content",
            "comments",
            "note_text",
            "subject",
            "action",
            "activity_type",
            "actor",
            "Name",
            "Type",
            "Candidate",
            "Job Title",
        ]
    else:
        fields = ["name", "title", "content", "text", "description"]

    parts = []
    for f in fields:
        val = payload.get(f, "")
        if val and str(val).strip():
            parts.append(f"{f}: {str(val)[:1000]}")

    if not parts:
        # Fallback: use all non-underscore fields
        for k, v in payload.items():
            if v and not k.startswith("_") and len(str(v)) < 2000:
                parts.append(f"{k}: {v}")

    return " | ".join(parts)[:8000]


def is_zero_vector(vector: list[float]) -> bool:
    return all(abs(v) < 1e-10 for v in vector)


def phase_a(
    client: QdrantClient, file_index: dict, dir_index: list, dry_run: bool = False
):
    """Enrich ALL existing vectors with metadata tags. Fix any zero vectors."""
    print("\n" + "=" * 70)
    print("PHASE A: ENRICH EXISTING VECTORS + FIX ZEROS")
    print("=" * 70)

    for coll in COLLECTIONS:
        info = client.get_collection(coll)
        total = info.points_count
        if total == 0:
            print(f"\n  {coll}: empty, skipping")
            continue

        print(f"\n  Processing {coll} ({total:,} vectors)...")

        # Step 1: Collect unique _source values via sampling
        # Optimization: scroll up to 20K vectors (enough to find all unique sources)
        # Use large batches and early termination when no new sources found
        source_metadata = {}
        offset = None
        sources_seen = set()
        scanned = 0
        stale_batches = 0  # Batches with no new sources

        while scanned < min(total, 20000):
            result = client.scroll(
                collection_name=coll,
                limit=1000,
                offset=offset,
                with_vectors=False,
                with_payload=True,
            )
            points, next_offset = result
            if not points:
                break

            new_in_batch = 0
            for p in points:
                src = p.payload.get("_source", "")
                src_type = p.payload.get("_source_type", "")
                if src and src not in sources_seen:
                    sources_seen.add(src)
                    meta = resolve_metadata(src, src_type, file_index, dir_index)
                    source_metadata[src] = meta
                    new_in_batch += 1

            scanned += len(points)

            # Early termination: if 3 consecutive batches have no new sources, stop
            if new_in_batch == 0:
                stale_batches += 1
                if stale_batches >= 3:
                    break
            else:
                stale_batches = 0

            offset = next_offset
            if offset is None:
                break

        print(
            f"    Found {len(source_metadata)} unique sources across {scanned:,} vectors"
        )

        # Step 2: Apply metadata via filter-based set_payload (very efficient)
        enriched = 0
        for src, meta in source_metadata.items():
            payload_update = {
                "intel_category": meta["intel_category"],
                "search_tags": meta["search_tags"],
                "priority": meta["priority"],
                "source_project": meta["source_project"],
                "_enriched_at": datetime.now().isoformat(),
            }

            if dry_run:
                enriched += 1
                continue

            try:
                client.set_payload(
                    collection_name=coll,
                    payload=payload_update,
                    points=Filter(
                        must=[
                            FieldCondition(key="_source", match=MatchValue(value=src))
                        ]
                    ),
                )
                enriched += 1
            except Exception as e:
                logger.error("  set_payload failed for _source=%s: %s", src, e)
                stats[coll]["errors"] += 1

        stats[coll]["metadata_added"] = enriched
        print(f"    Enriched {enriched}/{len(source_metadata)} source groups")

        # Step 3: Check for zero vectors (sample first, full scan if found)
        sample_result = client.scroll(
            collection_name=coll, limit=100, with_vectors=True, with_payload=False
        )
        sample_zeros = sum(1 for p in sample_result[0] if is_zero_vector(p.vector))

        if sample_zeros == 0:
            print(f"    No zero vectors detected (sample of {len(sample_result[0])})")
            continue

        # Full scan for zeros
        print(f"    WARNING: {sample_zeros} zeros in sample! Full scan + re-embed...")
        offset = None
        zero_ids = []
        zero_texts = []
        zero_payloads = []

        while True:
            result = client.scroll(
                collection_name=coll,
                limit=100,
                offset=offset,
                with_vectors=True,
                with_payload=True,
            )
            points, next_offset = result
            if not points:
                break

            for p in points:
                if is_zero_vector(p.vector):
                    text = create_text_for_reembed(p.payload, coll)
                    if text.strip():
                        zero_ids.append(p.id)
                        zero_texts.append(text)
                        zero_payloads.append(p.payload)

            offset = next_offset
            if offset is None:
                break

        if zero_ids:
            print(f"    Found {len(zero_ids)} zero vectors, re-embedding...")
            if not dry_run:
                embeddings = batch_embed(zero_texts)
                batch = []
                for pid, emb, pay in zip(zero_ids, embeddings, zero_payloads):
                    if emb is None:
                        stats[coll]["errors"] += 1
                        continue
                    pay["_reembedded_at"] = datetime.now().isoformat()
                    batch.append(PointStruct(id=pid, vector=emb, payload=pay))
                    if len(batch) >= UPSERT_BATCH_SIZE:
                        client.upsert(collection_name=coll, points=batch)
                        stats[coll]["zeros_fixed"] += len(batch)
                        batch = []
                if batch:
                    client.upsert(collection_name=coll, points=batch)
                    stats[coll]["zeros_fixed"] += len(batch)
            print(f"    Fixed {stats[coll]['zeros_fixed']} zero vectors")


# ══════════════════════════════════════════════════════════════════════════
# PHASE B: INDEX NEW STAGED FILES
# ══════════════════════════════════════════════════════════════════════════

# Files already handled by index_staged_data.py (9 phases)
ALREADY_INDEXED_DS = {
    # Phase 1: Contracts
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
    # Phase 2: BD Targets
    "master_bd_targets.csv",
    "master_bd_targets_contract_enriched.csv",
    "master_bd_targets_fpds_enriched.csv",
    "db6_bd_targets_all.csv",
    "db6_bd_targets_priority.csv",
    "tier1_high_priority_targets.csv",
    "tier2_medium_priority_targets.csv",
    "tier3_standard_targets.csv",
    "it_services_all_targets.csv",
    # Phase 3: Primes
    "MASTER_PRIMES_ENRICHED.csv",
    "PRIMES_FROM_NOTES.csv",
    "PRIME_INTELLIGENCE_DETAILED.csv",
    "FULL_PRIME_ENRICHMENT.csv",
    "primes_usaspending_enriched.csv",
    "high_subcontract_activity.csv",
    # Phase 4: Contacts
    "CONTACTS_INTELLIGENCE.csv",
    "CONTACT_INTELLIGENCE_DETAILED.csv",
    "bullhorn_contacts_master.csv",
    "PHASE1_FAIR_GAME_CONTACTS.csv",
    "PHASE1_CLAIMED_CONTACTS.csv",
    "ORG_CHART_DATA.csv",
    "colton_scurry_contacts.csv",
    "colton_scurry_contact_handoff.csv",
    "ZOOMINFO_L3HARRIS.csv",
    # Phase 6: Jobs
    "JOBS_ENRICHED.csv",
    "JOBS_INTELLIGENCE_MAPPED.csv",
    "bd_top_program_jobs_detail.csv",
    "colton_scurry_jobs.csv",
    "hub_jobs_2026-01-26.json",
    "standardized_jobs_2026-01-26.json",
    # Phase 7: Programs
    "MASTER_PROGRAMS_ENRICHED.csv",
    "PROGRAMS_CLEAN.csv",
    "PROGRAMS_FROM_NOTES.csv",
    "GAP_PROGRAMS.csv",
    "PROGRAM_INTELLIGENCE_DETAILED.csv",
    # Skip files
    "bullhorn_programs_master.csv",
    "bullhorn_primes_master.csv",
}

SKIP_DS_FILES = {
    "bullhorn_past_performance.db",
    "data_inventory.json",
    "BD_Job_Openings_2026-01-26.xlsx",
    "ALL_NOTES_COMBINED.csv",  # 292K rows, duplicates existing activities
}

# N8N files to skip
N8N_SKIP_PREFIXES = [
    "CSIS",
    "Lookup_",
    "VendorNames_",
    "CSISbudget",
    "CSISvariable",
]

N8N_SKIP_PATTERNS = [
    r"^Agency_",  # Reference lookup tables
    r"^Budget_",
    r"^Contract_Pricing",
    r"^ProductOrService",
    r"^action_",  # action_obligation, action_type_code
    r"^agency_",  # agency_Department_of_*
    r"^assistance_type",
    r"^awarding_",
    r"^business_type",
    r"^contract_",  # Lowercase reference tables
    r"^extent_competed",
    r"^fair_opportunity",
    r"^funding_",
    r"^legal_entity",
    r"^naics_",  # Reference NAICS tables
    r"^number_of_",
    r"^object_class",
    r"^period_of_",
    r"^place_of_",
    r"^pop_",  # Period of performance ref
    r"^price_evaluation",
    r"^product_or_service",
    r"^program_activity",
    r"^pulled_from",
    r"^recipient_",
    r"^referenced_",
    r"^sam_",
    r"^solicitation_",
    r"^sub_",
    r"^total_",
    r"^treasury_",
    r"^type_of_",
    r"^ultimate_parent",
    r"^vendor_",
    r"^2\d{3}[-_]\d{2}",  # Historical date-prefixed files (2012-08-*, 2025_07_*)
    r"^A\d{3}",  # BEA reference tables (A191RD3A086NBEA etc.)
    r"^Vehicle\.csv$",  # Reference table
    r"^VendorSize",  # Reference table
    r"^World_Factbook",  # Reference data
    r"^watcher_state",  # System file
    r"^graph_hints",  # System file
    r"^project_index",  # System file
    r"^file_categories",  # System file
    r"^settings\.local",  # System config
    r"^commodity_",  # commodity_translations_merge (36K rows)
    r"^Contract_Large",  # Contract_LargeVendorLabeledAsSmallBusiness (312K rows)
    r"^Contract_N\d",  # Contract_N0001920C0032 sub-awards
    r"^Defense_Major",  # Defense_Major_Command_Codes (19K rows)
    r"^ProdServ",  # ProdServPlatformNAICS (695K rows)
    r"^Footing_",  # Budget footing reference data
]

# Max rows to index per CSV file (skip massive reference tables)
MAX_CSV_ROWS = 20000


def should_skip_n8n(filename: str) -> bool:
    for prefix in N8N_SKIP_PREFIXES:
        if filename.startswith(prefix):
            return True
    for pattern in N8N_SKIP_PATTERNS:
        if re.match(pattern, filename):
            return True
    return False


def classify_file_to_collection(filename: str) -> str:
    """Route a file to the right Qdrant collection based on filename."""
    fn = filename.lower()

    # Programs
    if re.match(r"federal.?program", fn):
        return "programs"
    if fn.startswith("discovered_programs") or fn.startswith("programs_kb"):
        return "programs"
    if fn.startswith("dod-staffing-programs") or fn.startswith("dod-programs"):
        return "programs"
    if fn in (
        "programs_final.csv",
        "program_intelligence.csv",
        "program_hierarchy.csv",
        "programs_with_contracts.csv",
    ):
        return "programs"
    if fn.startswith("01_program_directory"):
        return "programs"

    # Jobs
    if "jobs" in fn and ("mapped" in fn or "scrape" in fn or "enriched" in fn):
        return "jobs"
    if fn == "jobs_master.csv":
        return "jobs"
    if fn.startswith("hiring_intelligence"):
        return "jobs"

    # Activities
    if fn in ("all_notes_combined.csv", "author_performance.csv"):
        return "activities"
    if fn.startswith("notes activity report"):
        return "activities"

    # Contacts - be selective (only clearly contact-specific files)
    if fn.startswith("contact_search_list") or fn.startswith("immediate_action_call"):
        return "contacts"
    if fn.startswith("dormant_contacts"):
        return "contacts"

    # Default: documents (largest catch-all)
    return "documents"


def index_csv_file(
    client: QdrantClient,
    filepath: Path,
    collection: str,
    metadata: dict,
    source_project: str = "data-scraper",
):
    """Index a CSV file into Qdrant with metadata tags."""
    rows = read_csv_rows(filepath)
    if not rows:
        return 0

    if len(rows) > MAX_CSV_ROWS:
        logger.warning(
            "SKIPPING %s: %d rows exceeds MAX_CSV_ROWS (%d)",
            filepath.name,
            len(rows),
            MAX_CSV_ROWS,
        )
        return 0

    logger.info("Indexing CSV %s -> %s (%d rows)", filepath.name, collection, len(rows))

    texts, ids, payloads = [], [], []
    for row in rows:
        # Build ID from all key fields
        id_parts = []
        for f in [
            "piid",
            "notice_id",
            "contract_id",
            "award_id",
            "title",
            "name",
            "Name",
            "Full Name",
            "contact_name",
            "company",
            "Program Name",
            "program_name",
            "Acronym",
        ]:
            val = row.get(f, "")
            if val:
                id_parts.append(val)
        if not id_parts:
            id_parts = [filepath.name, json.dumps(row, sort_keys=True)[:200]]

        point_id = make_id(collection, *id_parts)
        text = make_text_from_row(row)
        if not text.strip():
            continue

        payload = {
            **{k: v for k, v in row.items() if v},
            "_source": filepath.name,
            "_indexed_at": datetime.now().isoformat(),
            "_embedding_model": EMBEDDING_MODEL,
            "_source_type": f"analytical_{source_project.replace('-', '_')}",
            "intel_category": metadata.get("intel_category", []),
            "search_tags": metadata.get("search_tags", []),
            "priority": metadata.get("priority", "MEDIUM"),
            "source_project": metadata.get("source_project", source_project),
        }

        texts.append(text)
        ids.append(point_id)
        payloads.append(payload)

    if not texts:
        return 0

    embeddings = batch_embed(texts)
    batch = []
    count = 0
    for point_id, embedding, payload in zip(ids, embeddings, payloads):
        if embedding is None:
            stats[collection]["errors"] += 1
            continue
        batch.append(PointStruct(id=point_id, vector=embedding, payload=payload))
        if len(batch) >= UPSERT_BATCH_SIZE:
            client.upsert(collection_name=collection, points=batch)
            count += len(batch)
            batch = []
    if batch:
        client.upsert(collection_name=collection, points=batch)
        count += len(batch)

    stats[collection]["indexed"] += count
    return count


def index_md_file(
    client: QdrantClient,
    filepath: Path,
    collection: str,
    metadata: dict,
    source_project: str = "data-scraper",
):
    """Index a Markdown file, chunking if > 8000 chars."""
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        logger.error("Failed to read %s: %s", filepath.name, e)
        return 0

    if not content.strip():
        return 0

    # Extract title from first heading or filename
    title = filepath.stem.replace("_", " ")
    first_line = content.split("\n")[0].strip()
    if first_line.startswith("#"):
        title = first_line.lstrip("#").strip()

    # Chunk if large
    chunks = []
    if len(content) <= 8000:
        chunks = [(content, 0)]
    else:
        # Split by headings (## or ###)
        sections = re.split(r"\n(?=##\s)", content)
        current_chunk = ""
        for section in sections:
            if len(current_chunk) + len(section) > 7000 and current_chunk:
                chunks.append((current_chunk, len(chunks)))
                # Overlap: keep last 500 chars
                current_chunk = current_chunk[-500:] + section
            else:
                current_chunk += ("\n" if current_chunk else "") + section
        if current_chunk:
            chunks.append((current_chunk, len(chunks)))

    texts, ids, payloads = [], [], []
    for chunk_text, chunk_idx in chunks:
        point_id = make_id(collection, filepath.name, str(chunk_idx))
        embed_text = f"title: {title} | content: {chunk_text}"[:8000]

        payload = {
            "title": title,
            "content": chunk_text[:5000],
            "_source": filepath.name,
            "_indexed_at": datetime.now().isoformat(),
            "_embedding_model": EMBEDDING_MODEL,
            "_source_type": f"analytical_{source_project.replace('-', '_')}",
            "_chunk_index": chunk_idx,
            "_total_chunks": len(chunks),
            "intel_category": metadata.get("intel_category", []),
            "search_tags": metadata.get("search_tags", []),
            "priority": metadata.get("priority", "MEDIUM"),
            "source_project": metadata.get("source_project", source_project),
        }

        texts.append(embed_text)
        ids.append(point_id)
        payloads.append(payload)

    if not texts:
        return 0

    embeddings = batch_embed(texts)
    batch = []
    count = 0
    for point_id, embedding, payload in zip(ids, embeddings, payloads):
        if embedding is None:
            stats[collection]["errors"] += 1
            continue
        batch.append(PointStruct(id=point_id, vector=embedding, payload=payload))
        if len(batch) >= UPSERT_BATCH_SIZE:
            client.upsert(collection_name=collection, points=batch)
            count += len(batch)
            batch = []
    if batch:
        client.upsert(collection_name=collection, points=batch)
        count += len(batch)

    stats[collection]["indexed"] += count
    logger.info("  %s -> %s: %d chunks", filepath.name, collection, count)
    return count


def index_json_file(
    client: QdrantClient,
    filepath: Path,
    collection: str,
    metadata: dict,
    source_project: str = "data-scraper",
):
    """Index a JSON file (array or dict of records)."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)
    except Exception as e:
        logger.error("Failed to read JSON %s: %s", filepath.name, e)
        return 0

    if isinstance(data, dict):
        # If it's a single dict (not array), treat as one document
        if not any(isinstance(v, (list, dict)) for v in data.values()):
            data = [data]
        else:
            # Dict of records (like processed_docs.json)
            records = []
            for key, val in data.items():
                if isinstance(val, dict):
                    val["_doc_key"] = key
                    records.append(val)
                elif isinstance(val, list):
                    for item in val:
                        if isinstance(item, dict):
                            records.append(item)
            data = records

    if not isinstance(data, list) or not data:
        return 0

    logger.info(
        "Indexing JSON %s -> %s (%d records)", filepath.name, collection, len(data)
    )

    texts, ids, payloads = [], [], []
    for record in data:
        if not isinstance(record, dict):
            continue

        id_parts = [filepath.name]
        for f in ["title", "name", "id", "_doc_key"]:
            val = record.get(f, "")
            if val:
                id_parts.append(str(val)[:100])
                break

        point_id = make_id(
            collection, *id_parts, json.dumps(record, sort_keys=True)[:100]
        )

        # Build text
        text_parts = []
        for k, v in record.items():
            if v and not k.startswith("_") and isinstance(v, (str, int, float)):
                text_parts.append(f"{k}: {str(v)[:500]}")
        text = " | ".join(text_parts)[:8000]
        if not text.strip():
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
        payload["_source_type"] = f"analytical_{source_project.replace('-', '_')}"
        payload["intel_category"] = metadata.get("intel_category", [])
        payload["search_tags"] = metadata.get("search_tags", [])
        payload["priority"] = metadata.get("priority", "MEDIUM")
        payload["source_project"] = metadata.get("source_project", source_project)

        texts.append(text)
        ids.append(point_id)
        payloads.append(payload)

    if not texts:
        return 0

    embeddings = batch_embed(texts)
    batch = []
    count = 0
    for point_id, embedding, payload in zip(ids, embeddings, payloads):
        if embedding is None:
            stats[collection]["errors"] += 1
            continue
        batch.append(PointStruct(id=point_id, vector=embedding, payload=payload))
        if len(batch) >= UPSERT_BATCH_SIZE:
            client.upsert(collection_name=collection, points=batch)
            count += len(batch)
            batch = []
    if batch:
        client.upsert(collection_name=collection, points=batch)
        count += len(batch)

    stats[collection]["indexed"] += count
    return count


def phase_b(
    client: QdrantClient, file_index: dict, dir_index: list, dry_run: bool = False
):
    """Index new staged analytical files."""
    print("\n" + "=" * 70)
    print("PHASE B: INDEX NEW STAGED FILES")
    print("=" * 70)

    for coll in COLLECTIONS:
        ensure_collection(client, coll)

    # ── Part 1: from_data_scraper remaining files ──
    print("\n  Part 1: data/from_data_scraper (uncovered files)")
    print("  " + "-" * 50)

    ds_files = []
    if DS_DIR.exists():
        for fp in sorted(DS_DIR.iterdir()):
            if not fp.is_file():
                continue
            if fp.name in ALREADY_INDEXED_DS:
                continue
            if fp.name in SKIP_DS_FILES:
                continue
            if fp.suffix.lower() not in (".csv", ".md", ".json"):
                continue
            ds_files.append(fp)

    print(f"    Found {len(ds_files)} new files to index")

    ds_indexed = 0
    for fp in ds_files:
        collection = classify_file_to_collection(fp.name)
        metadata = resolve_metadata(fp.name, "data_scraper", file_index, dir_index)
        metadata.setdefault("source_project", "data-scraper")

        if dry_run:
            print(f"    [DRY] {fp.name} -> {collection} ({metadata['intel_category']})")
            ds_indexed += 1
            continue

        if fp.suffix.lower() == ".csv":
            count = index_csv_file(client, fp, collection, metadata, "data-scraper")
        elif fp.suffix.lower() == ".md":
            count = index_md_file(client, fp, collection, metadata, "data-scraper")
        elif fp.suffix.lower() == ".json":
            count = index_json_file(client, fp, collection, metadata, "data-scraper")
        else:
            count = 0

        if count > 0:
            ds_indexed += 1
            logger.info("    %s -> %s: %d vectors", fp.name, collection, count)

    print(f"    Part 1 complete: {ds_indexed} files indexed")

    # ── Part 2: from_n8n_builder/analytical_outputs ──
    print("\n  Part 2: data/from_n8n_builder/analytical_outputs")
    print("  " + "-" * 50)

    n8n_files = []
    if N8N_OUTPUTS_DIR.exists():
        # Walk all files recursively (includes subdirectories)
        for fp in sorted(N8N_OUTPUTS_DIR.rglob("*")):
            if not fp.is_file():
                continue
            if fp.suffix.lower() not in (".csv", ".md", ".json"):
                continue
            if should_skip_n8n(fp.name):
                continue
            n8n_files.append(fp)

    print(f"    Found {len(n8n_files)} files to index (after filtering)")

    n8n_indexed = 0
    for fp in n8n_files:
        collection = classify_file_to_collection(fp.name)
        metadata = resolve_metadata(fp.name, "n8n_builder", file_index, dir_index)
        metadata.setdefault("source_project", "n8n-builder")

        if dry_run:
            print(f"    [DRY] {fp.name} -> {collection} ({metadata['intel_category']})")
            n8n_indexed += 1
            continue

        if fp.suffix.lower() == ".csv":
            count = index_csv_file(client, fp, collection, metadata, "n8n-builder")
        elif fp.suffix.lower() == ".md":
            count = index_md_file(client, fp, collection, metadata, "n8n-builder")
        elif fp.suffix.lower() == ".json":
            count = index_json_file(client, fp, collection, metadata, "n8n-builder")
        else:
            count = 0

        if count > 0:
            n8n_indexed += 1

    print(f"    Part 2 complete: {n8n_indexed} files indexed")


# ══════════════════════════════════════════════════════════════════════════
# PHASE C: BENCHMARK QUERIES
# ══════════════════════════════════════════════════════════════════════════

BENCHMARK_QUERIES = [
    ("FPDS federal contract GDIT", "documents", 0.75),
    ("Kingsley Ero PACAF San Diego", "contacts", 0.75),
    ("L3Harris company intelligence", "documents", 0.70),
    ("Bullhorn placement history DCGS", "documents", 0.80),
    ("DoD opportunity solicitation 100M", "documents", 0.70),
    ("network engineer TS/SCI Langley", "jobs", 0.75),
]


def phase_c(client: QdrantClient):
    """Run 6 benchmark queries and report scores."""
    print("\n" + "=" * 70)
    print("PHASE C: SEARCH QUALITY BENCHMARK")
    print("=" * 70)

    print(
        f"\n{'#':<3} {'Query':<40} {'Collection':<12} {'Top Score':<10} "
        f"{'Target':<8} {'Status':<6} {'Top Result Source':<40}"
    )
    print("-" * 160)

    passed = 0
    for i, (query, collection, target) in enumerate(BENCHMARK_QUERIES, 1):
        try:
            # Generate query embedding
            resp = oai_client.embeddings.create(model=EMBEDDING_MODEL, input=[query])
            query_vec = resp.data[0].embedding

            # Search
            results = client.query_points(
                collection_name=collection, query=query_vec, limit=3
            )

            if results.points:
                top = results.points[0]
                score = top.score
                source = (top.payload or {}).get("_source", "?")[:40]
                (top.payload or {}).get("intel_category", [])
                status = "PASS" if score >= target else "MISS"
                if status == "PASS":
                    passed += 1

                print(
                    f"{i:<3} {query:<40} {collection:<12} {score:<10.4f} "
                    f"{target:<8.2f} {status:<6} {source}"
                )

                # Show top 3 results
                for j, pt in enumerate(results.points[:3]):
                    pt_src = (pt.payload or {}).get("_source", "?")[:50]
                    pt_cat = (pt.payload or {}).get("intel_category", [])
                    print(
                        f"    #{j + 1}: score={pt.score:.4f} src={pt_src} "
                        f"intel={pt_cat}"
                    )
            else:
                print(
                    f"{i:<3} {query:<40} {collection:<12} {'N/A':<10} "
                    f"{target:<8.2f} {'FAIL':<6} No results"
                )
        except Exception as e:
            print(f"{i:<3} {query:<40} {collection:<12} ERROR: {e}")

    print(f"\nBenchmark: {passed}/{len(BENCHMARK_QUERIES)} queries met target score")


# ══════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════


def main():
    parser = argparse.ArgumentParser(description="Enrich + Reindex + New Files")
    parser.add_argument("--phase", choices=["a", "b", "c", "all"], default="all")
    parser.add_argument("--dry-run", action="store_true", help="Report only, no writes")
    args = parser.parse_args()

    print("=" * 70)
    print("QDRANT ENRICHMENT + REINDEX ENGINE")
    print(f"Qdrant: {QDRANT_URL}")
    print(f"Embedding: {EMBEDDING_MODEL} ({EMBEDDING_DIM}d)")
    print(f"Phase: {args.phase} | Dry run: {args.dry_run}")
    print("=" * 70)

    # Verify OpenAI key
    if not OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY not set!")
        sys.exit(1)

    client = QdrantClient(url=QDRANT_URL, timeout=600)

    # Load metadata registry
    registry = load_registry()
    file_index, dir_index = build_metadata_index(registry)
    print(f"\nRegistry loaded: {len(file_index)} files, {len(dir_index)} directories")

    # Baseline counts
    baseline = {}
    print("\nBaseline:")
    for coll in COLLECTIONS:
        try:
            info = client.get_collection(coll)
            baseline[coll] = info.points_count
            print(f"  {coll}: {info.points_count:,}")
        except Exception:
            baseline[coll] = 0
            print(f"  {coll}: not found")
    total_baseline = sum(baseline.values())
    print(f"  TOTAL: {total_baseline:,}")

    # Execute phases
    if args.phase in ("a", "all"):
        phase_a(client, file_index, dir_index, args.dry_run)

    if args.phase in ("b", "all"):
        phase_b(client, file_index, dir_index, args.dry_run)

    if args.phase in ("c", "all"):
        phase_c(client)

    # Final report
    print("\n" + "=" * 70)
    print("FINAL REPORT")
    print("=" * 70)

    print(
        f"\n{'Collection':<15} {'Before':>10} {'After':>10} {'Net':>10} "
        f"{'Enriched':>10} {'Zeros':>8} {'Errors':>8}"
    )
    print("-" * 75)

    for coll in COLLECTIONS:
        try:
            info = client.get_collection(coll)
            after = info.points_count
        except Exception:
            after = 0
        before = baseline.get(coll, 0)
        net = after - before
        enriched = stats[coll]["metadata_added"]
        zeros = stats[coll]["zeros_fixed"]
        errs = stats[coll]["errors"]
        print(
            f"{coll:<15} {before:>10,} {after:>10,} {'+' if net >= 0 else ''}{net:>9,} "
            f"{enriched:>10} {zeros:>8} {errs:>8}"
        )

    total_after = sum(
        client.get_collection(c).points_count
        for c in COLLECTIONS
        if c in [col.name for col in client.get_collections().collections]
    )
    total_indexed = sum(s["indexed"] for s in stats.values())
    total_enriched = sum(s["metadata_added"] for s in stats.values())
    total_zeros = sum(s["zeros_fixed"] for s in stats.values())
    total_errors = sum(s["errors"] for s in stats.values())

    print(f"\nTotals:")
    print(
        f"  Vectors: {total_baseline:,} -> {total_after:,} (+{total_after - total_baseline:,})"
    )
    print(f"  New indexed: {total_indexed:,}")
    print(f"  Metadata enriched: {total_enriched:,} source groups")
    print(f"  Zeros fixed: {total_zeros:,}")
    print(f"  Errors: {total_errors:,}")


if __name__ == "__main__":
    start = time.time()
    main()
    elapsed = time.time() - start
    print(f"\nTotal time: {elapsed / 60:.1f} minutes")
