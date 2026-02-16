"""Phase 33A: Natural Language Query API — 9 endpoints.

POST   /nlq/ask                  — Natural language query
POST   /nlq/clarify              — Provide clarification
GET    /nlq/suggestions          — Follow-up suggestions
GET    /nlq/autocomplete         — Typeahead suggestions
GET    /nlq/history              — Conversation history
DELETE /nlq/history              — Clear conversation
GET    /nlq/intents              — List supported query intents
GET    /nlq/examples             — Example queries per intent
POST   /nlq/feedback             — Rate response quality
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from src.nlq.query_router import NLQueryRouter, QueryIntent, EXAMPLE_QUERIES
from src.nlq.query_executor import QueryExecutor
from src.nlq.conversation_manager import ConversationManager
from src.nlq.autocomplete import SmartAutocomplete

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nlq", tags=["natural-language-query"])


# =========================================
# REQUEST/RESPONSE MODELS
# =========================================


class AskRequest(BaseModel):
    query: str = Field(
        ..., min_length=1, max_length=2000, description="Natural language query"
    )
    user_id: str = Field(
        default="default", description="User identifier for conversation context"
    )
    format: str = Field(
        default="natural",
        description="Response format: natural, table, chart, brief, detailed",
    )


class ClarifyRequest(BaseModel):
    clarification: str = Field(..., min_length=1, max_length=500)
    user_id: str = Field(default="default")


class FeedbackRequest(BaseModel):
    query: str = Field(..., description="The original query")
    rating: int = Field(..., ge=1, le=5, description="Rating 1-5")
    comment: str = Field(default="", max_length=500)
    user_id: str = Field(default="default")


# =========================================
# MODULE STATE
# =========================================

_router_instance: Optional[NLQueryRouter] = None
_executor_instance: Optional[QueryExecutor] = None
_conversation_mgr: Optional[ConversationManager] = None
_autocomplete: Optional[SmartAutocomplete] = None
_feedback_store: List[Dict[str, Any]] = []


def _get_router() -> NLQueryRouter:
    global _router_instance
    if _router_instance is None:
        _router_instance = NLQueryRouter()
    return _router_instance


def _get_executor() -> QueryExecutor:
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = QueryExecutor()
    return _executor_instance


def _get_conversation_mgr() -> ConversationManager:
    global _conversation_mgr
    if _conversation_mgr is None:
        _conversation_mgr = ConversationManager(
            query_router=_get_router(),
            query_executor=_get_executor(),
        )
    return _conversation_mgr


def _get_autocomplete() -> SmartAutocomplete:
    global _autocomplete
    if _autocomplete is None:
        _autocomplete = SmartAutocomplete()
    return _autocomplete


# =========================================
# ENDPOINTS
# =========================================


@router.post("/ask")
async def nlq_ask(request: AskRequest) -> Dict[str, Any]:
    """Natural language query — the main endpoint."""
    mgr = _get_conversation_mgr()
    response = await mgr.ask(request.user_id, request.query)

    # Reformat if requested
    if request.format != "natural" and response.data:
        from src.nlq.query_router import QueryResult

        result = QueryResult(
            data=response.data,
            summary=response.answer,
            count=len(response.data) if isinstance(response.data, list) else 1,
            intent=response.intent,
        )
        formatted = await _get_router().format_response(result, request.format)
        response.answer = formatted

    return {
        "answer": response.answer,
        "intent": response.intent,
        "confidence": response.confidence,
        "data": response.data,
        "suggestions": response.suggestions,
        "clarification_needed": response.clarification_needed,
        "execution_time_ms": response.execution_time_ms,
        "sources": response.sources,
    }


@router.post("/clarify")
async def nlq_clarify(request: ClarifyRequest) -> Dict[str, Any]:
    """Provide clarification for an ambiguous query."""
    mgr = _get_conversation_mgr()
    response = await mgr.clarify(request.user_id, request.clarification)
    return {
        "answer": response.answer,
        "intent": response.intent,
        "confidence": response.confidence,
        "data": response.data,
        "suggestions": response.suggestions,
    }


@router.get("/suggestions")
async def nlq_suggestions(
    user_id: str = Query(default="default"),
) -> Dict[str, Any]:
    """Get follow-up suggestions based on conversation context."""
    mgr = _get_conversation_mgr()
    session = mgr._sessions.get(user_id)
    context = session.context if session else {}
    suggestions = await mgr.get_suggestions(context)
    return {"suggestions": suggestions, "user_id": user_id}


@router.get("/autocomplete")
async def nlq_autocomplete(
    q: str = Query(default="", description="Partial query"),
    limit: int = Query(default=8, ge=1, le=20),
) -> Dict[str, Any]:
    """Typeahead suggestions as user types."""
    ac = _get_autocomplete()
    suggestions = await ac.suggest(q, limit=limit)
    return {
        "query": q,
        "suggestions": [
            {"text": s.text, "category": s.category, "score": s.score}
            for s in suggestions
        ],
        "total": len(suggestions),
    }


@router.get("/history")
async def nlq_history(
    user_id: str = Query(default="default"),
    limit: int = Query(default=20, ge=1, le=100),
) -> Dict[str, Any]:
    """Get conversation history for a user."""
    mgr = _get_conversation_mgr()
    history = await mgr.get_conversation_history(user_id, limit)
    return {"history": history, "total": len(history), "user_id": user_id}


@router.delete("/history")
async def nlq_clear_history(
    user_id: str = Query(default="default"),
) -> Dict[str, Any]:
    """Clear conversation history for a user."""
    mgr = _get_conversation_mgr()
    cleared = await mgr.clear_conversation(user_id)
    return {"cleared": cleared, "user_id": user_id}


@router.get("/intents")
async def nlq_intents() -> Dict[str, Any]:
    """List all supported query intents."""
    intents = [
        {"name": intent.value, "description": desc}
        for intent, desc in [
            (
                QueryIntent.SEARCH_CONTACTS,
                "Search for contacts by company, role, tier, location",
            ),
            (
                QueryIntent.SEARCH_JOBS,
                "Find job openings by clearance, location, program",
            ),
            (QueryIntent.SEARCH_PROGRAMS, "Look up federal programs and contracts"),
            (
                QueryIntent.SEARCH_CONTRACTS,
                "Search contract awards, recompetes, task orders",
            ),
            (QueryIntent.GRAPH_QUERY, "Explore relationship networks and connections"),
            (QueryIntent.ANALYTICS, "Pipeline metrics, conversion rates, KPIs"),
            (QueryIntent.PREDICTION, "Win probability and opportunity scoring"),
            (QueryIntent.FORECAST, "Hiring trends, demand forecasting, ramp signals"),
            (QueryIntent.CAMPAIGN, "Create and manage outreach campaigns"),
            (QueryIntent.GENERATE, "Generate emails, call scripts, meeting prep"),
            (
                QueryIntent.COMPARE,
                "Compare companies, programs, locations side-by-side",
            ),
            (QueryIntent.EXPLAIN, "Explain scores, predictions, and rankings"),
            (QueryIntent.STATUS, "Daily digest and recent activity summary"),
            (QueryIntent.MEMORY, "Recall previous interactions and stored knowledge"),
        ]
    ]
    return {"intents": intents, "total": len(intents)}


@router.get("/examples")
async def nlq_examples(
    intent: Optional[str] = Query(default=None, description="Filter by intent"),
) -> Dict[str, Any]:
    """Example queries per intent."""
    if intent:
        examples = EXAMPLE_QUERIES.get(intent, [])
        return {"intent": intent, "examples": examples}
    return {"examples": EXAMPLE_QUERIES, "total_intents": len(EXAMPLE_QUERIES)}


@router.post("/feedback")
async def nlq_feedback(request: FeedbackRequest) -> Dict[str, Any]:
    """Rate response quality for improvement."""
    feedback_entry = {
        "query": request.query,
        "rating": request.rating,
        "comment": request.comment,
        "user_id": request.user_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _feedback_store.append(feedback_entry)

    # Track in autocomplete if positive
    if request.rating >= 4:
        ac = _get_autocomplete()
        ac.add_recent_query(request.query)

    return {
        "status": "recorded",
        "feedback_id": len(_feedback_store),
        "message": "Thank you for your feedback!",
    }


# =========================================
# ROUTER INTEGRATION
# =========================================


def configure_nlq(
    search_client: Any = None,
    graph_client: Any = None,
    analytics_client: Any = None,
    prediction_client: Any = None,
    campaign_client: Any = None,
    memory_client: Any = None,
) -> None:
    """Wire up NLQ components during app startup."""
    global _executor_instance, _conversation_mgr
    _executor_instance = QueryExecutor(
        search_client=search_client,
        graph_client=graph_client,
        analytics_client=analytics_client,
        prediction_client=prediction_client,
        campaign_client=campaign_client,
        memory_client=memory_client,
    )
    _conversation_mgr = ConversationManager(
        query_router=_get_router(),
        query_executor=_executor_instance,
        memory_client=memory_client,
    )


def include_nlq_router(app, **kwargs):
    """Include the Phase 33A NLQ router in the main FastAPI app."""
    configure_nlq(**kwargs)
    app.include_router(router)
    logger.info("Phase 33A NLQ routes enabled: /nlq/* (9 endpoints)")
