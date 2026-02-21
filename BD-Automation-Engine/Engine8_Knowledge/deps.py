"""Dependency injection for BD Knowledge API routers.

Global state is initialized in api.py's lifespan handler. Routers use
these dependency functions to access shared instances without importing
mutable globals directly.
"""

from typing import Any, Optional


# Registry of global instances — populated by api.py lifespan
_registry: dict[str, Any] = {}


def register(name: str, instance: Any) -> None:
    """Register a global instance (called from api.py lifespan)."""
    _registry[name] = instance


def get_store():
    """Get BDKnowledgeStore instance."""
    return _registry.get("store")


def get_rag_engine():
    """Get BDRAGEngine instance."""
    return _registry.get("rag_engine")


def get_indexer():
    """Get BDIndexer instance."""
    return _registry.get("indexer")


def get_memory():
    """Get memory layer instance."""
    return _registry.get("memory")


def get_graph():
    """Get LightRAG knowledge graph instance."""
    return _registry.get("graph")


def get_retriever():
    """Get hybrid retriever instance."""
    return _registry.get("retriever")


def get_query_router():
    """Get query router instance."""
    return _registry.get("router")


def get_pageindex():
    """Get pageindex engine instance."""
    return _registry.get("pageindex")


def get_cache():
    """Get Redis cache instance."""
    return _registry.get("cache")


def get_orchestrator():
    """Get CrewAI orchestrator instance."""
    return _registry.get("orchestrator")
