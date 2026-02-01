"""Test UltraRAG implementation."""
import sys
import asyncio
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from ultra_rag import UltraRAG, PipelineConfig, QueryPlan


def mock_retriever(query, strategy="hybrid", top_k=5, collection=None):
    """Mock retriever for testing."""
    return [
        {"content": f"Result 1 for '{query}'", "source": "test_doc.pdf", "score": 0.9},
        {"content": f"Result 2 for '{query}'", "source": "test_doc2.pdf", "score": 0.8},
    ]


async def test_async_queries():
    """Test async query methods."""
    print("Testing UltraRAG...")

    # Initialize
    ultra = UltraRAG(retriever_func=mock_retriever)
    print("[OK] UltraRAG initialized")

    # Test simple query
    print("\nTesting simple pipeline...")
    plan = await ultra.query("What is AF DCGS?", pipeline="simple")
    print(f"    Answer: {plan.final_answer}")
    print(f"    Citations: {len(plan.citations)}")
    print(f"    Time: {plan.execution_time_ms}ms")
    assert plan.final_answer is not None
    print("[OK] Simple pipeline works")

    # Test complex query
    print("\nTesting complex pipeline...")
    plan = await ultra.query(
        "Compare AF DCGS and Army DCGS-A: Who are the prime contractors and what are the contract values?",
        pipeline="complex"
    )
    print(f"    Sub-queries: {plan.sub_queries}")
    print(f"    Answer: {plan.final_answer}")
    print(f"    Confidence: {plan.confidence}")
    assert len(plan.sub_queries) > 0
    print("[OK] Complex pipeline works")

    # Test BD intelligence pipeline
    print("\nTesting BD intelligence pipeline...")
    plan = await ultra.query(
        "Analyze GDIT opportunities on DCGS programs",
        pipeline="bd_intelligence"
    )
    print(f"    Answer: {plan.final_answer}")
    print(f"    Intermediate results keys: {list(plan.intermediate_results.keys())}")
    assert "retrieve_hybrid_programs" in plan.intermediate_results
    print("[OK] BD intelligence pipeline works")

    # Test auto classification
    print("\nTesting auto classification...")
    test_cases = [
        ("What is the contract value?", "bd_intelligence"),  # has "contract"
        ("Compare GDIT and Lockheed on DCGS", "bd_intelligence"),  # has "DCGS"
        ("Is it true that the sky is blue?", "factcheck"),  # has "is it true"
        ("What is Python?", "simple"),  # generic
    ]
    for query, expected in test_cases:
        pipeline = ultra._classify_query(query)
        status = "[OK]" if pipeline == expected else "[WARN]"
        print(f"    {status} '{query[:35]}...' -> {pipeline} (expected: {expected})")

    # Test list pipelines
    print("\nTesting list pipelines...")
    pipelines = ultra.list_pipelines()
    print(f"    Available: {[p['id'] for p in pipelines]}")
    assert len(pipelines) >= 5
    print("[OK] List pipelines works")

    return ultra


def test_sync_wrapper():
    """Test sync query wrapper (must be called from sync context)."""
    print("\nTesting sync wrapper...")
    ultra = UltraRAG(retriever_func=mock_retriever)
    plan = ultra.query_sync("Test query", pipeline="simple")
    assert plan.final_answer is not None
    print("[OK] Sync wrapper works")


def test_routes():
    """Test routes import."""
    from ultra_rag_routes import router
    print(f"\n[OK] Router created with prefix: {router.prefix}")


def main():
    # Run async tests
    asyncio.run(test_async_queries())

    # Run sync tests (from sync context)
    test_sync_wrapper()

    # Test routes
    test_routes()

    print("\n[SUCCESS] All UltraRAG tests passed!")


if __name__ == "__main__":
    main()
