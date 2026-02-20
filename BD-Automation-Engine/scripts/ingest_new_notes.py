"""
Ingest new Bullhorn AM Notes (Feb 16-20, 2026) into the BD pipeline.
- Parses XLS export
- Extracts intelligence (primes, programs, hiring signals, etc.)
- Appends to master_notes.csv and timeline.csv
- Loads into master_federal_contracts.db activities table
"""
import csv
import hashlib
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

BASE = Path(__file__).parent.parent
XLS_PATH = BASE / "Engine7_BullhornETL" / "data" / "2.16-2.20BullHornAMNotesActivity.XLS"
MASTER_NOTES = BASE / "data" / "bullhorn_analysis" / "source_csvs" / "master_notes.csv"
TIMELINE_CSV = BASE / "data" / "bullhorn_analysis" / "source_csvs" / "timeline.csv"
DB_PATH = BASE / "data" / "master_federal_contracts.db"

# Known primes and programs for extraction
PRIMES = [
    "Leidos", "GDIT", "General Dynamics", "Northrop Grumman", "Northrop",
    "Lockheed Martin", "Lockheed", "LMCO", "Boeing", "Raytheon", "RTX",
    "SAIC", "CACI", "Booz Allen", "BAH", "Peraton", "ManTech", "KBR",
    "L3Harris", "L3 Harris", "Parsons", "Jacobs", "Deloitte", "Accenture",
    "AWS", "Microsoft", "Palantir", "Sierra Nevada", "SNC", "BAE Systems",
    "BAE", "Amentum", "V2X", "Serco", "CGI", "Maximus", "ICF", "Engility",
    "Alion", "DLT", "CSRA", "Vencore", "Noblis", "Torch Technologies",
    "Intelligent Waves", "Telos", "Akima", "LinQuest", "Allyon",
]

PROGRAMS = [
    "DCGS", "NGEN", "GSM-O", "GSMO", "DES", "Defense Enclave", "ABMS",
    "JRSS", "Cloud One", "DEOS", "AESD", "AFNCR", "JADC2", "CYBERCOM",
    "Platform One", "HITS", "HPCMP", "CENTCOM", "SOCOM", "INSCOM",
    "BICES", "ISEO", "I2TS", "I3TS", "RS3", "Alliant", "OASIS", "SEWP",
    "CIO-SP3", "ENCORE", "NETCENTS", "MCEN", "GBSD", "NGI", "IBCS",
    "Aegis", "THAAD", "Patriot", "FORGE", "MHS GENESIS", "MOSSAIC",
    "SITEC", "NGA", "NRO", "NSA", "DIA", "DISA", "DLA", "FAA",
    "Space Force", "USSF", "SLS", "Orion", "SDA", "MDA", "JCIDS",
    "LOGCAP", "ARNG", "ARL", "PEO", "FORSCOM", "TRADOC", "ARCYBER",
    "NAWCAD", "NAVSEA", "NAVAIR", "SPAWAR", "NIWC", "ONR",
    "C2BMC", "COOLR", "PRISM", "MITS", "ECIS", "HOPE",
    "VC25B", "VC25A", "E4B", "STOL", "EDIS", "RITS",
    "BOA", "JTAGS", "FMS", "Project Convergence",
]

CLEARANCES = [
    "TS/SCI", "TS/SCI Poly", "TS/SCI CI Poly", "TS/SCI Full Scope",
    "Top Secret", "TS", "Secret", "Public Trust",
]

HIRING_KEYWORDS = [
    r"open\s*(req|position|role|job|head\s*count)",
    r"need\s*(to\s*hire|someone|a\s*\w+\s*engineer|people|candidates|contractor)",
    r"backfill", r"hiring", r"looking\s*for", r"staffing",
    r"head\s*count", r"headcount", r"new\s*position",
    r"surge", r"ramp\s*up", r"attrition", r"turnover",
    r"interview", r"open\s*req", r"requisition",
    r"bill\s*rate", r"replacement", r"vacancy",
]

TRACTION_KEYWORDS = [
    r"meeting\s*set", r"appointment", r"set\s*up\s*(a|an)\s*meeting",
    r"scheduled", r"call\s*back", r"follow\s*up", r"interested",
    r"send\s*(me|over|us)\s*(resume|candidate|the)", r"good\s*call",
    r"great\s*conversation", r"warm\s*intro",
]

