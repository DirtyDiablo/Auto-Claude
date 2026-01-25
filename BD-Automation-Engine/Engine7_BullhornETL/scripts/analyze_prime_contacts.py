#!/usr/bin/env python3
"""
Prime Contact Database Analyzer

Analyzes each prime's contact database to identify:
- Coverage by location
- Coverage by program
- Key contact titles (PMs, Staffing, Contracts)
- Gaps needing ZoomInfo research
"""

import pandas as pd
import os
import re
import json
from collections import defaultdict
from datetime import datetime

# Directories
PRIME_CONTACTS_DIR = "Engine3_OrgChart/data/Prime_Contacts"
LOCKHEED_EXTRA_DB = "Engine3_OrgChart/data/Lockheed Contact.csv"
OUTPUT_DIR = "Engine7_BullhornETL/outputs"

# Key locations by prime
PRIME_LOCATIONS = {
    'CACI': ['Arlington', 'Chantilly', 'Fort Belvoir', 'Colorado Springs', 'San Diego', 'Huntsville', 'Springfield'],
    'GDIT': ['Falls Church', 'Herndon', 'San Diego', 'San Antonio', 'Colorado Springs', 'Fort Meade', 'Hampton'],
    'Leidos': ['Reston', 'Frederick', 'San Diego', 'Huntsville', 'Columbia', 'Fort Meade'],
    'Lockheed Martin': ['Fort Worth', 'Orlando', 'Huntsville', 'Moorestown', 'Denver', 'San Diego', 'Fort Meade', 'Chandler'],
    'Northrop Grumman': ['Falls Church', 'Redondo Beach', 'San Diego', 'Huntsville', 'Aurora', 'Chandler', 'Roy'],
    'SAIC': ['Reston', 'San Diego', 'Huntsville', 'Colorado Springs', 'San Antonio'],
    'Raytheon': ['Tucson', 'Aurora', 'El Segundo', 'Andover', 'McKinney'],
    'Peraton': ['Herndon', 'Chantilly', 'Fort Meade', 'Tampa', 'Colorado Springs'],
    'Boeing': ['Huntsville', 'St. Louis', 'Seattle', 'Colorado Springs', 'El Segundo'],
    'BAE Systems': ['Falls Church', 'Nashua', 'San Diego', 'Austin', 'Huntsville'],
    'Booz Allen Hamilton': ['McLean', 'San Diego', 'Huntsville', 'Tampa', 'Colorado Springs'],
    'L3Harris': ['Melbourne', 'Colorado Springs', 'Salt Lake City', 'Rochester', 'San Diego'],
    'ManTech': ['Herndon', 'Fort Meade', 'San Antonio', 'Tampa'],
    'Palantir': ['Denver', 'Palo Alto', 'Washington DC', 'New York'],
}

# Key programs by prime
PRIME_PROGRAMS = {
    'CACI': ['BICES', 'DIA', 'Army ITES', 'NSA', 'NGEN'],
    'GDIT': ['DCGS', 'NGEN', 'GSM-O', 'DISA', 'Army'],
    'Leidos': ['DIA ISEO', 'Defense Enclave', 'GSM-O', 'NGEN', 'NASA'],
    'Lockheed Martin': ['F-35', 'Aegis', 'NGI', 'GPS', 'THAAD', 'PAC-3', 'NSA', 'CPS'],
    'Northrop Grumman': ['GBSD', 'IBCS', 'B-21', 'NGI', 'OPIR', 'E-2D'],
    'SAIC': ['Cloud One', 'ABMS', 'Army AESD', 'Navy', 'Air Force'],
    'Raytheon': ['GPS OCX', 'AMRAAM', 'Patriot', 'SM-3', 'Tomahawk'],
    'Peraton': ['ARCYBER', 'SITEC', 'NASA', 'FAA'],
    'Boeing': ['GMD', 'KC-46', 'MQ-25', 'SLS', 'CST-100'],
    'BAE Systems': ['Bradley', 'AMPV', 'Ship Repair', 'EW'],
    'Booz Allen Hamilton': ['Army', 'Navy', 'DHS', 'VA', 'HHS'],
    'L3Harris': ['GPS', 'Satcom', 'Tactical Radio', 'ISR'],
    'ManTech': ['SCITES', 'SOUTHCOM', 'Cyber'],
    'Palantir': ['Army', 'SOCOM', 'IC', 'Gotham', 'Foundry'],
}

