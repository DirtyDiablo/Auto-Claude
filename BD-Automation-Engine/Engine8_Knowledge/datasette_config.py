"""
Datasette configuration for Bullhorn SQLite database exploration.

Launches Datasette alongside the FastAPI server to provide a browsable
SQL interface for bullhorn_master.db and other SQLite databases.

Usage:
    from Engine8_Knowledge.datasette_config import start_datasette
    start_datasette()  # Starts on port 8200

    Or from CLI:
    python -m Engine8_Knowledge.datasette_config
"""

import os
import subprocess
import sys
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
DATASETTE_PORT = int(os.environ.get("DATASETTE_PORT", "8200"))

# SQLite databases to serve
DATABASES = [
    BASE_DIR / "Engine7_BullhornETL" / "data" / "bullhorn_master.db",
    BASE_DIR / "Engine8_Knowledge" / "data" / "bd_graph.db",
    BASE_DIR / "Engine8_Knowledge" / "data" / "memories.db",
    BASE_DIR / "Engine8_Knowledge" / "data" / "page_index.db",
]

# Datasette metadata for documentation
METADATA = {
    "title": "PTS BD Intelligence - Data Explorer",
    "description": "Browse Bullhorn CRM data, knowledge graph, and memory system",
    "databases": {
        "bullhorn_master": {
            "description": "Bullhorn CRM ETL database (293 MB) - jobs, candidates, placements, activities, prime contractors, programs, past performance",
            "tables": {
                "jobs": {"description": "Job postings from Bullhorn CRM"},
                "candidates": {"description": "Contacts and candidates"},
                "placements": {"description": "Staffing placements (job-candidate matches)"},
                "activities": {"description": "Call notes and interaction activities"},
                "prime_contractors": {"description": "Defense prime contractors"},
                "programs": {"description": "Federal programs and contracts"},
                "past_performance": {"description": "Aggregated performance metrics"},
            }
        },
        "bd_graph": {
            "description": "BD Knowledge Graph (entities and relationships)"
        },
        "memories": {
            "description": "Memory system (long-term memories, interactions, insights)"
        },
        "page_index": {
            "description": "BM25 page-level document index"
        }
    }
}


def get_available_databases() -> list:
    """Return list of existing database paths."""
    return [str(db) for db in DATABASES if db.exists()]


def start_datasette(port: int = None, background: bool = True) -> subprocess.Popen | None:
    """
    Start Datasette server for SQLite database exploration.

    Args:
        port: Port to serve on (default: 8200)
        background: Run as background process

    Returns:
        Popen process if background=True, else None (blocks)
    """
    port = port or DATASETTE_PORT
    dbs = get_available_databases()

    if not dbs:
        logger.warning("datasette_no_databases: No SQLite databases found to serve")
        return None

    try:
        import datasette  # noqa: F401
    except ImportError:
        logger.error("datasette_not_installed: Install with: pip install datasette")
        return None

    cmd = [
        sys.executable, "-m", "datasette", "serve",
        *dbs,
        "--port", str(port),
        "--cors",
        "--setting", "sql_time_limit_ms", "10000",
        "--setting", "max_returned_rows", "1000",
    ]

    logger.info("datasette_starting", port=port, databases=len(dbs))

    if background:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        logger.info("datasette_started", pid=process.pid, url=f"http://localhost:{port}")
        return process
    else:
        subprocess.run(cmd)
        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    dbs = get_available_databases()
    print(f"Found {len(dbs)} databases:")
    for db in dbs:
        print(f"  - {db}")
    print(f"\nStarting Datasette on port {DATASETTE_PORT}...")
    start_datasette(background=False)
