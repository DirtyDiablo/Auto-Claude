#!/usr/bin/env python3
"""
BD-Automation-Engine Data Reorganization Script

Consolidates ~700+ scattered data files into a unified data/ hierarchy.
Eliminates duplicates, archives old versions, and makes every file discoverable.

Usage:
    python scripts/reorganize_data.py --dry-run     # Preview all moves
    python scripts/reorganize_data.py --execute      # Execute migration
    python scripts/reorganize_data.py --verify       # Post-migration verification
"""

import sys
import os
# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import argparse
import csv
import hashlib
import re
import shutil
from datetime import datetime
from pathlib import Path

# ── Project root ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = PROJECT_ROOT / "data"

# ── Target directories ──
TARGET_DIRS = [
    "data/raw/scraper",
    "data/raw/bullhorn/job_records",
    "data/raw/bullhorn/sales_activity",
    "data/raw/bullhorn/aggregate_reports",
    "data/raw/notion_exports/federal_programs",
    "data/raw/notion_exports/bd_opportunities",
    "data/raw/notion_exports/contractors",
    "data/raw/notion_exports/contract_vehicles",
    "data/raw/notion_exports/programs_kb",
    "data/raw/notion_exports/jobs",
    "data/raw/notion_exports/intellirepo",
    "data/raw/federal_apis/contracts",
    "data/raw/federal_apis/subawards",
    "data/raw/federal_apis/opportunities",
    "data/raw/zoominfo",
    "data/enriched/contacts/by_company",
    "data/enriched/contacts/cross_cutting",
    "data/enriched/programs",
    "data/enriched/contracts",
    "data/enriched/jobs",
    "data/enriched/primes",
    "data/enriched/targets",
    "data/enriched/intelligence",
    "data/deliverables/briefings",
    "data/deliverables/call_lists",
    "data/deliverables/playbooks",
    "data/deliverables/reports",
    "data/deliverables/coworker_takeover",
    "data/deliverables/coworker_takeover/programs",
    "data/deliverables/notion_uploads",
    "data/bullhorn_analysis/ANALYSIS",
    "data/bullhorn_analysis/ANALYSIS/NOTES_DEEP_DIVE",
    "data/bullhorn_analysis/FINAL_OUTPUTS",
    "data/bullhorn_analysis/source_csvs",
    "data/dashboard",
    "data/reference/fpds",
    "data/reference/usaspending",
    "data/reference/naics_psc",
    "data/reference/geo_economic",
    "data/reference/mcp_extracts",
    "data/reference/templates",
    "data/knowledge",
    "data/state",
    "data/archive/federal_programs_versions",
    "data/archive/dod_staffing_versions",
    "data/archive/notion_export_history",
    "data/archive/notion_api_dumps",
    "data/archive/contractors_iterations",
    "data/archive/cv_iterations",
    "data/archive/engine1_iterations",
    "data/archive/historical_fpds_usaspending",
    "data/archive/scraper_runs",
    "data/archive/playbook_versions",
    "data/archive/engine_data_duplicates",
    "data/archive/contacts_raw",
]

# ── Filename normalization ──
def normalize_filename(name: str) -> str:
    """Remove emoji prefixes, replace spaces with underscores."""
    # Strip leading emoji characters (common Unicode emoji ranges)
    name = re.sub(r'^[\U0001F300-\U0001FAD6\u2600-\u27BF\uFE00-\uFE0F\u200d]+\s*', '', name)
    # Also strip the mojibake version of emoji
    name = re.sub(r'^≡ƒ[^\s]+\s*', '', name)
    return name


def file_hash(path: Path) -> str:
    """Get MD5 hash of first 64KB for dedup."""
    h = hashlib.md5()
    try:
        with open(path, 'rb') as f:
            h.update(f.read(65536))
    except (OSError, PermissionError):
        return ""
    return h.hexdigest()


# ════════════════════════════════════════════════════════════════════
#  RULE-BASED MIGRATION MAPPINGS
# ════════════════════════════════════════════════════════════════════

