"""
BD Knowledge Store - Unified Vector Database for BD Intelligence
Uses Qdrant in embedded mode for zero-setup deployment.
"""

import os
import sys
import json
import hashlib
import logging
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance, VectorParams, PointStruct,
        Filter, FieldCondition, MatchValue, MatchAny,
        UpdateStatus, CollectionStatus
    )
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    print("Warning: qdrant-client not installed. Run: pip install qdrant-client")

try:
    import openai
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("Warning: openai not installed. Run: pip install openai")

from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('BDKnowledgeStore')

# =========================================
# CONFIGURATION
# =========================================

PROJECT_ROOT = Path(__file__).parent.parent.parent
DEFAULT_QDRANT_PATH = PROJECT_ROOT / "Engine8_Knowledge" / "data" / "qdrant"
DEFAULT_MODEL = "text-embedding-3-small"  # OpenAI, 1536 dimensions
EMBEDDING_DIMENSION = 1536


@dataclass
class CollectionConfig:
    """Configuration for a Qdrant collection."""
    name: str
    description: str
    vector_size: int = EMBEDDING_DIMENSION
    distance: str = "Cosine"

    # Text fields to embed
    text_fields: List[str] = field(default_factory=list)

    # Payload schema
    indexed_fields: List[str] = field(default_factory=list)


# Collection definitions for BD data types
COLLECTION_CONFIGS = {
    'jobs': CollectionConfig(
        name='jobs',
        description='Job postings with program mappings and BD scores',
        text_fields=['title', 'company', 'location', 'program_name', 'clearance'],
        indexed_fields=['company', 'program_name', 'clearance', 'bd_priority', 'source']
    ),
    'contacts': CollectionConfig(
        name='contacts',
        description='Contacts with tier classification and company affiliation',
        text_fields=['name', 'first_name', 'last_name', 'title', 'company', 'program', 'notes'],
        indexed_fields=['company', 'tier', 'program', 'bd_priority', 'source_db']
    ),
    'programs': CollectionConfig(
        name='programs',
        description='Federal programs and contracts',
        text_fields=['name', 'prime_contractor', 'location', 'mission_area', 'notes'],
        indexed_fields=['prime_contractor', 'status', 'contract_vehicle', 'bd_priority']
    ),
    'documents': CollectionConfig(
        name='documents',
        description='Processed documents, briefings, and exports',
        text_fields=['content', 'title', 'summary'],
        indexed_fields=['doc_type', 'source_file', 'tags', 'created_date']
    ),
    'activities': CollectionConfig(
        name='activities',
        description='Bullhorn call notes, activities, and interactions',
        text_fields=['content', 'subject', 'contact_name', 'company_name'],
        indexed_fields=['activity_type', 'contact_id', 'company', 'date']
    ),
    'bullhorn_notes': CollectionConfig(
        name='bullhorn_notes',
        description='Bullhorn CRM call notes with hybrid (dense + sparse) vectors',
        text_fields=['note_body', 'comments', 'about', 'action'],
        indexed_fields=['note_type', 'noteType', 'personReference', '_source']
    ),
    'federal_contracts': CollectionConfig(
        name='federal_contracts',
        description='Federal contract awards, vehicles, and modifications',
        text_fields=['title', 'description', 'agency', 'contractor'],
        indexed_fields=['agency', 'contractor', 'contract_vehicle', 'status']
    ),
    'intelligence_reports': CollectionConfig(
        name='intelligence_reports',
        description='BD intelligence reports, HUMINT briefings, analysis docs',
        text_fields=['content', 'title', 'summary', 'source'],
        indexed_fields=['report_type', 'classification', 'source', 'date']
    ),
    'opportunities': CollectionConfig(
        name='opportunities',
        description='BD pipeline opportunities and capture tracking',
        text_fields=['title', 'description', 'program', 'agency', 'prime'],
        indexed_fields=['status', 'priority', 'agency', 'program']
    ),
}


@dataclass
class SearchResult:
    """Result from a semantic search."""
    id: str
    score: float
    payload: Dict[str, Any]
    collection: str

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'score': self.score,
            'payload': self.payload,
            'collection': self.collection
        }


# =========================================
# KNOWLEDGE STORE CLASS
# =========================================

