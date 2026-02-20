"""
BD Playbook Generator - Insight Global Jobs
============================================
Creates a master Excel workbook with one sheet per Prime+Program combo.
Each sheet has: Table 1 (Jobs), Table 2 (Program-Matched Contacts), Table 3 (All Prime Contacts).

Usage: python generate_bd_playbook.py
"""

import ast
import os
import sys
import json
import csv
import re
from collections import defaultdict
from datetime import datetime

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    print("Installing openpyxl...")
    import subprocess

    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "openpyxl", "--quiet"]
    )
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

# === PATHS ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.dirname(BASE_DIR)
DASHBOARD_DATA = os.path.join(PROJECT_DIR, "dashboard", "dist", "data")
ENGINE2_DATA = os.path.join(BASE_DIR, "data")
BULLHORN_ANALYSIS = os.path.join(
    PROJECT_DIR, "Engine7_BullhornETL", "colton_scurry_analysis"
)

# === PRIME INFERENCE MAP ===
# Location + Program signals -> likely prime contractor
LOCATION_PRIME_MAP = {
    "colorado springs": {
        "default": "Northrop Grumman",
        "MDA": "Lockheed Martin",
        "C2BMC": "Lockheed Martin",
        "Space Force": "Northrop Grumman",
        "GPS": "Lockheed Martin",
        "SBIRS": "Lockheed Martin",
        "Schriever": "Multiple",
        "NORAD": "Northrop Grumman",
        "SDA": "L3Harris",
    },
    "huntsville": {
        "default": "Northrop Grumman",
        "MDA": "Lockheed Martin",
        "THAAD": "Lockheed Martin",
        "Patriot": "Raytheon",
        "IBCS": "Northrop Grumman",
        "SLS": "Boeing",
        "NASA": "Boeing",
        "Sentinel": "Northrop Grumman",
        "PEO Missiles": "Multiple",
    },
    "san diego": {
        "default": "General Dynamics",
        "Aegis": "Lockheed Martin",
        "NAVWAR": "Leidos",
        "Navy": "General Dynamics",
    },
    "el segundo": {
        "default": "Northrop Grumman",
        "Space Force": "Northrop Grumman",
        "NRO": "Northrop Grumman",
    },
    "redondo beach": {"default": "Northrop Grumman"},
    "aurora": {"default": "Lockheed Martin", "NRO": "Lockheed Martin"},
    "fort meade": {
        "default": "General Dynamics",
        "NSA": "Multiple",
        "Cyber": "General Dynamics",
    },
    "annapolis junction": {"default": "General Dynamics", "NSA": "Multiple"},
    "reston": {"default": "Leidos"},
    "mclean": {"default": "Booz Allen"},
    "chantilly": {"default": "Northrop Grumman", "NRO": "Northrop Grumman"},
    "springfield": {"default": "Leidos", "NGA": "Leidos"},
    "arlington": {"default": "Multiple"},
    "st. louis": {"default": "Boeing", "F-15": "Boeing", "F-18": "Boeing"},
    "saint louis": {"default": "Boeing"},
    "tucson": {"default": "Raytheon", "Missiles": "Raytheon"},
    "dallas": {"default": "Raytheon"},
    "fort worth": {"default": "Lockheed Martin", "F-35": "Lockheed Martin"},
    "montgomery": {"default": "General Dynamics", "Maxwell": "ManTech"},
    "warren afb": {
        "default": "Northrop Grumman",
        "ICBM": "Northrop Grumman",
        "Sentinel": "Northrop Grumman",
    },
    "cheyenne": {"default": "Northrop Grumman"},
    "hill afb": {"default": "Northrop Grumman"},
    "clearfield": {"default": "Northrop Grumman"},
    "ogden": {"default": "Northrop Grumman"},
    "aberdeen": {"default": "CACI", "APG": "CACI"},
    "dahlgren": {"default": "Leidos"},
    "norfolk": {"default": "General Dynamics"},
    "hampton": {"default": "Northrop Grumman"},
    "lexington park": {"default": "Northrop Grumman"},
    "warner robins": {"default": "Northrop Grumman"},
    "eglin": {"default": "SAIC"},
    "lackland": {"default": "ManTech"},
    "tampa": {"default": "SAIC"},
    "panama city": {"default": "General Dynamics"},
    "sierra vista": {"default": "Peraton"},
    "fort huachuca": {"default": "Peraton"},
    "fort liberty": {"default": "Peraton"},
    "seal beach": {"default": "Boeing"},
    "middletown": {"default": "Lockheed Martin"},
    "north berwick": {"default": "Lockheed Martin"},
    "suffolk": {"default": "Lockheed Martin"},
    "linthicum": {"default": "Leidos"},
    "jessup": {"default": "General Dynamics"},
    "columbia": {"default": "General Dynamics"},
    "kirtland": {"default": "Northrop Grumman"},
    "san antonio": {"default": "Boeing"},
    "aiea": {"default": "Lockheed Martin"},
    "honolulu": {"default": "Lockheed Martin"},
    "pearl harbor": {"default": "Lockheed Martin"},
}

