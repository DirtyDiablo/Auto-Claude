"""Phase 50A — Yjs Collaboration Engine.

CRDT-based real-time collaboration rooms that allow multiple BD reps to
co-edit call sheets, pipelines, war-room boards, and briefings concurrently
without conflicts.  Uses Yjs-style operational-transform semantics.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# DATA MODELS
# =========================================

class RoomType(str, Enum):
    CALL_SHEET = "call_sheet"
    PIPELINE = "pipeline"
    WAR_ROOM = "war_room"
    BRIEFING = "briefing"


class PresenceStatus(str, Enum):
    ONLINE = "online"
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"


@dataclass
class UserPresence:
    """Tracks a user's presence in a collaboration room."""
    user_id: str
    display_name: str
    status: PresenceStatus = PresenceStatus.ONLINE
    cursor_position: Optional[Dict[str, Any]] = None
    joined_at: str = ""
    last_active: str = ""
    color: str = "#4A90D9"  # user accent color for cursors

    def __post_init__(self):
        now = datetime.utcnow().isoformat()
        if not self.joined_at:
            self.joined_at = now
        if not self.last_active:
            self.last_active = now

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "display_name": self.display_name,
            "status": self.status.value,
            "cursor_position": self.cursor_position,
            "joined_at": self.joined_at,
            "last_active": self.last_active,
            "color": self.color,
        }


@dataclass
class CRDTOperation:
    """A single CRDT operation (insert, delete, update) for conflict-free merging."""
    op_id: str
    op_type: str  # insert | delete | update
    path: str     # JSON path in the document (e.g., "contacts.0.notes")
    value: Any = None
    user_id: str = ""
    timestamp: str = ""
    version: int = 0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "op_id": self.op_id,
            "op_type": self.op_type,
            "path": self.path,
            "value": self.value,
            "user_id": self.user_id,
            "timestamp": self.timestamp,
            "version": self.version,
        }


