"""Entity name mapping and category definitions.

Extracted from gen_v3_explorer.py -- canonical NAME_MAP that maps
(project_id:entity_name) -> unified canonical name, plus 7 category definitions.
"""

from collections import OrderedDict

# Maps (project_id:json_entity_name) -> canonical name.  None = skip entity.
NAME_MAP = {
    # BD-Automation-Engine
    'BD_ENGINE:CONTACT': 'Contact',
    'BD_ENGINE:PROGRAM': 'Program',
    'BD_ENGINE:JOB': 'Job',
    'BD_ENGINE:PRIME_CONTRACTOR': 'Prime',
    'BD_ENGINE:PLACEMENT': 'Placement',
    'BD_ENGINE:ACTIVITY': 'Activity',
    'BD_ENGINE:DOCUMENT': 'Document',
    'BD_ENGINE:PAST_PERFORMANCE': 'Past Performance',
    'BD_ENGINE:INTELLIGENCE_REPORT': 'Intelligence Report',
    'BD_ENGINE:BULLHORN_NOTE': 'Bullhorn Note',
    'BD_ENGINE:LOCATION': 'Location',
    'BD_ENGINE:FEDERAL_CONTRACT': 'Contract',
    'BD_ENGINE:CONTRACT_OPPORTUNITY': 'Opportunity',
    'BD_ENGINE:MEMORY': 'Memory',
    'BD_ENGINE:INSIGHT': 'Insight',
    'BD_ENGINE:WORKFLOW_RUN': 'Workflow Run',
    'BD_ENGINE:WEEKLY_REPORT': 'Weekly Report',
    'BD_ENGINE:NOTIFICATION': 'Notification',
    'BD_ENGINE:ALERT': 'Notification',
    'BD_ENGINE:CONTRACT_WATCH': 'Contract Watch',
    'BD_ENGINE:RECOMPETE_PREDICTION': 'Recompete Prediction',
    'BD_ENGINE:PROPOSAL_ARTIFACT': 'Proposal Artifact',
    'BD_ENGINE:RELATIONSHIP_SCORE': 'Relationship Score',
    'BD_ENGINE:WIN_PROBABILITY': 'Win Probability',
    'BD_ENGINE:REVENUE_PLACEMENT': 'Revenue Placement',
    'BD_ENGINE:CONTACT_CLAIM': 'Contact Claim',
    'BD_ENGINE:HIRING_FORECAST': 'Hiring Forecast',
    # Skip internal/meta
    'BD_ENGINE:GRAPH_ENTITY': None,
    'BD_ENGINE:GRAPH_RELATIONSHIP': None,
    'BD_ENGINE:SOURCE_FILE': None,
    'BD_ENGINE:DATA_QUALITY_LOG': None,
    'BD_ENGINE:PROCESSING_STATS': None,
    'BD_ENGINE:SWARM_TASK': None,
    'BD_ENGINE:STREAMING_EVENT': None,
    'BD_ENGINE:FILE_NODE': None,
    'BD_ENGINE:PROCESS_NODE': None,
    'BD_ENGINE:INTERACTION': None,
    'BD_ENGINE:CALL_BRIEFING': None,
    'BD_ENGINE:TRANSCRIPT_INTEL': None,
    'BD_ENGINE:STRATEGIC_PATTERN': None,

    # data-scraper
    'DATA_SCRAPER:ScrapedJob': 'Scraped Job',
    'DATA_SCRAPER:EnrichedJobCSV': 'Job',
    'DATA_SCRAPER:Program': 'Program',
    'DATA_SCRAPER:Contact': 'Contact',
    'DATA_SCRAPER:BullhornActivity': 'Activity',
    'DATA_SCRAPER:CompetitiveSignal': 'Competitive Signal',
    'DATA_SCRAPER:IntelReport': 'Intelligence Report',
    'DATA_SCRAPER:BullhornJob': 'Job',
    'DATA_SCRAPER:FederalContract': 'Contract',
    'DATA_SCRAPER:FPDSContract': 'FPDS Contract',
    'DATA_SCRAPER:Subaward': 'Subaward',
    'DATA_SCRAPER:USASpendingContractDelta': 'Transaction',
    'DATA_SCRAPER:TaskOrder': 'Task Order',
    'DATA_SCRAPER:Company': 'Prime',
    'DATA_SCRAPER:VendorProfile': 'Vendor',
    'DATA_SCRAPER:SAMOpportunity': 'Opportunity',
    'DATA_SCRAPER:BDTarget': 'BD Target',
    'DATA_SCRAPER:PipelineRun': 'Pipeline Run',
    'DATA_SCRAPER:KnowledgeFile': 'Knowledge File',
    'DATA_SCRAPER:DataQualityReport': None,
    'DATA_SCRAPER:ActorConfig': None,
    'DATA_SCRAPER:Tag': None,
    'DATA_SCRAPER:APIConfig': None,

    # N8N-Builder
    'N8N_BUILDER:Agency': 'Agency',
    'N8N_BUILDER:Contractor': 'Prime',
    'N8N_BUILDER:FederalProgram': 'Program',
    'N8N_BUILDER:CanonicalContract': 'Canonical Contract',
    'N8N_BUILDER:CanonicalEntity': 'Canonical Entity',
    'N8N_BUILDER:Contract': 'Contract',
    'N8N_BUILDER:Subcontractor': 'Subcontractor',
    'N8N_BUILDER:Subaward': 'Subaward',
    'N8N_BUILDER:EnrichmentRun': 'Enrichment Run',
    'N8N_BUILDER:Opportunity': 'Opportunity',
    'N8N_BUILDER:Forecast': 'Forecast',
    'N8N_BUILDER:IDV': 'IDV',
    'N8N_BUILDER:Vehicle': 'Contract Vehicle',
    'N8N_BUILDER:Contact': 'Contact',
    'N8N_BUILDER:Job': 'Job',
    'N8N_BUILDER:Activity': 'Activity',
    'N8N_BUILDER:FederalProgramIntelligence': 'Federal Program Intel',
    'N8N_BUILDER:BDProposalState': 'BD Proposal State',
    'N8N_BUILDER:ContactOutreachState': 'Outreach State',
    'N8N_BUILDER:DiscoveredProgram': 'Discovered Program',
    'N8N_BUILDER:WorkflowExecution': 'Workflow Execution',
    'N8N_BUILDER:IntelligenceReport': 'Intelligence Report',
    'N8N_BUILDER:BullhornNote': 'Bullhorn Note',
    'N8N_BUILDER:Document': 'Document',
    'N8N_BUILDER:BDMemory': 'Memory',
    'N8N_BUILDER:OutreachSequence': 'Outreach Sequence',
    'N8N_BUILDER:Campaign': 'Campaign',
    'N8N_BUILDER:NAICSCode': 'NAICS Code',
    'N8N_BUILDER:PSCCode': 'PSC Code',
    'N8N_BUILDER:LocationRecord': 'Location',
    'N8N_BUILDER:SearchFilters': None,
    'N8N_BUILDER:StarChart': None,
}

