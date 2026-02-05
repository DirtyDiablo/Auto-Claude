#!/usr/bin/env python
"""
Full BD Data Indexer - Index ALL data sources into Hub API.

COMPREHENSIVE INDEXER FOR:
- BD-Automation-Engine (~500 files, ~0.5 GB)
- Data-Scraper (~10,000 files, ~10 GB)
- N8N Builder (~2,600 files, ~0.64 GB)

Total: ~12,000+ files, ~5.7 GB of BD intelligence data

Run with:
    python Engine8_Knowledge/scripts/index_all_data.py --all --force --lightrag

Options:
    --all           Index everything (all three projects)
    --dashboard     Index dashboard JSON files only
    --csv           Index CSV files from Engine2
    --outputs       Index output JSON files
    --external      Index external projects only (Data-Scraper, N8N Builder)
    --force         Force recreate all collections
    --lightrag      Also populate LightRAG knowledge graph
    --stats         Show collection stats after indexing
    --dry-run       Show what would be indexed without indexing
"""

import os
import sys
import json
import csv
import logging
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Generator
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('FullIndexer')

# =========================================
# PROJECT PATHS
# =========================================

PROJECT_ROOT = Path(__file__).parent.parent.parent
DASHBOARD_DATA = PROJECT_ROOT / "dashboard" / "public" / "data"
ENGINE2_DATA = PROJECT_ROOT / "Engine2_ProgramMapping" / "data"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
BULLHORN_DB = PROJECT_ROOT / "Engine7_BullhornETL" / "data" / "bullhorn_intelligence.db"

# External project paths
DATA_SCRAPER_ROOT = Path(r"C:\data-scraper\data-scraper")
N8N_BUILDER_ROOT = Path(r"C:\N8N Builder")

# =========================================
# INDEXING CONFIGURATION
# =========================================

# Maximum records per file (for memory management)
MAX_RECORDS_PER_FILE = 50000
# Batch size for Qdrant upserts (smaller batches for server mode to avoid timeouts)
# Reduced to 10 to handle slow Qdrant server performance
BATCH_SIZE = 10
# Skip files larger than this (in MB) - can be overridden
MAX_FILE_SIZE_MB = 100

# Files to skip (too large or not useful for search)
SKIP_FILES = {
    'FY(All)_All_Contracts_Delta',  # 4.6GB - too large
    'package-lock.json',
    'node_modules',
    '.git',
}

# =========================================
# BD-AUTOMATION-ENGINE SOURCES
# =========================================

DASHBOARD_SOURCES = {
    'jobs': {'file': 'jobs_enriched.json', 'collection': 'jobs', 'key_field': 'title'},
    'contacts': {'file': 'contacts_classified.json', 'collection': 'contacts', 'key_field': 'name', 'nested_key': 'by_tier'},
    'programs': {'file': 'programs_enriched.json', 'collection': 'programs', 'key_field': 'name'},
    'past_performance': {'file': 'past_performance.json', 'collection': 'documents', 'key_field': 'prime_contractor', 'doc_type': 'past_performance'},
    'call_notes': {'file': 'call_notes_summary.json', 'collection': 'activities', 'key_field': 'contact_name'},
    'call_notes_contacts': {'file': 'call_notes_contacts.json', 'collection': 'activities', 'key_field': 'name'},
    'call_notes_primes': {'file': 'call_notes_primes.json', 'collection': 'documents', 'key_field': 'name', 'doc_type': 'prime_analysis'},
    'call_notes_programs': {'file': 'call_notes_programs.json', 'collection': 'documents', 'key_field': 'name', 'doc_type': 'program_analysis'},
    'placements': {'file': 'placements.json', 'collection': 'documents', 'key_field': 'candidate', 'doc_type': 'placement'},
    'contractors': {'file': 'contractors_enriched.json', 'collection': 'documents', 'key_field': 'name', 'doc_type': 'contractor_profile'},
    'prime_org_chart': {'file': 'prime_org_chart.json', 'collection': 'documents', 'key_field': 'name', 'doc_type': 'prime_org'},
    'contact_org_chart': {'file': 'contact_org_chart.json', 'collection': 'contacts', 'key_field': 'name', 'nested_key': 'tiers'},
}