class BDKnowledgeStore:
    """
    Unified vector store for BD intelligence data.

    Uses Qdrant in embedded mode (file-based) for zero-setup deployment.
    Supports semantic search across jobs, contacts, programs, documents, and activities.
    """

    def __init__(
        self,
        path: Optional[str] = None,
        model_name: str = DEFAULT_MODEL,
        in_memory: bool = False,
        url: Optional[str] = None
    ):
        """
        Initialize the knowledge store.

        Args:
            path: Path to Qdrant data directory. Uses default if None.
            model_name: Sentence transformer model for embeddings.
            in_memory: If True, use in-memory storage (for testing).
            url: Qdrant server URL (e.g., http://localhost:6333). If set, uses server mode.
        """
        if not QDRANT_AVAILABLE:
            raise ImportError("qdrant-client is required. Install with: pip install qdrant-client")

        if not EMBEDDINGS_AVAILABLE:
            raise ImportError("openai is required. Install with: pip install openai")

        # Initialize Qdrant client
        if url:
            # Server mode - connects to Qdrant server (supports concurrent writes)
            # Use longer timeout (600s) for large batch operations with slow servers
            self.client = QdrantClient(url=url, timeout=600)
            self.path = None
            logger.info(f"Connected to Qdrant server at: {url}")
        elif in_memory:
            self.client = QdrantClient(":memory:")
            self.path = None
            logger.info("Initialized Qdrant in-memory mode")
        else:
            # Local file mode (embedded)
            self.path = Path(path) if path else DEFAULT_QDRANT_PATH
            self.path.mkdir(parents=True, exist_ok=True)
            self.client = QdrantClient(path=str(self.path))
            logger.info(f"Initialized Qdrant at: {self.path}")

        # Initialize OpenAI client for embeddings
        logger.info(f"Using OpenAI embedding model: {model_name}")
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model_name = model_name

        # Collection configs
        self.configs = COLLECTION_CONFIGS

    def initialize_collections(self, force_recreate: bool = False) -> Dict[str, bool]:
        """
        Create all collections if they don't exist.

        Args:
            force_recreate: If True, delete and recreate existing collections.

        Returns:
            Dict mapping collection name to creation success status.
        """
        results = {}

        for name, config in self.configs.items():
            try:
                # Check if collection exists
                collections = self.client.get_collections().collections
                exists = any(c.name == name for c in collections)

                if exists and force_recreate:
                    self.client.delete_collection(name)
                    logger.info(f"Deleted existing collection: {name}")
                    exists = False

                if not exists:
                    # Create collection
                    self.client.create_collection(
                        collection_name=name,
                        vectors_config=VectorParams(
                            size=config.vector_size,
                            distance=Distance.COSINE
                        )
                    )
                    logger.info(f"Created collection: {name} ({config.description})")
                    results[name] = True
                else:
                    logger.info(f"Collection exists: {name}")
                    results[name] = True

            except Exception as e:
                logger.error(f"Failed to create collection {name}: {e}")
                results[name] = False

        return results

    def get_collection_stats(self) -> Dict[str, Dict]:
        """Get statistics for all collections."""
        stats = {}

        for name in self.configs.keys():
            try:
                info = self.client.get_collection(name)
                # Handle different qdrant-client versions
                points_count = getattr(info, 'points_count', 0)
                vectors_count = getattr(info, 'vectors_count', points_count)
                indexed_count = getattr(info, 'indexed_vectors_count', vectors_count)
                status = getattr(info.status, 'name', str(info.status)) if hasattr(info, 'status') else 'unknown'

                stats[name] = {
                    'vectors_count': vectors_count,
                    'indexed_vectors_count': indexed_count,
                    'points_count': points_count,
                    'status': status
                }
            except Exception as e:
                stats[name] = {'error': str(e)}

        return stats

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI API with retry."""
        if not text or not text.strip():
            text = "empty"
        try:
            return self._call_embedding_api(text)
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            return [0.0] * EMBEDDING_DIMENSION

    @staticmethod
    def _init_embedding_retry():
        """Lazy-load tenacity decorator."""
        try:
            from config.resilience import with_embedding_retry
            return with_embedding_retry
        except ImportError:
            return lambda f: f  # no-op if tenacity missing

    def _call_embedding_api(self, text: str) -> List[float]:
        """Call OpenAI embedding API with tenacity retry."""
        decorator = self._init_embedding_retry()

        @decorator
        def _do_call():
            response = self.openai_client.embeddings.create(
                model=self.model_name,
                input=text,
            )
            return response.data[0].embedding

        return _do_call()

    def _generate_text_for_embedding(self, data: Dict, config: CollectionConfig) -> str:
        """Generate concatenated text for embedding from data fields."""
        parts = []
        for field in config.text_fields:
            value = data.get(field, '')
            if value and isinstance(value, str):
                parts.append(value)
            elif value and isinstance(value, list):
                parts.append(' '.join(str(v) for v in value))
        return ' '.join(parts)

    def _generate_point_id(self, data: Dict, collection: str) -> str:
        """Generate a unique point ID (UUID format) from data."""
        # Use existing ID if available and it's a valid UUID
        if 'id' in data:
            existing_id = str(data['id'])
            try:
                # Try to parse as UUID - if valid, use it
                uuid.UUID(existing_id)
                return existing_id
            except ValueError:
                # Not a valid UUID, generate one from this ID
                pass

        # Generate deterministic UUID from content
        # Use UUID5 with a namespace based on collection name
        namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # Standard namespace
        content = f"{collection}:{json.dumps(data, sort_keys=True)}"
        return str(uuid.uuid5(namespace, content))

    # =========================================
    # INDEXING METHODS
    # =========================================

    def index_jobs(self, jobs: List[Dict], batch_size: int = 100) -> Tuple[int, int]:
        """
        Index job postings with embeddings.

        Args:
            jobs: List of job dictionaries.
            batch_size: Number of jobs to index per batch.

        Returns:
            Tuple of (indexed_count, error_count).
        """
        return self._index_data('jobs', jobs, batch_size)

    def index_contacts(self, contacts: List[Dict], batch_size: int = 100) -> Tuple[int, int]:
        """
        Index contacts with embeddings.

        Args:
            contacts: List of contact dictionaries.
            batch_size: Number of contacts to index per batch.

        Returns:
            Tuple of (indexed_count, error_count).
        """
        return self._index_data('contacts', contacts, batch_size)

    def index_programs(self, programs: List[Dict], batch_size: int = 100) -> Tuple[int, int]:
        """
        Index federal programs with embeddings.

        Args:
            programs: List of program dictionaries.
            batch_size: Number of programs to index per batch.

        Returns:
            Tuple of (indexed_count, error_count).
        """
        return self._index_data('programs', programs, batch_size)

    def index_documents(self, documents: List[Dict], batch_size: int = 50) -> Tuple[int, int]:
        """
        Index documents with embeddings.

        Args:
            documents: List of document dictionaries with 'content' field.
            batch_size: Number of documents to index per batch.

        Returns:
            Tuple of (indexed_count, error_count).
        """
        return self._index_data('documents', documents, batch_size)

    def index_activities(self, activities: List[Dict], batch_size: int = 100) -> Tuple[int, int]:
        """
        Index activities (call notes, interactions) with embeddings.

        Args:
            activities: List of activity dictionaries.
            batch_size: Number of activities to index per batch.

        Returns:
            Tuple of (indexed_count, error_count).
        """
        return self._index_data('activities', activities, batch_size)

    def _index_data(
        self,
        collection: str,
        data: List[Dict],
        batch_size: int = 100
    ) -> Tuple[int, int]:
        """
        Generic indexing method for any collection.

        Args:
            collection: Collection name.
            data: List of data dictionaries.
            batch_size: Batch size for indexing.

        Returns:
            Tuple of (indexed_count, error_count).
        """
        if collection not in self.configs:
            raise ValueError(f"Unknown collection: {collection}")

        config = self.configs[collection]
        indexed = 0
        errors = 0

        # Process in batches
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            points = []

            for item in batch:
                try:
                    # Generate embedding text
                    text = self._generate_text_for_embedding(item, config)

                    # Generate embedding
                    embedding = self._generate_embedding(text)

                    # Generate point ID
                    point_id = self._generate_point_id(item, collection)

                    # Create payload (include all data plus metadata)
                    payload = {
                        **item,
                        '_indexed_at': datetime.now().isoformat(),
                        '_embedding_model': self.model_name
                    }

                    # Create point
                    point = PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=payload
                    )
                    points.append(point)

                except Exception as e:
                    logger.warning(f"Failed to process item: {e}")
                    errors += 1

            # Upsert batch
            if points:
                try:
                    self.client.upsert(
                        collection_name=collection,
                        points=points
                    )
                    indexed += len(points)
                    logger.info(f"Indexed {indexed}/{len(data)} to {collection}")
                except Exception as e:
                    logger.error(f"Failed to upsert batch: {e}")
                    errors += len(points)

        logger.info(f"Completed indexing {collection}: {indexed} indexed, {errors} errors")
        return indexed, errors

    # =========================================
    # SEARCH METHODS
    # =========================================

    def search(
        self,
        query: str,
        collection: str,
        limit: int = 10,
        score_threshold: float = 0.0,
        filters: Optional[Dict] = None
    ) -> List[SearchResult]:
        """
        Semantic search across a collection.

        Args:
            query: Natural language query.
            collection: Collection to search.
            limit: Maximum results to return.
            score_threshold: Minimum similarity score (0-1).
            filters: Optional filter conditions.

        Returns:
            List of SearchResult objects.
        """
        if collection not in self.configs:
            raise ValueError(f"Unknown collection: {collection}")

        # Generate query embedding
        query_embedding = self._generate_embedding(query)

        # Build filter if provided
        qdrant_filter = None
        if filters:
            conditions = []
            for field, value in filters.items():
                if isinstance(value, list):
                    conditions.append(FieldCondition(
                        key=field,
                        match=MatchAny(any=value)
                    ))
                else:
                    conditions.append(FieldCondition(
                        key=field,
                        match=MatchValue(value=value)
                    ))
            qdrant_filter = Filter(must=conditions)

        # Execute search using query_points (newer API)
        results = self.client.query_points(
            collection_name=collection,
            query=query_embedding,
            query_filter=qdrant_filter,
            limit=limit,
            score_threshold=score_threshold if score_threshold > 0 else None
        )

        # Convert to SearchResult objects
        return [
            SearchResult(
                id=str(r.id),
                score=r.score,
                payload=r.payload,
                collection=collection
            )
            for r in results.points
        ]

    def search_all(
        self,
        query: str,
        limit_per_collection: int = 5,
        score_threshold: float = 0.3,
        collections: Optional[List[str]] = None
    ) -> Dict[str, List[SearchResult]]:
        """
        Search across all (or specified) collections.

        Args:
            query: Natural language query.
            limit_per_collection: Max results per collection.
            score_threshold: Minimum similarity score.
            collections: Specific collections to search (all if None).

        Returns:
            Dict mapping collection name to search results.
        """
        target_collections = collections or list(self.configs.keys())
        results = {}

        for collection in target_collections:
            try:
                results[collection] = self.search(
                    query=query,
                    collection=collection,
                    limit=limit_per_collection,
                    score_threshold=score_threshold
                )
            except Exception as e:
                logger.warning(f"Search failed for {collection}: {e}")
                results[collection] = []

        return results

    def find_similar(
        self,
        item_id: str,
        collection: str,
        limit: int = 10,
        score_threshold: float = 0.5
    ) -> List[SearchResult]:
        """
        Find similar items to a given item.

        Args:
            item_id: ID of the source item.
            collection: Collection containing the item.
            limit: Maximum results to return.
            score_threshold: Minimum similarity score.

        Returns:
            List of similar items.
        """
        # Get the original item
        items = self.client.retrieve(
            collection_name=collection,
            ids=[item_id],
            with_vectors=True
        )

        if not items:
            logger.warning(f"Item not found: {item_id} in {collection}")
            return []

        # Search using the item's vector (query_points API)
        results = self.client.query_points(
            collection_name=collection,
            query=items[0].vector,
            limit=limit + 1,  # +1 to exclude self
            score_threshold=score_threshold if score_threshold > 0 else None
        )

        # Filter out the source item
        return [
            SearchResult(
                id=str(r.id),
                score=r.score,
                payload=r.payload,
                collection=collection
            )
            for r in results.points
            if str(r.id) != item_id
        ][:limit]

    def get_all(
        self,
        collection: str,
        limit: int = 10000,
        offset: int = 0
    ) -> List[SearchResult]:
        """
        Retrieve all items from a collection.

        Args:
            collection: Collection name.
            limit: Maximum items to return.
            offset: Number of items to skip.

        Returns:
            List of SearchResult objects with all payloads.
        """
        if collection not in self.configs:
            raise ValueError(f"Unknown collection: {collection}")

        # Use scroll to get all points
        results = []
        scroll_result = self.client.scroll(
            collection_name=collection,
            limit=limit,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )

        points = scroll_result[0]  # First element is the list of points

        return [
            SearchResult(
                id=str(p.id),
                score=1.0,  # No score for direct retrieval
                payload=p.payload,
                collection=collection
            )
            for p in points
        ]

    # =========================================
    # CROSS-REFERENCE METHODS
    # =========================================

    def find_contacts_for_program(
        self,
        program_name: str,
        limit: int = 20
    ) -> List[SearchResult]:
        """Find contacts associated with a program."""
        return self.search(
            query=program_name,
            collection='contacts',
            limit=limit,
            score_threshold=0.3
        )

    def find_jobs_for_program(
        self,
        program_name: str,
        limit: int = 20
    ) -> List[SearchResult]:
        """Find job postings associated with a program."""
        return self.search(
            query=program_name,
            collection='jobs',
            limit=limit,
            score_threshold=0.3
        )

    def find_contacts_at_company(
        self,
        company_name: str,
        limit: int = 20
    ) -> List[SearchResult]:
        """Find contacts at a specific company."""
        # Use both semantic search and filter
        return self.search(
            query=company_name,
            collection='contacts',
            limit=limit,
            score_threshold=0.2
        )

    def get_program_intelligence(
        self,
        program_name: str
    ) -> Dict[str, List[SearchResult]]:
        """
        Get comprehensive intelligence for a program.

        Returns related jobs, contacts, and documents.
        """
        return {
            'program': self.search('programs', program_name, limit=3),
            'jobs': self.find_jobs_for_program(program_name),
            'contacts': self.find_contacts_for_program(program_name),
            'documents': self.search('documents', program_name, limit=10)
        }


# =========================================
# CLI INTERFACE
# =========================================

def main():
    """CLI for testing the knowledge store."""
    import argparse

    parser = argparse.ArgumentParser(description='BD Knowledge Store CLI')
    parser.add_argument('--init', action='store_true', help='Initialize collections')
    parser.add_argument('--stats', action='store_true', help='Show collection statistics')
    parser.add_argument('--search', type=str, help='Search query')
    parser.add_argument('--collection', type=str, default='all', help='Collection to search')
    parser.add_argument('--limit', type=int, default=5, help='Max results')
    parser.add_argument('--in-memory', action='store_true', help='Use in-memory storage')

    args = parser.parse_args()

    # Initialize store
    store = BDKnowledgeStore(in_memory=args.in_memory)

    if args.init:
        print("Initializing collections...")
        results = store.initialize_collections()
        for name, success in results.items():
            status = "OK" if success else "FAILED"
            print(f"  {name}: {status}")

    if args.stats:
        print("\nCollection Statistics:")
        stats = store.get_collection_stats()
        for name, stat in stats.items():
            if 'error' in stat:
                print(f"  {name}: ERROR - {stat['error']}")
            else:
                print(f"  {name}: {stat['points_count']} points, status={stat['status']}")

    if args.search:
        print(f"\nSearching for: {args.search}")
        if args.collection == 'all':
            results = store.search_all(args.search, limit_per_collection=args.limit)
            for collection, items in results.items():
                if items:
                    print(f"\n  {collection.upper()} ({len(items)} results):")
                    for r in items:
                        print(f"    [{r.score:.3f}] {r.payload.get('name', r.payload.get('title', r.id))}")
        else:
            results = store.search(args.search, args.collection, limit=args.limit)
            print(f"\n  {args.collection.upper()} ({len(results)} results):")
            for r in results:
                print(f"    [{r.score:.3f}] {r.payload.get('name', r.payload.get('title', r.id))}")


if __name__ == '__main__':
    main()
