"""
Three-tier classification pipeline for BD Intelligence Hub.

Tier 1 - Rules (free, instant, ~60-70% coverage):
    Pattern matching, file extensions, directory structure, naming conventions.

Tier 2 - Local zero-shot model (~20% coverage):
    DeBERTa-v3-large-mnli for ambiguous texts. ~50-100 texts/second on CPU.

Tier 3 - LLM via Instructor (~10% coverage):
    Structured LLM output for complex/ambiguous classifications.

Usage:
    from Engine8_Knowledge.scripts.classifier_pipeline import ClassifierPipeline
    pipeline = ClassifierPipeline()
    result = pipeline.classify("Senior Systems Engineer at Leidos on DCGS program")

Install (Tier 2+3):
    pip install transformers torch instructor
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Optional dependencies
try:
    from transformers import pipeline as hf_pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    import instructor
    INSTRUCTOR_AVAILABLE = True
except ImportError:
    INSTRUCTOR_AVAILABLE = False

try:
    from pydantic import BaseModel, Field
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False


# ---------------------------------------------------------------------------
# Classification categories
# ---------------------------------------------------------------------------

BD_CATEGORIES = [
    "executive_contact",
    "program_manager",
    "technical_lead",
    "hiring_manager",
    "recruiter",
    "engineer",
    "analyst",
    "administrative",
    "unknown",
]

ENTITY_CATEGORIES = [
    "person",
    "company",
    "program",
    "job",
    "contract",
    "location",
    "interaction",
    "document",
    "unknown",
]

FILE_CATEGORIES = [
    "source_code",
    "configuration",
    "documentation",
    "data_file",
    "test_file",
    "build_artifact",
    "media",
    "unknown",
]

CLEARANCE_LEVELS = [
    "TS/SCI",
    "TS",
    "Secret",
    "Public Trust",
    "None",
    "Unknown",
]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ClassificationResult:
    """Result from classification pipeline."""
    text: str
    category: str
    confidence: float
    tier_used: int  # 1=rules, 2=zero-shot, 3=LLM
    all_scores: Dict[str, float] = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)


@dataclass
class ContactClassification:
    """Classification result for a BD contact."""
    name: str
    tier: int  # 1-6
    tier_name: str
    bd_priority: str
    is_hiring_manager: bool
    is_decision_maker: bool
    functional_area: str
    confidence: float
    signals: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Tier 1: Rule-based classification
# ---------------------------------------------------------------------------

class RuleClassifier:
    """Pattern matching classifier — instant, free, ~60-70% coverage."""

    # Contact title → tier patterns (from Engine3 contact_classifier.py)
    TIER_PATTERNS = {
        1: {  # Executive
            "name": "Executive",
            "patterns": [
                r"\b(CEO|CTO|COO|CFO|CIO|CISO)\b",
                r"\bChief\s+\w+\s+Officer\b",
                r"\bPresident\b",
                r"\bGeneral\s+Manager\b",
                r"\bExecutive\s+(VP|Vice\s+President)\b",
                r"\bSVP\b",
                r"\bSenior\s+Vice\s+President\b",
            ],
        },
        2: {  # Director
            "name": "Director",
            "patterns": [
                r"\bDirector\b",
                r"\bVP\b",
                r"\bVice\s+President\b",
                r"\bDivision\s+(Head|Chief|Lead)\b",
            ],
        },
        3: {  # Program Leadership
            "name": "Program Leadership",
            "patterns": [
                r"\bProgram\s+Manager\b",
                r"\bProject\s+Manager\b",
                r"\bSite\s+Lead\b",
                r"\bTask\s+Order\s+Manager\b",
                r"\bDeputy\s+Program\s+Manager\b",
                r"\bPrincipal\s+(Engineer|Scientist|Analyst)\b",
                r"\bChief\s+(Engineer|Architect|Scientist)\b",
            ],
        },
        4: {  # Management
            "name": "Management",
            "patterns": [
                r"\bManager\b",
                r"\bTeam\s+Lead\b",
                r"\bTechnical\s+Lead\b",
                r"\bSupervisor\b",
                r"\bSection\s+(Chief|Lead)\b",
                r"\bGroup\s+Lead\b",
            ],
        },
        5: {  # Senior IC
            "name": "Senior IC",
            "patterns": [
                r"\bSenior\s+\w*\s*(Engineer|Developer|Analyst|Specialist|Consultant)\b",
                r"\bSr\.?\s+\w*\s*(Engineer|Developer|Analyst|Specialist)\b",
                r"\bStaff\s+\w*\s*(Engineer|Scientist)\b",
                r"\bArchitect\b",
                r"\bSubject\s+Matter\s+Expert\b",
                r"\bSME\b",
            ],
        },
        6: {  # Individual Contributor
            "name": "Individual Contributor",
            "patterns": [
                r"\b(Engineer|Developer|Analyst|Specialist|Technician|Administrator)\b",
                r"\bConsultant\b",
                r"\bCoordinator\b",
                r"\bAssistant\b",
                r"\bAssociate\b",
            ],
        },
    }

    # Hiring manager signals
    HIRING_SIGNALS = [
        r"\bHiring\s+Manager\b",
        r"\bRecruit(ing|er)\b",
        r"\bTalent\s+Acquisition\b",
        r"\bStaffing\b",
        r"\bHR\s+(Manager|Director|Lead)\b",
    ]

    # Decision maker signals
    DECISION_SIGNALS = [
        r"\bDecision\s+Maker\b",
        r"\bApproval\s+Authority\b",
        r"\bBudget\s+Owner\b",
        r"\bContracting\s+Officer\b",
        r"\bCOR\b",
        r"\bCOTR\b",
    ]

    # Clearance patterns
    CLEARANCE_PATTERNS = [
        (r"\bTS/SCI\b", "TS/SCI"),
        (r"\bTop\s+Secret\b", "TS"),
        (r"\bTS\b(?!/SCI)", "TS"),
        (r"\bSecret\b", "Secret"),
        (r"\bPublic\s+Trust\b", "Public Trust"),
    ]

    # File extension → category
    FILE_EXT_MAP = {
        ".py": "source_code", ".js": "source_code", ".ts": "source_code",
        ".tsx": "source_code", ".jsx": "source_code", ".rs": "source_code",
        ".go": "source_code", ".java": "source_code", ".c": "source_code",
        ".cpp": "source_code", ".cs": "source_code", ".rb": "source_code",
        ".php": "source_code", ".swift": "source_code", ".kt": "source_code",
        ".sql": "source_code", ".sh": "source_code", ".bash": "source_code",
        ".json": "configuration", ".yaml": "configuration", ".yml": "configuration",
        ".toml": "configuration", ".ini": "configuration", ".cfg": "configuration",
        ".env": "configuration", ".xml": "configuration",
        ".md": "documentation", ".rst": "documentation", ".txt": "documentation",
        ".pdf": "documentation", ".docx": "documentation",
        ".csv": "data_file", ".xlsx": "data_file", ".xls": "data_file",
        ".db": "data_file", ".sqlite": "data_file", ".parquet": "data_file",
        ".png": "media", ".jpg": "media", ".jpeg": "media", ".gif": "media",
        ".svg": "media", ".mp4": "media", ".mp3": "media",
    }

    # Directory name → category
    DIR_CATEGORY_MAP = {
        "test": "test_file", "tests": "test_file", "__tests__": "test_file",
        "spec": "test_file", "specs": "test_file",
        "docs": "documentation", "doc": "documentation",
        "data": "data_file", "datasets": "data_file",
        "dist": "build_artifact", "build": "build_artifact",
        "node_modules": "build_artifact", "__pycache__": "build_artifact",
        ".git": "build_artifact",
    }

    def classify_contact(self, title: str, name: str = "") -> Optional[ContactClassification]:
        """Classify a contact by job title using rule patterns."""
        if not title:
            return None

        title_upper = title.strip()

        # Find tier
        best_tier = 6
        best_name = "Individual Contributor"
        for tier, info in self.TIER_PATTERNS.items():
            for pattern in info["patterns"]:
                if re.search(pattern, title_upper, re.IGNORECASE):
                    if tier < best_tier:
                        best_tier = tier
                        best_name = info["name"]
                    break

        # Check hiring signals
        is_hiring = any(re.search(p, title_upper, re.IGNORECASE) for p in self.HIRING_SIGNALS)

        # Check decision maker signals
        is_decision = best_tier <= 2 or any(
            re.search(p, title_upper, re.IGNORECASE) for p in self.DECISION_SIGNALS
        )

        # Determine BD priority
        if best_tier <= 2:
            bd_priority = "Critical"
        elif best_tier <= 4:
            bd_priority = "High"
        elif best_tier == 5:
            bd_priority = "Medium"
        else:
            bd_priority = "Low"

        # Functional area detection
        functional_area = self._detect_functional_area(title_upper)

        return ContactClassification(
            name=name,
            tier=best_tier,
            tier_name=best_name,
            bd_priority=bd_priority,
            is_hiring_manager=is_hiring,
            is_decision_maker=is_decision,
            functional_area=functional_area,
            confidence=0.85 if best_tier < 6 else 0.5,
            signals=[],
        )

    def classify_clearance(self, text: str) -> Tuple[str, float]:
        """Extract clearance level from text."""
        for pattern, level in self.CLEARANCE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return level, 0.95
        return "Unknown", 0.0

    def classify_file(self, file_path: str) -> ClassificationResult:
        """Classify a file by path, extension, and directory."""
        path = Path(file_path)
        ext = path.suffix.lower()

        # Check extension first
        category = self.FILE_EXT_MAP.get(ext)
        confidence = 0.9 if category else 0.0

        # Check directory patterns
        if not category:
            for part in path.parts:
                if part.lower() in self.DIR_CATEGORY_MAP:
                    category = self.DIR_CATEGORY_MAP[part.lower()]
                    confidence = 0.8
                    break

        # Check for test files by name pattern
        if category == "source_code" and re.search(r"test_|_test\.|\.test\.|\.spec\.", path.name, re.IGNORECASE):
            category = "test_file"
            confidence = 0.95

        return ClassificationResult(
            text=str(file_path),
            category=category or "unknown",
            confidence=confidence,
            tier_used=1,
        )

    def classify_entity(self, text: str) -> ClassificationResult:
        """Classify text into entity type using rules."""
        text_lower = text.lower()

        # Person patterns
        if re.search(r"\b(mr|mrs|ms|dr)\.?\s", text_lower) or re.search(r"\b\w+\s+\w+\s+(at|from|with)\s", text_lower):
            return ClassificationResult(text=text, category="person", confidence=0.8, tier_used=1)

        # Company patterns
        if re.search(r"\b(inc|llc|corp|ltd|gdit|leidos|bah|raytheon|northrop|lockheed|saic|caci|peraton)\b", text_lower):
            return ClassificationResult(text=text, category="company", confidence=0.85, tier_used=1)

        # Program patterns
        if re.search(r"\b(dcgs|gbsd|aegis|abms|jadc2|ngj|peo|program)\b", text_lower):
            return ClassificationResult(text=text, category="program", confidence=0.8, tier_used=1)

        # Job patterns
        if re.search(r"\b(engineer|developer|analyst|manager|opening|position|posting)\b", text_lower):
            return ClassificationResult(text=text, category="job", confidence=0.6, tier_used=1)

        return ClassificationResult(text=text, category="unknown", confidence=0.0, tier_used=1)

    def _detect_functional_area(self, title: str) -> str:
        """Detect functional area from title."""
        areas = {
            "Engineering": r"\b(Engineer|Engineering|Software|Systems|Hardware)\b",
            "Intelligence": r"\b(Intel|Intelligence|SIGINT|GEOINT|HUMINT|ISR|Analyst)\b",
            "Cybersecurity": r"\b(Cyber|Security|CISO|InfoSec|IA)\b",
            "Program Management": r"\b(Program|Project)\s+Manage",
            "Business Development": r"\b(BD|Business\s+Development|Capture|Proposal)\b",
            "Human Resources": r"\b(HR|Human\s+Resources|Recruit|Talent|Staffing)\b",
            "Finance": r"\b(Finance|Financial|Accounting|Budget|Controller)\b",
            "Operations": r"\b(Operations|Ops|Logistics|Supply\s+Chain)\b",
            "IT": r"\b(IT|Information\s+Technology|Network|Cloud|DevOps|SRE)\b",
        }
        for area, pattern in areas.items():
            if re.search(pattern, title, re.IGNORECASE):
                return area
        return "General"


# ---------------------------------------------------------------------------
# Tier 2: Zero-shot classification
# ---------------------------------------------------------------------------

class ZeroShotClassifier:
    """DeBERTa-v3-large zero-shot classifier — no API costs, ~50-100 texts/sec."""

    def __init__(self, model_name: str = "MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli"):
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("transformers is required. Install with: pip install transformers torch")
        self._classifier = None
        self.model_name = model_name

    @property
    def classifier(self):
        """Lazy-load the model."""
        if self._classifier is None:
            self._classifier = hf_pipeline(
                "zero-shot-classification",
                model=self.model_name,
                device=-1,  # CPU
            )
        return self._classifier

    def classify(
        self,
        text: str,
        candidate_labels: List[str],
        multi_label: bool = False,
    ) -> ClassificationResult:
        """Classify text using zero-shot inference."""
        result = self.classifier(
            text,
            candidate_labels,
            multi_label=multi_label,
        )

        scores = dict(zip(result["labels"], result["scores"]))
        top_label = result["labels"][0]
        top_score = result["scores"][0]

        return ClassificationResult(
            text=text,
            category=top_label,
            confidence=top_score,
            tier_used=2,
            all_scores=scores,
        )

    def classify_batch(
        self,
        texts: List[str],
        candidate_labels: List[str],
    ) -> List[ClassificationResult]:
        """Classify multiple texts."""
        results = []
        for text in texts:
            results.append(self.classify(text, candidate_labels))
        return results


# ---------------------------------------------------------------------------
# Tier 3: LLM-based classification via Instructor
# ---------------------------------------------------------------------------

class LLMClassifier:
    """Structured LLM classifier using Instructor — highest accuracy, API costs."""

    def __init__(self, provider: str = "anthropic/claude-3-5-haiku-latest"):
        if not INSTRUCTOR_AVAILABLE:
            raise ImportError("instructor is required. Install with: pip install instructor")
        if not PYDANTIC_AVAILABLE:
            raise ImportError("pydantic is required. Install with: pip install pydantic")
        self.provider = provider
        self._client = None

    @property
    def client(self):
        """Lazy-load Instructor client."""
        if self._client is None:
            self._client = instructor.from_provider(self.provider)
        return self._client

    def classify_contact(self, name: str, title: str, company: str = "") -> ClassificationResult:
        """Classify a contact using structured LLM output."""
        # Define response model inline to avoid import issues
        class ContactClassificationResponse(BaseModel):
            tier: int = Field(ge=1, le=6, description="Contact tier (1=Executive, 6=IC)")
            tier_name: str = Field(description="Tier label")
            bd_priority: str = Field(description="BD priority level")
            is_hiring_manager: bool = Field(default=False)
            is_decision_maker: bool = Field(default=False)
            functional_area: str = Field(description="Primary functional area")
            confidence: float = Field(ge=0, le=1, description="Classification confidence")
            reasoning: str = Field(description="Brief reasoning")

        context = f"Name: {name}\nTitle: {title}"
        if company:
            context += f"\nCompany: {company}"

        response = self.client.chat.completions.create(
            model=self.provider.split("/")[-1] if "/" in self.provider else self.provider,
            response_model=ContactClassificationResponse,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a BD intelligence classifier for federal defense programs. "
                        "Classify the contact into a tier (1=Executive, 2=Director, 3=Program Leadership, "
                        "4=Management, 5=Senior IC, 6=Individual Contributor). "
                        "Determine BD priority (Critical/High/Medium/Low), hiring manager status, "
                        "and decision maker status."
                    ),
                },
                {"role": "user", "content": context},
            ],
        )

        return ClassificationResult(
            text=context,
            category=f"tier_{response.tier}_{response.tier_name}",
            confidence=response.confidence,
            tier_used=3,
            metadata={
                "tier": response.tier,
                "tier_name": response.tier_name,
                "bd_priority": response.bd_priority,
                "is_hiring_manager": response.is_hiring_manager,
                "is_decision_maker": response.is_decision_maker,
                "functional_area": response.functional_area,
                "reasoning": response.reasoning,
            },
        )

    def classify_entity(self, text: str, categories: List[str] = None) -> ClassificationResult:
        """Classify text into an entity category using LLM."""
        cats = categories or ENTITY_CATEGORIES

        class EntityClassificationResponse(BaseModel):
            category: str = Field(description="Entity category")
            confidence: float = Field(ge=0, le=1)
            reasoning: str = Field(description="Brief reasoning")

        response = self.client.chat.completions.create(
            model=self.provider.split("/")[-1] if "/" in self.provider else self.provider,
            response_model=EntityClassificationResponse,
            messages=[
                {
                    "role": "system",
                    "content": f"Classify the following text into one of these categories: {', '.join(cats)}",
                },
                {"role": "user", "content": text},
            ],
        )

        return ClassificationResult(
            text=text,
            category=response.category,
            confidence=response.confidence,
            tier_used=3,
            metadata={"reasoning": response.reasoning},
        )


# ---------------------------------------------------------------------------
# BERTopic category discovery (optional)
# ---------------------------------------------------------------------------

class TopicDiscovery:
    """BERTopic-based automatic category discovery from embeddings."""

    def __init__(self):
        try:
            from bertopic import BERTopic
            self.BERTopic = BERTopic
            self._model = None
        except ImportError:
            raise ImportError("bertopic is required. Install with: pip install bertopic")

    def discover_topics(
        self,
        texts: List[str],
        embeddings=None,
        nr_topics: int = None,
        min_topic_size: int = 10,
    ) -> Dict:
        """Discover natural topic groupings from texts.

        Args:
            texts: List of text documents
            embeddings: Pre-computed embeddings (e.g., from Qdrant)
            nr_topics: Target number of topics (None = auto)
            min_topic_size: Minimum documents per topic

        Returns:
            Dict with topics, topic_labels, topic_sizes, document_topics
        """
        self._model = self.BERTopic(
            nr_topics=nr_topics,
            min_topic_size=min_topic_size,
            verbose=False,
        )

        if embeddings is not None:
            topics, probs = self._model.fit_transform(texts, embeddings=embeddings)
        else:
            topics, probs = self._model.fit_transform(texts)

        topic_info = self._model.get_topic_info()
        topic_labels = {}
        for _, row in topic_info.iterrows():
            tid = row["Topic"]
            if tid != -1:
                topic_labels[tid] = row.get("Name", f"Topic_{tid}")

        return {
            "num_topics": len(topic_labels),
            "topic_labels": topic_labels,
            "topic_sizes": {tid: int(count) for tid, count in zip(topic_info["Topic"], topic_info["Count"]) if tid != -1},
            "document_topics": topics,
            "outliers": sum(1 for t in topics if t == -1),
        }


# ---------------------------------------------------------------------------
# Pipeline orchestrator
# ---------------------------------------------------------------------------

class ClassifierPipeline:
    """Three-tier classification pipeline.

    Tier 1 (Rules) → Tier 2 (Zero-shot) → Tier 3 (LLM)
    Escalates only when confidence is below threshold.
    """

    def __init__(
        self,
        confidence_threshold: float = 0.7,
        enable_tier2: bool = True,
        enable_tier3: bool = True,
        llm_provider: str = "anthropic/claude-3-5-haiku-latest",
    ):
        self.confidence_threshold = confidence_threshold
        self.enable_tier2 = enable_tier2 and TRANSFORMERS_AVAILABLE
        self.enable_tier3 = enable_tier3 and INSTRUCTOR_AVAILABLE and PYDANTIC_AVAILABLE

        self.rule_classifier = RuleClassifier()
        self._zero_shot = None
        self._llm = None
        self.llm_provider = llm_provider

    @property
    def zero_shot(self) -> Optional[ZeroShotClassifier]:
        if self._zero_shot is None and self.enable_tier2:
            try:
                self._zero_shot = ZeroShotClassifier()
            except Exception as e:
                logger.warning("zero_shot_init_failed", error=str(e))
        return self._zero_shot

    @property
    def llm(self) -> Optional[LLMClassifier]:
        if self._llm is None and self.enable_tier3:
            try:
                self._llm = LLMClassifier(provider=self.llm_provider)
            except Exception as e:
                logger.warning("llm_classifier_init_failed", error=str(e))
        return self._llm

    def classify(
        self,
        text: str,
        categories: List[str] = None,
        classification_type: str = "entity",
    ) -> ClassificationResult:
        """Classify text through the three-tier pipeline.

        Args:
            text: Text to classify
            categories: Custom category list (or use defaults)
            classification_type: "entity", "contact", or "file"

        Returns:
            ClassificationResult with tier_used indicating which level resolved it
        """
        cats = categories or ENTITY_CATEGORIES

        # Tier 1: Rules
        if classification_type == "file":
            result = self.rule_classifier.classify_file(text)
        elif classification_type == "contact":
            contact = self.rule_classifier.classify_contact(text)
            if contact:
                result = ClassificationResult(
                    text=text,
                    category=f"tier_{contact.tier}_{contact.tier_name}",
                    confidence=contact.confidence,
                    tier_used=1,
                    metadata={"contact": contact.__dict__},
                )
            else:
                result = ClassificationResult(text=text, category="unknown", confidence=0.0, tier_used=1)
        else:
            result = self.rule_classifier.classify_entity(text)

        if result.confidence >= self.confidence_threshold:
            return result

        # Tier 2: Zero-shot
        if self.zero_shot and classification_type != "file":
            try:
                result = self.zero_shot.classify(text, cats)
                if result.confidence >= self.confidence_threshold:
                    return result
            except Exception as e:
                logger.warning("tier2_classification_failed", error=str(e))

        # Tier 3: LLM
        if self.llm and classification_type != "file":
            try:
                if classification_type == "contact":
                    result = self.llm.classify_contact(name="", title=text)
                else:
                    result = self.llm.classify_entity(text, cats)
                return result
            except Exception as e:
                logger.warning("tier3_classification_failed", error=str(e))

        return result

    def classify_batch(
        self,
        texts: List[str],
        categories: List[str] = None,
        classification_type: str = "entity",
    ) -> List[ClassificationResult]:
        """Classify multiple texts through the pipeline."""
        return [self.classify(t, categories, classification_type) for t in texts]

    def stats(self) -> Dict:
        """Get pipeline capabilities status."""
        return {
            "tier1_rules": True,
            "tier2_zero_shot": self.enable_tier2 and TRANSFORMERS_AVAILABLE,
            "tier3_llm": self.enable_tier3 and INSTRUCTOR_AVAILABLE,
            "confidence_threshold": self.confidence_threshold,
            "llm_provider": self.llm_provider if self.enable_tier3 else None,
            "bertopic_available": _check_bertopic(),
        }


def _check_bertopic() -> bool:
    try:
        return True
    except ImportError:
        return False


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO)

    pipeline = ClassifierPipeline(enable_tier2=False, enable_tier3=False)
    print(f"Pipeline stats: {json.dumps(pipeline.stats(), indent=2)}")

    # Test contact classification
    test_titles = [
        "Chief Technology Officer",
        "Program Manager - DCGS",
        "Senior Systems Engineer",
        "Software Developer",
        "Recruiter",
    ]
    print("\n--- Contact Classification (Tier 1 Rules) ---")
    for title in test_titles:
        result = pipeline.classify(title, classification_type="contact")
        print(f"  {title}: {result.category} (conf={result.confidence:.2f}, tier={result.tier_used})")

    # Test entity classification
    test_entities = [
        "Leidos Inc",
        "DCGS-A Program",
        "John Smith at Northrop Grumman",
        "Senior Analyst position in Fort Meade",
    ]
    print("\n--- Entity Classification (Tier 1 Rules) ---")
    for entity in test_entities:
        result = pipeline.classify(entity, classification_type="entity")
        print(f"  {entity}: {result.category} (conf={result.confidence:.2f}, tier={result.tier_used})")

    # Test file classification
    test_files = [
        "Engine2_ProgramMapping/scripts/pipeline.py",
        "docs/README.md",
        "dashboard/public/data/contacts.json",
        "tests/test_api.py",
    ]
    print("\n--- File Classification (Tier 1 Rules) ---")
    for fp in test_files:
        result = pipeline.classify(fp, classification_type="file")
        print(f"  {fp}: {result.category} (conf={result.confidence:.2f}, tier={result.tier_used})")