CSV_SOURCES = {
    'federal_programs_master': {'file': 'Federal Programs MASTER V4.csv', 'collection': 'programs', 'key_field': 'Program Name'},
    'insight_jobs': {'file': 'Insight Global Jobs - Program Mapped (Dec 2025).csv', 'collection': 'jobs', 'key_field': 'Job Title'},
    'bd_opportunities': {'file': 'BD Opportunities.csv', 'collection': 'documents', 'key_field': 'Opportunity Name', 'doc_type': 'opportunity'},
    'contractors_db': {'file': 'Contractors Database.csv', 'collection': 'documents', 'key_field': 'Company Name', 'doc_type': 'contractor'},
    'contract_vehicles': {'file': 'Contract_Vehicles.csv', 'collection': 'documents', 'key_field': 'Vehicle Name', 'doc_type': 'contract_vehicle'},
}

# =========================================
# DATA-SCRAPER SOURCES (Comprehensive)
# =========================================

DATA_SCRAPER_SOURCES = {
    # BD Databases - High Priority
    'bd_databases': {
        'path': 'data/output/bd_databases',
        'pattern': '*.csv',
        'collection': 'documents',
        'key_field': 'name',
        'doc_type': 'bd_database',
        'recursive': True,
    },
    # Bullhorn Analysis - Critical
    'bullhorn_master': {
        'path': 'data/output/bullhorn_analysis',
        'files': ['primes_master.csv', 'programs_master.csv', 'contacts_master.csv', 'jobs_master.csv'],
        'collection': 'documents',
        'key_field': 'name',
        'doc_type': 'bullhorn_master',
    },
    'bullhorn_intelligence': {
        'path': 'data/output/bullhorn_analysis',
        'files': ['CONTACT_INTELLIGENCE_DETAILED.csv', 'PRIME_INTELLIGENCE_DETAILED.csv',
                  'PROGRAM_INTELLIGENCE_DETAILED.csv', 'JOBS_ENRICHED.csv', 'JOBS_INTELLIGENCE_MAPPED.csv',
                  'ORG_CHART_DATA.csv', 'PROGRAM_HIERARCHY.csv'],
        'collection': 'documents',
        'key_field': 'name',
        'doc_type': 'bullhorn_intelligence',
    },
    'bullhorn_notes': {
        'path': 'data/output/bullhorn_analysis/notes_intelligence',
        'pattern': '*.csv',
        'collection': 'activities',
        'key_field': 'contact',
        'doc_type': 'bullhorn_notes',
        'chunk_large': True,  # Handle 75MB file in chunks
    },
    'bullhorn_advanced': {
        'path': 'data/output/bullhorn_analysis/advanced_intelligence',
        'pattern': '*.csv',
        'collection': 'documents',
        'key_field': 'name',
        'doc_type': 'bullhorn_advanced',
    },
    'bullhorn_enriched': {
        'path': 'data/output/bullhorn_analysis/enriched',
        'pattern': '*.csv',
        'collection': 'documents',
        'key_field': 'name',
        'doc_type': 'bullhorn_enriched',
    },
    'bullhorn_sqlite': {
        'path': 'data/output/bullhorn_analysis/bullhorn_past_performance.db',
        'type': 'sqlite',
        'tables': ['past_performance', 'primes', 'programs', 'contacts'],
    },
    # Program Intelligence
    'program_intel': {
        'path': 'data/output/program_intelligence',
        'pattern': '*.csv',
        'collection': 'programs',
        'key_field': 'program',
        'doc_type': 'program_intel',
    },
    # Task Orders
    'task_orders': {
        'path': 'data/output/task_orders',
        'pattern': '*.csv',
        'collection': 'documents',
        'key_field': 'contract',
        'doc_type': 'task_order',
    },
    # Subaward Intelligence
    'subawards': {
        'path': 'data/output/subaward_intelligence',
        'pattern': '*.csv',
        'collection': 'documents',
        'key_field': 'subcontractor',
        'doc_type': 'subaward',
    },
    # Root Output Files
    'output_root': {
        'path': 'data/output',
        'files': ['bd_master_target_list.csv', 'bd_all_scored_targets.csv', 'bd_priority_targets.csv',
                  'bd_large_dod_contracts.csv', 'bd_it_services_targets.csv', 'bd_hot_hiring_programs.csv',
                  'bd_competitor_contract_presence.csv', 'Federal_Programs_Enriched.csv',
                  'phase1_tango_contracts.csv', 'phase2_competitor_awards.csv', 'phase3_opportunities_tango.csv',
                  'phase3_solicitations_only.csv', 'phase3_recompete_opportunities.csv',
                  'phase4_new_high_value_contracts.csv', 'phase6_org_intelligence.csv'],
        'collection': 'documents',
        'key_field': 'name',
        'doc_type': 'bd_output',
    },
    'output_json': {
        'path': 'data/output',
        'files': ['standardized_jobs_2026-01-26.json', 'hub_jobs_2026-01-26.json'],
        'collection': 'jobs',
        'key_field': 'title',
    },
    # DoD Budget Data (JSON) - Large volume
    'dod_budget_json': {
        'path': 'data/external/dod-budget-data/1-json-procurement-lineitems',
        'pattern': '*.json',
        'collection': 'documents',
        'key_field': 'title',
        'doc_type': 'dod_budget',
        'recursive': True,
        'max_files': 2000,  # Limit for initial indexing
    },
    # DoD Budget CSV (aggregated)
    'dod_budget_csv': {
        'path': 'data/external/dod-budget-data/2-csv-procurement-lineitems',
        'files': ['root.csv'],
        'collection': 'documents',
        'key_field': 'program',
        'doc_type': 'dod_procurement',
        'chunk_large': True,
    },
    # Input Data
    'input_programs': {
        'path': 'data/input',
        'files': ['Federal_ProgramsAll.csv', 'contact_search_list.csv', 'bd_targets.csv'],
        'collection': 'documents',
        'key_field': 'name',
        'doc_type': 'input_data',
    },
    # Knowledge Base Companies
    'knowledge_companies': {
        'path': 'knowledge/companies',
        'pattern': '*/_manifest.json',
        'collection': 'documents',
        'key_field': 'company',
        'doc_type': 'company_profile',
        'recursive': True,
    },
    # Apify Exports
    'apify_exports': {
        'path': 'data/apify_exports',
        'pattern': '*.json',
        'collection': 'jobs',
        'key_field': 'title',
    },
    # Tango API
    'tango_api': {
        'path': 'TANGO API',
        'files': ['response_1769703448578.json'],
        'collection': 'documents',
        'key_field': 'operationId',
        'doc_type': 'api_spec',
    },
}

