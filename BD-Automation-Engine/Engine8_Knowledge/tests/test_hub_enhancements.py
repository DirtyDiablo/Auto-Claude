"""
Test Hub Enhancements
Verifies all enhancement packages and scripts are properly installed and working.
"""

import os
import sys
import logging

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_packages():
    """Test that all enhancement packages are installed."""
    print("\n" + "=" * 60)
    print("TESTING PACKAGE INSTALLATIONS")
    print("=" * 60 + "\n")

    packages = {
        "rank_bm25": "BM25 Search",
        "mem0": "Memory Layer",
        "redis": "Redis Client",
        "crewai": "Agent Framework",
        "langgraph": "Workflow Engine",
        "langchain_anthropic": "Anthropic Integration",
    }

    results = {}
    for pkg, desc in packages.items():
        try:
            __import__(pkg)
            results[pkg] = {"status": "OK", "description": desc}
            print(f"  [OK] {pkg} - {desc}")
        except ImportError as e:
            results[pkg] = {"status": "MISSING", "description": desc, "error": str(e)}
            print(f"  [MISSING] {pkg} - {desc}")

    return results


def test_scripts():
    """Test that all enhancement scripts exist and can be imported."""
    print("\n" + "=" * 60)
    print("TESTING SCRIPT FILES")
    print("=" * 60 + "\n")

    scripts = [
        ("Engine8_Knowledge.schemas.vector_collections", "Vector Collections Schema"),
        ("Engine8_Knowledge.scripts.hybrid_retriever", "Hybrid Retriever"),
        ("Engine8_Knowledge.scripts.memory_system", "Memory System"),
        ("Engine8_Knowledge.scripts.rag_router", "RAG Router"),
        ("Engine8_Knowledge.scripts.init_bm25", "BM25 Initializer"),
        ("Engine8_Knowledge.scripts.memory_layer", "Memory Layer (existing)"),
        ("Engine8_Knowledge.scripts.lightrag_engine", "LightRAG Engine (existing)"),
    ]

    results = {}
    for module, desc in scripts:
        try:
            __import__(module)
            results[module] = {"status": "OK", "description": desc}
            print(f"  [OK] {module}")
        except ImportError as e:
            results[module] = {"status": "ERROR", "description": desc, "error": str(e)}
            print(f"  [ERROR] {module}: {e}")

    return results


def test_memory_system():
    """Test memory system functionality."""
    print("\n" + "=" * 60)
    print("TESTING MEMORY SYSTEM")
    print("=" * 60 + "\n")

    try:
        from Engine8_Knowledge.scripts.memory_system import get_memory_system

        system = get_memory_system()

        # Test remember/recall
        memory_id = system.remember("Test memory for verification", memory_type="test")
        print(f"  [OK] Created memory: {memory_id[:8]}...")

        # Test recall
        results = system.recall("verification", limit=5)
        print(f"  [OK] Recall returned {len(results)} results")

        # Test contact interaction
        system.log_contact_interaction(
            contact="Test Contact",
            type="email",
            notes="Verification test",
            outcome="success",
        )
        print("  [OK] Logged contact interaction")

        # Test program insight
        system.log_program_insight(
            program="Test Program", insight="Verification test insight", source="test"
        )
        print("  [OK] Logged program insight")

        # Test context retrieval
        contact_ctx = system.get_contact_context("Test Contact")
        print(
            f"  [OK] Contact context: {len(contact_ctx.get('interactions', []))} interactions"
        )

        program_ctx = system.get_program_context("Test Program")
        print(
            f"  [OK] Program context: {len(program_ctx.get('insights', []))} insights"
        )

        # Test stats
        stats = system.get_stats()
        print(f"  [OK] Stats: {stats}")

        return {"status": "OK", "stats": stats}

    except Exception as e:
        print(f"  [ERROR] {e}")
        return {"status": "ERROR", "error": str(e)}


def test_rag_router():
    """Test RAG router functionality."""
    print("\n" + "=" * 60)
    print("TESTING RAG ROUTER")
    print("=" * 60 + "\n")

    try:
        from Engine8_Knowledge.scripts.rag_router import (
            get_rag_router,
            RetrievalStrategy,
        )

        router = get_rag_router()

        # Test query analysis
        test_queries = [
            ("Who works on DCGS?", RetrievalStrategy.LIGHTRAG),
            ("contract number FA123", RetrievalStrategy.BM25),
            ("How should we approach Leidos?", RetrievalStrategy.HYBRID),
        ]

        for query, expected in test_queries:
            strategy = router.analyze_query(query)
            status = "OK" if strategy == expected else "UNEXPECTED"
            print(f"  [{status}] '{query[:30]}...' -> {strategy.value}")

        # Test available strategies
        strategies = router.get_available_strategies()
        print(f"  [OK] Available strategies: {strategies}")

        return {"status": "OK", "strategies": strategies}

    except Exception as e:
        print(f"  [ERROR] {e}")
        return {"status": "ERROR", "error": str(e)}


def test_vector_schema():
    """Test vector collections schema."""
    print("\n" + "=" * 60)
    print("TESTING VECTOR COLLECTIONS SCHEMA")
    print("=" * 60 + "\n")

    try:
        from Engine8_Knowledge.schemas.vector_collections import COLLECTIONS

        # Test collections definition
        expected_collections = [
            "jobs",
            "contacts",
            "programs",
            "documents",
            "memories",
            "knowledge_graph",
        ]
        for coll in expected_collections:
            if coll in COLLECTIONS:
                print(f"  [OK] Collection defined: {coll}")
            else:
                print(f"  [MISSING] Collection not defined: {coll}")

        return {"status": "OK", "collections": list(COLLECTIONS.keys())}

    except Exception as e:
        print(f"  [ERROR] {e}")
        return {"status": "ERROR", "error": str(e)}


def run_all_tests():
    """Run all tests and generate report."""
    print("\n" + "#" * 60)
    print("#  BD INTELLIGENCE HUB ENHANCEMENT VERIFICATION")
    print("#" * 60)

    results = {
        "packages": test_packages(),
        "scripts": test_scripts(),
        "vector_schema": test_vector_schema(),
        "rag_router": test_rag_router(),
        "memory_system": test_memory_system(),
    }

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_ok = True
    for category, result in results.items():
        if isinstance(result, dict):
            if result.get("status") == "OK":
                print(f"  [OK] {category}")
            elif result.get("status") == "ERROR":
                print(f"  [ERROR] {category}: {result.get('error', 'Unknown')}")
                all_ok = False
            else:
                # Check individual results
                errors = [
                    k
                    for k, v in result.items()
                    if isinstance(v, dict) and v.get("status") != "OK"
                ]
                if errors:
                    print(f"  [PARTIAL] {category}: {len(errors)} issues")
                else:
                    print(f"  [OK] {category}")

    print("\n" + "=" * 60)
    if all_ok:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED - Review errors above")
    print("=" * 60 + "\n")

    return results


if __name__ == "__main__":
    run_all_tests()
