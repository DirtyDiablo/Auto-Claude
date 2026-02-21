"""
Ingest new Bullhorn Notes Activity Report and merge into existing analysis files.
Usage: python ingest_new_notes.py <path_to_xls>
"""

import ast
import sys
import os
import re
import json
import csv
import logging
from datetime import datetime
from collections import Counter, defaultdict
from html.parser import HTMLParser

import pandas as pd

logger = logging.getLogger(__name__)


def _safe_parse_list(value: str) -> list:
    """Safely parse a string representation of a Python list.

    Uses ast.literal_eval which ONLY parses literals (strings, numbers,
    lists, dicts, booleans, None) — NO code execution. Returns empty list
    on malformed input instead of crashing the ingestion pipeline.
    """
    if not value or not value.strip():
        return []
    try:
        result = ast.literal_eval(value)
        return result if isinstance(result, list) else [result]
    except (ValueError, SyntaxError, TypeError):
        logger.warning(f"Malformed list literal, using default: {value[:80]!r}")
        return []

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANALYSIS_DIR = os.path.join(BASE_DIR, "colton_scurry_analysis")
DEEP_DIVE_DIR = os.path.join(ANALYSIS_DIR, "ANALYSIS", "NOTES_DEEP_DIVE")

# Known prime contractors for extraction
PRIME_CONTRACTORS = [
    "Boeing",
    "General Dynamics",
    "GDIT",
    "Northrop Grumman",
    "Lockheed Martin",
    "Leidos",
    "SAIC",
    "Raytheon",
    "RTX",
    "BAE Systems",
    "Booz Allen",
    "CACI",
    "Peraton",
    "L3Harris",
    "L3 Harris",
    "Deloitte",
    "Accenture Federal",
    "ManTech",
    "Parsons",
    "KBR",
    "CSRA",
    "DXC",
    "Unisys",
    "Amentum",
    "Jacobs",
    "Maximus",
    "ICF",
    "Serco",
    "CGI",
    "Cisco",
    "Vision Technologies",
    "Modern Technology Solutions",
    "Harris Corporation",
]

# Known programs/acronyms for extraction
PROGRAM_KEYWORDS = [
    "IBCS",
    "DCGS",
    "GBSD",
    "Sentinel",
    "Aegis",
    "THAAD",
    "Patriot",
    "AMRAAM",
    "F-35",
    "F-22",
    "F-15",
    "F-16",
    "F-18",
    "F-47",
    "B-52",
    "B-21",
    "B-2",
    "SLS",
    "Artemis",
    "ARTEMUS",
    "NASA",
    "MDA",
    "SDA",
    "DARPA",
    "NGA",
    "NSA",
    "NRO",
    "Space Force",
    "PMS",
    "OPIR",
    "BOA",
    "IDIQ",
    "OASIS",
    "JDAM",
    "SDB",
    "VC-25",
    "VC25",
    "T7",
    "MQ-25",
    "Stingray",
    "LEOS",
    "COPV",
    "EUS",
    "PAC-3",
    "GBU",
    "Harpoon",
    "JWICS",
    "SIPR",
    "NIPR",
    "DDG",
    "BICES",
    "WGS",
    "SBIRS",
    "GPS",
    "AEHF",
    "Minuteman",
    "ICBM",
    "PEO",
    "787",
    "777",
    "767",
    "747",
    "737",
    "Starliner",
]

# Locations for extraction
LOCATION_KEYWORDS = [
    "Huntsville",
    "Colorado Springs",
    "St. Louis",
    "San Diego",
    "El Segundo",
    "Redondo Beach",
    "Dallas",
    "Fort Worth",
    "Houston",
    "Titusville",
    "Kennedy Space Center",
    "KSC",
    "Cape Canaveral",
    "Charleston",
    "Seattle",
    "Denver",
    "Arlington",
    "McLean",
    "Fairfax",
    "Chantilly",
    "Springfield",
    "Hill AFB",
    "Tinker",
    "Wright-Patterson",
    "Eglin",
    "Luke",
    "San Antonio",
    "Fort Bragg",
    "Fort Liberty",
    "Michoud",
    "New Orleans",
    "Oklahoma City",
    "Omaha",
    "Offutt",
    "Norfolk",
    "Dahlgren",
    "Aberdeen",
    "Annapolis Junction",
    "Maryland",
    "Virginia",
    "Alabama",
    "Georgia",
    "Florida",
    "Texas",
    "Missouri",
    "California",
    "Ohio",
    "DC",
    "Washington",
]

ROLE_KEYWORDS = [
    "Systems Engineer",
    "Software Engineer",
    "Program Manager",
    "Project Manager",
    "Engineering Manager",
    "Electrical Engineer",
    "Mechanical Engineer",
    "Manufacturing Engineer",
    "Design Engineer",
    "Test Engineer",
    "Quality Engineer",
    "DevOps",
    "ISSO",
    "Cybersecurity",
    "Analyst",
    "Field Service",
    "FSE",
    "FSR",
    "Integration",
    "Requirements",
    "MBSE",
    "Site Lead",
    "Technical Lead",
    "Data Scientist",
    "Avionics",
    "Propulsion",
    "Structures",
    "Network Engineer",
    "System Administrator",
    "Help Desk",
    "DBA",
]