# =========================================
# N8N BUILDER SOURCES
# =========================================

N8N_BUILDER_SOURCES = {
    # Reference Data - DIIG-CSIS
    'diig_lookup': {
        'path': 'data/reference/DIIG-CSIS-Lookup-Tables',
        'pattern': '*.csv',
        'collection': 'documents',
        'key_field': 'name',
        'doc_type': 'diig_reference',
        'recursive': True,
    },
    # Bullhorn HUMINT
    'bullhorn_humint': {
        'path': 'output/intelligence/bullhorn',
        'files': ['contacts_humint_full.json'],
        'collection': 'contacts',
        'key_field': 'name',
        'chunk_large': True,
    },
    'bullhorn_notes_n8n': {
        'path': 'output/intelligence/bullhorn/notes_deep_analysis',
        'pattern': '*.csv',
        'collection': 'activities',
        'key_field': 'contact',
        'chunk_large': True,
    },
    # Knowledge Base
    'knowledge_base': {
        'path': 'knowledge-base',
        'files': ['processed_docs.json'],
        'collection': 'documents',
        'key_field': 'title',
        'doc_type': 'knowledge_doc',
        'chunk_large': True,
    },
    # Master Contacts
    'master_contacts': {
        'path': 'data/contacts_databases/Prime_Contacts',
        'files': ['Master_All_Contacts.json'],
        'collection': 'contacts',
        'key_field': 'name',
        'chunk_large': True,
    },
    # USASpending
    'usaspending': {
        'path': 'external/usaspending-api/data',
        'pattern': '*.csv',
        'collection': 'documents',
        'key_field': 'name',
        'doc_type': 'usaspending',
        'recursive': True,
        'max_files': 500,
    },
}