# Category -> functional area prime mapping
CATEGORY_PRIME_MAP = {
    "network engineer": {"default": "General Dynamics"},
    "security engineering": {"default": "General Dynamics"},
    "system administrator": {"default": "General Dynamics"},
}


def load_json(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        return json.load(f)


def load_csv(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def infer_prime(job):
    """Infer prime contractor from location + program + category."""
    location = (job.get("location") or "").lower()
    program = job.get("mapped_program", "")
    category = (job.get("category") or "").lower()

    # Check explicit prime first
    prime = job.get("identified_prime_contractor", "")
    if prime and prime != "Unknown - Requires Research":
        return prime.split(" | ")[0], False  # Not inferred

    # Try location-based inference
    for loc_key, prime_map in LOCATION_PRIME_MAP.items():
        if loc_key in location:
            # Check program-specific mapping first
            if program in prime_map:
                return prime_map[program], True
            return prime_map["default"], True

    # Try category-based
    for cat_key, prime_map in CATEGORY_PRIME_MAP.items():
        if cat_key in category:
            return prime_map["default"], True

    # Default to Unknown
    return "Unknown", True


def aggregate_contact_notes(contact_name, timeline):
    """Aggregate ALL notes for a contact into a single narrative."""
    name_lower = contact_name.lower().strip()
    notes = []
    for entry in timeline:
        entry_contact = (entry.get("contact") or "").lower().strip()
        if entry_contact == name_lower:
            date = entry.get("date", "")
            author = entry.get("author", "")
            summary = (entry.get("summary") or "").strip()
            if summary:
                notes.append(f"[{date}] ({author}) {summary}")

    if not notes:
        return ""

    # Return all notes joined, capped at 2000 chars for Excel cell limits
    combined = " | ".join(notes)
    if len(combined) > 2000:
        combined = combined[:1997] + "..."
    return combined


def build_contact_database(dashboard_contacts, bullhorn_contacts, timeline):
    """Build a unified contact database indexed by company."""
    # Master contact dict: name -> details
    master_contacts = {}

    # Dashboard contacts (have structured data)
    for c in dashboard_contacts:
        name = (c.get("name") or "").strip()
        if not name or len(name) < 2:
            continue
        company = (c.get("company") or "").strip()
        # Map GDIT -> General Dynamics
        if company == "GDIT":
            company = "General Dynamics"
        key = f"{name}|{company}".lower()
        agg_notes = aggregate_contact_notes(name, timeline)
        master_contacts[key] = {
            "name": name,
            "job_title": c.get("jobTitle", "") or "",
            "company": company,
            "phone": c.get("phone", "") or "",
            "email": c.get("email", "") or "",
            "city": c.get("city", "") or "",
            "state": c.get("state", "") or "",
            "tier": c.get("tier", "") or "",
            "aggregated_notes": agg_notes,
            "source": "Dashboard",
        }

    # Bullhorn contacts
    for bc in bullhorn_contacts:
        name = (bc.get("name") or "").strip()
        if not name or len(name) < 2:
            continue
        companies_str = bc.get("companies", "[]")
        try:
            companies = (
                ast.literal_eval(companies_str) if companies_str and companies_str != "[]" else []
            )
        except (ValueError, SyntaxError):
            companies = []
        if not companies:
            continue

        agg_notes = aggregate_contact_notes(name, timeline)

        # Extract any emails/phones from notes
        email_match = re.findall(r"[\w.+-]+@[\w.-]+\.\w+", agg_notes)
        phone_match = re.findall(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", agg_notes)

        for company in companies:
            key = f"{name}|{company}".lower()
            if key not in master_contacts:
                master_contacts[key] = {
                    "name": name,
                    "job_title": "",
                    "company": company,
                    "phone": phone_match[0] if phone_match else "",
                    "email": email_match[0] if email_match else "",
                    "city": "",
                    "state": "",
                    "tier": "",
                    "aggregated_notes": agg_notes,
                    "source": "Bullhorn",
                }
            else:
                # Merge notes if not already present
                existing = master_contacts[key]
                if not existing["aggregated_notes"] and agg_notes:
                    existing["aggregated_notes"] = agg_notes
                if not existing["email"] and email_match:
                    existing["email"] = email_match[0]
                if not existing["phone"] and phone_match:
                    existing["phone"] = phone_match[0]

    # Index by company
    company_index = defaultdict(list)
    for key, contact in master_contacts.items():
        company = contact["company"].lower()
        company_index[company].append(contact)
        # Also add common aliases
        if company == "general dynamics":
            company_index["gdit"].append(contact)
        elif company == "raytheon":
            company_index["rtx"].append(contact)
        elif company == "l3harris":
            company_index["l3 harris"].append(contact)

    # Index by company + program (from notes)
    program_contact_index = defaultdict(list)
    for key, contact in master_contacts.items():
        notes = contact["aggregated_notes"].lower()
        company = contact["company"].lower()
        # Check which programs are mentioned in their notes
        programs_mentioned = set()
        program_keywords = [
            "MDA",
            "THAAD",
            "Patriot",
            "IBCS",
            "Aegis",
            "Sentinel",
            "GBSD",
            "F-35",
            "F-22",
            "F-15",
            "F-16",
            "F-47",
            "B-21",
            "B-52",
            "SLS",
            "NASA",
            "Space Force",
            "DCGS",
            "DISA",
            "NGA",
            "NSA",
            "NRO",
            "ABMS",
            "JADC2",
            "Cyber",
            "SDA",
            "GPS",
            "SBIRS",
            "AEHF",
            "BOA",
            "IDIQ",
            "OASIS",
            "DDG",
            "BICES",
            "PMS",
            "OPIR",
            "C2BMC",
            "Cloud",
            "DevSecOps",
            "PEO",
        ]
        for prog in program_keywords:
            if prog.lower() in notes:
                programs_mentioned.add(prog)

        for prog in programs_mentioned:
            idx_key = f"{company}|{prog}".lower()
            program_contact_index[idx_key].append(contact)

    return company_index, program_contact_index


def find_contacts_for_sheet(prime, program, company_index, program_contact_index):
    """Find program-matched and all-prime contacts for a sheet."""
    prime_lower = prime.lower()

    # Program-matched contacts
    prog_key = f"{prime_lower}|{program}".lower()
    program_matched = program_contact_index.get(prog_key, [])

    # All prime contacts
    all_prime = company_index.get(prime_lower, [])

    # Deduplicate
    matched_names = set(c["name"].lower() for c in program_matched)
    other_contacts = [c for c in all_prime if c["name"].lower() not in matched_names]

    # Sort: program-matched by tier then name, others by notes length (most intel first)
    program_matched.sort(key=lambda x: (int(x.get("tier") or 99), x["name"]))
    other_contacts.sort(key=lambda x: (-len(x.get("aggregated_notes", "")), x["name"]))

    return program_matched, other_contacts


# === EXCEL STYLING ===

HEADER_FILL_JOBS = PatternFill(
    start_color="1F4E79", end_color="1F4E79", fill_type="solid"
)
HEADER_FILL_CONTACTS_MATCHED = PatternFill(
    start_color="2E7D32", end_color="2E7D32", fill_type="solid"
)
HEADER_FILL_CONTACTS_ALL = PatternFill(
    start_color="5D4037", end_color="5D4037", fill_type="solid"
)
SECTION_LABEL_FILL = PatternFill(
    start_color="E3F2FD", end_color="E3F2FD", fill_type="solid"
)
SECTION_LABEL_FILL_GREEN = PatternFill(
    start_color="E8F5E9", end_color="E8F5E9", fill_type="solid"
)
SECTION_LABEL_FILL_BROWN = PatternFill(
    start_color="EFEBE9", end_color="EFEBE9", fill_type="solid"
)

HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
SECTION_FONT = Font(bold=True, size=12, color="1F4E79")
NORMAL_FONT = Font(size=10)
LINK_FONT = Font(size=10, color="0563C1", underline="single")

THIN_BORDER = Border(
    left=Side(style="thin", color="D0D0D0"),
    right=Side(style="thin", color="D0D0D0"),
    top=Side(style="thin", color="D0D0D0"),
    bottom=Side(style="thin", color="D0D0D0"),
)

WRAP_ALIGNMENT = Alignment(wrap_text=True, vertical="top")
TOP_ALIGNMENT = Alignment(vertical="top")


def write_sheet(
    ws, sheet_name, prime, program, jobs, program_contacts, other_contacts, is_inferred
):
    """Write a complete sheet with jobs and contacts tables."""
    row = 1

    # === SHEET TITLE ===
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=8)
    title_cell = ws.cell(row=row, column=1)
    inferred_tag = " (Inferred)" if is_inferred else ""
    title_cell.value = f"{prime}{inferred_tag} - {program} | {len(jobs)} Jobs | {len(program_contacts)} Program Contacts | {len(other_contacts)} Other Contacts"
    title_cell.font = Font(bold=True, size=14, color="1F4E79")
    row += 2

    # === TABLE 1: JOBS ===
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=8)
    section_cell = ws.cell(row=row, column=1)
    section_cell.value = f"JOBS - {program} ({len(jobs)} positions)"
    section_cell.font = SECTION_FONT
    section_cell.fill = SECTION_LABEL_FILL
    row += 1

    job_headers = [
        "Job Title",
        "Location",
        "Clearance",
        "Pay Rate",
        "Emp Type",
        "Category",
        "BD Score",
        "Job URL",
    ]
    for col, header in enumerate(job_headers, 1):
        cell = ws.cell(row=row, column=col, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL_JOBS
        cell.border = THIN_BORDER
    row += 1

    for job in jobs:
        ws.cell(row=row, column=1, value=job.get("job_title", "")).font = NORMAL_FONT
        ws.cell(row=row, column=2, value=job.get("location", "")).font = NORMAL_FONT
        ws.cell(
            row=row, column=3, value=job.get("security_clearance", "")
        ).font = NORMAL_FONT
        ws.cell(row=row, column=4, value=job.get("pay_rate", "")).font = NORMAL_FONT
        ws.cell(
            row=row, column=5, value=job.get("employment_type", "")
        ).font = NORMAL_FONT
        ws.cell(row=row, column=6, value=job.get("category", "")).font = NORMAL_FONT
        ws.cell(row=row, column=7, value=job.get("bd_score", "")).font = NORMAL_FONT
        url_cell = ws.cell(row=row, column=8)
        url = job.get("job_url", "")
        if url:
            url_cell.value = url
            url_cell.hyperlink = url
            url_cell.font = LINK_FONT
        for col in range(1, 9):
            ws.cell(row=row, column=col).border = THIN_BORDER
            ws.cell(row=row, column=col).alignment = TOP_ALIGNMENT
        row += 1

    row += 1  # Spacer

    # === TABLE 2: PROGRAM-MATCHED CONTACTS ===
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=8)
    section_cell = ws.cell(row=row, column=1)
    section_cell.value = (
        f"PROGRAM CONTACTS - Matched to {program} ({len(program_contacts)} contacts)"
    )
    section_cell.font = SECTION_FONT
    section_cell.fill = SECTION_LABEL_FILL_GREEN
    row += 1

    contact_headers = [
        "Contact Name",
        "Job Title",
        "Company",
        "Phone",
        "Email",
        "Location",
        "Tier",
        "Aggregated Notes",
    ]
    for col, header in enumerate(contact_headers, 1):
        cell = ws.cell(row=row, column=col, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL_CONTACTS_MATCHED
        cell.border = THIN_BORDER
    row += 1

    if program_contacts:
        for contact in program_contacts:
            loc = f"{contact.get('city', '')}, {contact.get('state', '')}".strip(", ")
            ws.cell(row=row, column=1, value=contact.get("name", "")).font = NORMAL_FONT
            ws.cell(
                row=row, column=2, value=contact.get("job_title", "")
            ).font = NORMAL_FONT
            ws.cell(
                row=row, column=3, value=contact.get("company", "")
            ).font = NORMAL_FONT
            ws.cell(
                row=row, column=4, value=contact.get("phone", "")
            ).font = NORMAL_FONT
            ws.cell(
                row=row, column=5, value=contact.get("email", "")
            ).font = NORMAL_FONT
            ws.cell(row=row, column=6, value=loc).font = NORMAL_FONT
            ws.cell(row=row, column=7, value=contact.get("tier", "")).font = NORMAL_FONT
            notes_cell = ws.cell(
                row=row, column=8, value=contact.get("aggregated_notes", "")
            )
            notes_cell.font = NORMAL_FONT
            notes_cell.alignment = WRAP_ALIGNMENT
            for col in range(1, 9):
                ws.cell(row=row, column=col).border = THIN_BORDER
                ws.cell(row=row, column=col).alignment = TOP_ALIGNMENT
            row += 1
    else:
        ws.cell(
            row=row, column=1, value="No program-specific contacts found"
        ).font = Font(italic=True, size=10, color="999999")
        row += 1

    row += 1  # Spacer

    # === TABLE 3: ALL PRIME CONTACTS ===
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=8)
    section_cell = ws.cell(row=row, column=1)
    section_cell.value = (
        f"ALL {prime.upper()} CONTACTS ({len(other_contacts)} additional)"
    )
    section_cell.font = SECTION_FONT
    section_cell.fill = SECTION_LABEL_FILL_BROWN
    row += 1

    for col, header in enumerate(contact_headers, 1):
        cell = ws.cell(row=row, column=col, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL_CONTACTS_ALL
        cell.border = THIN_BORDER
    row += 1

    # Cap at 200 to keep sheet manageable
    for contact in other_contacts[:200]:
        loc = f"{contact.get('city', '')}, {contact.get('state', '')}".strip(", ")
        ws.cell(row=row, column=1, value=contact.get("name", "")).font = NORMAL_FONT
        ws.cell(
            row=row, column=2, value=contact.get("job_title", "")
        ).font = NORMAL_FONT
        ws.cell(row=row, column=3, value=contact.get("company", "")).font = NORMAL_FONT
        ws.cell(row=row, column=4, value=contact.get("phone", "")).font = NORMAL_FONT
        ws.cell(row=row, column=5, value=contact.get("email", "")).font = NORMAL_FONT
        ws.cell(row=row, column=6, value=loc).font = NORMAL_FONT
        ws.cell(row=row, column=7, value=contact.get("tier", "")).font = NORMAL_FONT
        notes_cell = ws.cell(
            row=row, column=8, value=contact.get("aggregated_notes", "")
        )
        notes_cell.font = NORMAL_FONT
        notes_cell.alignment = WRAP_ALIGNMENT
        for col in range(1, 9):
            ws.cell(row=row, column=col).border = THIN_BORDER
            ws.cell(row=row, column=col).alignment = TOP_ALIGNMENT
        row += 1

    if not other_contacts:
        ws.cell(row=row, column=1, value="No additional contacts found").font = Font(
            italic=True, size=10, color="999999"
        )

    # Set column widths
    widths = [25, 25, 20, 18, 30, 22, 6, 80]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


def sanitize_sheet_name(name):
    """Sanitize sheet name for Excel (max 31 chars, no special chars)."""
    # Remove invalid characters
    name = re.sub(r"[\\/*?\[\]:]", "-", name)
    # Truncate to 31 chars
    if len(name) > 31:
        name = name[:31]
    return name


def main():
    print("=== BD Playbook Generator ===")
    print()

    # Load enriched jobs
    enriched_path = os.path.join(
        ENGINE2_DATA, "Insight_Global_Jobs_DataMapped_Enriched_2026-02-16.json"
    )
    if not os.path.exists(enriched_path):
        # Try to find any enriched file
        import glob

        files = sorted(
            glob.glob(
                os.path.join(
                    ENGINE2_DATA, "Insight_Global_Jobs_DataMapped_Enriched_*.json"
                )
            ),
            key=os.path.getmtime,
            reverse=True,
        )
        if files:
            enriched_path = files[0]
        else:
            print("ERROR: No enriched jobs file found!")
            sys.exit(1)

    print(f"Loading enriched jobs from: {enriched_path}")
    jobs = load_json(enriched_path)
    print(f"  {len(jobs)} jobs loaded")

    # Load all contact sources
    print("Loading contact databases...")
    dashboard_contacts = load_json(os.path.join(DASHBOARD_DATA, "contacts.json"))
    print(f"  Dashboard: {len(dashboard_contacts)} contacts")

    bullhorn_contacts = load_csv(os.path.join(BULLHORN_ANALYSIS, "contacts.csv"))
    print(f"  Bullhorn: {len(bullhorn_contacts)} contacts")

    timeline = load_csv(os.path.join(BULLHORN_ANALYSIS, "timeline.csv"))
    print(f"  Timeline: {len(timeline)} notes")

    # Build unified contact database
    print("\nBuilding unified contact database...")
    company_index, program_contact_index = build_contact_database(
        dashboard_contacts, bullhorn_contacts, timeline
    )
    total_contacts = sum(len(v) for v in company_index.items())
    print(f"  Companies indexed: {len(company_index)}")

    # Organize jobs by Prime + Program
    print("\nOrganizing jobs by Prime + Program...")
    prime_program_jobs = defaultdict(list)
    prime_inferred = {}  # Track which primes were inferred

    for job in jobs:
        prime, is_inferred = infer_prime(job)
        program = job.get("mapped_program", "Unknown")

        if prime == "Unknown" or prime == "Multiple":
            prime = "Research Required"
            is_inferred = True

        key = (prime, program)
        prime_program_jobs[key].append(job)
        if key not in prime_inferred:
            prime_inferred[key] = is_inferred

    # Sort keys: confirmed primes first, then by job count
    sorted_keys = sorted(
        prime_program_jobs.keys(),
        key=lambda k: (
            prime_inferred.get(k, True),
            -len(prime_program_jobs[k]),
            k[0],
            k[1],
        ),
    )

    print(f"  {len(sorted_keys)} Prime+Program combinations")
    for key in sorted_keys:
        tag = " (Inferred)" if prime_inferred[key] else ""
        print(f"    {key[0]}{tag} - {key[1]}: {len(prime_program_jobs[key])} jobs")

    # Create workbook
    print("\nGenerating Excel workbook...")
    wb = Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    # Create index/summary sheet
    ws_index = wb.create_sheet("INDEX")
    ws_index.cell(
        row=1, column=1, value="BD Playbook - Insight Global Jobs"
    ).font = Font(bold=True, size=16, color="1F4E79")
    ws_index.cell(
        row=2, column=1, value=f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    ).font = Font(size=11)
    ws_index.cell(
        row=3,
        column=1,
        value=f"Total Jobs: {len(jobs)} | Total Sheets: {len(sorted_keys)}",
    ).font = Font(size=11)
    idx_row = 5
    idx_headers = [
        "Sheet",
        "Prime",
        "Program",
        "Jobs",
        "Program Contacts",
        "Other Contacts",
        "Inferred?",
    ]
    for col, h in enumerate(idx_headers, 1):
        cell = ws_index.cell(row=idx_row, column=col, value=h)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL_JOBS
    idx_row += 1

    sheet_count = 0
    for key in sorted_keys:
        prime, program = key
        is_inferred = prime_inferred[key]
        jobs_for_sheet = prime_program_jobs[key]

        # Sort jobs by BD score descending
        jobs_for_sheet.sort(key=lambda x: x.get("bd_score", 0), reverse=True)

        # Find contacts
        program_contacts, other_contacts = find_contacts_for_sheet(
            prime, program, company_index, program_contact_index
        )

        # Create sheet
        sheet_name = sanitize_sheet_name(f"{prime[:15]} - {program[:13]}")
        # Ensure unique sheet names
        if sheet_name in [ws.title for ws in wb.worksheets]:
            sheet_name = sanitize_sheet_name(
                f"{prime[:12]} - {program[:10]} {sheet_count}"
            )
        ws = wb.create_sheet(sheet_name)
        write_sheet(
            ws,
            sheet_name,
            prime,
            program,
            jobs_for_sheet,
            program_contacts,
            other_contacts,
            is_inferred,
        )

        # Update index
        ws_index.cell(row=idx_row, column=1, value=sheet_name).font = NORMAL_FONT
        ws_index.cell(row=idx_row, column=2, value=prime).font = NORMAL_FONT
        ws_index.cell(row=idx_row, column=3, value=program).font = NORMAL_FONT
        ws_index.cell(
            row=idx_row, column=4, value=len(jobs_for_sheet)
        ).font = NORMAL_FONT
        ws_index.cell(
            row=idx_row, column=5, value=len(program_contacts)
        ).font = NORMAL_FONT
        ws_index.cell(
            row=idx_row, column=6, value=len(other_contacts)
        ).font = NORMAL_FONT
        ws_index.cell(
            row=idx_row, column=7, value="Yes" if is_inferred else "No"
        ).font = NORMAL_FONT
        for col in range(1, 8):
            ws_index.cell(row=idx_row, column=col).border = THIN_BORDER
        idx_row += 1
        sheet_count += 1

        print(
            f"  Created: {sheet_name} ({len(jobs_for_sheet)} jobs, {len(program_contacts)} prog contacts, {len(other_contacts)} other)"
        )

    # Set index column widths
    idx_widths = [30, 25, 20, 8, 18, 18, 10]
    for i, w in enumerate(idx_widths, 1):
        ws_index.column_dimensions[get_column_letter(i)].width = w

    # Save
    output_path = os.path.join(
        ENGINE2_DATA,
        f"Insight_Global_BD_Playbook_Master_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
    )
    wb.save(output_path)
    print(f"\n=== COMPLETE ===")
    print(f"Output: {output_path}")
    print(f"Sheets: {sheet_count} + INDEX")
    print(f"Total jobs mapped: {len(jobs)}")


if __name__ == "__main__":
    main()