class HTMLStripper(HTMLParser):
    """Strip HTML tags and decode entities."""

    def __init__(self):
        super().__init__()
        self.result = []
        self.skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("br", "p", "li"):
            self.result.append("\n")

    def handle_data(self, data):
        self.result.append(data)

    def handle_entityref(self, name):
        self.result.append(f"&{name};")

    def get_text(self):
        return "".join(self.result).strip()


def strip_html(text):
    """Remove HTML tags from text, preserve line breaks."""
    if not text or pd.isna(text):
        return ""
    text = str(text)
    # Replace common HTML entities
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = text.replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("\xa0", " ").replace("�", "'")
    try:
        stripper = HTMLStripper()
        stripper.feed(text)
        result = stripper.get_text()
    except Exception:
        result = re.sub(r"<[^>]+>", " ", text)
    # Normalize whitespace
    result = re.sub(r"\n{3,}", "\n\n", result)
    result = re.sub(r" {2,}", " ", result)
    return result.strip()


def extract_companies(text):
    """Extract company names from note text."""
    found = []
    text_lower = text.lower() if text else ""
    for company in PRIME_CONTRACTORS:
        if company.lower() in text_lower:
            # Normalize variations
            if company in ("GDIT",):
                found.append("General Dynamics")
            elif company in ("RTX",):
                found.append("Raytheon")
            elif company in ("L3 Harris",):
                found.append("L3Harris")
            else:
                found.append(company)
    return list(set(found))


def extract_programs(text):
    """Extract program names/acronyms from note text."""
    found = []
    if not text:
        return found
    for prog in PROGRAM_KEYWORDS:
        # Use word boundary matching for short acronyms
        if len(prog) <= 4:
            if re.search(r"\b" + re.escape(prog) + r"\b", text, re.IGNORECASE):
                found.append(prog)
        else:
            if prog.lower() in text.lower():
                found.append(prog)
    return list(set(found))


def extract_locations(text):
    """Extract location references from note text."""
    found = []
    if not text:
        return found
    for loc in LOCATION_KEYWORDS:
        if loc.lower() in text.lower():
            found.append(loc)
    return list(set(found))


def extract_roles(text):
    """Extract role/title references from note text."""
    found = []
    if not text:
        return found
    text_lower = text.lower()
    for role in ROLE_KEYWORDS:
        if role.lower() in text_lower:
            found.append(role)
    return list(set(found))


def extract_headcount(text):
    """Extract headcount numbers from note text."""
    if not text:
        return []
    patterns = [
        r"(?:need|needs|hiring|looking for|in need of|team of|headcount[: ]*)\s*(\d+)",
        r"(\d+)\s*(?:engineers?|positions?|openings?|roles?|contractors?|people|staff)",
    ]
    counts = []
    for pat in patterns:
        matches = re.findall(pat, text, re.IGNORECASE)
        counts.extend(matches)
    return list(set(counts))


def extract_bill_rates(text):
    """Extract bill rate / dollar amounts from note text."""
    if not text:
        return []
    patterns = [
        r"\$[\d,]+(?:\.\d{2})?(?:/hr)?",
        r"[\d,]+k(?:\s*(?:a year|annually|salary))?",
    ]
    rates = []
    for pat in patterns:
        matches = re.findall(pat, text, re.IGNORECASE)
        rates.extend(matches)
    return list(set(rates))


def extract_emails(text):
    """Extract email addresses from note text."""
    if not text:
        return []
    return list(set(re.findall(r"[\w.+-]+@[\w.-]+\.\w+", text)))


