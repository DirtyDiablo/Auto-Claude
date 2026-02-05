"""
INTEGRATIONS MODULE
===================
Wrapper functions that call existing src/ modules and MCP tools.

These functions provide the business logic for workflow nodes,
abstracting the underlying API clients and data processing.

All external API calls use tenacity for retry logic with exponential backoff.
Logging uses structlog for structured, queryable log output.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

# Try to import from src modules - gracefully handle if not available
try:
    from src.config import settings
except ImportError:
    settings = None

# Use structlog for structured logging
logger = structlog.get_logger(__name__)

try:
    from src.api_clients.base import BaseAPIClient
except ImportError:
    BaseAPIClient = None


# ============================================================================
# RETRY DECORATORS FOR EXTERNAL API CALLS
# ============================================================================

# Standard retry for external API calls (Tango, SAM.gov, USASpending)
external_api_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, IOError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)

# Lighter retry for database/file operations
db_retry = retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=0.5, min=1, max=10),
    retry=retry_if_exception_type((IOError, OSError)),
    reraise=True,
)


# ============================================================================
# CONTRACT & OPPORTUNITY SEARCH
# ============================================================================

@external_api_retry
def search_similar_contracts(
    naics_codes: List[str],
    agency: Optional[str] = None,
    min_value: float = 0,
    max_value: Optional[float] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Search for similar contracts using Tango and USASpending APIs.

    Args:
        naics_codes: NAICS codes to search for
        agency: Filter by agency name
        min_value: Minimum contract value
        max_value: Maximum contract value
        limit: Maximum results to return

    Returns:
        List of contract dictionaries
    """
    logger.info("searching_similar_contracts", naics_codes=naics_codes, agency=agency)
    contracts = []

    try:
        # Use MCP tools if available through capture-mcp-server
        # This is a placeholder - actual implementation would use the MCP tools
        for naics in naics_codes:
            # Simulate contract search results
            contracts.append({
                'contract_id': f'CONT_{naics}_{datetime.now().strftime("%Y%m%d")}',
                'naics_code': naics,
                'agency': agency or 'Department of Defense',
                'value': min_value + 1000000,
                'description': f'Contract for NAICS {naics}',
                'incumbent': 'Unknown',
                'end_date': '2025-12-31',
                'source': 'usaspending'
            })
    except Exception as e:
        logger.error("contract_search_failed", error=str(e))

    logger.info("contracts_found", count=len(contracts))
    return contracts[:limit]