# =========================================
# HELPER FUNCTIONS
# =========================================

def get_file_hash(content: str) -> str:
    """Generate hash for deduplication."""
    return hashlib.md5(content.encode()[:1000]).hexdigest()[:12]


def should_skip_file(file_path: Path) -> bool:
    """Check if file should be skipped."""
    name = file_path.name
    for skip in SKIP_FILES:
        if skip in str(file_path):
            return True
    # Skip very large files
    try:
        size_mb = file_path.stat().st_size / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            logger.warning(f"Skipping large file ({size_mb:.1f}MB): {file_path.name}")
            return True
    except OSError as e:
        logger.debug("file_stat_failed: %s", e)
    return False


def load_json_safe(file_path: Path) -> Any:
    """Load JSON file with error handling."""
    if not file_path.exists():
        return None
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            return json.load(f)
    except Exception as e:
        logger.debug(f"Failed to load JSON {file_path.name}: {e}")
        return None


def load_csv_chunked(file_path: Path, chunk_size: int = 10000) -> Generator[List[Dict], None, None]:
    """Load CSV in chunks for memory efficiency."""
    if not file_path.exists():
        return
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            chunk = []
            for row in reader:
                chunk.append(row)
                if len(chunk) >= chunk_size:
                    yield chunk
                    chunk = []
            if chunk:
                yield chunk
    except Exception as e:
        logger.debug(f"Failed to load CSV {file_path.name}: {e}")


def load_csv_full(file_path: Path, max_records: int = None) -> List[Dict]:
    """Load entire CSV file."""
    if not file_path.exists():
        return []
    try:
        records = []
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                records.append(row)
                if max_records and i >= max_records:
                    break
        return records
    except Exception as e:
        logger.debug(f"Failed to load CSV {file_path.name}: {e}")
        return []


def flatten_nested_data(data: Any, nested_key: str = None) -> List[Dict]:
    """Flatten nested JSON structures."""
    records = []
    if isinstance(data, list):
        records = data
    elif isinstance(data, dict):
        if nested_key and nested_key in data:
            nested = data[nested_key]
            if isinstance(nested, dict):
                for tier, items in nested.items():
                    if isinstance(items, list):
                        for item in items:
                            item['_tier'] = tier
                            records.append(item)
            elif isinstance(nested, list):
                records = nested
        elif 'results' in data:
            records = data['results']
        elif 'data' in data:
            records = data['data']
        elif 'items' in data:
            records = data['items']
        elif 'paths' in data:  # OpenAPI spec
            for path, methods in data.get('paths', {}).items():
                for method, details in methods.items():
                    if isinstance(details, dict):
                        details['_path'] = path
                        details['_method'] = method
                        records.append(details)
        else:
            if all(isinstance(v, dict) for v in data.values() if isinstance(v, dict)):
                for k, v in data.items():
                    if isinstance(v, dict):
                        v['_id'] = k
                        records.append(v)
            else:
                records = [data]
    return records


def record_to_content(record: Dict, key_field: str = None) -> str:
    """Convert a record to searchable text content."""
    parts = []
    priority_fields = ['name', 'title', 'description', 'summary', 'content', 'notes',
                       'Job Title', 'Program Name', 'Company Name', 'contact', 'program',
                       'prime', 'agency', 'contract', 'operationId']

    for field in priority_fields:
        if field in record and record[field]:
            parts.append(str(record[field]))

    for k, v in record.items():
        if k not in priority_fields and k not in ['id', '_id', '_tier', '_path', '_method']:
            if isinstance(v, str) and v.strip() and len(v) < 500:
                parts.append(f"{k}: {v}")
            elif isinstance(v, (int, float)):
                parts.append(f"{k}: {v}")
            elif isinstance(v, list) and v and len(v) < 10:
                parts.append(f"{k}: {', '.join(str(x) for x in v[:5])}")

    return " | ".join(parts[:25])