def build_migration_plan() -> list[tuple[Path, Path, str]]:
    """
    Returns list of (source, destination, reason) tuples.
    Sources are absolute paths, destinations are relative to PROJECT_ROOT.
    """
    moves = []

    def add(src_rel: str, dst_rel: str, reason: str = ""):
        src = PROJECT_ROOT / src_rel
        if src.exists():
            moves.append((src, PROJECT_ROOT / dst_rel, reason))

    def add_glob(pattern: str, dst_dir: str, reason: str = "", rename_fn=None):
        """Add all files matching a glob pattern to a destination directory."""
        for f in sorted(PROJECT_ROOT.glob(pattern)):
            if f.is_file():
                name = rename_fn(f.name) if rename_fn else f.name
                moves.append((f, PROJECT_ROOT / dst_dir / name, reason))

    # ────────────────────────────────────────────────────────
    # 1. DASHBOARD JSON → data/dashboard/
    # ────────────────────────────────────────────────────────
    add_glob("engine_data/dashboard_public/*.json", "data/dashboard",
             "dashboard JSON from engine_data")
    add_glob("outputs/bd_dashboard/*.json", "data/dashboard",
             "dashboard JSON from outputs")

    # ────────────────────────────────────────────────────────
    # 2. ENRICHED CONTACTS → data/enriched/contacts/
    # ────────────────────────────────────────────────────────
    # Per-company enriched contacts (canonical: from_n8n_builder or Engine3)
    COMPANIES = [
        "Accenture", "Amentum", "Anduril", "AWS", "BAE_Systems", "Boeing",
        "Booz_Allen_Hamilton", "CACI", "Deloitte", "GDIT", "General_Dynamics",
        "Jacobs", "KBR", "L3Harris", "Leidos", "Lockheed_Martin", "ManTech",
        "Microsoft", "Northrop_Grumman", "Palantir", "Parsons", "Peraton",
        "Raytheon", "SAIC", "Sierra_Nevada", "Unclassified",
    ]
    for co in COMPANIES:
        # Enriched version is canonical
        add(f"data/from_n8n_builder/contacts/{co}_Contacts_Enriched.csv",
            f"data/enriched/contacts/by_company/{co}_Contacts_Enriched.csv",
            "enriched company contacts")

    # Cross-cutting contact files
    cross_cutting = {
        "Bullhorn_Contact_Search.csv": "Bullhorn_Contact_Search.csv",
        "Contact_Search_List_MASTER.csv": "Contact_Search_List_MASTER.csv",
        "DCGS_Contacts.csv": "DCGS_Contacts.csv",
        "DCGS_ContactsAll.csv": "DCGS_ContactsAll.csv",
        "DCGS Contact Sorted.csv": "DCGS_Contact_Sorted.csv",
        "DCGS Contact SortedAll.csv": "DCGS_Contact_SortedAll.csv",
        "GBSD Contact Chart Updated 9 4.csv": "GBSD_Contact_Chart.csv",
        "GBSD Contact Chart Updated 9 4 All.csv": "GBSD_Contact_Chart_All.csv",
        "GDIT PTS Contacts.csv": "GDIT_PTS_Contacts.csv",
        "GDIT PTS Contacts All.csv": "GDIT_PTS_Contacts_All.csv",
        "GDIT_Other_Contacts.csv": "GDIT_Other_Contacts.csv",
        "GDIT Other ContactsAll.csv": "GDIT_Other_ContactsAll.csv",
        "Lockheed Contact.csv": "Lockheed_Contact.csv",
        "Lockheed ContactAll.csv": "Lockheed_ContactAll.csv",
        "ZoomInfo_Contact_Search.csv": "ZoomInfo_Contact_Search.csv",
    }
    for orig, dest in cross_cutting.items():
        add(f"data/from_n8n_builder/contacts/{orig}",
            f"data/enriched/contacts/cross_cutting/{dest}",
            "cross-cutting contacts")

    # Raw (non-enriched) per-company contacts → archive (enriched supersedes)
    for co in COMPANIES:
        if co == "Unclassified":
            continue
        add(f"data/from_n8n_builder/contacts/{co}_Contacts.csv",
            f"data/archive/contacts_raw/{co}_Contacts.csv",
            "raw contacts archived (enriched supersedes)")

    # Templates
    add("data/from_n8n_builder/contacts/Contacts_TEMPLATE.csv",
        "data/reference/templates/Contacts_TEMPLATE.csv",
        "contact template")

    # ────────────────────────────────────────────────────────
    # 3. ENRICHED PROGRAMS → data/enriched/programs/
    # ────────────────────────────────────────────────────────
    add("engine_data/Engine2_ProgramMapping/Federal Programs MASTER V4.csv",
        "data/enriched/programs/Federal_Programs_MASTER_V4.csv",
        "latest programs master")
    add("engine_data/Engine2_ProgramMapping/Federal Programs MASTER ENRICHED.csv",
        "data/enriched/programs/Federal_Programs_MASTER_ENRICHED.csv",
        "enriched programs")
    add("engine_data/Engine2_ProgramMapping/Federal Programs TANGO ENRICHED.csv",
        "data/enriched/programs/Federal_Programs_TANGO_ENRICHED.csv",
        "tango enriched programs")
    add("engine_data/Engine2_ProgramMapping/Federal Programs ACTIVE ENRICHED V3.csv",
        "data/enriched/programs/Federal_Programs_ACTIVE_ENRICHED_V3.csv",
        "active enriched v3")
    add("data/from_data_scraper/MASTER_PROGRAMS_ENRICHED.csv",
        "data/enriched/programs/MASTER_PROGRAMS_ENRICHED.csv",
        "data scraper programs")
    add("data/from_data_scraper/PROGRAMS_CLEAN.csv",
        "data/enriched/programs/PROGRAMS_CLEAN.csv", "cleaned programs")
    add("data/from_data_scraper/PROGRAMS_FINAL.csv",
        "data/enriched/programs/PROGRAMS_FINAL.csv", "final programs")
    add("data/from_data_scraper/PROGRAMS_FROM_NOTES.csv",
        "data/enriched/programs/PROGRAMS_FROM_NOTES.csv", "programs from notes")
    add("data/from_data_scraper/GAP_PROGRAMS.csv",
        "data/enriched/programs/GAP_PROGRAMS.csv", "gap programs")
    add("data/from_data_scraper/PROGRAM_HIERARCHY.csv",
        "data/enriched/programs/PROGRAM_HIERARCHY.csv", "program hierarchy")
    add("data/from_data_scraper/PROGRAM_INTELLIGENCE.csv",
        "data/enriched/intelligence/PROGRAM_INTELLIGENCE.csv", "program intel")
    add("data/from_data_scraper/PROGRAM_INTELLIGENCE_DETAILED.csv",
        "data/enriched/intelligence/PROGRAM_INTELLIGENCE_DETAILED.csv", "detailed program intel")

    # Federal Programs archive (old versions)
    archive_programs = [
        "Federal Programs 9db40fce078142b9902cd4b0263b1e23.csv",
        "Federal Programs.csv",
        "Federal ProgramsAll.csv",
        "Federal Programs_BACKUP_20260119_1841.csv",
    ]
    for f in archive_programs:
        add(f"data/from_n8n_builder/analytical_outputs/{f}",
            f"data/archive/federal_programs_versions/{f.replace(' ', '_')}",
            "archived federal programs version")
        add(f"engine_data/Engine2_ProgramMapping/{f}",
            f"data/archive/federal_programs_versions/e2_{f.replace(' ', '_')}",
            "archived e2 federal programs version")

    # All the iteration versions
    fed_prog_versions = [
        "Federal Programs ACTIVE ENRICHED ENHANCED.csv",
        "Federal Programs ACTIVE ENRICHED V2.csv",
        "Federal Programs ACTIVE ENRICHED V4 TANGO.csv",
        "Federal Programs ACTIVE ENRICHED.csv",
        "Federal Programs ACTIVE.csv",
        "Federal Programs COMPLETE ENRICHED.csv",
        "Federal Programs ENRICHED.csv",
        "Federal Programs FULLY ENRICHED.csv",
        "Federal Programs MASTER V2 HIGH SUB.csv",
        "Federal Programs MASTER.csv",
        "Federal Programs REMOVED.csv",
        "Federal Programs MASTER ENRICHED.csv",
        "Federal Programs MASTER V4.csv",
        "Federal Programs TANGO ENRICHED.csv",
    ]
    for f in fed_prog_versions:
        add(f"data/from_n8n_builder/analytical_outputs/{f}",
            f"data/archive/federal_programs_versions/{f.replace(' ', '_')}",
            "archived federal programs version")
    add("data/from_n8n_builder/analytical_outputs/Federal Programs MASTER V2 HIGH SUB.xlsx",
        "data/archive/federal_programs_versions/Federal_Programs_MASTER_V2_HIGH_SUB.xlsx",
        "archived xlsx version")

    # ────────────────────────────────────────────────────────
    # 4. ENRICHED CONTRACTS → data/enriched/contracts/
    # ────────────────────────────────────────────────────────
    add("data/from_data_scraper/MASTER_CONTRACTS_COMBINED.csv",
        "data/enriched/contracts/MASTER_CONTRACTS_COMBINED.csv", "master contracts")
    add("data/from_data_scraper/FULL_PROGRAM_CONTRACTS.csv",
        "data/enriched/contracts/FULL_PROGRAM_CONTRACTS.csv", "full program contracts")
    add("data/from_data_scraper/PHASE3_ALL_PROGRAM_CONTRACTS.csv",
        "data/enriched/contracts/PHASE3_ALL_PROGRAM_CONTRACTS.csv", "phase3 contracts")
    add("data/from_data_scraper/PHASE2_PROGRAM_PIIDS_FULL.csv",
        "data/enriched/contracts/PHASE2_PROGRAM_PIIDS_FULL.csv", "phase2 PIIDs")
    add("data/from_data_scraper/PHASE5_RECENT_ACTIVE_CONTRACTS.csv",
        "data/enriched/contracts/PHASE5_RECENT_ACTIVE_CONTRACTS.csv", "recent active")
    add("data/from_data_scraper/L3Harris_GBS_PROGRAM_CONTRACTS.csv",
        "data/enriched/contracts/L3Harris_GBS_PROGRAM_CONTRACTS.csv", "L3Harris GBS")
    add("data/from_data_scraper/L3Harris_SATCOM_RF_CONTRACTS.csv",
        "data/enriched/contracts/L3Harris_SATCOM_RF_CONTRACTS.csv", "L3Harris SATCOM")
    add("data/from_n8n_builder/analytical_outputs/programs_with_contracts.csv",
        "data/enriched/contracts/programs_with_contracts.csv", "programs with contracts")

    # ────────────────────────────────────────────────────────
    # 5. ENRICHED JOBS → data/enriched/jobs/
    # ────────────────────────────────────────────────────────
    add("data/from_data_scraper/JOBS_ENRICHED.csv",
        "data/enriched/jobs/JOBS_ENRICHED.csv", "enriched jobs")
    add("data/from_data_scraper/JOBS_INTELLIGENCE_MAPPED.csv",
        "data/enriched/jobs/JOBS_INTELLIGENCE_MAPPED.csv", "jobs intel mapped")
    add("data/from_data_scraper/jobs_master.csv",
        "data/enriched/jobs/jobs_master.csv", "jobs master")
    add("data/from_data_scraper/bd_top_program_jobs_detail.csv",
        "data/enriched/jobs/bd_top_program_jobs_detail.csv", "top program jobs")
    add("engine_data/Engine1_Scraper/Jobs_Mapped_to_Programs_MASTER.csv",
        "data/enriched/jobs/Jobs_Mapped_to_Programs_MASTER.csv", "mapped jobs master")
    add("engine_data/Engine1_Scraper/Jobs_Mapped_to_Programs_2026-01-19.csv",
        "data/enriched/jobs/Jobs_Mapped_to_Programs_2026-01-19.csv", "mapped jobs snapshot")

    # ────────────────────────────────────────────────────────
    # 6. ENRICHED PRIMES → data/enriched/primes/
    # ────────────────────────────────────────────────────────
    add("data/from_data_scraper/MASTER_PRIMES_ENRICHED.csv",
        "data/enriched/primes/MASTER_PRIMES_ENRICHED.csv", "master primes")
    add("data/from_data_scraper/PRIMES_CLEAN.csv",
        "data/enriched/primes/PRIMES_CLEAN.csv", "primes clean")
    add("data/from_data_scraper/PRIMES_FINAL.csv",
        "data/enriched/primes/PRIMES_FINAL.csv", "primes final")
    add("data/from_data_scraper/PRIMES_FROM_NOTES.csv",
        "data/enriched/primes/PRIMES_FROM_NOTES.csv", "primes from notes")
    add("data/from_data_scraper/PRIME_INTELLIGENCE_DETAILED.csv",
        "data/enriched/primes/PRIME_INTELLIGENCE_DETAILED.csv", "prime intel")
    add("data/from_data_scraper/PRIME_SCORECARD.csv",
        "data/enriched/primes/PRIME_SCORECARD.csv", "prime scorecard")
    add("data/from_data_scraper/FULL_PRIME_ENRICHMENT.csv",
        "data/enriched/primes/FULL_PRIME_ENRICHMENT.csv", "full prime enrichment")
    add("data/from_data_scraper/primes_usaspending_enriched.csv",
        "data/enriched/primes/primes_usaspending_enriched.csv", "usaspending primes")

    # ────────────────────────────────────────────────────────
    # 7. ENRICHED TARGETS → data/enriched/targets/
    # ────────────────────────────────────────────────────────
    add("data/from_data_scraper/master_bd_targets.csv",
        "data/enriched/targets/master_bd_targets.csv", "master BD targets")
    add("data/from_data_scraper/master_bd_targets_fpds_enriched.csv",
        "data/enriched/targets/master_bd_targets_fpds_enriched.csv", "FPDS enriched targets")
    add("data/from_data_scraper/master_bd_targets_contract_enriched.csv",
        "data/enriched/targets/master_bd_targets_contract_enriched.csv", "contract enriched targets")
    add("data/from_data_scraper/db6_bd_targets_all.csv",
        "data/enriched/targets/db6_bd_targets_all.csv", "all targets")
    add("data/from_data_scraper/db6_bd_targets_priority.csv",
        "data/enriched/targets/db6_bd_targets_priority.csv", "priority targets")
    add("data/from_data_scraper/tier1_high_priority_targets.csv",
        "data/enriched/targets/tier1_high_priority_targets.csv", "tier1")
    add("data/from_data_scraper/tier2_medium_priority_targets.csv",
        "data/enriched/targets/tier2_medium_priority_targets.csv", "tier2")
    add("data/from_data_scraper/tier3_standard_targets.csv",
        "data/enriched/targets/tier3_standard_targets.csv", "tier3")

    # Size-based target segments
    for f in ["size_billion_1b_5b", "size_giant_5b_10b", "size_large_500m_1b", "size_mega_10b_plus"]:
        add(f"data/from_data_scraper/{f}.csv",
            f"data/enriched/targets/{f}.csv", "size segment")

    add("data/from_data_scraper/agency_Department_of_Defense.csv",
        "data/enriched/targets/agency_Department_of_Defense.csv", "DoD targets")
    add("data/from_data_scraper/high_subcontract_activity.csv",
        "data/enriched/targets/high_subcontract_activity.csv", "high sub activity")
    add("data/from_data_scraper/it_services_all_targets.csv",
        "data/enriched/targets/it_services_all_targets.csv", "IT services targets")

    # ────────────────────────────────────────────────────────
    # 8. ENRICHED INTELLIGENCE → data/enriched/intelligence/
    # ────────────────────────────────────────────────────────
    add("data/from_data_scraper/CONTACT_INTELLIGENCE_DETAILED.csv",
        "data/enriched/intelligence/CONTACT_INTELLIGENCE_DETAILED.csv", "contact intel")
    add("data/from_data_scraper/CONTACTS_INTELLIGENCE.csv",
        "data/enriched/intelligence/CONTACTS_INTELLIGENCE.csv", "contacts intel")
    add("data/from_data_scraper/ORG_CHART_DATA.csv",
        "data/enriched/intelligence/ORG_CHART_DATA.csv", "org chart")
    add("data/from_data_scraper/FULL_OPPORTUNITIES.csv",
        "data/enriched/intelligence/FULL_OPPORTUNITIES.csv", "opportunities")
    add("data/from_data_scraper/PHASE1_CLAIMED_CONTACTS.csv",
        "data/enriched/intelligence/PHASE1_CLAIMED_CONTACTS.csv", "claimed contacts")
    add("data/from_data_scraper/PHASE1_FAIR_GAME_CONTACTS.csv",
        "data/enriched/intelligence/PHASE1_FAIR_GAME_CONTACTS.csv", "fair game contacts")
    add("data/from_data_scraper/ALL_NOTES_COMBINED.csv",
        "data/enriched/intelligence/ALL_NOTES_COMBINED.csv", "combined notes")
    add("data/from_data_scraper/AUTHOR_PERFORMANCE.csv",
        "data/enriched/intelligence/AUTHOR_PERFORMANCE.csv", "author performance")
    add("data/from_data_scraper/NARRATIVE_INDEX.csv",
        "data/enriched/intelligence/NARRATIVE_INDEX.csv", "narrative index")

    # Intelligence reports (markdown)
    intel_reports = [
        "COMPREHENSIVE_BD_INTELLIGENCE_REPORT.md",
        "CONTACT_ORG_REPORT.md",
        "EXECUTIVE_DASHBOARD.md",
        "JOBS_ANALYSIS_REPORT.md",
        "PAST_PERFORMANCE_FINAL.md",
        "PAST_PERFORMANCE_NARRATIVE.md",
        "PAST_PERFORMANCE_REPORT_ENHANCED.md",
        "PROGRAM_HIERARCHY_REPORT.md",
    ]
    for f in intel_reports:
        add(f"data/from_data_scraper/{f}",
            f"data/enriched/intelligence/{f}", "intelligence report")

    # Past performance by company
    add_glob("data/from_data_scraper/*_past_performance.md",
             "data/enriched/intelligence/past_performance",
             "company past performance")

    # Dossiers by company
    add_glob("data/from_data_scraper/*_dossier.md",
             "data/enriched/intelligence/dossiers",
             "company dossier")

    # ────────────────────────────────────────────────────────
    # 9. RAW SCRAPER DATA → data/raw/scraper/
    # ────────────────────────────────────────────────────────
    add_glob("engine_data/Engine1_Scraper/dataset_*.json", "data/raw/scraper",
             "raw scraper JSON")
    add_glob("engine_data/Engine1_Scraper/dataset_*.csv", "data/raw/scraper",
             "raw scraper CSV")
    add("engine_data/Engine1_Scraper/Sample_Jobs.json",
        "data/raw/scraper/Sample_Jobs.json", "sample jobs")
    for name in ["Apex Job Scrape.json", "Apex Job Scrape2.json",
                  "Insight Global Scrape.json"]:
        add(f"engine_data/Engine1_Scraper/{name}",
            f"data/raw/scraper/{name.replace(' ', '_')}", "scraper output")

    # ────────────────────────────────────────────────────────
    # 10. RAW BULLHORN → data/raw/bullhorn/
    # ────────────────────────────────────────────────────────
    # UUID-named job records
    uuid_pattern = re.compile(r'^[0-9A-F]{8}-[0-9A-F]{4}', re.IGNORECASE)
    for f in sorted((PROJECT_ROOT / "data/from_n8n_builder/bullhorn").glob("*.csv")):
        name = f.name
        if uuid_pattern.match(name):
            if "_" in name and not name.endswith("B741.csv"):
                # Activity report (Client Submissions, Interviews, etc.)
                moves.append((f, PROJECT_ROOT / "data/raw/bullhorn/sales_activity" / name.replace(' ', '_'),
                              "bullhorn activity report"))
            else:
                moves.append((f, PROJECT_ROOT / "data/raw/bullhorn/job_records" / name,
                              "bullhorn job record"))
        elif name.startswith("Sales Activity"):
            moves.append((f, PROJECT_ROOT / "data/raw/bullhorn/sales_activity" / name.replace(' ', '_'),
                          "sales activity report"))
        elif name in ("Client_Submissions.csv", "Client_Visits.csv", "Interviews.csv",
                       "Job_Client_Interviews.csv", "Job_Client_Submissions.csv",
                       "Job_Submissions.csv", "New_Contacts.csv", "Submissions.csv"):
            moves.append((f, PROJECT_ROOT / "data/raw/bullhorn/aggregate_reports" / name,
                          "bullhorn aggregate"))

    # Bullhorn analysis summary JSONs
    add("data/from_n8n_builder/bullhorn/_analysis_summary.json",
        "data/raw/bullhorn/analysis_summary.json", "bullhorn analysis")
    add("data/from_n8n_builder/bullhorn/_comprehensive_summary.json",
        "data/raw/bullhorn/comprehensive_summary.json", "bullhorn summary")

    # Bullhorn special files
    add("data/from_n8n_builder/bullhorn/07_PROGRAM_MATRIX.csv",
        "data/bullhorn_analysis/ANALYSIS/07_PROGRAM_MATRIX.csv", "program matrix")
    add("data/from_n8n_builder/bullhorn/07_PROGRAM_MATRIX_V2.csv",
        "data/bullhorn_analysis/ANALYSIS/07_PROGRAM_MATRIX_V2.csv", "program matrix v2")
    add("data/from_n8n_builder/bullhorn/COLTON_SCURRY_CONTACTS_MASTER.csv",
        "data/bullhorn_analysis/source_csvs/COLTON_SCURRY_CONTACTS_MASTER.csv",
        "scurry contacts master")
    add("data/from_n8n_builder/bullhorn/MASTER_DATA_AGGREGATION.csv",
        "data/bullhorn_analysis/ANALYSIS/NOTES_DEEP_DIVE/MASTER_DATA_AGGREGATION.csv",
        "master data aggregation")

    # Bullhorn data from data_scraper
    add("data/from_data_scraper/bullhorn_programs_master.csv",
        "data/enriched/programs/bullhorn_programs_master.csv", "bullhorn programs")
    add("data/from_data_scraper/bullhorn_primes_master.csv",
        "data/enriched/primes/bullhorn_primes_master.csv", "bullhorn primes")
    add("data/from_data_scraper/bullhorn_contacts_master.csv",
        "data/enriched/contacts/cross_cutting/bullhorn_contacts_master.csv",
        "bullhorn contacts master")

    # Scurry handoff data
    add("data/from_data_scraper/colton_scurry_contacts.csv",
        "data/deliverables/coworker_takeover/colton_scurry_contacts.csv", "scurry contacts")
    add("data/from_data_scraper/colton_scurry_jobs.csv",
        "data/deliverables/coworker_takeover/colton_scurry_jobs.csv", "scurry jobs")
    add("data/from_data_scraper/colton_scurry_contact_handoff.csv",
        "data/deliverables/coworker_takeover/colton_scurry_contact_handoff.csv", "scurry handoff")

    # ────────────────────────────────────────────────────────
    # 11. RAW NOTION EXPORTS → data/raw/notion_exports/
    # ────────────────────────────────────────────────────────
    notion_mapping = {
        "Federal Programs 9db40fce078142b9902cd4b0263b1e23.csv": "federal_programs",
        "Federal Programs 9db40fce078142b9902cd4b0263b1e23.html": "federal_programs",
        "BD Opportunities.csv": "bd_opportunities",
        "BD OpportunitiesAll.csv": "bd_opportunities",
        "Contractors Database.csv": "contractors",
        "Contractors Database All.csv": "contractors",
        "Contractors.csv": "contractors",
        "Contract_Vehicles.csv": "contract_vehicles",
        "Contract_VehiclesAll.csv": "contract_vehicles",
        "Programs_KB.csv": "programs_kb",
        "Programs_KBAll.csv": "programs_kb",
        "GDIT Jobs 2.csv": "jobs",
        "GDIT Jobs 2All.csv": "jobs",
        "BD IntelliRepo File Management.csv": "intellirepo",
        "BD IntelliRepo File ManagementAll.csv": "intellirepo",
        "Program Mapping Intelligence Hub.csv": "programs_kb",
        "Program Mapping Intelligence Hub All.csv": "programs_kb",
    }
    for orig, folder in notion_mapping.items():
        add(f"Engine2_ProgramMapping/data/{orig}",
            f"data/raw/notion_exports/{folder}/{orig.replace(' ', '_')}",
            "notion export")

    # ────────────────────────────────────────────────────────
    # 12. RAW FEDERAL API DATA → data/raw/federal_apis/
    # ────────────────────────────────────────────────────────
    add("data/from_data_scraper/db1_dod_prime_contracts_100m.csv",
        "data/raw/federal_apis/contracts/db1_dod_prime_contracts_100m.csv", "DoD contracts")
    add("data/from_data_scraper/db2_subawards_tango.csv",
        "data/raw/federal_apis/subawards/db2_subawards_tango.csv", "Tango subawards")
    add("data/from_data_scraper/db3_dod_opportunities_all.csv",
        "data/raw/federal_apis/opportunities/db3_dod_opportunities_all.csv", "DoD opps")
    add("data/from_data_scraper/db3_dod_solicitations.csv",
        "data/raw/federal_apis/opportunities/db3_dod_solicitations.csv", "DoD solicitations")
    add("data/from_data_scraper/db3_dod_it_opportunities.csv",
        "data/raw/federal_apis/opportunities/db3_dod_it_opportunities.csv", "DoD IT opps")
    add("data/from_data_scraper/phase3_opportunities_tango.csv",
        "data/raw/federal_apis/opportunities/phase3_opportunities_tango.csv", "tango opps")
    add("data/from_data_scraper/phase3_solicitations_only.csv",
        "data/raw/federal_apis/opportunities/phase3_solicitations_only.csv", "solicitations only")
    add("data/from_data_scraper/sam_data_elements.csv",
        "data/raw/federal_apis/contracts/sam_data_elements.csv", "SAM data elements")
    add("data/from_data_scraper/navy_subaward_N00019.csv",
        "data/raw/federal_apis/subawards/navy_subaward_N00019.csv", "Navy subaward")

    # USAspending contract downloads
    add_glob("data/from_n8n_builder/analytical_outputs/Contract_N0001920C0032_*.csv",
             "data/raw/federal_apis/contracts",
             "USAspending contract data")

    # ────────────────────────────────────────────────────────
    # 13. RAW ZOOMINFO → data/raw/zoominfo/
    # ────────────────────────────────────────────────────────
    add("data/from_data_scraper/ZOOMINFO_L3HARRIS.csv",
        "data/raw/zoominfo/ZOOMINFO_L3HARRIS.csv", "ZoomInfo L3Harris")

    # ────────────────────────────────────────────────────────
    # 14. DELIVERABLES → data/deliverables/
    # ────────────────────────────────────────────────────────
    # Briefings
    add_glob("outputs/BD_Briefings/*.md", "data/deliverables/briefings",
             "BD briefing")
    add_glob("outputs/BD_Briefings/*.txt", "data/deliverables/briefings",
             "BD briefing email")

    # Call lists
    add("outputs/call_sheet.csv", "data/deliverables/call_lists/call_sheet.csv", "call sheet")
    add("outputs/gdit_call_sheet.csv", "data/deliverables/call_lists/gdit_call_sheet.csv", "GDIT call sheet")
    add("outputs/bd_call_sheet_20260119_005930.csv",
        "data/deliverables/call_lists/bd_call_sheet_20260119.csv", "BD call sheet")
    add("data/from_n8n_builder/analytical_outputs/AM_CALL_LIST.xlsx",
        "data/deliverables/call_lists/AM_CALL_LIST.xlsx", "AM call list")
    add("data/from_n8n_builder/analytical_outputs/MASTER_CONTACTS_CHEAT_SHEET.xlsx",
        "data/deliverables/call_lists/MASTER_CONTACTS_CHEAT_SHEET.xlsx", "contacts cheat sheet")
    add("outputs/call_script_template.txt",
        "data/deliverables/call_lists/call_script_template.txt", "call script template")
    add("outputs/george_call_script.txt",
        "data/deliverables/call_lists/george_call_script.txt", "george call script")

    # Playbooks
    add("outputs/BD_Playbook_2026-01-23.md",
        "data/deliverables/playbooks/BD_Playbook_2026-01-23.md", "BD playbook")
    add("outputs/HUMINT_BD_BRIEFINGS_2026-01-24.md",
        "data/deliverables/playbooks/HUMINT_BD_BRIEFINGS_2026-01-24.md", "HUMINT briefings")
    add("outputs/HUMINT_JRSS_MONTGOMERY_2026-02-03.md",
        "data/deliverables/playbooks/HUMINT_JRSS_MONTGOMERY_2026-02-03.md", "HUMINT JRSS")
    add("outputs/bd_playbook_monday_20260119_012059.csv",
        "data/archive/playbook_versions/bd_playbook_monday_20260119_012059.csv", "old playbook")
    add("outputs/bd_playbook_monday_20260119_012144.csv",
        "data/archive/playbook_versions/bd_playbook_monday_20260119_012144.csv", "old playbook")

    # Reports
    add("outputs/BD_Pipeline_Report_2026-01-19_15-45.xlsx",
        "data/deliverables/reports/BD_Pipeline_Report_2026-01-19.xlsx", "pipeline report")
    add("outputs/PROGRAM_PLACEMENT_GAP_ANALYSIS_20260122.csv",
        "data/deliverables/reports/PROGRAM_PLACEMENT_GAP_ANALYSIS.csv", "gap analysis")
    add("outputs/QUICK_ACTION_SHEET_20260122.md",
        "data/deliverables/reports/QUICK_ACTION_SHEET.md", "quick action sheet")
    add("outputs/SESSION_SUMMARY_20260119.md",
        "data/deliverables/reports/SESSION_SUMMARY_20260119.md", "session summary")
    add("outputs/ZOOMINFO_EXPORT_STRATEGY_COMPREHENSIVE_20260122.md",
        "data/deliverables/reports/ZOOMINFO_EXPORT_STRATEGY.md", "zoominfo strategy")
    add("outputs/ZOOMINFO_STRATEGY_V2_CALL_NOTES_INTEGRATED_20260122.md",
        "data/deliverables/reports/ZOOMINFO_STRATEGY_V2.md", "zoominfo v2")
    add("outputs/ZoomInfo_Master_Search_List_2026-01-23.md",
        "data/deliverables/reports/ZoomInfo_Master_Search_List.md", "zoominfo search list")
    add("outputs/ZoomInfo_Research_List_2026-01-23.md",
        "data/deliverables/reports/ZoomInfo_Research_List.md", "zoominfo research list")
    add("outputs/job_opportunities_20260119_083758.csv",
        "data/deliverables/reports/job_opportunities_20260119.csv", "job opportunities")

    # Coworker takeover
    add_glob("outputs/coworker_takeover/*.md", "data/deliverables/coworker_takeover",
             "takeover doc")
    add_glob("outputs/coworker_takeover/*.csv", "data/deliverables/coworker_takeover",
             "takeover CSV")
    add_glob("outputs/coworker_takeover/*.json", "data/deliverables/coworker_takeover",
             "takeover JSON")
    add_glob("outputs/coworker_takeover/programs/*.md",
             "data/deliverables/coworker_takeover/programs", "takeover program brief")

    # ────────────────────────────────────────────────────────
    # 15. BULLHORN ANALYSIS → data/bullhorn_analysis/ (intact)
    # ────────────────────────────────────────────────────────
    bh_analysis = PROJECT_ROOT / "Engine7_BullhornETL/colton_scurry_analysis"
    if bh_analysis.exists():
        for f in sorted(bh_analysis.glob("ANALYSIS/*.md")):
            moves.append((f, PROJECT_ROOT / f"data/bullhorn_analysis/ANALYSIS/{f.name}",
                          "bullhorn analysis report"))
        for f in sorted(bh_analysis.glob("ANALYSIS/*.csv")):
            moves.append((f, PROJECT_ROOT / f"data/bullhorn_analysis/ANALYSIS/{f.name}",
                          "bullhorn analysis CSV"))
        for f in sorted(bh_analysis.glob("ANALYSIS/*.txt")):
            moves.append((f, PROJECT_ROOT / f"data/bullhorn_analysis/ANALYSIS/{f.name}",
                          "bullhorn analysis TXT"))
        for f in sorted(bh_analysis.glob("ANALYSIS/NOTES_DEEP_DIVE/*.*")):
            moves.append((f, PROJECT_ROOT / f"data/bullhorn_analysis/ANALYSIS/NOTES_DEEP_DIVE/{f.name}",
                          "bullhorn notes deep dive"))
        for f in sorted(bh_analysis.glob("FINAL_OUTPUTS/*.*")):
            moves.append((f, PROJECT_ROOT / f"data/bullhorn_analysis/FINAL_OUTPUTS/{f.name}",
                          "bullhorn final output"))
        add("Engine7_BullhornETL/colton_scurry_analysis/COLTON_SCURRY_COMPREHENSIVE_ANALYSIS_REPORT.md",
            "data/bullhorn_analysis/COLTON_SCURRY_COMPREHENSIVE_ANALYSIS_REPORT.md",
            "scurry analysis master")
        # Source CSVs
        for f in sorted(bh_analysis.glob("*.csv")):
            moves.append((f, PROJECT_ROOT / f"data/bullhorn_analysis/source_csvs/{f.name}",
                          "bullhorn source CSV"))
        for f in sorted(bh_analysis.glob("*.xlsx")):
            moves.append((f, PROJECT_ROOT / f"data/bullhorn_analysis/source_csvs/{f.name}",
                          "bullhorn source xlsx"))
        add("Engine7_BullhornETL/colton_scurry_analysis/colton_scurry_analysis_stats.json",
            "data/bullhorn_analysis/colton_scurry_analysis_stats.json",
            "analysis stats")

    # ────────────────────────────────────────────────────────
    # 16. REFERENCE DATA → data/reference/
    # ────────────────────────────────────────────────────────
    # FPDS code tables
    fpds_files = [
        "action_type_code.csv", "assistance_type_code.csv",
        "business_funds_indicator_code.csv", "CCRexception.csv",
        "cfda_number.csv", "ContingencyHumanitarianPeacekeepingOperation.csv",
        "FinancingStatus.csv", "FinancingType.csv", "NationalInterestActionCode.csv",
        "CompetitionClassification.csv", "contract.TypeOfContractPricing.csv",
        "CSIS_contract_inspection.csv", "LetterContract.csv",
        "ReasonForModification.csv", "Vehicle.csv", "ContractActionType.csv",
        "Contract_LargeVendorLabeledAsSmallBusiness.csv",
        "ExtentCompleted.csv",
    ]
    for f in fpds_files:
        add(f"data/from_n8n_builder/analytical_outputs/{f}",
            f"data/reference/fpds/{f}", "FPDS code table")

    # USAspending reference
    usaspending_files = [
        "Agency_AgencyID.csv", "Agency_TreasuryAccountCode.csv",
        "Budget_CostType.csv", "Budget_FundedByForeignEntity.csv",
        "Budget_MainAccountCode.csv", "Budget_SubAccountCode.csv",
        "Data_Feed_State_FY2017_2018_01_22.csv",
    ]
    for f in usaspending_files:
        add(f"data/from_n8n_builder/analytical_outputs/{f}",
            f"data/reference/usaspending/{f}", "USAspending reference")

    add("data/from_n8n_builder/analytical_outputs/Data_Dictionary_Crosswalk.xlsx",
        "data/reference/usaspending/Data_Dictionary_Crosswalk.xlsx",
        "USAspending data dictionary")

    # NAICS/PSC
    naics_files = [
        "Lookup_PrincipalNAICScode.csv", "naics_hightech_bls.csv",
        "ProdServPlatformNAICS.csv",
    ]
    for f in naics_files:
        add(f"data/from_n8n_builder/analytical_outputs/{f}",
            f"data/reference/naics_psc/{f}", "NAICS/PSC reference")

    # Geo/economic
    geo_files = [
        "countries_in_dataset.csv", "A191RD3A086NBEA.csv",
        "CN2023.csv", "commodity_translations_merge.csv",
        "corruptionpi_long.csv", "corruptionpi_lookup.csv",
        "FormerCFIUScriticalTech.csv", "hist10z1_fy22.csv", "hts10.csv",
        "Lookup_Calendar_Deflator.csv", "Lookup_Deflators.csv",
        "Lookup_Fiscal_Year_Period.csv",
        "nama_10_gdp__custom_6102823_linear.csv",
    ]
    for f in geo_files:
        add(f"data/from_n8n_builder/analytical_outputs/{f}",
            f"data/reference/geo_economic/{f}", "geo/economic reference")

    # Templates
    add("engine_data/Engine2_ProgramMapping/Programs_KB_TEMPLATE.csv",
        "data/reference/templates/Programs_KB_TEMPLATE.csv", "programs KB template")
    add("engine_data/Engine3_OrgChart/Contacts_TEMPLATE.csv",
        "data/reference/templates/Contacts_TEMPLATE.csv", "contacts template (engine3)")

    # ────────────────────────────────────────────────────────
    # 17. DOD STAFFING VERSIONS → data/archive/dod_staffing_versions/
    # ────────────────────────────────────────────────────────
    dod_staffing = [
        "dod-staffing-programs-FINAL-FIXED.csv",
        "dod-staffing-programs-FINAL-WORKING.csv",
        "dod-staffing-programs-PHASE1-FIXED.csv",
        "dod-staffing-programs-PHASE1-RAW.csv",
        "dod-staffing-programs-PHASE1-WORKING.csv",
        "dod-staffing-programs-PHASE2-WITH-TARGETS.csv",
    ]
    for f in dod_staffing:
        add(f"data/from_n8n_builder/analytical_outputs/{f}",
            f"data/archive/dod_staffing_versions/{f}", "DoD staffing version")

    # ────────────────────────────────────────────────────────
    # 18. DISCOVERED PROGRAMS → data/enriched/programs/
    # ────────────────────────────────────────────────────────
    add("data/from_n8n_builder/analytical_outputs/DISCOVERED_PROGRAMS_ALL_V2.csv",
        "data/enriched/programs/DISCOVERED_PROGRAMS_ALL_V2.csv", "discovered programs")
    add("data/from_n8n_builder/analytical_outputs/DISCOVERED_PROGRAMS_QUALIFIED_V2.csv",
        "data/enriched/programs/DISCOVERED_PROGRAMS_QUALIFIED_V2.csv", "qualified programs")

    # ────────────────────────────────────────────────────────
    # 19. HISTORICAL FPDS/USASPENDING → data/archive/
    # ────────────────────────────────────────────────────────
    add_glob("data/from_n8n_builder/analytical_outputs/2012-*_*.csv",
             "data/archive/historical_fpds_usaspending",
             "historical FPDS/USAspending data")

    # ────────────────────────────────────────────────────────
    # 20. ANALYTICAL OUTPUT MDs → data/deliverables/reports/
    # ────────────────────────────────────────────────────────
    analytical_reports = [
        "00_MASTER_ORCHESTRATION_GUIDE.md",
        "00_QUICK_REFERENCE_CARD.md",
        "01_EXECUTIVE_SUMMARY.md",
        "02_PRIME_CONTRACTOR_BREAKDOWN.md",
        "03_ACTIVE_PLACEMENTS.md",
        "04_OPEN_JOBS_PIPELINE.md",
        "05_CONTACTS_DATABASE.md",
        "06_BD_PLAYBOOK.md",
        "08_TRANSITION_CHECKLIST.md",
        "09_PROGRAM_MASTER_LIST.md",
        "10_PROGRAM_MASTER_LIST_COMPLETE.md",
        "AGGREGATED_NOTES_BY_CONTACT.md",
        "COLTON_SCURRY_AUTHORED_NOTES_MASTER.md",
        "ACTIONABLE_INSIGHTS_REPORT.md",
        "CONTACT_PROGRAM_MATRIX.md",
        "FULL_NOTES_EXPORT.md",
        "NOTES_INTELLIGENCE_EXTRACT.md",
        "ORG_STRUCTURE_MAP.md",
        "PRIME_CONTRACTOR_PROGRAMS.md",
        "PROGRAM_COMPLETE_DATABASE.md",
        "RAW_SHEETS_EXPORT.md",
        "NOTES_EXTRACTED.md",
        "BD_INTELLIGENCE_HUB_MASTER_UTILIZATION_GUIDE.md",
        "COMPREHENSIVE_BD_HUB_MASTER_PLAN_V2.md",
    ]
    for f in analytical_reports:
        add(f"data/from_n8n_builder/analytical_outputs/{f}",
            f"data/deliverables/reports/{f}", "analytical report")

    # Scurry-specific from analytical outputs
    add("data/from_n8n_builder/analytical_outputs/COLTON_SCURRY_CONTACTS_MASTER.xlsx",
        "data/deliverables/coworker_takeover/COLTON_SCURRY_CONTACTS_MASTER.xlsx",
        "scurry contacts xlsx")
    add("data/from_n8n_builder/analytical_outputs/Notes Activity Report scurry.xlsx",
        "data/deliverables/coworker_takeover/Notes_Activity_Report_Scurry.xlsx",
        "scurry notes report")

    # ────────────────────────────────────────────────────────
    # 21. NOTION API DUMPS → data/archive/notion_api_dumps/
    # ────────────────────────────────────────────────────────
    add_glob("outputs/db_*.json", "data/archive/notion_api_dumps",
             "Notion API dump")
    add_glob("outputs/db_data_*.json", "data/archive/notion_api_dumps",
             "Notion API data dump")
    add("outputs/all_databases.json",
        "data/archive/notion_api_dumps/all_databases.json", "all databases dump")
    add("outputs/all_dbs.json",
        "data/archive/notion_api_dumps/all_dbs.json", "all dbs dump")
    add("outputs/notion_dbs.json",
        "data/archive/notion_api_dumps/notion_dbs.json", "notion dbs dump")

    # ────────────────────────────────────────────────────────
    # 22. CONTRACTORS ITERATIONS → data/archive/
    # ────────────────────────────────────────────────────────
    contractors_archive = [
        "contractors_cleanup1.json", "contractors_data.json",
        "contractors_data_full.json", "contractors_del1.json",
        "contractors_del2.json", "contractors_del3.json",
        "contractors_del4.json", "contractors_del5.json",
        "contractors_final.json", "contractors_fresh.json",
        "contractors_schema.json",
    ]
    for f in contractors_archive:
        add(f"outputs/{f}", f"data/archive/contractors_iterations/{f}",
            "contractors iteration")

    # CV iterations
    cv_archive = ["cv_data.json", "cv_del1.json", "cv_del2.json",
                   "cv_final.json", "cv_schema.json", "cv_search.json"]
    for f in cv_archive:
        add(f"outputs/{f}", f"data/archive/cv_iterations/{f}", "CV iteration")

    # ────────────────────────────────────────────────────────
    # 23. ENGINE1 ITERATIONS → data/archive/engine1_iterations/
    # ────────────────────────────────────────────────────────
    engine1_files = [
        "engine1_ai_enriched.json", "engine1_fallback_enriched.json",
        "engine1_fully_enriched.json", "engine1_parsed.json",
        "engine1_pts_refreshed.json", "engine1_relational_enriched.json",
    ]
    for f in engine1_files:
        add(f"outputs/{f}", f"data/archive/engine1_iterations/{f}",
            "engine1 iteration")

    # Job enrichment iterations
    job_archive = ["all_jobs_complete.json", "all_jobs_enriched.json",
                    "all_jobs_fully_enriched.json", "all_jobs_with_hiring_leaders.json",
                    "enriched_jobs.json"]
    for f in job_archive:
        add(f"outputs/{f}", f"data/archive/engine1_iterations/{f}",
            "job enrichment iteration")

    # ────────────────────────────────────────────────────────
    # 24. STATE/MISC OUTPUTS → data/state/ or archive
    # ────────────────────────────────────────────────────────
    add("data/from_data_scraper/data_inventory.json",
        "data/state/data_inventory.json", "data inventory")
    add("data/from_data_scraper/hub_jobs_2026-01-26.json",
        "data/state/hub_jobs_2026-01-26.json", "hub jobs snapshot")
    add("data/from_data_scraper/standardized_jobs_2026-01-26.json",
        "data/state/standardized_jobs_2026-01-26.json", "standardized jobs snapshot")

    # Misc outputs that are API exploration dumps
    misc_archive = [
        "dcgs_contacts_data.json", "dcgs_contacts_schema.json",
        "dcgs_final.json", "dcgs_props.json",
        "enrich_log_check.json", "enrich_log_data.json", "enrich_log_schema.json",
        "federal_programs_current.json", "federal_programs_data.json",
        "federal_programs_schema.json", "federal_programs_schema2.json",
        "federal_programs_updated.json", "fp_final.json",
        "gdit_other_data.json", "gdit_other_schema.json",
        "gdit_pts_data.json", "gdit_pts_schema.json",
        "intellirepo_del.json", "one_contact.json",
        "pmh_data.json", "pmh_final.json", "pmh_props.json", "pmh_schema.json",
        "bd_events_del.json", "bd_opps_del.json",
        "prime_summary.txt",
    ]
    for f in misc_archive:
        add(f"outputs/{f}", f"data/archive/notion_api_dumps/{f}",
            "API exploration dump")

    # ────────────────────────────────────────────────────────
    # 25. ANALYTICAL OUTPUTS - JSON caches and misc
    # ────────────────────────────────────────────────────────
    cache_files = [
        "contract_cache.json", "tango_cache.json",
        "tango-api-endpoints.json", "tango-test-naics-query.json",
        "tango-test-single-contract.json", "tango-test-subawards.json",
    ]
    for f in cache_files:
        add(f"data/from_n8n_builder/analytical_outputs/{f}",
            f"data/state/{f}", "API cache/state")

    discovery_json = [
        "discovery-stats-v2.json", "dod-discovery-stats-FIXED.json",
        "dod-discovery-stats-WORKING.json", "high-sub-spend-stats.json",
    ]
    for f in discovery_json:
        add(f"data/from_n8n_builder/analytical_outputs/{f}",
            f"data/state/{f}", "discovery stats")

    # Settings/config files
    add("data/from_n8n_builder/analytical_outputs/graph_hints.json",
        "data/state/graph_hints.json", "graph hints")
    add("data/from_n8n_builder/analytical_outputs/project_index.json",
        "data/state/project_index.json", "project index")
    add("data/from_n8n_builder/analytical_outputs/settings.local.json",
        "data/state/settings.local.json", "local settings")

    # Misc MDs from analytical outputs
    misc_analytical_md = [
        "03_IMPL_N8N_Builder.md", "AUTO-CLAUDE-HANDOFF.md",
        "WEBHOOK_URLS.md", "CRITICAL-FIX-FUNDING-OFFICE.md",
    ]
    for f in misc_analytical_md:
        add(f"data/from_n8n_builder/analytical_outputs/{f}",
            f"data/deliverables/reports/{f}", "misc analytical report")

    # ────────────────────────────────────────────────────────
    # 26. NOTION EXPORT CSVS (analytical_outputs duplicates)
    # ────────────────────────────────────────────────────────
    notion_ao_dupes = [
        "BD IntelliRepo File ManagementAll.csv",
        "BD OpportunitiesAll.csv",
        "Contractors Database All.csv",
        "Contractors.csv",
        "Contract_VehiclesAll.csv",
        "GDIT Jobs 2All.csv",
        "Insight Global Jobs - Program Mapped (Dec 2025) All.csv",
        "Program Mapping Intelligence Hub All.csv",
        "Programs_KBAll.csv",
        "Programs_KB_TEMPLATE.csv",
    ]
    for f in notion_ao_dupes:
        add(f"data/from_n8n_builder/analytical_outputs/{f}",
            f"data/archive/notion_export_history/{f.replace(' ', '_')}",
            "notion export copy")

    # Emoji-prefixed files
    for pattern in ["≡ƒ*", "📊*"]:
        for f in sorted((PROJECT_ROOT / "data/from_n8n_builder/analytical_outputs").glob(pattern)):
            if f.is_file():
                clean = normalize_filename(f.name).replace(' ', '_')
                moves.append((f, PROJECT_ROOT / f"data/archive/notion_export_history/{clean}",
                              "emoji-prefixed notion export"))
        for f in sorted((PROJECT_ROOT / "engine_data/Engine2_ProgramMapping").glob(pattern)):
            if f.is_file():
                clean = normalize_filename(f.name).replace(' ', '_')
                moves.append((f, PROJECT_ROOT / f"data/archive/notion_export_history/e2_{clean}",
                              "emoji-prefixed e2 export"))

    # Markdown reports from analytical that reference integration setup
    for f in sorted((PROJECT_ROOT / "data/from_n8n_builder/analytical_outputs").glob(
            "Integration Setup*")):
        if f.is_file():
            moves.append((f, PROJECT_ROOT / f"data/archive/notion_export_history/{f.name.replace(' ', '_')}",
                          "integration setup doc"))

    # V3 breakthrough reports
    add("data/from_n8n_builder/analytical_outputs/FINAL-V3-BREAKTHROUGH-REPORT.md",
        "data/deliverables/reports/FINAL-V3-BREAKTHROUGH-REPORT.md", "v3 breakthrough")
    add("data/from_n8n_builder/analytical_outputs/V3-BREAKTHROUGH-SUMMARY.md",
        "data/deliverables/reports/V3-BREAKTHROUGH-SUMMARY.md", "v3 summary")
    add("data/from_n8n_builder/analytical_outputs/test_jobs.json",
        "data/state/test_jobs.json", "test jobs")

    # ────────────────────────────────────────────────────────
    # 27. DOCUMENTS
    # ────────────────────────────────────────────────────────
    add("data/from_n8n_builder/documents/processed_docs.json",
        "data/knowledge/processed_docs.json", "processed docs")

    # ────────────────────────────────────────────────────────
    # 28. DATABASE FILES → data/state/
    # ────────────────────────────────────────────────────────
    add("data/checkpoints_meta.db", "data/state/checkpoints_meta.db", "checkpoints DB")
    add("data/master_federal_contracts.db",
        "data/state/master_federal_contracts.db", "master contracts DB")

    # ────────────────────────────────────────────────────────
    # 29. ENGINE2 DATA (non-notion scripts)
    # ────────────────────────────────────────────────────────
    add("Engine2_ProgramMapping/data/Insight_Global_Jobs_DataMapped_Enriched_2026-02-16.csv",
        "data/enriched/jobs/Insight_Global_Jobs_DataMapped_Enriched_2026-02-16.csv",
        "latest enriched IG jobs")
    add("Engine2_ProgramMapping/data/Insight_Global_Jobs_DataMapped_Enriched_2026-02-16.json",
        "data/enriched/jobs/Insight_Global_Jobs_DataMapped_Enriched_2026-02-16.json",
        "latest enriched IG jobs JSON")
    add("Engine2_ProgramMapping/data/Insight_Global_Jobs_Enrichment_Summary_2026-02-16.md",
        "data/deliverables/reports/Insight_Global_Jobs_Enrichment_Summary_2026-02-16.md",
        "IG enrichment summary")
    add("Engine2_ProgramMapping/data/Insight_Global_BD_Playbook_Master_2026-02-16.xlsx",
        "data/deliverables/playbooks/Insight_Global_BD_Playbook_Master_2026-02-16.xlsx",
        "IG playbook xlsx")

    # ────────────────────────────────────────────────────────
    # 30. ENGINE_DATA DUPLICATES → skip (already handled above)
    # ────────────────────────────────────────────────────────
    # engine_data/Engine2_ProgramMapping/* → duplicates of Engine2_ProgramMapping/data/*
    # engine_data/Engine3_OrgChart/* → duplicates of Engine3_OrgChart/data/*
    # These are exact copies. We mark them for deletion after migration.

    # ════════════════════════════════════════════════════════════
    # CATCH-ALL SWEEP RULES (run after specific rules)
    # These handle files not covered by explicit mappings above
    # ════════════════════════════════════════════════════════════
    already_planned = {m[0] for m in moves}

    def sweep(src_glob: str, dst_dir: str, reason: str):
        """Move all unplanned files matching glob to dst_dir."""
        for f in sorted(PROJECT_ROOT.glob(src_glob)):
            if f.is_file() and f not in already_planned:
                moves.append((f, PROJECT_ROOT / dst_dir / f.name.replace(' ', '_'), reason))
                already_planned.add(f)

    # ── Remaining from_data_scraper files ──
    # Phase/enrichment CSVs → enriched/intelligence
    for f in sorted((PROJECT_ROOT / "data/from_data_scraper").glob("PHASE*.csv")):
        if f not in already_planned:
            moves.append((f, PROJECT_ROOT / "data/enriched/intelligence" / f.name, "phase data"))
            already_planned.add(f)

    # bd_* targets/analysis CSVs → enriched/targets
    for f in sorted((PROJECT_ROOT / "data/from_data_scraper").glob("bd_*.csv")):
        if f not in already_planned:
            moves.append((f, PROJECT_ROOT / "data/enriched/targets" / f.name, "BD target data"))
            already_planned.add(f)

    # phase* (lowercase) CSVs → enriched/contracts
    for f in sorted((PROJECT_ROOT / "data/from_data_scraper").glob("phase*.csv")):
        if f not in already_planned:
            moves.append((f, PROJECT_ROOT / "data/enriched/contracts" / f.name, "phase contract data"))
            already_planned.add(f)

    # competitor_* → enriched/intelligence
    sweep("data/from_data_scraper/competitor_*.csv", "data/enriched/intelligence",
          "competitor data")

    # Remaining specific files
    add("data/from_data_scraper/COMBINED_INTELLIGENCE_REPORT.csv",
        "data/enriched/intelligence/COMBINED_INTELLIGENCE_REPORT.csv", "combined intel")
    add("data/from_data_scraper/Federal_Programs_Enriched.csv",
        "data/archive/federal_programs_versions/Federal_Programs_Enriched.csv", "old FP enriched")
    add("data/from_data_scraper/MASTER_TARGET_LIST.csv",
        "data/enriched/targets/MASTER_TARGET_LIST.csv", "master target list")
    add("data/from_data_scraper/primes_tango_enriched.csv",
        "data/enriched/primes/primes_tango_enriched.csv", "tango primes")
    add("data/from_data_scraper/unmatched_budget_programs.csv",
        "data/enriched/programs/unmatched_budget_programs.csv", "unmatched budget")

    # MD reports
    for f in sorted((PROJECT_ROOT / "data/from_data_scraper").glob("*.md")):
        if f not in already_planned:
            moves.append((f, PROJECT_ROOT / "data/enriched/intelligence" / f.name, "intel report"))
            already_planned.add(f)

    # xlsx files
    for f in sorted((PROJECT_ROOT / "data/from_data_scraper").glob("*.xlsx")):
        if f not in already_planned:
            moves.append((f, PROJECT_ROOT / "data/deliverables/reports" / f.name.replace(' ', '_'),
                          "deliverable xlsx"))
            already_planned.add(f)

    # DB files
    add("data/from_data_scraper/bullhorn_past_performance.db",
        "data/state/bullhorn_past_performance.db", "past performance DB")

    # Catch remaining from_data_scraper CSVs
    for f in sorted((PROJECT_ROOT / "data/from_data_scraper").glob("*.csv")):
        if f not in already_planned:
            moves.append((f, PROJECT_ROOT / "data/enriched/intelligence" / f.name,
                          "remaining from_data_scraper"))
            already_planned.add(f)

    # ── Remaining from_n8n_builder/analytical_outputs CSVs ──
    ao_dir = PROJECT_ROOT / "data/from_n8n_builder/analytical_outputs"
    if ao_dir.exists():
        # CSIS/ETL/FPDS reference tables
        csis_etl_patterns = [
            "CSIS*", "ETL_*", "FPDS*", "Error*", "Count*", "Create*",
            "Name*", "Postgres*", "USAspending*", "stage1*",
        ]
        for pat in csis_etl_patterns:
            for f in sorted(ao_dir.glob(f"{pat}.csv")):
                if f not in already_planned:
                    moves.append((f, PROJECT_ROOT / "data/reference/fpds" / f.name,
                                  "CSIS/ETL reference"))
                    already_planned.add(f)

        # Location/geo reference
        for pat in ["Location_*", "eurostat_*", "World_*", "UNSD*"]:
            for f in sorted(ao_dir.glob(f"{pat}.csv")):
                if f not in already_planned:
                    moves.append((f, PROJECT_ROOT / "data/reference/geo_economic" / f.name.replace(' ', '_'),
                                  "geo reference"))
                    already_planned.add(f)

        # Agency/customer/organization reference
        for pat in ["Agency_*", "awarding_*", "Contracting*", "Customer*",
                     "Defense_*", "Lookup_*", "MajCom*", "SubCustomer*"]:
            for f in sorted(ao_dir.glob(f"{pat}.csv")):
                if f not in already_planned:
                    moves.append((f, PROJECT_ROOT / "data/reference/usaspending" / f.name,
                                  "agency reference"))
                    already_planned.add(f)

        # Product/service/NAICS reference
        for pat in ["Product*", "PSCA*", "Recovered*", "Information*",
                     "Platform*", "Principal*", "Entity*", "Vendor*",
                     "Assistance_*", "Manufacturing*", "System*", "SOSA*",
                     "Statutory*", "ReasonNot*", "RDP*"]:
            for f in sorted(ao_dir.glob(f"{pat}.csv")):
                if f not in already_planned:
                    moves.append((f, PROJECT_ROOT / "data/reference/fpds" / f.name,
                                  "FPDS/PSC reference"))
                    already_planned.add(f)

        # 2013+ and 2025+ historical data
        for f in sorted(ao_dir.glob("2013-*.csv")):
            if f not in already_planned:
                moves.append((f, PROJECT_ROOT / "data/archive/historical_fpds_usaspending" / f.name,
                              "historical data"))
                already_planned.add(f)
        for f in sorted(ao_dir.glob("2025_*.csv")):
            if f not in already_planned:
                moves.append((f, PROJECT_ROOT / "data/archive/historical_fpds_usaspending" / f.name,
                              "historical data"))
                already_planned.add(f)
        for f in sorted(ao_dir.glob("FPDSdelta_*.csv")):
            if f not in already_planned:
                moves.append((f, PROJECT_ROOT / "data/archive/historical_fpds_usaspending" / f.name,
                              "FPDS delta"))
                already_planned.add(f)
        add("data/from_n8n_builder/analytical_outputs/2025-07-25 CAU CTU import.csv",
            "data/archive/historical_fpds_usaspending/2025-07-25_CAU_CTU_import.csv",
            "CAU CTU import")

        # BD target/scoring CSVs from analytical_outputs (duplicates of from_data_scraper)
        for pat in ["bd_*", "tier*", "size_*", "agency_*", "high_*",
                     "it_services*", "medium_*", "some_*", "top_*",
                     "db1_*", "db2_*", "db3_*", "db4_*", "db5_*", "db6_*", "db7_*"]:
            for f in sorted(ao_dir.glob(f"{pat}.csv")):
                if f not in already_planned:
                    moves.append((f, PROJECT_ROOT / "data/archive/notion_export_history" / f.name,
                                  "analytical output duplicate"))
                    already_planned.add(f)

        # dod-programs variants
        for f in sorted(ao_dir.glob("dod-programs*.csv")):
            if f not in already_planned:
                moves.append((f, PROJECT_ROOT / "data/archive/dod_staffing_versions" / f.name,
                              "DoD programs variant"))
                already_planned.add(f)

        # FULL_INDEX manifest
        add("data/from_n8n_builder/analytical_outputs/FULL_INDEX_FILE_MANIFEST.csv",
            "data/state/FULL_INDEX_FILE_MANIFEST.csv", "file manifest")

        # Catch remaining analytical_outputs CSVs
        for f in sorted(ao_dir.glob("*.csv")):
            if f not in already_planned:
                moves.append((f, PROJECT_ROOT / "data/reference/mcp_extracts" / f.name.replace(' ', '_'),
                              "remaining analytical CSV"))
                already_planned.add(f)

        # Remaining analytical_outputs MDs
        for f in sorted(ao_dir.glob("*.md")):
            if f not in already_planned:
                moves.append((f, PROJECT_ROOT / "data/deliverables/reports" / f.name.replace(' ', '_'),
                              "remaining analytical report"))
                already_planned.add(f)

        # Remaining JSON
        for f in sorted(ao_dir.glob("*.json")):
            if f not in already_planned:
                moves.append((f, PROJECT_ROOT / "data/state" / f.name,
                              "remaining analytical JSON"))
                already_planned.add(f)

        # Remaining xlsx
        for f in sorted(ao_dir.glob("*.xlsx")):
            if f not in already_planned:
                moves.append((f, PROJECT_ROOT / "data/deliverables/reports" / f.name.replace(' ', '_'),
                              "remaining analytical xlsx"))
                already_planned.add(f)

    # ── engine_data/ duplicates → archive ──
    # These are confirmed duplicates of Engine2/Engine3 data dirs
    for f in sorted((PROJECT_ROOT / "engine_data").rglob("*")):
        if f.is_file() and f not in already_planned:
            rel = f.relative_to(PROJECT_ROOT / "engine_data")
            moves.append((f, PROJECT_ROOT / "data/archive/engine_data_duplicates" / rel,
                          "engine_data duplicate"))
            already_planned.add(f)

    # ── Remaining outputs/ files → archive ──
    for f in sorted((PROJECT_ROOT / "outputs").rglob("*")):
        if f.is_file() and f not in already_planned:
            rel = f.relative_to(PROJECT_ROOT / "outputs")
            # State files
            if f.name in ("pipeline_state.json", "alert_state.json"):
                moves.append((f, PROJECT_ROOT / "data/state" / f.name, "pipeline state"))
            elif f.name == "INDEXING_PROGRESS_LOG.md":
                moves.append((f, PROJECT_ROOT / "data/state/INDEXING_PROGRESS_LOG.md", "indexing log"))
            elif f.name in ("contract_assignments_matched.csv",
                             "contract_assignments_CORRECTED.csv",
                             "open_contracts_UNASSIGNED.csv"):
                moves.append((f, PROJECT_ROOT / "data/deliverables/reports" / f.name,
                              "contract deliverable"))
            elif f.suffix == '.json':
                moves.append((f, PROJECT_ROOT / "data/archive/notion_api_dumps" / f.name,
                              "remaining output JSON"))
            elif f.suffix == '.md':
                moves.append((f, PROJECT_ROOT / "data/deliverables/reports" / f.name.replace(' ', '_'),
                              "remaining output report"))
            elif f.suffix == '.csv':
                moves.append((f, PROJECT_ROOT / "data/archive/engine1_iterations" / f.name,
                              "remaining output CSV"))
            else:
                moves.append((f, PROJECT_ROOT / "data/archive/engine1_iterations" / str(rel),
                              "remaining output"))
            already_planned.add(f)

    return moves


