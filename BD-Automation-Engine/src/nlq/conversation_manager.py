"""Phase 33A — Conversation Manager

Multi-turn conversation with context memory. Handles pronoun resolution,
conversation history, follow-up suggestions, and disambiguation.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.nlq.query_router import NLQueryRouter, QueryPlan, QueryResult

logger = logging.getLogger(__name__)


# =========================================
# DATA CLASSES
# =========================================

@dataclass
class ConversationTurn:
    role: str  # "user" or "assistant"
    content: str
    intent: str = ""
    entities: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""
    query_plan: Optional[QueryPlan] = None
    result: Optional[QueryResult] = None


@dataclass
class ConversationResponse:
    answer: str
    intent: str = ""
    confidence: float = 0.0
    data: Any = None
    suggestions: List[str] = field(default_factory=list)
    clarification_needed: Optional[str] = None
    execution_time_ms: float = 0.0
    sources: List[str] = field(default_factory=list)


@dataclass
class ConversationSession:
    user_id: str
    turns: List[ConversationTurn] = field(default_factory=list)
    created_at: str = ""
    last_active: str = ""
    context: Dict[str, Any] = field(default_factory=dict)


# =========================================
# PRONOUN/REFERENCE PATTERNS
# =========================================

_PRONOUNS = {
    "they", "them", "their", "those", "these",
    "it", "its", "that", "this", "the same",
}

_REFERENCE_PATTERNS = [
    "those contacts", "these jobs", "that program", "that contract",
    "the same company", "the same location", "those results",
    "them", "they", "it",
]


class ConversationManager:
    """Multi-turn conversation with context memory."""

    def __init__(
        self,
        query_router: Optional[NLQueryRouter] = None,
        query_executor: Any = None,
        memory_client: Any = None,
    ):
        self.router = query_router or NLQueryRouter()
        self.executor = query_executor
        self.memory = memory_client
        self._sessions: Dict[str, ConversationSession] = {}

    async def ask(
        self, user_id: str, query: str,
    ) -> ConversationResponse:
        """Handle a question with full conversation context."""
        now = datetime.now(timezone.utc).isoformat()
        session = self._get_or_create_session(user_id)

        # 1. Resolve pronouns and references
        resolved_query = self._resolve_references(query, session)

        # 2. Build context from conversation history
        context = self._build_context(session)

        # 3. Route query with context enrichment
        plan = await self.router.route_query(resolved_query, context)

        # 4. Check if clarification is needed
        if plan.clarification_needed:
            # Save pending plan for clarification
            session.context["pending_plan"] = plan
            return ConversationResponse(
                answer=plan.clarification_needed,
                intent=plan.intent,
                confidence=plan.confidence,
                clarification_needed=plan.clarification_needed,
            )

        # 5. Execute query plan
        result = await self._execute_plan(plan)

        # 6. Format response
        answer = await self.router.format_response(result, "natural")

        # 7. Save turn to history
        user_turn = ConversationTurn(
            role="user",
            content=query,
            intent=plan.intent,
            entities=plan.parameters,
            timestamp=now,
            query_plan=plan,
        )
        assistant_turn = ConversationTurn(
            role="assistant",
            content=answer,
            intent=plan.intent,
            entities=plan.parameters,
            timestamp=now,
            result=result,
        )
        session.turns.append(user_turn)
        session.turns.append(assistant_turn)
        session.last_active = now

        # Update context for next turn
        session.context["last_intent"] = plan.intent
        session.context["last_entities"] = plan.parameters
        session.context["last_result_count"] = result.count
        if isinstance(result.data, list):
            session.context["last_result_data"] = result.data[:10]

        # 8. Generate suggestions
        suggestions = await self.get_suggestions(session.context)

        return ConversationResponse(
            answer=answer,
            intent=plan.intent,
            confidence=plan.confidence,
            data=result.data,
            suggestions=suggestions,
            execution_time_ms=result.execution_time_ms,
            sources=result.sources,
        )

    async def clarify(
        self, user_id: str, clarification: str,
    ) -> ConversationResponse:
        """Handle disambiguation responses."""
        session = self._get_or_create_session(user_id)
        pending = session.context.get("pending_plan")

        if pending and isinstance(pending, QueryPlan):
            # Merge clarification into parameters
            pending.parameters["clarification"] = clarification
            pending.clarification_needed = None

            # Re-route with clarification
            return await self.ask(user_id, f"{pending.original_query} ({clarification})")

        # No pending plan — treat as a new question
        return await self.ask(user_id, clarification)

    async def get_suggestions(
        self, context: Dict[str, Any],
    ) -> List[str]:
        """Context-aware follow-up suggestions."""
        intent = context.get("last_intent", "")
        suggestions_map = {
            "search_contacts": [
                "Show their open jobs",
                "Generate outreach emails for these contacts",
                "Who else works at the same company?",
            ],
            "search_jobs": [
                "Who are the best contacts for these jobs?",
                "What's the win probability?",
                "Compare with last quarter",
            ],
            "search_programs": [
                "Show jobs on this program",
                "Who are the key contacts?",
                "When does the contract recompete?",
            ],
            "search_contracts": [
                "Show contacts on this contract",
                "When does it recompete?",
                "What's the hiring forecast?",
            ],
            "analytics": [
                "Which opportunities are stale?",
                "Revenue forecast for next quarter",
                "Compare with last quarter",
            ],
            "prediction": [
                "What would improve the score?",
                "Show all scoring dimensions",
                "Compare with similar opportunities",
            ],
            "forecast": [
                "Who should we approach?",
                "Show related contracts",
                "What's the optimal timing?",
            ],
            "generate": [
                "Review the contact's profile",
                "Draft a follow-up",
                "Schedule the outreach",
            ],
            "compare": [
                "Drill into the first entity",
                "Show the hiring trend",
                "Who are the key contacts?",
            ],
            "status": [
                "Show top opportunities",
                "Any new contacts this week?",
                "What needs immediate attention?",
            ],
        }

        return suggestions_map.get(intent, [
            "Show me the pipeline",
            "What's trending?",
            "Find contacts at Leidos",
        ])

    async def get_conversation_history(
        self, user_id: str, limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Get conversation history for a user."""
        session = self._sessions.get(user_id)
        if not session:
            return []

        turns = session.turns[-limit * 2:]  # user+assistant pairs
        return [
            {
                "role": t.role,
                "content": t.content,
                "intent": t.intent,
                "timestamp": t.timestamp,
            }
            for t in turns
        ]

    async def clear_conversation(self, user_id: str) -> bool:
        """Clear conversation history for a user."""
        if user_id in self._sessions:
            del self._sessions[user_id]
            return True
        return False

    # =========================================
    # INTERNAL HELPERS
    # =========================================

    def _get_or_create_session(self, user_id: str) -> ConversationSession:
        """Get or create a conversation session."""
        if user_id not in self._sessions:
            self._sessions[user_id] = ConversationSession(
                user_id=user_id,
                created_at=datetime.now(timezone.utc).isoformat(),
                last_active=datetime.now(timezone.utc).isoformat(),
            )
        return self._sessions[user_id]

    def _resolve_references(self, query: str, session: ConversationSession) -> str:
        """Resolve pronouns and references from conversation context."""
        if not session.turns:
            return query

        query_lower = query.lower()

        # Check for pronoun references
        has_reference = any(ref in query_lower for ref in _REFERENCE_PATTERNS)
        if not has_reference:
            return query

        # Get last entities from context
        last_entities = session.context.get("last_entities", {})

        # Replace references with actual entities
        resolved = query
        if "those contacts" in query_lower or "them" in query_lower:
            if last_entities.get("companies"):
                resolved = query + f" at {last_entities['companies'][0]}"
            elif last_entities.get("programs"):
                resolved = query + f" for {last_entities['programs'][0]}"

        if "that program" in query_lower or "this program" in query_lower:
            if last_entities.get("programs"):
                resolved = resolved.replace("that program", last_entities["programs"][0])
                resolved = resolved.replace("this program", last_entities["programs"][0])

        if "the same company" in query_lower:
            if last_entities.get("companies"):
                resolved = resolved.replace("the same company", last_entities["companies"][0])

        if "the same location" in query_lower:
            if last_entities.get("locations"):
                resolved = resolved.replace("the same location", last_entities["locations"][0])

        if resolved != query:
            logger.debug(f"Resolved references: '{query}' → '{resolved}'")

        return resolved

    def _build_context(self, session: ConversationSession) -> Dict[str, Any]:
        """Build context dictionary from session history."""
        context = dict(session.context)

        # Add recent intents for pattern detection
        recent_intents = [
            t.intent for t in session.turns[-6:]
            if t.role == "user" and t.intent
        ]
        context["recent_intents"] = recent_intents

        return context

    async def _execute_plan(self, plan: QueryPlan) -> QueryResult:
        """Execute a query plan through the executor."""
        if self.executor:
            return await self.executor.execute(plan)

        # No executor — return plan info as result
        return QueryResult(
            data={"plan": plan.intent, "parameters": plan.parameters},
            summary=f"Query classified as {plan.intent} with confidence {plan.confidence:.0%}",
            count=0,
            intent=plan.intent,
            parameters=plan.parameters,
        )
