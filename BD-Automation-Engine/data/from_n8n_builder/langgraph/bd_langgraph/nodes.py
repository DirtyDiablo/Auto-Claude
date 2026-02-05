"""
WORKFLOW NODE FUNCTIONS
=======================
Node functions for LangGraph workflows. Each function represents a single step
in a workflow graph.

Nodes follow the pattern:
1. Receive state dictionary
2. Perform operation using integrations
3. Return updated state fields
"""

from datetime import datetime
from typing import Any, Dict
import uuid

from .states import (
    WorkflowStatus,
    HumanReviewType,
    BDProposalState,
    ContactOutreachState,
    RecompeteState,
    WeeklyPipelineState,
)
from .integrations import (
    search_similar_contracts,
    search_opportunities,
    get_market_intelligence,
    search_crm_contacts,
    get_sam_entity_contacts,
    search_job_posting_contacts,
    score_contacts,
    analyze_incumbent,
    get_competitive_landscape,
    calculate_win_probability,
    build_bd_strategy,
    generate_bd_playbook,
    score_opportunity,
    check_contract_status,
    detect_recompete_signals,
)
from .human_in_loop import create_review_request

# Try to import logger
try:
    from src.utils import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


# ============================================================================
# BD PROPOSAL PIPELINE NODES
# ============================================================================

