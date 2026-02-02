"""
Coworker Takeover Data Importer v2
Parses Bullhorn XLS exports and generates comprehensive BD Playbook.
Extracts: Contacts, Candidates, Clients, Jobs, Recruiters, Pipeline Status
"""

import os
import sys
import json
import xlrd
import pandas as pd
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# =========================================
# CONFIGURATION
# =========================================

DATA_DIR = PROJECT_ROOT / "Engine7_BullhornETL" / "data" / "raw" / "coworker_takeover"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "coworker_takeover"
PROCESSED_DIR = PROJECT_ROOT / "Engine7_BullhornETL" / "data" / "processed"

# Known values for parsing
DEPARTMENTS = ['Atlanta', 'Denver', 'DC', 'Remote', 'San Diego', 'Austin', 'Dallas', 'Houston', 'Charlotte']
CONTACT_STATUSES = ['New Lead', 'New Contact', 'New Contacts', 'Active', 'Inactive']
JOB_STATUSES = ['Open', 'Placed', 'Closed', 'On Hold', 'Filled']
SUBMISSION_STATUSES = ['Client Submission', 'Interview Scheduled', 'Placed', 'Offer Extended',
                       'Offer Accepted', 'Sendout', 'Declined', 'Rejected', 'Withdrawn']
JOB_TYPES = ['Contract', 'Contract To Hire', 'Direct Hire', 'Temp', 'Permanent']


# =========================================
# XLS PARSER v2
# =========================================

