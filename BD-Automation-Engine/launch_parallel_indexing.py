#!/usr/bin/env python3
"""
Launch 4 parallel indexing workers:
- 2 for contacts (remaining ~345K records)
- 2 for activities (~405K records)

This preserves existing progress (81,500 contacts already indexed).
"""

import subprocess
import sys
import os
from datetime import datetime

os.chdir(r"C:\Users\gtmar\Projects\Auto-Claude\BD-Automation-Engine")

PYTHON = r"C:\Python313\python.exe"
SCRIPT = "index_parallel_worker.py"

# Calculate splits
# Contacts: 426,565 total, 89,500 already done (through ID 90,000)
# Remaining: IDs 90,001 - 426,565 (~336,565 records)
# Split at midpoint: 90,001 + (426,565 - 90,001) / 2 = 258,283

# Activities: 404,715 total, 0 done
# Split at midpoint: 202,357

WORKERS = [
    # Contacts workers
    {
        "name": "contacts-w1",
        "args": ["--type", "contacts", "--start-id", "90001", "--end-id", "258000", "--worker", "1"],
        "desc": "Contacts IDs 90,001-258,000 (~168K records)"
    },
    {
        "name": "contacts-w2",
        "args": ["--type", "contacts", "--start-id", "258001", "--end-id", "426565", "--worker", "2"],
        "desc": "Contacts IDs 258,001-426,565 (~168K records)"
    },
    # Activities workers
    {
        "name": "activities-w1",
        "args": ["--type", "activities", "--start-id", "1", "--end-id", "202000", "--worker", "1"],
        "desc": "Activities IDs 1-202,000 (~202K records)"
    },
    {
        "name": "activities-w2",
        "args": ["--type", "activities", "--start-id", "202001", "--end-id", "404715", "--worker", "2"],
        "desc": "Activities IDs 202,001-404,715 (~202K records)"
    },
]

def main():
    print("=" * 70)
    print("PARALLEL INDEXING LAUNCHER")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print("\nLaunching 4 workers:")

    processes = []

    for w in WORKERS:
        print(f"\n  [{w['name']}] {w['desc']}")

        # Create log file for this worker
        log_file = f"worker_{w['name']}.log"

        cmd = [PYTHON, SCRIPT] + w['args']
        print(f"    Command: {' '.join(cmd)}")
        print(f"    Log: {log_file}")

        # Start process with output redirected to log file
        with open(log_file, 'w') as f:
            proc = subprocess.Popen(
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
            )
            processes.append({
                "name": w['name'],
                "proc": proc,
                "log": log_file
            })
            print(f"    PID: {proc.pid}")

    print("\n" + "=" * 70)
    print("All 4 workers launched!")
    print("=" * 70)
    print("\nTo monitor progress:")
    print("  tail -f worker_contacts-w1.log")
    print("  tail -f worker_contacts-w2.log")
    print("  tail -f worker_activities-w1.log")
    print("  tail -f worker_activities-w2.log")
    print("\nOr check Qdrant directly:")
    print("  curl http://localhost:6333/collections/contacts")
    print("  curl http://localhost:6333/collections/activities")
    print("\nEstimated completion: 20-30 minutes (with optimized batch sizes)")
    print("=" * 70)

    # Don't wait for processes - let them run in background
    print("\nWorkers are running in background. Exiting launcher.")


if __name__ == "__main__":
    main()
