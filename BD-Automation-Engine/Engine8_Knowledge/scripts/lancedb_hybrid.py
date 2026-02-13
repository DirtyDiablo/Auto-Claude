"""
LanceDB hybrid search module for BD Intelligence Hub.

Provides three-tier search architecture:
1. SQLite FTS5 — structured metadata queries, faceted filtering
2. LanceDB Hybrid — semantic + keyword with RRF reranking (PRIMARY search path)
3. Qdrant — deep semantic similarity across 1.42M vector corpus

Usage:
    from Engine8_Knowledge.scripts.lancedb_hybrid import LanceDBHybrid
    hybrid = LanceDBHybrid()
    results = hybrid.search("DCGS analyst with TS/SCI", limit=10)

Install:
    pip install lancedb
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

try:
    import lancedb
    LANCEDB_AVAILABLE = True
except ImportError:
    LANCEDB_AVAILABLE = False
    logger.warning("lancedb not installed. Install with: pip install lancedb")

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


BASE_DIR = Path(__file__).parent.parent
LANCEDB_PATH = os.environ.get("LANCEDB_PATH", str(BASE_DIR / "data" / "lancedb"))
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536


@dataclass
class HybridSearchResult:
    """Single search result from hybrid search."""
    id: str
    score: float
    text: str
    metadata: Dict = field(default_factory=dict)
    search_mode: str = "hybrid"


@dataclass
class HybridSearchResponse:
    """Response from hybrid search."""
    query: str
    results: List[HybridSearchResult] = field(default_factory=list)
    total: int = 0
    search_mode: str = "hybrid"
    search_time_ms: float = 0


class LanceDBHybrid:
    """
    LanceDB-based hybrid search combining BM25 keyword + semantic vector search
    with Reciprocal Rank Fusion (RRF) reranking.
    """

    def __init__(self, db_path: str = None):
        """
        Initialize LanceDB hybrid search.

        Args:
            db_path: Path to LanceDB storage directory
        """
        if not LANCEDB_AVAILABLE:
            raise ImportError("lancedb is required. Install with: pip install lancedb")

        self.db_path = db_path or LANCEDB_PATH
        Path(self.db_path).mkdir(parents=True, exist_ok=True)
        self.db = lancedb.connect(self.db_path)
        self._openai_client = None

    @property
    def openai_client(self):
        """Lazy OpenAI client initialization."""
        if self._openai_client is None and OPENAI_AVAILABLE:
            self._openai_client = openai.OpenAI(
                api_key=os.environ.get("OPENAI_API_KEY")
            )
        return self._openai_client

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding vector for text."""
        if not self.openai_client:
            raise RuntimeError("OpenAI client not available for embeddings")
        response = self.openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text[:8000]
        )
        return response.data[0].embedding

    def create_table(
        self,
        table_name: str,
        records: List[Dict],
        text_field: str = "content",
        overwrite: bool = False,
    ) -> int:
        """
        Create a LanceDB table from records with embeddings.

        Args:
            table_name: Name for the table
            records: List of dicts with at least a text field
            text_field: Field name containing text to embed
            overwrite: Whether to overwrite existing table

        Returns:
            Number of records indexed
        """
        if not records:
            return 0

        # Check if table exists
        existing_tables = self.db.table_names()
        if table_name in existing_tables:
            if overwrite:
                self.db.drop_table(table_name)
            else:
                logger.info("lancedb_table_exists", table=table_name)
                return 0

        # Build records with embeddings
        indexed_records = []
        batch_size = 100

        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            texts = [r.get(text_field, "") or "" for r in batch]
            texts = [t[:8000] if t else "empty" for t in texts]

            try:
                response = self.openai_client.embeddings.create(
                    model=EMBEDDING_MODEL,
                    input=texts
                )
                embeddings = [item.embedding for item in response.data]

                for record, embedding in zip(batch, embeddings):
                    indexed_records.append({
                        **record,
                        "vector": embedding,
                        "text": record.get(text_field, ""),
                    })
            except Exception as e:
                logger.error("lancedb_embedding_error", batch=i, error=str(e))

        if indexed_records:
            self.db.create_table(table_name, indexed_records)
            logger.info("lancedb_table_created", table=table_name, records=len(indexed_records))

        return len(indexed_records)

    def search(
        self,
        query: str,
        table_name: str = "documents",
        limit: int = 10,
        query_type: str = "hybrid",
        filters: Optional[str] = None,
    ) -> HybridSearchResponse:
        """
        Execute hybrid search combining BM25 keyword + semantic vector search.

        Args:
            query: Search query string
            table_name: Table to search in
            limit: Maximum results to return
            query_type: "hybrid" (BM25+semantic), "vector" (semantic only), "fts" (keyword only)
            filters: Optional SQL-like filter string (e.g., "status = 'Active'")

        Returns:
            HybridSearchResponse with ranked results
        """
        import time
        start = time.time()

        try:
            table = self.db.open_table(table_name)
        except Exception as e:
            return HybridSearchResponse(
                query=query,
                search_mode=query_type,
            )

        try:
            if query_type == "hybrid":
                results = self._hybrid_search(table, query, limit, filters)
            elif query_type == "vector":
                results = self._vector_search(table, query, limit, filters)
            elif query_type == "fts":
                results = self._fts_search(table, query, limit, filters)
            else:
                results = self._hybrid_search(table, query, limit, filters)
        except Exception as e:
            logger.error("lancedb_search_error", error=str(e), query_type=query_type)
            results = []

        elapsed = (time.time() - start) * 1000

        return HybridSearchResponse(
            query=query,
            results=results,
            total=len(results),
            search_mode=query_type,
            search_time_ms=round(elapsed, 2),
        )

    def _hybrid_search(
        self, table, query: str, limit: int, filters: Optional[str]
    ) -> List[HybridSearchResult]:
        """BM25 + semantic with RRF reranking."""
        self.get_embedding(query)

        search_builder = table.search(query, query_type="hybrid")
        search_builder = search_builder.limit(limit)

        if filters:
            search_builder = search_builder.where(filters)

        try:
            # Try with RRF reranker if available
            from lancedb.rerankers import RRFReranker
            search_builder = search_builder.rerank(reranker=RRFReranker())
        except (ImportError, Exception):
            pass

        df = search_builder.to_pandas()
        return self._df_to_results(df, "hybrid")

    def _vector_search(
        self, table, query: str, limit: int, filters: Optional[str]
    ) -> List[HybridSearchResult]:
        """Pure semantic vector search."""
        query_vector = self.get_embedding(query)

        search_builder = table.search(query_vector).limit(limit)
        if filters:
            search_builder = search_builder.where(filters)

        df = search_builder.to_pandas()
        return self._df_to_results(df, "vector")

    def _fts_search(
        self, table, query: str, limit: int, filters: Optional[str]
    ) -> List[HybridSearchResult]:
        """Pure BM25 keyword search."""
        search_builder = table.search(query, query_type="fts").limit(limit)
        if filters:
            search_builder = search_builder.where(filters)

        df = search_builder.to_pandas()
        return self._df_to_results(df, "fts")

    def _df_to_results(self, df, mode: str) -> List[HybridSearchResult]:
        """Convert pandas DataFrame to list of HybridSearchResult."""
        results = []
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            # Remove vector from metadata
            row_dict.pop("vector", None)
            text = row_dict.pop("text", "")
            score = row_dict.pop("_relevance_score", row_dict.pop("_distance", 0))
            record_id = str(row_dict.pop("id", row_dict.pop("_rowid", "")))

            results.append(HybridSearchResult(
                id=record_id,
                score=float(score) if score else 0.0,
                text=text,
                metadata=row_dict,
                search_mode=mode,
            ))
        return results

    def list_tables(self) -> List[str]:
        """List all available tables."""
        return self.db.table_names()

    def table_stats(self, table_name: str) -> Dict:
        """Get statistics for a table."""
        try:
            table = self.db.open_table(table_name)
            return {
                "table": table_name,
                "row_count": table.count_rows(),
            }
        except Exception as e:
            return {"table": table_name, "error": str(e)}

    def stats(self) -> Dict:
        """Get overall LanceDB statistics."""
        tables = self.list_tables()
        return {
            "db_path": self.db_path,
            "table_count": len(tables),
            "tables": {t: self.table_stats(t) for t in tables},
        }


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    hybrid = LanceDBHybrid()
    print(f"LanceDB at: {hybrid.db_path}")
    print(f"Tables: {hybrid.list_tables()}")
    print(f"Stats: {json.dumps(hybrid.stats(), indent=2)}")

    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"\nSearching: {query}")
        response = hybrid.search(query)
        print(f"Results: {response.total} ({response.search_time_ms}ms)")
        for r in response.results:
            print(f"  [{r.score:.3f}] {r.text[:100]}...")