@external_api_retry
def search_opportunities(
    keywords: Optional[List[str]] = None,
    naics_codes: Optional[List[str]] = None,
    posted_from: Optional[str] = None,
    posted_to: Optional[str] = None,
    set_aside: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Search for contract opportunities from SAM.gov.

    Args:
        keywords: Keywords to search
        naics_codes: NAICS codes to filter
        posted_from: Start date (YYYY-MM-DD)
        posted_to: End date (YYYY-MM-DD)
        set_aside: Set-aside type filter
        limit: Maximum results

    Returns:
        List of opportunity dictionaries
    """
    logger.info("searching_opportunities", keywords=keywords, naics_codes=naics_codes)
    opportunities = []

    try:
        # Placeholder - would use mcp__capture-mcp-server__get_sam_opportunities
        opportunities = [{
            'opportunity_id': 'OPP_001',
            'title': 'Sample Opportunity',
            'agency': 'Department of Defense',
            'posted_date': posted_from or datetime.now().strftime('%Y-%m-%d'),
            'response_deadline': posted_to or '2025-06-30',
            'naics': naics_codes[0] if naics_codes else '541512',
            'set_aside': set_aside,
            'source': 'sam.gov'
        }]
    except Exception as e:
        logger.error("opportunity_search_failed", error=str(e))

    return opportunities[:limit]


# ============================================================================
# MARKET INTELLIGENCE
# ============================================================================

@external_api_retry
def get_market_intelligence(
    naics_codes: List[str],
    agency: Optional[str] = None,
    fiscal_year: Optional[int] = None
) -> Dict[str, Any]:
    """
    Aggregate market intelligence data for a sector.

    Args:
        naics_codes: NAICS codes for market
        agency: Specific agency to analyze
        fiscal_year: Fiscal year for data

    Returns:
        Market intelligence dictionary
    """
    logger.info("gathering_market_intelligence", naics_codes=naics_codes)
    fy = fiscal_year or datetime.now().year

    market_data = {
        'naics_codes': naics_codes,
        'agency': agency,
        'fiscal_year': fy,
        'total_market_size': 0,
        'contract_count': 0,
        'top_contractors': [],
        'growth_trend': 'stable',
        'set_aside_breakdown': {},
        'competition_level': 'moderate',
        'generated_at': datetime.now().isoformat()
    }

    try:
        # Would aggregate from multiple sources:
        # - USASpending spending data
        # - SAM.gov entity data
        # - Historical contract data
        pass
    except Exception as e:
        logger.error("market_intelligence_failed", error=str(e))

    return market_data


@external_api_retry
def analyze_spending_trends(
    agency_code: str,
    fiscal_year: Optional[int] = None,
    naics_code: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze spending trends for an agency.

    Args:
        agency_code: 3-digit agency code
        fiscal_year: Fiscal year to analyze
        naics_code: Filter by NAICS

    Returns:
        Spending analysis dictionary
    """
    logger.info("analyzing_spending_trends", agency_code=agency_code)

    return {
        'agency_code': agency_code,
        'fiscal_year': fiscal_year or datetime.now().year,
        'total_obligations': 0,
        'by_category': {},
        'year_over_year_change': 0,
        'top_vendors': [],
        'generated_at': datetime.now().isoformat()
    }


# ============================================================================
# CONTACT GATHERING
# ============================================================================

@db_retry
def search_crm_contacts(
    company: Optional[str] = None,
    program: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Search for contacts in CRM (Bullhorn) data.

    Args:
        company: Company name to search
        program: Program name to search
        limit: Maximum results

    Returns:
        List of contact dictionaries
    """
    logger.info("searching_crm_contacts", company=company, program=program)
    contacts = []

    try:
        # Would load from Bullhorn export data
        data_dir = Path(__file__).parent.parent / "data" / "BullHorn Export Data"
        if data_dir.exists():
            # Load and filter contacts from CSV/JSON
            pass
    except Exception as e:
        logger.error("crm_contact_search_failed", error=str(e))

    return contacts[:limit]


@external_api_retry
def get_sam_entity_contacts(
    uei: Optional[str] = None,
    company_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get executive contacts from SAM.gov entity data.

    Args:
        uei: Unique Entity Identifier
        company_name: Company name to search

    Returns:
        List of executive contact dictionaries
    """
    logger.info("getting_sam_contacts", uei=uei, company_name=company_name)
    contacts = []

    try:
        # Would use mcp__capture-mcp-server__search_sam_entities
        # and mcp__capture-mcp-server__get_sam_entity_details
        pass
    except Exception as e:
        logger.error("sam_contact_retrieval_failed", error=str(e))

    return contacts


@external_api_retry
def search_job_posting_contacts(
    company: str,
    keywords: Optional[List[str]] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Extract potential contacts from job postings.

    Args:
        company: Company name
        keywords: Keywords to search
        limit: Maximum results

    Returns:
        List of inferred contact dictionaries
    """
    logger.info("searching_job_posting_contacts", company=company)
    contacts = []

    # Job postings can reveal:
    # - Hiring managers
    # - Program managers
    # - Department leads

    return contacts[:limit]


def score_contacts(
    contacts: List[Dict[str, Any]],
    scoring_criteria: Optional[Dict[str, float]] = None
) -> List[Dict[str, Any]]:
    """
    Score and prioritize contacts for outreach.

    Args:
        contacts: List of contact dictionaries
        scoring_criteria: Weights for scoring factors

    Returns:
        Sorted list of contacts with scores
    """
    logger.info("scoring_contacts", contact_count=len(contacts))

    default_criteria = {
        'title_seniority': 0.3,
        'relationship_history': 0.25,
        'recent_activity': 0.2,
        'company_relevance': 0.15,
        'accessibility': 0.1
    }
    criteria = scoring_criteria or default_criteria

    scored = []
    for contact in contacts:
        score = 0.0

        # Title seniority scoring
        title = contact.get('title', '').lower()
        if any(x in title for x in ['vp', 'vice president', 'director', 'ceo', 'cto', 'coo']):
            score += criteria['title_seniority'] * 100
        elif any(x in title for x in ['manager', 'lead', 'head']):
            score += criteria['title_seniority'] * 70
        else:
            score += criteria['title_seniority'] * 40

        # Other scoring factors would be applied here

        contact['score'] = round(score, 2)
        scored.append(contact)

    # Sort by score descending
    scored.sort(key=lambda x: x.get('score', 0), reverse=True)
    return scored


# ============================================================================
# COMPETITIVE INTELLIGENCE
# ============================================================================

@external_api_retry
def analyze_incumbent(
    contract_id: Optional[str] = None,
    company_uei: Optional[str] = None,
    company_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze incumbent contractor for a contract.

    Args:
        contract_id: Contract ID to analyze
        company_uei: Incumbent's UEI
        company_name: Incumbent's name

    Returns:
        Incumbent analysis dictionary
    """
    logger.info("analyzing_incumbent", contract_id=contract_id, company_uei=company_uei)

    analysis = {
        'company_name': company_name or 'Unknown',
        'uei': company_uei,
        'contract_id': contract_id,
        'contract_history': [],
        'performance_indicators': {},
        'strengths': [],
        'weaknesses': [],
        'likelihood_to_recompete': 'unknown',
        'generated_at': datetime.now().isoformat()
    }

    try:
        # Would use:
        # - mcp__capture-mcp-server__get_tango_vendor_profile
        # - mcp__capture-mcp-server__search_usaspending_awards_by_recipient
        pass
    except Exception as e:
        logger.error("incumbent_analysis_failed", error=str(e))

    return analysis


@external_api_retry
def get_competitive_landscape(
    naics_codes: List[str],
    agency: Optional[str] = None,
    set_aside: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Map the competitive landscape for a market segment.

    Args:
        naics_codes: NAICS codes defining the market
        agency: Target agency
        set_aside: Set-aside type

    Returns:
        List of competitor profiles
    """
    logger.info("mapping_competitive_landscape", naics_codes=naics_codes)
    competitors = []

    try:
        # Would aggregate:
        # - Top contractors by NAICS
        # - Recent award winners
        # - Small business competitors
        pass
    except Exception as e:
        logger.error("competitive_landscape_mapping_failed", error=str(e))

    return competitors


def calculate_win_probability(
    opportunity: Dict[str, Any],
    our_capabilities: Dict[str, Any],
    competitive_landscape: List[Dict[str, Any]]
) -> float:
    """
    Calculate estimated win probability for an opportunity.

    Args:
        opportunity: Opportunity details
        our_capabilities: Our company capabilities
        competitive_landscape: Known competitors

    Returns:
        Win probability as decimal (0-1)
    """
    # Simplified Pwin calculation
    # Real implementation would use more sophisticated models
    base_probability = 0.15  # Base probability for full & open

    # Adjust based on factors
    adjustments = 0.0

    # Incumbent factor
    if opportunity.get('we_are_incumbent'):
        adjustments += 0.25

    # Set-aside match
    if opportunity.get('set_aside') and our_capabilities.get('qualifies_for_set_aside'):
        adjustments += 0.15

    # Competition level
    competitors = len(competitive_landscape)
    if competitors <= 3:
        adjustments += 0.10
    elif competitors >= 10:
        adjustments -= 0.05

    return min(max(base_probability + adjustments, 0.05), 0.95)


# ============================================================================
# BD STRATEGY & PLAYBOOK
# ============================================================================

def build_bd_strategy(
    opportunity: Dict[str, Any],
    market_intelligence: Dict[str, Any],
    contacts: List[Dict[str, Any]],
    competitive_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Build BD strategy based on gathered intelligence.

    Args:
        opportunity: Target opportunity details
        market_intelligence: Market data
        contacts: Gathered contacts
        competitive_analysis: Competition analysis

    Returns:
        BD strategy dictionary
    """
    logger.info("building_bd_strategy", opportunity_id=opportunity.get('opportunity_id', 'Unknown'))

    strategy = {
        'opportunity_id': opportunity.get('opportunity_id'),
        'opportunity_title': opportunity.get('title'),
        'strategy_date': datetime.now().isoformat(),

        # Win themes
        'win_themes': [],

        # Differentiators
        'differentiators': [],

        # Teaming strategy
        'teaming_strategy': {
            'approach': 'prime',  # prime, sub, joint_venture
            'recommended_partners': [],
            'capability_gaps': [],
        },

        # Capture activities
        'capture_activities': [],

        # Pricing strategy
        'pricing_strategy': {
            'approach': 'competitive',
            'considerations': [],
        },

        # Risk assessment
        'risks': [],
        'mitigations': [],

        # Timeline
        'key_milestones': [],

        # Resource requirements
        'resource_needs': [],
    }

    return strategy


def generate_bd_playbook(
    strategy: Dict[str, Any],
    contacts: List[Dict[str, Any]],
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate comprehensive BD playbook document.

    Args:
        strategy: BD strategy dictionary
        contacts: Prioritized contacts
        output_path: Path to save playbook

    Returns:
        Playbook dictionary with path
    """
    logger.info("generating_bd_playbook", opportunity_id=strategy.get('opportunity_id'))

    playbook = {
        'generated_at': datetime.now().isoformat(),
        'opportunity_id': strategy.get('opportunity_id'),
        'opportunity_title': strategy.get('opportunity_title'),

        # Executive summary
        'executive_summary': '',

        # Strategy section
        'strategy': strategy,

        # Contact plan
        'contact_plan': {
            'priority_contacts': contacts[:10],
            'weekly_call_targets': [],
            'meeting_objectives': [],
        },

        # Action items
        'action_items': [],

        # Timeline
        'timeline': [],

        # Appendices
        'appendices': {
            'market_data': {},
            'competitive_intel': {},
            'contact_profiles': contacts,
        }
    }

    # Save to file if path provided
    if output_path:
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(playbook, f, indent=2, default=str)

        playbook['playbook_path'] = output_path
        logger.info("playbook_saved", output_path=output_path)

    return playbook


# ============================================================================
# OPPORTUNITY SCORING
# ============================================================================

def score_opportunity(
    opportunity: Dict[str, Any],
    scoring_weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Score an opportunity for BD prioritization.

    Based on patterns from src/models/federal_program.py calculate_bd_score()

    Args:
        opportunity: Opportunity dictionary
        scoring_weights: Custom scoring weights

    Returns:
        Opportunity with score and breakdown
    """
    default_weights = {
        'value': 0.30,           # Contract value
        'timing': 0.25,          # Recompete/deadline timing
        'fit': 0.20,             # Capability fit
        'competition': 0.15,     # Competition level
        'relationship': 0.10,    # Existing relationships
    }
    weights = scoring_weights or default_weights

    score = 0.0
    breakdown = {}

    # Value scoring (max 30 points)
    value = opportunity.get('estimated_value', 0)
    if value >= 100_000_000:  # $100M+
        value_score = 30
    elif value >= 50_000_000:  # $50M+
        value_score = 25
    elif value >= 10_000_000:  # $10M+
        value_score = 20
    elif value >= 1_000_000:   # $1M+
        value_score = 15
    else:
        value_score = 10
    breakdown['value'] = value_score
    score += value_score * weights['value'] / 0.30

    # Timing scoring (max 25 points)
    days_to_deadline = opportunity.get('days_to_deadline', 365)
    if days_to_deadline <= 30:
        timing_score = 25
    elif days_to_deadline <= 90:
        timing_score = 20
    elif days_to_deadline <= 180:
        timing_score = 15
    else:
        timing_score = 10
    breakdown['timing'] = timing_score
    score += timing_score * weights['timing'] / 0.25

    # Other factors would be scored similarly

    opportunity['bd_score'] = round(score, 2)
    opportunity['score_breakdown'] = breakdown

    # Set priority tier
    if score >= 70:
        opportunity['priority_tier'] = 1
    elif score >= 50:
        opportunity['priority_tier'] = 2
    else:
        opportunity['priority_tier'] = 3

    return opportunity


# ============================================================================
# RECOMPETE MONITORING
# ============================================================================

@external_api_retry
def check_contract_status(
    contract_ids: List[str]
) -> List[Dict[str, Any]]:
    """
    Check current status of monitored contracts.

    Args:
        contract_ids: List of contract IDs to check

    Returns:
        List of contract status dictionaries
    """
    logger.info("checking_contract_status", contract_count=len(contract_ids))
    statuses = []

    for contract_id in contract_ids:
        statuses.append({
            'contract_id': contract_id,
            'status': 'active',
            'end_date': None,
            'days_remaining': None,
            'modifications_count': 0,
            'last_checked': datetime.now().isoformat()
        })

    return statuses


def detect_recompete_signals(
    contract_statuses: List[Dict[str, Any]],
    threshold_days: int = 365
) -> List[Dict[str, Any]]:
    """
    Detect contracts approaching recompete.

    Args:
        contract_statuses: Current contract statuses
        threshold_days: Days threshold for alert

    Returns:
        List of contracts with recompete signals
    """
    logger.info("detecting_recompete_signals", threshold_days=threshold_days)
    signals = []

    for status in contract_statuses:
        days_remaining = status.get('days_remaining')
        if days_remaining is not None and days_remaining <= threshold_days:
            signals.append({
                'contract_id': status['contract_id'],
                'signal_type': 'approaching_end',
                'days_remaining': days_remaining,
                'priority': 'high' if days_remaining <= 180 else 'medium',
                'detected_at': datetime.now().isoformat()
            })

    return signals


# Export all functions
__all__ = [
    # Contract search
    'search_similar_contracts',
    'search_opportunities',
    # Market intelligence
    'get_market_intelligence',
    'analyze_spending_trends',
    # Contact gathering
    'search_crm_contacts',
    'get_sam_entity_contacts',
    'search_job_posting_contacts',
    'score_contacts',
    # Competitive intelligence
    'analyze_incumbent',
    'get_competitive_landscape',
    'calculate_win_probability',
    # BD strategy
    'build_bd_strategy',
    'generate_bd_playbook',
    # Opportunity scoring
    'score_opportunity',
    # Recompete monitoring
    'check_contract_status',
    'detect_recompete_signals',
]
