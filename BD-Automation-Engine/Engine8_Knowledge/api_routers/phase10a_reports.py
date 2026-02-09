"""
Phase 10A API Router - Weekly BD Report Generator

Endpoints:
  - POST /reports/weekly   - Generate comprehensive weekly BD report
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

logger = logging.getLogger("BDKnowledgeAPI.phase10a")

router = APIRouter()


# ─── Request / Response Models ────────────────────────────────────────────────


class WeeklyReportRequest(BaseModel):
    weeks_back: int = Field(1, ge=1, le=12, description="Number of weeks to cover")


class OpportunityItem(BaseModel):
    program: str
    company: str
    contact: str
    estimated_value: float
    stage: str
    priority: str


class ActionItem(BaseModel):
    action: str
    priority: str
    due: str
    related_program: Optional[str] = None


class WeeklyReportResponse(BaseModel):
    period: dict
    generated_at: str
    pipeline_summary: dict
    outreach_activity: dict
    meetings: dict
    competitive_changes: dict
    top_opportunities: List[dict]
    action_items: List[dict]
    executive_summary: str


# ─── Mock Report Data ─────────────────────────────────────────────────────────

_PROGRAMS = [
    "AF DCGS Block 5", "Army DCGS-A", "Navy DCGS-N", "SOCOM DCGS-SOF",
    "GBSD", "JSTARS Recap", "PACAF ISR Modernization",
]

_COMPANIES = ["GDIT", "Leidos", "SAIC", "CACI", "Peraton", "BAE Systems"]


def _generate_report(weeks_back: int) -> dict:
    """Generate a comprehensive weekly BD report with realistic mock data."""
    now = datetime.utcnow()
    start = now - timedelta(weeks=weeks_back)

    return {
        "period": {
            "start": start.strftime("%Y-%m-%d"),
            "end": now.strftime("%Y-%m-%d"),
        },
        "generated_at": now.isoformat() + "Z",

        "pipeline_summary": {
            "total_pipeline_value": 4_850_000,
            "deals_by_stage": {
                "identified": {"count": 8, "value": 920_000},
                "outreach_active": {"count": 5, "value": 780_000},
                "meeting_set": {"count": 3, "value": 650_000},
                "engaged": {"count": 4, "value": 1_200_000},
                "placement_made": {"count": 2, "value": 800_000},
                "revenue_realized": {"count": 1, "value": 500_000},
            },
            "new_this_period": 3,
            "moved_forward": 4,
            "stalled": 2,
        },

        "outreach_activity": {
            "sequences_created": 6,
            "steps_sent": 14,
            "emails_sent": 8,
            "calls_made": 4,
            "linkedin_messages": 2,
            "response_rate": 28.6,
            "positive_responses": 4,
            "bounced": 1,
            "top_performing_template": "Day 1 Intro Email (35% response rate)",
        },

        "meetings": {
            "scheduled": 3,
            "held": 2,
            "cancelled": 0,
            "conversion_to_engaged": 1,
            "upcoming": [
                {
                    "contact": "J. Miller",
                    "company": "GDIT",
                    "program": "AF DCGS Block 5",
                    "date": (now + timedelta(days=2)).strftime("%Y-%m-%d"),
                    "type": "Technical Deep-Dive",
                },
                {
                    "contact": "R. Chen",
                    "company": "Leidos",
                    "program": "Army DCGS-A",
                    "date": (now + timedelta(days=5)).strftime("%Y-%m-%d"),
                    "type": "Capability Brief",
                },
            ],
        },

        "competitive_changes": {
            "new_awards": [
                {
                    "contractor": "SAIC",
                    "program": "PACAF ISR Modernization",
                    "value": 12_500_000,
                    "date": (now - timedelta(days=3)).strftime("%Y-%m-%d"),
                },
            ],
            "expiring_contracts": 2,
            "competitor_hiring_spike": {
                "company": "Leidos",
                "location": "Fort Liberty, NC",
                "positions": 8,
                "signal": "Possible DCGS-A ramp-up",
            },
        },

        "top_opportunities": [
            {
                "program": "AF DCGS Block 5",
                "company": "GDIT",
                "contact": "J. Miller",
                "estimated_value": 450_000,
                "stage": "engaged",
                "priority": "critical",
            },
            {
                "program": "Army DCGS-A",
                "company": "Leidos",
                "contact": "R. Chen",
                "estimated_value": 380_000,
                "stage": "meeting_set",
                "priority": "high",
            },
            {
                "program": "SOCOM DCGS-SOF",
                "company": "CACI",
                "contact": "M. Torres",
                "estimated_value": 320_000,
                "stage": "outreach_active",
                "priority": "high",
            },
            {
                "program": "Navy DCGS-N",
                "company": "BAE Systems",
                "contact": "K. Ero",
                "estimated_value": 275_000,
                "stage": "identified",
                "priority": "medium",
            },
            {
                "program": "GBSD",
                "company": "Peraton",
                "contact": "S. Yamamoto",
                "estimated_value": 250_000,
                "stage": "outreach_active",
                "priority": "medium",
            },
        ],

        "action_items": [
            {
                "action": "Follow up with J. Miller (GDIT) on AF DCGS Block 5 tech evaluation results",
                "priority": "critical",
                "due": (now + timedelta(days=1)).strftime("%Y-%m-%d"),
                "related_program": "AF DCGS Block 5",
            },
            {
                "action": "Prepare capability brief for R. Chen (Leidos) meeting on Army DCGS-A",
                "priority": "high",
                "due": (now + timedelta(days=4)).strftime("%Y-%m-%d"),
                "related_program": "Army DCGS-A",
            },
            {
                "action": "Advance Day 5 Call step for M. Torres (CACI) SOCOM DCGS-SOF sequence",
                "priority": "high",
                "due": (now + timedelta(days=2)).strftime("%Y-%m-%d"),
                "related_program": "SOCOM DCGS-SOF",
            },
            {
                "action": "Research BAE Systems hiring activity at Fort Meade for Navy DCGS-N intel",
                "priority": "medium",
                "due": (now + timedelta(days=5)).strftime("%Y-%m-%d"),
                "related_program": "Navy DCGS-N",
            },
            {
                "action": "Review SAIC PACAF ISR award for competitive positioning updates",
                "priority": "medium",
                "due": (now + timedelta(days=3)).strftime("%Y-%m-%d"),
                "related_program": "PACAF ISR Modernization",
            },
        ],

        "executive_summary": (
            f"This week ({start.strftime('%b %d')} - {now.strftime('%b %d')}), the BD pipeline "
            f"holds $4.85M across 23 active deals. 4 opportunities advanced stages and 3 new "
            f"prospects were identified. Outreach activity produced a 28.6% response rate with "
            f"4 positive responses from 14 touchpoints. Key highlight: GDIT's AF DCGS Block 5 "
            f"engagement moved to the 'Engaged' stage after a successful technical deep-dive. "
            f"Competitive watch: SAIC won a $12.5M PACAF ISR Modernization award, and Leidos "
            f"is ramping hiring at Fort Liberty (8 new positions), signaling DCGS-A activity. "
            f"Priority action: Close the J. Miller follow-up within 24 hours to maintain momentum "
            f"on the highest-value opportunity ($450K)."
        ),
    }


# ─── Endpoint ─────────────────────────────────────────────────────────────────


@router.post("/reports/weekly")
async def generate_weekly_report(req: WeeklyReportRequest = WeeklyReportRequest()):
    """Generate a comprehensive weekly BD report aggregating pipeline,
    outreach, meetings, and competitive intelligence data."""
    logger.info("Generating weekly BD report (weeks_back=%d)", req.weeks_back)
    report = _generate_report(req.weeks_back)
    return report