# ════════════════════════════════════════════════════════════════════
#  EXECUTION
# ════════════════════════════════════════════════════════════════════

def create_directories():
    """Create all target directories."""
    for d in TARGET_DIRS:
        (PROJECT_ROOT / d).mkdir(parents=True, exist_ok=True)
    # Additional directories that may be needed
    extra = [
        "data/enriched/intelligence/past_performance",
        "data/enriched/intelligence/dossiers",
        "data/archive/contacts_raw",
    ]
    for d in extra:
        (PROJECT_ROOT / d).mkdir(parents=True, exist_ok=True)


def execute_migration(moves: list[tuple[Path, Path, str]], dry_run: bool = True):
    """Execute or preview the migration."""
    log_rows = []
    skipped = 0
    moved = 0
    errors = 0
    conflicts = 0

    for src, dst, reason in moves:
        if not src.exists():
            skipped += 1
            continue

        # Check for destination conflict
        if dst.exists():
            # If same content, skip silently
            if file_hash(src) == file_hash(dst):
                log_rows.append([str(src.relative_to(PROJECT_ROOT)),
                                 str(dst.relative_to(PROJECT_ROOT)),
                                 "SKIP_DUPLICATE", reason])
                skipped += 1
                continue
            else:
                # Rename destination with suffix
                stem = dst.stem
                suffix = dst.suffix
                dst = dst.with_name(f"{stem}_conflict{suffix}")
                conflicts += 1

        rel_src = str(src.relative_to(PROJECT_ROOT))
        rel_dst = str(dst.relative_to(PROJECT_ROOT))

        if dry_run:
            print(f"  {rel_src}")
            print(f"    -> {rel_dst}")
            log_rows.append([rel_src, rel_dst, "PLANNED", reason])
        else:
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))
                log_rows.append([rel_src, rel_dst, "MOVED", reason])
                moved += 1
            except Exception as e:
                log_rows.append([rel_src, rel_dst, f"ERROR: {e}", reason])
                errors += 1
                print(f"  ERROR: {rel_src} → {e}")

    # Write migration log
    log_path = PROJECT_ROOT / "data" / "archive" / "migration_log.csv"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["source", "destination", "status", "reason"])
        writer.writerows(log_rows)

    mode = "DRY RUN" if dry_run else "EXECUTED"
    print(f"\n{'='*60}")
    print(f"  Migration {mode} Summary")
    print(f"{'='*60}")
    print(f"  Planned moves: {len(moves)}")
    if not dry_run:
        print(f"  Moved:         {moved}")
    print(f"  Skipped:       {skipped} (missing source or duplicate)")
    print(f"  Conflicts:     {conflicts}")
    if not dry_run:
        print(f"  Errors:        {errors}")
    print(f"  Log:           {log_path.relative_to(PROJECT_ROOT)}")


