"""
Contact Enrichment Workflow — Refresh stale contacts (4 nodes).

Nodes:
    1. fetch_stale    — Find contacts not enriched in 30+ days
    2. enrich_bullhorn — Pull latest data from Bullhorn CRM
    3. enrich_web      — Placeholder for web enrichment
    4. update_store    — Upsert refreshed contacts to Qdrant
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

try:
    import structlog
    _log = structlog.get_logger("workflows.contact_enrichment")
except ImportError:
    _log = logging.getLogger("workflows.contact_enrichment")

try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict

try:
    from langgraph.graph import END, StateGraph
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    StateGraph = None
    END = "__end__"


# ===================================================================
# State
# ===================================================================

class EnrichmentState(TypedDict, total=False):
    """State for the contact enrichment workflow."""
    stale_contacts: List[Dict[str, Any]]
    bullhorn_enriched: List[Dict[str, Any]]
    web_enriched: List[Dict[str, Any]]
    updated_contacts: List[Dict[str, Any]]
    errors: List[str]
    metadata: Dict[str, Any]


def make_enrichment_state(**overrides: Any) -> EnrichmentState:
    state: EnrichmentState = {
        "stale_contacts": [],
        "bullhorn_enriched": [],
        "web_enriched": [],
        "updated_contacts": [],
        "errors": [],
        "metadata": {},
    }
    state.update(overrides)  # type: ignore[typeddict-item]
    return state


# ===================================================================
# Node implementations
# ===================================================================

def fetch_stale(state: EnrichmentState) -> EnrichmentState:
    """Find contacts not enriched in the last 30 days."""
    try:
        cutoff = datetime.utcnow() - timedelta(days=30)
        cutoff_iso = cutoff.isoformat()

        try:
            from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore
            store = BDKnowledgeStore()
            # Search for all contacts, then filter stale ones
            results = store.search(
                query="contact",
                collection="contacts",
                limit=500,
            )
            stale = []
            for r in (results or []):
                meta = r.get("metadata", {})
                last_enriched = meta.get("last_enriched", "")
                if not last_enriched or last_enriched < cutoff_iso:
                    stale.append(r)
            state["stale_contacts"] = stale
            _log.info("fetch_stale.done", stale_count=len(stale),
                       total_checked=len(results or []))
        except ImportError:
            _log.warning("fetch_stale.no_store", msg="BDKnowledgeStore not available")
    except Exception as exc:
        state.setdefault("errors", []).append(f"fetch_stale: {exc}")
        _log.error("fetch_stale.failed", error=str(exc))
    return state


def enrich_bullhorn(state: EnrichmentState) -> EnrichmentState:
    """Pull latest contact data from Bullhorn CRM."""
    stale = state.get("stale_contacts", [])
    if not stale:
        _log.info("enrich_bullhorn.skip", reason="no stale contacts")
        state["bullhorn_enriched"] = []
        return state

    try:
        from Engine7_BullhornETL.scripts.bullhorn_etl_v2 import BullhornETL
        etl = BullhornETL()
        enriched = []
        for contact in stale:
            contact_id = contact.get("id") or contact.get("metadata", {}).get("id")
            if contact_id:
                try:
                    fresh_data = etl.get_contact(contact_id)
                    if fresh_data:
                        merged = {**contact, **fresh_data,
                                  "last_enriched": datetime.utcnow().isoformat()}
                        enriched.append(merged)
                    else:
                        enriched.append(contact)
                except Exception:
                    enriched.append(contact)
            else:
                enriched.append(contact)
        state["bullhorn_enriched"] = enriched
        _log.info("enrich_bullhorn.done", enriched_count=len(enriched))
    except ImportError:
        _log.warning("enrich_bullhorn.no_engine", msg="Engine7 not available")
        state["bullhorn_enriched"] = stale
    except Exception as exc:
        state.setdefault("errors", []).append(f"enrich_bullhorn: {exc}")
        _log.error("enrich_bullhorn.failed", error=str(exc))
        state["bullhorn_enriched"] = stale
    return state


def enrich_web(state: EnrichmentState) -> EnrichmentState:
    """Placeholder for web-based contact enrichment.

    Future: LinkedIn, company website, news articles, etc.
    """
    contacts = state.get("bullhorn_enriched", [])
    # Pass through for now — web enrichment is a future enhancement
    state["web_enriched"] = [
        {**c, "web_enrichment": "pending"} for c in contacts
    ]
    _log.info("enrich_web.placeholder", count=len(contacts))
    return state


def update_store(state: EnrichmentState) -> EnrichmentState:
    """Upsert enriched contacts back to Qdrant vector store."""
    contacts = state.get("web_enriched", [])
    if not contacts:
        _log.info("update_store.skip", reason="no contacts to update")
        state["updated_contacts"] = []
        return state

    try:
        from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore
        store = BDKnowledgeStore()
        updated = []
        for contact in contacts:
            try:
                text = (
                    f"{contact.get('name', '')} "
                    f"{contact.get('title', '')} "
                    f"{contact.get('company', '')} "
                    f"{contact.get('email', '')}"
                ).strip()
                if text:
                    store.upsert(
                        collection="contacts",
                        text=text,
                        metadata=contact.get("metadata", contact),
                    )
                    updated.append(contact)
            except Exception as exc:
                _log.warning("update_store.upsert_error", error=str(exc))
        state["updated_contacts"] = updated
        _log.info("update_store.done", count=len(updated))
    except ImportError:
        _log.warning("update_store.no_store", msg="BDKnowledgeStore not available")
        state["updated_contacts"] = contacts
    except Exception as exc:
        state.setdefault("errors", []).append(f"update_store: {exc}")
        _log.error("update_store.failed", error=str(exc))
        state["updated_contacts"] = contacts
    return state


# ===================================================================
# Graph builder
# ===================================================================

def build_contact_enrichment():
    """Compile the contact enrichment StateGraph."""
    if not LANGGRAPH_AVAILABLE:
        _log.warning("langgraph not installed — returning None")
        return None

    graph = StateGraph(EnrichmentState)
    graph.add_node("fetch_stale", fetch_stale)
    graph.add_node("enrich_bullhorn", enrich_bullhorn)
    graph.add_node("enrich_web", enrich_web)
    graph.add_node("update_store", update_store)

    graph.add_edge("fetch_stale", "enrich_bullhorn")
    graph.add_edge("enrich_bullhorn", "enrich_web")
    graph.add_edge("enrich_web", "update_store")
    graph.add_edge("update_store", END)

    graph.set_entry_point("fetch_stale")
    return graph.compile()


def run_contact_enrichment(
    initial_state: EnrichmentState | None = None,
) -> EnrichmentState:
    """Convenience runner for the contact enrichment workflow."""
    state = initial_state or make_enrichment_state()

    compiled = build_contact_enrichment()
    if compiled is not None:
        return compiled.invoke(state)

    # Fallback: sequential
    for fn in [fetch_stale, enrich_bullhorn, enrich_web, update_store]:
        state = fn(state)
    return state
