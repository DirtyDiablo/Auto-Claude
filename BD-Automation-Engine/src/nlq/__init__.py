"""Phase 33A — Natural Language Query Engine + Conversational BI."""

from src.nlq.query_router import NLQueryRouter, QueryPlan, QueryIntent
from src.nlq.query_executor import QueryExecutor, QueryResult
from src.nlq.conversation_manager import ConversationManager, ConversationResponse
from src.nlq.autocomplete import SmartAutocomplete, Suggestion

__all__ = [
    "NLQueryRouter",
    "QueryPlan",
    "QueryIntent",
    "QueryExecutor",
    "QueryResult",
    "ConversationManager",
    "ConversationResponse",
    "SmartAutocomplete",
    "Suggestion",
]