def extract_phones(text):
    """Extract phone numbers from note text."""
    if not text:
        return []
    return list(set(re.findall(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", text)))


def parse_xls(filepath):
    """Parse the Bullhorn Notes Activity Report XLS file."""
    df = pd.read_excel(filepath)

    # The XLS has a header row in the data (row index 1 in the dataframe)
    # First row (index 0) is usually blank, row 1 has actual column names
    # Columns: Department, Note Author, Date Note Added, Type, Note Action, About, Status, Note Body

    # Rename columns based on the actual header row
    col_names = [
        "department",
        "note_author",
        "date_added",
        "type",
        "action",
        "about",
        "status",
        "note_body",
    ]
    # Find the header row - look for "Department" or "Note Author"
    header_idx = None
    for i in range(min(5, len(df))):
        row_vals = [str(v).strip() for v in df.iloc[i].values if pd.notna(v)]
        if any("Department" in v or "Note Author" in v for v in row_vals):
            header_idx = i
            break

    if header_idx is not None:
        # Skip rows up to and including header
        df = df.iloc[header_idx + 1 :].reset_index(drop=True)

    df.columns = col_names
    # Drop rows where essential fields are missing
    df = df.dropna(subset=["note_author", "about"], how="all").reset_index(drop=True)
    # Clean date column
    df["date_added"] = pd.to_datetime(df["date_added"], errors="coerce")
    df = df.dropna(subset=["date_added"]).reset_index(drop=True)

    print(
        f"Parsed {len(df)} notes from {df['date_added'].min()} to {df['date_added'].max()}"
    )
    return df


def process_notes(df):
    """Process all notes: clean HTML, extract entities."""
    records = []
    for _, row in df.iterrows():
        raw_body = (
            str(row.get("note_body", "")) if pd.notna(row.get("note_body")) else ""
        )
        clean_body = strip_html(raw_body)
        contact = (
            str(row.get("about", "")).strip() if pd.notna(row.get("about")) else ""
        )

        rec = {
            "source_sheet": "NotesActivityReport_Jan22_Feb16_2026",
            "department": str(row.get("department", "")).strip()
            if pd.notna(row.get("department"))
            else "",
            "note_author": str(row.get("note_author", "")).strip()
            if pd.notna(row.get("note_author"))
            else "",
            "date_added": row["date_added"].strftime("%m/%d/%Y")
            if pd.notna(row["date_added"])
            else "",
            "date_obj": row["date_added"],
            "type": str(row.get("type", "")).strip()
            if pd.notna(row.get("type"))
            else "",
            "action": str(row.get("action", "")).strip()
            if pd.notna(row.get("action"))
            else "",
            "about": contact,
            "status": str(row.get("status", "")).strip()
            if pd.notna(row.get("status"))
            else "",
            "note_body_raw": raw_body,
            "note_body_clean": clean_body,
            "extracted_primes": extract_companies(clean_body),
            "extracted_programs": extract_programs(clean_body),
            "extracted_roles": extract_roles(clean_body),
            "extracted_locations": extract_locations(clean_body),
            "extracted_headcount": extract_headcount(clean_body),
            "extracted_bill_rates": extract_bill_rates(clean_body),
            "extracted_emails": extract_emails(clean_body),
            "extracted_phones": extract_phones(clean_body),
        }
        records.append(rec)
    return records


def update_master_notes_csv(records):
    """Append new notes to master_notes.csv."""
    filepath = os.path.join(ANALYSIS_DIR, "master_notes.csv")
    existing = []
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            existing_fields = reader.fieldnames
            existing = list(reader)
        print(f"Existing master_notes.csv: {len(existing)} rows")

    fieldnames = [
        "source_sheet",
        "department",
        "note_author",
        "date_added",
        "type",
        "action",
        "about",
        "status",
        "note_body_raw",
        "note_body_clean",
        "extracted_primes",
        "extracted_programs",
        "extracted_contracts",
        "extracted_roles",
        "extracted_locations",
        "extracted_headcount",
        "extracted_bill_rates",
        "extracted_dates_mentioned",
        "extracted_experience_levels",
        "extracted_skills",
        "extracted_acronyms",
        "extracted_emails",
        "extracted_phone_numbers",
        "Column1",
    ]

    new_rows = []
    for rec in records:
        row = {
            "source_sheet": rec["source_sheet"],
            "department": rec["department"],
            "note_author": rec["note_author"],
            "date_added": rec["date_added"],
            "type": rec["type"],
            "action": rec["action"],
            "about": rec["about"],
            "status": rec["status"],
            "note_body_raw": rec["note_body_raw"],
            "note_body_clean": rec["note_body_clean"],
            "extracted_primes": str(rec["extracted_primes"]),
            "extracted_programs": str(rec["extracted_programs"]),
            "extracted_contracts": "[]",
            "extracted_roles": str(rec["extracted_roles"]),
            "extracted_locations": str(rec["extracted_locations"]),
            "extracted_headcount": str(rec["extracted_headcount"]),
            "extracted_bill_rates": str(rec["extracted_bill_rates"]),
            "extracted_dates_mentioned": "[]",
            "extracted_experience_levels": "[]",
            "extracted_skills": "[]",
            "extracted_acronyms": "[]",
            "extracted_emails": str(rec["extracted_emails"]),
            "extracted_phone_numbers": str(rec["extracted_phones"]),
            "Column1": "",
        }
        new_rows.append(row)

    all_rows = existing + new_rows
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)
    print(
        f"Updated master_notes.csv: {len(all_rows)} total rows (+{len(new_rows)} new)"
    )


def update_contacts_csv(records):
    """Update contacts.csv with new contacts from the notes."""
    filepath = os.path.join(ANALYSIS_DIR, "contacts.csv")
    existing = {}
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for row in reader:
                existing[row.get("name", "").strip()] = row

    # Build contact data from new notes
    contact_data = defaultdict(
        lambda: {
            "dates": [],
            "authors": set(),
            "departments": set(),
            "companies": set(),
            "programs": set(),
            "roles": set(),
            "statuses": set(),
            "interactions": 0,
        }
    )

    for rec in records:
        name = rec["about"]
        if not name:
            continue
        cd = contact_data[name]
        cd["dates"].append(rec["date_obj"])
        cd["authors"].add(rec["note_author"])
        cd["departments"].add(rec["department"])
        cd["companies"].update(rec["extracted_primes"])
        cd["programs"].update(rec["extracted_programs"])
        cd["roles"].update(rec["extracted_roles"])
        cd["statuses"].add(rec["status"])
        cd["interactions"] += 1

    new_contacts = 0
    updated_contacts = 0
    for name, cd in contact_data.items():
        if name in existing:
            # Update existing contact
            row = existing[name]
            old_interactions = int(row.get("interactions", 0) or 0)
            row["interactions"] = str(old_interactions + cd["interactions"])
            row["last_interaction"] = max(cd["dates"]).strftime("%m/%d/%Y")
            # Merge companies and programs
            old_companies = (
                _safe_parse_list(row.get("companies", "[]") or "[]") if row.get("companies") else []
            )
            old_programs = (
                _safe_parse_list(row.get("programs", "[]") or "[]") if row.get("programs") else []
            )
            merged_companies = list(set(old_companies) | cd["companies"])
            merged_programs = list(set(old_programs) | cd["programs"])
            row["companies"] = str(merged_companies)
            row["programs"] = str(merged_programs)
            updated_contacts += 1
        else:
            # New contact
            latest_status = list(cd["statuses"])[-1] if cd["statuses"] else ""
            existing[name] = {
                "name": name,
                "status": latest_status,
                "date_first_contact": min(cd["dates"]).strftime("%m/%d/%Y"),
                "salesperson": ", ".join(cd["authors"]),
                "department": ", ".join(cd["departments"]),
                "companies": str(list(cd["companies"])),
                "programs": str(list(cd["programs"])),
                "roles": str(list(cd["roles"])),
                "interactions": str(cd["interactions"]),
                "last_interaction": max(cd["dates"]).strftime("%m/%d/%Y"),
            }
            new_contacts += 1

    fieldnames = [
        "name",
        "status",
        "date_first_contact",
        "salesperson",
        "department",
        "companies",
        "programs",
        "roles",
        "interactions",
        "last_interaction",
    ]
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in existing.values():
            writer.writerow(row)
    print(
        f"Updated contacts.csv: {new_contacts} new, {updated_contacts} updated, {len(existing)} total"
    )
    return new_contacts, updated_contacts, len(existing)


def update_companies_csv(records):
    """Update companies.csv with new company data from notes."""
    filepath = os.path.join(ANALYSIS_DIR, "companies.csv")
    existing = {}
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing[row.get("company_name", "").strip()] = row

    # Aggregate company data from new notes
    company_data = defaultdict(
        lambda: {
            "mentions": 0,
            "contacts": set(),
            "programs": set(),
            "locations": set(),
            "roles": set(),
            "headcount": [],
        }
    )

    for rec in records:
        for company in rec["extracted_primes"]:
            cd = company_data[company]
            cd["mentions"] += 1
            if rec["about"]:
                cd["contacts"].add(rec["about"])
            cd["programs"].update(rec["extracted_programs"])
            cd["locations"].update(rec["extracted_locations"])
            cd["roles"].update(rec["extracted_roles"])
            cd["headcount"].extend(rec["extracted_headcount"])

    for company, cd in company_data.items():
        if company in existing:
            row = existing[company]
            old_mentions = int(row.get("total_mentions", 0) or 0)
            row["total_mentions"] = str(old_mentions + cd["mentions"])
            # Merge contacts
            old_contacts = (
                _safe_parse_list(row.get("contacts_list", "[]") or "[]")
                if row.get("contacts_list")
                else []
            )
            merged_contacts = list(set(old_contacts) | cd["contacts"])
            row["contacts_list"] = str(merged_contacts)
            row["unique_contacts"] = str(len(merged_contacts))
            # Merge programs
            old_programs = (
                _safe_parse_list(row.get("programs", "[]") or "[]") if row.get("programs") else []
            )
            merged_programs = list(set(old_programs) | cd["programs"])
            row["programs"] = str(merged_programs)
            # Merge locations
            old_locations = (
                _safe_parse_list(row.get("locations", "[]") or "[]") if row.get("locations") else []
            )
            merged_locations = list(set(old_locations) | cd["locations"])
            row["locations"] = str(merged_locations)
            # Merge roles
            old_roles = (
                _safe_parse_list(row.get("roles_needed", "[]") or "[]")
                if row.get("roles_needed")
                else []
            )
            merged_roles = list(set(old_roles) | cd["roles"])
            row["roles_needed"] = str(merged_roles)
        else:
            existing[company] = {
                "company_name": company,
                "total_mentions": str(cd["mentions"]),
                "unique_contacts": str(len(cd["contacts"])),
                "contacts_list": str(list(cd["contacts"])),
                "programs": str(list(cd["programs"])),
                "locations": str(list(cd["locations"])),
                "roles_needed": str(list(cd["roles"])),
                "contract_types": "[]",
                "total_headcount_mentioned": str(
                    sum(int(h) for h in cd["headcount"] if h.isdigit())
                ),
            }

    fieldnames = [
        "company_name",
        "total_mentions",
        "unique_contacts",
        "contacts_list",
        "programs",
        "locations",
        "roles_needed",
        "contract_types",
        "total_headcount_mentioned",
    ]
    # Sort by total mentions descending
    sorted_companies = sorted(
        existing.values(),
        key=lambda x: int(x.get("total_mentions", 0) or 0),
        reverse=True,
    )
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(sorted_companies)
    print(f"Updated companies.csv: {len(existing)} companies")


def update_programs_csv(records):
    """Update programs.csv with new program references from notes."""
    filepath = os.path.join(ANALYSIS_DIR, "programs.csv")
    existing = {}
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing[row.get("program_name", "").strip()] = row

    # Aggregate program data
    program_data = defaultdict(
        lambda: {
            "mentions": 0,
            "companies": set(),
            "contacts": set(),
            "locations": set(),
            "roles": set(),
        }
    )

    for rec in records:
        for prog in rec["extracted_programs"]:
            pd_ = program_data[prog]
            pd_["mentions"] += 1
            pd_["companies"].update(rec["extracted_primes"])
            if rec["about"]:
                pd_["contacts"].add(rec["about"])
            pd_["locations"].update(rec["extracted_locations"])
            pd_["roles"].update(rec["extracted_roles"])

    for prog, pd_ in program_data.items():
        if prog in existing:
            row = existing[prog]
            old_mentions = int(row.get("total_mentions", 0) or 0)
            row["total_mentions"] = str(old_mentions + pd_["mentions"])
            # Merge
            old_companies = (
                _safe_parse_list(row.get("companies", "[]") or "[]") if row.get("companies") else []
            )
            row["companies"] = str(list(set(old_companies) | pd_["companies"]))
            old_contacts = (
                _safe_parse_list(row.get("contacts_list", "[]") or "[]")
                if row.get("contacts_list")
                else []
            )
            merged_contacts = list(set(old_contacts) | pd_["contacts"])
            row["contacts_list"] = str(merged_contacts)
            row["unique_contacts"] = str(len(merged_contacts))
            old_locations = (
                _safe_parse_list(row.get("locations", "[]") or "[]") if row.get("locations") else []
            )
            row["locations"] = str(list(set(old_locations) | pd_["locations"]))
            old_roles = (
                _safe_parse_list(row.get("roles_mentioned", "[]") or "[]")
                if row.get("roles_mentioned")
                else []
            )
            row["roles_mentioned"] = str(list(set(old_roles) | pd_["roles"]))
        else:
            existing[prog] = {
                "program_name": prog,
                "total_mentions": str(pd_["mentions"]),
                "companies": str(list(pd_["companies"])),
                "unique_contacts": str(len(pd_["contacts"])),
                "contacts_list": str(list(pd_["contacts"])),
                "locations": str(list(pd_["locations"])),
                "roles_mentioned": str(list(pd_["roles"])),
            }

    fieldnames = [
        "program_name",
        "total_mentions",
        "companies",
        "unique_contacts",
        "contacts_list",
        "locations",
        "roles_mentioned",
    ]
    sorted_programs = sorted(
        existing.values(),
        key=lambda x: int(x.get("total_mentions", 0) or 0),
        reverse=True,
    )
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(sorted_programs)
    print(f"Updated programs.csv: {len(existing)} programs")


def update_timeline_csv(records):
    """Append new entries to timeline.csv."""
    filepath = os.path.join(ANALYSIS_DIR, "timeline.csv")
    existing = []
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            existing = list(reader)

    new_rows = []
    for rec in records:
        clean = rec["note_body_clean"]
        summary = clean[:200] if len(clean) > 200 else clean
        new_rows.append(
            {
                "date": rec["date_obj"].strftime("%Y-%m-%d"),
                "author": rec["note_author"],
                "contact": rec["about"],
                "action": rec["action"],
                "type": rec["type"],
                "companies": str(rec["extracted_primes"]),
                "programs": str(rec["extracted_programs"]),
                "status": rec["status"],
                "summary": summary.replace("\n", " "),
            }
        )

    all_rows = existing + new_rows
    fieldnames = [
        "date",
        "author",
        "contact",
        "action",
        "type",
        "companies",
        "programs",
        "status",
        "summary",
    ]
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"Updated timeline.csv: {len(all_rows)} total entries (+{len(new_rows)} new)")


def update_stats_json(records, existing_stats_path):
    """Update the analysis stats JSON."""
    with open(existing_stats_path, "r") as f:
        stats = json.load(f)

    old_total = stats["total_notes"]
    new_total = old_total + len(records)

    # Count new unique contacts
    new_contacts = set(r["about"] for r in records if r["about"])
    all_unique = stats["unique_contacts"]  # This was a count, not a set

    # Update date range
    new_dates = [r["date_obj"] for r in records]
    latest_new = max(new_dates).strftime("%Y-%m-%d %H:%M:%S")

    # Count companies in new notes
    company_counter = Counter()
    for rec in records:
        for c in rec["extracted_primes"]:
            company_counter[c] += 1

    # Update top_companies
    old_company_counts = {
        c["company_name"]: c["total_mentions"] for c in stats["top_companies"]
    }
    for company, count in company_counter.items():
        old_company_counts[company] = old_company_counts.get(company, 0) + count
    stats["top_companies"] = sorted(
        [
            {"company_name": k, "total_mentions": v}
            for k, v in old_company_counts.items()
        ],
        key=lambda x: x["total_mentions"],
        reverse=True,
    )

    # Count programs in new notes
    program_counter = Counter()
    for rec in records:
        for p in rec["extracted_programs"]:
            program_counter[p] += 1

    old_program_counts = {
        p["program_name"]: p["total_mentions"] for p in stats["top_programs"]
    }
    for prog, count in program_counter.items():
        old_program_counts[prog] = old_program_counts.get(prog, 0) + count
    stats["top_programs"] = sorted(
        [
            {"program_name": k, "total_mentions": v}
            for k, v in old_program_counts.items()
        ],
        key=lambda x: x["total_mentions"],
        reverse=True,
    )[:15]

    # Update status distribution
    status_counter = Counter(r["status"] for r in records if r["status"])
    for status, count in status_counter.items():
        stats["status_distribution"][status] = (
            stats["status_distribution"].get(status, 0) + count
        )

    # Update action types
    action_counter = Counter(r["action"] for r in records if r["action"])
    for action, count in action_counter.items():
        stats["action_types"][action] = stats["action_types"].get(action, 0) + count

    # Update authors
    author_counter = Counter(r["note_author"] for r in records if r["note_author"])
    for author, count in author_counter.items():
        stats["authors"][author] = stats["authors"].get(author, 0) + count

    # Update totals
    stats["total_notes"] = new_total
    stats["unique_contacts"] = all_unique + len(
        new_contacts
    )  # Approximate - may overcount
    stats["date_range"]["latest"] = latest_new

    with open(existing_stats_path, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"Updated stats: {old_total} -> {new_total} notes, latest date: {latest_new}")
    return stats


def update_master_data_aggregation(records):
    """Append to MASTER_DATA_AGGREGATION.csv in NOTES_DEEP_DIVE."""
    filepath = os.path.join(DEEP_DIVE_DIR, "MASTER_DATA_AGGREGATION.csv")
    existing = []
    fieldnames = None
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            existing = list(reader)

    if not fieldnames:
        fieldnames = [
            "Sheet",
            "Date",
            "Contact",
            "Author",
            "Type",
            "Action",
            "Category",
            "Status",
            "Department",
            "Companies",
            "Programs",
            "Locations",
            "Dollar_Amounts",
            "Headcounts",
            "Titles",
            "Emails",
            "Phones",
            "Note_Preview",
            "Full_Note",
        ]

    new_rows = []
    for rec in records:
        clean = rec["note_body_clean"]
        preview = clean[:200] if len(clean) > 200 else clean
        # Determine category
        category = "General"
        clean_lower = clean.lower()
        if any(
            w in clean_lower
            for w in ["hiring", "headcount", "openings", "positions", "need"]
        ):
            category = "Hiring"
        elif any(w in clean_lower for w in ["interview", "prescreen", "submitted"]):
            category = "Interview"
        elif any(w in clean_lower for w in ["visit", "onsite", "on-site", "met with"]):
            category = "Site Visit"
        elif any(
            w in clean_lower
            for w in ["follow up", "follow-up", "touch point", "check in"]
        ):
            category = "Follow-up"
        elif any(
            w in clean_lower for w in ["placed", "started", "start date", "onboard"]
        ):
            category = "Placement"
        elif any(w in clean_lower for w in ["proposal", "capture", "bid", "teaming"]):
            category = "Business Discussion"

        new_rows.append(
            {
                "Sheet": rec["source_sheet"],
                "Date": rec["date_obj"].strftime("%Y-%m-%d %H:%M:%S"),
                "Contact": rec["about"],
                "Author": rec["note_author"],
                "Type": rec["type"],
                "Action": rec["action"],
                "Category": category,
                "Status": rec["status"],
                "Department": rec["department"],
                "Companies": "|".join(rec["extracted_primes"]),
                "Programs": "|".join(rec["extracted_programs"]),
                "Locations": "|".join(rec["extracted_locations"]),
                "Dollar_Amounts": "|".join(rec["extracted_bill_rates"]),
                "Headcounts": "|".join(rec["extracted_headcount"]),
                "Titles": "|".join(rec["extracted_roles"]),
                "Emails": "|".join(rec["extracted_emails"]),
                "Phones": "|".join(rec["extracted_phones"]),
                "Note_Preview": preview.replace("\n", " "),
                "Full_Note": clean.replace("\n", " "),
            }
        )

    all_rows = existing + new_rows
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)
    print(
        f"Updated MASTER_DATA_AGGREGATION.csv: {len(all_rows)} total (+{len(new_rows)} new)"
    )
    return new_rows


