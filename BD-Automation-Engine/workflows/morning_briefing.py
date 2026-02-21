"""
Morning Briefing Workflow — Daily intelligence briefing (3 nodes).

Nodes:
    1. gather_signals — Query Qdrant for recent changes, new jobs, hiring signals
    2. analyze        — Summarize key findings (mock LLM call)
    3. format_brief   — Generate structured briefing dict
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

try:
    import structlog
    _log = structlog.get_logger("workflows.morning_briefing")
except ImportError:
    _log = logging.getLogger("workflows.morning_briefing")

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

class BriefingState(TypedDict, total=False):
    """State for the morning briefing workflow."""
    signals: List[Dict[str, Any]]
    analysis: Dict[str, Any]
    briefing: Dict[str, Any]
    errors: List[str]
    metadata: Dict[str, Any]


def make_briefing_state(**overrides: Any) -> BriefingState:
    state: BriefingState = {
        "signals": [],
        "analysis": {},
        "briefing": {},
        "errors": [],
        "metadata": {},
    }
    state.update(overrides)  # type: ignore[typeddict-item]
    return state


# ===================================================================
# Node implementations
# ===================================================================

def gather_signals(state: BriefingState) -> BriefingState:
    """Query Qdrant for recent changes, new jobs, and hiring signals."""
    started = datetime.utcnow()
    try:
        from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore
        store = BDKnowledgeStore()
        # Search for recent activity across collections
        signals: List[Dict[str, Any]] = []
        for collection in ["jobs", "contacts", "activities"]:
            try:
                results = store.search(
                    query="recent hiring activity new positions",
                    collection=collection,
                    limit=10,
                )
                for r in (results or []):
                    signals.append({
                        "collection": collection,
                        "content": r.get("content", r.get("text", "")),
                        "score": r.get("score", 0),
                        "metadata": r.get("metadata", {}),
                    })
            except Exception as exc:
                _log.warning("gather_signals.collection_error",
                             collection=collection, error=str(exc))
        state["signals"] = signals
        _log.info("gather_signals.done", count=len(signals))
    except ImportError:
        _log.warning("gather_signals.no_store", msg="BDKnowledgeStore not available")
    except Exception as exc:
        state.setdefault("errors", []).append(f"gather_signals: {exc}")
        _log.error("gather_signals.failed", error=str(exc))
    return state


def analyze(state: BriefingState) -> BriefingState:
    """Summarize key findings from gathered signals (mock LLM call)."""
    signals = state.get("signals", [])
    try:
        # Group signals by collection
        by_collection: Dict[str, List] = {}
        for sig in signals:
            coll = sig.get("collection", "unknown")
            by_collection.setdefault(coll, []).append(sig)

        analysis = {
            "total_signals": len(signals),
            "collections_scanned": list(by_collection.keys()),
            "signal_counts": {k: len(v) for k, v in by_collection.items()},
            "top_signals": signals[:5],
            "generated_at": datetime.utcnow().isoformat(),
            "summary": (
                f"Detected {len(signals)} signals across "
                f"{len(by_collection)} collections. "
                f"Top areas: {', '.join(by_collection.keys())}."
            ),
        }
        state["analysis"] = analysis
        _log.info("analyze.done", total_signals=len(signals))
    except Exception as exc:
        state.setdefault("errors", []).append(f"analyze: {exc}")
        _log.error("analyze.failed", error=str(exc))
    return state


def format_brief(state: BriefingState) -> BriefingState:
    """Generate a structured briefing dict from analysis."""
    analysis = state.get("analysis", {})
    try:
        now = datetime.utcnow()
        briefing = {
            "title": f"BD Intelligence Briefing - {now.strftime('%Y-%m-%d')}",
            "generated_at": now.isoformat(),
            "executive_summary": analysis.get("summary", "No signals detected."),
            "signal_count": analysis.get("total_signals", 0),
            "collections": analysis.get("collections_scanned", []),
            "highlights": [
                {
                    "collection": s.get("collection"),
                    "content": (s.get("content", "")[:200]
                                if s.get("content") else ""),
                    "relevance_score": s.get("score", 0),
                }
                for s in analysis.get("top_signals", [])
            ],
            "recommendations": [
                "Review top-scoring signals for immediate BD action",
                "Cross-reference new contacts with existing program map",
                "Update call lists for any Tier 1/2 contacts identified",
            ],
        }
        state["briefing"] = briefing
        _log.info("format_brief.done")
    except Exception as exc:
        state.setdefault("errors", []).append(f"format_brief: {exc}")
        _log.error("format_brief.failed", error=str(exc))
    return state


# ===================================================================
# Graph builder
# ===================================================================

def build_morning_briefing():
    """Compile the morning briefing StateGraph."""
    if not LANGGRAPH_AVAILABLE:
        _log.warning("langgraph not installed — returning None")
        return None

    graph = StateGraph(BriefingState)
    graph.add_node("gather_signals", gather_signals)
    graph.add_node("analyze", analyze)
    graph.add_node("format_brief", format_brief)

    graph.add_edge("gather_signals", "analyze")
    graph.add_edge("analyze", "format_brief")
    graph.add_edge("format_brief", END)

    graph.set_entry_point("gather_signals")
    return graph.compile()


def run_morning_briefing(
    initial_state: BriefingState | None = None,
) -> BriefingState:
    """Convenience runner for the morning briefing workflow."""
    state = initial_state or make_briefing_state()

    compiled = build_morning_briefing()
    if compiled is not None:
        return compiled.invoke(state)

    # Fallback: sequential
    for fn in [gather_signals, analyze, format_brief]:
        state = fn(state)
    return state
