"""
Initialize BM25 Index from Qdrant Data
Reads existing vectors from Qdrant and populates the BM25 keyword index.
"""

import os
import sys
import logging
from typing import Dict, List, Any

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_qdrant_data(collection: str, qdrant_path: str = None) -> List[Dict]:
    """Fetch all documents from a Qdrant collection."""
    try:
        from qdrant_client import QdrantClient

        if qdrant_path is None:
            qdrant_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "data", "qdrant"
            )

        client = QdrantClient(path=qdrant_path)

        docs = []
        offset = None

        while True:
            results, offset = client.scroll(
                collection_name=collection,
                limit=100,
                offset=offset,
                with_payload=True
            )

            for r in results:
                # Extract text content from payload
                payload = r.payload or {}
                text_parts = []

                # Common text fields
                for field in ['text', 'content', 'description', 'title', 'notes', 'name']:
                    if field in payload and payload[field]:
                        text_parts.append(str(payload[field]))

                text = " ".join(text_parts) if text_parts else str(payload)

                docs.append({
                    "id": str(r.id),
                    "text": text,
                    **payload
                })

            if offset is None:
                break

        return docs

    except Exception as e:
        logger.error(f"Failed to fetch from {collection}: {e}")
        return []


def initialize_bm25_index(collections: List[str] = None):
    """
    Initialize BM25 index from Qdrant collections.

    Args:
        collections: List of collections to index. Defaults to jobs and contacts.
    """
    from Engine8_Knowledge.scripts.hybrid_retriever import get_hybrid_retriever

    if collections is None:
        collections = ["jobs", "contacts"]

    retriever = get_hybrid_retriever()
    total_indexed = 0
    stats = {}

    for collection in collections:
        logger.info(f"Indexing collection: {collection}")

        docs = get_qdrant_data(collection)

        if not docs:
            logger.warning(f"No documents found in {collection}")
            stats[collection] = 0
            continue

        # Build BM25 index for this collection
        retriever._build_bm25_index(collection, docs)

        count = len(docs)
        total_indexed += count
        stats[collection] = count
        logger.info(f"Indexed {count} documents from {collection}")

    return {
        "total_indexed": total_indexed,
        "by_collection": stats,
        "status": "success"
    }


def main():
    """Run BM25 initialization."""
    import argparse

    parser = argparse.ArgumentParser(description='Initialize BM25 Index')
    parser.add_argument(
        '--collections',
        nargs='+',
        default=['jobs', 'contacts', 'programs', 'documents'],
        help='Collections to index'
    )
    parser.add_argument(
        '--qdrant-path',
        default=None,
        help='Path to Qdrant data directory'
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("BM25 INDEX INITIALIZATION")
    print("=" * 60 + "\n")

    result = initialize_bm25_index(args.collections)

    print("\n" + "-" * 40)
    print("RESULTS:")
    print("-" * 40)
    print(f"Total Documents Indexed: {result['total_indexed']}")
    print("\nBy Collection:")
    for coll, count in result['by_collection'].items():
        print(f"  - {coll}: {count} documents")
    print(f"\nStatus: {result['status']}")
    print("=" * 60 + "\n")

    return result


if __name__ == "__main__":
    main()