# 7 categories with colors and member entity lists
CATEGORY_DEFS = OrderedDict([
    ('Federal Awards', {
        'color': '#3b82f6',
        'nodes': ['Contract', 'Subaward', 'Task Order', 'OTA', 'Transaction',
                  'Federal Account', 'Canonical Contract', 'FPDS Contract']
    }),
    ('Procurement', {
        'color': '#10b981',
        'nodes': ['Opportunity', 'Forecast', 'Notice', 'IDV', 'Contract Vehicle',
                  'Grant', 'Recompete', 'Recompete Prediction', 'Competitive Signal',
                  'Discovered Program']
    }),
    ('Organizations', {
        'color': '#f97316',
        'nodes': ['Prime', 'Vendor', 'Agency', 'Subcontractor', 'Canonical Entity']
    }),
    ('BD Intelligence', {
        'color': '#8b5cf6',
        'nodes': ['Contact', 'Job', 'Activity', 'Program', 'BD Target', 'Competitor',
                  'Note', 'Placement', 'Bullhorn Note', 'Document', 'Scraped Job',
                  'Federal Program Intel', 'Intelligence Report', 'Relationship Score',
                  'Win Probability', 'Hiring Forecast']
    }),
    ('Reference', {
        'color': '#64748b',
        'nodes': ['NAICS Code', 'PSC Code', 'Location', 'Technology', 'Certification',
                  'Knowledge File']
    }),
    ('BD Operations', {
        'color': '#f43f5e',
        'nodes': ['Campaign', 'Outreach Sequence', 'Outreach State',
                  'BD Proposal State', 'Proposal Artifact', 'Revenue Placement',
                  'Contact Claim', 'Contract Watch', 'Weekly Report']
    }),
    ('Meta/Ops', {
        'color': '#06b6d4',
        'nodes': ['Author', 'Scrape Run', 'Fiscal Phase', 'Past Performance',
                  'Capability', 'Enrichment Run', 'Memory', 'Insight',
                  'Workflow Run', 'Workflow Execution', 'Notification',
                  'Pipeline Run']
    }),
])

# Project ID -> display label
PROJECT_LABELS = {
    'BD_ENGINE': 'BD-Engine',
    'DATA_SCRAPER': 'Data-Scraper',
    'N8N_BUILDER': 'N8N-Builder',
    'V2_CURATED': 'V2-Curated',
}


def get_canonical_name(project_id: str, entity_name: str) -> str | None:
    """Get canonical entity name for a (project, entity) pair.

    Returns None if the entity should be skipped.
    Falls back to title-cased name for unmapped entities.
    """
    key = f'{project_id}:{entity_name}'
    if key in NAME_MAP:
        return NAME_MAP[key]
    return entity_name.replace('_', ' ').title()


def assign_category(entity_name: str) -> str:
    """Find which category an entity belongs to. Defaults to 'Meta/Ops'."""
    for cat_name, cat_data in CATEGORY_DEFS.items():
        if entity_name in cat_data['nodes']:
            return cat_name
    return 'Meta/Ops'
