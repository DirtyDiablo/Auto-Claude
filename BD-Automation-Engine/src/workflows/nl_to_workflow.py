"""Phase 49A — Natural Language to Workflow Engine.

Converts natural language instructions into executable workflow definitions.
Parses intent, extracts parameters, validates against available workflows,
and executes or creates custom workflows on the fly.
"""

from __future__ import annotations

import hashlib
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# =========================================
# DATA MODELS
# =========================================


class IntentType(str, Enum):
    RUN_WORKFLOW = "run_workflow"
    ENRICH_CONTACT = "enrich_contact"
    SCRAPE_JOBS = "scrape_jobs"
    SCORE_PIPELINE = "score_pipeline"
    GENERATE_REPORT = "generate_report"
    ANALYZE_COMPETITION = "analyze_competition"
    FIND_CONTACTS = "find_contacts"
    CREATE_CAMPAIGN = "create_campaign"
    SCHEDULE_CYCLE = "schedule_cycle"
    UNKNOWN = "unknown"


class ValidationStatus(str, Enum):
    VALID = "valid"
    NEEDS_PARAMS = "needs_params"
    AMBIGUOUS = "ambiguous"
    INVALID = "invalid"


@dataclass
class ParsedIntent:
    """Result of NL intent parsing."""

    intent: IntentType
    confidence: float  # 0.0 – 1.0
    raw_text: str
    extracted_params: Dict[str, Any] = field(default_factory=dict)
    matched_workflow_id: Optional[str] = None
    entities: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent.value,
            "confidence": round(self.confidence, 3),
            "raw_text": self.raw_text,
            "extracted_params": self.extracted_params,
            "matched_workflow_id": self.matched_workflow_id,
            "entities": self.entities,
            "suggestions": self.suggestions,
        }


@dataclass
class ValidationResult:
    """Result of workflow validation before execution."""

    status: ValidationStatus
    workflow_id: Optional[str] = None
    missing_params: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "workflow_id": self.workflow_id,
            "missing_params": self.missing_params,
            "warnings": self.warnings,
            "alternatives": self.alternatives,
        }


@dataclass
class NLExecutionResult:
    """Result of NL-triggered workflow execution."""

    execution_id: str
    intent: ParsedIntent
    validation: ValidationResult
    workflow_run_id: Optional[str] = None
    status: str = "pending"
    created_at: str = ""
    output: Any = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "intent": self.intent.to_dict(),
            "validation": self.validation.to_dict(),
            "workflow_run_id": self.workflow_run_id,
            "status": self.status,
            "created_at": self.created_at,
            "output": self.output,
        }


# =========================================
# INTENT PATTERNS
# =========================================

_INTENT_PATTERNS: List[Tuple[str, IntentType, float]] = [
    # Campaign
    (
        r"(run|start|launch|execute)\s+(full\s+)?bd\s+campaign",
        IntentType.CREATE_CAMPAIGN,
        0.95,
    ),
    (r"(create|build|set\s+up)\s+(a\s+)?campaign", IntentType.CREATE_CAMPAIGN, 0.90),
    (r"campaign\s+for\s+\w+", IntentType.CREATE_CAMPAIGN, 0.85),
    # Contact enrichment
    (r"enrich\s+(contact|person|candidate)", IntentType.ENRICH_CONTACT, 0.95),
    (r"(update|refresh)\s+contact", IntentType.ENRICH_CONTACT, 0.85),
    (r"classify\s+(tier|contact)", IntentType.ENRICH_CONTACT, 0.80),
    # Scraping
    (r"scrape\s+(jobs?|postings?)", IntentType.SCRAPE_JOBS, 0.95),
    (r"(run|start)\s+scraper", IntentType.SCRAPE_JOBS, 0.90),
    (r"pull\s+(new\s+)?jobs", IntentType.SCRAPE_JOBS, 0.85),
    # Scoring
    (r"(score|rescore)\s+(pipeline|opportunities)", IntentType.SCORE_PIPELINE, 0.95),
    (r"(update|refresh)\s+scores", IntentType.SCORE_PIPELINE, 0.90),
    (r"prioritize\s+pipeline", IntentType.SCORE_PIPELINE, 0.85),
    # Reports
    (r"generate\s+(weekly\s+)?report", IntentType.GENERATE_REPORT, 0.95),
    (r"(create|compile)\s+intel\s+report", IntentType.GENERATE_REPORT, 0.90),
    (r"weekly\s+intel", IntentType.GENERATE_REPORT, 0.85),
    # Competition
    (r"(analyze|check)\s+competition", IntentType.ANALYZE_COMPETITION, 0.95),
    (r"competitive\s+(density|analysis|intel)", IntentType.ANALYZE_COMPETITION, 0.90),
    (r"competitor\s+(landscape|presence)", IntentType.ANALYZE_COMPETITION, 0.85),
    # Find contacts
    (r"find\s+(contacts?|people)", IntentType.FIND_CONTACTS, 0.90),
    (r"(search|look\s+up)\s+contacts?", IntentType.FIND_CONTACTS, 0.85),
    (r"who\s+(works|is)\s+(at|on|in)", IntentType.FIND_CONTACTS, 0.80),
    # Schedule cycle
    (r"(schedule|set\s+up)\s+(weekly\s+)?cycle", IntentType.SCHEDULE_CYCLE, 0.90),
    (r"(run|start)\s+weekly\s+intel\s+cycle", IntentType.SCHEDULE_CYCLE, 0.95),
    # Run a specific workflow
    (r"run\s+workflow\s+\w+", IntentType.RUN_WORKFLOW, 0.90),
    (r"execute\s+workflow", IntentType.RUN_WORKFLOW, 0.85),
]

