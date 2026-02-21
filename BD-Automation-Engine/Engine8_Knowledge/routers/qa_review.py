"""QA Human Review Queue router — approve, reject, reclassify flagged items."""

import asyncio
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from Engine6_QA.scripts.qa_feedback import ReviewQueue

logger = logging.getLogger("BDKnowledgeAPI")

router = APIRouter(prefix="/qa", tags=["QA Review Queue"])


# ---------------------------------------------------------------------------
# Pydantic request / response models
# ---------------------------------------------------------------------------


class ApproveRequest(BaseModel):
    reviewer: str = Field(..., description="Name of the reviewer")
    notes: str = Field("", description="Optional approval notes")


class RejectRequest(BaseModel):
    reviewer: str = Field(..., description="Name of the reviewer")
    reason: str = Field("", description="Reason for rejection")


class ReclassifyRequest(BaseModel):
    reviewer: str = Field(..., description="Name of the reviewer")
    new_program: str = Field(..., description="New program to assign")


class BulkApproveRequest(BaseModel):
    job_ids: List[str] = Field(..., description="List of job IDs to approve")
    reviewer: str = Field(..., description="Name of the reviewer")


class BulkRejectRequest(BaseModel):
    job_ids: List[str] = Field(..., description="List of job IDs to reject")
    reviewer: str = Field(..., description="Name of the reviewer")
    reason: str = Field("", description="Reason for rejection")


class ActionResponse(BaseModel):
    success: bool
    message: str


class BulkActionResponse(BaseModel):
    success: int
    failed: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_queue() -> ReviewQueue:
    """Instantiate a ReviewQueue (loads from disk)."""
    return ReviewQueue()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/queue")
async def list_pending_items(
    skip: int = Query(0, ge=0, description="Items to skip"),
    limit: int = Query(50, ge=1, le=200, description="Max items to return"),
    sort_by: str = Query("added_at", description="Field to sort by"),
    filter_status: Optional[str] = Query(None, description="Filter by status"),
):
    """List review queue items with pagination and optional filtering."""
    queue = await asyncio.to_thread(_get_queue)

    items = list(queue.items)

    if filter_status:
        items = [i for i in items if i.get("status") == filter_status]

    reverse = sort_by in ("confidence",)
    items.sort(key=lambda i: i.get(sort_by, ""), reverse=reverse)

    total = len(items)
    page = items[skip : skip + limit]
    return {"total": total, "skip": skip, "limit": limit, "items": page}


@router.get("/queue/{job_id}")
async def get_item(job_id: str):
    """Get a single review queue item by job_id."""
    queue = await asyncio.to_thread(_get_queue)
    item = queue.get_item(job_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Item '{job_id}' not found")
    return item


@router.post("/queue/{job_id}/approve", response_model=ActionResponse)
async def approve_item(job_id: str, body: ApproveRequest):
    """Approve a review queue item."""
    queue = await asyncio.to_thread(_get_queue)
    ok = await asyncio.to_thread(queue.approve, job_id, body.reviewer)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Item '{job_id}' not found")
    return ActionResponse(success=True, message=f"Item '{job_id}' approved by {body.reviewer}")


@router.post("/queue/{job_id}/reject", response_model=ActionResponse)
async def reject_item(job_id: str, body: RejectRequest):
    """Reject a review queue item."""
    queue = await asyncio.to_thread(_get_queue)
    ok = await asyncio.to_thread(queue.reject, job_id, body.reviewer, body.reason)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Item '{job_id}' not found")
    return ActionResponse(success=True, message=f"Item '{job_id}' rejected by {body.reviewer}")


@router.post("/queue/{job_id}/reclassify", response_model=ActionResponse)
async def reclassify_item(job_id: str, body: ReclassifyRequest):
    """Reclassify a review queue item to a different program."""
    queue = await asyncio.to_thread(_get_queue)
    ok = await asyncio.to_thread(queue.reclassify, job_id, body.new_program, body.reviewer)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Item '{job_id}' not found")
    return ActionResponse(
        success=True,
        message=f"Item '{job_id}' reclassified to '{body.new_program}' by {body.reviewer}",
    )


@router.post("/queue/bulk/approve", response_model=BulkActionResponse)
async def bulk_approve(body: BulkApproveRequest):
    """Approve multiple review queue items."""
    queue = await asyncio.to_thread(_get_queue)
    result = await asyncio.to_thread(queue.bulk_approve, body.job_ids, body.reviewer)
    return BulkActionResponse(**result)


@router.post("/queue/bulk/reject", response_model=BulkActionResponse)
async def bulk_reject(body: BulkRejectRequest):
    """Reject multiple review queue items."""
    queue = await asyncio.to_thread(_get_queue)
    result = await asyncio.to_thread(queue.bulk_reject, body.job_ids, body.reviewer, body.reason)
    return BulkActionResponse(**result)


@router.get("/stats")
async def get_stats():
    """Get queue statistics."""
    queue = await asyncio.to_thread(_get_queue)
    return await asyncio.to_thread(queue.get_stats)


@router.get("/history")
async def get_review_history(
    skip: int = Query(0, ge=0, description="Items to skip"),
    limit: int = Query(50, ge=1, le=200, description="Max items to return"),
):
    """Get review audit history with pagination."""
    queue = await asyncio.to_thread(_get_queue)
    history = await asyncio.to_thread(queue.get_review_history)

    history.sort(key=lambda i: i.get("reviewed_at", ""), reverse=True)

    total = len(history)
    page = history[skip : skip + limit]
    return {"total": total, "skip": skip, "limit": limit, "items": page}