def research_opportunity(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Research phase: Find similar contracts and gather market intelligence.

    Args:
        state: Current workflow state

    Returns:
        Updated state fields
    """
    logger.info(f"[research_opportunity] Starting for: {state.get('opportunity_title', 'Unknown')}")

    naics_codes = state.get('naics_codes', [])
    agency = state.get('agency')

    # Search for similar contracts
    similar_contracts = search_similar_contracts(
        naics_codes=naics_codes,
        agency=agency,
        min_value=state.get('target_value', 0) * 0.5,  # 50% of target
        limit=50
    )

    # Get market intelligence
    market_intelligence = get_market_intelligence(
        naics_codes=naics_codes,
        agency=agency
    )

    # Analyze any known incumbent
    incumbent_info = {}
    if state.get('incumbent_uei') or state.get('incumbent_name'):
        incumbent_info = analyze_incumbent(
            company_uei=state.get('incumbent_uei'),
            company_name=state.get('incumbent_name')
        )

    # Build opportunity analysis
    opportunity_analysis = {
        'opportunity_id': state.get('target_opportunity_id'),
        'similar_contracts_count': len(similar_contracts),
        'market_size': market_intelligence.get('total_market_size', 0),
        'competition_level': market_intelligence.get('competition_level', 'unknown'),
        'analyzed_at': datetime.now().isoformat()
    }

    logger.info(f"[research_opportunity] Found {len(similar_contracts)} similar contracts")

    return {
        'similar_contracts': similar_contracts,
        'market_intelligence': market_intelligence,
        'incumbent_info': incumbent_info,
        'opportunity_analysis': opportunity_analysis,
        'current_node': 'research_opportunity',
        'completed_nodes': state.get('completed_nodes', []) + ['research_opportunity'],
        'updated_at': datetime.now().isoformat(),
        'stats': {
            **state.get('stats', {}),
            'similar_contracts_found': len(similar_contracts)
        }
    }


def gather_contacts(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Contacts phase: Gather contacts from CRM, SAM.gov, and job postings.

    Args:
        state: Current workflow state

    Returns:
        Updated state fields
    """
    logger.info(f"[gather_contacts] Starting contact gathering")

    agency = state.get('agency')
    incumbent_name = state.get('incumbent_info', {}).get('company_name')

    # Search CRM contacts
    contacts_from_crm = search_crm_contacts(
        company=incumbent_name,
        program=state.get('opportunity_title'),
        limit=50
    )

    # Get SAM.gov executive contacts
    contacts_from_sam = []
    for contract in state.get('similar_contracts', [])[:10]:
        sam_contacts = get_sam_entity_contacts(
            uei=contract.get('incumbent_uei'),
            company_name=contract.get('incumbent')
        )
        contacts_from_sam.extend(sam_contacts)

    # Search job postings for contacts
    contacts_from_jobs = []
    if incumbent_name:
        contacts_from_jobs = search_job_posting_contacts(
            company=incumbent_name,
            keywords=state.get('naics_codes', [])[:3],
            limit=20
        )

    # Combine all contacts
    all_contacts = contacts_from_crm + contacts_from_sam + contacts_from_jobs

    # Score and prioritize contacts
    prioritized_contacts = score_contacts(all_contacts)

    logger.info(f"[gather_contacts] Gathered {len(all_contacts)} total contacts")

    return {
        'contacts_gathered': all_contacts,
        'contacts_from_crm': contacts_from_crm,
        'contacts_from_sam': contacts_from_sam,
        'contacts_from_jobs': contacts_from_jobs,
        'prioritized_contacts': prioritized_contacts,
        'current_node': 'gather_contacts',
        'completed_nodes': state.get('completed_nodes', []) + ['gather_contacts'],
        'updated_at': datetime.now().isoformat(),
        'stats': {
            **state.get('stats', {}),
            'contacts_gathered': len(all_contacts),
            'contacts_from_crm': len(contacts_from_crm),
            'contacts_from_sam': len(contacts_from_sam),
            'contacts_from_jobs': len(contacts_from_jobs)
        }
    }


def analyze_competition(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Competition phase: Analyze incumbent and competitive landscape.

    Args:
        state: Current workflow state

    Returns:
        Updated state fields
    """
    logger.info(f"[analyze_competition] Starting competitive analysis")

    naics_codes = state.get('naics_codes', [])
    agency = state.get('agency')

    # Get competitive landscape
    competitive_landscape = get_competitive_landscape(
        naics_codes=naics_codes,
        agency=agency,
        set_aside=state.get('set_aside')
    )

    # Deep dive on incumbent
    incumbent_data = state.get('incumbent_info', {})
    if not incumbent_data and state.get('similar_contracts'):
        # Get incumbent from most recent similar contract
        recent_contract = state['similar_contracts'][0]
        incumbent_data = analyze_incumbent(
            company_name=recent_contract.get('incumbent'),
            contract_id=recent_contract.get('contract_id')
        )

    # Build competitor analysis
    competitor_analysis = {
        'total_competitors': len(competitive_landscape),
        'top_competitors': competitive_landscape[:5],
        'incumbent': incumbent_data,
        'market_concentration': 'moderate',  # Would calculate
        'analyzed_at': datetime.now().isoformat()
    }

    # Calculate win probability
    opportunity = {
        'opportunity_id': state.get('target_opportunity_id'),
        'estimated_value': state.get('target_value'),
        'set_aside': state.get('set_aside'),
        'we_are_incumbent': False  # Would check
    }
    win_probability = calculate_win_probability(
        opportunity=opportunity,
        our_capabilities={},  # Would load from config
        competitive_landscape=competitive_landscape
    )

    logger.info(f"[analyze_competition] Found {len(competitive_landscape)} competitors, Pwin={win_probability:.1%}")

    return {
        'competitor_analysis': competitor_analysis,
        'incumbent_data': incumbent_data,
        'competitive_landscape': competitive_landscape,
        'win_probability': win_probability,
        'current_node': 'analyze_competition',
        'completed_nodes': state.get('completed_nodes', []) + ['analyze_competition'],
        'updated_at': datetime.now().isoformat(),
        'stats': {
            **state.get('stats', {}),
            'competitors_analyzed': len(competitive_landscape),
            'win_probability': win_probability
        }
    }


def generate_strategy(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Strategy phase: Generate BD strategy based on gathered intelligence.

    Args:
        state: Current workflow state

    Returns:
        Updated state fields
    """
    logger.info(f"[generate_strategy] Building BD strategy")

    opportunity = {
        'opportunity_id': state.get('target_opportunity_id'),
        'title': state.get('opportunity_title'),
        'agency': state.get('agency'),
        'value': state.get('target_value'),
        'naics_codes': state.get('naics_codes', [])
    }

    # Build strategy
    bd_strategy = build_bd_strategy(
        opportunity=opportunity,
        market_intelligence=state.get('market_intelligence', {}),
        contacts=state.get('prioritized_contacts', []),
        competitive_analysis=state.get('competitor_analysis', {})
    )

    # Extract key elements
    win_themes = bd_strategy.get('win_themes', [])
    differentiators = bd_strategy.get('differentiators', [])
    teaming_recommendations = bd_strategy.get('teaming_strategy', {}).get('recommended_partners', [])

    logger.info(f"[generate_strategy] Generated strategy with {len(win_themes)} win themes")

    return {
        'bd_strategy': bd_strategy,
        'win_themes': win_themes,
        'differentiators': differentiators,
        'teaming_recommendations': teaming_recommendations,
        'current_node': 'generate_strategy',
        'completed_nodes': state.get('completed_nodes', []) + ['generate_strategy'],
        'updated_at': datetime.now().isoformat()
    }


def request_human_review(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Human review gate: Create review request and pause for approval.

    Args:
        state: Current workflow state

    Returns:
        Updated state fields with review request
    """
    logger.info(f"[request_human_review] Creating review request")

    # Prepare review data
    review_data = {
        'opportunity_id': state.get('target_opportunity_id'),
        'opportunity_title': state.get('opportunity_title'),
        'win_probability': state.get('win_probability'),
        'win_themes': state.get('win_themes', []),
        'differentiators': state.get('differentiators', []),
        'top_contacts': state.get('prioritized_contacts', [])[:5],
        'competitor_count': len(state.get('competitive_landscape', [])),
        'bd_strategy_summary': state.get('bd_strategy', {}).get('executive_summary', '')
    }

    # Create review request
    review_request = create_review_request(
        workflow_id=state.get('workflow_id'),
        review_type=HumanReviewType.STRATEGY_APPROVAL,
        review_data=review_data,
        instructions="Please review the BD strategy and approve, request revisions, or abort."
    )

    logger.info(f"[request_human_review] Created review request: {review_request.request_id}")

    return {
        'awaiting_human_review': True,
        'human_review_type': HumanReviewType.STRATEGY_APPROVAL.value,
        'human_review_request_id': review_request.request_id,
        'status': WorkflowStatus.AWAITING_HUMAN_REVIEW.value,
        'current_node': 'request_human_review',
        'completed_nodes': state.get('completed_nodes', []) + ['request_human_review'],
        'updated_at': datetime.now().isoformat()
    }


def process_human_feedback(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process human review feedback after resume.

    Args:
        state: Current workflow state (should include human_feedback)

    Returns:
        Updated state fields based on feedback
    """
    logger.info(f"[process_human_feedback] Processing feedback")

    feedback = state.get('human_feedback', {})
    decision = feedback.get('decision', 'abort')
    notes = feedback.get('notes', '')

    logger.info(f"[process_human_feedback] Decision: {decision}")

    result = {
        'awaiting_human_review': False,
        'human_review_type': None,
        'human_review_request_id': None,
        'status': WorkflowStatus.IN_PROGRESS.value,
        'current_node': 'process_human_feedback',
        'completed_nodes': state.get('completed_nodes', []) + ['process_human_feedback'],
        'updated_at': datetime.now().isoformat()
    }

    if decision == 'approve':
        result['strategy_approved'] = True
    elif decision == 'revise':
        result['strategy_approved'] = False
        result['strategy_revision_notes'] = notes
    else:  # abort
        result['status'] = WorkflowStatus.ABORTED.value

    return result


def finalize_playbook(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Final phase: Generate the BD playbook document.

    Args:
        state: Current workflow state

    Returns:
        Updated state fields with playbook
    """
    logger.info(f"[finalize_playbook] Generating final playbook")

    # Generate playbook
    output_dir = f"data/playbooks/{state.get('workflow_id', 'unknown')}"
    output_path = f"{output_dir}/bd_playbook.json"

    final_playbook = generate_bd_playbook(
        strategy=state.get('bd_strategy', {}),
        contacts=state.get('prioritized_contacts', []),
        output_path=output_path
    )

    # Create summary
    playbook_summary = f"""
BD Playbook Generated
=====================
Opportunity: {state.get('opportunity_title')}
Agency: {state.get('agency')}
Win Probability: {state.get('win_probability', 0):.1%}
Contacts Identified: {len(state.get('prioritized_contacts', []))}
Competitors Analyzed: {len(state.get('competitive_landscape', []))}
Path: {output_path}
"""

    logger.info(f"[finalize_playbook] Playbook saved to: {output_path}")

    return {
        'final_playbook': final_playbook,
        'playbook_path': output_path,
        'playbook_summary': playbook_summary.strip(),
        'status': WorkflowStatus.COMPLETED.value,
        'completed_at': datetime.now().isoformat(),
        'current_node': 'finalize_playbook',
        'completed_nodes': state.get('completed_nodes', []) + ['finalize_playbook'],
        'updated_at': datetime.now().isoformat()
    }


# ============================================================================
# CONTACT OUTREACH NODES
# ============================================================================

def discover_contacts(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Discovery phase: Find contacts from multiple sources.

    Args:
        state: Current workflow state

    Returns:
        Updated state fields
    """
    logger.info(f"[discover_contacts] Starting discovery for: {state.get('target_company')}")

    target_company = state.get('target_company')
    target_program = state.get('target_program')
    max_contacts = state.get('max_contacts', 20)

    # CRM contacts
    crm_contacts = search_crm_contacts(
        company=target_company,
        program=target_program,
        limit=max_contacts
    )

    # SAM executives
    sam_executives = get_sam_entity_contacts(
        company_name=target_company
    )

    # Job posting contacts
    job_contacts = search_job_posting_contacts(
        company=target_company,
        limit=max_contacts // 2
    )

    all_contacts = crm_contacts + sam_executives + job_contacts

    logger.info(f"[discover_contacts] Discovered {len(all_contacts)} contacts")

    return {
        'discovered_contacts': all_contacts,
        'linkedin_profiles': [],  # Would integrate with LinkedIn
        'sam_executives': sam_executives,
        'job_posting_contacts': job_contacts,
        'current_node': 'discover_contacts',
        'completed_nodes': state.get('completed_nodes', []) + ['discover_contacts'],
        'updated_at': datetime.now().isoformat(),
        'stats': {
            **state.get('stats', {}),
            'contacts_discovered': len(all_contacts)
        }
    }


def score_and_prioritize_contacts(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scoring phase: Score and rank discovered contacts.

    Args:
        state: Current workflow state

    Returns:
        Updated state fields
    """
    logger.info(f"[score_and_prioritize_contacts] Scoring contacts")

    contacts = state.get('discovered_contacts', [])
    scored = score_contacts(contacts)

    # Create rankings
    rankings = [
        {
            'rank': i + 1,
            'name': c.get('name'),
            'title': c.get('title'),
            'score': c.get('score'),
            'company': c.get('company')
        }
        for i, c in enumerate(scored[:state.get('max_contacts', 20)])
    ]

    logger.info(f"[score_and_prioritize_contacts] Scored {len(scored)} contacts")

    return {
        'scored_contacts': scored,
        'contact_rankings': rankings,
        'current_node': 'score_and_prioritize_contacts',
        'completed_nodes': state.get('completed_nodes', []) + ['score_and_prioritize_contacts'],
        'updated_at': datetime.now().isoformat()
    }


def request_contact_approval(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Approval gate: Request human approval for contact list.

    Args:
        state: Current workflow state

    Returns:
        Updated state fields
    """
    logger.info(f"[request_contact_approval] Creating approval request")

    review_data = {
        'target_company': state.get('target_company'),
        'target_program': state.get('target_program'),
        'contact_rankings': state.get('contact_rankings', [])[:10],
        'total_contacts': len(state.get('scored_contacts', []))
    }

    review_request = create_review_request(
        workflow_id=state.get('workflow_id'),
        review_type=HumanReviewType.CONTACT_APPROVAL,
        review_data=review_data,
        instructions="Review the contact list and approve contacts for outreach."
    )

    return {
        'awaiting_human_review': True,
        'human_review_type': HumanReviewType.CONTACT_APPROVAL.value,
        'human_review_request_id': review_request.request_id,
        'status': WorkflowStatus.AWAITING_HUMAN_REVIEW.value,
        'current_node': 'request_contact_approval',
        'completed_nodes': state.get('completed_nodes', []) + ['request_contact_approval'],
        'updated_at': datetime.now().isoformat()
    }


def generate_outreach_materials(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Output phase: Generate outreach materials for approved contacts.

    Args:
        state: Current workflow state

    Returns:
        Updated state fields
    """
    logger.info(f"[generate_outreach_materials] Generating materials")

    approved = state.get('approved_contacts', state.get('scored_contacts', [])[:10])
    outreach_goal = state.get('outreach_goal', 'meeting')

    materials = []
    email_templates = []
    linkedin_messages = []
    call_scripts = []

    for contact in approved:
        # Generate personalized materials
        materials.append({
            'contact_name': contact.get('name'),
            'contact_title': contact.get('title'),
            'outreach_type': outreach_goal,
            'generated_at': datetime.now().isoformat()
        })

        # Email template
        email_templates.append({
            'contact': contact.get('name'),
            'subject': f"Regarding {state.get('target_program', 'opportunity')}",
            'body': f"[Personalized email for {contact.get('name')}]"
        })

    logger.info(f"[generate_outreach_materials] Generated materials for {len(approved)} contacts")

    return {
        'outreach_materials': materials,
        'email_templates': email_templates,
        'linkedin_messages': linkedin_messages,
        'call_scripts': call_scripts,
        'status': WorkflowStatus.COMPLETED.value,
        'completed_at': datetime.now().isoformat(),
        'current_node': 'generate_outreach_materials',
        'completed_nodes': state.get('completed_nodes', []) + ['generate_outreach_materials'],
        'updated_at': datetime.now().isoformat()
    }


# ============================================================================
# RECOMPETE INTELLIGENCE NODES
# ============================================================================

def monitor_contracts(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Monitoring phase: Check status of monitored contracts.

    Args:
        state: Current workflow state

    Returns:
        Updated state fields
    """
    logger.info(f"[monitor_contracts] Checking {len(state.get('monitored_contracts', []))} contracts")

    contract_ids = state.get('monitored_contracts', [])
    statuses = check_contract_status(contract_ids)

    return {
        'contract_statuses': statuses,
        'last_check_date': datetime.now().isoformat(),
        'current_node': 'monitor_contracts',
        'completed_nodes': state.get('completed_nodes', []) + ['monitor_contracts'],
        'updated_at': datetime.now().isoformat(),
        'stats': {
            **state.get('stats', {}),
            'contracts_checked': len(statuses)
        }
    }


def detect_recompete_signals_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detection phase: Identify contracts approaching recompete.

    Args:
        state: Current workflow state

    Returns:
        Updated state fields
    """
    logger.info(f"[detect_recompete_signals] Analyzing for signals")

    statuses = state.get('contract_statuses', [])
    threshold = state.get('alert_threshold_days', 365)

    signals = detect_recompete_signals(statuses, threshold)

    # Categorize signal types
    signal_types = list(set(s.get('signal_type') for s in signals))

    logger.info(f"[detect_recompete_signals] Detected {len(signals)} signals")

    return {
        'recompete_signals': signals,
        'detected_opportunities': [s for s in signals if s.get('priority') == 'high'],
        'signal_types': signal_types,
        'current_node': 'detect_recompete_signals',
        'completed_nodes': state.get('completed_nodes', []) + ['detect_recompete_signals'],
        'updated_at': datetime.now().isoformat(),
        'stats': {
            **state.get('stats', {}),
            'signals_detected': len(signals)
        }
    }


def generate_alert(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Alert phase: Generate alerts for detected signals.

    Args:
        state: Current workflow state

    Returns:
        Updated state fields
    """
    logger.info(f"[generate_alert] Creating alerts")

    signals = state.get('recompete_signals', [])
    alerts = []
    priorities = {}

    for signal in signals:
        alert = {
            'alert_id': str(uuid.uuid4())[:8],
            'contract_id': signal.get('contract_id'),
            'signal_type': signal.get('signal_type'),
            'priority': signal.get('priority'),
            'days_remaining': signal.get('days_remaining'),
            'created_at': datetime.now().isoformat()
        }
        alerts.append(alert)
        priorities[signal.get('contract_id')] = signal.get('priority')

    logger.info(f"[generate_alert] Generated {len(alerts)} alerts")

    return {
        'alerts_generated': alerts,
        'alert_priorities': priorities,
        'current_node': 'generate_alert',
        'completed_nodes': state.get('completed_nodes', []) + ['generate_alert'],
        'updated_at': datetime.now().isoformat()
    }


def prepare_capture(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Capture phase: Prepare capture plans for priority alerts.

    Args:
        state: Current workflow state

    Returns:
        Updated state fields
    """
    logger.info(f"[prepare_capture] Preparing capture plans")

    alerts = state.get('alerts_generated', [])
    decisions = state.get('capture_decisions', {})
    capture_plans = []

    for alert in alerts:
        contract_id = alert.get('contract_id')
        if decisions.get(contract_id, False):
            capture_plans.append({
                'contract_id': contract_id,
                'priority': alert.get('priority'),
                'action_items': [
                    'Identify incumbent team',
                    'Research contract history',
                    'Gather key contacts',
                    'Develop win themes'
                ],
                'created_at': datetime.now().isoformat()
            })

    return {
        'capture_plans': capture_plans,
        'capture_team_assigned': len(capture_plans) > 0,
        'status': WorkflowStatus.COMPLETED.value,
        'completed_at': datetime.now().isoformat(),
        'current_node': 'prepare_capture',
        'completed_nodes': state.get('completed_nodes', []) + ['prepare_capture'],
        'updated_at': datetime.now().isoformat()
    }


# ============================================================================
# WEEKLY PIPELINE NODES
# ============================================================================

def scrape_opportunities_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scraping phase: Gather opportunities from sources.

    Args:
        state: Current workflow state

    Returns:
        Updated state fields
    """
    logger.info(f"[scrape_opportunities] Starting opportunity scrape")

    opportunities = search_opportunities(
        naics_codes=state.get('target_naics', []),
        posted_from=state.get('scrape_from_date'),
        posted_to=state.get('scrape_to_date'),
        limit=100
    )

    return {
        'raw_opportunities': opportunities,
        'scrape_sources': ['sam.gov'],
        'scrape_timestamp': datetime.now().isoformat(),
        'current_node': 'scrape_opportunities',
        'completed_nodes': state.get('completed_nodes', []) + ['scrape_opportunities'],
        'updated_at': datetime.now().isoformat(),
        'stats': {
            **state.get('stats', {}),
            'opportunities_scraped': len(opportunities)
        }
    }


def enrich_opportunities(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrichment phase: Add market and incumbent data.

    Args:
        state: Current workflow state

    Returns:
        Updated state fields
    """
    logger.info(f"[enrich_opportunities] Enriching opportunities")

    raw = state.get('raw_opportunities', [])
    enriched = []
    incumbent_data = {}
    market_data = {}

    for opp in raw:
        # Get market context
        naics = opp.get('naics')
        if naics and naics not in market_data:
            market_data[naics] = get_market_intelligence([naics])

        # Enrich opportunity
        enriched_opp = {
            **opp,
            'market_size': market_data.get(naics, {}).get('total_market_size', 0),
            'competition_level': market_data.get(naics, {}).get('competition_level', 'unknown'),
            'enriched_at': datetime.now().isoformat()
        }
        enriched.append(enriched_opp)

    logger.info(f"[enrich_opportunities] Enriched {len(enriched)} opportunities")

    return {
        'enriched_opportunities': enriched,
        'incumbent_data': incumbent_data,
        'market_data': market_data,
        'current_node': 'enrich_opportunities',
        'completed_nodes': state.get('completed_nodes', []) + ['enrich_opportunities'],
        'updated_at': datetime.now().isoformat()
    }


def score_and_rank(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scoring phase: Score and rank opportunities.

    Args:
        state: Current workflow state

    Returns:
        Updated state fields
    """
    logger.info(f"[score_and_rank] Scoring opportunities")

    enriched = state.get('enriched_opportunities', [])
    scored = [score_opportunity(opp) for opp in enriched]

    # Sort by score
    scored.sort(key=lambda x: x.get('bd_score', 0), reverse=True)

    # Get top opportunities
    top = [opp for opp in scored if opp.get('priority_tier') == 1][:10]

    logger.info(f"[score_and_rank] Scored {len(scored)} opportunities, {len(top)} tier-1")

    return {
        'scored_opportunities': scored,
        'top_opportunities': top,
        'current_node': 'score_and_rank',
        'completed_nodes': state.get('completed_nodes', []) + ['score_and_rank'],
        'updated_at': datetime.now().isoformat(),
        'stats': {
            **state.get('stats', {}),
            'opportunities_scored': len(scored),
            'tier_1_opportunities': len(top)
        }
    }


def generate_report(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Report phase: Generate weekly pipeline report.

    Args:
        state: Current workflow state

    Returns:
        Updated state fields
    """
    logger.info(f"[generate_report] Generating weekly report")

    scored = state.get('scored_opportunities', [])
    top = state.get('top_opportunities', [])

    # Calculate totals
    total_value = sum(opp.get('estimated_value', 0) for opp in scored)

    # Build report
    report = {
        'report_date': datetime.now().isoformat(),
        'period': f"{state.get('date_range_days', 7)} days",
        'summary': {
            'total_opportunities': len(scored),
            'tier_1': len([o for o in scored if o.get('priority_tier') == 1]),
            'tier_2': len([o for o in scored if o.get('priority_tier') == 2]),
            'tier_3': len([o for o in scored if o.get('priority_tier') == 3]),
            'total_value': total_value
        },
        'top_opportunities': top,
        'all_opportunities': scored,
        'methodology': state.get('score_criteria', {})
    }

    # Save report
    output_path = f"data/reports/weekly_pipeline_{datetime.now().strftime('%Y%m%d')}.json"

    report_summary = f"""
Weekly Pipeline Report
======================
Period: {report['period']}
Total Opportunities: {report['summary']['total_opportunities']}
Tier 1 (High Priority): {report['summary']['tier_1']}
Total Value: ${total_value:,.0f}
"""

    logger.info(f"[generate_report] Report generated with {len(scored)} opportunities")

    return {
        'weekly_report': report,
        'report_path': output_path,
        'report_summary': report_summary.strip(),
        'opportunities_count': len(scored),
        'total_value': total_value,
        'status': WorkflowStatus.COMPLETED.value,
        'completed_at': datetime.now().isoformat(),
        'current_node': 'generate_report',
        'completed_nodes': state.get('completed_nodes', []) + ['generate_report'],
        'updated_at': datetime.now().isoformat()
    }


# Export all nodes
__all__ = [
    # BD Proposal nodes
    'research_opportunity',
    'gather_contacts',
    'analyze_competition',
    'generate_strategy',
    'request_human_review',
    'process_human_feedback',
    'finalize_playbook',
    # Contact Outreach nodes
    'discover_contacts',
    'score_and_prioritize_contacts',
    'request_contact_approval',
    'generate_outreach_materials',
    # Recompete nodes
    'monitor_contracts',
    'detect_recompete_signals_node',
    'generate_alert',
    'prepare_capture',
    # Weekly Pipeline nodes
    'scrape_opportunities_node',
    'enrich_opportunities',
    'score_and_rank',
    'generate_report',
]