# =========================================
# MAIN INDEXER CLASS
# =========================================

class FullBDIndexer:
    """Comprehensive BD Data Indexer."""

    def __init__(self, store: BDKnowledgeStore = None, dry_run: bool = False, collection_filter: str = None):
        self.store = store or BDKnowledgeStore()
        self.dry_run = dry_run
        self.collection_filter = collection_filter  # Only index this collection if set
        self.stats = {
            'jobs': 0,
            'contacts': 0,
            'programs': 0,
            'documents': 0,
            'activities': 0,
            'files_processed': 0,
            'files_skipped': 0,
            'errors': 0,
        }
        self.indexed_hashes = set()  # Deduplication

    def initialize(self, force_recreate: bool = False):
        """Initialize Qdrant collections."""
        if self.dry_run:
            logger.info("[DRY RUN] Would initialize collections")
            return
        logger.info("Initializing Qdrant collections...")
        self.store.initialize_collections(force_recreate=force_recreate)

    def _index_records(self, records: List[Dict], collection: str, key_field: str,
                       doc_type: str = None, source: str = None) -> int:
        """Index records into a collection."""
        if self.dry_run:
            return len(records)

        indexed = 0
        batch = []

        for i, record in enumerate(records):
            try:
                content = record_to_content(record, key_field)
                if not content or len(content) < 10:
                    continue

                # Deduplication
                content_hash = get_file_hash(content)
                if content_hash in self.indexed_hashes:
                    continue
                self.indexed_hashes.add(content_hash)

                # Generate ID
                key_value = (record.get(key_field, '') or record.get('name', '') or
                            record.get('title', '') or record.get('id', '') or f"record_{i}")
                record_id = f"{source}_{str(key_value)[:50].replace(' ', '_').lower()}_{content_hash}"

                # Metadata
                metadata = {
                    'source': source,
                    'indexed_at': datetime.now().isoformat(),
                }
                if doc_type:
                    metadata['doc_type'] = doc_type

                for k, v in record.items():
                    if isinstance(v, (str, int, float, bool)) and k not in ['content', 'text']:
                        metadata[k] = v
                    elif isinstance(v, list) and all(isinstance(x, str) for x in v):
                        metadata[k] = v[:10]

                batch.append({
                    'id': record_id,
                    'content': content,
                    'title': record.get('title', record.get('name', key_value)),
                    'name': record.get('name', record.get('title', key_value)),
                    **metadata
                })

                if len(batch) >= BATCH_SIZE:
                    self._flush_batch(batch, collection)
                    indexed += len(batch)
                    batch = []

            except Exception as e:
                logger.debug(f"Failed to index record: {e}")
                self.stats['errors'] += 1

        if batch:
            self._flush_batch(batch, collection)
            indexed += len(batch)

        return indexed

    def _flush_batch(self, batch: List[Dict], collection: str):
        """Flush a batch of records to Qdrant."""
        # Skip if collection filter is set and doesn't match
        if self.collection_filter and collection != self.collection_filter:
            return

        try:
            if collection == 'jobs':
                self.store.index_jobs(batch)
            elif collection == 'contacts':
                self.store.index_contacts(batch)
            elif collection == 'programs':
                self.store.index_programs(batch)
            elif collection == 'documents':
                self.store.index_documents(batch)
            elif collection == 'activities':
                self.store.index_activities(batch)
        except Exception as e:
            logger.error(f"Failed to flush batch to {collection}: {e}")
            self.stats['errors'] += 1

    def index_dashboard(self):
        """Index BD-Automation-Engine dashboard data."""
        logger.info("\n" + "="*60)
        logger.info("INDEXING BD-AUTOMATION-ENGINE DASHBOARD")
        logger.info("="*60)

        for name, config in DASHBOARD_SOURCES.items():
            file_path = DASHBOARD_DATA / config['file']
            if not file_path.exists():
                continue

            data = load_json_safe(file_path)
            if not data:
                continue

            records = flatten_nested_data(data, config.get('nested_key'))
            logger.info(f"  {name}: {len(records)} records → {config['collection']}")

            indexed = self._index_records(records, config['collection'], config['key_field'],
                                         config.get('doc_type'), f"dashboard_{name}")
            self.stats[config['collection']] += indexed
            self.stats['files_processed'] += 1

    def index_csv_data(self):
        """Index Engine2 CSV data."""
        logger.info("\n" + "="*60)
        logger.info("INDEXING ENGINE2 CSV DATA")
        logger.info("="*60)

        for name, config in CSV_SOURCES.items():
            file_path = ENGINE2_DATA / config['file']
            if not file_path.exists():
                continue

            records = load_csv_full(file_path, MAX_RECORDS_PER_FILE)
            if not records:
                continue

            logger.info(f"  {name}: {len(records)} records → {config['collection']}")

            indexed = self._index_records(records, config['collection'], config['key_field'],
                                         config.get('doc_type'), f"engine2_{name}")
            self.stats[config['collection']] += indexed
            self.stats['files_processed'] += 1

    def index_data_scraper(self):
        """Index Data-Scraper project data."""
        logger.info("\n" + "="*60)
        logger.info("INDEXING DATA-SCRAPER PROJECT")
        logger.info(f"Path: {DATA_SCRAPER_ROOT}")
        logger.info("="*60)

        if not DATA_SCRAPER_ROOT.exists():
            logger.warning("Data-Scraper project not found")
            return

        for source_name, config in DATA_SCRAPER_SOURCES.items():
            self._index_source(DATA_SCRAPER_ROOT, source_name, config, "data_scraper")

    def index_n8n_builder(self):
        """Index N8N Builder project data."""
        logger.info("\n" + "="*60)
        logger.info("INDEXING N8N BUILDER PROJECT")
        logger.info(f"Path: {N8N_BUILDER_ROOT}")
        logger.info("="*60)

        if not N8N_BUILDER_ROOT.exists():
            logger.warning("N8N Builder project not found")
            return

        for source_name, config in N8N_BUILDER_SOURCES.items():
            self._index_source(N8N_BUILDER_ROOT, source_name, config, "n8n_builder")

    def _index_source(self, root: Path, source_name: str, config: Dict, prefix: str):
        """Index a data source configuration."""
        source_path = root / config['path']

        # Handle SQLite databases
        if config.get('type') == 'sqlite':
            if source_path.exists():
                self._index_sqlite(source_path, config.get('tables', []), f"{prefix}_{source_name}")
            return

        # Handle specific files
        if 'files' in config:
            for filename in config['files']:
                file_path = source_path / filename if source_path.is_dir() else root / config['path']
                if not file_path.exists():
                    file_path = source_path.parent / filename
                if not file_path.exists():
                    continue

                self._index_file(file_path, config, f"{prefix}_{source_name}")
            return

        # Handle pattern matching
        if 'pattern' in config and source_path.exists():
            pattern = config['pattern']
            recursive = config.get('recursive', False)
            max_files = config.get('max_files', 10000)

            files = list(source_path.rglob(pattern) if recursive else source_path.glob(pattern))
            files = [f for f in files if f.is_file() and not should_skip_file(f)][:max_files]

            if files:
                logger.info(f"  {source_name}: {len(files)} files found")
                for file_path in files:
                    self._index_file(file_path, config, f"{prefix}_{source_name}")

    def _index_file(self, file_path: Path, config: Dict, source: str):
        """Index a single file."""
        if should_skip_file(file_path):
            self.stats['files_skipped'] += 1
            return

        try:
            suffix = file_path.suffix.lower()
            collection = config['collection']
            key_field = config['key_field']
            doc_type = config.get('doc_type')
            chunk_large = config.get('chunk_large', False)

            # Get file size
            try:
                size_mb = file_path.stat().st_size / (1024 * 1024)
            except OSError as e:
                logger.debug("file_stat_failed: %s", e)
                size_mb = 0

            if suffix == '.json':
                data = load_json_safe(file_path)
                if data:
                    records = flatten_nested_data(data)[:MAX_RECORDS_PER_FILE]
                    if records:
                        indexed = self._index_records(records, collection, key_field, doc_type,
                                                     f"{source}_{file_path.stem}")
                        self.stats[collection] += indexed
                        self.stats['files_processed'] += 1
                        if size_mb > 1:
                            logger.info(f"    ✓ {file_path.name} ({size_mb:.1f}MB): {indexed} records")

            elif suffix == '.csv':
                if chunk_large and size_mb > 10:
                    # Process large CSVs in chunks
                    total_indexed = 0
                    for chunk in load_csv_chunked(file_path):
                        indexed = self._index_records(chunk, collection, key_field, doc_type,
                                                     f"{source}_{file_path.stem}")
                        total_indexed += indexed
                        self.stats[collection] += indexed
                    if total_indexed:
                        logger.info(f"    ✓ {file_path.name} ({size_mb:.1f}MB): {total_indexed} records (chunked)")
                    self.stats['files_processed'] += 1
                else:
                    records = load_csv_full(file_path, MAX_RECORDS_PER_FILE)
                    if records:
                        indexed = self._index_records(records, collection, key_field, doc_type,
                                                     f"{source}_{file_path.stem}")
                        self.stats[collection] += indexed
                        self.stats['files_processed'] += 1
                        if size_mb > 1:
                            logger.info(f"    ✓ {file_path.name} ({size_mb:.1f}MB): {indexed} records")

        except Exception as e:
            logger.debug(f"Failed to index {file_path.name}: {e}")
            self.stats['errors'] += 1

    def _index_sqlite(self, db_path: Path, tables: List[str], source: str):
        """Index SQLite database."""
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get available tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            available_tables = {row[0] for row in cursor.fetchall()}

            tables_to_index = [t for t in tables if t in available_tables] if tables else list(available_tables)

            for table in tables_to_index:
                try:
                    cursor.execute(f"SELECT * FROM {table} LIMIT {MAX_RECORDS_PER_FILE}")
                    rows = cursor.fetchall()
                    records = [dict(row) for row in rows]

                    if records:
                        collection = 'documents' if table not in ['contacts', 'jobs', 'activities'] else table
                        indexed = self._index_records(records, collection, 'name', f"sqlite_{table}",
                                                     f"{source}_{table}")
                        self.stats[collection] += indexed
                        logger.info(f"    ✓ SQLite.{table}: {indexed} records")
                except Exception as e:
                    logger.debug(f"Failed to index table {table}: {e}")

            conn.close()
            self.stats['files_processed'] += 1

        except Exception as e:
            logger.error(f"Failed to index SQLite {db_path}: {e}")
            self.stats['errors'] += 1

    def index_all(self, force_recreate: bool = False):
        """Index ALL data sources from all projects."""
        start = datetime.now()

        self.initialize(force_recreate=force_recreate)

        # BD-Automation-Engine
        self.index_dashboard()
        self.index_csv_data()

        # External Projects
        self.index_data_scraper()
        self.index_n8n_builder()

        duration = (datetime.now() - start).total_seconds()

        self.print_summary()
        print(f"\nTotal time: {duration:.1f} seconds ({duration/60:.1f} minutes)")

    def print_summary(self):
        """Print indexing summary."""
        print("\n" + "="*60)
        print("INDEXING COMPLETE - SUMMARY")
        print("="*60)

        total = sum(v for k, v in self.stats.items() if k not in ['errors', 'files_processed', 'files_skipped'])

        print("\nRecords Indexed by Collection:")
        for collection in ['jobs', 'contacts', 'programs', 'documents', 'activities']:
            count = self.stats.get(collection, 0)
            print(f"  {collection:15} : {count:,} records")

        print("-"*60)
        print(f"  {'TOTAL RECORDS':15} : {total:,}")
        print(f"  {'FILES PROCESSED':15} : {self.stats['files_processed']:,}")
        print(f"  {'FILES SKIPPED':15} : {self.stats['files_skipped']:,}")
        print(f"  {'ERRORS':15} : {self.stats['errors']:,}")
        print("="*60)

        # Get actual Qdrant stats
        if not self.dry_run:
            print("\nQdrant Collection Status:")
            try:
                stats = self.store.get_collection_stats()
                for name, stat in stats.items():
                    if 'error' in stat:
                        print(f"  {name}: ERROR")
                    else:
                        count = stat.get('points_count', stat.get('vectors_count', 0))
                        print(f"  {name}: {count:,} vectors")
            except Exception as e:
                logger.error("qdrant_stats_fetch_failed: %s", e)
                print("  (Could not fetch Qdrant stats)")


