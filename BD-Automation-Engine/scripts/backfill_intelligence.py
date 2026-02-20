"""Backfill NLP intelligence extraction on 50,710 old activity records.

Reads note_body, note_author, date_added from bullhorn_master.db call_notes,
runs entity extraction (primes, programs, hiring signals, traction, etc.),
and updates master_federal_contracts.db activities table.
"""
import sqlite3
import re
import time
from pathlib import Path

BASE = Path(__file__).parent.parent
MASTER_DB = BASE / "data" / "master_federal_contracts.db"
BULLHORN_DB = BASE / "Engine7_BullhornETL" / "data" / "bullhorn_master.db"

BATCH_SIZE = 2000

# ─────────────────────────────────────────────────────────────────────────────
# NLP Extraction - same patterns as ingest_new_notes.py
# ─────────────────────────────────────────────────────────────────────────────

PRIMES = [
    "Leidos", "GDIT", "General Dynamics", "Northrop Grumman", "NGC", "Raytheon",
    "RTX", "Lockheed", "LMCO", "L3Harris", "Harris", "BAE Systems", "BAE",
    "Booz Allen", "CACI", "ManTech", "Peraton", "SAIC", "Accenture Federal",
    "Accenture", "Deloitte", "IBM", "Oracle", "Microsoft", "AWS", "Amazon",
    "Palantir", "Parsons", "KBR", "AECOM", "Jacobs", "Serco", "CGI",
    "Maximus", "ICF", "Unisys", "DXC", "Amentum", "V2X", "Vectrus",
    "PAE", "Engility", "Alion", "Vencore", "KeyW", "ECS Federal",
    "Telos", "Sotera", "Boeing", "SRC",
]
PRIME_PAT = re.compile(
    r"\b(" + "|".join(re.escape(p) for p in PRIMES) + r")\b", re.IGNORECASE
)

PROGRAMS = [
    "DCGS", "NGEN", "GSM-O", "GSMO", "DES", "Defense Enclave", "Cloud One",
    "DEOS", "milCloud", "JEDI", "JWCC", "ABMS", "JADC2", "IBCS", "Aegis",
    "SEWP", "CIO-SP3", "ALLIANT", "OASIS", "NETCENTS", "ENCORE",
    "INSCOM", "I2TS", "BICES", "RS3", "CENTCOM", "ARCYBER", "CYBERCOM",
    "DISA", "SOCOM", "INDOPACOM", "SOUTHCOM", "TRANSCOM", "EUCOM",
    "AFRICOM", "SPACECOM", "STRATCOM", "NORTHCOM", "NGA", "NSA",
    "DIA", "NRO", "CIA", "FBI", "DHS", "CBP", "ICE", "TSA", "FEMA",
    "MDA", "BMDS", "THAAD", "Patriot", "SBIRS", "OPIR", "GBSD",
    "Sentinel", "ICBM", "Minuteman", "B-21", "F-35", "F35", "F-22", "F22",
    "KC-46", "P-8", "MQ-9", "MQ-25", "V-22", "CH-53K", "AH-64",
    "Black Hawk", "Apache", "ALIS", "ODIN", "GCSS", "DPAS", "DEAMS",
    "EBS", "GFEBS", "LMP", "ACAT", "AFIT", "NAVAIR", "NAVSEA",
    "MARCORSYSCOM", "PEO", "SPAWAR", "NIWC", "AFLCMC", "AFMC",
    "SEAPORT", "SLS", "VC25", "E4B", "AWACS", "MCEN", "ARLE",
    "LEOS", "Starliner", "ISR",
]
PROGRAM_PAT = re.compile(
    r"\b(" + "|".join(re.escape(p) for p in PROGRAMS) + r")\b", re.IGNORECASE
)

HIRING_PATS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"open\s*(req|position|role|job|head)",
        r"backfill",
        r"hiring",
        r"head\s*count",
        r"need[s]?\s+\d+",
        r"looking\s+(for|to\s+hire|to\s+fill|to\s+bring)",
        r"staffing\s+(up|need|gap|shortfall)",
        r"positions?\s+(open|available|posted|approved)",
        r"req[s]?\s+(open|posted|approved|pending)",
        r"new\s+(req|position|role|opening|job)",
        r"grow(ing)?\s+(the\s+)?team",
        r"attrition",
        r"need\s+(a|an|more|additional)\s+\w+\s+(engineer|analyst|developer|admin|specialist|manager|lead)",
        r"team\s+of\s+\d+",
        r"bring\s+on\s+\d+",
        r"contractor\s+(need|position|req|opening)",
        r"replacing\s+\w+",
        r"\d+\s+(open|new)?\s*(position|req|role|job|opening)",
    ]
]