def generate_new_notes_intelligence_report(records, stats):
    """Generate intelligence report for the new notes period."""
    filepath = os.path.join(
        DEEP_DIVE_DIR, "NOTES_INTELLIGENCE_EXTRACT_UPDATE_JAN22_FEB16.md"
    )

    # Identify high-value BD notes (hiring, programs, headcount)
    bd_notes = []
    for rec in records:
        clean = rec["note_body_clean"]
        if not clean or len(clean) < 50:
            continue
        clean_lower = clean.lower()
        is_bd = (
            rec["extracted_primes"]
            or rec["extracted_programs"]
            or rec["extracted_headcount"]
            or any(
                w in clean_lower
                for w in [
                    "hiring",
                    "headcount",
                    "openings",
                    "need",
                    "positions",
                    "program",
                    "contract",
                    "award",
                    "capture",
                    "bid",
                ]
            )
        )
        if is_bd and rec["type"] == "Contact":
            bd_notes.append(rec)

    # Sort by date
    bd_notes.sort(key=lambda x: x["date_obj"])

    # Stats for this period
    author_counter = Counter(r["note_author"] for r in records)
    company_counter = Counter()
    program_counter = Counter()
    action_counter = Counter(r["action"] for r in records)
    status_counter = Counter(r["status"] for r in records)
    dept_counter = Counter(r["department"] for r in records)

    for rec in records:
        for c in rec["extracted_primes"]:
            company_counter[c] += 1
        for p in rec["extracted_programs"]:
            program_counter[p] += 1

    lines = [
        "# Business Intelligence Extraction - Update",
        "",
        f"**Period:** January 22, 2026 - February 16, 2026",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**New Notes Processed:** {len(records)}",
        "",
        "---",
        "",
        "## Period Summary",
        "",
        f"- **Total New Notes:** {len(records)}",
        f"- **Unique Contacts Mentioned:** {len(set(r['about'] for r in records if r['about']))}",
        f"- **BD-Relevant Notes (Contact type with intel):** {len(bd_notes)}",
        "",
        "### Activity by Department",
        "",
        "| Department | Notes |",
        "|-----------|-------|",
    ]
    for dept, count in dept_counter.most_common():
        lines.append(f"| {dept} | {count} |")

    lines.extend(
        [
            "",
            "### Top Authors This Period",
            "",
            "| Author | Notes |",
            "|--------|-------|",
        ]
    )
    for author, count in author_counter.most_common(20):
        lines.append(f"| {author} | {count} |")

    lines.extend(
        [
            "",
            "### Companies Mentioned",
            "",
            "| Company | Mentions |",
            "|---------|----------|",
        ]
    )
    for company, count in company_counter.most_common():
        lines.append(f"| {company} | {count} |")

    lines.extend(
        [
            "",
            "### Programs Referenced",
            "",
            "| Program | Mentions |",
            "|---------|----------|",
        ]
    )
    for prog, count in program_counter.most_common():
        lines.append(f"| {prog} | {count} |")

    lines.extend(
        [
            "",
            "### Note Actions",
            "",
            "| Action | Count |",
            "|--------|-------|",
        ]
    )
    for action, count in action_counter.most_common():
        lines.append(f"| {action} | {count} |")

    lines.extend(
        [
            "",
            "### Contact Status Distribution",
            "",
            "| Status | Count |",
            "|--------|-------|",
        ]
    )
    for status, count in status_counter.most_common():
        lines.append(f"| {status} | {count} |")

    # Key BD intelligence notes
    lines.extend(
        [
            "",
            "---",
            "",
            "## Key BD Intelligence Notes",
            "",
            f"**Total BD-Relevant Notes:** {len(bd_notes)}",
            "",
        ]
    )

    for rec in bd_notes[:100]:  # Cap at 100 most relevant
        clean = rec["note_body_clean"]
        # Truncate very long notes
        display = clean[:500] + "..." if len(clean) > 500 else clean
        programs_str = (
            ", ".join(rec["extracted_programs"]) if rec["extracted_programs"] else "N/A"
        )
        companies_str = (
            ", ".join(rec["extracted_primes"])
            if rec["extracted_primes"]
            else "Company TBD"
        )

        lines.extend(
            [
                f"### {rec['about']} - {companies_str}",
                f"**Date:** {rec['date_obj'].strftime('%Y-%m-%d')}",
                f"**Author:** {rec['note_author']}",
                f"**Programs:** {programs_str}",
            ]
        )
        if rec["extracted_headcount"]:
            lines.append(f"**Headcount:** {', '.join(rec['extracted_headcount'])}")
        if rec["extracted_bill_rates"]:
            lines.append(f"**Rates/Budget:** {', '.join(rec['extracted_bill_rates'])}")
        lines.extend(
            [
                f"**Details:**",
                display,
                "",
            ]
        )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Generated intelligence report: {len(bd_notes)} BD notes documented")
    return bd_notes


