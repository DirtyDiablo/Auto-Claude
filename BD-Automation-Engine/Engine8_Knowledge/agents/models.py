"""
Pydantic output models for CrewAI BD agents.

These models enforce structured output from agent tasks,
enabling downstream consumption by APIs and dashboards.
"""

from pydantic import BaseModel, Field
from typing import Optional


class ProgramIntelligence(BaseModel):
    program_name: str
    agency: str
    estimated_value: Optional[str] = None
    prime_contractor: Optional[str] = None
    key_contacts: list[dict] = Field(
        default_factory=list,
        description="List of {name, title, tier, program}",
    )
    competitive_landscape: str = Field(
        description="Analysis of competitors and positioning"
    )
    pts_past_performance: str = Field(
        description="Relevant PTS experience for this program"
    )
    pain_points: list[str] = Field(
        default_factory=list,
        description="Known program pain points",
    )
    recommendation: str = Field(
        description="Specific BD recommendation and next steps"
    )
    confidence_score: float = Field(
        ge=0, le=1, description="Confidence in the analysis"
    )


class ContactProfile(BaseModel):
    name: str
    title: str
    company: str
    programs: list[str] = Field(default_factory=list)
    tier: str = Field(description="Tier 1-6 classification")
    location: Optional[str] = None
    pain_points: list[str] = Field(default_factory=list)
    interaction_history: str = Field(
        default="", description="Summary of past interactions"
    )
    outreach_recommendation: str
    best_channel: str = Field(
        description="Email, LinkedIn, Phone, or SMS"
    )


class CompetitiveReport(BaseModel):
    program_name: str
    competitors: list[dict] = Field(
        description="List of {company, role, strengths, weaknesses}"
    )
    pts_differentiators: list[str]
    win_probability: str = Field(
        description="High/Medium/Low with reasoning"
    )
    risks: list[str]
    recommended_strategy: str


class OutreachPlan(BaseModel):
    contact_name: str
    contact_title: str
    program: str
    channel: str = Field(description="Primary outreach channel")
    personalized_opener: str = Field(
        description="Role-specific icebreaker showing program knowledge"
    )
    pain_point_reference: str = Field(
        description="Their specific challenge we can solve"
    )
    labor_gap_reference: str = Field(
        description="Current vacancies at their location"
    )
    pts_past_performance: str = Field(
        description="Relevant PTS experience matching their needs"
    )
    call_to_action: str
    follow_up_plan: str
    talking_points: list[str] = Field(default_factory=list)


class HUMINTBrief(BaseModel):
    source_contact: str
    date: str
    program: str
    key_findings: list[str]
    pain_points_discovered: list[str]
    hiring_manager_names: list[str] = Field(default_factory=list)
    budget_cycle_info: Optional[str] = None
    vendor_preferences: Optional[str] = None
    action_items: list[str]
    confidence_level: str = Field(description="High/Medium/Low")
