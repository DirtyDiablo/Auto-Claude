"""
BD Memory Module - Supermemory AI Integration.

Provides document-level memory storage and retrieval for BD Intelligence.
Complements Mem0 conversation memory with document-level semantic search.

Usage:
    from memory import BDMemoryManager, get_bd_memory_manager

    # Quick access via singleton
    manager = get_bd_memory_manager()

    # Or create instance
    async with BDMemoryManager(supermemory_key="...") as manager:
        await manager.store_rfp("rfp.pdf", "DCGS RFP", agency="Air Force")
        results = await manager.search_rfps("DCGS requirements")

API Integration:
    from memory import memory_router
    app.include_router(memory_router)  # Adds /memory/* endpoints
"""

from .supermemory_client import (
    SupermemoryClient,
    BDMemoryManager,
    get_bd_memory_manager,
)
from .routes import router as memory_router

__all__ = [
    "SupermemoryClient",
    "BDMemoryManager",
    "get_bd_memory_manager",
    "memory_router",
]