# Title patterns for key roles
KEY_TITLE_PATTERNS = {
    'Program Manager': r'program\s*manager|pm\b|deputy\s*pm|deputy\s*program',
    'Staffing/TA': r'staffing|talent\s*acquisition|recruiting|recruiter|hr\s*manager|hr\s*business\s*partner',
    'Contracts': r'contracts?\s*manager|subcontracts|contracts?\s*admin',
    'Site Lead': r'site\s*lead|site\s*manager|operations\s*manager',
    'Director': r'\bdirector\b|vp\b|vice\s*president',
    'Engineering Lead': r'engineering\s*manager|chief\s*engineer|technical\s*lead',
}


def analyze_prime(prime_name: str, df: pd.DataFrame) -> dict:
    """Analyze a single prime's contact database."""

    analysis = {
        'prime': prime_name,
        'total_contacts': len(df),
        'with_programs': 0,
        'with_clearances': 0,
        'locations': defaultdict(int),
        'programs': defaultdict(int),
        'clearances': defaultdict(int),
        'key_titles': defaultdict(list),
        'top_contacts': [],
        'recent_activity': [],
        'gaps': [],
    }

    # Get expected locations and programs for this prime
    expected_locations = PRIME_LOCATIONS.get(prime_name, [])
    expected_programs = PRIME_PROGRAMS.get(prime_name, [])

    for _, row in df.iterrows():
        name = row.get('Name', '')
        programs = str(row.get('Programs', ''))
        clearances = str(row.get('Clearances', ''))
        note_count = row.get('Note Count', 0)
        recent_note = str(row.get('Recent Note', ''))
        last_activity = str(row.get('Last Activity', ''))

        # Count programs
        if programs and programs != 'nan':
            analysis['with_programs'] += 1
            for prog in programs.split(','):
                prog = prog.strip()
                if prog:
                    analysis['programs'][prog] += 1

        # Count clearances
        if clearances and clearances != 'nan':
            analysis['with_clearances'] += 1
            for clr in clearances.split(','):
                clr = clr.strip()
                if clr:
                    analysis['clearances'][clr] += 1

        # Extract locations from notes
        for loc in expected_locations:
            if loc.lower() in recent_note.lower():
                analysis['locations'][loc] += 1

        # Identify key titles from notes
        note_lower = recent_note.lower()
        for title_type, pattern in KEY_TITLE_PATTERNS.items():
            if re.search(pattern, note_lower, re.IGNORECASE):
                analysis['key_titles'][title_type].append({
                    'name': name,
                    'note_count': note_count,
                })

        # Track top contacts by note count
        if note_count and int(note_count) > 10:
            analysis['top_contacts'].append({
                'name': name,
                'note_count': int(note_count),
                'programs': programs,
                'clearances': clearances,
            })

        # Track recent activity (2026)
        if '2026' in last_activity:
            analysis['recent_activity'].append({
                'name': name,
                'last_activity': last_activity,
                'note_count': note_count,
            })

    # Sort top contacts
    analysis['top_contacts'] = sorted(
        analysis['top_contacts'],
        key=lambda x: x['note_count'],
        reverse=True
    )[:20]

    # Sort recent activity
    analysis['recent_activity'] = sorted(
        analysis['recent_activity'],
        key=lambda x: x['last_activity'],
        reverse=True
    )[:20]

    # Identify gaps
    for loc in expected_locations:
        if analysis['locations'].get(loc, 0) < 5:
            analysis['gaps'].append(f"Location: {loc} ({analysis['locations'].get(loc, 0)} contacts)")

    for prog in expected_programs:
        if analysis['programs'].get(prog, 0) < 3:
            analysis['gaps'].append(f"Program: {prog} ({analysis['programs'].get(prog, 0)} contacts)")

    # Check for key title gaps
    for title_type in ['Program Manager', 'Staffing/TA', 'Contracts']:
        if len(analysis['key_titles'].get(title_type, [])) < 3:
            analysis['gaps'].append(f"Title: {title_type} (only {len(analysis['key_titles'].get(title_type, []))} found)")

    return analysis


