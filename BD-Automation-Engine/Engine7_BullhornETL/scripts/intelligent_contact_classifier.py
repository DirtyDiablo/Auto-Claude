#!/usr/bin/env python3
"""
Intelligent Contact Classifier

Deep analysis of Bullhorn exports to extract and classify:
- Job titles from notes
- Programs and contracts
- Locations
- Hiring manager status
- Decision maker tier
- Relationship strength
- Pain points and opportunities
- Contact type (client vs candidate)
"""

import pandas as pd
import os
import re
import json
from collections import defaultdict
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Directories
BULLHORN_DIR = "docs/Bullhorn Exports"
OUTPUT_DIR = "Engine3_OrgChart/data/Prime_Contacts_Enriched"
REPORTS_DIR = "Engine7_BullhornETL/outputs"

# ============================================================================
# PATTERN DEFINITIONS
# ============================================================================

# Job title patterns (extracted from notes)
JOB_TITLE_PATTERNS = {
    # Executive Level
    'VP': r'\b(VP|Vice President)\b',
    'Director': r'\b(Director|Dir\.)\b',
    'Chief': r'\b(Chief|CTO|CIO|CISO|CFO)\b',

    # Program Management
    'Program Manager': r'\b(Program Manager|PM|Prog\.?\s*Mgr|Program Mgr)\b',
    'Deputy Program Manager': r'\b(Deputy PM|Deputy Program|DPM)\b',
    'Project Manager': r'\b(Project Manager|Proj\.?\s*Mgr)\b',
    'Capture Manager': r'\b(Capture Manager|Capture Mgr)\b',

    # Staffing/HR
    'Staffing Manager': r'\b(Staffing Manager|Staffing Mgr|Staffing Lead)\b',
    'Talent Acquisition': r'\b(Talent Acquisition|TA Manager|TA Lead|Recruiting Manager)\b',
    'Recruiter': r'\b(Recruiter|Technical Recruiter|Sr\.?\s*Recruiter)\b',
    'HR Manager': r'\b(HR Manager|HR Business Partner|HRBP|Human Resources)\b',

    # Contracts
    'Contracts Manager': r'\b(Contracts Manager|Contracts Mgr|Contract Manager)\b',
    'Subcontracts': r'\b(Subcontracts|Subcontract Manager|Sub-?K)\b',
    'Procurement': r'\b(Procurement|Purchasing Manager)\b',

    # Operations
    'Site Lead': r'\b(Site Lead|Site Manager|Site Mgr)\b',
    'Operations Manager': r'\b(Operations Manager|Ops Manager|Ops Mgr)\b',
    'Task Order Lead': r'\b(Task Order Lead|TO Lead|Task Lead)\b',

    # Engineering
    'Engineering Manager': r'\b(Engineering Manager|Eng\.?\s*Mgr|Engineering Lead)\b',
    'Technical Lead': r'\b(Technical Lead|Tech Lead|Technical Manager)\b',
    'Systems Engineer': r'\b(Systems Engineer|System Engineer|SE\b)\b',
    'Software Engineer': r'\b(Software Engineer|SW Engineer|Developer)\b',

    # Security
    'ISSM': r'\b(ISSM|Information System Security)\b',
    'FSO': r'\b(FSO|Facility Security)\b',
    'Security Manager': r'\b(Security Manager|Security Officer)\b',
}

