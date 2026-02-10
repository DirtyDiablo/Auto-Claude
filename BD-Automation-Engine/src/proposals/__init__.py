"""Phase 35A — Proposal & Capture Automation Engine."""

from src.proposals.capability_generator import (
    CapabilityStatementGenerator,
    CapabilityStatement,
    CapabilitySection,
    TemplateVariant,
    get_capability_generator,
)
from src.proposals.past_performance import (
    PastPerformanceBuilder,
    PastPerformanceEntry,
    PerformanceMatrix,
    RelevanceScore,
    get_past_performance_builder,
)
from src.proposals.compliance_matrix import (
    ComplianceMatrixGenerator,
    ComplianceMatrix,
    ComplianceRow,
    GapAnalysis,
    TeamingRecommendation,
    get_compliance_generator,
)
from src.proposals.pricing_engine import (
    PricingEngine,
    LaborCategory,
    RateCard,
    PricingTemplate,
    PricingAnalysis,
    get_pricing_engine,
)

__all__ = [
    "CapabilityStatementGenerator",
    "CapabilityStatement",
    "CapabilitySection",
    "TemplateVariant",
    "get_capability_generator",
    "PastPerformanceBuilder",
    "PastPerformanceEntry",
    "PerformanceMatrix",
    "RelevanceScore",
    "get_past_performance_builder",
    "ComplianceMatrixGenerator",
    "ComplianceMatrix",
    "ComplianceRow",
    "GapAnalysis",
    "TeamingRecommendation",
    "get_compliance_generator",
    "PricingEngine",
    "LaborCategory",
    "RateCard",
    "PricingTemplate",
    "PricingAnalysis",
    "get_pricing_engine",
]
