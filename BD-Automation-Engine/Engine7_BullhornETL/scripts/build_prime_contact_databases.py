#!/usr/bin/env python3
"""
Bullhorn Export Parser - Build Per-Prime Contact Databases

This script parses all Bullhorn XLS exports and creates dedicated contact
databases for each prime contractor with aggregated notes history.

Data Sources:
- Notes Activity Reports: Contact names, call notes, prime/program mentions
- Client Visits: Contact names, salespeople, dates
- Placement Reports: Confirmed hiring manager contacts with companies

Output:
- Per-prime CSV files in Engine3_OrgChart/data/
- Master aggregated contacts JSON
- Prime coverage analysis report
"""

import pandas as pd
import os
import re
import json
from collections import defaultdict
from datetime import datetime
from typing import Dict, List
import warnings

warnings.filterwarnings("ignore")

# Configuration
BULLHORN_DIR = "docs/Bullhorn Exports"
OUTPUT_DIR = "Engine3_OrgChart/data/Prime_Contacts"
REPORTS_DIR = "Engine7_BullhornETL/outputs"

# Prime contractor patterns (case-insensitive matching)
PRIME_PATTERNS = {
    "CACI": [r"\bCACI\b"],
    "GDIT": [
        r"\bGDIT\b",
        r"\bGeneral Dynamics IT\b",
        r"\bGeneral Dynamics Information Technology\b",
    ],
    "Leidos": [r"\bLeidos\b"],
    "Lockheed Martin": [
        r"\bLockheed\b",
        r"\bLMCO\b",
        r"\bLockheed Martin\b",
        r"\bLM\s",
    ],
    "SAIC": [r"\bSAIC\b"],
    "Northrop Grumman": [r"\bNorthrop\b", r"\bNGC\b", r"\bNorthrop Grumman\b"],
    "Raytheon": [r"\bRaytheon\b", r"\bRTX\b", r"\bRaytheon Intelligence\b"],
    "BAE Systems": [r"\bBAE\b", r"\bBAE Systems\b"],
    "Peraton": [r"\bPeraton\b"],
    "Booz Allen Hamilton": [r"\bBooz Allen\b", r"\bBAH\b", r"\bBooz Allen Hamilton\b"],
    "ManTech": [r"\bManTech\b"],
    "L3Harris": [r"\bL3Harris\b", r"\bL3 Harris\b", r"\bHarris\b"],
    "Palantir": [r"\bPalantir\b"],
    "Anduril": [r"\bAnduril\b"],
    "Parsons": [r"\bParsons\b"],
    "Jacobs": [r"\bJacobs\b"],
    "KBR": [r"\bKBR\b"],
    "Deloitte": [r"\bDeloitte\b"],
    "Accenture": [r"\bAccenture\b", r"\bAccenture Federal\b"],
    "AWS": [r"\bAWS\b", r"\bAmazon Web Services\b"],
    "Microsoft": [r"\bMicrosoft\b"],
    "Boeing": [r"\bBoeing\b"],
    "General Dynamics": [r"\bGeneral Dynamics\b", r"\bGD\b"],
    "Sierra Nevada": [r"\bSierra Nevada\b", r"\bSNC\b"],
    "Amentum": [r"\bAmentum\b"],
}

# Program patterns for additional context
PROGRAM_PATTERNS = {
    "DCGS": r"\bDCGS\b",
    "NGEN": r"\bNGEN\b",
    "GSM-O": r"\bGSM-?O\b",
    "DISA": r"\bDISA\b",
    "NSA": r"\bNSA\b",
    "CYBERCOM": r"\bCYBERCOM\b",
    "CENTCOM": r"\bCENTCOM\b",
    "SOCOM": r"\bSOCOM\b",
    "DIA": r"\bDIA\b",
    "NRO": r"\bNRO\b",
    "NGA": r"\bNGA\b",
}

# Clearance patterns
CLEARANCE_PATTERNS = {
    "TS/SCI Poly": r"TS/SCI.*Poly|Poly.*TS/SCI|Full.?Scope.?Poly|FSP",
    "TS/SCI": r"TS/SCI(?!.*Poly)",
    "Top Secret": r"Top.?Secret|TS(?!/SCI)",
    "Secret": r"\bSecret\b(?!.*Top)",
}


