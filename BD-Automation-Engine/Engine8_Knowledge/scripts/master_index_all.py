"""
Master Index All - Sequential Runner
Runs all indexers in sequence to avoid rate limits
"""
import os
import sys
import time
import subprocess
from pathlib import Path

PYTHON = r"C:\Users\gtmar\AppData\Local\Programs\Python\Python312\python.exe"
SCRIPTS_DIR = Path(__file__).parent

def run_indexer(script_name: str):
    """Run an indexer script and wait for completion."""
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        print(f"Script not found: {script_path}")
        return False

    print(f"\n{'='*60}")
    print(f"RUNNING: {script_name}")
    print(f"{'='*60}\n")

    try:
        result = subprocess.run(
            [PYTHON, str(script_path)],
            cwd=str(SCRIPTS_DIR.parent.parent),
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error running {script_name}: {e}")
        return False

def check_qdrant_status():
    """Check and print Qdrant status."""
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(url="http://localhost:6333")
        print("\n=== QDRANT STATUS ===")
        total = 0
        for coll in client.get_collections().collections:
            info = client.get_collection(coll.name)
            print(f"  {coll.name}: {info.points_count:,} points")
            total += info.points_count
        print(f"  TOTAL: {total:,} points\n")
        return total
    except Exception as e:
        print(f"Error checking Qdrant: {e}")
        return 0

def main():
    start_time = time.time()
    print("="*60)
    print("MASTER INDEX ALL - SEQUENTIAL RUNNER")
    print("="*60)

    # Check initial status
    initial_count = check_qdrant_status()

    # List of indexers to run in order
    indexers = [
        "index_engine3_contacts.py",   # 35K+ Master Contacts + Prime CSVs
        "index_engine2_programs.py",   # Federal Programs, Contractors
        "index_engine1_jobs.py",       # Scraped jobs
        "index_dashboard_data.py",     # Dashboard public data
    ]

    for indexer in indexers:
        run_indexer(indexer)
        check_qdrant_status()
        time.sleep(2)  # Brief pause between indexers

    # Final status
    final_count = check_qdrant_status()

    elapsed = time.time() - start_time
    print("="*60)
    print("MASTER INDEX COMPLETE")
    print(f"  Initial: {initial_count:,} points")
    print(f"  Final: {final_count:,} points")
    print(f"  Added: {final_count - initial_count:,} points")
    print(f"  Time: {elapsed/60:.1f} minutes")
    print("="*60)

if __name__ == "__main__":
    main()