_INTENT_TO_WORKFLOW: Dict[IntentType, str] = {
    IntentType.CREATE_CAMPAIGN: "wf_full_bd_campaign",
    IntentType.ENRICH_CONTACT: "wf_contact_enrichment",
    IntentType.SCHEDULE_CYCLE: "wf_weekly_intel_cycle",
    IntentType.SCRAPE_JOBS: "wf_weekly_intel_cycle",  # scraping is part of weekly cycle
    IntentType.SCORE_PIPELINE: "wf_weekly_intel_cycle",
    IntentType.GENERATE_REPORT: "wf_weekly_intel_cycle",
    IntentType.ANALYZE_COMPETITION: "wf_opportunity_response",
    IntentType.FIND_CONTACTS: "wf_contact_enrichment",
    IntentType.RUN_WORKFLOW: None,  # determined by params
}

# Entity extraction patterns
_ENTITY_PATTERNS = [
    (r"\b(DCGS[-\s]?[A-Z]?)\b", "program"),
    (r"\b(JADC2|GBSD|MQ-25|F-35|ABMS|TITAN|IBCS)\b", "program"),
    (
        r"\b(Leidos|Northrop\s*Grumman|Raytheon|GDIT|BAE|L3Harris|Booz\s*Allen)\b",
        "company",
    ),
    (r"\b(NCR|southeast|west|midwest|southwest)\b", "region"),
    (r"\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b", "person_name"),
]


# =========================================
# NL-TO-WORKFLOW ENGINE
# =========================================


