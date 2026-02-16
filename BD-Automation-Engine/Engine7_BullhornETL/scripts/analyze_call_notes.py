#!/usr/bin/env python3
"""
Bullhorn Call Notes Analyzer

Analyzes Bullhorn export files containing outbound call notes and actions
to extract intelligence about programs, contacts, primes, and gaps.
"""

import xlrd
import re
import json
from collections import defaultdict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# New files to analyze (dated Jan 22)
NEW_FILES = [
    "E78E29A9-B506-C26A-AB0089D0A75A329B.XLS",
    "E78F10F0-E9D0-F16F-4FB20D646B889715.XLS",
    "E79002A3-FEFD-FD63-2642726BB4E74BFA.XLS",
    "E7911AC5-9238-F650-B79C390989A70F66.XLS",
    "E79223ED-F853-73CD-F96610BB266A9B5D.XLS",
    "E7934ECC-A43D-312F-7CD3D30B3FA3BC0E.XLS",
]

# Known program/contract patterns
PROGRAM_PATTERNS = [
    r"\bDCGS[-\s]?[A-Z]?\b",
    r"\bDCGS\b",
    r"\bAFCENT\b",
    r"\bCENTCOM\b",
    r"\bSOCOM\b",
    r"\bAFSOC\b",
    r"\bNSA\b",
    r"\bDIA\b",
    r"\bNGA\b",
    r"\bNRO\b",
    r"\bCIA\b",
    r"\bDOD\b",
    r"\bArmy\s+Intelligence\b",
    r"\bAir\s+Force\s+ISR\b",
    r"\bNavy\s+Intel\b",
    r"\bMarine\s+Corps\b",
    r"\bJIED+O\b",
    r"\bJSOC\b",
    r"\bUSSOCOM\b",
    r"\bCYBERCOM\b",
    r"\bSTRATCOM\b",
    r"\bINDOPACOM\b",
    r"\bEUCOM\b",
    r"\bAFRICOM\b",
    r"\bSCIF\b",
    r"\bTS/SCI\b",
    r"\bTop\s+Secret\b",
    r"\bSecret\b",
    r"\bPoly(?:graph)?\b",
    r"\bFSP\b",
    r"\bCI\s+Poly\b",
    r"\bFull\s+Scope\b",
]

# Prime contractor patterns
PRIME_PATTERNS = [
    r"\bGDIT\b",
    r"\bGeneral\s+Dynamics\b",
    r"\bLeidos\b",
    r"\bBooz\s+Allen\b",
    r"\bBAH\b",
    r"\bNorthrop\b",
    r"\bNorthrop\s+Grumman\b",
    r"\bRaytheon\b",
    r"\bL3Harris\b",
    r"\bL3\s+Harris\b",
    r"\bManTech\b",
    r"\bSAIC\b",
    r"\bPeraton\b",
    r"\bCACI\b",
    r"\bParsons\b",
    r"\bJacobs\b",
    r"\bBAE\b",
    r"\bBAE\s+Systems\b",
    r"\bLockheed\b",
    r"\bLockheed\s+Martin\b",
    r"\bLMCO\b",
    r"\bKBR\b",
    r"\bAccenture\b",
    r"\bDeloitte\b",
    r"\bAmazon\b",
    r"\bAWS\b",
    r"\bMicrosoft\b",
    r"\bPalantir\b",
    r"\bAnduril\b",
    r"\bShield\s+AI\b",
    r"\bSierra\s+Nevada\b",
    r"\bSNC\b",
]

# Location patterns
LOCATION_PATTERNS = [
    r"\bFort\s+\w+\b",
    r"\bCamp\s+\w+\b",
    r"\bJoint\s+Base\s+\w+\b",
    r"\bAFB\b",
    r"\bLangley\b",
    r"\bMeade\b",
    r"\bBelvoir\b",
    r"\bBragg\b",
    r"\bLiberty\b",
    r"\bHuachuca\b",
    r"\bGordon\b",
    r"\bPentagon\b",
    r"\bArlington\b",
    r"\bMcLean\b",
    r"\bReston\b",
    r"\bChantilly\b",
    r"\bHerndon\b",
    r"\bSpringfield\b",
    r"\bTampa\b",
    r"\bMacDill\b",
    r"\bSan\s+Antonio\b",
    r"\bLackland\b",
    r"\bAugusta\b",
    r"\bHawaii\b",
    r"\bGermany\b",
    r"\bKorea\b",
    r"\bJapan\b",
    r"\bQatar\b",
    r"\bKuwait\b",
    r"\bScott\s+AFB\b",
    r"\bWright[-\s]Patterson\b",
    r"\bHunter\s+AAF\b",
    r"\bSavannah\b",
    r"\bColorado\s+Springs\b",
    r"\bPeterson\b",
    r"\bSchriever\b",
]


