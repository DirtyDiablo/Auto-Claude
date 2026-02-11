"""Phase 50A — Real-Time Collaboration API (12 endpoints).

REST endpoints for Yjs collaboration rooms, contact claiming,
presence tracking, and shared intelligence feed.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from src.collaboration.yjs_engine import (
    YjsCollaborationEngine, get_yjs_engine,
    RoomType, PresenceStatus,
)
from src.collaboration.contact_claiming import (
    ContactClaimingSystem, get_claiming_system, ClaimStatus,
)
from src.collaboration.shared_intel_feed import (
    SharedIntelligenceFeed, get_intel_feed,
    IntelType, IntelPriority,
)

logger = logging.getLogger(__name__)


# =========================================
# REQUEST MODELS
# =========================================

class CreateRoomRequest(BaseModel):
    room_type: str  # call_sheet | pipeline | war_room | briefing
    name: str
    initial_state: Optional[Dict[str, Any]] = None


class JoinRoomRequest(BaseModel):
    user_id: str
    display_name: str


class OperationRequest(BaseModel):
    op_type: str  # insert | update | delete
    path: str
    value: Any = None
    user_id: str = ""


class ClaimContactRequest(BaseModel):
    contact_id: str
    contact_name: str
    owner_id: str
    owner_name: str
    reason: str = ""
    program: str = ""


class TransferClaimRequest(BaseModel):
    new_owner_id: str
    new_owner_name: str


class ContestClaimRequest(BaseModel):
    requester_id: str
    requester_name: str
    reason: str = ""


class ResolveContestRequest(BaseModel):
    resolution: str  # approved | denied | split


class PostIntelRequest(BaseModel):
    intel_type: str
    priority: str = "normal"
    title: str
    body: str
    author_id: str
    author_name: str
    program: str = ""
    tags: Optional[List[str]] = None
    mentions: Optional[List[str]] = None


class ReactionRequest(BaseModel):
    user_id: str
    user_name: str
    emoji: str


class CommentRequest(BaseModel):
    user_id: str
    user_name: str
    text: str


# =========================================
# ROUTE SETUP
# =========================================

def include_collaboration_router(app: FastAPI) -> None:
    """Register all collaboration endpoints on the FastAPI app."""

    yjs = get_yjs_engine()
    claiming = get_claiming_system()
    feed = get_intel_feed()

    # --------------------------------------------------
    # 1. POST /api/collab/rooms — Create collaboration room
    # --------------------------------------------------
    @app.post("/api/collab/rooms")
    async def create_room(req: CreateRoomRequest):
        """Create a new real-time collaboration room."""
        try:
            room_type = RoomType(req.room_type)
        except ValueError:
            raise HTTPException(400, f"Invalid room type: {req.room_type}")

        room = yjs.create_room(room_type, req.name, req.initial_state)
        return room.to_full_dict()

    # --------------------------------------------------
    # 2. GET /api/collab/rooms — List rooms
    # --------------------------------------------------
    @app.get("/api/collab/rooms")
    async def list_rooms(
        room_type: str = Query("", description="Filter by room type"),
    ):
        """List collaboration rooms."""
        rt = None
        if room_type:
            try:
                rt = RoomType(room_type)
            except ValueError:
                raise HTTPException(400, f"Invalid room type: {room_type}")
        rooms = yjs.list_rooms(room_type=rt)
        return {
            "rooms": [r.to_dict() for r in rooms],
            "total": len(rooms),
        }

    # --------------------------------------------------
    # 3. POST /api/collab/rooms/{room_id}/join — Join room
    # --------------------------------------------------
    @app.post("/api/collab/rooms/{room_id}/join")
    async def join_room(room_id: str, req: JoinRoomRequest):
        """Join a collaboration room."""
        presence = yjs.join_room(room_id, req.user_id, req.display_name)
        if not presence:
            raise HTTPException(404, f"Room not found or full: {room_id}")
        return presence.to_dict()

    # --------------------------------------------------
    # 4. POST /api/collab/rooms/{room_id}/op — Apply CRDT operation
    # --------------------------------------------------
    @app.post("/api/collab/rooms/{room_id}/op")
    async def apply_operation(room_id: str, req: OperationRequest):
        """Apply a CRDT operation to the room state."""
        op = yjs.apply_operation(room_id, req.op_type, req.path, req.value, req.user_id)
        if not op:
            raise HTTPException(404, f"Room not found: {room_id}")
        return op.to_dict()

    # --------------------------------------------------
    # 5. GET /api/collab/rooms/{room_id}/state — Get room state
    # --------------------------------------------------
    @app.get("/api/collab/rooms/{room_id}/state")
    async def get_room_state(room_id: str):
        """Get the current CRDT-merged state of a room."""
        state = yjs.get_state(room_id)
        if state is None:
            raise HTTPException(404, f"Room not found: {room_id}")
        room = yjs.get_room(room_id)
        return {
            "room_id": room_id,
            "version": room.version,
            "state": state,
            "active_users": [u.to_dict() for u in yjs.get_room_presence(room_id)],
        }

    # --------------------------------------------------
    # 6. POST /api/collab/claims — Claim a contact
    # --------------------------------------------------
    @app.post("/api/collab/claims")
    async def claim_contact(req: ClaimContactRequest):
        """Claim exclusive ownership of a contact."""
        try:
            claim = claiming.claim_contact(
                contact_id=req.contact_id,
                contact_name=req.contact_name,
                owner_id=req.owner_id,
                owner_name=req.owner_name,
                reason=req.reason,
                program=req.program,
            )
            return claim.to_dict()
        except ValueError as e:
            raise HTTPException(409, str(e))

    # --------------------------------------------------
    # 7. GET /api/collab/claims — List claims
    # --------------------------------------------------
    @app.get("/api/collab/claims")
    async def list_claims(
        owner_id: str = Query("", description="Filter by owner"),
        active_only: bool = Query(False, description="Active claims only"),
    ):
        """List contact claims."""
        claims = claiming.list_claims(
            owner_id=owner_id or None,
            active_only=active_only,
        )
        return {
            "claims": [c.to_dict() for c in claims],
            "total": len(claims),
        }

    # --------------------------------------------------
    # 8. POST /api/collab/claims/{claim_id}/release — Release claim
    # --------------------------------------------------
    @app.post("/api/collab/claims/{claim_id}/release")
    async def release_claim(claim_id: str):
        """Release a contact claim."""
        if not claiming.release_claim(claim_id):
            raise HTTPException(404, f"Claim not found or not active: {claim_id}")
        return {"status": "released", "claim_id": claim_id}

    # --------------------------------------------------
    # 9. POST /api/collab/claims/{claim_id}/contest — Contest claim
    # --------------------------------------------------
    @app.post("/api/collab/claims/{claim_id}/contest")
    async def contest_claim(claim_id: str, req: ContestClaimRequest):
        """Raise a dispute for a claimed contact."""
        try:
            contest = claiming.contest_claim(
                claim_id=claim_id,
                requester_id=req.requester_id,
                requester_name=req.requester_name,
                reason=req.reason,
            )
            return contest.to_dict()
        except ValueError as e:
            raise HTTPException(404, str(e))

    # --------------------------------------------------
    # 10. POST /api/collab/intel — Post intelligence
    # --------------------------------------------------
    @app.post("/api/collab/intel")
    async def post_intel(req: PostIntelRequest):
        """Post a new intelligence item to the shared feed."""
        try:
            itype = IntelType(req.intel_type)
        except ValueError:
            raise HTTPException(400, f"Invalid intel type: {req.intel_type}")
        try:
            prio = IntelPriority(req.priority)
        except ValueError:
            raise HTTPException(400, f"Invalid priority: {req.priority}")

        item = feed.post_intel(
            intel_type=itype, priority=prio,
            title=req.title, body=req.body,
            author_id=req.author_id, author_name=req.author_name,
            program=req.program, tags=req.tags, mentions=req.mentions,
        )
        return item.to_dict()

    # --------------------------------------------------
    # 11. GET /api/collab/intel — Get intelligence feed
    # --------------------------------------------------
    @app.get("/api/collab/intel")
    async def get_feed(
        intel_type: str = Query("", description="Filter by type"),
        priority: str = Query("", description="Filter by priority"),
        program: str = Query("", description="Filter by program"),
        limit: int = Query(50, description="Max items to return"),
    ):
        """Get the shared intelligence feed."""
        itype = None
        if intel_type:
            try:
                itype = IntelType(intel_type)
            except ValueError:
                raise HTTPException(400, f"Invalid intel type: {intel_type}")
        prio = None
        if priority:
            try:
                prio = IntelPriority(priority)
            except ValueError:
                raise HTTPException(400, f"Invalid priority: {priority}")

        items = feed.get_feed(
            intel_type=itype, priority=prio,
            program=program or None, limit=limit,
        )
        return {
            "items": [i.to_dict() for i in items],
            "total": len(items),
        }

    # --------------------------------------------------
    # 12. GET /api/collab/stats — Collaboration stats
    # --------------------------------------------------
    @app.get("/api/collab/stats")
    async def collab_stats():
        """Combined collaboration system stats."""
        return {
            "rooms": yjs.get_stats(),
            "claims": claiming.get_stats(),
            "intel_feed": feed.get_stats(),
        }

    logger.info("Collaboration API: 12 endpoints registered under /api/collab/*")