class BullhornXLSParser:
    """Parse Bullhorn XLS exports with full structure extraction."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.workbook = None
        self.salesperson = None
        self.data = {
            'metadata': {},
            'contacts': [],           # Client visit contacts
            'new_contacts': [],       # Newly added contacts
            'jobs': [],               # Job postings
            'submissions': [],        # Candidate submissions to jobs
            'clients': set(),         # Unique clients
            'recruiters': set(),      # Unique recruiters
            'candidates': [],         # Candidates worked with
            'raw_rows': []
        }

    def parse(self) -> Dict[str, Any]:
        """Parse the XLS file and extract structured data."""
        print(f"\nParsing: {self.file_path.name}")

        try:
            self.workbook = xlrd.open_workbook(str(self.file_path))
        except Exception as e:
            print(f"  Error opening file: {e}")
            return self.data

        for sheet_idx in range(self.workbook.nsheets):
            sheet = self.workbook.sheet_by_index(sheet_idx)
            print(f"  Sheet: {sheet.name} ({sheet.nrows} rows x {sheet.ncols} cols)")

            if 'SalesActivity' in sheet.name:
                self._parse_sales_activity(sheet)
            elif 'NotesActivity' in sheet.name:
                self._parse_notes_activity(sheet)
            elif 'JobActivity' in sheet.name:
                self._parse_job_activity(sheet)

        # Convert sets to lists for JSON serialization
        self.data['clients'] = list(self.data['clients'])
        self.data['recruiters'] = list(self.data['recruiters'])

        return self.data

    def _cell_value(self, sheet, row, col):
        """Get cell value with type handling."""
        try:
            cell = sheet.cell(row, col)
            if cell.ctype == xlrd.XL_CELL_DATE:
                dt = xlrd.xldate_as_datetime(cell.value, self.workbook.datemode)
                return dt.strftime('%m/%d/%Y')
            elif cell.ctype == xlrd.XL_CELL_NUMBER:
                if cell.value == int(cell.value):
                    return int(cell.value)
                return cell.value
            return str(cell.value).strip() if cell.value else ''
        except:
            return ''

    def _parse_sales_activity(self, sheet):
        """Parse SalesActivityReport sheet with full structure."""
        current_section = None

        for row_idx in range(sheet.nrows):
            row = [self._cell_value(sheet, row_idx, col_idx) for col_idx in range(sheet.ncols)]
            row_text = ' '.join(str(c) for c in row if c).strip()

            if not row_text:
                continue

            # Store raw
            self.data['raw_rows'].append(row)

            # Detect metadata
            if 'Period' in row_text and 'to' in row_text:
                self.data['metadata']['period'] = row_text
                continue

            # Detect section headers
            if 'Client Visits' in row_text:
                current_section = 'client_visits'
                continue
            elif 'New Contacts' in row_text:
                current_section = 'new_contacts'
                continue
            elif 'New Jobs' in row_text or ':JOBPOSTING:' in row_text:
                current_section = 'new_jobs'
                continue

            # Skip header rows
            if any(h in row_text for h in ['Department', 'Salesperson', 'Contact Name', '# Pos', 'Recruiter']):
                continue

            # Parse data based on section
            if current_section == 'client_visits':
                self._parse_client_visit(row)
            elif current_section == 'new_contacts':
                self._parse_new_contact(row)
            elif current_section == 'new_jobs':
                # Check if it's a job posting or a submission
                if any(row_text.startswith(f'#{i}') for i in range(8000, 10000)):
                    self._parse_job_posting(row)
                elif '#' in row_text and any(s in row_text for s in SUBMISSION_STATUSES):
                    self._parse_submission(row)
                else:
                    self._parse_job_or_submission(row)

    def _parse_client_visit(self, row):
        """Parse a client visit row: [Dept, Salesperson, Contact, Date, Status]"""
        values = [str(v) for v in row if v]  # Convert all to strings
        if len(values) < 3:
            return

        contact = {'raw': values, 'type': 'client_visit'}

        for val in values:
            if val in DEPARTMENTS:
                contact['department'] = val
            elif val in CONTACT_STATUSES:
                contact['status'] = val
            elif '/' in val and len(val) <= 10:
                try:
                    datetime.strptime(val, '%m/%d/%Y')
                    contact['date_added'] = val
                except:
                    pass

        # Extract names - typically position 1 is salesperson, position 2 is contact
        name_candidates = [v for v in values if v not in DEPARTMENTS + CONTACT_STATUSES
                          and not ('/' in v and len(v) <= 10)]

        if len(name_candidates) >= 2:
            self.salesperson = name_candidates[0]
            contact['salesperson'] = name_candidates[0]
            contact['name'] = name_candidates[1]
            name_parts = name_candidates[1].split()
            if len(name_parts) >= 2:
                contact['first_name'] = name_parts[0]
                contact['last_name'] = ' '.join(name_parts[1:])
        elif len(name_candidates) == 1:
            contact['name'] = name_candidates[0]

        if contact.get('name'):
            self.data['contacts'].append(contact)

    def _parse_new_contact(self, row):
        """Parse a new contact row."""
        values = [str(v) for v in row if v]  # Convert all to strings
        if len(values) < 3:
            return

        contact = {'raw': values, 'type': 'new_contact'}

        for val in values:
            if val in DEPARTMENTS:
                contact['department'] = val
            elif val in CONTACT_STATUSES:
                contact['status'] = val
            elif '/' in val and len(val) <= 10:
                try:
                    datetime.strptime(val, '%m/%d/%Y')
                    contact['date_added'] = val
                except:
                    pass

        name_candidates = [v for v in values if v not in DEPARTMENTS + CONTACT_STATUSES
                          and not ('/' in v and len(v) <= 10)]

        if len(name_candidates) >= 2:
            contact['salesperson'] = name_candidates[0]
            contact['name'] = name_candidates[1]
        elif len(name_candidates) == 1:
            contact['name'] = name_candidates[0]

        if contact.get('name'):
            self.data['new_contacts'].append(contact)

    def _parse_job_posting(self, row):
        """Parse a job posting row: [JobID+Title, Type, Date, Status, Location, ...]"""
        values = [str(v) for v in row if v]  # Convert all to strings
        if not values:
            return

        job = {'raw': values}

        for val in values:
            # Job ID and title (e.g., "#8513 All Source Intel Analyst")
            if val.startswith('#') and ' ' in val:
                parts = val.split(' ', 1)
                job['job_id'] = parts[0]
                job['title'] = parts[1] if len(parts) > 1 else ''
            elif val.startswith('#'):
                job['job_id'] = val
            # Job type
            elif val in JOB_TYPES:
                job['type'] = val
            # Status
            elif val in JOB_STATUSES:
                job['status'] = val
            # Date
            elif '/' in val and len(val) <= 10:
                try:
                    datetime.strptime(val, '%m/%d/%Y')
                    job['date'] = val
                except:
                    pass
            # Location (contains comma)
            elif ',' in val and any(c.isalpha() for c in val):
                job['location'] = val

        if job.get('job_id'):
            self.data['jobs'].append(job)

    def _parse_job_or_submission(self, row):
        """Parse row that could be job posting or candidate submission."""
        values = [str(v) for v in row if v]  # Convert all to strings
        if len(values) < 4:
            return

        # Submission format: [Dept, Salesperson, Candidate, Job, Client, Recruiter, Date, Status]
        # Check if we have a submission status
        has_submission_status = any(v in SUBMISSION_STATUSES for v in values)
        has_job_id = any(v.startswith('#') or ('#' in v and any(c.isdigit() for c in v)) for v in values)

        if has_submission_status and has_job_id:
            self._parse_submission(row)
        elif has_job_id:
            self._parse_job_posting(row)

    def _parse_submission(self, row):
        """Parse a candidate submission: [Dept, Salesperson, Candidate, Job, Client, Recruiter, Date, Status]"""
        values = [str(v) for v in row if v]  # Convert all to strings
        if len(values) < 5:
            return

        submission = {'raw': values}

        # Extract by position and pattern
        for i, val in enumerate(values):
            # Department
            if val in DEPARTMENTS:
                submission['department'] = val
            # Job ID + Title
            elif val.startswith('#') or (val.startswith('#') and ' ' in val):
                if ' ' in val:
                    parts = val.split(' ', 1)
                    submission['job_id'] = parts[0]
                    submission['title'] = parts[1]
                else:
                    submission['job_id'] = val
            elif '#' in val:
                # Extract job ID from within text
                import re
                match = re.search(r'#\d+', val)
                if match:
                    submission['job_id'] = match.group()
                    remaining = val.replace(match.group(), '').strip()
                    if remaining:
                        submission['title'] = remaining
            # Client (contains "ONLY ONE" or known patterns)
            elif 'ONLY ONE' in val or 'Grumman' in val or 'SAIC' in val or 'Leidos' in val or 'Raytheon' in val:
                # Clean up client name
                client = val.replace(' - ONLY ONE YOU ARE TO USE', '').replace('- ONLY ONE YOU ARE TO USE', '').strip()
                submission['client'] = client
                self.data['clients'].add(client)
            # Submission status
            elif val in SUBMISSION_STATUSES:
                submission['status'] = val
            # Date
            elif '/' in val and len(val) <= 10:
                try:
                    datetime.strptime(val, '%m/%d/%Y')
                    submission['date'] = val
                except:
                    pass

        # Extract names (salesperson, candidate, recruiter)
        name_candidates = []
        for val in values:
            if val not in DEPARTMENTS + SUBMISSION_STATUSES:
                if not val.startswith('#') and '#' not in val:
                    if 'ONLY ONE' not in val and 'Grumman' not in val and 'SAIC' not in val:
                        if not ('/' in val and len(val) <= 10):
                            # Check if it looks like a name
                            cleaned = val.replace(' ', '').replace('.', '').replace('-', '')
                            if cleaned.isalpha() and len(val) > 1 and len(val) < 50:
                                name_candidates.append(val)

        # Assign names based on position
        if len(name_candidates) >= 3:
            submission['salesperson'] = name_candidates[0]
            submission['candidate'] = name_candidates[1]
            submission['recruiter'] = name_candidates[2]
            self.data['recruiters'].add(name_candidates[2])
        elif len(name_candidates) >= 2:
            submission['salesperson'] = name_candidates[0]
            submission['candidate'] = name_candidates[1]
        elif len(name_candidates) >= 1:
            submission['candidate'] = name_candidates[0]

        # Add to candidates list
        if submission.get('candidate'):
            candidate = {
                'name': submission['candidate'],
                'job_id': submission.get('job_id'),
                'job_title': submission.get('title'),
                'client': submission.get('client'),
                'status': submission.get('status'),
                'date': submission.get('date')
            }
            self.data['candidates'].append(candidate)

        if submission.get('job_id') or submission.get('candidate'):
            self.data['submissions'].append(submission)

    def _parse_notes_activity(self, sheet):
        """Parse NotesActivityReport sheet."""
        for row_idx in range(sheet.nrows):
            row = [self._cell_value(sheet, row_idx, col_idx) for col_idx in range(sheet.ncols)]
            row_text = ' '.join(str(c) for c in row if c).strip()

            if row_text and 'No data was returned' not in row_text:
                self.data['raw_rows'].append(row)

    def _parse_job_activity(self, sheet):
        """Parse JobActivityReport sheet - contains job postings with status."""
        for row_idx in range(sheet.nrows):
            row = [self._cell_value(sheet, row_idx, col_idx) for col_idx in range(sheet.ncols)]
            values = [str(v) for v in row if v]

            if not values:
                continue

            # Skip header rows
            row_text = ' '.join(values)
            if 'No data was returned' in row_text:
                continue
            if any(h in row_text for h in ['Job ID', 'Job Title', 'Status', 'Date Opened']):
                continue

            # Store raw
            self.data['raw_rows'].append(row)

            # Parse job data
            job = {'raw': values, 'source': 'JobActivityReport'}

            for val in values:
                # Job ID (starts with #)
                if val.startswith('#') and any(c.isdigit() for c in val):
                    if ' ' in val:
                        parts = val.split(' ', 1)
                        job['job_id'] = parts[0]
                        job['title'] = parts[1]
                    else:
                        job['job_id'] = val
                # Status
                elif val in JOB_STATUSES:
                    job['status'] = val
                # Job type
                elif val in JOB_TYPES:
                    job['type'] = val
                # Date
                elif '/' in val and len(val) <= 10:
                    try:
                        datetime.strptime(val, '%m/%d/%Y')
                        job['date'] = val
                    except:
                        pass
                # Location (contains comma and letters)
                elif ',' in val and any(c.isalpha() for c in val):
                    job['location'] = val
                # Client detection
                elif 'Grumman' in val or 'SAIC' in val or 'GDIT' in val or 'Leidos' in val or 'Raytheon' in val:
                    client = val.replace(' - ONLY ONE YOU ARE TO USE', '').strip()
                    job['client'] = client
                    self.data['clients'].add(client)

            if job.get('job_id'):
                self.data['jobs'].append(job)


# =========================================
# BD PLAYBOOK GENERATOR v2
# =========================================

class BDPlaybookGenerator:
    """Generate comprehensive BD Playbook from parsed data."""

    def __init__(self, parsed_data: Dict[str, Any], salesperson: str = "Colton Scurry"):
        self.data = parsed_data
        self.salesperson = salesperson
        self.playbook = {
            'generated_at': datetime.now().isoformat(),
            'salesperson': salesperson,
            'summary': {},
            'contacts': {
                'all': [],
                'by_status': {},
                'by_date': {},
                'timeline': []
            },
            'clients': {
                'all': [],
                'by_activity': {}
            },
            'jobs': {
                'all': [],
                'by_status': {},
                'by_client': {}
            },
            'candidates': {
                'all': [],
                'by_status': {},
                'by_client': {}
            },
            'pipeline': {
                'submissions': [],
                'interviews': [],
                'placements': [],
                'active': []
            },
            'recruiters': [],
            'analysis': {},
            'recommendations': []
        }

    def generate(self) -> Dict[str, Any]:
        """Generate the full playbook."""
        print("\n" + "="*60)
        print("GENERATING BD PLAYBOOK")
        print("="*60)

        self._process_contacts()
        self._process_clients()
        self._process_jobs()
        self._process_candidates()
        self._process_pipeline()
        self._analyze_relationships()
        self._generate_recommendations()
        self._build_summary()

        return self.playbook

    def _process_contacts(self):
        """Process all contacts."""
        all_contacts = []
        all_contacts.extend(self.data.get('contacts', []))
        all_contacts.extend(self.data.get('new_contacts', []))

        # Deduplicate by name
        seen_names = set()
        unique_contacts = []
        for contact in all_contacts:
            name = contact.get('name', '').lower().strip()
            if name and name not in seen_names:
                seen_names.add(name)
                unique_contacts.append(contact)

        self.playbook['contacts']['all'] = unique_contacts

        # Group by status
        by_status = defaultdict(list)
        for contact in unique_contacts:
            status = contact.get('status', 'Unknown')
            by_status[status].append(contact)
        self.playbook['contacts']['by_status'] = dict(by_status)

        # Group by month
        by_date = defaultdict(list)
        for contact in unique_contacts:
            date_str = contact.get('date_added', '')
            if date_str:
                try:
                    dt = datetime.strptime(date_str, '%m/%d/%Y')
                    year_month = dt.strftime('%Y-%m')
                    by_date[year_month].append(contact)
                except:
                    pass
        self.playbook['contacts']['by_date'] = dict(by_date)

        # Build timeline
        timeline = []
        for date_key in sorted(by_date.keys()):
            contacts = by_date[date_key]
            timeline.append({
                'period': date_key,
                'count': len(contacts),
                'contacts': [c.get('name', 'Unknown') for c in contacts]
            })
        self.playbook['contacts']['timeline'] = timeline

        print(f"  Processed {len(unique_contacts)} unique contacts")

    def _process_clients(self):
        """Process clients."""
        clients = self.data.get('clients', [])
        self.playbook['clients']['all'] = clients

        # Count activity by client
        by_activity = defaultdict(lambda: {'submissions': 0, 'placements': 0, 'jobs': []})

        for submission in self.data.get('submissions', []):
            client = submission.get('client', 'Unknown')
            if client:
                by_activity[client]['submissions'] += 1
                if submission.get('status') == 'Placed':
                    by_activity[client]['placements'] += 1
                job_id = submission.get('job_id')
                if job_id and job_id not in by_activity[client]['jobs']:
                    by_activity[client]['jobs'].append(job_id)

        self.playbook['clients']['by_activity'] = {k: dict(v) for k, v in by_activity.items()}
        print(f"  Processed {len(clients)} unique clients")

    def _process_jobs(self):
        """Process jobs."""
        jobs = self.data.get('jobs', [])
        self.playbook['jobs']['all'] = jobs

        # Group by status
        by_status = defaultdict(list)
        for job in jobs:
            status = job.get('status', 'Unknown')
            by_status[status].append(job)
        self.playbook['jobs']['by_status'] = dict(by_status)

        # Also gather jobs from submissions
        submission_jobs = defaultdict(lambda: {'submissions': 0, 'placements': 0, 'candidates': []})
        for submission in self.data.get('submissions', []):
            job_id = submission.get('job_id')
            if job_id:
                submission_jobs[job_id]['submissions'] += 1
                if submission.get('status') == 'Placed':
                    submission_jobs[job_id]['placements'] += 1
                candidate = submission.get('candidate')
                if candidate:
                    submission_jobs[job_id]['candidates'].append(candidate)
                if submission.get('client'):
                    submission_jobs[job_id]['client'] = submission.get('client')
                if submission.get('title'):
                    submission_jobs[job_id]['title'] = submission.get('title')

        self.playbook['jobs']['by_client'] = {k: dict(v) for k, v in submission_jobs.items()}
        print(f"  Processed {len(jobs)} job postings, {len(submission_jobs)} with submissions")

    def _process_candidates(self):
        """Process candidates."""
        candidates = self.data.get('candidates', [])

        # Deduplicate by name
        seen = set()
        unique = []
        for c in candidates:
            name = c.get('name', '').lower()
            if name and name not in seen:
                seen.add(name)
                unique.append(c)

        self.playbook['candidates']['all'] = unique

        # Group by status
        by_status = defaultdict(list)
        for c in candidates:
            status = c.get('status', 'Unknown')
            by_status[status].append(c)
        self.playbook['candidates']['by_status'] = dict(by_status)

        # Group by client
        by_client = defaultdict(list)
        for c in candidates:
            client = c.get('client', 'Unknown')
            by_client[client].append(c)
        self.playbook['candidates']['by_client'] = dict(by_client)

        print(f"  Processed {len(unique)} unique candidates")

    def _process_pipeline(self):
        """Process submission pipeline."""
        submissions = self.data.get('submissions', [])

        for sub in submissions:
            status = sub.get('status', '')
            if status == 'Placed':
                self.playbook['pipeline']['placements'].append(sub)
            elif 'Interview' in status:
                self.playbook['pipeline']['interviews'].append(sub)
            elif status == 'Client Submission':
                self.playbook['pipeline']['submissions'].append(sub)
            else:
                self.playbook['pipeline']['active'].append(sub)

        print(f"  Pipeline: {len(self.playbook['pipeline']['placements'])} placements, "
              f"{len(self.playbook['pipeline']['interviews'])} interviews, "
              f"{len(self.playbook['pipeline']['submissions'])} submissions")

    def _analyze_relationships(self):
        """Analyze relationship patterns."""
        analysis = {
            'top_clients': [],
            'hot_jobs': [],
            'recent_placements': [],
            'active_candidates': [],
            'recruiter_partnerships': []
        }

        # Top clients by activity
        client_activity = self.playbook['clients'].get('by_activity', {})
        sorted_clients = sorted(client_activity.items(),
                                key=lambda x: x[1].get('submissions', 0),
                                reverse=True)
        analysis['top_clients'] = [
            {'name': c[0], 'submissions': c[1].get('submissions', 0),
             'placements': c[1].get('placements', 0)}
            for c in sorted_clients[:10]
        ]

        # Hot jobs (most submissions)
        job_activity = self.playbook['jobs'].get('by_client', {})
        sorted_jobs = sorted(job_activity.items(),
                            key=lambda x: x[1].get('submissions', 0),
                            reverse=True)
        analysis['hot_jobs'] = [
            {'job_id': j[0], 'title': j[1].get('title', ''),
             'client': j[1].get('client', ''), 'submissions': j[1].get('submissions', 0)}
            for j in sorted_jobs[:10]
        ]

        # Recent placements
        placements = self.playbook['pipeline'].get('placements', [])
        analysis['recent_placements'] = placements[:20]

        # Recruiters
        recruiters = list(self.data.get('recruiters', []))
        self.playbook['recruiters'] = recruiters
        analysis['recruiter_partnerships'] = recruiters

        self.playbook['analysis'] = analysis

    def _generate_recommendations(self):
        """Generate actionable recommendations."""
        recommendations = []

        # Top client relationships to maintain
        top_clients = self.playbook['analysis'].get('top_clients', [])[:5]
        if top_clients:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Client Relationships',
                'action': f"Introduce yourself to {len(top_clients)} key client contacts",
                'clients': [c['name'] for c in top_clients],
                'rationale': 'These clients had the most activity and represent ongoing relationships'
            })

        # Active interviews to follow up
        interviews = self.playbook['pipeline'].get('interviews', [])
        if interviews:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Interview Pipeline',
                'action': f"Follow up on {len(interviews)} active interviews",
                'candidates': list(set(i.get('candidate', '') for i in interviews[:10] if i.get('candidate'))),
                'rationale': 'Candidates in interview stage are closest to placement'
            })

        # Recent submissions needing follow-up
        submissions = self.playbook['pipeline'].get('submissions', [])
        if submissions:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Submission Follow-up',
                'action': f"Check status of {len(submissions)} pending submissions",
                'rationale': 'Submitted candidates need follow-up to move to interview stage'
            })

        # Hot contacts
        contacts = self.playbook['contacts'].get('all', [])
        new_leads = [c for c in contacts if c.get('status') in ['New Lead', 'New Contact']]
        if new_leads:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'New Contact Engagement',
                'action': f"Reach out to {len(new_leads)} new leads/contacts",
                'contacts': [c.get('name') for c in new_leads[:10]],
                'rationale': 'New leads need nurturing to convert to active relationships'
            })

        # Recruiter coordination
        recruiters = self.playbook.get('recruiters', [])
        if recruiters:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Recruiter Coordination',
                'action': f"Connect with {len(recruiters)} recruiting partners",
                'recruiters': recruiters,
                'rationale': 'Maintain recruiter relationships for ongoing candidate flow'
            })

        self.playbook['recommendations'] = recommendations
        print(f"  Generated {len(recommendations)} recommendations")

    def _build_summary(self):
        """Build executive summary."""
        self.playbook['summary'] = {
            'total_contacts': len(self.playbook['contacts']['all']),
            'total_clients': len(self.playbook['clients']['all']),
            'total_jobs': len(self.playbook['jobs']['all']),
            'total_candidates': len(self.playbook['candidates']['all']),
            'total_submissions': len(self.data.get('submissions', [])),
            'total_placements': len(self.playbook['pipeline']['placements']),
            'total_interviews': len(self.playbook['pipeline']['interviews']),
            'total_recruiters': len(self.playbook.get('recruiters', [])),
            'contact_statuses': {k: len(v) for k, v in self.playbook['contacts']['by_status'].items()},
            'activity_period': self.data.get('metadata', {}).get('period', 'Unknown')
        }


# =========================================
# REPORT GENERATOR
# =========================================

def generate_markdown_report(playbook: Dict) -> str:
    """Generate a comprehensive markdown report."""

    lines = [
        f"# BD Takeover Playbook: {playbook['salesperson']}",
        f"",
        f"**Generated:** {playbook['generated_at']}",
        f"**Activity Period:** {playbook['summary'].get('activity_period', 'Unknown')}",
        f"",
        "---",
        "",
        "## Executive Summary",
        "",
        "| Metric | Count |",
        "|--------|-------|",
        f"| Contacts | {playbook['summary']['total_contacts']} |",
        f"| Clients | {playbook['summary']['total_clients']} |",
        f"| Jobs Worked | {playbook['summary']['total_jobs']} |",
        f"| Candidates | {playbook['summary']['total_candidates']} |",
        f"| Total Submissions | {playbook['summary']['total_submissions']} |",
        f"| Placements | {playbook['summary']['total_placements']} |",
        f"| Active Interviews | {playbook['summary']['total_interviews']} |",
        f"| Recruiter Partners | {playbook['summary']['total_recruiters']} |",
        "",
        "---",
        "",
        "## Priority Actions",
        ""
    ]

    for rec in playbook.get('recommendations', []):
        lines.append(f"### {rec['priority']}: {rec['category']}")
        lines.append(f"")
        lines.append(f"**Action:** {rec['action']}")
        lines.append(f"")
        lines.append(f"**Rationale:** {rec['rationale']}")
        lines.append(f"")

        if rec.get('clients'):
            lines.append("**Clients:**")
            for name in rec['clients'][:10]:
                lines.append(f"- {name}")
            lines.append("")

        if rec.get('candidates'):
            lines.append("**Candidates:**")
            for name in rec['candidates'][:10]:
                lines.append(f"- {name}")
            lines.append("")

        if rec.get('contacts'):
            lines.append("**Contacts:**")
            for name in rec['contacts'][:10]:
                lines.append(f"- {name}")
            lines.append("")

        if rec.get('recruiters'):
            lines.append("**Recruiters:**")
            for name in rec['recruiters'][:10]:
                lines.append(f"- {name}")
            lines.append("")

    # Top Clients Section
    lines.extend([
        "---",
        "",
        "## Top Clients",
        "",
        "| Client | Submissions | Placements |",
        "|--------|-------------|------------|"
    ])

    for client in playbook['analysis'].get('top_clients', [])[:15]:
        lines.append(f"| {client['name']} | {client['submissions']} | {client['placements']} |")

    # Hot Jobs Section
    lines.extend([
        "",
        "---",
        "",
        "## Hot Jobs (Most Activity)",
        "",
        "| Job ID | Title | Client | Submissions |",
        "|--------|-------|--------|-------------|"
    ])

    for job in playbook['analysis'].get('hot_jobs', [])[:15]:
        lines.append(f"| {job['job_id']} | {job.get('title', 'N/A')[:30]} | {job.get('client', 'N/A')[:20]} | {job['submissions']} |")

    # Pipeline Section
    lines.extend([
        "",
        "---",
        "",
        "## Active Pipeline",
        "",
        "### Interviews in Progress",
        ""
    ])

    for interview in playbook['pipeline'].get('interviews', [])[:20]:
        candidate = interview.get('candidate', 'Unknown')
        job = interview.get('job_id', '') + ' ' + interview.get('title', '')
        client = interview.get('client', '')
        lines.append(f"- **{candidate}** - {job.strip()} ({client})")

    lines.extend([
        "",
        "### Recent Placements",
        ""
    ])

    for placement in playbook['pipeline'].get('placements', [])[:20]:
        candidate = placement.get('candidate', 'Unknown')
        job = placement.get('job_id', '') + ' ' + placement.get('title', '')
        client = placement.get('client', '')
        date = placement.get('date', '')
        lines.append(f"- **{candidate}** - {job.strip()} @ {client} ({date})")

    # Contacts Section
    lines.extend([
        "",
        "---",
        "",
        "## Contact Directory",
        "",
        "### By Status",
        ""
    ])

    for status, contacts in playbook['contacts']['by_status'].items():
        lines.append(f"#### {status} ({len(contacts)})")
        lines.append("")
        for contact in contacts[:10]:
            name = contact.get('name', 'Unknown')
            date = contact.get('date_added', '')
            lines.append(f"- **{name}** (Added: {date})")
        if len(contacts) > 10:
            lines.append(f"- ... and {len(contacts) - 10} more")
        lines.append("")

    # Recruiter Partners
    lines.extend([
        "---",
        "",
        "## Recruiter Partners",
        ""
    ])

    for recruiter in playbook.get('recruiters', []):
        lines.append(f"- {recruiter}")

    # Activity Timeline
    lines.extend([
        "",
        "---",
        "",
        "## Activity Timeline",
        ""
    ])

    for period in playbook['contacts'].get('timeline', [])[-12:]:
        lines.append(f"### {period['period']} ({period['count']} contacts)")
        for name in period['contacts'][:5]:
            lines.append(f"- {name}")
        if len(period['contacts']) > 5:
            lines.append(f"- ... and {len(period['contacts']) - 5} more")
        lines.append("")

    return '\n'.join(lines)


# =========================================
# MAIN
# =========================================

def main():
    """Main entry point."""
    print("="*60)
    print("COWORKER TAKEOVER DATA IMPORTER v2")
    print("="*60)

    # Create output directories
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Find all XLS files
    xls_files = list(DATA_DIR.glob("*.XLS")) + list(DATA_DIR.glob("*.xls"))
    print(f"\nFound {len(xls_files)} XLS files")

    if not xls_files:
        print("No XLS files found!")
        return

    # Parse all files
    all_data = {
        'metadata': {},
        'contacts': [],
        'new_contacts': [],
        'jobs': [],
        'submissions': [],
        'clients': set(),
        'recruiters': set(),
        'candidates': [],
        'raw_rows': []
    }

    for xls_file in xls_files:
        parser = BullhornXLSParser(xls_file)
        data = parser.parse()

        # Merge data
        if data.get('metadata'):
            all_data['metadata'].update(data['metadata'])
        all_data['contacts'].extend(data.get('contacts', []))
        all_data['new_contacts'].extend(data.get('new_contacts', []))
        all_data['jobs'].extend(data.get('jobs', []))
        all_data['submissions'].extend(data.get('submissions', []))
        all_data['clients'].update(data.get('clients', []))
        all_data['recruiters'].update(data.get('recruiters', []))
        all_data['candidates'].extend(data.get('candidates', []))
        all_data['raw_rows'].extend(data.get('raw_rows', []))

    # Convert sets to lists
    all_data['clients'] = list(all_data['clients'])
    all_data['recruiters'] = list(all_data['recruiters'])

    # Save parsed data
    parsed_output = OUTPUT_DIR / "parsed_data.json"
    with open(parsed_output, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, default=str)
    print(f"\nSaved parsed data to: {parsed_output}")

    # Generate playbook
    generator = BDPlaybookGenerator(all_data)
    playbook = generator.generate()

    # Save playbook JSON
    playbook_json = OUTPUT_DIR / "bd_playbook.json"
    with open(playbook_json, 'w', encoding='utf-8') as f:
        json.dump(playbook, f, indent=2, default=str)
    print(f"Saved playbook JSON to: {playbook_json}")

    # Generate markdown report
    report = generate_markdown_report(playbook)
    report_md = OUTPUT_DIR / "BD_TAKEOVER_PLAYBOOK.md"
    with open(report_md, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"Saved markdown report to: {report_md}")

    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"  Contacts: {playbook['summary']['total_contacts']}")
    print(f"  Clients: {playbook['summary']['total_clients']}")
    print(f"  Jobs: {playbook['summary']['total_jobs']}")
    print(f"  Candidates: {playbook['summary']['total_candidates']}")
    print(f"  Submissions: {playbook['summary']['total_submissions']}")
    print(f"  Placements: {playbook['summary']['total_placements']}")
    print(f"  Interviews: {playbook['summary']['total_interviews']}")
    print(f"  Recruiters: {playbook['summary']['total_recruiters']}")
    print("="*60)

    print(f"\n[OK] Playbook generated successfully!")
    print(f"  -> View report: {report_md}")
    print(f"  -> Raw data: {playbook_json}")

    return playbook


if __name__ == '__main__':
    main()
