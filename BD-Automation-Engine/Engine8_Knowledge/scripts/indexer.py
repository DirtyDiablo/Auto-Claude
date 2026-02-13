"""
BD Data Indexer - Index all BD intelligence data into Qdrant.
Supports dashboard JSON files, Bullhorn exports, and processed documents.
"""

import sys
import csv
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from dataclasses import dataclass

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore

# Try to import auto-tagger
try:
    from Engine8_Knowledge.scripts.auto_tagger import AutoTagger, enrich_with_tags
    AUTO_TAGGER_AVAILABLE = True
except ImportError:
    AUTO_TAGGER_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('BDIndexer')

# =========================================
# CONFIGURATION
# =========================================

PROJECT_ROOT = Path(__file__).parent.parent.parent

# Data source paths
DASHBOARD_DATA_DIR = PROJECT_ROOT / "dashboard" / "public" / "data"
BULLHORN_DB_PATH = PROJECT_ROOT / "Engine7_BullhornETL" / "data" / "bullhorn_intelligence.db"
FEDERAL_PROGRAMS_CSV = PROJECT_ROOT / "Engine2_ProgramMapping" / "data" / "Federal_Programs_Master_Enriched_v2.csv"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
ANALYTICAL_OUTPUTS_DIR = PROJECT_ROOT / "data" / "from_n8n_builder" / "analytical_outputs"

# Dashboard data files
DASHBOARD_FILES = {
    'jobs': 'jobs_enriched.json',
    'contacts': 'contacts_classified.json',
    'programs': 'programs_enriched.json',
    'activities': 'call_notes_summary.json',
    'past_performance': 'past_performance.json',
}


@dataclass
class IndexingResult:
    """Result of an indexing operation."""
    collection: str
    source: str
    total_items: int
    indexed: int
    errors: int
    duration_seconds: float
    timestamp: str = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return {
            'collection': self.collection,
            'source': self.source,
            'total_items': self.total_items,
            'indexed': self.indexed,
            'errors': self.errors,
            'duration_seconds': self.duration_seconds,
            'timestamp': self.timestamp
        }


# =========================================
# DATA LOADERS
# =========================================

