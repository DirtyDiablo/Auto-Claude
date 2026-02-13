"""
Cross-Encoder Reranker Service - Improves search precision.

Uses a cross-encoder model to rerank search results for better relevance.

Usage:
    from services.reranker import Reranker, rerank

    reranker = Reranker()
    reranked = reranker.rerank("query", documents, top_k=10)

    # Or use the convenience function
    reranked = rerank("query", documents)
"""

from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Logging
try:
    from utils.logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# Try to import cross-encoder
try:
    from sentence_transformers import CrossEncoder
    CROSSENCODER_AVAILABLE = True
except ImportError:
    CROSSENCODER_AVAILABLE = False
    logger.warning("sentence-transformers not installed. Run: pip install sentence-transformers")


# Global reranker instance (lazy loaded)
_reranker_instance = None


class Reranker:
    """
    Cross-encoder reranker for improving search result precision.

    Uses ms-marco-MiniLM-L-6-v2 model for fast, accurate reranking.
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Initialize the reranker.

        Args:
            model_name: HuggingFace model name for cross-encoder
        """
        self.model_name = model_name
        self._model = None

    @property
    def model(self) -> "CrossEncoder":
        """Lazy load the cross-encoder model."""
        if self._model is None:
            if not CROSSENCODER_AVAILABLE:
                raise ImportError(
                    "sentence-transformers not installed. "
                    "Run: pip install sentence-transformers"
                )
            logger.info("loading_reranker", model=self.model_name)
            self._model = CrossEncoder(self.model_name, max_length=512)
            logger.info("reranker_loaded", model=self.model_name)
        return self._model

    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 10,
        content_key: str = "content",
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents using cross-encoder.

        Args:
            query: Search query
            documents: List of document dicts with content
            top_k: Number of results to return
            content_key: Key in document dict containing text content

        Returns:
            Top-K documents sorted by relevance, with rerank_score added
        """
        if not documents:
            return []

        # Build query-document pairs
        pairs = []
        for doc in documents:
            content = doc.get(content_key, "")
            if not content and "payload" in doc:
                content = doc["payload"].get(content_key, "")
            if not content:
                content = str(doc)
            pairs.append((query, content))

        # Get cross-encoder scores
        try:
            scores = self.model.predict(pairs)
        except Exception as e:
            logger.error("reranking_failed", error=str(e))
            return documents[:top_k]

        # Combine documents with scores
        scored_docs = list(zip(documents, scores))

        # Sort by score descending
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        # Add rerank_score and return top_k
        results = []
        for doc, score in scored_docs[:top_k]:
            doc_copy = dict(doc)
            doc_copy["rerank_score"] = float(score)
            results.append(doc_copy)

        logger.info(
            "reranking_complete",
            query_len=len(query),
            input_count=len(documents),
            output_count=len(results),
        )

        return results

    def rerank_with_threshold(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        threshold: float = 0.0,
        content_key: str = "content",
    ) -> List[Dict[str, Any]]:
        """
        Rerank and filter by score threshold.

        Args:
            query: Search query
            documents: List of document dicts
            threshold: Minimum score to include
            content_key: Key containing text content

        Returns:
            Documents with rerank_score >= threshold
        """
        reranked = self.rerank(query, documents, top_k=len(documents), content_key=content_key)
        return [doc for doc in reranked if doc.get("rerank_score", 0) >= threshold]


def get_reranker() -> Reranker:
    """Get or create the global reranker instance."""
    global _reranker_instance
    if _reranker_instance is None:
        _reranker_instance = Reranker()
    return _reranker_instance


def rerank(
    query: str,
    documents: List[Dict[str, Any]],
    top_k: int = 10,
    content_key: str = "content",
) -> List[Dict[str, Any]]:
    """
    Convenience function to rerank documents.

    Usage:
        from services.reranker import rerank

        results = search_engine.search("query")
        reranked = rerank("query", results, top_k=10)
    """
    reranker = get_reranker()
    return reranker.rerank(query, documents, top_k=top_k, content_key=content_key)


# CLI usage
if __name__ == "__main__":
    pass

    # Test the reranker
    test_docs = [
        {"content": "Network engineer with TS/SCI clearance in San Diego", "id": "1"},
        {"content": "Software developer working on DCGS program", "id": "2"},
        {"content": "Project manager for federal contracts", "id": "3"},
        {"content": "Cyber security analyst with Top Secret clearance", "id": "4"},
        {"content": "Systems administrator for Navy programs", "id": "5"},
    ]

    query = "DCGS network engineer with security clearance"

    print(f"Query: {query}")
    print("\nOriginal order:")
    for i, doc in enumerate(test_docs, 1):
        print(f"  {i}. {doc['content'][:50]}...")

    reranked = rerank(query, test_docs, top_k=5)

    print("\nReranked order:")
    for i, doc in enumerate(reranked, 1):
        print(f"  {i}. (score: {doc['rerank_score']:.4f}) {doc['content'][:50]}...")