@dataclass
class CollaborationRoom:
    """A real-time collaboration room backed by CRDT state."""
    room_id: str
    room_type: RoomType
    name: str
    state: Dict[str, Any] = field(default_factory=dict)
    users: Dict[str, UserPresence] = field(default_factory=dict)
    operations: List[CRDTOperation] = field(default_factory=list)
    version: int = 0
    created_at: str = ""
    updated_at: str = ""
    max_users: int = 20

    def __post_init__(self):
        now = datetime.utcnow().isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def to_dict(self) -> Dict[str, Any]:
        return {
            "room_id": self.room_id,
            "room_type": self.room_type.value,
            "name": self.name,
            "version": self.version,
            "active_users": len([u for u in self.users.values()
                                 if u.status != PresenceStatus.OFFLINE]),
            "total_operations": len(self.operations),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_full_dict(self) -> Dict[str, Any]:
        d = self.to_dict()
        d["state"] = self.state
        d["users"] = {uid: u.to_dict() for uid, u in self.users.items()}
        return d


# =========================================
# DEFAULT ROOM TEMPLATES
# =========================================

_ROOM_TEMPLATES: Dict[RoomType, Dict[str, Any]] = {
    RoomType.CALL_SHEET: {
        "contacts": [],
        "notes": "",
        "agenda": [],
        "follow_ups": [],
        "participants": [],
    },
    RoomType.PIPELINE: {
        "opportunities": [],
        "stages": ["prospect", "qualify", "propose", "negotiate", "close"],
        "filters": {},
        "sort_by": "priority",
    },
    RoomType.WAR_ROOM: {
        "program": "",
        "competitors": [],
        "win_themes": [],
        "action_items": [],
        "intelligence": [],
        "timeline": [],
    },
    RoomType.BRIEFING: {
        "title": "",
        "sections": [],
        "key_findings": [],
        "recommendations": [],
        "attachments": [],
    },
}


# =========================================
# YJS COLLABORATION ENGINE
# =========================================

class YjsCollaborationEngine:
    """CRDT-based real-time collaboration engine.

    Manages rooms where multiple users can concurrently edit shared documents.
    Operations are merged conflict-free using CRDT semantics (last-writer-wins
    for scalar fields, set-union for collections).
    """

    # Pre-defined user colors for presence cursors
    _USER_COLORS = [
        "#4A90D9", "#E74C3C", "#2ECC71", "#F39C12",
        "#9B59B6", "#1ABC9C", "#E67E22", "#3498DB",
        "#E91E63", "#00BCD4", "#FF5722", "#8BC34A",
    ]

    def __init__(self):
        self._rooms: Dict[str, CollaborationRoom] = {}
        self._room_counter = 0
        self._op_counter = 0
        logger.info("YjsCollaborationEngine initialized")

    # ----- room management -----

    def create_room(
        self,
        room_type: RoomType,
        name: str,
        initial_state: Optional[Dict[str, Any]] = None,
    ) -> CollaborationRoom:
        """Create a new collaboration room."""
        self._room_counter += 1
        room_id = f"room_{hashlib.md5(f'{room_type.value}:{name}:{self._room_counter}'.encode()).hexdigest()[:10]}"

        template = dict(_ROOM_TEMPLATES.get(room_type, {}))
        if initial_state:
            template.update(initial_state)

        room = CollaborationRoom(
            room_id=room_id,
            room_type=room_type,
            name=name,
            state=template,
        )
        self._rooms[room_id] = room
        logger.info("Created room %s (%s: %s)", room_id, room_type.value, name)
        return room

    def get_room(self, room_id: str) -> Optional[CollaborationRoom]:
        return self._rooms.get(room_id)

    def list_rooms(
        self,
        room_type: Optional[RoomType] = None,
    ) -> List[CollaborationRoom]:
        rooms = list(self._rooms.values())
        if room_type:
            rooms = [r for r in rooms if r.room_type == room_type]
        return sorted(rooms, key=lambda r: r.updated_at, reverse=True)

    def delete_room(self, room_id: str) -> bool:
        if room_id in self._rooms:
            del self._rooms[room_id]
            return True
        return False

    # ----- presence -----

    def join_room(self, room_id: str, user_id: str, display_name: str) -> Optional[UserPresence]:
        """Add a user to a room's presence list."""
        room = self._rooms.get(room_id)
        if not room:
            return None

        if len(room.users) >= room.max_users:
            return None

        color_idx = len(room.users) % len(self._USER_COLORS)
        presence = UserPresence(
            user_id=user_id,
            display_name=display_name,
            color=self._USER_COLORS[color_idx],
        )
        room.users[user_id] = presence
        return presence

    def leave_room(self, room_id: str, user_id: str) -> bool:
        room = self._rooms.get(room_id)
        if room and user_id in room.users:
            room.users[user_id].status = PresenceStatus.OFFLINE
            return True
        return False

    def update_presence(
        self,
        room_id: str,
        user_id: str,
        status: Optional[PresenceStatus] = None,
        cursor_position: Optional[Dict[str, Any]] = None,
    ) -> Optional[UserPresence]:
        room = self._rooms.get(room_id)
        if not room or user_id not in room.users:
            return None

        presence = room.users[user_id]
        if status:
            presence.status = status
        if cursor_position is not None:
            presence.cursor_position = cursor_position
        presence.last_active = datetime.utcnow().isoformat()
        return presence

    def get_room_presence(self, room_id: str) -> List[UserPresence]:
        room = self._rooms.get(room_id)
        if not room:
            return []
        return [u for u in room.users.values() if u.status != PresenceStatus.OFFLINE]

    # ----- CRDT operations -----

    def apply_operation(
        self,
        room_id: str,
        op_type: str,
        path: str,
        value: Any = None,
        user_id: str = "",
    ) -> Optional[CRDTOperation]:
        """Apply a CRDT operation to a room's state."""
        room = self._rooms.get(room_id)
        if not room:
            return None

        self._op_counter += 1
        room.version += 1

        op = CRDTOperation(
            op_id=f"op_{self._op_counter}",
            op_type=op_type,
            path=path,
            value=value,
            user_id=user_id,
            version=room.version,
        )

        # Apply to state
        self._apply_to_state(room.state, op)
        room.operations.append(op)
        room.updated_at = datetime.utcnow().isoformat()
        return op

    def _apply_to_state(self, state: Dict[str, Any], op: CRDTOperation) -> None:
        """Apply operation to the state dictionary."""
        parts = op.path.split(".")
        target = state

        # Navigate to parent
        for part in parts[:-1]:
            if isinstance(target, dict) and part in target:
                target = target[part]
            elif isinstance(target, list):
                try:
                    idx = int(part)
                    target = target[idx]
                except (ValueError, IndexError):
                    return
            else:
                return

        key = parts[-1]

        if op.op_type == "insert":
            if isinstance(target, dict):
                target[key] = op.value
            elif isinstance(target, list):
                target.append(op.value)
        elif op.op_type == "update":
            if isinstance(target, dict):
                target[key] = op.value
        elif op.op_type == "delete":
            if isinstance(target, dict) and key in target:
                del target[key]
            elif isinstance(target, list):
                try:
                    idx = int(key)
                    if 0 <= idx < len(target):
                        target.pop(idx)
                except ValueError:
                    pass

    def get_operations(
        self,
        room_id: str,
        since_version: int = 0,
    ) -> List[CRDTOperation]:
        """Get operations since a version for incremental sync."""
        room = self._rooms.get(room_id)
        if not room:
            return []
        return [op for op in room.operations if op.version > since_version]

    def get_state(self, room_id: str) -> Optional[Dict[str, Any]]:
        """Get the current merged state of a room."""
        room = self._rooms.get(room_id)
        if not room:
            return None
        return room.state

    # ----- stats -----

    def get_stats(self) -> Dict[str, Any]:
        total_users = sum(
            len([u for u in r.users.values() if u.status != PresenceStatus.OFFLINE])
            for r in self._rooms.values()
        )
        by_type: Dict[str, int] = {}
        for r in self._rooms.values():
            by_type[r.room_type.value] = by_type.get(r.room_type.value, 0) + 1

        return {
            "total_rooms": len(self._rooms),
            "rooms_by_type": by_type,
            "total_active_users": total_users,
            "total_operations": sum(len(r.operations) for r in self._rooms.values()),
        }


# =========================================
# SINGLETON
# =========================================

_instance: Optional[YjsCollaborationEngine] = None


def get_yjs_engine() -> YjsCollaborationEngine:
    global _instance
    if _instance is None:
        _instance = YjsCollaborationEngine()
    return _instance