def generate_report(analyses: list) -> str:
    """Generate comprehensive markdown report."""

    report = []
    report.append("# Prime Contact Database Analysis Report")
    report.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append(f"\n**Total Primes Analyzed:** {len(analyses)}")

    # Executive Summary
    report.append("\n\n---\n")
    report.append("# EXECUTIVE SUMMARY")
    report.append("\n## Contact Coverage by Prime\n")
    report.append("| Prime | Total Contacts | With Programs | With Clearances | Key Title Contacts | Gaps |")
    report.append("|-------|----------------|---------------|-----------------|-------------------|------|")

    for a in sorted(analyses, key=lambda x: -x['total_contacts']):
        key_titles = sum(len(v) for v in a['key_titles'].values())
        gaps = len(a['gaps'])
        report.append(f"| {a['prime']} | {a['total_contacts']} | {a['with_programs']} | {a['with_clearances']} | {key_titles} | {gaps} |")

    # Detailed analysis for each prime
    for a in sorted(analyses, key=lambda x: -x['total_contacts']):
        report.append(f"\n\n---\n")
        report.append(f"# {a['prime'].upper()}")
        report.append(f"\n**Total Contacts:** {a['total_contacts']}")
        report.append(f"\n**With Program Tags:** {a['with_programs']}")
        report.append(f"\n**With Clearance Tags:** {a['with_clearances']}")

        # Programs
        if a['programs']:
            report.append("\n\n## Programs Mentioned")
            report.append("\n| Program | Contacts |")
            report.append("|---------|----------|")
            for prog, count in sorted(a['programs'].items(), key=lambda x: -x[1])[:15]:
                report.append(f"| {prog} | {count} |")

        # Clearances
        if a['clearances']:
            report.append("\n\n## Clearance Distribution")
            report.append("\n| Clearance | Contacts |")
            report.append("|-----------|----------|")
            for clr, count in sorted(a['clearances'].items(), key=lambda x: -x[1]):
                report.append(f"| {clr} | {count} |")

        # Locations
        if a['locations']:
            report.append("\n\n## Location Coverage")
            report.append("\n| Location | Mentions |")
            report.append("|----------|----------|")
            for loc, count in sorted(a['locations'].items(), key=lambda x: -x[1]):
                report.append(f"| {loc} | {count} |")

        # Key Titles
        report.append("\n\n## Key Title Contacts")
        for title_type, contacts in a['key_titles'].items():
            if contacts:
                report.append(f"\n### {title_type} ({len(contacts)} found)")
                for c in contacts[:5]:
                    report.append(f"- {c['name']} ({c['note_count']} notes)")

        # Top Contacts
        if a['top_contacts']:
            report.append("\n\n## Top Contacts (by note count)")
            report.append("\n| Name | Notes | Programs | Clearances |")
            report.append("|------|-------|----------|------------|")
            for c in a['top_contacts'][:10]:
                report.append(f"| {c['name']} | {c['note_count']} | {c['programs'][:30] if c['programs'] else ''} | {c['clearances'][:30] if c['clearances'] else ''} |")

        # Recent Activity
        if a['recent_activity']:
            report.append("\n\n## Recent Activity (2026)")
            report.append("\n| Name | Last Activity | Notes |")
            report.append("|------|---------------|-------|")
            for c in a['recent_activity'][:10]:
                report.append(f"| {c['name']} | {c['last_activity'][:10] if c['last_activity'] else ''} | {c['note_count']} |")

        # Gaps
        if a['gaps']:
            report.append("\n\n## GAPS - NEEDS ZOOMINFO RESEARCH")
            for gap in a['gaps']:
                report.append(f"- {gap}")
        else:
            report.append("\n\n## Coverage Status: GOOD")
            report.append("\nNo major gaps identified.")

    return '\n'.join(report)


