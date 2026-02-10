"""Tests for Phase 33A — Conversation Manager."""

import pytest

from src.nlq.query_router import NLQueryRouter
from src.nlq.query_executor import QueryExecutor
from src.nlq.conversation_manager import (
    ConversationManager,
    ConversationResponse,
    ConversationSession,
    ConversationTurn,
)


# =========================================
# FIXTURES
# =========================================

@pytest.fixture
def manager():
    router = NLQueryRouter()
    executor = QueryExecutor()
    return ConversationManager(query_router=router, query_executor=executor)


# =========================================
# BASIC ASK
# =========================================

@pytest.mark.asyncio
class TestBasicAsk:
    async def test_ask_returns_response(self, manager):
        resp = await manager.ask("user1", "Find contacts at Leidos")
        assert isinstance(resp, ConversationResponse)

    async def test_response_has_answer(self, manager):
        resp = await manager.ask("user1", "Show TS/SCI jobs in San Diego")
        assert isinstance(resp.answer, str)
        assert len(resp.answer) > 0

    async def test_response_has_intent(self, manager):
        resp = await manager.ask("user1", "Find contacts at GDIT")
        assert resp.intent != ""

    async def test_response_has_confidence(self, manager):
        resp = await manager.ask("user1", "Find jobs")
        assert 0.0 <= resp.confidence <= 1.0

    async def test_response_has_suggestions(self, manager):
        resp = await manager.ask("user1", "Show pipeline analytics")
        assert isinstance(resp.suggestions, list)
        assert len(resp.suggestions) > 0


# =========================================
# MULTI-TURN CONTEXT
# =========================================

@pytest.mark.asyncio
class TestMultiTurnContext:
    async def test_second_turn_has_context(self, manager):
        await manager.ask("user1", "Find contacts at Leidos")
        # Second turn should have context from first
        resp = await manager.ask("user1", "Show their jobs")
        assert isinstance(resp, ConversationResponse)

    async def test_context_tracks_last_intent(self, manager):
        await manager.ask("user1", "Find contacts at Leidos")
        session = manager._sessions.get("user1")
        assert session is not None
        assert session.context.get("last_intent") is not None

    async def test_context_tracks_entities(self, manager):
        await manager.ask("user1", "Find contacts at leidos")
        session = manager._sessions["user1"]
        entities = session.context.get("last_entities", {})
        assert "leidos" in entities.get("companies", [])

    async def test_different_users_separate_sessions(self, manager):
        await manager.ask("user1", "Find contacts at Leidos")
        await manager.ask("user2", "Show jobs in San Diego")
        assert "user1" in manager._sessions
        assert "user2" in manager._sessions
        assert manager._sessions["user1"].context.get("last_intent") != \
               manager._sessions["user2"].context.get("last_intent")


# =========================================
# CLARIFICATION
# =========================================

@pytest.mark.asyncio
class TestClarification:
    async def test_clarify_with_pending(self, manager):
        # Force a clarification scenario
        session = manager._get_or_create_session("user1")
        from src.nlq.query_router import QueryPlan
        session.context["pending_plan"] = QueryPlan(
            intent="search_contacts",
            parameters={"search_query": "PACAF contacts"},
            confidence=0.5,
            clarification_needed="Hickam or Langley?",
            original_query="Find PACAF contacts",
        )
        resp = await manager.clarify("user1", "Hickam")
        assert isinstance(resp, ConversationResponse)

    async def test_clarify_without_pending(self, manager):
        # No pending plan — should just ask normally
        resp = await manager.clarify("user1", "Find jobs in San Diego")
        assert isinstance(resp, ConversationResponse)


# =========================================
# CONVERSATION HISTORY
# =========================================

@pytest.mark.asyncio
class TestConversationHistory:
    async def test_history_grows(self, manager):
        await manager.ask("user1", "Find contacts at Leidos")
        history = await manager.get_conversation_history("user1")
        assert len(history) == 2  # user turn + assistant turn

    async def test_history_limit(self, manager):
        for i in range(5):
            await manager.ask("user1", f"Query number {i}")
        history = await manager.get_conversation_history("user1", limit=3)
        assert len(history) <= 6  # limit * 2 (user+assistant pairs)

    async def test_empty_history(self, manager):
        history = await manager.get_conversation_history("nonexistent")
        assert history == []

    async def test_clear_conversation(self, manager):
        await manager.ask("user1", "Find jobs")
        cleared = await manager.clear_conversation("user1")
        assert cleared is True
        history = await manager.get_conversation_history("user1")
        assert history == []

    async def test_clear_nonexistent(self, manager):
        cleared = await manager.clear_conversation("nonexistent")
        assert cleared is False


# =========================================
# SUGGESTIONS
# =========================================

@pytest.mark.asyncio
class TestSuggestions:
    async def test_suggestions_for_contact_search(self, manager):
        context = {"last_intent": "search_contacts"}
        suggestions = await manager.get_suggestions(context)
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0

    async def test_suggestions_for_analytics(self, manager):
        context = {"last_intent": "analytics"}
        suggestions = await manager.get_suggestions(context)
        assert len(suggestions) > 0

    async def test_default_suggestions(self, manager):
        suggestions = await manager.get_suggestions({})
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