class BDDataLoader:
    """Load data from various BD sources."""

    @staticmethod
    def load_dashboard_jobs(path: Path = None) -> List[Dict]:
        """Load jobs from dashboard JSON."""
        file_path = path or (DASHBOARD_DATA_DIR / DASHBOARD_FILES['jobs'])

        if not file_path.exists():
            logger.warning(f"Jobs file not found: {file_path}")
            return []

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Handle nested structure
        if isinstance(data, dict) and 'jobs' in data:
            jobs = data['jobs']
        elif isinstance(data, list):
            jobs = data
        else:
            logger.warning(f"Unexpected jobs data format")
            return []

        # Filter out empty/test jobs
        valid_jobs = []
        for job in jobs:
            title = job.get('title', '').strip()
            if title and title.lower() not in ['', 'auto', 'job title', 'test']:
                valid_jobs.append(job)

        logger.info(f"Loaded {len(valid_jobs)} valid jobs from {file_path.name}")
        return valid_jobs

    @staticmethod
    def load_dashboard_contacts(path: Path = None) -> List[Dict]:
        """Load contacts from dashboard JSON."""
        file_path = path or (DASHBOARD_DATA_DIR / DASHBOARD_FILES['contacts'])

        if not file_path.exists():
            logger.warning(f"Contacts file not found: {file_path}")
            return []

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Handle tiered structure
        contacts = []
        if isinstance(data, dict):
            if 'by_tier' in data:
                for tier_contacts in data['by_tier'].values():
                    contacts.extend(tier_contacts)
            elif 'contacts' in data:
                contacts = data['contacts']
        elif isinstance(data, list):
            contacts = data

        # Filter contacts with names
        valid_contacts = []
        for contact in contacts:
            name = contact.get('name', '') or contact.get('first_name', '')
            if name and name.strip():
                valid_contacts.append(contact)

        logger.info(f"Loaded {len(valid_contacts)} contacts from {file_path.name}")
        return valid_contacts

    @staticmethod
    def load_dashboard_programs(path: Path = None) -> List[Dict]:
        """Load programs from dashboard JSON."""
        file_path = path or (DASHBOARD_DATA_DIR / DASHBOARD_FILES['programs'])

        if not file_path.exists():
            logger.warning(f"Programs file not found: {file_path}")
            return []

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Handle nested structure
        if isinstance(data, dict) and 'programs' in data:
            programs = data['programs']
        elif isinstance(data, list):
            programs = data
        else:
            logger.warning(f"Unexpected programs data format")
            return []

        # Filter programs with names
        valid_programs = [p for p in programs if p.get('name', '').strip()]

        logger.info(f"Loaded {len(valid_programs)} programs from {file_path.name}")
        return valid_programs

    @staticmethod
    def load_call_notes_as_activities(path: Path = None) -> List[Dict]:
        """Load call notes/activities from dashboard JSON."""
        # Try multiple sources
        sources = [
            DASHBOARD_DATA_DIR / 'call_notes_summary.json',
            DASHBOARD_DATA_DIR / 'call_notes_contacts.json',
        ]

        if path:
            sources = [path]

        activities = []
        for file_path in sources:
            if not file_path.exists():
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Handle different structures
                if isinstance(data, list):
                    activities.extend(data)
                elif isinstance(data, dict):
                    # Extract activities from nested structure
                    if 'activities' in data:
                        activities.extend(data['activities'])
                    elif 'contacts' in data:
                        # Call notes by contact
                        for contact_data in data['contacts']:
                            if isinstance(contact_data, dict) and 'notes' in contact_data:
                                for note in contact_data.get('notes', []):
                                    note['contact_name'] = contact_data.get('name', '')
                                    activities.append(note)

                logger.info(f"Loaded activities from {file_path.name}")
            except Exception as e:
                logger.warning(f"Failed to load {file_path}: {e}")

        logger.info(f"Total activities loaded: {len(activities)}")
        return activities

    @staticmethod
    def load_past_performance(path: Path = None) -> List[Dict]:
        """Load past performance data as documents."""
        file_path = path or (DASHBOARD_DATA_DIR / DASHBOARD_FILES['past_performance'])

        if not file_path.exists():
            logger.warning(f"Past performance file not found: {file_path}")
            return []

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        documents = []

        # Convert past performance entries to document format
        if isinstance(data, dict):
            for prime, perf_data in data.items():
                if isinstance(perf_data, dict):
                    doc = {
                        'id': f"pp_{prime.lower().replace(' ', '_')}",
                        'title': f"Past Performance: {prime}",
                        'content': json.dumps(perf_data, indent=2),
                        'summary': f"Past performance data for {prime}",
                        'doc_type': 'past_performance',
                        'source_file': str(file_path),
                        'tags': ['past_performance', prime.lower()],
                        'created_date': datetime.now().isoformat()
                    }
                    documents.append(doc)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                prime = item.get('prime_contractor', item.get('company', f'Unknown_{i}'))
                doc = {
                    'id': f"pp_{i}",
                    'title': f"Past Performance: {prime}",
                    'content': json.dumps(item, indent=2),
                    'summary': f"Past performance data for {prime}",
                    'doc_type': 'past_performance',
                    'source_file': str(file_path),
                    'tags': ['past_performance'],
                    'created_date': datetime.now().isoformat()
                }
                documents.append(doc)

        logger.info(f"Loaded {len(documents)} past performance documents")
        return documents

    @staticmethod
    def load_intelligence_reports() -> List[Dict]:
        """Load BD intelligence reports from markdown, CSV, and JSON sources."""
        reports = []

        # --- 1. Markdown intelligence reports from analytical_outputs ---
        if ANALYTICAL_OUTPUTS_DIR.exists():
            for md_file in sorted(ANALYTICAL_OUTPUTS_DIR.glob('*.md')):
                try:
                    content = md_file.read_text(encoding='utf-8', errors='replace')
                    if len(content.strip()) < 50:
                        continue

                    # Extract title from first heading or filename
                    title = md_file.stem.replace('_', ' ').replace('-', ' ').title()
                    for line in content.split('\n')[:5]:
                        line = line.strip()
                        if line.startswith('#'):
                            title = line.lstrip('#').strip()
                            break

                    # Classify report type from filename
                    fname_lower = md_file.stem.lower()
                    if 'intelligence' in fname_lower or 'intel' in fname_lower:
                        report_type = 'intelligence_analysis'
                    elif 'competitive' in fname_lower or 'competitor' in fname_lower:
                        report_type = 'competitive_intelligence'
                    elif 'strategy' in fname_lower:
                        report_type = 'strategy'
                    elif 'summary' in fname_lower or 'executive' in fname_lower:
                        report_type = 'executive_summary'
                    elif 'audit' in fname_lower:
                        report_type = 'audit'
                    elif 'playbook' in fname_lower:
                        report_type = 'playbook'
                    elif 'analysis' in fname_lower:
                        report_type = 'analysis'
                    elif 'implementation' in fname_lower or 'guide' in fname_lower:
                        report_type = 'guide'
                    else:
                        report_type = 'analytical_report'

                    # Truncate very long content for embedding (keep first ~8000 chars)
                    summary = content[:2000] if len(content) > 2000 else content

                    reports.append({
                        'title': title,
                        'content': content[:8000],
                        'summary': summary,
                        'source': str(md_file.relative_to(PROJECT_ROOT)),
                        'report_type': report_type,
                        'classification': 'unclassified',
                        'date': datetime.fromtimestamp(md_file.stat().st_mtime).strftime('%Y-%m-%d'),
                    })
                except Exception as e:
                    logger.warning(f"Failed to load MD report {md_file.name}: {e}")

        # --- 2. HUMINT briefings from outputs ---
        if OUTPUTS_DIR.exists():
            for humint_file in sorted(OUTPUTS_DIR.glob('HUMINT_*.md')):
                try:
                    content = humint_file.read_text(encoding='utf-8', errors='replace')
                    if len(content.strip()) < 50:
                        continue

                    title = humint_file.stem.replace('_', ' ').title()
                    for line in content.split('\n')[:5]:
                        line = line.strip()
                        if line.startswith('#'):
                            title = line.lstrip('#').strip()
                            break

                    summary = content[:2000]
                    reports.append({
                        'title': title,
                        'content': content[:8000],
                        'summary': summary,
                        'source': str(humint_file.relative_to(PROJECT_ROOT)),
                        'report_type': 'humint_briefing',
                        'classification': 'unclassified',
                        'date': datetime.fromtimestamp(humint_file.stat().st_mtime).strftime('%Y-%m-%d'),
                    })
                except Exception as e:
                    logger.warning(f"Failed to load HUMINT report {humint_file.name}: {e}")

            # BD Briefings subdirectory
            briefings_dir = OUTPUTS_DIR / 'BD_Briefings'
            if briefings_dir.exists():
                for brief_file in sorted(briefings_dir.glob('*.md')):
                    try:
                        content = brief_file.read_text(encoding='utf-8', errors='replace')
                        if len(content.strip()) < 50:
                            continue

                        title = brief_file.stem.replace('_', ' ').title()
                        for line in content.split('\n')[:5]:
                            line = line.strip()
                            if line.startswith('#'):
                                title = line.lstrip('#').strip()
                                break

                        reports.append({
                            'title': title,
                            'content': content[:8000],
                            'summary': content[:2000],
                            'source': str(brief_file.relative_to(PROJECT_ROOT)),
                            'report_type': 'bd_briefing',
                            'classification': 'unclassified',
                            'date': datetime.fromtimestamp(brief_file.stat().st_mtime).strftime('%Y-%m-%d'),
                        })
                    except Exception as e:
                        logger.warning(f"Failed to load briefing {brief_file.name}: {e}")

        # --- 3. Intelligence CSV files (row-per-record) ---
        csv_files = {
            'competitive_intelligence': 'COMPETITIVE_INTELLIGENCE.csv',
            'hiring_intelligence': 'hiring_intelligence.csv',
            'location_intelligence': 'location_intelligence.csv',
            'subaward_intelligence': 'subaward_intelligence.csv',
        }

        for report_type, csv_name in csv_files.items():
            csv_path = ANALYTICAL_OUTPUTS_DIR / csv_name
            if not csv_path.exists():
                continue

            try:
                with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
                    reader = csv.DictReader(f)
                    for i, row in enumerate(reader):
                        # Build content from all fields
                        content_parts = [f"{k}: {v}" for k, v in row.items() if v and v.strip()]
                        content = '; '.join(content_parts)

                        # Extract a meaningful title
                        title_field = next(
                            (row.get(k, '') for k in ['Prime', 'Program Name', 'Location', 'Company']
                             if row.get(k, '').strip()),
                            f"Row {i + 1}"
                        )

                        reports.append({
                            'title': f"{report_type.replace('_', ' ').title()}: {title_field}",
                            'content': content,
                            'summary': content[:500],
                            'source': str(csv_path.relative_to(PROJECT_ROOT)),
                            'report_type': report_type,
                            'classification': 'unclassified',
                            'date': datetime.fromtimestamp(csv_path.stat().st_mtime).strftime('%Y-%m-%d'),
                        })
            except Exception as e:
                logger.warning(f"Failed to load CSV {csv_name}: {e}")

        # --- 4. Master program intelligence JSON ---
        master_intel = ANALYTICAL_OUTPUTS_DIR / 'master_program_intelligence.json'
        if master_intel.exists():
            try:
                with open(master_intel, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                programs = data.get('programs', []) if isinstance(data, dict) else data
                for prog in programs:
                    if not isinstance(prog, dict):
                        continue

                    name = prog.get('program_name', 'Unknown Program')
                    content_parts = [f"{k}: {v}" for k, v in prog.items()
                                     if isinstance(v, (str, int, float)) and str(v).strip()]
                    content = '; '.join(content_parts)

                    reports.append({
                        'title': f"Program Intelligence: {name}",
                        'content': content,
                        'summary': content[:500],
                        'source': str(master_intel.relative_to(PROJECT_ROOT)),
                        'report_type': 'program_intelligence',
                        'classification': 'unclassified',
                        'date': data.get('metadata', {}).get('generated', '2026-01-21')[:10]
                            if isinstance(data, dict) else
                            datetime.fromtimestamp(master_intel.stat().st_mtime).strftime('%Y-%m-%d'),
                    })
            except Exception as e:
                logger.warning(f"Failed to load master_program_intelligence.json: {e}")

        # --- 5. Competitor analysis JSON ---
        competitor_json = ANALYTICAL_OUTPUTS_DIR / 'competitor-analysis.json'
        if competitor_json.exists():
            try:
                with open(competitor_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                items = data if isinstance(data, list) else [data]
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    name = item.get('name', item.get('company', 'Unknown'))
                    content = json.dumps(item, indent=2)[:6000]
                    reports.append({
                        'title': f"Competitor Analysis: {name}",
                        'content': content,
                        'summary': content[:500],
                        'source': str(competitor_json.relative_to(PROJECT_ROOT)),
                        'report_type': 'competitive_intelligence',
                        'classification': 'unclassified',
                        'date': datetime.fromtimestamp(competitor_json.stat().st_mtime).strftime('%Y-%m-%d'),
                    })
            except Exception as e:
                logger.warning(f"Failed to load competitor-analysis.json: {e}")

        logger.info(f"Loaded {len(reports)} intelligence reports from all sources")
        return reports


# =========================================
# INDEXER CLASS
# =========================================

class BDIndexer:
    """
    Index BD intelligence data into Qdrant vector store.

    Supports incremental and full indexing modes.
    Optionally enriches data with auto-generated tags.
    """

    def __init__(
        self,
        store: BDKnowledgeStore = None,
        enable_auto_tagging: bool = True
    ):
        """
        Initialize the indexer.

        Args:
            store: BDKnowledgeStore instance. Creates new one if None.
            enable_auto_tagging: Enable automatic tag generation.
        """
        self.store = store or BDKnowledgeStore()
        self.loader = BDDataLoader()
        self.results: List[IndexingResult] = []

        # Initialize auto-tagger if available and enabled
        self.auto_tagger = None
        if enable_auto_tagging and AUTO_TAGGER_AVAILABLE:
            self.auto_tagger = AutoTagger(use_llm=False)  # Use rules for speed
            logger.info("Auto-tagging enabled")

    def _enrich_data(self, data: List[Dict]) -> List[Dict]:
        """Enrich data with auto-generated tags if tagger is available."""
        if not self.auto_tagger:
            return data

        enriched = []
        for item in data:
            try:
                enriched.append(enrich_with_tags(item, self.auto_tagger))
            except Exception as e:
                logger.warning(f"Auto-tagging failed for item: {e}")
                enriched.append(item)

        return enriched

    def initialize(self, force_recreate: bool = False) -> Dict[str, bool]:
        """Initialize all collections."""
        logger.info("Initializing Qdrant collections...")
        return self.store.initialize_collections(force_recreate=force_recreate)

    def index_all(self, force_recreate: bool = False) -> List[IndexingResult]:
        """
        Index all available data sources.

        Args:
            force_recreate: If True, recreate collections before indexing.

        Returns:
            List of IndexingResult for each operation.
        """
        logger.info("Starting full indexing...")
        self.results = []

        # Initialize collections
        self.initialize(force_recreate=force_recreate)

        # Index each data source
        self.results.append(self.index_jobs())
        self.results.append(self.index_contacts())
        self.results.append(self.index_programs())
        self.results.append(self.index_documents())
        self.results.append(self.index_activities())
        self.results.append(self.index_intelligence_reports())

        # Print summary
        self._print_summary()

        return self.results

    def index_jobs(self, jobs: List[Dict] = None) -> IndexingResult:
        """Index job postings."""
        start_time = datetime.now()

        if jobs is None:
            jobs = self.loader.load_dashboard_jobs()

        # Enrich with auto-tags
        jobs = self._enrich_data(jobs)

        indexed, errors = 0, 0
        if jobs:
            indexed, errors = self.store.index_jobs(jobs)

        duration = (datetime.now() - start_time).total_seconds()

        result = IndexingResult(
            collection='jobs',
            source='dashboard/jobs_enriched.json',
            total_items=len(jobs),
            indexed=indexed,
            errors=errors,
            duration_seconds=duration
        )

        logger.info(f"Jobs indexing complete: {indexed} indexed, {errors} errors")
        return result

    def index_contacts(self, contacts: List[Dict] = None) -> IndexingResult:
        """Index contacts."""
        start_time = datetime.now()

        if contacts is None:
            contacts = self.loader.load_dashboard_contacts()

        # Enrich with auto-tags
        contacts = self._enrich_data(contacts)

        indexed, errors = 0, 0
        if contacts:
            indexed, errors = self.store.index_contacts(contacts)

        duration = (datetime.now() - start_time).total_seconds()

        result = IndexingResult(
            collection='contacts',
            source='dashboard/contacts_classified.json',
            total_items=len(contacts),
            indexed=indexed,
            errors=errors,
            duration_seconds=duration
        )

        logger.info(f"Contacts indexing complete: {indexed} indexed, {errors} errors")
        return result

    def index_programs(self, programs: List[Dict] = None) -> IndexingResult:
        """Index federal programs."""
        start_time = datetime.now()

        if programs is None:
            programs = self.loader.load_dashboard_programs()

        # Enrich with auto-tags
        programs = self._enrich_data(programs)

        indexed, errors = 0, 0
        if programs:
            indexed, errors = self.store.index_programs(programs)

        duration = (datetime.now() - start_time).total_seconds()

        result = IndexingResult(
            collection='programs',
            source='dashboard/programs_enriched.json',
            total_items=len(programs),
            indexed=indexed,
            errors=errors,
            duration_seconds=duration
        )

        logger.info(f"Programs indexing complete: {indexed} indexed, {errors} errors")
        return result

    def index_documents(self, documents: List[Dict] = None) -> IndexingResult:
        """Index documents (past performance, briefings, etc.)."""
        start_time = datetime.now()

        if documents is None:
            # Load past performance as documents
            documents = self.loader.load_past_performance()

            # TODO: Add more document sources
            # - Briefings from outputs/BD_Briefings/
            # - Playbooks from outputs/
            # - Processed Bullhorn exports

        # Enrich with auto-tags
        documents = self._enrich_data(documents)

        indexed, errors = 0, 0
        if documents:
            indexed, errors = self.store.index_documents(documents)

        duration = (datetime.now() - start_time).total_seconds()

        result = IndexingResult(
            collection='documents',
            source='dashboard/past_performance.json',
            total_items=len(documents),
            indexed=indexed,
            errors=errors,
            duration_seconds=duration
        )

        logger.info(f"Documents indexing complete: {indexed} indexed, {errors} errors")
        return result

    def index_activities(self, activities: List[Dict] = None) -> IndexingResult:
        """Index activities (call notes, interactions)."""
        start_time = datetime.now()

        if activities is None:
            activities = self.loader.load_call_notes_as_activities()

        # Enrich with auto-tags
        activities = self._enrich_data(activities)

        indexed, errors = 0, 0
        if activities:
            indexed, errors = self.store.index_activities(activities)

        duration = (datetime.now() - start_time).total_seconds()

        result = IndexingResult(
            collection='activities',
            source='dashboard/call_notes_*.json',
            total_items=len(activities),
            indexed=indexed,
            errors=errors,
            duration_seconds=duration
        )

        logger.info(f"Activities indexing complete: {indexed} indexed, {errors} errors")
        return result

    def index_intelligence_reports(self, reports: List[Dict] = None) -> IndexingResult:
        """Index BD intelligence reports, HUMINT briefings, and analysis docs."""
        start_time = datetime.now()

        if reports is None:
            reports = self.loader.load_intelligence_reports()

        # Enrich with auto-tags
        reports = self._enrich_data(reports)

        indexed, errors = 0, 0
        if reports:
            indexed, errors = self.store._index_data('intelligence_reports', reports, batch_size=50)

        duration = (datetime.now() - start_time).total_seconds()

        result = IndexingResult(
            collection='intelligence_reports',
            source='analytical_outputs + HUMINT + BD_Briefings',
            total_items=len(reports),
            indexed=indexed,
            errors=errors,
            duration_seconds=duration
        )

        logger.info(f"Intelligence reports indexing complete: {indexed} indexed, {errors} errors")
        return result

    def _print_summary(self):
        """Print indexing summary."""
        print("\n" + "=" * 60)
        print("INDEXING SUMMARY")
        print("=" * 60)

        total_items = 0
        total_indexed = 0
        total_errors = 0
        total_duration = 0

        for r in self.results:
            status = "OK" if r.errors == 0 else "WARN"
            print(f"  {r.collection:12} | {r.indexed:5} indexed | {r.errors:3} errors | {r.duration_seconds:.1f}s | {status}")
            total_items += r.total_items
            total_indexed += r.indexed
            total_errors += r.errors
            total_duration += r.duration_seconds

        print("-" * 60)
        print(f"  {'TOTAL':12} | {total_indexed:5} indexed | {total_errors:3} errors | {total_duration:.1f}s")
        print("=" * 60)

    def get_stats(self) -> Dict[str, Dict]:
        """Get collection statistics."""
        return self.store.get_collection_stats()

    def save_index_report(self, output_path: Path = None) -> Path:
        """Save indexing report to JSON file."""
        if output_path is None:
            output_path = PROJECT_ROOT / "Engine8_Knowledge" / "data" / "index_report.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        report = {
            'generated_at': datetime.now().isoformat(),
            'results': [r.to_dict() for r in self.results],
            'stats': self.get_stats()
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Index report saved to: {output_path}")
        return output_path


# =========================================
# CLI INTERFACE
# =========================================

def main():
    """CLI for the BD Indexer."""
    import argparse

    parser = argparse.ArgumentParser(description='BD Data Indexer')
    parser.add_argument('--all', action='store_true', help='Index all data sources')
    parser.add_argument('--jobs', action='store_true', help='Index jobs only')
    parser.add_argument('--contacts', action='store_true', help='Index contacts only')
    parser.add_argument('--programs', action='store_true', help='Index programs only')
    parser.add_argument('--documents', action='store_true', help='Index documents only')
    parser.add_argument('--activities', action='store_true', help='Index activities only')
    parser.add_argument('--intelligence', action='store_true', help='Index intelligence reports only')
    parser.add_argument('--force-recreate', action='store_true', help='Recreate collections')
    parser.add_argument('--stats', action='store_true', help='Show collection stats')
    parser.add_argument('--report', action='store_true', help='Save index report')

    args = parser.parse_args()

    # Create indexer
    indexer = BDIndexer()

    # Determine what to index
    if args.all or not any([args.jobs, args.contacts, args.programs, args.documents, args.activities, args.intelligence, args.stats]):
        indexer.index_all(force_recreate=args.force_recreate)
    else:
        indexer.initialize(force_recreate=args.force_recreate)

        if args.jobs:
            indexer.index_jobs()
        if args.contacts:
            indexer.index_contacts()
        if args.programs:
            indexer.index_programs()
        if args.documents:
            indexer.index_documents()
        if args.activities:
            indexer.index_activities()
        if args.intelligence:
            indexer.index_intelligence_reports()

    if args.stats:
        print("\nCollection Statistics:")
        stats = indexer.get_stats()
        for name, stat in stats.items():
            if 'error' in stat:
                print(f"  {name}: ERROR - {stat['error']}")
            else:
                print(f"  {name}: {stat.get('points_count', 0)} points")

    if args.report:
        indexer.save_index_report()


if __name__ == '__main__':
    main()
