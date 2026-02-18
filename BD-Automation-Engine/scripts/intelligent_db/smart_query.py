"""
Smart Query Engine - Routes queries to SQL, Vector, or Hybrid retrieval.
Combines structured SQL (counts, filters), semantic search (similarity),
and optionally graph traversal.
"""
import json
import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

DB_PATH = PROJECT_ROOT / "data" / "unified_federal_contracts.db"
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

# Query type detection patterns
SQL_PATTERNS = [
    r"\bhow many\b", r"\bcount\b", r"\btotal\b", r"\blist all\b",
    r"\btop \d+\b", r"\bhighest\b", r"\blowest\b", r"\baverage\b",
    r"\bsum\b", r"\bwhere\b", r"\bfilter\b", r"\bsort\b",
    r"\bgroup by\b", r"\bvalue\b.*\b(?:greater|less|above|below|over|under)\b",
]

VECTOR_PATTERNS = [
    r"\bsimilar to\b", r"\blike\b", r"\brelated to\b", r"\babout\b",
    r"\bwho works on\b", r"\bfind.*(?:expert|specialist|contact)\b",
    r"\bwhat programs?\b.*\bfor\b", r"\btell me about\b",
    r"\bexperience with\b", r"\bknowledge of\b",
]

GRAPH_PATTERNS = [
    r"\brelationship\b", r"\bconnected to\b", r"\bpath\b",
    r"\bnetwork\b", r"\bwho knows\b", r"\binfluence\b",
    r"\bcompetes?\b", r"\bpartner\b", r"\bsubs?\s+to\b",
]


def detect_query_type(query: str) -> str:
    """Detect whether query should use sql, vector, graph, or hybrid."""
    q = query.lower()

    sql_score = sum(1 for p in SQL_PATTERNS if re.search(p, q))
    vec_score = sum(1 for p in VECTOR_PATTERNS if re.search(p, q))
    graph_score = sum(1 for p in GRAPH_PATTERNS if re.search(p, q))

    if graph_score > 0 and graph_score >= sql_score and graph_score >= vec_score:
        return "graph"
    if sql_score > vec_score:
        return "sql"
    if vec_score > 0:
        return "vector"
    return "hybrid"


def _detect_table(query: str) -> str:
    """Detect which table the query is about."""
    q = query.lower()
    if any(w in q for w in ["contact", "person", "people", "who"]):
        return "contacts"
    if any(w in q for w in ["program", "contract", "dcgs", "project"]):
        return "programs"
    if any(w in q for w in ["company", "contractor", "vendor", "prime"]):
        return "companies"
    if any(w in q for w in ["job", "opening", "position", "hiring"]):
        return "jobs"
    if any(w in q for w in ["activity", "call", "note", "meeting"]):
        return "activities"
    if any(w in q for w in ["intel", "intelligence", "score", "analysis"]):
        return "intelligence"
    return "programs"