class CallNotesAnalyzer:
    def __init__(self, exports_dir: str):
        self.exports_dir = Path(exports_dir)
        self.all_records = []
        self.programs_mentioned = defaultdict(list)
        self.primes_mentioned = defaultdict(list)
        self.contacts_extracted = []
        self.locations_mentioned = defaultdict(int)
        self.clearances_mentioned = defaultdict(int)
        self.no_traction_indicators = []
        self.gap_programs = set()
        self.gap_contacts = []
        self.action_types = defaultdict(int)
        self.departments = defaultdict(int)
        self.authors = defaultdict(int)
        self.statuses = defaultdict(int)

    def read_xls_file(self, filepath: str) -> list:
        """Read XLS file and return list of row dictionaries."""
        records = []
        try:
            workbook = xlrd.open_workbook(filepath)
            sheet = workbook.sheet_by_index(0)

            # Find the header row (usually row 2 in Bullhorn exports)
            header_row = 2
            headers = [
                str(sheet.cell_value(header_row, col)).strip()
                for col in range(sheet.ncols)
            ]

            # Read data rows (starting after header)
            for row_idx in range(header_row + 1, sheet.nrows):
                row_data = {}
                for col_idx, header in enumerate(headers):
                    if not header:
                        continue
                    cell = sheet.cell(row_idx, col_idx)
                    value = cell.value

                    # Handle dates
                    if cell.ctype == xlrd.XL_CELL_DATE:
                        try:
                            value = xlrd.xldate_as_datetime(value, workbook.datemode)
                            value = value.strftime("%Y-%m-%d %H:%M:%S")
                        except (ValueError, OverflowError) as e:
                            logger.debug(
                                "xlrd_date_conversion_failed", extra={"error": str(e)}
                            )

                    row_data[header] = value

                # Only add non-empty records
                if any(v for v in row_data.values() if v):
                    records.append(row_data)

            print(f"  Read {len(records)} records from {Path(filepath).name}")
            print(f"  Headers: {headers}")
            return records

        except Exception as e:
            print(f"  Error reading {filepath}: {e}")
            import traceback

            traceback.print_exc()
            return []

    def extract_mentions(self, text: str, patterns: list) -> list:
        """Extract pattern matches from text."""
        if not text or not isinstance(text, str):
            return []

        mentions = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            mentions.extend(matches)
        return list(set(mentions))  # Unique mentions only

    def analyze_note_for_traction(self, note: str) -> dict:
        """Analyze a note for indicators of traction or lack thereof."""
        if not note or not isinstance(note, str):
            return {}

        note_lower = note.lower()

        indicators = {
            "no_answer": any(
                x in note_lower
                for x in [
                    "no answer",
                    "voicemail",
                    "vm",
                    "left message",
                    "lvm",
                    "did not answer",
                    "didn't answer",
                ]
            ),
            "not_interested": any(
                x in note_lower
                for x in [
                    "not interested",
                    "no interest",
                    "declined",
                    "passed",
                    "not looking",
                    "not a fit",
                ]
            ),
            "wrong_contact": any(
                x in note_lower
                for x in [
                    "wrong number",
                    "wrong person",
                    "no longer",
                    "left company",
                    "moved on",
                    "retired",
                ]
            ),
            "no_openings": any(
                x in note_lower
                for x in [
                    "no openings",
                    "no positions",
                    "fully staffed",
                    "no needs",
                    "not hiring",
                    "on hold",
                ]
            ),
            "positive_response": any(
                x in note_lower
                for x in [
                    "interested",
                    "send resume",
                    "send cv",
                    "follow up",
                    "scheduled",
                    "meeting",
                    "call back",
                    "spoke with",
                    "great call",
                    "good conversation",
                ]
            ),
            "contract_mention": any(
                x in note_lower
                for x in ["contract", "program", "project", "task order", "idiq", "bpa"]
            ),
            "clearance_issue": any(
                x in note_lower
                for x in [
                    "clearance",
                    "poly",
                    "ts/sci",
                    "secret",
                    "waiting on clearance",
                    "clearance expired",
                ]
            ),
            "hiring_signal": any(
                x in note_lower
                for x in [
                    "hiring",
                    "looking for",
                    "need",
                    "openings",
                    "positions",
                    "ramp up",
                    "ramping",
                ]
            ),
        }

        return indicators

    def analyze_all_files(self):
        """Analyze all new export files."""
        print("\n" + "=" * 80)
        print("BULLHORN CALL NOTES ANALYSIS")
        print("=" * 80)

        for filename in NEW_FILES:
            filepath = self.exports_dir / filename
            if filepath.exists():
                print(f"\nProcessing: {filename}")
                records = self.read_xls_file(str(filepath))
                self.all_records.extend(records)
            else:
                print(f"  File not found: {filename}")

        print(f"\n\nTotal records loaded: {len(self.all_records)}")

        return self.all_records

    def extract_intelligence(self):
        """Extract intelligence from all records."""
        print("\n" + "=" * 80)
        print("EXTRACTING INTELLIGENCE")
        print("=" * 80)

        for idx, record in enumerate(self.all_records):
            # Get the note body
            note_body = record.get("Note Body", "") or ""
            about = record.get("About", "") or ""
            action = record.get("Note Action", "") or ""
            status = record.get("Status", "") or ""
            department = record.get("Department", "") or ""
            author = record.get("Note Author", "") or ""
            note_type = record.get("Type", "") or ""
            date_added = record.get("Date Note Added", "") or ""

            # Track action types, departments, statuses
            if action:
                self.action_types[action] += 1
            if department:
                self.departments[department] += 1
            if author:
                self.authors[author] += 1
            if status:
                self.statuses[status] += 1

            # Combine all text for analysis
            full_text = f"{note_body} {about}"

            # Extract programs/agencies
            programs = self.extract_mentions(full_text, PROGRAM_PATTERNS)
            for prog in programs:
                self.programs_mentioned[prog.upper()].append(
                    {
                        "record_idx": idx,
                        "about": about,
                        "note": note_body[:300],
                        "action": action,
                        "status": status,
                        "date": date_added,
                        "author": author,
                    }
                )

            # Extract primes
            primes = self.extract_mentions(full_text, PRIME_PATTERNS)
            for prime in primes:
                self.primes_mentioned[prime.upper()].append(
                    {
                        "record_idx": idx,
                        "about": about,
                        "note": note_body[:300],
                        "action": action,
                        "status": status,
                        "date": date_added,
                    }
                )

            # Extract locations
            locations = self.extract_mentions(full_text, LOCATION_PATTERNS)
            for loc in locations:
                self.locations_mentioned[loc] += 1

            # Extract clearances
            clearance_patterns = [
                r"\bTS/SCI\b",
                r"\bTS\b",
                r"\bSecret\b",
                r"\bPoly\b",
                r"\bFSP\b",
                r"\bCI\s+Poly\b",
            ]
            clearances = self.extract_mentions(full_text, clearance_patterns)
            for clr in clearances:
                self.clearances_mentioned[clr.upper()] += 1

            # Analyze traction
            traction = self.analyze_note_for_traction(note_body)

            # Track no-traction cases
            if (
                traction.get("no_answer")
                or traction.get("not_interested")
                or traction.get("no_openings")
            ):
                self.no_traction_indicators.append(
                    {
                        "about": about,
                        "note": note_body[:500],
                        "action": action,
                        "status": status,
                        "date": date_added,
                        "indicators": traction,
                        "programs": programs,
                        "primes": primes,
                    }
                )

            # Extract contact info
            if about and note_type == "Contact":
                contact_info = {
                    "name": about.strip(),
                    "status": status,
                    "last_action": action,
                    "last_note": note_body[:200],
                    "date": date_added,
                    "author": author,
                    "department": department,
                    "traction": traction,
                    "programs_mentioned": programs,
                    "primes_mentioned": primes,
                }
                self.contacts_extracted.append(contact_info)

        # Identify gaps
        self.identify_gaps()

        return self.generate_report()

    def identify_gaps(self):
        """Identify gap programs and contacts that need attention."""
        # Programs mentioned but with mostly negative traction
        program_traction = defaultdict(
            lambda: {"positive": 0, "negative": 0, "total": 0}
        )

        for indicator in self.no_traction_indicators:
            for prog in indicator["programs"]:
                prog_upper = prog.upper()
                if indicator["indicators"].get("positive_response"):
                    program_traction[prog_upper]["positive"] += 1
                else:
                    program_traction[prog_upper]["negative"] += 1
                program_traction[prog_upper]["total"] += 1

        # Identify gap programs (high negative, low positive)
        for prog, stats in program_traction.items():
            if stats["negative"] > stats["positive"] * 2 and stats["negative"] >= 3:
                self.gap_programs.add(prog)

        # Identify gap contacts (no positive response in recent interactions)
        contact_responses = defaultdict(
            lambda: {"positive": 0, "negative": 0, "last_contact": None}
        )
        for contact in self.contacts_extracted:
            name = contact["name"]
            if contact.get("traction", {}).get("positive_response"):
                contact_responses[name]["positive"] += 1
            elif contact.get("traction", {}).get("no_answer") or contact.get(
                "traction", {}
            ).get("not_interested"):
                contact_responses[name]["negative"] += 1
            contact_responses[name]["last_contact"] = contact

        for name, stats in contact_responses.items():
            if stats["negative"] >= 2 and stats["positive"] == 0:
                self.gap_contacts.append(stats["last_contact"])

    def generate_report(self) -> dict:
        """Generate comprehensive analysis report."""
        report = {
            "summary": {
                "total_records": len(self.all_records),
                "total_contacts_extracted": len(self.contacts_extracted),
                "unique_programs_mentioned": len(self.programs_mentioned),
                "unique_primes_mentioned": len(self.primes_mentioned),
                "unique_locations": len(self.locations_mentioned),
                "no_traction_count": len(self.no_traction_indicators),
                "gap_programs_count": len(self.gap_programs),
                "gap_contacts_count": len(self.gap_contacts),
            },
            "action_types": dict(
                sorted(self.action_types.items(), key=lambda x: -x[1])
            ),
            "departments": dict(sorted(self.departments.items(), key=lambda x: -x[1])),
            "top_authors": dict(sorted(self.authors.items(), key=lambda x: -x[1])[:20]),
            "statuses": dict(sorted(self.statuses.items(), key=lambda x: -x[1])),
            "programs_analysis": {},
            "primes_analysis": {},
            "locations": dict(
                sorted(self.locations_mentioned.items(), key=lambda x: -x[1])[:30]
            ),
            "clearances": dict(
                sorted(self.clearances_mentioned.items(), key=lambda x: -x[1])
            ),
            "gap_programs": list(self.gap_programs),
            "no_traction_patterns": {},
        }

        # Program analysis
        for prog, mentions in sorted(
            self.programs_mentioned.items(), key=lambda x: -len(x[1])
        ):
            report["programs_analysis"][prog] = {
                "mention_count": len(mentions),
                "sample_notes": [
                    {"about": m["about"], "note": m["note"][:100], "date": m["date"]}
                    for m in mentions[:5]
                ],
            }

        # Prime analysis
        for prime, mentions in sorted(
            self.primes_mentioned.items(), key=lambda x: -len(x[1])
        ):
            report["primes_analysis"][prime] = {
                "mention_count": len(mentions),
                "sample_notes": [
                    {"about": m["about"], "note": m["note"][:100], "date": m["date"]}
                    for m in mentions[:5]
                ],
            }

        # No traction patterns
        no_answer_count = sum(
            1 for x in self.no_traction_indicators if x["indicators"].get("no_answer")
        )
        not_interested_count = sum(
            1
            for x in self.no_traction_indicators
            if x["indicators"].get("not_interested")
        )
        no_openings_count = sum(
            1 for x in self.no_traction_indicators if x["indicators"].get("no_openings")
        )
        hiring_signals = sum(
            1
            for x in self.no_traction_indicators
            if x["indicators"].get("hiring_signal")
        )

        report["no_traction_patterns"] = {
            "no_answer_voicemail": no_answer_count,
            "not_interested": not_interested_count,
            "no_openings": no_openings_count,
            "hiring_signals_detected": hiring_signals,
        }

        return report