def generate_zoominfo_recommendations(analyses: list) -> str:
    """Generate ZoomInfo search recommendations."""

    report = []
    report.append("# ZoomInfo Research Recommendations by Prime")
    report.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    report.append("\n\n---\n")
    report.append("# PRIORITY SEARCHES\n")

    for a in sorted(analyses, key=lambda x: len(x['gaps']), reverse=True):
        if not a['gaps']:
            continue

        report.append(f"\n## {a['prime']}")
        report.append(f"\n**Current Contacts:** {a['total_contacts']}")
        report.append(f"\n**Gaps Identified:** {len(a['gaps'])}")

        # Location gaps
        loc_gaps = [g for g in a['gaps'] if g.startswith('Location:')]
        if loc_gaps:
            report.append("\n\n### Location Searches Needed")
            report.append("\n| Location | Current | Search Keywords |")
            report.append("|----------|---------|-----------------|")
            for gap in loc_gaps:
                loc = gap.replace('Location: ', '').split(' (')[0]
                current = gap.split('(')[1].replace(' contacts)', '')
                keywords = f'"{a["prime"]}" "{loc}" "program manager" OR "staffing"'
                report.append(f"| {loc} | {current} | {keywords} |")

        # Program gaps
        prog_gaps = [g for g in a['gaps'] if g.startswith('Program:')]
        if prog_gaps:
            report.append("\n\n### Program Searches Needed")
            report.append("\n| Program | Current | Search Keywords |")
            report.append("|---------|---------|-----------------|")
            for gap in prog_gaps:
                prog = gap.replace('Program: ', '').split(' (')[0]
                current = gap.split('(')[1].replace(' contacts)', '')
                keywords = f'"{a["prime"]}" "{prog}" "manager"'
                report.append(f"| {prog} | {current} | {keywords} |")

        # Title gaps
        title_gaps = [g for g in a['gaps'] if g.startswith('Title:')]
        if title_gaps:
            report.append("\n\n### Title Searches Needed")
            for gap in title_gaps:
                title = gap.replace('Title: ', '').split(' (')[0]
                report.append(f"- Search for: \"{a['prime']}\" \"{title}\"")

    # Primes with good coverage
    report.append("\n\n---\n")
    report.append("# PRIMES WITH GOOD COVERAGE (No ZoomInfo needed)\n")
    for a in analyses:
        if not a['gaps']:
            report.append(f"- **{a['prime']}**: {a['total_contacts']} contacts, no gaps")

    return '\n'.join(report)


def main():
    """Main entry point."""
    print("="*70)
    print("PRIME CONTACT DATABASE ANALYZER")
    print("="*70)

    analyses = []

    # Get all prime contact CSVs
    csv_files = [f for f in os.listdir(PRIME_CONTACTS_DIR) if f.endswith('_Contacts.csv') and f != 'Master_All_Contacts.csv']

    print(f"\nAnalyzing {len(csv_files)} prime databases...")

    for csv_file in sorted(csv_files):
        prime_name = csv_file.replace('_Contacts.csv', '').replace('_', ' ')
        filepath = os.path.join(PRIME_CONTACTS_DIR, csv_file)

        try:
            df = pd.read_csv(filepath)
            analysis = analyze_prime(prime_name, df)
            analyses.append(analysis)
            print(f"  {prime_name}: {analysis['total_contacts']} contacts, {len(analysis['gaps'])} gaps")
        except Exception as e:
            print(f"  Error analyzing {prime_name}: {e}")

    # Generate reports
    print("\n" + "-"*50)
    print("Generating reports...")

    # Main analysis report
    report = generate_report(analyses)
    report_path = os.path.join(OUTPUT_DIR, "prime_contact_analysis_report.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"  Analysis report: {report_path}")

    # ZoomInfo recommendations
    zoom_report = generate_zoominfo_recommendations(analyses)
    zoom_path = os.path.join(OUTPUT_DIR, "zoominfo_recommendations_by_prime.md")
    with open(zoom_path, 'w', encoding='utf-8') as f:
        f.write(zoom_report)
    print(f"  ZoomInfo recommendations: {zoom_path}")

    # JSON summary
    summary = []
    for a in analyses:
        summary.append({
            'prime': a['prime'],
            'total_contacts': a['total_contacts'],
            'with_programs': a['with_programs'],
            'with_clearances': a['with_clearances'],
            'programs': dict(a['programs']),
            'clearances': dict(a['clearances']),
            'locations': dict(a['locations']),
            'key_titles': {k: len(v) for k, v in a['key_titles'].items()},
            'gaps': a['gaps'],
            'top_contacts': a['top_contacts'][:5],
        })

    json_path = os.path.join(OUTPUT_DIR, "prime_contact_analysis.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"  JSON summary: {json_path}")

    # Print summary to console
    print("\n" + "="*70)
    print("ANALYSIS SUMMARY")
    print("="*70)
    print(f"\n{'Prime':<25} {'Contacts':>10} {'Programs':>10} {'Clearances':>12} {'Gaps':>6}")
    print("-"*70)
    for a in sorted(analyses, key=lambda x: -x['total_contacts']):
        print(f"{a['prime']:<25} {a['total_contacts']:>10} {a['with_programs']:>10} {a['with_clearances']:>12} {len(a['gaps']):>6}")

    print("\n" + "="*70)
    print("COMPLETE!")
    print("="*70)


if __name__ == "__main__":
    main()