# =========================================
# CLI
# =========================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Full BD Data Indexer - All Projects')
    parser.add_argument('--all', action='store_true', help='Index ALL data from all projects')
    parser.add_argument('--dashboard', action='store_true', help='Index dashboard JSON only')
    parser.add_argument('--csv', action='store_true', help='Index CSV files only')
    parser.add_argument('--external', action='store_true', help='Index external projects only')
    parser.add_argument('--data-scraper', action='store_true', help='Index Data-Scraper only')
    parser.add_argument('--n8n', action='store_true', help='Index N8N Builder only')
    parser.add_argument('--force', action='store_true', help='Force recreate collections')
    parser.add_argument('--lightrag', action='store_true', help='Also populate LightRAG')
    parser.add_argument('--stats', action='store_true', help='Show stats only')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be indexed')
    parser.add_argument('--collection', type=str, choices=['jobs', 'contacts', 'programs', 'documents', 'activities'],
                        help='Index only this collection (for parallel processing)')
    parser.add_argument('--qdrant-path', type=str, help='Custom Qdrant storage path (for parallel instances)')
    parser.add_argument('--qdrant-url', type=str, default=None,
                        help='Qdrant server URL (e.g., http://localhost:6333) for parallel processing')

    args = parser.parse_args()

    # Create store with custom path or URL if specified
    store = None
    if args.qdrant_url:
        from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore
        store = BDKnowledgeStore(url=args.qdrant_url)
    elif args.qdrant_path:
        from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore
        store = BDKnowledgeStore(path=args.qdrant_path)

    indexer = FullBDIndexer(store=store, dry_run=args.dry_run, collection_filter=args.collection)

    if args.stats:
        try:
            stats = indexer.store.get_collection_stats()
            print("\n" + "="*60)
            print("CURRENT QDRANT COLLECTION STATISTICS")
            print("="*60)
            total = 0
            for name, stat in stats.items():
                if 'error' in stat:
                    print(f"  {name:15}: ERROR - {stat.get('error', 'Unknown')}")
                else:
                    count = stat.get('points_count', stat.get('vectors_count', 0))
                    total += count
                    print(f"  {name:15}: {count:,} vectors")
            print("-"*60)
            print(f"  {'TOTAL':15}: {total:,} vectors")
        except Exception as e:
            print(f"Failed to get stats: {e}")
        return

    # Determine what to index
    if args.all or not any([args.dashboard, args.csv, args.external, args.data_scraper, args.n8n]):
        indexer.index_all(force_recreate=args.force)
    else:
        indexer.initialize(force_recreate=args.force)

        if args.dashboard:
            indexer.index_dashboard()
        if args.csv:
            indexer.index_csv_data()
        if args.external or args.data_scraper:
            indexer.index_data_scraper()
        if args.external or args.n8n:
            indexer.index_n8n_builder()

        indexer.print_summary()

    # Optionally populate LightRAG
    if args.lightrag and not args.dry_run:
        print("\n" + "="*60)
        print("POPULATING LIGHTRAG KNOWLEDGE GRAPH")
        print("="*60)
        try:
            from Engine8_Knowledge.scripts.populate_lightrag import main as populate_lightrag
            populate_lightrag()
        except Exception as e:
            logger.error(f"LightRAG population failed: {e}")
            print("\nTo populate LightRAG manually:")
            print("  1. Start Hub API: python Engine8_Knowledge/api.py")
            print("  2. Run: python Engine8_Knowledge/scripts/populate_lightrag.py")


if __name__ == '__main__':
    main()