class NLToWorkflowEngine:
    """Converts natural language instructions into executable workflows.

    Pipeline: parse intent → extract entities → match workflow → validate → execute.
    """

    def __init__(self):
        self._executions: Dict[str, NLExecutionResult] = {}
        self._exec_counter = 0
        self._available_workflow_ids = [
            "wf_full_bd_campaign",
            "wf_contact_enrichment",
            "wf_weekly_intel_cycle",
            "wf_opportunity_response",
        ]
        logger.info("NLToWorkflowEngine initialized")

    # ----- intent parsing -----

    def parse_intent(self, text: str) -> ParsedIntent:
        """Parse natural language text into a structured intent."""
        if not text or not text.strip():
            return ParsedIntent(
                intent=IntentType.UNKNOWN,
                confidence=0.0,
                raw_text=text or "",
            )

        lower = text.lower().strip()
        best_intent = IntentType.UNKNOWN
        best_confidence = 0.0

        for pattern, intent, base_conf in _INTENT_PATTERNS:
            match = re.search(pattern, lower)
            if match:
                if base_conf > best_confidence:
                    best_intent = intent
                    best_confidence = base_conf

        # Extract entities
        entities = self._extract_entities(text)

        # Extract params
        params = self._extract_params(text, best_intent)

        # Map to workflow
        workflow_id = _INTENT_TO_WORKFLOW.get(best_intent)
        if best_intent == IntentType.RUN_WORKFLOW:
            # Try to extract workflow ID from text
            wf_match = re.search(r"workflow\s+(wf_\w+)", lower)
            if wf_match:
                workflow_id = wf_match.group(1)

        # Suggestions for ambiguous intents
        suggestions = []
        if best_confidence < 0.5:
            suggestions = [
                "Try: 'Run full BD campaign for DCGS-A'",
                "Try: 'Enrich contact John Smith'",
                "Try: 'Scrape jobs for defense programs'",
                "Try: 'Generate weekly intel report'",
            ]

        return ParsedIntent(
            intent=best_intent,
            confidence=best_confidence,
            raw_text=text,
            extracted_params=params,
            matched_workflow_id=workflow_id,
            entities=entities,
            suggestions=suggestions,
        )

    def _extract_entities(self, text: str) -> List[str]:
        """Extract named entities from text."""
        entities = []
        for pattern, etype in _ENTITY_PATTERNS:
            for match in re.finditer(pattern, text):
                entity_str = f"{etype}:{match.group(1)}"
                if entity_str not in entities:
                    entities.append(entity_str)
        return entities

    def _extract_params(self, text: str, intent: IntentType) -> Dict[str, Any]:
        """Extract workflow parameters from text based on intent."""
        params: Dict[str, Any] = {}

        # Extract program names
        programs = re.findall(
            r"\b(DCGS[-\s]?[A-Z]?|JADC2|GBSD|MQ-25|F-35|ABMS|TITAN|IBCS)\b", text
        )
        if programs:
            params["programs"] = programs

        # Extract company names
        companies = re.findall(
            r"\b(Leidos|Northrop\s*Grumman|Raytheon|GDIT|BAE|L3Harris|Booz\s*Allen)\b",
            text,
            re.IGNORECASE,
        )
        if companies:
            params["companies"] = companies

        # Extract region
        region_match = re.search(
            r"\b(NCR|southeast|west|midwest|southwest)\b", text, re.IGNORECASE
        )
        if region_match:
            params["region"] = region_match.group(1)

        # Extract contact name for enrichment
        if intent == IntentType.ENRICH_CONTACT:
            name_match = re.search(
                r"(?:contact|person|enrich)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)", text
            )
            if name_match:
                params["contact_name"] = name_match.group(1)

        return params

    # ----- validation -----

    def validate(self, intent: ParsedIntent) -> ValidationResult:
        """Validate a parsed intent before execution."""
        if intent.intent == IntentType.UNKNOWN:
            return ValidationResult(
                status=ValidationStatus.INVALID,
                warnings=["Could not determine intent from text"],
                alternatives=intent.suggestions,
            )

        workflow_id = intent.matched_workflow_id
        if workflow_id and workflow_id not in self._available_workflow_ids:
            return ValidationResult(
                status=ValidationStatus.INVALID,
                warnings=[f"Workflow '{workflow_id}' not found"],
                alternatives=self._available_workflow_ids,
            )

        # Check for required params based on intent
        missing = []
        if intent.intent == IntentType.ENRICH_CONTACT:
            if "contact_name" not in intent.extracted_params:
                missing.append("contact_name")

        if intent.confidence < 0.5:
            return ValidationResult(
                status=ValidationStatus.AMBIGUOUS,
                workflow_id=workflow_id,
                warnings=["Low confidence — intent may be misinterpreted"],
                alternatives=intent.suggestions,
            )

        if missing:
            return ValidationResult(
                status=ValidationStatus.NEEDS_PARAMS,
                workflow_id=workflow_id,
                missing_params=missing,
            )

        return ValidationResult(
            status=ValidationStatus.VALID,
            workflow_id=workflow_id,
        )

    # ----- execution -----

    def execute(self, text: str) -> NLExecutionResult:
        """Full pipeline: parse → validate → create execution record."""
        self._exec_counter += 1
        exec_id = f"nlexec_{hashlib.md5(f'{text}:{self._exec_counter}:{time.time()}'.encode()).hexdigest()[:10]}"

        intent = self.parse_intent(text)
        validation = self.validate(intent)

        status = (
            "ready"
            if validation.status == ValidationStatus.VALID
            else validation.status.value
        )

        result = NLExecutionResult(
            execution_id=exec_id,
            intent=intent,
            validation=validation,
            workflow_run_id=None,
            status=status,
            output=None,
        )
        self._executions[exec_id] = result
        return result

    def get_execution(self, exec_id: str) -> Optional[NLExecutionResult]:
        return self._executions.get(exec_id)

    def list_executions(self, limit: int = 50) -> List[NLExecutionResult]:
        execs = sorted(
            self._executions.values(), key=lambda e: e.created_at, reverse=True
        )
        return execs[:limit]

    # ----- autocomplete -----

    def autocomplete(self, partial: str) -> List[Dict[str, Any]]:
        """Suggest completions for partial NL input."""
        if not partial or not partial.strip():
            return []

        lower = partial.lower().strip()
        suggestions = []

        templates = [
            ("Run full BD campaign for {program}", "Launch end-to-end BD campaign"),
            ("Enrich contact {name}", "Enrich and classify a contact"),
            ("Scrape jobs for {program}", "Run job scraper for a program"),
            ("Rescore pipeline", "Re-score all BD opportunities"),
            ("Generate weekly intel report", "Compile weekly intelligence"),
            ("Analyze competition in {region}", "Competitive density analysis"),
            ("Find contacts at {company}", "Search for company contacts"),
            ("Run weekly intel cycle", "Execute full weekly intelligence cycle"),
            ("Score and prioritize {program}", "Score opportunities for a program"),
        ]

        for template, description in templates:
            if any(word in template.lower() for word in lower.split()):
                suggestions.append(
                    {
                        "template": template,
                        "description": description,
                        "confidence": 0.8,
                    }
                )

        return suggestions[:5]

    # ----- stats -----

    def get_stats(self) -> Dict[str, Any]:
        total = len(self._executions)
        by_intent: Dict[str, int] = {}
        for ex in self._executions.values():
            key = ex.intent.intent.value
            by_intent[key] = by_intent.get(key, 0) + 1

        return {
            "total_executions": total,
            "by_intent": by_intent,
            "available_workflows": self._available_workflow_ids,
        }


# =========================================
# SINGLETON
# =========================================

_instance: Optional[NLToWorkflowEngine] = None


def get_nl_engine() -> NLToWorkflowEngine:
    global _instance
    if _instance is None:
        _instance = NLToWorkflowEngine()
    return _instance