class SmartQueryEngine:
    """Routes queries to the best retrieval method."""

    def __init__(self, db_path=None, qdrant_url=None):
        self.db_path = db_path or DB_PATH
        self.qdrant_url = qdrant_url or QDRANT_URL
        self._store = None
        self._graph = None

    @property
    def store(self):
        """Lazy-load vector store."""
        if self._store is None:
            try:
                from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore
                self._store = BDKnowledgeStore(url=self.qdrant_url)
            except Exception:
                self._store = False  # Mark as unavailable
        return self._store if self._store is not False else None

    @property
    def graph(self):
        """Lazy-load knowledge graph."""
        if self._graph is None:
            try:
                from Engine8_Knowledge.graph.bd_knowledge_graph import BDKnowledgeGraph
                graph_path = PROJECT_ROOT / "Engine8_Knowledge" / "data" / "bd_graph.db"
                self._graph = BDKnowledgeGraph(db_path=str(graph_path))
            except Exception:
                self._graph = False
        return self._graph if self._graph is not False else None

    def query(self, q: str, limit: int = 10) -> Dict[str, Any]:
        """Execute a smart query, routing to the best backend."""
        query_type = detect_query_type(q)

        result = {
            "query": q,
            "query_type": query_type,
            "results": [],
            "count": 0,
            "systems_used": [],
        }

        if query_type == "sql":
            result.update(self._sql_query(q, limit))
        elif query_type == "vector":
            result.update(self._vector_query(q, limit))
        elif query_type == "graph":
            result.update(self._graph_query(q, limit))
        else:
            # Hybrid: combine SQL and vector
            sql_result = self._sql_query(q, limit)
            vec_result = self._vector_query(q, limit)
            result["results"] = sql_result.get("results", []) + vec_result.get("results", [])
            result["count"] = len(result["results"])
            result["systems_used"] = sql_result.get("systems_used", []) + vec_result.get("systems_used", [])

        return result

    def _sql_query(self, q: str, limit: int) -> Dict:
        """Execute structured SQL query."""
        table = _detect_table(q)
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        results = []
        try:
            # Count queries
            count_match = re.search(r"\bhow many\b|\bcount\b|\btotal\b", q.lower())
            if count_match:
                cursor.execute(f"SELECT COUNT(*) as total FROM {table}")
                row = cursor.fetchone()
                results = [{"total": row["total"], "table": table}]
            else:
                # Search queries - look for keywords to filter
                words = re.findall(r'\b[A-Za-z]{3,}\b', q)
                search_words = [w for w in words if w.lower() not in
                    {"the", "and", "for", "with", "who", "what", "how", "all",
                     "list", "find", "show", "get", "top", "are", "from"}]

                if search_words:
                    # Get searchable text columns
                    cursor.execute(f"PRAGMA table_info({table})")
                    text_cols = [r[1] for r in cursor.fetchall() if r[2] == "TEXT"][:5]

                    if text_cols:
                        where_parts = []
                        params = []
                        for word in search_words[:3]:
                            col_checks = " OR ".join(f"[{c}] LIKE ?" for c in text_cols)
                            where_parts.append(f"({col_checks})")
                            params.extend([f"%{word}%"] * len(text_cols))

                        where_clause = " AND ".join(where_parts)
                        cursor.execute(
                            f"SELECT * FROM {table} WHERE {where_clause} LIMIT ?",
                            params + [limit]
                        )
                        results = [dict(row) for row in cursor.fetchall()]
                else:
                    cursor.execute(f"SELECT * FROM {table} LIMIT ?", (limit,))
                    results = [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError as e:
            results = [{"error": str(e)}]
        finally:
            conn.close()

        return {"results": results, "count": len(results), "systems_used": ["sql"]}

    def _vector_query(self, q: str, limit: int) -> Dict:
        """Execute semantic vector search."""
        if not self.store:
            return {"results": [], "count": 0, "systems_used": ["vector(unavailable)"]}

        table = _detect_table(q)
        # Map table to collection name
        collection_map = {
            "contacts": "contacts",
            "programs": "programs",
            "activities": "activities",
            "intelligence": "intelligence_reports",
            "contracts": "federal_contracts",
            "jobs": "jobs",
            "companies": "programs",  # No dedicated companies collection
        }
        collection = collection_map.get(table, "programs")

        try:
            results = self.store.search(collection, q, limit=limit)
            return {
                "results": [r.to_dict() if hasattr(r, 'to_dict') else r for r in results],
                "count": len(results),
                "systems_used": ["vector"],
            }
        except Exception as e:
            return {"results": [{"error": str(e)}], "count": 0, "systems_used": ["vector(error)"]}

    def _graph_query(self, q: str, limit: int) -> Dict:
        """Execute graph traversal query."""
        if not self.graph:
            return {"results": [], "count": 0, "systems_used": ["graph(unavailable)"]}

        # Extract entity names from query
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', q)

        results = []
        for name in words[:3]:
            try:
                entities = self.graph.find_entities(name)
                for entity in entities[:limit]:
                    neighbors = self.graph.get_neighbors(entity.id) if hasattr(self.graph, 'get_neighbors') else []
                    results.append({
                        "entity": entity.to_dict(),
                        "neighbors": [n.to_dict() if hasattr(n, 'to_dict') else str(n) for n in neighbors[:5]],
                    })
            except Exception:
                continue

        return {"results": results, "count": len(results), "systems_used": ["graph"]}


def run():
    """Interactive query mode."""
    engine = SmartQueryEngine()
    print("Smart Query Engine (type 'quit' to exit)")
    print("=" * 50)

    while True:
        try:
            q = input("\nQuery> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if q.lower() in ("quit", "exit", "q"):
            break
        if not q:
            continue

        result = engine.query(q)
        print(f"  Type: {result['query_type']} | Systems: {result['systems_used']} | Results: {result['count']}")
        for r in result["results"][:5]:
            print(f"  - {json.dumps(r, default=str)[:200]}")


if __name__ == "__main__":
    run()