def cleanup_empty_dirs():
    """Remove empty directories left after migration."""
    cleanup_roots = [
        PROJECT_ROOT / "engine_data",
        PROJECT_ROOT / "outputs",
        PROJECT_ROOT / "data" / "from_data_scraper",
        PROJECT_ROOT / "data" / "from_n8n_builder",
    ]
    removed = 0
    for root in cleanup_roots:
        if not root.exists():
            continue
        # Walk bottom-up to remove empty dirs
        for dirpath, dirnames, filenames in os.walk(str(root), topdown=False):
            if not filenames and not dirnames:
                try:
                    os.rmdir(dirpath)
                    removed += 1
                except OSError:
                    pass
    print(f"  Removed {removed} empty directories")


def verify_migration():
    """Post-migration verification."""
    print("\n=== Migration Verification ===\n")

    # Count files in new structure
    data_dir = PROJECT_ROOT / "data"
    categories = {
        "raw": 0, "enriched": 0, "deliverables": 0,
        "bullhorn_analysis": 0, "dashboard": 0, "reference": 0,
        "knowledge": 0, "state": 0, "archive": 0,
    }
    for cat in categories:
        cat_dir = data_dir / cat
        if cat_dir.exists():
            count = sum(1 for _ in cat_dir.rglob("*") if _.is_file())
            categories[cat] = count

    total = sum(categories.values())
    print("File counts by category:")
    for cat, count in sorted(categories.items()):
        print(f"  data/{cat:25s} {count:5d} files")
    print(f"  {'TOTAL':30s} {total:5d} files")

    # Check for residual files in old locations
    print("\nResidual files in old locations:")
    old_dirs = [
        "engine_data", "outputs",
        "data/from_data_scraper", "data/from_n8n_builder",
    ]
    for d in old_dirs:
        p = PROJECT_ROOT / d
        if p.exists():
            count = sum(1 for _ in p.rglob("*") if _.is_file())
            status = "CLEAN" if count == 0 else f"{count} files remaining"
            print(f"  {d:40s} {status}")
        else:
            print(f"  {d:40s} REMOVED")

    # Spot-check key files
    print("\nSpot-check key files:")
    checks = [
        "data/enriched/programs/Federal_Programs_MASTER_V4.csv",
        "data/enriched/contacts/by_company/Leidos_Contacts_Enriched.csv",
        "data/enriched/contracts/MASTER_CONTRACTS_COMBINED.csv",
        "data/enriched/jobs/JOBS_ENRICHED.csv",
        "data/enriched/targets/master_bd_targets.csv",
        "data/dashboard/contacts_classified.json",
        "data/deliverables/briefings",
        "data/bullhorn_analysis/FINAL_OUTPUTS",
        "data/reference/fpds/action_type_code.csv",
    ]
    for check in checks:
        p = PROJECT_ROOT / check
        if p.exists():
            if p.is_dir():
                count = sum(1 for _ in p.rglob("*") if _.is_file())
                print(f"  OK  {check} ({count} files)")
            else:
                size = p.stat().st_size
                print(f"  OK  {check} ({size:,} bytes)")
        else:
            print(f"  MISSING  {check}")


# ════════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="BD-Automation-Engine data reorganization")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="Preview all planned moves")
    group.add_argument("--execute", action="store_true", help="Execute the migration")
    group.add_argument("--verify", action="store_true", help="Post-migration verification")
    args = parser.parse_args()

    if args.verify:
        verify_migration()
        return

    print(f"BD-Automation-Engine Data Reorganization")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    # Step 1: Create target directories
    print("Creating target directories...")
    create_directories()

    # Step 2: Build migration plan
    print("Building migration plan...")
    moves = build_migration_plan()
    print(f"  {len(moves)} moves planned\n")

    # Step 3: Execute or preview
    if args.dry_run:
        print("=== DRY RUN (no files moved) ===\n")
        execute_migration(moves, dry_run=True)
    else:
        print("=== EXECUTING MIGRATION ===\n")
        execute_migration(moves, dry_run=False)
        print("\nCleaning up empty directories...")
        cleanup_empty_dirs()
        print("\nRunning verification...")
        verify_migration()


if __name__ == "__main__":
    main()