POSITIVE_KEYWORDS = [
    r"placement", r"placed", r"started", r"onboard",
    r"accepted\s*(the|our)\s*offer", r"signed", r"converted",
    r"extension", r"renewed",
]


def clean_html(text):
    """Strip HTML tags and clean whitespace."""
    if not text or pd.isna(text):
        return ""
    text = str(text)
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'[\xa0\u00a0]', ' ', text)  # non-breaking spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_entities(text):
    """Extract primes, programs, clearances, bill rates from note text."""
    result = {
        "primes": [],
        "programs": [],
        "clearances": [],
        "bill_rates": [],
        "locations": [],
        "hiring_signal": False,
        "traction": False,
        "positive_response": False,
    }
    if not text:
        return result

    text_lower = text.lower()
    text_upper = text

    # Primes
    for p in PRIMES:
        if p.lower() in text_lower:
            result["primes"].append(p)

    # Programs
    for p in PROGRAMS:
        if len(p) <= 3:
            # Short acronyms need word boundary matching
            if re.search(r'\b' + re.escape(p) + r'\b', text_upper):
                result["programs"].append(p)
        elif p.lower() in text_lower:
            result["programs"].append(p)

    # Clearances
    for c in CLEARANCES:
        if c.lower() in text_lower:
            result["clearances"].append(c)

    # Bill rates
    for m in re.finditer(r'\$\s*(\d{2,3}(?:\.\d{2})?)\s*/\s*hr', text):
        result["bill_rates"].append(m.group(0))

    # Hiring signals
    for pattern in HIRING_KEYWORDS:
        if re.search(pattern, text_lower):
            result["hiring_signal"] = True
            break

    # Traction
    for pattern in TRACTION_KEYWORDS:
        if re.search(pattern, text_lower):
            result["traction"] = True
            break

    # Positive response
    for pattern in POSITIVE_KEYWORDS:
        if re.search(pattern, text_lower):
            result["positive_response"] = True
            break

    return result


def parse_xls():
    """Parse the Bullhorn XLS export into structured records."""
    df = pd.read_excel(str(XLS_PATH), engine='xlrd', header=None, skiprows=2)
    df.columns = ['department', 'note_author', 'date_added', 'type', 'action', 'about', 'status', 'note_body']
    df = df.dropna(how='all')
    # Drop the header echo row
    df = df[df['note_author'] != 'Note Author']
    df['department'] = df['department'].ffill()
    df['date_added'] = pd.to_datetime(df['date_added'], errors='coerce')

    records = []
    for _, row in df.iterrows():
        if pd.isna(row['note_author']) or pd.isna(row['about']):
            continue

        raw_body = str(row['note_body']) if pd.notna(row['note_body']) else ""
        clean_body = clean_html(raw_body)
        entities = extract_entities(clean_body)

        date_str = row['date_added'].strftime('%m/%d/%Y') if pd.notna(row['date_added']) else ""
        date_iso = row['date_added'].strftime('%Y-%m-%d') if pd.notna(row['date_added']) else ""

        record_id = hashlib.md5(
            f"{row['note_author']}_{row['about']}_{date_str}_{clean_body[:100]}".encode()
        ).hexdigest()[:16]

        records.append({
            "id": record_id,
            "department": str(row['department']).strip() if pd.notna(row['department']) else "",
            "note_author": str(row['note_author']).strip(),
            "date_added": date_str,
            "date_iso": date_iso,
            "type": str(row['type']).strip() if pd.notna(row['type']) else "",
            "action": str(row['action']).strip() if pd.notna(row['action']) else "",
            "about": str(row['about']).strip(),
            "status": str(row['status']).strip() if pd.notna(row['status']) else "",
            "note_body_raw": raw_body,
            "note_body_clean": clean_body,
            "extracted_primes": entities["primes"],
            "extracted_programs": entities["programs"],
            "extracted_clearances": entities["clearances"],
            "extracted_bill_rates": entities["bill_rates"],
            "hiring_signal": entities["hiring_signal"],
            "traction": entities["traction"],
            "positive_response": entities["positive_response"],
        })

    return records