class BullhornParser:
    """Parse Bullhorn exports and build prime contact databases."""

    def __init__(self, bullhorn_dir: str, output_dir: str):
        self.bullhorn_dir = bullhorn_dir
        self.output_dir = output_dir
        self.contacts = defaultdict(
            lambda: {
                "name": "",
                "primes": set(),
                "programs": set(),
                "clearances": set(),
                "notes": [],
                "statuses": set(),
                "dates": [],
                "authors": set(),
                "locations": set(),
            }
        )
        self.placements = []
        self.client_visits = []

    def parse_all_files(self):
        """Parse all Bullhorn XLS files."""
        print("=" * 70)
        print("BULLHORN EXPORT PARSER")
        print("=" * 70)

        xls_files = [f for f in os.listdir(self.bullhorn_dir) if f.endswith(".XLS")]
        print(f"\nFound {len(xls_files)} XLS files to process")

        notes_files = []
        visits_files = []
        placement_files = []

        # Categorize files
        for filename in xls_files:
            filepath = os.path.join(self.bullhorn_dir, filename)
            try:
                df = pd.read_excel(filepath, nrows=5)
                if len(df) > 1:
                    row1_str = str(df.iloc[1].tolist())
                    if "Note Author" in row1_str and "Note Body" in row1_str:
                        notes_files.append(filepath)
                    elif "Contact Name" in row1_str and "Salesperson" in row1_str:
                        visits_files.append(filepath)
                    elif "Company" in row1_str and ":PLACEMENT:" in row1_str:
                        placement_files.append(filepath)
                    elif "Placement" in filename:
                        placement_files.append(filepath)
            except Exception as e:
                print(f"  Error categorizing {filename}: {e}")

        print(f"\n  Notes Activity files: {len(notes_files)}")
        print(f"  Client Visits files: {len(visits_files)}")
        print(f"  Placement files: {len(placement_files)}")

        # Parse each category
        print("\n" + "-" * 50)
        print("Parsing Notes Activity files...")
        for filepath in notes_files:
            self._parse_notes_file(filepath)

        print("\n" + "-" * 50)
        print("Parsing Client Visits files...")
        for filepath in visits_files:
            self._parse_visits_file(filepath)

        print("\n" + "-" * 50)
        print("Parsing Placement files...")
        for filepath in placement_files:
            self._parse_placement_file(filepath)

    def _parse_notes_file(self, filepath: str):
        """Parse a Notes Activity XLS file."""
        filename = os.path.basename(filepath)
        try:
            df = pd.read_excel(filepath)
            # Fix headers - row 1 contains actual headers
            if len(df) > 1:
                df.columns = df.iloc[1].tolist()
                df = df.iloc[2:].reset_index(drop=True)

            rows_processed = 0
            for _, row in df.iterrows():
                if pd.isna(row.get("About")) or pd.isna(row.get("Note Body")):
                    continue

                contact_name = str(row["About"]).strip()
                note_body = str(row["Note Body"])
                note_date = row.get("Date Note Added", "")
                note_author = row.get("Note Author", "")
                status = row.get("Status", "")

                # Update contact record
                contact = self.contacts[contact_name.lower()]
                contact["name"] = contact_name

                # Extract primes from note body
                for prime, patterns in PRIME_PATTERNS.items():
                    for pattern in patterns:
                        if re.search(pattern, note_body, re.IGNORECASE):
                            contact["primes"].add(prime)
                            break

                # Extract programs
                for program, pattern in PROGRAM_PATTERNS.items():
                    if re.search(pattern, note_body, re.IGNORECASE):
                        contact["programs"].add(program)

                # Extract clearances
                for clearance, pattern in CLEARANCE_PATTERNS.items():
                    if re.search(pattern, note_body, re.IGNORECASE):
                        contact["clearances"].add(clearance)

                # Add note
                contact["notes"].append(
                    {
                        "date": str(note_date),
                        "author": str(note_author),
                        "body": note_body[:1000],  # Truncate long notes
                    }
                )

                if pd.notna(status):
                    contact["statuses"].add(str(status))
                if pd.notna(note_date):
                    contact["dates"].append(str(note_date))
                if pd.notna(note_author):
                    contact["authors"].add(str(note_author))

                rows_processed += 1

            print(f"  {filename}: {rows_processed} notes processed")

        except Exception as e:
            print(f"  Error parsing {filename}: {e}")

    def _parse_visits_file(self, filepath: str):
        """Parse a Client Visits XLS file."""
        filename = os.path.basename(filepath)
        try:
            df = pd.read_excel(filepath)
            # Fix headers
            if len(df) > 1:
                df.columns = df.iloc[1].tolist()
                df = df.iloc[2:].reset_index(drop=True)

            rows_processed = 0
            for _, row in df.iterrows():
                contact_name = row.get("Contact Name")
                if pd.isna(contact_name):
                    continue

                contact_name = str(contact_name).strip()
                salesperson = row.get("Salesperson", "")
                date_added = row.get("Date Added", "")
                status = row.get("Status", "")

                # Update contact record
                contact = self.contacts[contact_name.lower()]
                contact["name"] = contact_name

                if pd.notna(status):
                    contact["statuses"].add(str(status))
                if pd.notna(date_added):
                    contact["dates"].append(str(date_added))
                if pd.notna(salesperson):
                    contact["authors"].add(str(salesperson))

                self.client_visits.append(
                    {
                        "contact": contact_name,
                        "salesperson": salesperson,
                        "date": date_added,
                        "status": status,
                    }
                )

                rows_processed += 1

            print(f"  {filename}: {rows_processed} visits processed")

        except Exception as e:
            print(f"  Error parsing {filename}: {e}")

    def _parse_placement_file(self, filepath: str):
        """Parse a Placement Activity XLS file."""
        filename = os.path.basename(filepath)
        try:
            df = pd.read_excel(filepath)
            # Fix headers
            if len(df) > 0:
                df.columns = df.iloc[0].tolist()
                df = df.iloc[1:].reset_index(drop=True)

            # Find company and contact columns
            company_col = None
            contact_col = None
            title_col = None

            for col in df.columns:
                col_str = str(col)
                if "Company" in col_str:
                    company_col = col
                if "Contact" in col_str and contact_col is None:
                    contact_col = col
                if "Title" in col_str:
                    title_col = col

            if not company_col or not contact_col:
                print(f"  {filename}: Could not find Company/Contact columns")
                return

            rows_processed = 0
            for _, row in df.iterrows():
                company = row.get(company_col)
                contact = row.get(contact_col)

                if pd.isna(company) or pd.isna(contact):
                    continue

                company = str(company).strip()
                contact_name = str(contact).strip()
                job_title = str(row.get(title_col, "")) if title_col else ""

                # Update contact record with confirmed company
                contact_key = contact_name.lower()
                self.contacts[contact_key]["name"] = contact_name

                # Map company to prime
                for prime, patterns in PRIME_PATTERNS.items():
                    for pattern in patterns:
                        if re.search(pattern, company, re.IGNORECASE):
                            self.contacts[contact_key]["primes"].add(prime)
                            break

                self.placements.append(
                    {
                        "contact": contact_name,
                        "company": company,
                        "job_title": job_title,
                    }
                )

                rows_processed += 1

            print(f"  {filename}: {rows_processed} placements processed")

        except Exception as e:
            print(f"  Error parsing {filename}: {e}")

    def build_prime_databases(self):
        """Build per-prime contact databases."""
        print("\n" + "=" * 70)
        print("BUILDING PRIME CONTACT DATABASES")
        print("=" * 70)

        os.makedirs(self.output_dir, exist_ok=True)

        prime_contacts = defaultdict(list)

        # Organize contacts by prime
        for contact_key, contact_data in self.contacts.items():
            if not contact_data["primes"]:
                continue

            for prime in contact_data["primes"]:
                prime_contacts[prime].append(contact_data)

        # Create CSV for each prime
        summary = []
        for prime, contacts in sorted(prime_contacts.items(), key=lambda x: -len(x[1])):
            # Build DataFrame
            rows = []
            for c in contacts:
                # Get most recent note
                recent_note = ""
                if c["notes"]:
                    sorted_notes = sorted(
                        c["notes"], key=lambda x: x["date"], reverse=True
                    )
                    recent_note = sorted_notes[0]["body"][:500]

                rows.append(
                    {
                        "Name": c["name"],
                        "Primes": ", ".join(sorted(c["primes"])),
                        "Programs": ", ".join(sorted(c["programs"])),
                        "Clearances": ", ".join(sorted(c["clearances"])),
                        "Status": ", ".join(sorted(c["statuses"]))
                        if c["statuses"]
                        else "",
                        "Note Count": len(c["notes"]),
                        "Last Activity": max(c["dates"]) if c["dates"] else "",
                        "Authors": ", ".join(sorted(c["authors"])),
                        "Recent Note": recent_note,
                    }
                )

            df = pd.DataFrame(rows)
            df = df.sort_values("Note Count", ascending=False)

            # Save CSV
            safe_name = prime.replace(" ", "_").replace("/", "_")
            csv_path = os.path.join(self.output_dir, f"{safe_name}_Contacts.csv")
            df.to_csv(csv_path, index=False)

            print(f"\n  {prime}: {len(contacts)} contacts")
            print(f"    Saved to: {csv_path}")

            summary.append(
                {
                    "prime": prime,
                    "contact_count": len(contacts),
                    "with_programs": len([c for c in contacts if c["programs"]]),
                    "with_clearances": len([c for c in contacts if c["clearances"]]),
                    "total_notes": sum(len(c["notes"]) for c in contacts),
                    "file": csv_path,
                }
            )

        return summary

    def build_master_database(self):
        """Build master aggregated contacts database."""
        print("\n" + "-" * 50)
        print("Building master contacts database...")

        master_contacts = []
        for contact_key, contact_data in self.contacts.items():
            if not contact_data["name"]:
                continue

            master_contacts.append(
                {
                    "name": contact_data["name"],
                    "primes": list(contact_data["primes"]),
                    "programs": list(contact_data["programs"]),
                    "clearances": list(contact_data["clearances"]),
                    "statuses": list(contact_data["statuses"]),
                    "note_count": len(contact_data["notes"]),
                    "last_activity": max(contact_data["dates"])
                    if contact_data["dates"]
                    else None,
                    "authors": list(contact_data["authors"]),
                }
            )

        # Save master JSON
        master_path = os.path.join(self.output_dir, "Master_All_Contacts.json")
        with open(master_path, "w") as f:
            json.dump(master_contacts, f, indent=2, default=str)

        print(f"  Total unique contacts: {len(master_contacts)}")
        print(f"  Saved to: {master_path}")

        return master_contacts

    def generate_report(self, summary: List[Dict]):
        """Generate prime coverage analysis report."""
        print("\n" + "=" * 70)
        print("PRIME COVERAGE ANALYSIS REPORT")
        print("=" * 70)

        report_path = os.path.join(REPORTS_DIR, "prime_contact_coverage_report.md")

        with open(report_path, "w") as f:
            f.write("# Prime Contact Coverage Analysis Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")

            f.write("## Summary\n\n")
            f.write(
                f"| Prime | Contacts | With Programs | With Clearances | Total Notes |\n"
            )
            f.write(
                f"|-------|----------|---------------|-----------------|-------------|\n"
            )

            for s in sorted(summary, key=lambda x: -x["contact_count"]):
                f.write(
                    f"| {s['prime']} | {s['contact_count']} | {s['with_programs']} | {s['with_clearances']} | {s['total_notes']} |\n"
                )

            f.write("\n## Files Generated\n\n")
            for s in summary:
                f.write(f"- `{s['file']}`\n")

            f.write("\n## Recommendations\n\n")
            f.write("### High Priority (Many contacts, need organization):\n")
            for s in summary:
                if s["contact_count"] >= 100:
                    f.write(
                        f"- **{s['prime']}**: {s['contact_count']} contacts - Review and deduplicate\n"
                    )

            f.write("\n### Medium Priority (Good coverage):\n")
            for s in summary:
                if 20 <= s["contact_count"] < 100:
                    f.write(f"- **{s['prime']}**: {s['contact_count']} contacts\n")

            f.write("\n### Low Coverage (Need ZoomInfo research):\n")
            for s in summary:
                if s["contact_count"] < 20:
                    f.write(
                        f"- **{s['prime']}**: Only {s['contact_count']} contacts - NEEDS ZOOMINFO\n"
                    )

        print(f"\n  Report saved to: {report_path}")

        # Print summary to console
        print("\n" + "-" * 50)
        print("PRIME CONTACT COUNTS:")
        print("-" * 50)
        for s in sorted(summary, key=lambda x: -x["contact_count"]):
            bar = "█" * min(50, s["contact_count"] // 10)
            print(f"  {s['prime']:25} {s['contact_count']:5} {bar}")


def main():
    """Main entry point."""
    parser = BullhornParser(BULLHORN_DIR, OUTPUT_DIR)

    # Parse all files
    parser.parse_all_files()

    # Build databases
    summary = parser.build_prime_databases()
    parser.build_master_database()

    # Generate report
    parser.generate_report(summary)

    print("\n" + "=" * 70)
    print("COMPLETE!")
    print("=" * 70)
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print(f"Report: {REPORTS_DIR}/prime_contact_coverage_report.md")


if __name__ == "__main__":
    main()