def main():
    exports_dir = Path(__file__).parent.parent.parent / "docs" / "Bullhorn Exports"
    output_dir = Path(__file__).parent.parent / "outputs"
    output_dir.mkdir(exist_ok=True)

    print(f"Exports directory: {exports_dir}")
    print(f"Output directory: {output_dir}")

    analyzer = CallNotesAnalyzer(str(exports_dir))

    # Load and analyze all files
    records = analyzer.analyze_all_files()

    if not records:
        print("No records found. Exiting.")
        return

    # Extract intelligence
    report = analyzer.extract_intelligence()

    # Print summary
    print("\n" + "=" * 80)
    print("ANALYSIS SUMMARY")
    print("=" * 80)

    summary = report["summary"]
    print(f"\nTotal Records Analyzed: {summary['total_records']}")
    print(f"Contacts Extracted: {summary['total_contacts_extracted']}")
    print(f"Unique Programs/Agencies Mentioned: {summary['unique_programs_mentioned']}")
    print(f"Unique Primes Mentioned: {summary['unique_primes_mentioned']}")
    print(f"Unique Locations: {summary['unique_locations']}")
    print(f"No-Traction Cases: {summary['no_traction_count']}")
    print(f"Gap Programs Identified: {summary['gap_programs_count']}")
    print(f"Gap Contacts: {summary['gap_contacts_count']}")

    print("\n--- Action Types ---")
    for action, count in list(report["action_types"].items())[:10]:
        print(f"  {action}: {count}")

    print("\n--- Departments ---")
    for dept, count in list(report["departments"].items())[:10]:
        print(f"  {dept}: {count}")

    print("\n--- Contact Statuses ---")
    for status, count in list(report["statuses"].items())[:10]:
        print(f"  {status}: {count}")

    print("\n--- Top Programs/Agencies Mentioned ---")
    for prog, data in list(report["programs_analysis"].items())[:15]:
        print(f"  {prog}: {data['mention_count']} mentions")

    print("\n--- Top Primes Mentioned ---")
    for prime, data in list(report["primes_analysis"].items())[:15]:
        print(f"  {prime}: {data['mention_count']} mentions")

    print("\n--- Top Locations ---")
    for loc, count in list(report["locations"].items())[:15]:
        print(f"  {loc}: {count} mentions")

    print("\n--- Clearances Mentioned ---")
    for clr, count in report["clearances"].items():
        print(f"  {clr}: {count}")

    print("\n--- No Traction Patterns ---")
    for pattern, count in report["no_traction_patterns"].items():
        print(f"  {pattern}: {count}")

    print("\n--- Gap Programs (Need Attention) ---")
    for prog in report["gap_programs"]:
        print(f"  - {prog}")

    # Save full report
    report_path = output_dir / "call_notes_analysis.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\nFull report saved to: {report_path}")

    # Save contacts for database import
    contacts_path = output_dir / "extracted_contacts.json"
    with open(contacts_path, "w") as f:
        json.dump(analyzer.contacts_extracted, f, indent=2, default=str)
    print(f"Contacts saved to: {contacts_path}")

    # Save gap analysis
    gaps_path = output_dir / "gap_analysis.json"
    gap_data = {
        "gap_programs": list(analyzer.gap_programs),
        "gap_contacts": analyzer.gap_contacts[:100],  # Top 100
        "no_traction_details": analyzer.no_traction_indicators[:200],
    }
    with open(gaps_path, "w") as f:
        json.dump(gap_data, f, indent=2, default=str)
    print(f"Gap analysis saved to: {gaps_path}")

    # Save primes analysis
    primes_path = output_dir / "primes_from_notes.json"
    with open(primes_path, "w") as f:
        json.dump(report["primes_analysis"], f, indent=2, default=str)
    print(f"Primes analysis saved to: {primes_path}")

    # Save all raw records for further processing
    records_path = output_dir / "all_call_notes_records.json"
    with open(records_path, "w") as f:
        json.dump(analyzer.all_records, f, indent=2, default=str)
    print(f"All records saved to: {records_path}")

    return report


if __name__ == "__main__":
    main()
