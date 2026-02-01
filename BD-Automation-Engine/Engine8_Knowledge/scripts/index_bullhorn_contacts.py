"""
Index Bullhorn candidates to contacts collection.
Indexes 426K+ candidates from bullhorn_master.db into Qdrant.
"""

import os
import sys
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('BullhornContactIndexer')

# Paths
BULLHORN_DB = Path(__file__).parent.parent.parent / "Engine7_BullhornETL" / "data" / "bullhorn_master.db"
BATCH_SIZE = 500  # Process in batches to manage memory


def get_candidates_count(conn: sqlite3.Connection) -> int:
    """Get total candidate count."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM candidates")
    return cursor.fetchone()[0]


def get_candidates_batch(conn: sqlite3.Connection, offset: int, limit: int) -> List[Dict]:
    """Get a batch of candidates."""
    cursor = conn.cursor()
    cursor.row_factory = sqlite3.Row
    cursor.execute(f"""
        SELECT * FROM candidates
        ORDER BY id
        LIMIT {limit} OFFSET {offset}
    """)
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def transform_candidate_to_contact(candidate: Dict) -> Dict:
    """Transform a Bullhorn candidate to contact format."""
    # Build content string for embedding
    parts = []

    name = candidate.get('full_name') or f"{candidate.get('first_name', '')} {candidate.get('last_name', '')}".strip()
    if name:
        parts.append(name)

    title = candidate.get('job_title') or candidate.get('occupation', '')
    if title:
        parts.append(title)

    company = candidate.get('company_name') or candidate.get('current_employer', '')
    if company:
        parts.append(f"at {company}")

    # Add skills/experience if available
    skills = candidate.get('skills', '')
    if skills:
        parts.append(f"Skills: {skills[:200]}")

    # Add clearance if available
    clearance = candidate.get('clearance', '') or candidate.get('security_clearance', '')
    if clearance:
        parts.append(f"Clearance: {clearance}")

    # Add location
    city = candidate.get('city', '')
    state = candidate.get('state', '')
    if city or state:
        location = f"{city}, {state}".strip(', ')
        parts.append(f"Location: {location}")

    content = " | ".join(parts) if parts else f"Candidate {candidate.get('id', 'unknown')}"

    return {
        "id": f"bullhorn_candidate_{candidate.get('bullhorn_candidate_id') or candidate.get('id')}",
        "content": content,
        "name": name or "Unknown",
        "title": title,
        "first_name": candidate.get('first_name', ''),
        "last_name": candidate.get('last_name', ''),
        "company": company,
        "email": candidate.get('email', ''),
        "phone": candidate.get('phone', '') or candidate.get('mobile', ''),
        "linkedin": candidate.get('linkedin', ''),
        "clearance": clearance,
        "city": city,
        "state": state,
        "skills": candidate.get('skills', '')[:500] if candidate.get('skills') else '',
        "status": candidate.get('status', ''),
        "source": "bullhorn_candidates",
        "source_db": "bullhorn_master",
        "bullhorn_id": candidate.get('bullhorn_candidate_id'),
        "indexed_at": datetime.now().isoformat()
    }


def index_bullhorn_contacts():
    """Main indexing function."""
    logger.info("=" * 60)
    logger.info("BULLHORN CONTACTS INDEXER")
    logger.info("=" * 60)

    # Check database exists
    if not BULLHORN_DB.exists():
        logger.error(f"Database not found: {BULLHORN_DB}")
        return

    logger.info(f"Database: {BULLHORN_DB}")

    # Connect to database
    conn = sqlite3.connect(str(BULLHORN_DB))
    total_candidates = get_candidates_count(conn)
    logger.info(f"Total candidates to index: {total_candidates:,}")

    # Initialize vector store
    logger.info("Initializing vector store...")
    store = BDKnowledgeStore()
    store.initialize_collections()

    # Get current contacts count
    try:
        current_count = store.client.get_collection("contacts").points_count
        logger.info(f"Current contacts in Qdrant: {current_count:,}")
    except:
        current_count = 0

    # Process in batches
    total_indexed = 0
    total_errors = 0
    offset = 0
    start_time = datetime.now()

    while offset < total_candidates:
        batch_start = datetime.now()

        # Get batch of candidates
        candidates = get_candidates_batch(conn, offset, BATCH_SIZE)
        if not candidates:
            break

        # Transform to contacts
        contacts = [transform_candidate_to_contact(c) for c in candidates]

        # Index batch
        indexed, errors = store.index_contacts(contacts)
        total_indexed += indexed
        total_errors += errors

        offset += BATCH_SIZE
        batch_time = (datetime.now() - batch_start).total_seconds()

        # Progress update every 10 batches
        if (offset // BATCH_SIZE) % 10 == 0:
            elapsed = (datetime.now() - start_time).total_seconds()
            rate = total_indexed / elapsed if elapsed > 0 else 0
            remaining = (total_candidates - offset) / rate if rate > 0 else 0
            logger.info(
                f"Progress: {offset:,}/{total_candidates:,} ({100*offset/total_candidates:.1f}%) | "
                f"Indexed: {total_indexed:,} | Errors: {total_errors} | "
                f"Rate: {rate:.0f}/sec | ETA: {remaining/60:.1f} min"
            )

    conn.close()

    # Final stats
    duration = (datetime.now() - start_time).total_seconds()
    logger.info("=" * 60)
    logger.info("INDEXING COMPLETE")
    logger.info(f"  Total indexed: {total_indexed:,}")
    logger.info(f"  Total errors: {total_errors}")
    logger.info(f"  Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    logger.info(f"  Rate: {total_indexed/duration:.0f} contacts/sec")

    # Verify final count
    try:
        final_count = store.client.get_collection("contacts").points_count
        logger.info(f"  Final contacts in Qdrant: {final_count:,}")
    except Exception as e:
        logger.warning(f"Could not get final count: {e}")

    logger.info("=" * 60)


if __name__ == "__main__":
    index_bullhorn_contacts()