def generate_updated_executive_summary(stats, records, contact_counts):
    """Generate an updated executive summary addendum."""
    filepath = os.path.join(
        ANALYSIS_DIR, "ANALYSIS", "01_EXECUTIVE_SUMMARY_UPDATE_JAN22_FEB16.md"
    )

    new_contacts_count, updated_contacts, total_contacts = contact_counts

    # Count client visits in new data
    client_visits = [r for r in records if r["action"] == "Client Visit"]
    appointments = [r for r in records if r["action"] == "Appointment"]
    prescreens = [r for r in records if r["action"] == "Prescreen"]

    # Unique authors
    authors = Counter(r["note_author"] for r in records)

    # Companies
    company_counter = Counter()
    for rec in records:
        for c in rec["extracted_primes"]:
            company_counter[c] += 1

    lines = [
        "# Activity Update - January 22 to February 16, 2026",
        "",
        f"**Analysis Date:** {datetime.now().strftime('%B %d, %Y')}",
        f"**Data Period:** January 22, 2026 - February 16, 2026",
        f"**Previous Coverage:** July 23, 2024 - January 21, 2026",
        "",
        "---",
        "",
        "## New Activity Overview",
        "",
        f"- **New Notes Added:** {len(records)}",
        f"- **New Unique Contacts:** {new_contacts_count}",
        f"- **Updated Existing Contacts:** {updated_contacts}",
        f"- **Total Contacts in Database:** {total_contacts}",
        f"- **Client Visits:** {len(client_visits)}",
        f"- **Appointments:** {len(appointments)}",
        f"- **Prescreens:** {len(prescreens)}",
        f"- **Active Authors:** {len(authors)}",
        "",
        "### Cumulative Totals (All Time)",
        "",
        f"- **Total Notes:** {stats['total_notes']}",
        f"- **Date Range:** {stats['date_range']['earliest']} to {stats['date_range']['latest']}",
        "",
        "---",
        "",
        "## Top Authors This Period",
        "",
        "| Author | Notes | Rank |",
        "|--------|-------|------|",
    ]
    for i, (author, count) in enumerate(authors.most_common(20), 1):
        lines.append(f"| {author} | {count} | #{i} |")

    lines.extend(
        [
            "",
            "## Company Activity This Period",
            "",
            "| Company | New Mentions |",
            "|---------|-------------|",
        ]
    )
    for company, count in company_counter.most_common():
        lines.append(f"| {company} | {count} |")

    lines.extend(
        [
            "",
            "## Updated Top Companies (All Time)",
            "",
            "| Company | Total Mentions |",
            "|---------|---------------|",
        ]
    )
    for c in stats["top_companies"][:15]:
        lines.append(f"| {c['company_name']} | {c['total_mentions']} |")

    lines.extend(
        [
            "",
            "## Updated Top Programs (All Time)",
            "",
            "| Program | Total Mentions |",
            "|---------|---------------|",
        ]
    )
    for p in stats["top_programs"][:15]:
        lines.append(f"| {p['program_name']} | {p['total_mentions']} |")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Generated executive summary update")


