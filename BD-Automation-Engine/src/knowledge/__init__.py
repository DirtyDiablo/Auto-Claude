"""Phase 39A — Temporal Knowledge Graph + Entity Resolution + Knowledge Compiler."""

from src.knowledge.temporal_kg import (
    TemporalKnowledgeGraph,
    Episode,
    EpisodeResult,
    TemporalFact,
    EntityTimeline,
    ChangeEvent,
    Contradiction,
    get_temporal_kg,
)
from src.knowledge.entity_resolution import (
    EntityResolutionEngine,
    ResolutionResult,
    ResolutionCandidate,
    MergeResult,
    GlobalResolutionReport,
    get_resolution_engine,
)
from src.knowledge.compiler import (
    KnowledgeCompiler,
    ExtractedFact,
    CompilationReport,
    EpisodeSource,
    get_knowledge_compiler,
)

__all__ = [
    "TemporalKnowledgeGraph", "Episode", "EpisodeResult", "TemporalFact",
    "EntityTimeline", "ChangeEvent", "Contradiction", "get_temporal_kg",
    "EntityResolutionEngine", "ResolutionResult", "ResolutionCandidate",
    "MergeResult", "GlobalResolutionReport", "get_resolution_engine",
    "KnowledgeCompiler", "ExtractedFact", "CompilationReport",
    "EpisodeSource", "get_knowledge_compiler",
]