def append_to_master_notes(records):
    """Append new records to master_notes.csv."""
    existing_ids = set()
    if MASTER_NOTES.exists():
        with open(MASTER_NOTES, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # Count existing rows for dedup awareness
            for row in reader:
                pass

    fieldnames = [
        'source_sheet', 'department', 'note_author', 'date_added', 'type',
        'action', 'about', 'status', 'note_body_raw', 'note_body_clean',
        'extracted_primes', 'extracted_programs', 'extracted_contracts',
        'extracted_roles', 'extracted_locations', 'extracted_headcount',
        'extracted_bill_rates', 'extracted_dates_mentioned',
        'extracted_experience_levels', 'extracted_skills',
        'extracted_acronyms', 'extracted_emails', 'extracted_phone_numbers',
        'Column1',
    ]

    new_count = 0
    with open(MASTER_NOTES, 'a', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        for r in records:
            writer.writerow({
                'source_sheet': '2.16-2.20_import',
                'department': r['department'],
                'note_author': r['note_author'],
                'date_added': r['date_added'],
                'type': r['type'],
                'action': r['action'],
                'about': r['about'],
                'status': r['status'],
                'note_body_raw': r['note_body_raw'],
                'note_body_clean': r['note_body_clean'],
                'extracted_primes': json.dumps(r['extracted_primes']),
                'extracted_programs': json.dumps(r['extracted_programs']),
                'extracted_contracts': '',
                'extracted_roles': '',
                'extracted_locations': '',
                'extracted_headcount': '',
                'extracted_bill_rates': json.dumps(r['extracted_bill_rates']),
                'extracted_dates_mentioned': '',
                'extracted_experience_levels': '',
                'extracted_skills': '',
                'extracted_acronyms': '',
                'extracted_emails': '',
                'extracted_phone_numbers': '',
                'Column1': '',
            })
            new_count += 1

    print(f"  Appended {new_count} notes to master_notes.csv")
    return new_count


def append_to_timeline(records):
    """Append new records to timeline.csv."""
    fieldnames = ['date', 'author', 'contact', 'action', 'type', 'companies', 'programs', 'status', 'summary']

    new_count = 0
    with open(TIMELINE_CSV, 'a', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        for r in records:
            summary = r['note_body_clean'][:200] if r['note_body_clean'] else ""
            writer.writerow({
                'date': r['date_iso'],
                'author': r['note_author'],
                'contact': r['about'],
                'action': r['action'],
                'type': r['type'],
                'companies': '; '.join(r['extracted_primes']),
                'programs': '; '.join(r['extracted_programs']),
                'status': r['status'],
                'summary': summary,
            })
            new_count += 1

    print(f"  Appended {new_count} entries to timeline.csv")
    return new_count


def load_to_database(records):
    """Load new notes into the master database activities table."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Get max bullhorn_activity_id
    cursor.execute("SELECT MAX(CAST(bullhorn_activity_id AS INTEGER)) FROM activities")
    max_id = cursor.fetchone()[0] or 0

    inserted = 0
    for i, r in enumerate(records):
        activity_id = max_id + i + 1
        record_id = r['id']

        try:
            cursor.execute("""
                INSERT OR IGNORE INTO activities (
                    id, bullhorn_activity_id, activity_type, action, about,
                    activity_date, actor, note_text, comments,
                    hiring_signal, positive_response, traction,
                    programs_mentioned, primes_mentioned, locations,
                    source_file, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record_id,
                str(activity_id),
                r['type'],
                r['action'],
                r['about'],
                r['date_iso'],
                r['note_author'],
                r['note_body_clean'],
                r['note_body_raw'],
                1 if r['hiring_signal'] else 0,
                1 if r['positive_response'] else 0,
                1 if r['traction'] else 0,
                '; '.join(r['extracted_programs']),
                '; '.join(r['extracted_primes']),
                '',
                '2.16-2.20BullHornAMNotesActivity.XLS',
                datetime.now().isoformat(),
            ))
            inserted += 1
        except sqlite3.IntegrityError:
            pass

    conn.commit()

    # Verify
    cursor.execute("SELECT COUNT(*) FROM activities")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM activities WHERE source_file = '2.16-2.20BullHornAMNotesActivity.XLS'")
    new_total = cursor.fetchone()[0]
    cursor.execute("SELECT MIN(activity_date), MAX(activity_date) FROM activities WHERE activity_date IS NOT NULL")
    dates = cursor.fetchone()

    print(f"  Inserted {inserted} new activities into DB")
    print(f"  Total activities now: {total}")
    print(f"  New import activities: {new_total}")
    print(f"  Date range now: {dates[0]} to {dates[1]}")

    conn.close()
    return inserted


def print_intelligence_summary(records):
    """Print summary of extracted intelligence from new notes."""
    print("\n" + "=" * 80)
    print("INTELLIGENCE EXTRACTION SUMMARY — Feb 16-20, 2026")
    print("=" * 80)

    # Hiring signals
    hiring = [r for r in records if r['hiring_signal']]
    traction = [r for r in records if r['traction']]
    positive = [r for r in records if r['positive_response']]

    print(f"\n  Total new notes: {len(records)}")
    print(f"  Hiring signals: {len(hiring)}")
    print(f"  Traction (meetings/callbacks): {len(traction)}")
    print(f"  Positive responses: {len(positive)}")

    # By author
    print("\n  --- Notes by Author ---")
    from collections import Counter
    authors = Counter(r['note_author'] for r in records)
    for a, c in authors.most_common():
        hire_count = sum(1 for r in records if r['note_author'] == a and r['hiring_signal'])
        tract_count = sum(1 for r in records if r['note_author'] == a and r['traction'])
        print(f"    {a:25s}: {c:3d} notes | {hire_count:2d} hiring | {tract_count:2d} traction")

    # Primes mentioned
    print("\n  --- Primes Mentioned ---")
    all_primes = Counter()
    for r in records:
        for p in r['extracted_primes']:
            all_primes[p] += 1
    for p, c in all_primes.most_common(20):
        print(f"    {p:25s}: {c} mentions")

    # Programs mentioned
    print("\n  --- Programs Mentioned ---")
    all_programs = Counter()
    for r in records:
        for p in r['extracted_programs']:
            all_programs[p] += 1
    for p, c in all_programs.most_common(20):
        print(f"    {p:25s}: {c} mentions")

    # Hiring signal details
    print("\n  --- Hiring Signal Notes (top 20) ---")
    for r in sorted(hiring, key=lambda x: x['date_iso'], reverse=True)[:20]:
        primes = ', '.join(r['extracted_primes'][:3]) or 'N/A'
        progs = ', '.join(r['extracted_programs'][:3]) or 'N/A'
        body = r['note_body_clean'][:120]
        print(f"    [{r['date_iso']}] {r['note_author']:15s} -> {r['about']:25s}")
        print(f"      Primes: {primes} | Programs: {progs}")
        print(f"      {body}")
        print()

    # SAIC specific
    saic_notes = [r for r in records if 'SAIC' in r['extracted_primes'] or 'SAIC' in str(r['note_body_clean']).upper()]
    print(f"\n  --- SAIC-Specific Notes: {len(saic_notes)} ---")
    for r in saic_notes:
        print(f"    [{r['date_iso']}] {r['note_author']:15s} -> {r['about']:25s}")
        print(f"      {r['note_body_clean'][:200]}")
        print()

    return {
        'total': len(records),
        'hiring_signals': len(hiring),
        'traction': len(traction),
        'positive': len(positive),
        'authors': dict(authors),
        'primes': dict(all_primes),
        'programs': dict(all_programs),
        'saic_notes': len(saic_notes),
    }


def main():
    print("=" * 80)
    print("BULLHORN NOTES INGESTION — Feb 16-20, 2026")
    print("=" * 80)

    # 1. Parse XLS
    print("\n[1/4] Parsing XLS...")
    records = parse_xls()
    print(f"  Parsed {len(records)} notes")

    # 2. Append to master_notes.csv
    print("\n[2/4] Appending to master_notes.csv...")
    append_to_master_notes(records)

    # 3. Append to timeline.csv
    print("\n[3/4] Appending to timeline.csv...")
    append_to_timeline(records)

    # 4. Load to database
    print("\n[4/4] Loading to master database...")
    load_to_database(records)

    # 5. Intelligence summary
    stats = print_intelligence_summary(records)

    # Save stats for downstream use
    stats_path = BASE / "data" / "bullhorn_analysis" / "ingestion_stats_20260220.json"
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2, default=str)
    print(f"\n  Stats saved to: {stats_path}")

    return records, stats


if __name__ == "__main__":
    records, stats = main()
