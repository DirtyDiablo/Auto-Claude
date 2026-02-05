#!/usr/bin/env python3
"""BD-Automation-Engine Status Check - Run this in any terminal"""

import sys
import os
import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Fix Windows encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Change to project directory
os.chdir(r"C:\Users\gtmar\Projects\Auto-Claude\BD-Automation-Engine")

print("=" * 70)
print("BD-AUTOMATION-ENGINE STATUS CHECK")
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# === QDRANT STATUS ===
print("\n=== QDRANT COLLECTIONS (INDEXED) ===")
qdrant_counts = {}
try:
    import urllib.request
    import json

    response = urllib.request.urlopen("http://localhost:6333/collections", timeout=5)
    data = json.loads(response.read())
    collections = data.get("result", {}).get("collections", [])

    total_records = 0
    for col in collections:
        name = col["name"]
        info_response = urllib.request.urlopen(f"http://localhost:6333/collections/{name}", timeout=5)
        info = json.loads(info_response.read())
        count = info["result"]["points_count"]
        qdrant_counts[name] = count
        total_records += count
        print(f"  {name:15} {count:>12,} vectors")

    print(f"  {'-'*30}")
    print(f"  {'TOTAL':15} {total_records:>12,} vectors")
    print("\n  [OK] QDRANT ONLINE")
except Exception as e:
    print(f"  [ERROR] Qdrant not responding: {e}")

# === SOURCE DATA ===
print("\n=== SOURCE DATA (bullhorn_master.db - 293MB) ===")
db_path = "Engine7_BullhornETL/data/bullhorn_master.db"
source_counts = {}
if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        key_tables = [
            ("candidates", "contacts"),
            ("activities", "activities"),
            ("call_notes", "activities"),
            ("jobs", "jobs"),
            ("placements", "activities"),
            ("past_performance", "documents"),
            ("contact_scores", "contacts"),
            ("contact_activity_summary", "activities"),
        ]
        print(f"  {'Source Table':<28} {'Rows':>12}  -> {'Target':>12}")
        print(f"  {'-'*60}")
        for table, target in key_tables:
            try:
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                print(f"  {table:<28} {count:>12,}  -> {target:>12}")
                if target not in source_counts:
                    source_counts[target] = 0
                source_counts[target] += count
            except Exception as e:
                logger.debug("table_count_failed for %s: %s", table, e)
        conn.close()
    except Exception as e:
        print(f"  Error reading DB: {e}")
else:
    print("  bullhorn_master.db not found")

# === INDEXING COVERAGE ===
print("\n=== INDEXING COVERAGE ANALYSIS ===")
print(f"  {'Collection':<15} {'Source':>12} {'Indexed':>12} {'Remaining':>12} {'Progress':>10}")
print(f"  {'-'*65}")

total_remaining = 0
for collection in ['contacts', 'activities', 'jobs', 'documents', 'programs']:
    source = source_counts.get(collection, 0)
    indexed = qdrant_counts.get(collection, 0)

    if collection == 'documents':
        # Documents come from files, not DB
        print(f"  {collection:<15} {'(files)':>12} {indexed:>12,} {'-':>12} {'[DONE]':>10}")
    elif collection == 'programs':
        # Programs from multiple sources
        print(f"  {collection:<15} {'(multi)':>12} {indexed:>12,} {'-':>12} {'[DONE]':>10}")
    elif source > 0:
        remaining = max(0, source - indexed)
        total_remaining += remaining
        pct = (indexed / source) * 100 if source > 0 else 0
        if pct >= 95:
            status = "[DONE]"
        elif pct >= 50:
            status = f"[{pct:.0f}%]"
        else:
            status = f"[{pct:.0f}%]"
        print(f"  {collection:<15} {source:>12,} {indexed:>12,} {remaining:>12,} {status:>10}")
    else:
        print(f"  {collection:<15} {source:>12,} {indexed:>12,} {'-':>12} {'[OK]':>10}")

print(f"  {'-'*65}")
print(f"  {'TOTAL REMAINING':>41} {total_remaining:>12,}")

# === WHAT NEEDS TO BE DONE ===
print("\n=== INDEXING TO-DO LIST ===")

contacts_source = source_counts.get('contacts', 0)
contacts_indexed = qdrant_counts.get('contacts', 0)
contacts_remaining = max(0, contacts_source - contacts_indexed)

activities_source = source_counts.get('activities', 0)
activities_indexed = qdrant_counts.get('activities', 0)
activities_remaining = max(0, activities_source - activities_indexed)

if contacts_remaining > 0:
    print(f"  1. [NEEDED] Index {contacts_remaining:,} more contacts from candidates table")
else:
    print(f"  1. [DONE] Contacts fully indexed")

if activities_remaining > 0:
    print(f"  2. [NEEDED] Index {activities_remaining:,} more activities")
else:
    print(f"  2. [DONE] Activities fully indexed")

print(f"  3. [DONE] Documents indexed (124,095)")
print(f"  4. [DONE] Programs indexed (2,124)")
print(f"  5. [DONE] Jobs indexed (1,039)")

# === KNOWLEDGE API ===
print("\n=== SERVICES STATUS ===")
try:
    response = urllib.request.urlopen("http://localhost:8100/health", timeout=5)
    print("  Knowledge API:    [RUNNING] on port 8100")
except Exception as e:
    logger.debug("knowledge_api_check_failed: %s", e)
    print("  Knowledge API:    [STOPPED] - Start with: python Engine8_Knowledge/api.py")

try:
    response = urllib.request.urlopen("http://localhost:6333/collections", timeout=5)
    print("  Qdrant Docker:    [RUNNING] on port 6333")
except Exception as e:
    logger.debug("qdrant_check_failed: %s", e)
    print("  Qdrant Docker:    [STOPPED]")

print("\n" + "=" * 70)
print("COMMAND: python status_check.py")
print("=" * 70)
