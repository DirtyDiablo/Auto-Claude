"""
Deduplicate programs collection in Qdrant.

Groups programs by (Program Name, Acronym), keeps the most enriched
version (most non-empty fields), deletes the rest.
"""

import os
from collections import defaultdict
from qdrant_client import QdrantClient
from qdrant_client.models import PointIdsList

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = "programs"

# Fields that indicate enrichment quality (more = better)
ENRICHMENT_FIELDS = [
    "Program Name",
    "Acronym",
    "Agency Owner",
    "Agency",
    "Program Type",
    "Priority Level",
    "Contract Number",
    "Contract Value",
    "Contract Value (Consolidated)",
    "total_contract_value",
    "obligated",
    "Prime Contractor",
    "Prime Contractor 1",
    "Prime Contractor (Consolidated)",
    "recipient_name",
    "recipient_uei",
    "Key Subcontractors",
    "Known Subcontractors",
    "period_start",
    "period_end",
    "ultimate_completion",
    "PoP Start (Consolidated)",
    "PoP End (Consolidated)",
    "Performance Location (TANGO)",
    "pop_city",
    "pop_state",
    "naics_code",
    "psc_code",
    "set_aside",
    "subawards_count",
    "subawards_total",
    "awarding_office",
    "awarding_agency",
    "funding_office",
    "Clearance Requirements",
    "Security Requirements",
    "Technical Stack",
    "Keywords/Signals",
    "tango_piid",
    "tango_description",
    "parent_piid",
    "parent_description",
    "Contract Description",
    "Match Confidence",
    "Match Score",
    "NAICS Code (Consolidated)",
    "PSC Code (Consolidated)",
    "Recompete Date",
    "Budget",
    "Pain Points",
    "Notes",
]


def compute_richness(payload: dict) -> int:
    """Count non-empty enrichment fields in payload."""
    score = 0
    for field in ENRICHMENT_FIELDS:
        val = payload.get(field)
        if (
            val
            and str(val).strip()
            and str(val).strip() not in ('""', "''", "N/A", "None")
        ):
            score += 1
    # Bonus: count total non-empty keys as tiebreaker
    total_keys = sum(
        1 for k, v in payload.items() if v and str(v).strip() and not k.startswith("_")
    )
    return (
        score * 1000 + total_keys
    )  # Primary: enrichment fields, secondary: total keys


def get_program_key(payload: dict) -> str:
    """Generate a grouping key for program identity."""
    name = (
        (
            payload.get("Program Name")
            or payload.get("name")
            or payload.get("title")
            or ""
        )
        .strip()
        .lower()
    )

    acronym = (payload.get("Acronym") or payload.get("acronym") or "").strip().lower()

    contract = (
        (payload.get("Contract Number") or payload.get("contract_number") or "")
        .strip()
        .lower()
    )

    # Primary key: name + acronym
    # If no name, fall back to contract number
    if name:
        return f"{name}|{acronym}"
    elif contract:
        return f"contract:{contract}"
    else:
        return f"unknown:{payload.get('id', payload.get('content', '')[:50])}"


def main():
    print(f"Connecting to Qdrant at {QDRANT_URL}...")
    client = QdrantClient(url=QDRANT_URL, timeout=120)

    # Get collection info
    info = client.get_collection(COLLECTION)
    total_points = info.points_count
    print(f"Collection '{COLLECTION}': {total_points:,} points")

    # Scroll all points
    print("Scrolling all program records...")
    all_points = []
    offset = None

    while True:
        results, offset = client.scroll(
            collection_name=COLLECTION,
            limit=250,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        all_points.extend(results)
        if offset is None:
            break

    print(f"Retrieved {len(all_points):,} points")

    # Group by program identity
    groups = defaultdict(list)
    for point in all_points:
        key = get_program_key(point.payload)
        groups[key].append(point)

    # Identify duplicates
    unique_count = len(groups)
    duplicate_ids = []
    kept_records = []

    print(
        f"\nFound {unique_count:,} unique programs across {len(all_points):,} records"
    )
    print(f"Duplicate groups: {sum(1 for g in groups.values() if len(g) > 1)}")
    print()

    # Show top duplicate groups
    dup_groups = [(k, v) for k, v in groups.items() if len(v) > 1]
    dup_groups.sort(key=lambda x: len(x[1]), reverse=True)

    print("Top duplicate groups:")
    for key, points in dup_groups[:15]:
        sources = [
            p.payload.get("_source", p.payload.get("source", "?")) for p in points
        ]
        print(f"  [{len(points)} copies] {key}")
        for src in sources:
            print(f"    - {src}")

    print()

    # For each group, keep the most enriched, mark rest for deletion
    for key, points in groups.items():
        if len(points) == 1:
            kept_records.append(points[0])
            continue

        # Score each by richness
        scored = [(compute_richness(p.payload), p) for p in points]
        scored.sort(key=lambda x: x[0], reverse=True)

        # Keep the best
        best_score, best_point = scored[0]
        kept_records.append(best_point)

        # Mark duplicates for deletion
        for score, point in scored[1:]:
            duplicate_ids.append(point.id)

    print(f"Records to keep: {len(kept_records):,}")
    print(f"Duplicates to delete: {len(duplicate_ids):,}")

    if not duplicate_ids:
        print("\nNo duplicates found. Collection is clean.")
        return

    # Show example of what's being kept vs deleted
    print("\nExample dedup decision:")
    example_key, example_points = dup_groups[0]
    scored_example = [(compute_richness(p.payload), p) for p in example_points]
    scored_example.sort(key=lambda x: x[0], reverse=True)
    print(f"  Program: {example_key}")
    for i, (score, p) in enumerate(scored_example):
        source = p.payload.get("_source", p.payload.get("source", "?"))
        action = "KEEP" if i == 0 else "DELETE"
        print(f"  [{action}] score={score}, source={source}, id={p.id}")

    # Delete duplicates in batches
    print(f"\nDeleting {len(duplicate_ids):,} duplicate points...")
    batch_size = 100
    deleted = 0

    for i in range(0, len(duplicate_ids), batch_size):
        batch = duplicate_ids[i : i + batch_size]
        client.delete(
            collection_name=COLLECTION,
            points_selector=PointIdsList(points=batch),
        )
        deleted += len(batch)
        print(f"  Deleted {deleted:,}/{len(duplicate_ids):,}")

    # Verify final count
    info_after = client.get_collection(COLLECTION)
    final_count = info_after.points_count

    print(f"\n{'=' * 50}")
    print(f"DEDUPLICATION COMPLETE")
    print(f"{'=' * 50}")
    print(f"Before:           {total_points:,} points")
    print(f"Duplicates found: {len(duplicate_ids):,}")
    print(f"After:            {final_count:,} points")
    print(f"Unique programs:  {unique_count:,}")
    print(f"Reduction:        {(1 - final_count / total_points) * 100:.1f}%")


if __name__ == "__main__":
    main()
