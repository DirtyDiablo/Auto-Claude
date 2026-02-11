"""Tests for Phase 50A — Yjs Collaboration Engine."""

import pytest

from src.collaboration.yjs_engine import (
    YjsCollaborationEngine,
    CollaborationRoom,
    RoomType,
    PresenceStatus,
    UserPresence,
    CRDTOperation,
    get_yjs_engine,
)


@pytest.fixture
def yjs():
    return YjsCollaborationEngine()


# =========================================
# ROOM CREATION
# =========================================

def test_create_call_sheet_room(yjs):
    room = yjs.create_room(RoomType.CALL_SHEET, "DCGS-A Call Prep")
    assert isinstance(room, CollaborationRoom)
    assert room.room_type == RoomType.CALL_SHEET
    assert "contacts" in room.state
    assert "notes" in room.state


def test_create_pipeline_room(yjs):
    room = yjs.create_room(RoomType.PIPELINE, "Q1 Pipeline")
    assert room.room_type == RoomType.PIPELINE
    assert "stages" in room.state


def test_create_war_room(yjs):
    room = yjs.create_room(RoomType.WAR_ROOM, "JADC2 War Room")
    assert room.room_type == RoomType.WAR_ROOM
    assert "competitors" in room.state
    assert "win_themes" in room.state


def test_create_briefing_room(yjs):
    room = yjs.create_room(RoomType.BRIEFING, "Weekly Brief")
    assert room.room_type == RoomType.BRIEFING
    assert "sections" in room.state


def test_create_with_initial_state(yjs):
    room = yjs.create_room(
        RoomType.CALL_SHEET, "Custom",
        initial_state={"custom_field": "value"},
    )
    assert room.state["custom_field"] == "value"


def test_room_id_unique(yjs):
    r1 = yjs.create_room(RoomType.CALL_SHEET, "A")
    r2 = yjs.create_room(RoomType.CALL_SHEET, "B")
    assert r1.room_id != r2.room_id


def test_get_room(yjs):
    room = yjs.create_room(RoomType.PIPELINE, "Test")
    fetched = yjs.get_room(room.room_id)
    assert fetched is not None
    assert fetched.room_id == room.room_id


def test_get_room_not_found(yjs):
    assert yjs.get_room("room_nonexistent") is None


def test_list_rooms(yjs):
    yjs.create_room(RoomType.CALL_SHEET, "A")
    yjs.create_room(RoomType.PIPELINE, "B")
    rooms = yjs.list_rooms()
    assert len(rooms) == 2


def test_list_rooms_filter_type(yjs):
    yjs.create_room(RoomType.CALL_SHEET, "A")
    yjs.create_room(RoomType.PIPELINE, "B")
    rooms = yjs.list_rooms(room_type=RoomType.CALL_SHEET)
    assert len(rooms) == 1


def test_delete_room(yjs):
    room = yjs.create_room(RoomType.CALL_SHEET, "Delete Me")
    assert yjs.delete_room(room.room_id) is True
    assert yjs.get_room(room.room_id) is None


# =========================================
# PRESENCE
# =========================================

def test_join_room(yjs):
    room = yjs.create_room(RoomType.CALL_SHEET, "Test")
    presence = yjs.join_room(room.room_id, "u1", "Alice")
    assert isinstance(presence, UserPresence)
    assert presence.user_id == "u1"
    assert presence.status == PresenceStatus.ONLINE


def test_join_assigns_color(yjs):
    room = yjs.create_room(RoomType.CALL_SHEET, "Test")
    p1 = yjs.join_room(room.room_id, "u1", "Alice")
    p2 = yjs.join_room(room.room_id, "u2", "Bob")
    assert p1.color != p2.color


def test_join_nonexistent_room(yjs):
    assert yjs.join_room("room_fake", "u1", "Alice") is None


def test_leave_room(yjs):
    room = yjs.create_room(RoomType.CALL_SHEET, "Test")
    yjs.join_room(room.room_id, "u1", "Alice")
    assert yjs.leave_room(room.room_id, "u1") is True
    presence = yjs.get_room_presence(room.room_id)
    assert len(presence) == 0  # offline users filtered out


