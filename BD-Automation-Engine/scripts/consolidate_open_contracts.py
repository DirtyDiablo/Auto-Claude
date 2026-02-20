#!/usr/bin/env python3
"""
Consolidate Open Contracts: Merge 3 sources into 1 master file.

Sources:
  1. TOP100_ENRICHED (1,270 rows, 63 cols) — base universe + tango_* enrichment
  2. OPEN_CONTRACTS (1,297 rows, 27 cols) — 27 additional PIIDs not in TOP100
  3. UNASSIGNED (283 rows, 27 cols) — Rank, BD Priority, Bullhorn intel, etc.

Output: data/deliverables/FINAL_OPEN_CONTRACTS_ENRICHED.csv
"""

import os
import sys
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Source paths
TOP100_PATH = os.path.join(
    BASE_DIR,
    "Engine8_Knowledge",
    "assigned and open contracts Data scraper",
    "OPEN_CONTRACTS_TOP100_ENRICHED.csv",
)
OPEN_PATH = os.path.join(
    BASE_DIR,
    "Engine8_Knowledge",
    "assigned and open contracts Data scraper",
    "OPEN_CONTRACTS.csv",
)
UNASSIGNED_PATH = os.path.join(
    BASE_DIR,
    "data", "deliverables", "reports",
    "open_contracts_UNASSIGNED.csv",
)
OUTPUT_PATH = os.path.join(
    BASE_DIR,
    "data", "deliverables",
    "FINAL_OPEN_CONTRACTS_ENRICHED.csv",
)


def load_sources():
    """Load all 3 source CSVs."""
    top100 = pd.read_csv(TOP100_PATH)
    open_contracts = pd.read_csv(OPEN_PATH)
    unassigned = pd.read_csv(UNASSIGNED_PATH)

    print(f"TOP100_ENRICHED:  {len(top100):,} rows, {len(top100.columns)} cols")
    print(f"OPEN_CONTRACTS:   {len(open_contracts):,} rows, {len(open_contracts.columns)} cols")
    print(f"UNASSIGNED:       {len(unassigned):,} rows, {len(unassigned.columns)} cols")

    return top100, open_contracts, unassigned


def append_missing_piids(top100: pd.DataFrame, open_contracts: pd.DataFrame) -> pd.DataFrame:
    """Find PIIDs in OPEN_CONTRACTS missing from TOP100 and append them."""
    top100_piids = set(top100["piid"].dropna().str.strip().str.upper())
    open_piids = open_contracts["piid"].dropna().str.strip().str.upper()

    missing_mask = ~open_piids.isin(top100_piids)
    # Also include rows where piid is NaN in open_contracts (check by acronym)
    nan_mask = open_contracts["piid"].isna()
    top100_acronyms = set(top100["acronym"].dropna().str.strip().str.upper())
    open_acronyms = open_contracts["acronym"].fillna("").str.strip().str.upper()
    nan_and_new = nan_mask & ~open_acronyms.isin(top100_acronyms)

    # Combine: rows with new PIIDs OR new acronyms (when piid is NaN)
    new_rows = open_contracts[missing_mask | nan_and_new].copy()

    print(f"\nNew PIIDs from OPEN_CONTRACTS: {missing_mask.sum()}")
    print(f"New acronyms (no piid):        {nan_and_new.sum()}")
    print(f"Total rows to append:          {len(new_rows)}")

    # Append — tango columns will be filled with NaN automatically
    merged = pd.concat([top100, new_rows], ignore_index=True)
    print(f"After append: {len(merged):,} rows, {len(merged.columns)} cols")
    return merged


def merge_unassigned(merged: pd.DataFrame, unassigned: pd.DataFrame) -> pd.DataFrame:
    """LEFT JOIN unassigned data on piid, with acronym fallback."""
    # Column mapping: UNASSIGNED Title Case → new snake_case columns
    col_map = {
        "Rank": "unassigned_rank",
        "BD Priority": "bd_priority",
        "Bullhorn Placements": "bullhorn_placements",
        "Bullhorn Mentions": "bullhorn_mentions",
        "Gap Status": "gap_status",
        "Recompete Date": "recompete_date",
        "Vehicle Type": "vehicle_type",
        "Set Aside": "set_aside",
        "Ultimate Completion": "ultimate_completion",
    }

    # Normalize join keys
    unassigned = unassigned.copy()
    unassigned["_join_piid"] = unassigned["Contract Number"].fillna("").str.strip().str.upper()
    unassigned["_join_acronym"] = unassigned["Acronym"].fillna("").str.strip().str.upper()

    merged["_join_piid"] = merged["piid"].fillna("").str.strip().str.upper()
    merged["_join_acronym"] = merged["acronym"].fillna("").str.strip().str.upper()

    # Initialize new columns
    for new_col in col_map.values():
        merged[new_col] = pd.NA

    # Pass 1: Match on PIID (most reliable)
    piid_matched = 0
    for _, urow in unassigned.iterrows():
        if not urow["_join_piid"]:
            continue
        mask = merged["_join_piid"] == urow["_join_piid"]
        if mask.any():
            for old_col, new_col in col_map.items():
                if old_col in urow.index and pd.notna(urow[old_col]):
                    merged.loc[mask, new_col] = urow[old_col]
            piid_matched += mask.sum()

    # Pass 2: Match on acronym for rows that didn't match by PIID
    acronym_matched = 0
    unmatched_piids = unassigned[unassigned["_join_piid"] == ""]
    piid_matched_acronyms = set(
        unassigned[unassigned["_join_piid"] != ""]["_join_acronym"]
    )
    for _, urow in unassigned.iterrows():
        if urow["_join_piid"]:
            continue  # Already handled in pass 1
        if not urow["_join_acronym"]:
            continue
        mask = (merged["_join_acronym"] == urow["_join_acronym"]) & merged["unassigned_rank"].isna()
        if mask.any():
            for old_col, new_col in col_map.items():
                if old_col in urow.index and pd.notna(urow[old_col]):
                    merged.loc[mask, new_col] = urow[old_col]
            acronym_matched += mask.sum()

    # Clean up join keys
    merged.drop(columns=["_join_piid", "_join_acronym"], inplace=True)

    total_enriched = merged["unassigned_rank"].notna().sum()
    print(f"\nUNASSIGNED merge: {piid_matched} piid matches, {acronym_matched} acronym matches")
    print(f"Total rows with unassigned data: {total_enriched}")

    return merged


def main():
    print("=" * 60)
    print("OPEN CONTRACTS CONSOLIDATION")
    print("=" * 60)

    top100, open_contracts, unassigned = load_sources()

    # Step 1: Append missing PIIDs from OPEN_CONTRACTS
    merged = append_missing_piids(top100, open_contracts)

    # Step 2: LEFT JOIN UNASSIGNED enrichment
    merged = merge_unassigned(merged, unassigned)

    # Step 3: Write output
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    merged.to_csv(OUTPUT_PATH, index=False)

    print(f"\nFINAL OUTPUT: {OUTPUT_PATH}")
    print(f"  Rows: {len(merged):,}")
    print(f"  Cols: {len(merged.columns)}")
    print(f"  Size: {os.path.getsize(OUTPUT_PATH) / 1024:.1f} KB")
    print("=" * 60)

    return merged


if __name__ == "__main__":
    main()
