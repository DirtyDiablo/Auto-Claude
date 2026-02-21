"""
Feature 19 — Enhanced CrewAI Multi-Agent BD Workflows.

8 specialist BD agent classes that work without crewai installed.
Uses pattern-based analysis as fallback when AI/external services are unavailable.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)

# Optional knowledge base integration
try:
    from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore

    _KNOWLEDGE_AVAILABLE = True
except ImportError:
    _KNOWLEDGE_AVAILABLE = False
    logger.warning("BDKnowledgeStore not available — agents will use pattern-based analysis")


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------


class BDAgentBase:
    """Base class for BD specialist agents."""

    name: str = "base"
    role: str = "Base Agent"
    goal: str = "Provide BD intelligence"

    def __init__(self):
        self._knowledge: Optional[Any] = None
        if _KNOWLEDGE_AVAILABLE:
            try:
                self._knowledge = BDKnowledgeStore()
            except Exception as exc:
                logger.warning("knowledge_store_init_failed", error=str(exc))

    def execute(self, context: dict) -> dict:
        """Execute agent task.  Override in subclasses."""
        raise NotImplementedError(f"{self.name} must implement execute()")

    def _make_result(
        self,
        *,
        status: str = "success",
        findings: List[str] | None = None,
        recommendations: List[str] | None = None,
        confidence: float = 0.5,
        metadata: dict | None = None,
    ) -> dict:
        """Build a standard result dict."""
        return {
            "agent_name": self.name,
            "status": status,
            "findings": findings or [],
            "recommendations": recommendations or [],
            "confidence": confidence,
            "metadata": metadata or {},
        }

    def _search_knowledge(self, query: str, collection: str = "programs", limit: int = 5) -> List[dict]:
        """Search knowledge base if available, otherwise return empty list."""
        if self._knowledge is None:
            return []
        try:
            results = self._knowledge.search(query, collection=collection, limit=limit)
            if isinstance(results, list):
                return results
            return []
        except Exception as exc:
            logger.debug("knowledge_search_failed", error=str(exc), collection=collection)
            return []


# ---------------------------------------------------------------------------
# 1. Researcher Agent
# ---------------------------------------------------------------------------


class ResearcherAgent(BDAgentBase):
    """Researches companies, programs, and opportunities."""

    name = "researcher"
    role = "BD Researcher"
    goal = "Gather intelligence from knowledge base, SAM.gov data, and job postings"

    def execute(self, context: dict) -> dict:
        logger.info("agent_execute", agent=self.name, context_keys=list(context.keys()))
        query = context.get("query", context.get("program", context.get("company", "")))
        target = context.get("target", query)

        findings: List[str] = []
        recommendations: List[str] = []

        # Knowledge base search
        for collection in ("programs", "documents", "jobs"):
            results = self._search_knowledge(str(query), collection=collection)
            for r in results:
                text = r.get("text", r.get("payload", {}).get("text", str(r)))
                findings.append(f"[{collection}] {str(text)[:200]}")

        # Pattern-based fallback
        if not findings:
            findings.append(f"Research target identified: {target}")
            findings.append("No indexed data found — recommend manual SAM.gov search")
            recommendations.append(f"Search SAM.gov for '{target}' solicitations")
            recommendations.append("Check USASpending.gov for historical awards")

        if target:
            recommendations.append(f"Monitor job postings from primes on '{target}'")
            recommendations.append(f"Identify incumbents and recompete timelines for '{target}'")

        return self._make_result(
            findings=findings,
            recommendations=recommendations,
            confidence=0.7 if findings else 0.3,
        )


# ---------------------------------------------------------------------------
# 2. Analyst Agent
# ---------------------------------------------------------------------------


class AnalystAgent(BDAgentBase):
    """Analyzes data for patterns, trends, and insights."""

    name = "analyst"
    role = "BD Analyst"
    goal = "Scoring analysis, trend detection, and market sizing"

    def execute(self, context: dict) -> dict:
        logger.info("agent_execute", agent=self.name, context_keys=list(context.keys()))

        findings: List[str] = []
        recommendations: List[str] = []
        confidence = 0.5

        # Analyze previous agent results if present
        prior = context.get("prior_results", {})
        if prior:
            for agent_name, result in prior.items():
                prior_findings = result.get("findings", [])
                findings.append(f"Synthesized {len(prior_findings)} findings from {agent_name}")
            confidence = 0.7

        query = context.get("query", "")
        program = context.get("program", "")

        # Score-based analysis patterns
        score = context.get("bd_score", context.get("score"))
        if score is not None:
            if score >= 80:
                findings.append(f"High-priority opportunity (score: {score})")
                recommendations.append("Escalate to BD leadership for immediate pursuit")
            elif score >= 50:
                findings.append(f"Medium-priority opportunity (score: {score})")
                recommendations.append("Add to pipeline watch list; gather more intel")
            else:
                findings.append(f"Low-priority opportunity (score: {score})")
                recommendations.append("Monitor passively; focus resources elsewhere")
            confidence = 0.8

        # Trend patterns
        jobs = context.get("jobs", [])
        if jobs:
            companies = {}
            for j in jobs:
                co = j.get("company", "Unknown")
                companies[co] = companies.get(co, 0) + 1
            top = sorted(companies.items(), key=lambda x: x[1], reverse=True)[:3]
            for co, count in top:
                findings.append(f"Hiring trend: {co} has {count} open positions")
            recommendations.append("Prioritize companies with highest hiring volume")
            confidence = 0.75

        if not findings:
            findings.append(f"Analysis requested for: {query or program or 'general review'}")
            recommendations.append("Provide job data or BD scores for deeper analysis")

        return self._make_result(
            findings=findings,
            recommendations=recommendations,
            confidence=confidence,
        )


# ---------------------------------------------------------------------------
# 3. Competitor Agent
# ---------------------------------------------------------------------------


class CompetitorAgent(BDAgentBase):
    """Monitors competitive landscape and positioning."""

    name = "competitor"
    role = "Competitive Intelligence Analyst"
    goal = "Track competitor wins, hiring, and teaming arrangements"

    def execute(self, context: dict) -> dict:
        logger.info("agent_execute", agent=self.name, context_keys=list(context.keys()))

        findings: List[str] = []
        recommendations: List[str] = []

        company = context.get("company", context.get("competitor", ""))
        program = context.get("program", context.get("query", ""))

        # Knowledge-based competitor search
        if company:
            results = self._search_knowledge(company, collection="contacts")
            if results:
                findings.append(f"Found {len(results)} contacts at {company}")
            results = self._search_knowledge(company, collection="programs")
            if results:
                findings.append(f"Found {len(results)} programs linked to {company}")

        # Pattern-based competitive analysis
        known_primes = ["GDIT", "Leidos", "SAIC", "BAE Systems", "Northrop Grumman",
                        "Raytheon", "L3Harris", "Booz Allen Hamilton", "CACI", "ManTech"]
        target = company or program
        matched_primes = [p for p in known_primes if p.lower() in str(target).lower()]
        if matched_primes:
            for p in matched_primes:
                findings.append(f"Known prime contractor identified: {p}")
                recommendations.append(f"Assess teaming vs competing against {p}")
        else:
            findings.append(f"Competitive landscape scan for: {target or 'DCGS portfolio'}")
            recommendations.append("Identify incumbent and subcontractor relationships")

        recommendations.append("Monitor competitor job postings for staffing signals")
        recommendations.append("Track contract award announcements on SAM.gov")

        return self._make_result(
            findings=findings,
            recommendations=recommendations,
            confidence=0.6,
        )


# ---------------------------------------------------------------------------
# 4. Playbook Agent
# ---------------------------------------------------------------------------


class PlaybookAgent(BDAgentBase):
    """Generates BD playbooks and capture strategies."""

    name = "playbook"
    role = "Capture Strategy Lead"
    goal = "Produce capture plans, gate reviews, and action items"

    def execute(self, context: dict) -> dict:
        logger.info("agent_execute", agent=self.name, context_keys=list(context.keys()))

        findings: List[str] = []
        recommendations: List[str] = []

        program = context.get("program", context.get("query", ""))
        prior = context.get("prior_results", {})

        # Build playbook from prior intel
        if prior:
            findings.append(f"Capture playbook built from {len(prior)} agent inputs")
            for agent_name, result in prior.items():
                recs = result.get("recommendations", [])
                if recs:
                    findings.append(f"Incorporated {len(recs)} recommendations from {agent_name}")

        # Standard capture phases
        phases = [
            "Phase 0: Opportunity Identification & Qualification",
            "Phase 1: Pre-RFP Positioning & Shaping",
            "Phase 2: Proposal Development & Teaming",
            "Phase 3: Submission & Oral Presentations",
            "Phase 4: Post-Award Transition",
        ]
        for phase in phases:
            recommendations.append(phase)

        findings.append(f"Capture playbook generated for: {program or 'target opportunity'}")
        findings.append("Gate review checkpoints defined for BD pipeline stages")

        return self._make_result(
            findings=findings,
            recommendations=recommendations,
            confidence=0.65,
        )


# ---------------------------------------------------------------------------
# 5. Call Prep Agent
# ---------------------------------------------------------------------------


class CallPrepAgent(BDAgentBase):
    """Prepares call briefings and talking points."""

    name = "call_prep"
    role = "Call Preparation Specialist"
    goal = "Contact background, recent activity, suggested topics"

    def execute(self, context: dict) -> dict:
        logger.info("agent_execute", agent=self.name, context_keys=list(context.keys()))

        findings: List[str] = []
        recommendations: List[str] = []

        contact = context.get("contact", {})
        contact_name = contact.get("name", context.get("contact_name", ""))
        company = contact.get("company", context.get("company", ""))
        program = context.get("program", context.get("query", ""))

        # Use prior research results
        prior = context.get("prior_results", {})
        if prior:
            for agent_name, result in prior.items():
                prior_findings = result.get("findings", [])
                for f in prior_findings[:3]:
                    findings.append(f"[from {agent_name}] {f}")

        # Contact intel
        if contact_name:
            findings.append(f"Briefing prepared for call with: {contact_name}")
            results = self._search_knowledge(contact_name, collection="contacts")
            if results:
                findings.append(f"Found {len(results)} records for {contact_name}")

        if company:
            findings.append(f"Target company: {company}")
            recommendations.append(f"Reference PTS past performance with {company}")

        if program:
            findings.append(f"Program context: {program}")
            recommendations.append(f"Discuss recent developments on {program}")

        # Standard talking points
        recommendations.append("Open with personalized reference to their program")
        recommendations.append("Present PTS cleared staffing capabilities")
        recommendations.append("Identify current pain points and staffing gaps")
        recommendations.append("Propose next steps and follow-up timeline")

        return self._make_result(
            findings=findings,
            recommendations=recommendations,
            confidence=0.6 if contact_name else 0.4,
        )


# ---------------------------------------------------------------------------
# 6. Outreach Agent
# ---------------------------------------------------------------------------


class OutreachAgent(BDAgentBase):
    """Drafts personalized BD outreach messages."""

    name = "outreach"
    role = "BD Outreach Strategist"
    goal = "Email templates, LinkedIn messages, and follow-ups"

    def execute(self, context: dict) -> dict:
        logger.info("agent_execute", agent=self.name, context_keys=list(context.keys()))

        findings: List[str] = []
        recommendations: List[str] = []

        contact_name = context.get("contact_name", context.get("contact", {}).get("name", ""))
        company = context.get("company", "")
        program = context.get("program", context.get("query", ""))
        prior = context.get("prior_results", {})

        # Outreach template generation
        findings.append(f"Outreach draft for: {contact_name or company or 'target contact'}")

        if prior:
            findings.append(f"Personalized using {len(prior)} agent research inputs")

        if program:
            findings.append(f"Program-specific talking points: {program}")
            recommendations.append(f"Reference {program} in subject line")

        recommendations.append("Follow PTS BD Formula: personalized opener → pain points → labor gaps → past performance")
        recommendations.append("Include specific role matches from current openings")
        if company:
            recommendations.append(f"Reference PTS past performance with {company} or similar primes")
        recommendations.append("End with clear call-to-action and proposed meeting time")

        return self._make_result(
            findings=findings,
            recommendations=recommendations,
            confidence=0.55,
        )


# ---------------------------------------------------------------------------
# 7. Win Strategy Agent
# ---------------------------------------------------------------------------


class WinStrategyAgent(BDAgentBase):
    """Develops win strategies and proposal themes."""

    name = "win_strategy"
    role = "Win Strategy Advisor"
    goal = "Win themes, discriminators, and ghost teams"

    def execute(self, context: dict) -> dict:
        logger.info("agent_execute", agent=self.name, context_keys=list(context.keys()))

        findings: List[str] = []
        recommendations: List[str] = []

        program = context.get("program", context.get("query", ""))
        prior = context.get("prior_results", {})

        # Synthesize win strategy from prior results
        if prior:
            findings.append(f"Win strategy synthesized from {len(prior)} intelligence sources")
            # Extract competitive intel
            comp_result = prior.get("competitor", prior.get("researcher", {}))
            if comp_result:
                comp_findings = comp_result.get("findings", [])
                findings.append(f"Competitive factors considered: {len(comp_findings)}")

        # Win theme generation
        findings.append(f"Win strategy developed for: {program or 'target opportunity'}")
        recommendations.append("Win Theme 1: Cleared staffing pipeline — faster fill rates than competitors")
        recommendations.append("Win Theme 2: DCGS domain expertise — proven past performance on ISR programs")
        recommendations.append("Win Theme 3: SDVOSB advantage — socioeconomic set-aside eligibility")
        recommendations.append("Define ghost team: identify teaming partners for capability gaps")
        recommendations.append("Develop price-to-win strategy based on competitive landscape")

        return self._make_result(
            findings=findings,
            recommendations=recommendations,
            confidence=0.65 if prior else 0.4,
        )


# ---------------------------------------------------------------------------
# 8. Account Mapper Agent
# ---------------------------------------------------------------------------


class AccountMapperAgent(BDAgentBase):
    """Maps organizational relationships and influence networks."""

    name = "account_mapper"
    role = "Account Intelligence Mapper"
    goal = "Org charts, decision makers, and influencers"

    def execute(self, context: dict) -> dict:
        logger.info("agent_execute", agent=self.name, context_keys=list(context.keys()))

        findings: List[str] = []
        recommendations: List[str] = []

        company = context.get("company", "")
        program = context.get("program", context.get("query", ""))
        contact_name = context.get("contact_name", "")

        # Knowledge base search for contacts
        search_term = company or program or contact_name
        if search_term:
            results = self._search_knowledge(search_term, collection="contacts")
            if results:
                findings.append(f"Found {len(results)} contacts related to '{search_term}'")
                # Tier classification
                tiers: Dict[str, int] = {}
                for r in results:
                    payload = r.get("payload", r) if isinstance(r, dict) else {}
                    tier = payload.get("tier", "unknown")
                    tier_key = f"Tier {tier}" if tier != "unknown" else "Unclassified"
                    tiers[tier_key] = tiers.get(tier_key, 0) + 1
                for tier_name, count in sorted(tiers.items()):
                    findings.append(f"  {tier_name}: {count} contacts")

        if not findings:
            findings.append(f"Account mapping initiated for: {search_term or 'target organization'}")

        recommendations.append("Identify decision makers (Tier 1-2) for executive engagement")
        recommendations.append("Map influencers (Tier 3) for technical credibility building")
        recommendations.append("Build HUMINT network through Tier 4-6 operational contacts")
        recommendations.append("Cross-reference org chart with program assignments")

        return self._make_result(
            findings=findings,
            recommendations=recommendations,
            confidence=0.6 if search_term else 0.3,
        )


# ---------------------------------------------------------------------------
# Agent Registry
# ---------------------------------------------------------------------------

ALL_AGENTS: Dict[str, type] = {
    "researcher": ResearcherAgent,
    "analyst": AnalystAgent,
    "competitor": CompetitorAgent,
    "playbook": PlaybookAgent,
    "call_prep": CallPrepAgent,
    "outreach": OutreachAgent,
    "win_strategy": WinStrategyAgent,
    "account_mapper": AccountMapperAgent,
}
