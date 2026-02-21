"""Portfolio-aware scoring engine.

Scores jobs and opportunities against a specific portfolio configuration,
applying portfolio-specific boosts for clearance, keywords, location,
and program alignment.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from Engine8_Knowledge.portfolios.portfolio_config import PortfolioConfig

try:
    import structlog

    logger = structlog.get_logger("PortfolioScorer")
except ImportError:
    logger = logging.getLogger("PortfolioScorer")


class PortfolioScorer:
    """Score jobs/opportunities against a specific portfolio config."""

    BASE_SCORE = 50
    PROGRAM_MATCH_BOOST = 20
    HOT_THRESHOLD = 80
    WARM_THRESHOLD = 50

    def __init__(self, portfolio: PortfolioConfig):
        self.portfolio = portfolio

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score(self, job: dict) -> dict:
        """Score a single job against this portfolio.

        Returns:
            dict with keys: score, tier, breakdown, portfolio_id
        """
        breakdown: Dict[str, int] = {}

        # Base score
        base = self.BASE_SCORE
        breakdown["base_score"] = base

        # Clearance boost
        clearance_boost = self._clearance_boost(job)
        breakdown["clearance_boost"] = clearance_boost

        # Primary keyword boost
        keyword_boost = self._keyword_boost(job)
        breakdown["keyword_boost"] = keyword_boost

        # Secondary keyword boost
        secondary_boost = self._secondary_keyword_boost(job)
        breakdown["secondary_keyword_boost"] = secondary_boost

        # Location boost
        location_boost = self._location_boost(job)
        breakdown["location_boost"] = location_boost

        # Program match boost
        program_boost = self._program_boost(job)
        breakdown["program_boost"] = program_boost

        total = base + clearance_boost + keyword_boost + secondary_boost + location_boost + program_boost
        total = min(total, 100)
        total = max(total, 0)

        tier = self._classify_tier(total)

        return {
            "score": total,
            "tier": tier,
            "breakdown": breakdown,
            "portfolio_id": self.portfolio.id,
        }

    def score_batch(self, jobs: list) -> list:
        """Score multiple jobs against this portfolio."""
        return [self.score(job) for job in jobs]

    def cross_portfolio_analysis(self, job: dict, portfolios: list) -> dict:
        """Score a single job against multiple portfolios and rank them.

        Args:
            job: Job data dictionary.
            portfolios: List of PortfolioConfig instances to score against.

        Returns:
            dict with keys: job, rankings (sorted best-first), best_match
        """
        rankings = []
        for portfolio in portfolios:
            scorer = PortfolioScorer(portfolio)
            result = scorer.score(job)
            result["portfolio_name"] = portfolio.name
            rankings.append(result)

        rankings.sort(key=lambda r: r["score"], reverse=True)

        best = rankings[0] if rankings else None

        return {
            "job": job,
            "rankings": rankings,
            "best_match": best,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _clearance_boost(self, job: dict) -> int:
        """Calculate clearance-based score boost."""
        clearance = self._extract_field(job, ["clearance", "Security Clearance", "security_clearance"])
        if not clearance:
            return 0

        clearance_upper = clearance.upper()
        for level, boost in self.portfolio.clearance_boost.items():
            if level.upper() in clearance_upper:
                return boost
        return 0

    def _keyword_boost(self, job: dict) -> int:
        """Calculate primary keyword match boost."""
        text = self._job_text(job)
        if not text:
            return 0

        text_upper = text.upper()
        for kw in self.portfolio.keywords:
            if kw.upper() in text_upper:
                return self.portfolio.keyword_boost
        return 0

    def _secondary_keyword_boost(self, job: dict) -> int:
        """Calculate secondary keyword match boost (half of keyword_boost)."""
        text = self._job_text(job)
        if not text:
            return 0

        text_upper = text.upper()
        for kw in self.portfolio.secondary_keywords:
            if kw.upper() in text_upper:
                return self.portfolio.keyword_boost // 2
        return 0

    def _location_boost(self, job: dict) -> int:
        """Calculate location-based score boost."""
        location = self._extract_field(job, ["location", "Location", "city", "site"])
        if not location:
            return 0

        location_upper = location.upper()
        for loc_kw in self.portfolio.location_keywords:
            if loc_kw.upper() in location_upper:
                return self.portfolio.location_boost
        return 0

    def _program_boost(self, job: dict) -> int:
        """Calculate program name match boost."""
        program = self._extract_field(job, ["program", "Program", "program_name"])
        if not program:
            return 0

        program_upper = program.upper()
        for prog in self.portfolio.programs:
            if prog.upper() in program_upper or program_upper in prog.upper():
                return self.PROGRAM_MATCH_BOOST
        return 0

    def _classify_tier(self, score: int) -> str:
        """Classify score into Hot/Warm/Cold tier."""
        if score >= self.HOT_THRESHOLD:
            return "Hot"
        elif score >= self.WARM_THRESHOLD:
            return "Warm"
        return "Cold"

    @staticmethod
    def _extract_field(job: dict, keys: list) -> str:
        """Extract the first non-empty value from a list of candidate keys."""
        for key in keys:
            val = job.get(key)
            if val:
                return str(val)
        return ""

    @staticmethod
    def _job_text(job: dict) -> str:
        """Build a searchable text blob from common job fields."""
        parts = []
        for key in ("title", "Title", "description", "Description", "skills", "Skills",
                     "program", "Program", "requirements", "Requirements", "summary", "Summary"):
            val = job.get(key)
            if val:
                parts.append(str(val))
        return " ".join(parts)