TRACTION_PATS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"meeting\s*(set|scheduled|confirmed|booked)",
        r"appointment\s*(set|scheduled)",
        r"scheduled\s*(a\s+)?(call|meeting|visit|intro|follow)",
        r"set\s+(up|a)\s+(meeting|call|time|intro)",
        r"follow[- ]?up\s*(call|meeting|scheduled)",
        r"on[- ]?site\s*(meeting|visit)",
        r"met\s+with",
        r"great\s+(meeting|call|conversation|discussion)",
        r"dinner\s+(with|at)",
        r"lunch\s+(with|at)",
        r"coffee\s+(with|at)",
        r"spoke\s+with\s+\w+.*\b(about|regarding|re:|discuss)",
        r"introduced\s+(us|me|to)",
        r"intro\s*call",
        r"warm\s*transfer",
    ]
]

POSITIVE_PATS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"interested\s+in\s+(our|working|partnering|using)",
        r"wants?\s+to\s+(see|review|get|discuss|explore|learn|meet|partner)",
        r"send\s+(me|him|her|them|over|the)\s+(resume|candidate|profile|info)",
        r"submit\s+(candidate|resume|profile)",
        r"approved\s+(to|for)\s+(hire|interview|submit|onboard)",
        r"verbal\s+(offer|approval|commitment)",
        r"moving\s+forward",
        r"green\s*light",
        r"excited\s+(about|to)",
        r"great\s+fit",
        r"perfect\s+(fit|match|candidate)",
        r"love[ds]?\s+(the|this|that)\s+(candidate|resume|background|profile)",
        r"start\s+date\s*(set|confirmed|is)",
    ]
]

CLEARANCE_PAT = re.compile(
    r"\b(TS/SCI|TS|SCI|Secret|Top\s*Secret|CI\s*Poly|Full\s*Scope|"
    r"Polygraph|Public\s*Trust|Interim|SAP|SAR|Q\s*Clearance|L\s*Clearance)\b",
    re.IGNORECASE
)

BILL_RATE_PAT = re.compile(r"\$\s*(\d{2,3}(?:\.\d{2})?)\s*/?\s*(?:hr|hour|per\s*hour)", re.IGNORECASE)


def extract_entities(text):
    """Extract intelligence from note text."""
    if not text:
        return {}

    primes = list(set(PRIME_PAT.findall(text)))
    programs = list(set(PROGRAM_PAT.findall(text)))
    hiring = 1 if any(p.search(text) for p in HIRING_PATS) else 0
    traction = 1 if any(p.search(text) for p in TRACTION_PATS) else 0
    positive = 1 if any(p.search(text) for p in POSITIVE_PATS) else 0
    clearances = list(set(CLEARANCE_PAT.findall(text)))
    bill_rates = list(set(BILL_RATE_PAT.findall(text)))

    return {
        "primes": ", ".join(primes) if primes else "",
        "programs": ", ".join(programs) if programs else "",
        "hiring_signal": hiring,
        "traction": traction,
        "positive_response": positive,
        "clearances": ", ".join(clearances) if clearances else "",
        "bill_rates": ", ".join(f"${r}" for r in bill_rates) if bill_rates else "",
    }


