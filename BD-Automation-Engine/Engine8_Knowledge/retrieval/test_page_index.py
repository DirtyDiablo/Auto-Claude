"""Test PageIndex implementation."""
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from page_index import PageIndex, PageIndexRAG


def test_page_index():
    print("Testing PageIndex...")

    # Use temp database for testing
    test_db = "data/test_page_index.db"

    # Clean up previous test
    if Path(test_db).exists():
        Path(test_db).unlink()

    # Initialize
    index = PageIndex(db_path=test_db)
    print("[OK] PageIndex initialized")

    # Index a test document
    test_pages = [
        {"page_number": 1, "content": "AF DCGS is a distributed common ground system operated by the Air Force."},
        {"page_number": 2, "content": "GDIT is the prime contractor for Army DCGS-A program worth $300M."},
        {"page_number": 3, "content": "Key locations include Langley AFB, Wright-Patterson, and San Diego."},
    ]

    num_indexed = index.index_document(
        document_id="test_doc_001",
        document_name="DCGS_Overview.pdf",
        pages=test_pages,
        metadata={"type": "test"}
    )
    print(f"[OK] Indexed {num_indexed} pages")

    # Test search
    results = index.search("DCGS contractor Army")
    print(f"[OK] Search returned {len(results)} results")
    for r in results:
        print(f"    - {r.citation}: score={r.score:.2f}, matched={r.matched_terms}")

    # Test citation context
    if results:
        context = index.get_citation_context(results[0].page_id)
        print(f"[OK] Citation context: {context['citation']}")

    # Test document pages
    pages = index.get_document_pages("test_doc_001")
    print(f"[OK] Get document pages: {len(pages)} pages")

    # Test stats
    stats = index.stats()
    print(f"[OK] Stats: {stats['total_documents']} docs, {stats['total_pages']} pages")

    # Test RAG wrapper
    rag = PageIndexRAG(index)
    answer = rag.answer_with_citations("Who is the contractor for Army DCGS?")
    print(f"[OK] RAG answer with {len(answer['citations'])} citations")

    # Test delete
    deleted = index.delete_document("test_doc_001")
    print(f"[OK] Deleted {deleted} pages")

    # Verify deletion
    stats = index.stats()
    assert stats['total_pages'] == 0, "Delete failed"
    print("[OK] Deletion verified")

    # Close connection before cleanup
    index.close()

    # Clean up test database
    try:
        Path(test_db).unlink()
        print("[OK] Cleaned up test database")
    except PermissionError:
        print("[WARN] Could not delete test database (file locked)")

    # Test routes import
    from routes import router
    print(f"[OK] Router created with prefix: {router.prefix}")

    print("\n[SUCCESS] All PageIndex tests passed!")


if __name__ == "__main__":
    test_page_index()