def generate_contact_program_matrix_update(records):
    """Generate an updated contact-program matrix for the new period."""
    filepath = os.path.join(
        DEEP_DIVE_DIR, "CONTACT_PROGRAM_MATRIX_UPDATE_JAN22_FEB16.md"
    )

    # Build contact -> company -> programs mapping
    matrix = defaultdict(lambda: defaultdict(set))
    contact_authors = defaultdict(set)
    contact_dates = defaultdict(list)

    for rec in records:
        if not rec["about"] or not rec["extracted_primes"]:
            continue
        for company in rec["extracted_primes"]:
            matrix[rec["about"]][company].update(rec["extracted_programs"])
        contact_authors[rec["about"]].add(rec["note_author"])
        contact_dates[rec["about"]].append(rec["date_obj"])

    lines = [
        "# Contact-Program Matrix Update",
        "",
        f"**Period:** January 22 - February 16, 2026",
        f"**Contacts with Company/Program Intel:** {len(matrix)}",
        "",
        "---",
        "",
    ]

    # Group by company
    company_contacts = defaultdict(list)
    for contact, companies in matrix.items():
        for company, programs in companies.items():
            company_contacts[company].append((contact, programs))

    for company in sorted(company_contacts.keys()):
        contacts = company_contacts[company]
        lines.extend(
            [
                f"## {company}",
                "",
                "| Contact | Programs | Authors | Last Activity |",
                "|---------|----------|---------|---------------|",
            ]
        )
        for contact, programs in sorted(contacts, key=lambda x: x[0]):
            progs = ", ".join(sorted(programs)) if programs else "-"
            authors = ", ".join(contact_authors.get(contact, set()))
            last_date = max(contact_dates.get(contact, [datetime.now()])).strftime(
                "%Y-%m-%d"
            )
            lines.append(f"| {contact} | {progs} | {authors} | {last_date} |")
        lines.append("")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Generated contact-program matrix update: {len(matrix)} contacts")


