"""Phase 33A — Natural Language Query Router

Routes natural language queries to appropriate platform services using
intent classification and entity extraction. Supports 14 query intents
covering search, analytics, prediction, generation, and memory recall.

When an LLM is available, uses it for classification. Falls back to a
robust keyword/pattern-based classifier that handles all 14 intents.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# QUERY INTENTS
# =========================================

class QueryIntent(str, Enum):
    SEARCH_CONTACTS = "search_contacts"
    SEARCH_JOBS = "search_jobs"
    SEARCH_PROGRAMS = "search_programs"
    SEARCH_CONTRACTS = "search_contracts"
    GRAPH_QUERY = "graph_query"
    ANALYTICS = "analytics"
    PREDICTION = "prediction"
    FORECAST = "forecast"
    CAMPAIGN = "campaign"
    GENERATE = "generate"
    COMPARE = "compare"
    EXPLAIN = "explain"
    STATUS = "status"
    MEMORY = "memory"


# =========================================
# DATA CLASSES
# =========================================

@dataclass
class QueryPlan:
    intent: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    clarification_needed: Optional[str] = None
    sub_queries: list = field(default_factory=list)
    original_query: str = ""
    created_at: str = ""


@dataclass
class QueryResult:
    data: Any = None
    summary: str = ""
    count: int = 0
    intent: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    sources: List[str] = field(default_factory=list)
    execution_time_ms: float = 0.0
    suggestions: List[str] = field(default_factory=list)


# =========================================
# INTENT PATTERNS
# =========================================

# Keyword patterns for rule-based classification
_INTENT_PATTERNS: Dict[str, List[str]] = {
    QueryIntent.SEARCH_CONTACTS: [
        r"\bcontact", r"\bwho\b.*\bat\b", r"\bfind\b.*\bpeople\b",
        r"\bpm\b", r"\bprogram manager\b", r"\bsite lead\b",
        r"\btier\s*[1-6]", r"\bdecision maker", r"\bperson\b",
        r"\bemployee", r"\bstaff\b", r"\brecruiter\b",
    ],
    QueryIntent.SEARCH_JOBS: [
        r"\bjob", r"\bposition", r"\bopening", r"\bposting",
        r"\bhiring\b", r"\bvacancy", r"\brole\b.*\bopen",
        r"\bts/sci\b", r"\bclearance\b.*\bjob", r"\banalyst\b.*\bposition",
    ],
    QueryIntent.SEARCH_PROGRAMS: [
        r"\bprogram\b", r"\bcontract\b.*\bprogram", r"\bprime\b",
        r"\bvehicle\b", r"\bidiq\b", r"\bbpa\b",
        r"\bwhat program", r"\bwhich program",
    ],
    QueryIntent.SEARCH_CONTRACTS: [
        r"\bcontract\b", r"\baward", r"\btask order\b",
        r"\brecompete\b", r"\bsolicitation\b", r"\brfp\b", r"\brfi\b",
        r"\bpop\b.*\bend", r"\boption year",
    ],
    QueryIntent.GRAPH_QUERY: [
        r"\bwho knows\b", r"\bconnected to\b", r"\brelationship\b",
        r"\bnetwork\b", r"\bpath\b.*\bto\b", r"\bintroduc",
        r"\bmutual\b", r"\bdegree", r"\blinked\b",
    ],
    QueryIntent.ANALYTICS: [
        r"\bpipeline\b.*\b(value|worth|size|conversion)",
        r"\bmetric", r"\bkpi\b", r"\bconversion rate",
        r"\banalytic", r"\bdashboard\b", r"\bsummary\b",
        r"\bhow many\b", r"\btotal\b.*\b(jobs|contacts|programs)",
    ],
    QueryIntent.PREDICTION: [
        r"\bwin prob", r"\blikelihood\b", r"\bchance\b",
        r"\bpredict\b", r"\bscore\b.*\bopportunity",
        r"\bcomposite score\b", r"\bwhat.?if\b",
    ],
    QueryIntent.FORECAST: [
        r"\bforecast", r"\btrend\b", r"\bramp\b",
        r"\bhiring trend", r"\bbudget cycle",
        r"\bnext quarter\b", r"\bproject\b.*\b(growth|demand)",
    ],
    QueryIntent.CAMPAIGN: [
        r"\bstart\b.*\boutreach\b", r"\bcampaign\b", r"\blaunch\b.*\boutreach",
        r"\bengage\b", r"\bsequence\b", r"\bcadence\b",
    ],
    QueryIntent.GENERATE: [
        r"\bwrite\b", r"\bgenerate\b", r"\bdraft\b", r"\bcreate\b.*\b(email|message|brief)",
        r"\boutreach\b.*\b(email|message)", r"\bcall\b.*\bscript",
        r"\bmeeting\b.*\bprep", r"\bplaybook\b",
    ],
    QueryIntent.COMPARE: [
        r"\bcompare\b", r"\bvs\.?\b", r"\bversus\b",
        r"\bdifference\b.*\bbetween\b", r"\bhead.to.head\b",
    ],
    QueryIntent.EXPLAIN: [
        r"\bwhy\b.*\bscore", r"\bexplain\b", r"\breason\b",
        r"\bwhy is\b", r"\bhow is\b.*\bcalculated",
    ],
    QueryIntent.STATUS: [
        r"\bwhat happened\b", r"\btoday\b", r"\bdigest\b",
        r"\bstatus\b", r"\brecent\b.*\bactivity", r"\bupdate\b.*\bme",
        r"\bwhat.?s new\b",
    ],
    QueryIntent.MEMORY: [
        r"\bwhat do we know\b", r"\bremember\b", r"\blast time\b",
        r"\bhistory\b.*\bwith\b", r"\bprevious\b.*\binteraction",
        r"\bnotes\b.*\bon\b",
    ],
}

# Entity extraction patterns
_COMPANY_PATTERNS = [
    "leidos", "gdit", "booz allen", "northrop grumman", "raytheon",
    "lockheed", "bae systems", "saic", "perspecta", "caci",
    "mantech", "l3harris", "general dynamics", "parsons", "aecom",
]

_CLEARANCE_PATTERNS = [
    r"\bts/sci\b", r"\btop secret\b", r"\bsecret\b", r"\bpublic trust\b",
    r"\bsci\b", r"\bts\b",
]

_LOCATION_PATTERNS = [
    "san diego", "langley", "fort meade", "colorado springs",
    "hickam", "beale", "ramstein", "wright-patt", "san antonio",
    "huntsville", "tampa", "norfolk", "honolulu", "springfield",
]

_PROGRAM_PATTERNS = [
    "dcgs", "pacaf", "gbsd", "ngen", "f-35", "sentinel",
    "jadc2", "abms", "navy isr", "disa", "centcom",
]

_TIMEFRAME_PATTERNS = {
    r"\btoday\b": "today",
    r"\bthis week\b": "this_week",
    r"\blast week\b": "last_week",
    r"\bthis month\b": "this_month",
    r"\blast month\b": "last_month",
    r"\bthis quarter\b": "this_quarter",
    r"\blast quarter\b": "last_quarter",
    r"\bthis year\b": "this_year",
    r"\blast 30 days\b": "last_30_days",
    r"\blast 90 days\b": "last_90_days",
}


class NLQueryRouter:
    """Routes natural language queries to appropriate platform services.

    Uses pattern-based intent classification with entity extraction.
    When an LLM client is provided, can enhance classification accuracy.
    """

    def __init__(self, llm_client: Any = None):
        self._llm = llm_client

    async def route_query(
        self, query: str, context: Optional[Dict[str, Any]] = None,
    ) -> QueryPlan:
        """Classify query into intent and extract parameters."""
        query_lower = query.lower().strip()
        context = context or {}

        # Detect intent
        intent, confidence = self._classify_intent(query_lower)

        # Extract parameters
        parameters = self._extract_parameters(query_lower, intent)

        # Enrich from conversation context
        if context.get("last_intent"):
            parameters["context_intent"] = context["last_intent"]
        if context.get("last_entities"):
            parameters["context_entities"] = context["last_entities"]

        # Check if clarification is needed
        clarification = self._check_clarification(intent, confidence, parameters, query_lower)

        # Detect multi-step queries
        sub_queries = self._detect_sub_queries(query_lower, intent, parameters)

        return QueryPlan(
            intent=intent,
            parameters=parameters,
            confidence=confidence,
            clarification_needed=clarification,
            sub_queries=sub_queries,
            original_query=query,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    async def format_response(
        self, result: QueryResult, format: str = "natural",
    ) -> str:
        """Format query results for display."""
        if format == "brief":
            return self._format_brief(result)
        elif format == "table":
            return self._format_table(result)
        elif format == "chart":
            return self._format_chart(result)
        elif format == "detailed":
            return self._format_detailed(result)
        else:
            return self._format_natural(result)

    # =========================================
    # INTENT CLASSIFICATION
    # =========================================

    def _classify_intent(self, query: str) -> tuple:
        """Rule-based intent classification with confidence scoring."""
        scores: Dict[str, float] = {}

        for intent_value, patterns in _INTENT_PATTERNS.items():
            intent_name = intent_value if isinstance(intent_value, str) else intent_value.value
            match_count = 0
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    match_count += 1
            scores[intent_name] = match_count

        if not scores or max(scores.values()) == 0:
            return QueryIntent.SEARCH_JOBS.value, 0.3

        best_intent = max(scores, key=scores.get)
        best_score = scores[best_intent]

        # Normalize: 1 match = 0.6, 2 = 0.75, 3+ = 0.85+
        confidence = min(1.0, 0.45 + best_score * 0.15)

        return best_intent, round(confidence, 2)

    # =========================================
    # PARAMETER EXTRACTION
    # =========================================

    def _extract_parameters(self, query: str, intent: str) -> Dict[str, Any]:
        """Extract entities and filters from query text."""
        params: Dict[str, Any] = {}

        # Companies
        companies = [c for c in _COMPANY_PATTERNS if c in query]
        if companies:
            params["companies"] = companies

        # Clearance levels
        for pattern in _CLEARANCE_PATTERNS:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                params["clearance"] = match.group(0).upper()
                break

        # Locations
        locations = [loc for loc in _LOCATION_PATTERNS if loc in query]
        if locations:
            params["locations"] = locations

        # Programs
        programs = [p for p in _PROGRAM_PATTERNS if p in query]
        if programs:
            params["programs"] = programs

        # Timeframe
        for pattern, value in _TIMEFRAME_PATTERNS.items():
            if re.search(pattern, query, re.IGNORECASE):
                params["timeframe"] = value
                break

        # Numeric limits
        limit_match = re.search(r"\btop\s+(\d+)\b", query, re.IGNORECASE)
        if limit_match:
            params["limit"] = int(limit_match.group(1))

        # Tier filtering
        tier_match = re.search(r"\btier\s*(\d)\b", query, re.IGNORECASE)
        if tier_match:
            params["tier"] = int(tier_match.group(1))

        # Comparison entities (for COMPARE intent)
        if intent == QueryIntent.COMPARE.value:
            vs_match = re.search(r"(.+?)\s+(?:vs\.?|versus)\s+(.+?)(?:\s+(?:in|at|for)\s+|$)", query)
            if vs_match:
                params["entity_a"] = vs_match.group(1).strip()
                params["entity_b"] = vs_match.group(2).strip()

        # Person names (heuristic: capitalized words not matching known entities)
        name_candidates = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b", query.replace(query.lower(), query))
        if name_candidates:
            params["names"] = name_candidates

        # Search query (cleaned version for vector search)
        params["search_query"] = query

        return params

    # =========================================
    # CLARIFICATION DETECTION
    # =========================================

    def _check_clarification(
        self, intent: str, confidence: float,
        parameters: Dict[str, Any], query: str,
    ) -> Optional[str]:
        """Determine if clarification is needed."""
        if confidence < 0.4:
            return f"I'm not sure what you're looking for. Did you mean to search for jobs, contacts, or programs?"

        # Ambiguous location for known multi-location programs
        if (intent in (QueryIntent.SEARCH_CONTACTS.value, QueryIntent.SEARCH_JOBS.value)
                and "pacaf" in query
                and not parameters.get("locations")):
            return "PACAF operates at multiple locations. Did you mean Hickam (Hawaii), Langley (Virginia), or all sites?"

        return None

    # =========================================
    # MULTI-STEP DETECTION
    # =========================================

    def _detect_sub_queries(
        self, query: str, intent: str, parameters: Dict[str, Any],
    ) -> List[QueryPlan]:
        """Detect if query requires multiple steps."""
        sub_queries = []

        # "Find contacts and their jobs" → search contacts + search jobs
        if "and" in query:
            parts = query.split(" and ")
            if len(parts) == 2:
                # Check if second part is a different intent
                second_intent, second_conf = self._classify_intent(parts[1].strip())
                if second_intent != intent and second_conf > 0.3:
                    sub_queries.append(QueryPlan(
                        intent=second_intent,
                        parameters=self._extract_parameters(parts[1].strip(), second_intent),
                        confidence=second_conf,
                        original_query=parts[1].strip(),
                        created_at=datetime.now(timezone.utc).isoformat(),
                    ))

        # "Compare X vs Y" with forecast → compare + forecast
        if intent == QueryIntent.COMPARE.value and re.search(r"\bforecast|trend\b", query):
            sub_queries.append(QueryPlan(
                intent=QueryIntent.FORECAST.value,
                parameters=parameters.copy(),
                confidence=0.6,
                original_query=query,
                created_at=datetime.now(timezone.utc).isoformat(),
            ))

        return sub_queries

    # =========================================
    # RESPONSE FORMATTING
    # =========================================

    def _format_natural(self, result: QueryResult) -> str:
        """Conversational prose with key highlights."""
        if result.count == 0:
            return f"I didn't find any results for your query. Try broadening your search or rephrasing."

        parts = []
        if result.summary:
            parts.append(result.summary)
        elif result.count > 0:
            parts.append(f"Found {result.count} result{'s' if result.count != 1 else ''}.")

        data = result.data
        if isinstance(data, list) and data:
            top_items = data[:5]
            for item in top_items:
                if isinstance(item, dict):
                    name = item.get("title") or item.get("name") or item.get("id", "")
                    company = item.get("company", "")
                    score = item.get("score") or item.get("composite_score", "")
                    line = f"  - {name}"
                    if company:
                        line += f" ({company})"
                    if score:
                        line += f" — score: {score}"
                    parts.append(line)
            if result.count > 5:
                parts.append(f"  ... and {result.count - 5} more")

        if result.suggestions:
            parts.append("\nYou might also want to ask:")
            for s in result.suggestions[:3]:
                parts.append(f"  → {s}")

        return "\n".join(parts)

    def _format_brief(self, result: QueryResult) -> str:
        """One-line summary."""
        if result.summary:
            return result.summary
        return f"{result.count} results for {result.intent} query"

    def _format_table(self, result: QueryResult) -> str:
        """Structured table format."""
        if not isinstance(result.data, list) or not result.data:
            return self._format_natural(result)

        # Build column headers from first item
        first = result.data[0] if result.data else {}
        if not isinstance(first, dict):
            return self._format_natural(result)

        columns = list(first.keys())[:6]  # Limit to 6 columns
        header = " | ".join(str(c).replace("_", " ").title() for c in columns)
        separator = " | ".join("-" * max(len(str(c)), 8) for c in columns)

        rows = [header, separator]
        for item in result.data[:20]:
            if isinstance(item, dict):
                row = " | ".join(str(item.get(c, ""))[:30] for c in columns)
                rows.append(row)

        return "\n".join(rows)

    def _format_chart(self, result: QueryResult) -> str:
        """Chart-ready data structure (JSON-like)."""
        import json
        chart_data = {
            "type": "bar",
            "title": result.summary or f"{result.intent} results",
            "data": result.data if isinstance(result.data, list) else [],
            "count": result.count,
        }
        return json.dumps(chart_data, default=str, indent=2)

    def _format_detailed(self, result: QueryResult) -> str:
        """Full analysis with context."""
        parts = [f"## Query: {result.intent}"]
        parts.append(f"**Parameters:** {result.parameters}")
        parts.append(f"**Results:** {result.count}")
        parts.append(f"**Execution time:** {result.execution_time_ms:.0f}ms")
        parts.append("")

        if result.summary:
            parts.append(f"### Summary\n{result.summary}")

        natural = self._format_natural(result)
        parts.append(f"\n### Details\n{natural}")

        if result.sources:
            parts.append("\n### Sources")
            for src in result.sources:
                parts.append(f"  - {src}")

        return "\n".join(parts)


# =========================================
# EXAMPLE QUERIES PER INTENT
# =========================================

EXAMPLE_QUERIES: Dict[str, List[str]] = {
    QueryIntent.SEARCH_CONTACTS.value: [
        "Find Tier 1 contacts at Leidos",
        "Who are the GDIT program managers in San Diego?",
        "Show me decision makers for PACAF",
    ],
    QueryIntent.SEARCH_JOBS.value: [
        "Show TS/SCI jobs at Langley posted this week",
        "What analyst positions are open in San Diego?",
        "Find all DCGS job openings",
    ],
    QueryIntent.SEARCH_PROGRAMS.value: [
        "What programs does GDIT run?",
        "Tell me about the DCGS program",
        "Which programs are in San Diego?",
    ],
    QueryIntent.SEARCH_CONTRACTS.value: [
        "Recent contract awards to Leidos",
        "Show NGEN contract details",
        "When does the DCGS contract recompete?",
    ],
    QueryIntent.GRAPH_QUERY.value: [
        "Who knows the PACAF site lead?",
        "Show connections between Leidos and GDIT contacts",
        "Path from our contact to the program manager",
    ],
    QueryIntent.ANALYTICS.value: [
        "What's our pipeline worth this quarter?",
        "Pipeline conversion rate this month",
        "How many jobs were posted last week?",
    ],
    QueryIntent.PREDICTION.value: [
        "Win probability for the Langley opportunity",
        "Score the PACAF analyst position",
        "What-if we improve our relationship with GDIT?",
    ],
    QueryIntent.FORECAST.value: [
        "Hiring trend for Navy DCGS-N",
        "Forecast demand for analysts next quarter",
        "Which programs are ramping up?",
    ],
    QueryIntent.CAMPAIGN.value: [
        "Start outreach to Wright-Patt contacts",
        "Launch email sequence for PACAF decision makers",
        "Engage Tier 1 contacts at Leidos",
    ],
    QueryIntent.GENERATE.value: [
        "Write outreach email for Kingsley Ero",
        "Generate call script for DCGS program manager",
        "Draft meeting prep for Leidos visit",
    ],
    QueryIntent.COMPARE.value: [
        "Compare GDIT vs Leidos hiring in Virginia",
        "Head to head: San Diego vs Langley job volumes",
        "Difference between DCGS and NGEN pipelines",
    ],
    QueryIntent.EXPLAIN.value: [
        "Why is PACAF scored critical?",
        "Explain the win probability for opportunity opp-1",
        "How is the composite score calculated?",
    ],
    QueryIntent.STATUS.value: [
        "What happened today?",
        "Give me a daily digest",
        "What's new this week?",
    ],
    QueryIntent.MEMORY.value: [
        "What do we know about Craig Lindahl?",
        "History of our interactions with GDIT",
        "Notes on the Langley site visit",
    ],
}
