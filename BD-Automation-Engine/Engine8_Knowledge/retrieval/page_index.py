"""
PageIndex - Vectorless RAG with Page-Level Indexing
Provides explainable retrieval with exact source citations.
"""
import sqlite3
import json
from pathlib import Path
from rank_bm25 import BM25Okapi
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PageRecord:
    """Represents a single page from a document."""
    page_id: str
    document_id: str
    document_name: str
    page_number: int
    content: str
    metadata: Dict
    indexed_at: datetime


@dataclass
class RetrievalResult:
    """Explainable retrieval result with source citation."""
    page_id: str
    document_name: str
    page_number: int
    content: str
    score: float
    matched_terms: List[str]
    citation: str  # Human-readable citation


class PageIndex:
    """
    Vectorless RAG using page-level BM25 indexing.
    Optimized for explainability and exact source tracking.
    """

    def __init__(self, db_path: str = "data/page_index.db"):
        self.db_path = db_path
        self.conn = None
        self.bm25_index = None
        self.page_cache = []
        self._init_database()

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def _init_database(self):
        """Initialize SQLite database for page storage."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS pages (
                page_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                document_name TEXT NOT NULL,
                page_number INTEGER NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(document_id, page_number)
            )
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_document_id ON pages(document_id)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_document_name ON pages(document_name)
        """)
        self.conn.commit()
        self._rebuild_bm25_index()

    def _rebuild_bm25_index(self):
        """Rebuild BM25 index from database."""
        cursor = self.conn.execute(
            "SELECT page_id, document_name, page_number, content FROM pages"
        )
        self.page_cache = []
        corpus = []

        for row in cursor:
            self.page_cache.append({
                "page_id": row[0],
                "document_name": row[1],
                "page_number": row[2],
                "content": row[3]
            })
            # Tokenize for BM25
            corpus.append(row[3].lower().split())

        if corpus:
            self.bm25_index = BM25Okapi(corpus)
        else:
            self.bm25_index = None

    def index_document(self,
                       document_id: str,
                       document_name: str,
                       pages: List[Dict[str, any]],
                       metadata: Optional[Dict] = None) -> int:
        """
        Index a document by its pages.

        Args:
            document_id: Unique document identifier
            document_name: Human-readable name (e.g., "AF_DCGS_Contract_2024.pdf")
            pages: List of {"page_number": int, "content": str}
            metadata: Optional document-level metadata

        Returns:
            Number of pages indexed
        """
        indexed = 0
        for page in pages:
            page_id = f"{document_id}_p{page['page_number']}"
            try:
                self.conn.execute("""
                    INSERT OR REPLACE INTO pages
                    (page_id, document_id, document_name, page_number, content, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    page_id,
                    document_id,
                    document_name,
                    page['page_number'],
                    page['content'],
                    json.dumps(metadata or {})
                ))
                indexed += 1
            except Exception as e:
                print(f"Error indexing page {page_id}: {e}")

        self.conn.commit()
        self._rebuild_bm25_index()
        return indexed

    def search(self,
               query: str,
               top_k: int = 5,
               document_filter: Optional[str] = None,
               min_score: float = 0.0) -> List[RetrievalResult]:
        """
        Search for pages matching the query.

        Args:
            query: Natural language search query
            top_k: Number of results to return
            document_filter: Optional filter by document name (partial match)
            min_score: Minimum BM25 score threshold

        Returns:
            List of RetrievalResult with explainable citations
        """
        if not self.bm25_index or not self.page_cache:
            return []

        # Tokenize query
        query_tokens = query.lower().split()

        # Get BM25 scores
        scores = self.bm25_index.get_scores(query_tokens)

        # Combine with page data and filter
        results = []
        for idx, score in enumerate(scores):
            if score < min_score:
                continue

            page = self.page_cache[idx]

            # Apply document filter
            if document_filter:
                if document_filter.lower() not in page["document_name"].lower():
                    continue

            # Find matched terms for explainability
            matched_terms = [
                term for term in query_tokens
                if term in page["content"].lower()
            ]

            # Generate citation
            citation = f"{page['document_name']}, Page {page['page_number']}"

            results.append(RetrievalResult(
                page_id=page["page_id"],
                document_name=page["document_name"],
                page_number=page["page_number"],
                content=page["content"][:2000],  # Truncate for response
                score=float(score),
                matched_terms=matched_terms,
                citation=citation
            ))

        # Sort by score and return top_k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def get_document_pages(self, document_id: str) -> List[Dict]:
        """Get all pages for a specific document."""
        cursor = self.conn.execute(
            "SELECT page_id, page_number, content FROM pages WHERE document_id = ? ORDER BY page_number",
            (document_id,)
        )
        return [{"page_id": r[0], "page_number": r[1], "content": r[2]} for r in cursor]

    def get_citation_context(self, page_id: str, context_pages: int = 1) -> Dict:
        """
        Get a page with surrounding context for full citation.

        Args:
            page_id: The page to retrieve
            context_pages: Number of pages before/after to include

        Returns:
            Dict with target page and context
        """
        # Get the target page
        cursor = self.conn.execute(
            "SELECT document_id, page_number, content, document_name FROM pages WHERE page_id = ?",
            (page_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None

        document_id, page_number, content, doc_name = row

        # Get surrounding pages
        cursor = self.conn.execute("""
            SELECT page_number, content FROM pages
            WHERE document_id = ? AND page_number BETWEEN ? AND ?
            ORDER BY page_number
        """, (document_id, page_number - context_pages, page_number + context_pages))

        context = [{"page_number": r[0], "content": r[1]} for r in cursor]

        return {
            "document_name": doc_name,
            "target_page": page_number,
            "citation": f"{doc_name}, Page {page_number}",
            "context": context
        }

    def delete_document(self, document_id: str) -> int:
        """Delete a document and all its pages from the index."""
        cursor = self.conn.execute(
            "DELETE FROM pages WHERE document_id = ?",
            (document_id,)
        )
        self.conn.commit()
        deleted = cursor.rowcount
        self._rebuild_bm25_index()
        return deleted

    def stats(self) -> Dict:
        """Get index statistics."""
        cursor = self.conn.execute("SELECT COUNT(*) FROM pages")
        total_pages = cursor.fetchone()[0]

        cursor = self.conn.execute("SELECT COUNT(DISTINCT document_id) FROM pages")
        total_docs = cursor.fetchone()[0]

        cursor = self.conn.execute("SELECT document_name, COUNT(*) FROM pages GROUP BY document_name")
        docs = [{"name": r[0], "pages": r[1]} for r in cursor]

        return {
            "total_pages": total_pages,
            "total_documents": total_docs,
            "documents": docs,
            "bm25_ready": self.bm25_index is not None
        }


class PageIndexRAG:
    """
    RAG wrapper for PageIndex providing question-answering with citations.
    """

    def __init__(self, page_index: PageIndex, llm_client=None):
        self.index = page_index
        self.llm = llm_client  # Anthropic or OpenAI client

    def answer_with_citations(self,
                              question: str,
                              top_k: int = 5) -> Dict:
        """
        Answer a question using PageIndex retrieval with full citations.

        Returns:
            {
                "answer": str,
                "citations": [{"citation": str, "excerpt": str, "page_id": str}],
                "confidence": float
            }
        """
        # Retrieve relevant pages
        results = self.index.search(question, top_k=top_k)

        if not results:
            return {
                "answer": "No relevant information found in the indexed documents.",
                "citations": [],
                "confidence": 0.0
            }

        # Build context from results
        context_parts = []
        citations = []

        for i, result in enumerate(results):
            context_parts.append(f"[Source {i+1}: {result.citation}]\n{result.content}")
            citations.append({
                "citation": result.citation,
                "excerpt": result.content[:500],
                "page_id": result.page_id,
                "score": result.score,
                "matched_terms": result.matched_terms
            })

        context = "\n\n---\n\n".join(context_parts)

        # If no LLM, return raw results
        if not self.llm:
            return {
                "answer": f"Found {len(results)} relevant pages. Top result from {results[0].citation}",
                "citations": citations,
                "confidence": min(results[0].score / 10.0, 1.0)  # Normalize
            }

        # Generate answer with LLM
        prompt = f"""Based on the following sources, answer the question.
Always cite your sources using [Source N] format.

Question: {question}

Sources:
{context}

Provide a clear, factual answer with citations:"""

        # Call LLM (implement based on your client)
        # answer = self.llm.generate(prompt)

        return {
            "answer": "LLM answer would go here",
            "citations": citations,
            "confidence": sum(r.score for r in results) / len(results) / 10.0
        }