def main():
    if len(sys.argv) < 2:
        # Default path
        xls_path = os.path.join(
            os.path.dirname(BASE_DIR),
            "docs",
            "Bullhorn Exports",
            "Notes Activity Report - Jan22-Feb16-2026.XLS",
        )
    else:
        xls_path = sys.argv[1]

    if not os.path.exists(xls_path):
        print(f"ERROR: File not found: {xls_path}")
        sys.exit(1)

    print(f"=== Bullhorn Notes Ingestion ===")
    print(f"Source: {xls_path}")
    print()

    # Step 1: Parse XLS
    print("Step 1: Parsing XLS...")
    df = parse_xls(xls_path)

    # Step 2: Process notes (clean HTML, extract entities)
    print("\nStep 2: Processing notes...")
    records = process_notes(df)
    print(f"Processed {len(records)} records")

    # Step 3: Update master_notes.csv
    print("\nStep 3: Updating master_notes.csv...")
    update_master_notes_csv(records)

    # Step 4: Update contacts.csv
    print("\nStep 4: Updating contacts.csv...")
    contact_counts = update_contacts_csv(records)

    # Step 5: Update companies.csv
    print("\nStep 5: Updating companies.csv...")
    update_companies_csv(records)

    # Step 6: Update programs.csv
    print("\nStep 6: Updating programs.csv...")
    update_programs_csv(records)

    # Step 7: Update timeline.csv
    print("\nStep 7: Updating timeline.csv...")
    update_timeline_csv(records)

    # Step 8: Update stats JSON
    print("\nStep 8: Updating stats JSON...")
    stats_path = os.path.join(ANALYSIS_DIR, "colton_scurry_analysis_stats.json")
    stats = update_stats_json(records, stats_path)

    # Step 9: Update MASTER_DATA_AGGREGATION.csv
    print("\nStep 9: Updating MASTER_DATA_AGGREGATION.csv...")
    update_master_data_aggregation(records)

    # Step 10: Generate intelligence report
    print("\nStep 10: Generating intelligence report...")
    bd_notes = generate_new_notes_intelligence_report(records, stats)

    # Step 11: Generate executive summary update
    print("\nStep 11: Generating executive summary update...")
    generate_updated_executive_summary(stats, records, contact_counts)

    # Step 12: Generate contact-program matrix update
    print("\nStep 12: Generating contact-program matrix update...")
    generate_contact_program_matrix_update(records)

    print("\n=== COMPLETE ===")
    print(f"Total new notes ingested: {len(records)}")
    print(f"BD-relevant notes identified: {len(bd_notes)}")
    print(f"New contacts added: {contact_counts[0]}")
    print(f"Existing contacts updated: {contact_counts[1]}")
    print(f"Total contacts in database: {contact_counts[2]}")
    print(f"\nFiles updated:")
    print(f"  - master_notes.csv")
    print(f"  - contacts.csv")
    print(f"  - companies.csv")
    print(f"  - programs.csv")
    print(f"  - timeline.csv")
    print(f"  - colton_scurry_analysis_stats.json")
    print(f"  - NOTES_DEEP_DIVE/MASTER_DATA_AGGREGATION.csv")
    print(f"  - NOTES_DEEP_DIVE/NOTES_INTELLIGENCE_EXTRACT_UPDATE_JAN22_FEB16.md")
    print(f"  - ANALYSIS/01_EXECUTIVE_SUMMARY_UPDATE_JAN22_FEB16.md")
    print(f"  - NOTES_DEEP_DIVE/CONTACT_PROGRAM_MATRIX_UPDATE_JAN22_FEB16.md")


if __name__ == "__main__":
    main()
