"""Phase 35A — Labor Category & Pricing Engine

Labor category builder and pricing intelligence:
  - Map to GSA schedule rates, market rates, and competitor pricing signals
  - Bill rate analysis from GDIT Jobs + market benchmarks
  - Pricing templates: T&M, FFP, CPFF with labor mixes
  - Rate card generator with escalation factors
  - Competitive pricing intelligence from job scrape salary data
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# DATA CLASSES
# =========================================


class PricingModel(str, Enum):
    TIME_AND_MATERIALS = "T&M"
    FIRM_FIXED_PRICE = "FFP"
    COST_PLUS_FIXED_FEE = "CPFF"
    COST_PLUS_AWARD_FEE = "CPAF"


@dataclass
class LaborCategory:
    """Single labor category definition."""

    id: str
    title: str
    description: str = ""
    min_education: str = ""  # BS, MS, PhD
    min_experience_years: int = 0
    clearance_required: str = ""
    certifications: List[str] = field(default_factory=list)
    gsa_rate: float = 0.0  # GSA schedule hourly rate
    market_rate: float = 0.0  # Market average hourly rate
    proposed_rate: float = 0.0  # Our proposed rate
    salary_range_low: float = 0.0
    salary_range_high: float = 0.0
    functional_area: str = ""  # e.g., "Engineering", "Analysis", "PM"


@dataclass
class RateCard:
    """Complete rate card for a pricing proposal."""

    id: str
    title: str
    categories: List[LaborCategory] = field(default_factory=list)
    pricing_model: PricingModel = PricingModel.TIME_AND_MATERIALS
    escalation_rate: float = 3.0  # Annual escalation %
    base_year: int = 0
    option_years: int = 4
    generated_at: str = ""
    total_categories: int = 0


@dataclass
class PricingTemplate:
    """Pricing template for a proposal."""

    id: str
    model: PricingModel
    rate_card: RateCard = field(default_factory=lambda: RateCard(id="", title=""))
    base_year_value: float = 0.0
    total_value: float = 0.0
    year_values: List[Dict[str, Any]] = field(default_factory=list)
    labor_mix: Dict[str, int] = field(default_factory=dict)  # category -> FTE count
    generated_at: str = ""


@dataclass
class PricingAnalysis:
    """Competitive pricing analysis."""

    id: str
    program: str
    avg_market_rate: float = 0.0
    our_rate: float = 0.0
    competitive_position: str = ""  # below_market, at_market, above_market
    rate_comparison: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    generated_at: str = ""


# =========================================
# GSA SCHEDULE RATES (REPRESENTATIVE)
# =========================================

GSA_SCHEDULE_RATES = {
    "Program Manager": {"rate": 195.00, "education": "MS", "experience": 15},
    "Senior Systems Engineer": {"rate": 175.00, "education": "BS", "experience": 12},
    "Systems Engineer": {"rate": 145.00, "education": "BS", "experience": 8},
    "Senior Software Engineer": {"rate": 170.00, "education": "BS", "experience": 10},
    "Software Engineer": {"rate": 140.00, "education": "BS", "experience": 5},
    "Senior Intelligence Analyst": {
        "rate": 155.00,
        "education": "BS",
        "experience": 10,
    },
    "Intelligence Analyst": {"rate": 120.00, "education": "BS", "experience": 5},
    "Junior Intelligence Analyst": {"rate": 85.00, "education": "BS", "experience": 2},
    "Cybersecurity Engineer": {"rate": 160.00, "education": "BS", "experience": 8},
    "Cloud Architect": {"rate": 185.00, "education": "BS", "experience": 12},
    "Data Scientist": {"rate": 165.00, "education": "MS", "experience": 8},
    "DevOps Engineer": {"rate": 155.00, "education": "BS", "experience": 6},
    "Technical Writer": {"rate": 95.00, "education": "BS", "experience": 5},
    "Help Desk Specialist": {"rate": 65.00, "education": "AS", "experience": 2},
    "Network Engineer": {"rate": 140.00, "education": "BS", "experience": 6},
    "Database Administrator": {"rate": 135.00, "education": "BS", "experience": 6},
    "Subject Matter Expert": {"rate": 200.00, "education": "MS", "experience": 15},
    "Quality Assurance Analyst": {"rate": 110.00, "education": "BS", "experience": 5},
}

# Clearance premium multipliers
CLEARANCE_PREMIUMS = {
    "TS/SCI CI Poly": 1.25,
    "TS/SCI": 1.18,
    "Top Secret": 1.12,
    "Secret": 1.05,
    "Public Trust": 1.0,
    "None": 1.0,
}

# Market rate adjustment (relative to GSA)
MARKET_RATE_FACTOR = 0.92  # Market typically 8% below GSA ceiling


# =========================================
# ENGINE
# =========================================


class PricingEngine:
    """Labor category builder and pricing engine."""

    def __init__(self, knowledge_client: Any = None):
        self._knowledge = knowledge_client
        self._history_rate_cards: List[RateCard] = []
        self._history_analyses: List[PricingAnalysis] = []

    def set_knowledge_client(self, client: Any) -> None:
        self._knowledge = client

    def build_labor_category(
        self,
        title: str,
        clearance: str = "Secret",
        experience_years: int = 5,
        education: str = "BS",
        certifications: Optional[List[str]] = None,
    ) -> LaborCategory:
        """Build a single labor category with rates."""
        # Find closest GSA match
        gsa_entry = GSA_SCHEDULE_RATES.get(title)
        if not gsa_entry:
            # Fuzzy match
            title_lower = title.lower()
            for gsa_title, data in GSA_SCHEDULE_RATES.items():
                if any(word in gsa_title.lower() for word in title_lower.split()):
                    gsa_entry = data
                    break

        base_rate = gsa_entry["rate"] if gsa_entry else 120.0
        clearance_mult = CLEARANCE_PREMIUMS.get(clearance, 1.0)
        gsa_rate = round(base_rate * clearance_mult, 2)
        market_rate = round(gsa_rate * MARKET_RATE_FACTOR, 2)
        # Propose between market and GSA ceiling
        proposed_rate = round((gsa_rate + market_rate) / 2, 2)

        # Salary estimation (assume 2080 hours/year, ~60% bill-to-salary ratio)
        salary_mid = proposed_rate * 2080 * 0.55
        salary_low = round(salary_mid * 0.85, 0)
        salary_high = round(salary_mid * 1.15, 0)

        # Determine functional area
        functional_area = _categorize_functional_area(title)

        return LaborCategory(
            id=f"lc-{title.lower().replace(' ', '-')[:30]}",
            title=title,
            description=f"{title} with {experience_years}+ years experience, {education} minimum",
            min_education=education,
            min_experience_years=experience_years,
            clearance_required=clearance,
            certifications=certifications or [],
            gsa_rate=gsa_rate,
            market_rate=market_rate,
            proposed_rate=proposed_rate,
            salary_range_low=salary_low,
            salary_range_high=salary_high,
            functional_area=functional_area,
        )

    def generate_rate_card(
        self,
        title: str,
        categories: List[LaborCategory],
        pricing_model: PricingModel = PricingModel.TIME_AND_MATERIALS,
        base_year: int = 0,
        option_years: int = 4,
        escalation_rate: float = 3.0,
    ) -> RateCard:
        """Generate a complete rate card."""
        if base_year == 0:
            base_year = datetime.now(timezone.utc).year

        card = RateCard(
            id=f"rc-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            title=title,
            categories=categories,
            pricing_model=pricing_model,
            escalation_rate=escalation_rate,
            base_year=base_year,
            option_years=option_years,
            generated_at=datetime.now(timezone.utc).isoformat(),
            total_categories=len(categories),
        )

        self._history_rate_cards.append(card)
        logger.info(f"Generated rate card '{title}' with {len(categories)} categories")
        return card

    def generate_pricing_template(
        self,
        rate_card: RateCard,
        labor_mix: Dict[str, int],
        hours_per_fte: int = 2080,
    ) -> PricingTemplate:
        """Generate a pricing template from rate card and labor mix."""
        # Build category lookup
        cat_by_title = {c.title: c for c in rate_card.categories}
        cat_by_id = {c.id: c for c in rate_card.categories}

        year_values = []
        total_value = 0.0

        total_years = 1 + rate_card.option_years
        for year_idx in range(total_years):
            escalation = (1 + rate_card.escalation_rate / 100) ** year_idx
            year_label = "Base Year" if year_idx == 0 else f"Option Year {year_idx}"
            year_total = 0.0
            year_detail = []

            for cat_key, fte_count in labor_mix.items():
                cat = cat_by_title.get(cat_key) or cat_by_id.get(cat_key)
                if not cat:
                    continue
                escalated_rate = round(cat.proposed_rate * escalation, 2)
                line_total = round(escalated_rate * hours_per_fte * fte_count, 2)
                year_total += line_total
                year_detail.append(
                    {
                        "category": cat.title,
                        "fte": fte_count,
                        "rate": escalated_rate,
                        "hours": hours_per_fte * fte_count,
                        "total": line_total,
                    }
                )

            year_values.append(
                {
                    "year": year_label,
                    "year_number": year_idx,
                    "total": round(year_total, 2),
                    "detail": year_detail,
                }
            )
            total_value += year_total

        base_value = year_values[0]["total"] if year_values else 0

        template = PricingTemplate(
            id=f"pt-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            model=rate_card.pricing_model,
            rate_card=rate_card,
            base_year_value=round(base_value, 2),
            total_value=round(total_value, 2),
            year_values=year_values,
            labor_mix=labor_mix,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

        logger.info(
            f"Generated {rate_card.pricing_model.value} pricing template: "
            f"${total_value:,.0f} total over {total_years} years"
        )
        return template

    async def analyze_competitive_pricing(
        self,
        program: str,
        categories: Optional[List[LaborCategory]] = None,
        market_data: Optional[List[dict]] = None,
    ) -> PricingAnalysis:
        """Analyze competitive pricing position."""
        if not categories:
            categories = []

        # Build comparison
        rate_comparisons = []
        total_our = 0.0
        total_market = 0.0

        for cat in categories:
            market_avg = cat.market_rate
            # Check for scraped market data
            if market_data:
                matching = [
                    m
                    for m in market_data
                    if cat.title.lower() in m.get("title", "").lower()
                ]
                if matching:
                    salaries = [
                        m.get("salary", 0) for m in matching if m.get("salary", 0) > 0
                    ]
                    if salaries:
                        avg_salary = sum(salaries) / len(salaries)
                        market_avg = round(
                            avg_salary / 2080 / 0.55, 2
                        )  # Convert salary to bill rate

            diff_pct = (
                ((cat.proposed_rate - market_avg) / market_avg * 100)
                if market_avg > 0
                else 0
            )

            rate_comparisons.append(
                {
                    "category": cat.title,
                    "our_rate": cat.proposed_rate,
                    "market_rate": round(market_avg, 2),
                    "gsa_ceiling": cat.gsa_rate,
                    "difference_pct": round(diff_pct, 1),
                }
            )

            total_our += cat.proposed_rate
            total_market += market_avg

        avg_our = total_our / len(categories) if categories else 0
        avg_market = total_market / len(categories) if categories else 0

        if avg_our < avg_market * 0.95:
            position = "below_market"
        elif avg_our > avg_market * 1.05:
            position = "above_market"
        else:
            position = "at_market"

        recommendations = _generate_pricing_recommendations(position, rate_comparisons)

        analysis = PricingAnalysis(
            id=f"pa-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            program=program,
            avg_market_rate=round(avg_market, 2),
            our_rate=round(avg_our, 2),
            competitive_position=position,
            rate_comparison=rate_comparisons,
            recommendations=recommendations,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

        self._history_analyses.append(analysis)
        logger.info(
            f"Competitive analysis for {program}: {position} (avg ${avg_our:.2f} vs market ${avg_market:.2f})"
        )
        return analysis

    def get_rate_card_history(self) -> List[RateCard]:
        return list(self._history_rate_cards)

    def get_analysis_history(self) -> List[PricingAnalysis]:
        return list(self._history_analyses)

    def export_rate_card_to_dict(self, card: RateCard) -> Dict[str, Any]:
        """Export rate card to serializable dictionary."""
        return {
            "id": card.id,
            "title": card.title,
            "pricing_model": card.pricing_model.value,
            "base_year": card.base_year,
            "option_years": card.option_years,
            "escalation_rate": card.escalation_rate,
            "total_categories": card.total_categories,
            "generated_at": card.generated_at,
            "categories": [
                {
                    "title": c.title,
                    "description": c.description,
                    "education": c.min_education,
                    "experience_years": c.min_experience_years,
                    "clearance": c.clearance_required,
                    "gsa_rate": c.gsa_rate,
                    "market_rate": c.market_rate,
                    "proposed_rate": c.proposed_rate,
                    "salary_range": f"${c.salary_range_low:,.0f} - ${c.salary_range_high:,.0f}",
                }
                for c in card.categories
            ],
        }


# =========================================
# HELPERS
# =========================================


def _categorize_functional_area(title: str) -> str:
    """Map title to functional area."""
    title_lower = title.lower()
    areas = {
        "Engineering": ["engineer", "architect", "devops", "cloud"],
        "Analysis": ["analyst", "intelligence", "data scientist"],
        "Management": ["manager", "director", "lead"],
        "Cyber": ["cyber", "security", "ia"],
        "Support": ["help desk", "admin", "technical writer", "qa"],
    }
    for area, keywords in areas.items():
        if any(kw in title_lower for kw in keywords):
            return area
    return "General"


def _generate_pricing_recommendations(
    position: str,
    comparisons: List[Dict[str, Any]],
) -> List[str]:
    """Generate pricing recommendations based on analysis."""
    recs = []
    if position == "above_market":
        recs.append(
            "Consider reducing rates on high-volume categories to improve competitiveness."
        )
        recs.append(
            "Emphasize value-added services and SDVOSB set-aside advantages to justify premium."
        )
    elif position == "below_market":
        recs.append(
            "Strong price competitiveness — ensure rates still cover costs and margins."
        )
        recs.append(
            "Consider raising rates on senior categories where PTS has clear differentiation."
        )
    else:
        recs.append(
            "Rates are market-competitive. Focus proposal win strategy on technical approach and past performance."
        )

    # Category-specific recommendations
    for comp in comparisons:
        diff = comp.get("difference_pct", 0)
        if diff > 15:
            recs.append(
                f"'{comp['category']}' is {diff:.0f}% above market — consider adjusting."
            )
        elif diff < -15:
            recs.append(
                f"'{comp['category']}' is {abs(diff):.0f}% below market — strong competitive position."
            )

    return recs[:6]  # Limit recommendations


# =========================================
# SINGLETON
# =========================================

_engine: Optional[PricingEngine] = None


def get_pricing_engine() -> PricingEngine:
    global _engine
    if _engine is None:
        _engine = PricingEngine()
    return _engine