def test_update_presence(yjs):
    room = yjs.create_room(RoomType.CALL_SHEET, "Test")
    yjs.join_room(room.room_id, "u1", "Alice")
    updated = yjs.update_presence(room.room_id, "u1", status=PresenceStatus.BUSY)
    assert updated.status == PresenceStatus.BUSY


def test_get_room_presence(yjs):
    room = yjs.create_room(RoomType.CALL_SHEET, "Test")
    yjs.join_room(room.room_id, "u1", "Alice")
    yjs.join_room(room.room_id, "u2", "Bob")
    presence = yjs.get_room_presence(room.room_id)
    assert len(presence) == 2


# =========================================
# CRDT OPERATIONS
# =========================================

def test_insert_operation(yjs):
    room = yjs.create_room(RoomType.CALL_SHEET, "Test")
    op = yjs.apply_operation(room.room_id, "insert", "notes", "Call Craig at 3pm", "u1")
    assert isinstance(op, CRDTOperation)
    assert op.op_type == "insert"
    state = yjs.get_state(room.room_id)
    assert state["notes"] == "Call Craig at 3pm"


def test_update_operation(yjs):
    room = yjs.create_room(RoomType.CALL_SHEET, "Test")
    yjs.apply_operation(room.room_id, "insert", "notes", "initial", "u1")
    yjs.apply_operation(room.room_id, "update", "notes", "updated", "u2")
    state = yjs.get_state(room.room_id)
    assert state["notes"] == "updated"


def test_delete_operation(yjs):
    room = yjs.create_room(RoomType.CALL_SHEET, "Test",
                            initial_state={"custom": "val"})
    yjs.apply_operation(room.room_id, "delete", "custom", user_id="u1")
    state = yjs.get_state(room.room_id)
    assert "custom" not in state


def test_list_append_operation(yjs):
    room = yjs.create_room(RoomType.CALL_SHEET, "Test")
    yjs.apply_operation(room.room_id, "insert", "contacts", {"name": "Craig"}, "u1")
    state = yjs.get_state(room.room_id)
    assert len(state["contacts"]) == 1


def test_operation_increments_version(yjs):
    room = yjs.create_room(RoomType.CALL_SHEET, "Test")
    assert room.version == 0
    yjs.apply_operation(room.room_id, "insert", "notes", "a", "u1")
    assert room.version == 1
    yjs.apply_operation(room.room_id, "insert", "notes", "b", "u1")
    assert room.version == 2


def test_get_operations_since_version(yjs):
    room = yjs.create_room(RoomType.CALL_SHEET, "Test")
    yjs.apply_operation(room.room_id, "insert", "notes", "a", "u1")
    yjs.apply_operation(room.room_id, "update", "notes", "b", "u2")
    ops = yjs.get_operations(room.room_id, since_version=1)
    assert len(ops) == 1
    assert ops[0].value == "b"


def test_operation_on_nonexistent_room(yjs):
    assert yjs.apply_operation("room_fake", "insert", "notes", "x") is None


# =========================================
# TO DICT
# =========================================

def test_room_to_dict(yjs):
    room = yjs.create_room(RoomType.WAR_ROOM, "Test War Room")
    d = room.to_dict()
    assert d["room_type"] == "war_room"
    assert "active_users" in d
    assert "total_operations" in d


def test_room_to_full_dict(yjs):
    room = yjs.create_room(RoomType.WAR_ROOM, "Test")
    yjs.join_room(room.room_id, "u1", "Alice")
    d = room.to_full_dict()
    assert "state" in d
    assert "users" in d


# =========================================
# STATS
# =========================================

def test_stats(yjs):
    yjs.create_room(RoomType.CALL_SHEET, "A")
    yjs.create_room(RoomType.PIPELINE, "B")
    stats = yjs.get_stats()
    assert stats["total_rooms"] == 2
    assert "call_sheet" in stats["rooms_by_type"]


# =========================================
# SINGLETON
# =========================================

def test_singleton():
    import src.collaboration.yjs_engine as mod
    mod._instance = None
    s1 = get_yjs_engine()
    s2 = get_yjs_engine()
    assert s1 is s2
    mod._instance = None
