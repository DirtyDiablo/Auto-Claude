#!/usr/bin/env python3
"""
Consolidate Team Assignments: Merge 2 sources into 1 master file.

Sources:
  1. CORRECTED (139 rows, 10 cols) — authoritative acronyms, Status, Bullhorn intel
  2. TEAM_CONTRACT_ASSIGNMENTS (139 rows, 16 cols) — piid, clearance, locations, etc.

Output: data/deliverables/FINAL_TEAM_ASSIGNMENTS.csv
"""

import os
import sys
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CORRECTED_PATH = os.path.join(
    BASE_DIR,
    "data", "deliverables", "reports",
    "contract_assignments_CORRECTED.csv",
)
TEAM_PATH = os.path.join(
    BASE_DIR,
    "Engine8_Knowledge",
    "Assigned and Open Contracts N8N Builder",
    "TEAM_CONTRACT_ASSIGNMENTS.csv",
)
OUTPUT_PATH = os.path.join(
    BASE_DIR,
    "data", "deliverables",
    "FINAL_TEAM_ASSIGNMENTS.csv",
)


def main():
    print("=" * 60)
    print("TEAM ASSIGNMENTS CONSOLIDATION")
    print("=" * 60)

    corrected = pd.read_csv(CORRECTED_PATH)
    team = pd.read_csv(TEAM_PATH)

    print(f"CORRECTED:              {len(corrected):,} rows, {len(corrected.columns)} cols")
    print(f"TEAM_CONTRACT_ASSIGN:   {len(team):,} rows, {len(team.columns)} cols")

    # Normalize join keys: Person ↔ assigned_to, Corrected Acronym ↔ roster_acronym
    corrected["_join_person"] = corrected["Person"].str.strip().str.upper()
    corrected["_join_acronym"] = corrected["Corrected Acronym"].str.strip().str.upper()

    team["_join_person"] = team["assigned_to"].str.strip().str.upper()
    team["_join_acronym"] = team["roster_acronym"].str.strip().str.upper()

    # Columns to pull from TEAM that don't exist in CORRECTED
    team_cols = ["piid", "clearance", "locations", "typical_roles",
                 "naics_code", "pop_end", "data_source", "matched_program"]

    # Pass 1: Exact merge on person + acronym
    merged = corrected.merge(
        team[["_join_person", "_join_acronym"] + team_cols],
        on=["_join_person", "_join_acronym"],
        how="left",
    )

    exact_matched = merged["piid"].notna().sum()
    print(f"\nPass 1 (exact): {exact_matched} matched")

    # Pass 2: Fuzzy fallback for unmatched — CORRECTED has expanded acronyms
    # (e.g., "SAIC BMC3") while TEAM has short ones ("BMC3").
    # Match on person + substring containment.
    unmatched_mask = merged["piid"].isna()
    if unmatched_mask.any():
        # Build lookup: (person) -> list of team rows
        team_by_person = {}
        for _, trow in team.iterrows():
            p = trow["_join_person"]
            team_by_person.setdefault(p, []).append(trow)

        fuzzy_count = 0
        for idx in merged[unmatched_mask].index:
            person = merged.at[idx, "_join_person"]
            acronym = merged.at[idx, "_join_acronym"]
            if person not in team_by_person:
                continue
            for trow in team_by_person[person]:
                ta = trow["_join_acronym"]
                # Check if one contains the other (handles "SAIC BMC3" vs "BMC3")
                if ta in acronym or acronym in ta:
                    for col in team_cols:
                        merged.at[idx, col] = trow[col]
                    fuzzy_count += 1
                    break

        print(f"Pass 2 (fuzzy): {fuzzy_count} additional matches")

    # Drop join helper columns
    merged.drop(columns=["_join_person", "_join_acronym"], inplace=True)

    matched = merged["piid"].notna().sum()
    unmatched = merged["piid"].isna().sum()
    print(f"Total: {matched} matched, {unmatched} unmatched")

    # Write output
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    merged.to_csv(OUTPUT_PATH, index=False)

    print(f"\nFINAL OUTPUT: {OUTPUT_PATH}")
    print(f"  Rows: {len(merged):,}")
    print(f"  Cols: {len(merged.columns)}")
    print(f"  Size: {os.path.getsize(OUTPUT_PATH) / 1024:.1f} KB")

    # Show sample of a matched row
    sample = merged[merged["piid"].notna()].head(1)
    if not sample.empty:
        print(f"\nSample matched row:")
        for col in merged.columns:
            val = sample.iloc[0][col]
            if pd.notna(val):
                text = str(val).encode("ascii", errors="replace").decode("ascii")
                print(f"  {col}: {text}")

    print("=" * 60)
    return merged


if __name__ == "__main__":
    main()