# Program/Contract patterns
PROGRAM_PATTERNS = {
    # Air Force
    'DCGS': r'\bDCGS\b',
    'ABMS': r'\bABMS\b',
    'Cloud One': r'\bCloud\s*One\b|C1\b',
    'BESPIN': r'\bBESPIN\b',
    'AFNET': r'\bAFNET\b',
    'F-35': r'\bF-?35\b',
    'B-21': r'\bB-?21\b',
    'KC-46': r'\bKC-?46\b',

    # Army
    'ITES': r'\bITES\b',
    'IBCS': r'\bIBCS\b',
    'ARCYBER': r'\bARCYBER\b',
    'Project Convergence': r'\bProject Convergence\b',
    'GBSD': r'\bGBSD\b|Sentinel\b',

    # Navy
    'NGEN': r'\bNGEN\b',
    'CANES': r'\bCANES\b',
    'Aegis': r'\bAegis\b',
    'DCGS-N': r'\bDCGS-?N\b',

    # Joint/Defense
    'GSM-O': r'\bGSM-?O\b',
    'DISA': r'\bDISA\b',
    'DIA': r'\bDIA\b',
    'NSA': r'\bNSA\b',
    'NGA': r'\bNGA\b',
    'NRO': r'\bNRO\b',
    'CYBERCOM': r'\bCYBERCOM\b',
    'CENTCOM': r'\bCENTCOM\b',
    'SOCOM': r'\bSOCOM\b',
    'SOUTHCOM': r'\bSOUTHCOM\b',
    'NORTHCOM': r'\bNORTHCOM\b',

    # Specific Contracts
    'BICES': r'\bBICES\b',
    'SITEC': r'\bSITEC\b',
    'SCITES': r'\bSCITES\b',
    'MCEN': r'\bMCEN\b',
    'Defense Enclave': r'\bDefense Enclave\b|DES\b',
    'DIA ISEO': r'\bISEO\b',

    # Missiles/Space
    'NGI': r'\bNGI\b',
    'GMD': r'\bGMD\b',
    'THAAD': r'\bTHAAD\b',
    'PAC-3': r'\bPAC-?3\b',
    'Patriot': r'\bPatriot\b',
    'OPIR': r'\bOPIR\b',
    'GPS OCX': r'\bGPS\s*OCX\b|OCX\b',
    'CPS': r'\bCPS\b|Conventional Prompt Strike|hypersonic\b',
}

# Location patterns
LOCATION_PATTERNS = {
    # Virginia
    'Arlington, VA': r'\bArlington\b',
    'Chantilly, VA': r'\bChantilly\b',
    'Falls Church, VA': r'\bFalls Church\b',
    'Herndon, VA': r'\bHerndon\b',
    'Reston, VA': r'\bReston\b',
    'McLean, VA': r'\bMcLean\b',
    'Fort Belvoir, VA': r'\bFort Belvoir\b|Ft\.?\s*Belvoir\b',
    'Springfield, VA': r'\bSpringfield\b',
    'Norfolk, VA': r'\bNorfolk\b',
    'Hampton, VA': r'\bHampton\b|Langley\b',

    # Maryland
    'Fort Meade, MD': r'\bFort Meade\b|Ft\.?\s*Meade\b',
    'Columbia, MD': r'\bColumbia,?\s*MD\b',
    'Frederick, MD': r'\bFrederick\b',
    'Annapolis Junction, MD': r'\bAnnapolis Junction\b',

    # Texas
    'San Antonio, TX': r'\bSan Antonio\b',
    'Fort Worth, TX': r'\bFort Worth\b|Ft\.?\s*Worth\b',
    'Dallas, TX': r'\bDallas\b',
    'Austin, TX': r'\bAustin\b',
    'Houston, TX': r'\bHouston\b',

    # California
    'San Diego, CA': r'\bSan Diego\b',
    'El Segundo, CA': r'\bEl Segundo\b',
    'Redondo Beach, CA': r'\bRedondo Beach\b',
    'Los Angeles, CA': r'\bLos Angeles\b|LA\b',

    # Colorado
    'Colorado Springs, CO': r'\bColorado Springs\b|COS\b',
    'Aurora, CO': r'\bAurora,?\s*CO\b',
    'Denver, CO': r'\bDenver\b',

    # Alabama
    'Huntsville, AL': r'\bHuntsville\b',

    # Florida
    'Tampa, FL': r'\bTampa\b',
    'Orlando, FL': r'\bOrlando\b',
    'Melbourne, FL': r'\bMelbourne\b',

    # Arizona
    'Chandler, AZ': r'\bChandler\b',
    'Phoenix, AZ': r'\bPhoenix\b',
    'Tucson, AZ': r'\bTucson\b',

    # Other
    'Omaha, NE': r'\bOmaha\b',
    'St. Louis, MO': r'\bSt\.?\s*Louis\b',
    'Seattle, WA': r'\bSeattle\b',
    'Moorestown, NJ': r'\bMoorestown\b',
    'Cherry Hill, NJ': r'\bCherry Hill\b',
}