def clean_html(text):
    """Strip HTML tags and clean up."""
    if not text:
        return ""
    text = re.sub(r'<br\s*/?>', ' ', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'[^\x20-\x7E\n]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def parse_date(d):
    """Convert date string to YYYY-MM-DD."""
    if not d:
        return None
    d = str(d).strip()
    # Try common formats
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y", "%m/%d/%Y %H:%M:%S"):
        try:
            return __import__('datetime').datetime.strptime(d, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def main():
    print("=" * 80)
    print("BACKFILL INTELLIGENCE EXTRACTION")
    print(f"Source: {BULLHORN_DB}")
    print(f"Target: {MASTER_DB}")
    print("=" * 80)

    # Connect to both databases
    bh_conn = sqlite3.connect(str(BULLHORN_DB))
    bh_conn.row_factory = sqlite3.Row
    bh_c = bh_conn.cursor()

    master_conn = sqlite3.connect(str(MASTER_DB))
    master_c = master_conn.cursor()

    # Count records to process
    bh_c.execute("SELECT COUNT(*) FROM call_notes")
    total = bh_c.fetchone()[0]
    print(f"\nTotal call_notes to process: {total:,}")

    # Verify master records exist
    master_c.execute("SELECT COUNT(*) FROM activities WHERE source_file = 'bullhorn_master.db'")
    master_count = master_c.fetchone()[0]
    print(f"Master DB records to update: {master_count:,}")

    # Stats tracking
    stats = {
        "processed": 0,
        "updated": 0,
        "skipped": 0,
        "hiring_signals": 0,
        "traction": 0,
        "positive": 0,
        "primes_found": 0,
        "programs_found": 0,
        "with_text": 0,
    }

    start = time.time()

    # Process in batches
    offset = 0
    while offset < total:
        bh_c.execute("""
            SELECT id, note_body, note_author, date_added, about, action,
                   department, note_type, status
            FROM call_notes
            ORDER BY id
            LIMIT ? OFFSET ?
        """, (BATCH_SIZE, offset))
        rows = bh_c.fetchall()

        if not rows:
            break

        updates = []
        for r in rows:
            note_id = r["id"]
            raw_text = r["note_body"] or ""
            clean_text = clean_html(raw_text)
            author = r["note_author"] or ""
            date_str = parse_date(r["date_added"])
            about = r["about"] or ""

            if clean_text:
                stats["with_text"] += 1
                intel = extract_entities(clean_text)
            else:
                intel = {
                    "primes": "", "programs": "", "hiring_signal": 0,
                    "traction": 0, "positive_response": 0,
                    "clearances": "", "bill_rates": "",
                }

            if intel["hiring_signal"]:
                stats["hiring_signals"] += 1
            if intel["traction"]:
                stats["traction"] += 1
            if intel["positive_response"]:
                stats["positive"] += 1
            if intel["primes"]:
                stats["primes_found"] += 1
            if intel["programs"]:
                stats["programs_found"] += 1

            updates.append((
                clean_text[:2000] if clean_text else None,  # note_text (cap at 2000)
                author,
                date_str,
                intel["hiring_signal"],
                intel["traction"],
                intel["positive_response"],
                intel["primes"],
                intel["programs"],
                intel.get("clearances", ""),  # store in locations field (reuse)
                str(note_id),  # bullhorn_activity_id match
            ))

        # Batch UPDATE
        master_c.executemany("""
            UPDATE activities SET
                note_text = ?,
                actor = ?,
                activity_date = ?,
                hiring_signal = ?,
                traction = ?,
                positive_response = ?,
                primes_mentioned = ?,
                programs_mentioned = ?,
                locations = ?
            WHERE bullhorn_activity_id = ?
            AND source_file = 'bullhorn_master.db'
        """, updates)

        stats["processed"] += len(rows)
        stats["updated"] += master_c.rowcount if hasattr(master_c, 'rowcount') else len(rows)

        offset += BATCH_SIZE
        elapsed = time.time() - start
        rate = stats["processed"] / elapsed if elapsed > 0 else 0
        pct = (stats["processed"] / total) * 100

        if offset % 10000 == 0 or offset >= total:
            print(f"  {stats['processed']:>6,}/{total:,} ({pct:.0f}%) | "
                  f"{rate:.0f} rows/sec | "
                  f"hiring={stats['hiring_signals']} traction={stats['traction']} "
                  f"positive={stats['positive']} | "
                  f"primes={stats['primes_found']} programs={stats['programs_found']}")

    # Commit
    master_conn.commit()
    elapsed = time.time() - start

    print(f"\n{'=' * 80}")
    print(f"BACKFILL COMPLETE in {elapsed:.1f}s")
    print(f"{'=' * 80}")
    print(f"\n  Records processed:  {stats['processed']:,}")
    print(f"  With note text:     {stats['with_text']:,}")
    print(f"  Hiring signals:     {stats['hiring_signals']:,}")
    print(f"  Traction notes:     {stats['traction']:,}")
    print(f"  Positive responses: {stats['positive']:,}")
    print(f"  Primes extracted:   {stats['primes_found']:,}")
    print(f"  Programs extracted: {stats['programs_found']:,}")

    # Verify
    print("\n--- Verification ---")
    master_c.execute("SELECT COUNT(*) FROM activities WHERE note_text IS NOT NULL AND note_text != ''")
    print(f"  Records with note_text: {master_c.fetchone()[0]:,}")
    master_c.execute("SELECT COUNT(*) FROM activities WHERE actor IS NOT NULL AND actor != ''")
    print(f"  Records with actor: {master_c.fetchone()[0]:,}")
    master_c.execute("SELECT COUNT(*) FROM activities WHERE activity_date IS NOT NULL")
    print(f"  Records with activity_date: {master_c.fetchone()[0]:,}")
    master_c.execute("SELECT COUNT(*) FROM activities WHERE hiring_signal = 1")
    print(f"  Total hiring signals: {master_c.fetchone()[0]:,}")
    master_c.execute("SELECT COUNT(*) FROM activities WHERE traction = 1")
    print(f"  Total traction: {master_c.fetchone()[0]:,}")
    master_c.execute("SELECT COUNT(*) FROM activities WHERE positive_response = 1")
    print(f"  Total positive: {master_c.fetchone()[0]:,}")
    master_c.execute("SELECT COUNT(*) FROM activities WHERE primes_mentioned IS NOT NULL AND primes_mentioned != ''")
    print(f"  Total with primes: {master_c.fetchone()[0]:,}")
    master_c.execute("SELECT COUNT(*) FROM activities WHERE programs_mentioned IS NOT NULL AND programs_mentioned != ''")
    print(f"  Total with programs: {master_c.fetchone()[0]:,}")

    # Top primes
    master_c.execute("""
        SELECT primes_mentioned, COUNT(*) as cnt
        FROM activities
        WHERE primes_mentioned IS NOT NULL AND primes_mentioned != ''
        GROUP BY primes_mentioned
        ORDER BY cnt DESC
        LIMIT 15
    """)
    print("\n  Top primes mentioned:")
    for r in master_c.fetchall():
        print(f"    {r[0][:40]:40s} | {r[1]:,}")

    # Top programs
    master_c.execute("""
        SELECT programs_mentioned, COUNT(*) as cnt
        FROM activities
        WHERE programs_mentioned IS NOT NULL AND programs_mentioned != ''
        GROUP BY programs_mentioned
        ORDER BY cnt DESC
        LIMIT 15
    """)
    print("\n  Top programs mentioned:")
    for r in master_c.fetchall():
        print(f"    {r[0][:40]:40s} | {r[1]:,}")

    # Date range
    master_c.execute("SELECT MIN(activity_date), MAX(activity_date) FROM activities WHERE activity_date IS NOT NULL")
    dates = master_c.fetchone()
    print(f"\n  Date range: {dates[0]} to {dates[1]}")

    # Recruiter leaderboard
    master_c.execute("""
        SELECT actor, COUNT(*) as notes,
               COUNT(CASE WHEN hiring_signal = 1 THEN 1 END) as hiring,
               COUNT(CASE WHEN traction = 1 THEN 1 END) as traction,
               COUNT(DISTINCT about) as contacts
        FROM activities
        WHERE actor IS NOT NULL AND actor != ''
        GROUP BY actor
        ORDER BY notes DESC
        LIMIT 15
    """)
    print("\n  Recruiter leaderboard (all time):")
    print(f"  {'Recruiter':25s} | {'Notes':>6s} | {'Hiring':>6s} | {'Traction':>8s} | {'Contacts':>8s}")
    print(f"  {'-'*25}-+-{'-'*6}-+-{'-'*6}-+-{'-'*8}-+-{'-'*8}")
    for r in master_c.fetchall():
        print(f"  {r[0][:25]:25s} | {r[1]:6,} | {r[2]:6,} | {r[3]:8,} | {r[4]:8,}")

    bh_conn.close()
    master_conn.close()


if __name__ == "__main__":
    main()
