"""
Master BD Pipeline — 7-node LangGraph StateGraph.

Nodes:
    1. scrape             — Load/scrape job data
    2. map_programs        — Program mapping (Engine 2)
    3. classify_contacts   — OrgChart classification (Engine 3)
    4. generate_playbooks  — BD playbook generation (Engine 4)
    5. score               — BD priority scoring (Engine 5)
    6. qa_check            — QA with human-in-the-loop gate (Engine 6)
    7. index_knowledge     — Knowledge base indexing (Engine 8)

Conditional edge after qa_check:
    - All pass  → index_knowledge
    - Failures  → END (with qa_results attached for human review)
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from workflows.state import PipelineState, StageEntry, WorkflowConfig, make_initial_state

# ---------------------------------------------------------------------------
# Structured logging (graceful fallback)
# ---------------------------------------------------------------------------

try:
    import structlog
    _log = structlog.get_logger("workflows.master_pipeline")
except ImportError:
    _log = logging.getLogger("workflows.master_pipeline")

# ---------------------------------------------------------------------------
# LangGraph import (graceful fallback)
# ---------------------------------------------------------------------------

try:
    from langgraph.graph import END, StateGraph

    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    StateGraph = None
    END = "__end__"

# ---------------------------------------------------------------------------
# Project root for engine imports
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ===================================================================
# Helper: run a stage and record timing/errors
# ===================================================================

def _run_node(name: str, state: PipelineState, fn) -> PipelineState:
    """Execute *fn*, record timing in stage_history, capture errors."""
    started = datetime.utcnow()
    entry: StageEntry = {
        "name": name,
        "status": "passed",
        "started_at": started.isoformat(),
        "ended_at": "",
        "duration_seconds": 0.0,
        "record_count": 0,
        "error": None,
    }
    try:
        _log.info("node.start", node=name)
        state = fn(state)
        entry["status"] = "passed"
    except Exception as exc:
        _log.error("node.failed", node=name, error=str(exc))
        entry["status"] = "failed"
        entry["error"] = str(exc)
        state.setdefault("errors", []).append(f"{name}: {exc}")
    finally:
        ended = datetime.utcnow()
        entry["ended_at"] = ended.isoformat()
        entry["duration_seconds"] = (ended - started).total_seconds()
        state.setdefault("stage_history", []).append(entry)
        _log.info("node.end", node=name, status=entry["status"],
                  duration=entry["duration_seconds"])
    return state


# ===================================================================
# Node implementations
# ===================================================================

def scrape(state: PipelineState) -> PipelineState:
    """Node 1: Load jobs from file or invoke Engine 1 scraper."""
    def _inner(s: PipelineState) -> PipelineState:
        input_path = s.get("metadata", {}).get("input_path")
        if input_path and Path(input_path).exists():
            with open(input_path, "r", encoding="utf-8") as fh:
                jobs = json.load(fh)
            s["jobs"] = jobs if isinstance(jobs, list) else [jobs]
            _log.info("scrape.loaded", count=len(s["jobs"]))
        else:
            # Attempt Engine1 Apify integration
            try:
                from Engine1_Scraper.scripts.scraper import run_scraper
                s["jobs"] = run_scraper()
            except ImportError:
                _log.warning("scrape.no_engine", msg="Engine1 not available and no input file")
                if not s.get("jobs"):
                    s["jobs"] = []
        return s
    return _run_node("scrape", state, _inner)


def map_programs(state: PipelineState) -> PipelineState:
    """Node 2: Map jobs to federal programs via Engine 2."""
    def _inner(s: PipelineState) -> PipelineState:
        if not s.get("jobs"):
            _log.warning("map_programs.skip", reason="no jobs")
            return s
        try:
            from Engine2_ProgramMapping.scripts.program_mapper import process_jobs_batch
            mapped = process_jobs_batch(s["jobs"])
            s["enriched_jobs"] = mapped if mapped else s["jobs"]
        except ImportError:
            _log.warning("map_programs.no_engine", msg="Engine2 not available")
            s["enriched_jobs"] = s["jobs"]
        return s
    return _run_node("map_programs", state, _inner)


def classify_contacts(state: PipelineState) -> PipelineState:
    """Node 3: Classify contacts via Engine 3 OrgChart."""
    def _inner(s: PipelineState) -> PipelineState:
        try:
            from Engine3_OrgChart.scripts.contact_lookup import lookup_contacts
            contacts = []
            jobs = s.get("enriched_jobs") or s.get("jobs", [])
            for job in jobs:
                program = job.get("_mapping", {}).get("program_name", "")
                company = job.get("company", "")
                if program or company:
                    found = lookup_contacts(program=program, company=company)
                    if found:
                        contacts.extend(found)
            s["contacts"] = contacts
            _log.info("classify_contacts.done", count=len(contacts))
        except ImportError:
            _log.warning("classify_contacts.no_engine", msg="Engine3 not available")
        return s
    return _run_node("classify_contacts", state, _inner)


def generate_playbooks(state: PipelineState) -> PipelineState:
    """Node 4: Generate BD playbooks via Engine 4."""
    def _inner(s: PipelineState) -> PipelineState:
        jobs = s.get("enriched_jobs") or s.get("jobs", [])
        if not jobs:
            return s
        try:
            from Engine4_Playbook.scripts.bd_playbook_generator import generate_playbooks_batch
            output_dir = str(PROJECT_ROOT / "outputs" / "BD_Briefings")
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            playbooks = generate_playbooks_batch(jobs, output_dir=output_dir)
            s["metadata"]["playbooks_generated"] = len(playbooks) if playbooks else 0
        except ImportError:
            _log.warning("generate_playbooks.no_engine", msg="Engine4 not available")
        return s
    return _run_node("generate_playbooks", state, _inner)


def score(state: PipelineState) -> PipelineState:
    """Node 5: Calculate BD priority scores via Engine 5."""
    def _inner(s: PipelineState) -> PipelineState:
        jobs = s.get("enriched_jobs") or s.get("jobs", [])
        if not jobs:
            return s
        try:
            from Engine5_Scoring.scripts.bd_scoring import score_batch
            scored = score_batch(jobs)
            s["scored_jobs"] = scored if scored else jobs
        except ImportError:
            _log.warning("score.no_engine", msg="Engine5 not available")
            s["scored_jobs"] = jobs
        return s
    return _run_node("score", state, _inner)


def qa_check(state: PipelineState) -> PipelineState:
    """Node 6: QA evaluation with human-in-the-loop gate via Engine 6."""
    def _inner(s: PipelineState) -> PipelineState:
        jobs = s.get("scored_jobs") or s.get("enriched_jobs") or s.get("jobs", [])
        if not jobs:
            s["qa_results"] = {"passed": True, "approved": 0, "needs_review": 0}
            return s
        try:
            from Engine6_QA.scripts.qa_feedback import run_qa_workflow
            qa_report, approved, review = run_qa_workflow(jobs)
            s["qa_results"] = {
                "passed": len(review) == 0,
                "approved": len(approved),
                "needs_review": len(review),
                "report": qa_report,
            }
        except ImportError:
            _log.warning("qa_check.no_engine", msg="Engine6 not available")
            s["qa_results"] = {"passed": True, "approved": len(jobs), "needs_review": 0}
        return s
    return _run_node("qa_check", state, _inner)


def index_knowledge(state: PipelineState) -> PipelineState:
    """Node 7: Index results into knowledge base via Engine 8."""
    def _inner(s: PipelineState) -> PipelineState:
        try:
            from Engine8_Knowledge.scripts.indexer import BDIndexer
            indexer = BDIndexer()
            indexer.index_all()
            s["metadata"]["knowledge_indexed"] = True
            _log.info("index_knowledge.done")
        except ImportError:
            _log.warning("index_knowledge.no_engine", msg="Engine8 not available")
        return s
    return _run_node("index_knowledge", state, _inner)


# ===================================================================
# Conditional edge: after qa_check
# ===================================================================

def _qa_gate(state: PipelineState) -> str:
    """Return next node name based on QA results."""
    qa = state.get("qa_results", {})
    if qa.get("passed", True):
        return "index_knowledge"
    return END


# ===================================================================
# Graph builder
# ===================================================================

def build_master_pipeline():
    """Construct and compile the master pipeline StateGraph.

    Returns the compiled graph, or None if LangGraph is unavailable.
    """
    if not LANGGRAPH_AVAILABLE:
        _log.warning("langgraph not installed — returning None")
        return None

    graph = StateGraph(PipelineState)

    # Add nodes
    graph.add_node("scrape", scrape)
    graph.add_node("map_programs", map_programs)
    graph.add_node("classify_contacts", classify_contacts)
    graph.add_node("generate_playbooks", generate_playbooks)
    graph.add_node("score", score)
    graph.add_node("qa_check", qa_check)
    graph.add_node("index_knowledge", index_knowledge)

    # Linear edges
    graph.add_edge("scrape", "map_programs")
    graph.add_edge("map_programs", "classify_contacts")
    graph.add_edge("classify_contacts", "generate_playbooks")
    graph.add_edge("generate_playbooks", "score")
    graph.add_edge("score", "qa_check")

    # Conditional: qa_check → index_knowledge | END
    graph.add_conditional_edges("qa_check", _qa_gate, {
        "index_knowledge": "index_knowledge",
        END: END,
    })

    graph.add_edge("index_knowledge", END)

    # Entry point
    graph.set_entry_point("scrape")

    return graph.compile()


def run_master_pipeline(
    config: WorkflowConfig | None = None,
    initial_state: PipelineState | None = None,
) -> PipelineState:
    """Convenience function: build graph, prepare state, invoke.

    Works with or without LangGraph installed — falls back to sequential
    execution of node functions.
    """
    cfg = config or WorkflowConfig()
    state = initial_state or make_initial_state(
        metadata={"input_path": cfg.input_path, "test_mode": cfg.test_mode},
    )

    compiled = build_master_pipeline()
    if compiled is not None:
        result = compiled.invoke(state)
        return result

    # Fallback: sequential execution without LangGraph
    _log.info("fallback.sequential", msg="Running nodes sequentially (no LangGraph)")
    for node_fn in [scrape, map_programs, classify_contacts,
                    generate_playbooks, score, qa_check]:
        state = node_fn(state)

    # Apply QA gate
    if _qa_gate(state) == "index_knowledge":
        state = index_knowledge(state)

    return state