# Prime contractor patterns
PRIME_PATTERNS = {
    'CACI': [r'\bCACI\b'],
    'GDIT': [r'\bGDIT\b', r'General Dynamics IT'],
    'Leidos': [r'\bLeidos\b'],
    'Lockheed Martin': [r'\bLockheed\b', r'\bLMCO\b', r'\bLM\s', r'Lockheed Martin'],
    'SAIC': [r'\bSAIC\b'],
    'Northrop Grumman': [r'\bNorthrop\b', r'\bNGC\b', r'Northrop Grumman'],
    'Raytheon': [r'\bRaytheon\b', r'\bRTX\b'],
    'BAE Systems': [r'\bBAE\b'],
    'Peraton': [r'\bPeraton\b'],
    'Booz Allen Hamilton': [r'\bBooz Allen\b', r'\bBAH\b'],
    'ManTech': [r'\bManTech\b'],
    'L3Harris': [r'\bL3Harris\b', r'\bL3 Harris\b', r'\bHarris\b'],
    'Palantir': [r'\bPalantir\b'],
    'Anduril': [r'\bAnduril\b'],
    'Parsons': [r'\bParsons\b'],
    'Jacobs': [r'\bJacobs\b'],
    'KBR': [r'\bKBR\b'],
    'Deloitte': [r'\bDeloitte\b'],
    'Accenture': [r'\bAccenture\b'],
    'AWS': [r'\bAWS\b', r'Amazon Web Services'],
    'Microsoft': [r'\bMicrosoft\b'],
    'Boeing': [r'\bBoeing\b'],
    'General Dynamics': [r'\bGeneral Dynamics\b', r'\bGD\b'],
    'Sierra Nevada': [r'\bSierra Nevada\b', r'\bSNC\b'],
    'Amentum': [r'\bAmentum\b'],
}

# Clearance patterns
CLEARANCE_PATTERNS = {
    'TS/SCI Poly': r'TS/SCI.*Poly|Poly.*TS/SCI|Full.?Scope.?Poly|FSP|CI\s*Poly',
    'TS/SCI': r'TS/SCI(?!.*Poly)',
    'Top Secret': r'Top.?Secret|TS(?!/SCI)',
    'Secret': r'\bSecret\b(?!.*Top)',
    'Public Trust': r'Public Trust',
}

# Hiring signals in notes
HIRING_SIGNALS = [
    r'has?\s*(?:some|several|multiple|new|open|upcoming)\s*(?:positions?|openings?|reqs?|requisitions?|needs?|roles?)',
    r'(?:looking|need|needs|hiring|staffing)\s*(?:for|to fill)',
    r'(?:new|open|upcoming)\s*(?:positions?|reqs?|roles?|billets?)',
    r'backfill',
    r'attrition',
    r'growth',
    r'expansion',
    r'ramping up',
    r'pipeline',
    r'send\s*(?:me|us|over)\s*(?:candidates?|resumes?)',
    r'interviewing',
]

# Pain point signals
PAIN_POINT_SIGNALS = [
    r'struggling',
    r'difficult',
    r'challenge',
    r'shortage',
    r'hard to find',
    r'clearance.*delay',
    r'budget.*constraint',
    r'hiring.*freeze',
    r'layoff',
    r'cut',
    r'reduction',
    r'attrition',
    r'turnover',
    r'competition',
]

# Decision maker indicators
DECISION_MAKER_INDICATORS = [
    r'approve',
    r'sign.?off',
    r'decision',
    r'authority',
    r'budget',
    r'final say',
    r'leadership',
    r'executive',
]


class IntelligentContactClassifier:
    """Intelligently classify contacts from Bullhorn data."""

    def __init__(self):
        self.contacts = {}
        self.raw_notes = []

    def parse_all_bullhorn_files(self):
        """Parse all Bullhorn XLS files."""
        print("="*70)
        print("INTELLIGENT CONTACT CLASSIFIER")
        print("="*70)

        xls_files = [f for f in os.listdir(BULLHORN_DIR) if f.endswith('.XLS')]
        print(f"\nFound {len(xls_files)} XLS files")

        total_notes = 0
        for filename in xls_files:
            filepath = os.path.join(BULLHORN_DIR, filename)
            try:
                df = pd.read_excel(filepath, nrows=5)
                if len(df) > 1:
                    row1_str = str(df.iloc[1].tolist())
                    if 'Note Author' in row1_str and 'Note Body' in row1_str:
                        notes = self._parse_notes_file(filepath)
                        total_notes += notes
                        print(f"  {filename}: {notes} notes")
            except Exception as e:
                print(f"  Error with {filename}: {e}")

        print(f"\nTotal notes parsed: {total_notes}")
        print(f"Unique contacts identified: {len(self.contacts)}")

    def _parse_notes_file(self, filepath: str) -> int:
        """Parse a notes file and extract intelligence."""
        df = pd.read_excel(filepath)
        df.columns = df.iloc[1].tolist()
        df = df.iloc[2:].reset_index(drop=True)

        notes_count = 0
        for _, row in df.iterrows():
            if pd.isna(row.get('About')) or pd.isna(row.get('Note Body')):
                continue

            contact_name = str(row['About']).strip()
            note_body = str(row['Note Body'])
            note_date = str(row.get('Date Note Added', ''))
            note_author = str(row.get('Note Author', ''))
            status = str(row.get('Status', ''))
            note_type = str(row.get('Type', ''))

            contact_key = contact_name.lower()

            if contact_key not in self.contacts:
                self.contacts[contact_key] = {
                    'name': contact_name,
                    'primes': set(),
                    'programs': set(),
                    'locations': set(),
                    'clearances': set(),
                    'job_titles': set(),
                    'is_hiring_manager': False,
                    'is_decision_maker': False,
                    'has_open_reqs': False,
                    'pain_points': set(),
                    'notes': [],
                    'statuses': set(),
                    'authors': set(),
                    'note_count': 0,
                    'last_activity': '',
                    'first_activity': '',
                    'contact_type': 'unknown',  # client, candidate, or unknown
                    'relationship_score': 0,
                    'hiring_signals': [],
                    'email': '',
                    'phone': '',
                    'linkedin': '',
                }

            contact = self.contacts[contact_key]
            contact['note_count'] += 1

            # Track dates
            if note_date and note_date != 'nan':
                if not contact['first_activity'] or note_date < contact['first_activity']:
                    contact['first_activity'] = note_date
                if not contact['last_activity'] or note_date > contact['last_activity']:
                    contact['last_activity'] = note_date

            # Extract intelligence from note
            self._extract_primes(contact, note_body)
            self._extract_programs(contact, note_body)
            self._extract_locations(contact, note_body)
            self._extract_clearances(contact, note_body)
            self._extract_job_titles(contact, note_body)
            self._extract_hiring_signals(contact, note_body)
            self._extract_pain_points(contact, note_body)
            self._extract_decision_maker_status(contact, note_body)
            self._extract_contact_info(contact, note_body)
            self._determine_contact_type(contact, note_body, note_type, status)

            # Store note summary
            contact['notes'].append({
                'date': note_date,
                'author': note_author,
                'body': note_body[:500],
                'type': note_type,
            })

            if status and status != 'nan':
                contact['statuses'].add(status)
            if note_author and note_author != 'nan':
                contact['authors'].add(note_author)

            notes_count += 1

        return notes_count

    def _extract_primes(self, contact: dict, note: str):
        """Extract prime contractor mentions."""
        for prime, patterns in PRIME_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, note, re.IGNORECASE):
                    contact['primes'].add(prime)
                    break

    def _extract_programs(self, contact: dict, note: str):
        """Extract program/contract mentions."""
        for program, pattern in PROGRAM_PATTERNS.items():
            if re.search(pattern, note, re.IGNORECASE):
                contact['programs'].add(program)

    def _extract_locations(self, contact: dict, note: str):
        """Extract location mentions."""
        for location, pattern in LOCATION_PATTERNS.items():
            if re.search(pattern, note, re.IGNORECASE):
                contact['locations'].add(location)

    def _extract_clearances(self, contact: dict, note: str):
        """Extract clearance mentions."""
        for clearance, pattern in CLEARANCE_PATTERNS.items():
            if re.search(pattern, note, re.IGNORECASE):
                contact['clearances'].add(clearance)

    def _extract_job_titles(self, contact: dict, note: str):
        """Extract job title mentions."""
        for title, pattern in JOB_TITLE_PATTERNS.items():
            if re.search(pattern, note, re.IGNORECASE):
                contact['job_titles'].add(title)

    def _extract_hiring_signals(self, contact: dict, note: str):
        """Extract hiring signals from notes."""
        note_lower = note.lower()
        for signal in HIRING_SIGNALS:
            if re.search(signal, note_lower):
                contact['has_open_reqs'] = True
                contact['is_hiring_manager'] = True
                # Extract the actual signal text
                match = re.search(signal, note_lower)
                if match:
                    start = max(0, match.start() - 50)
                    end = min(len(note), match.end() + 100)
                    context = note[start:end].strip()
                    if context not in contact['hiring_signals']:
                        contact['hiring_signals'].append(context)

    def _extract_pain_points(self, contact: dict, note: str):
        """Extract pain points from notes."""
        note_lower = note.lower()
        for signal in PAIN_POINT_SIGNALS:
            if re.search(signal, note_lower):
                match = re.search(signal, note_lower)
                if match:
                    start = max(0, match.start() - 30)
                    end = min(len(note), match.end() + 50)
                    context = note[start:end].strip()
                    contact['pain_points'].add(context[:100])

    def _extract_decision_maker_status(self, contact: dict, note: str):
        """Determine if contact is a decision maker."""
        note_lower = note.lower()
        for indicator in DECISION_MAKER_INDICATORS:
            if re.search(indicator, note_lower):
                contact['is_decision_maker'] = True
                break

    def _extract_contact_info(self, contact: dict, note: str):
        """Extract email, phone, LinkedIn from notes."""
        # Email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', note)
        if email_match and not contact['email']:
            contact['email'] = email_match.group()

        # Phone
        phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', note)
        if phone_match and not contact['phone']:
            contact['phone'] = phone_match.group()

        # LinkedIn
        linkedin_match = re.search(r'linkedin\.com/in/[\w-]+', note)
        if linkedin_match and not contact['linkedin']:
            contact['linkedin'] = 'https://' + linkedin_match.group()

    def _determine_contact_type(self, contact: dict, note: str, note_type: str, status: str):
        """Determine if contact is client or candidate."""
        note_lower = note.lower()

        # Client indicators
        client_indicators = [
            'meeting with', 'met with', 'spoke with', 'call with',
            'has openings', 'has positions', 'hiring', 'staffing needs',
            'biweekly', 'monthly meeting', 'site visit', 'onsite',
        ]

        # Candidate indicators
        candidate_indicators = [
            'submitted to', 'interview scheduled', 'offer', 'placement',
            'resume', 'looking for', 'open to opportunities', 'salary',
            'relocation', 'start date',
        ]

        client_score = sum(1 for ind in client_indicators if ind in note_lower)
        candidate_score = sum(1 for ind in candidate_indicators if ind in note_lower)

        if client_score > candidate_score:
            contact['contact_type'] = 'client'
        elif candidate_score > client_score:
            contact['contact_type'] = 'candidate'

        # Calculate relationship score
        contact['relationship_score'] = contact['note_count'] * 2
        if contact['is_hiring_manager']:
            contact['relationship_score'] += 20
        if contact['has_open_reqs']:
            contact['relationship_score'] += 15
        if contact['is_decision_maker']:
            contact['relationship_score'] += 10
        if contact['contact_type'] == 'client':
            contact['relationship_score'] += 10

    def classify_contacts_by_tier(self):
        """Classify contacts into tiers based on relationship score and role."""
        for contact_key, contact in self.contacts.items():
            # Determine tier
            if contact['relationship_score'] >= 50 and contact['is_hiring_manager']:
                contact['tier'] = 'Tier 1 - Key Decision Maker'
            elif contact['relationship_score'] >= 30 or contact['is_hiring_manager']:
                contact['tier'] = 'Tier 2 - Active Relationship'
            elif contact['relationship_score'] >= 15:
                contact['tier'] = 'Tier 3 - Developing'
            else:
                contact['tier'] = 'Tier 4 - Prospect'

            # Determine primary job title
            title_priority = ['VP', 'Director', 'Chief', 'Program Manager', 'Deputy Program Manager',
                            'Staffing Manager', 'Talent Acquisition', 'Contracts Manager',
                            'Site Lead', 'Engineering Manager', 'Project Manager']

            contact['primary_title'] = 'Unknown'
            for title in title_priority:
                if title in contact['job_titles']:
                    contact['primary_title'] = title
                    break

    def build_enriched_databases(self):
        """Build enriched per-prime contact databases."""
        print("\n" + "="*70)
        print("BUILDING ENRICHED PRIME DATABASES")
        print("="*70)

        os.makedirs(OUTPUT_DIR, exist_ok=True)

        # Group contacts by prime
        prime_contacts = defaultdict(list)
        no_prime_contacts = []

        for contact_key, contact in self.contacts.items():
            if contact['primes']:
                for prime in contact['primes']:
                    prime_contacts[prime].append(contact)
            else:
                no_prime_contacts.append(contact)

        # Build CSV for each prime
        for prime, contacts in sorted(prime_contacts.items(), key=lambda x: -len(x[1])):
            self._build_prime_csv(prime, contacts)

        # Build unclassified contacts CSV
        if no_prime_contacts:
            self._build_prime_csv('Unclassified', no_prime_contacts)

        print(f"\n  Contacts without prime: {len(no_prime_contacts)}")

    def _build_prime_csv(self, prime: str, contacts: list):
        """Build enriched CSV for a prime."""
        rows = []
        for c in contacts:
            # Get most recent hiring signals
            recent_signals = c['hiring_signals'][:3] if c['hiring_signals'] else []

            rows.append({
                'Name': c['name'],
                'Primary Title': c.get('primary_title', 'Unknown'),
                'All Titles': ', '.join(sorted(c['job_titles'])) if c['job_titles'] else '',
                'Tier': c.get('tier', 'Tier 4 - Prospect'),
                'Contact Type': c['contact_type'],
                'Primes': ', '.join(sorted(c['primes'])) if c['primes'] else '',
                'Programs': ', '.join(sorted(c['programs'])) if c['programs'] else '',
                'Locations': ', '.join(sorted(c['locations'])) if c['locations'] else '',
                'Clearances': ', '.join(sorted(c['clearances'])) if c['clearances'] else '',
                'Is Hiring Manager': 'Yes' if c['is_hiring_manager'] else 'No',
                'Has Open Reqs': 'Yes' if c['has_open_reqs'] else 'No',
                'Is Decision Maker': 'Yes' if c['is_decision_maker'] else 'No',
                'Relationship Score': c['relationship_score'],
                'Note Count': c['note_count'],
                'Last Activity': c['last_activity'][:10] if c['last_activity'] else '',
                'First Activity': c['first_activity'][:10] if c['first_activity'] else '',
                'Email': c['email'],
                'Phone': c['phone'],
                'LinkedIn': c['linkedin'],
                'Authors': ', '.join(sorted(c['authors'])) if c['authors'] else '',
                'Statuses': ', '.join(sorted(c['statuses'])) if c['statuses'] else '',
                'Hiring Signals': ' | '.join(recent_signals) if recent_signals else '',
                'Pain Points': ' | '.join(list(c['pain_points'])[:3]) if c['pain_points'] else '',
                'Recent Note': c['notes'][-1]['body'][:300] if c['notes'] else '',
            })

        df = pd.DataFrame(rows)
        df = df.sort_values(['Tier', 'Relationship Score'], ascending=[True, False])

        safe_name = prime.replace(' ', '_').replace('/', '_')
        csv_path = os.path.join(OUTPUT_DIR, f"{safe_name}_Contacts_Enriched.csv")
        df.to_csv(csv_path, index=False)

        # Count key metrics
        hiring_managers = len([c for c in contacts if c['is_hiring_manager']])
        with_reqs = len([c for c in contacts if c['has_open_reqs']])
        tier1 = len([c for c in contacts if c.get('tier', '').startswith('Tier 1')])
        tier2 = len([c for c in contacts if c.get('tier', '').startswith('Tier 2')])

        print(f"\n  {prime}: {len(contacts)} contacts")
        print(f"    Tier 1 (Key Decision Makers): {tier1}")
        print(f"    Tier 2 (Active Relationships): {tier2}")
        print(f"    Hiring Managers: {hiring_managers}")
        print(f"    With Open Reqs: {with_reqs}")
        print(f"    Saved to: {csv_path}")

    def generate_intelligence_report(self):
        """Generate comprehensive intelligence report."""
        print("\n" + "="*70)
        print("GENERATING INTELLIGENCE REPORT")
        print("="*70)

        # Aggregate statistics
        total_contacts = len(self.contacts)
        clients = len([c for c in self.contacts.values() if c['contact_type'] == 'client'])
        candidates = len([c for c in self.contacts.values() if c['contact_type'] == 'candidate'])
        hiring_managers = len([c for c in self.contacts.values() if c['is_hiring_manager']])
        with_reqs = len([c for c in self.contacts.values() if c['has_open_reqs']])
        decision_makers = len([c for c in self.contacts.values() if c['is_decision_maker']])

        # Count by tier
        tier_counts = defaultdict(int)
        for c in self.contacts.values():
            tier_counts[c.get('tier', 'Unknown')] += 1

        # Program coverage
        program_contacts = defaultdict(int)
        for c in self.contacts.values():
            for prog in c['programs']:
                program_contacts[prog] += 1

        # Location coverage
        location_contacts = defaultdict(int)
        for c in self.contacts.values():
            for loc in c['locations']:
                location_contacts[loc] += 1

        # Generate report
        report = []
        report.append("# Contact Intelligence Report")
        report.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        report.append("\n\n## Executive Summary\n")
        report.append(f"| Metric | Count |")
        report.append(f"|--------|-------|")
        report.append(f"| Total Contacts | {total_contacts} |")
        report.append(f"| Client Contacts | {clients} |")
        report.append(f"| Candidate Contacts | {candidates} |")
        report.append(f"| Hiring Managers | {hiring_managers} |")
        report.append(f"| With Open Reqs | {with_reqs} |")
        report.append(f"| Decision Makers | {decision_makers} |")

        report.append("\n\n## Contact Tiers\n")
        report.append(f"| Tier | Count |")
        report.append(f"|------|-------|")
        for tier, count in sorted(tier_counts.items()):
            report.append(f"| {tier} | {count} |")

        report.append("\n\n## Program Coverage\n")
        report.append(f"| Program | Contacts |")
        report.append(f"|---------|----------|")
        for prog, count in sorted(program_contacts.items(), key=lambda x: -x[1])[:30]:
            report.append(f"| {prog} | {count} |")

        report.append("\n\n## Location Coverage\n")
        report.append(f"| Location | Contacts |")
        report.append(f"|----------|----------|")
        for loc, count in sorted(location_contacts.items(), key=lambda x: -x[1])[:30]:
            report.append(f"| {loc} | {count} |")

        report.append("\n\n## Top Hiring Managers (by relationship score)\n")
        report.append(f"| Name | Prime | Score | Open Reqs | Recent Activity |")
        report.append(f"|------|-------|-------|-----------|-----------------|")

        hiring_mgrs = [c for c in self.contacts.values() if c['is_hiring_manager']]
        hiring_mgrs = sorted(hiring_mgrs, key=lambda x: -x['relationship_score'])[:50]
        for c in hiring_mgrs:
            primes = ', '.join(list(c['primes'])[:2]) if c['primes'] else 'Unknown'
            report.append(f"| {c['name']} | {primes} | {c['relationship_score']} | {'Yes' if c['has_open_reqs'] else 'No'} | {c['last_activity'][:10] if c['last_activity'] else ''} |")

        # Save report
        report_path = os.path.join(REPORTS_DIR, "contact_intelligence_report.md")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))

        print(f"\n  Report saved to: {report_path}")

        # Save JSON summary
        json_summary = {
            'total_contacts': total_contacts,
            'clients': clients,
            'candidates': candidates,
            'hiring_managers': hiring_managers,
            'with_open_reqs': with_reqs,
            'decision_makers': decision_makers,
            'tier_counts': dict(tier_counts),
            'program_coverage': dict(program_contacts),
            'location_coverage': dict(location_contacts),
            'top_hiring_managers': [
                {
                    'name': c['name'],
                    'primes': list(c['primes']),
                    'score': c['relationship_score'],
                    'has_open_reqs': c['has_open_reqs'],
                }
                for c in hiring_mgrs[:20]
            ],
        }

        json_path = os.path.join(REPORTS_DIR, "contact_intelligence_summary.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_summary, f, indent=2)

        print(f"  JSON saved to: {json_path}")


def main():
    """Main entry point."""
    classifier = IntelligentContactClassifier()

    # Parse all Bullhorn files
    classifier.parse_all_bullhorn_files()

    # Classify contacts by tier
    classifier.classify_contacts_by_tier()

    # Build enriched databases
    classifier.build_enriched_databases()

    # Generate intelligence report
    classifier.generate_intelligence_report()

    print("\n" + "="*70)
    print("COMPLETE!")
    print("="*70)


if __name__ == "__main__":
    main()
