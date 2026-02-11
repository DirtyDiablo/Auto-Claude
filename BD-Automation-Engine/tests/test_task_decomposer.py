"""Tests for Phase 41A — Task Decomposer."""

import pytest

from src.agents.swarm.decomposer import (
    TaskDecomposer,
    TaskDAG,
    CostEstimate,
    TASK_TEMPLATES,
    TEMPLATE_KEYWORDS,
    get_task_decomposer,
)


# =========================================
# FIXTURES
# =========================================

@pytest.fixture
def decomposer():
    return TaskDecomposer()


# =========================================
# TEMPLATE DETECTION
# =========================================

def test_detect_campaign(decomposer):
    assert decomposer._detect_template("Build a BD campaign for DCGS") == "campaign_build"


def test_detect_enrichment(decomposer):
    assert decomposer._detect_template("Enrich and validate contacts") == "contact_enrichment"


def test_detect_program_analysis(decomposer):
    assert decomposer._detect_template("Analyze program intel for GBSD") == "program_analysis"


def test_detect_weekly_briefing(decomposer):
    assert decomposer._detect_template("Generate weekly briefing") == "weekly_briefing"


def test_detect_competitive(decomposer):
    assert decomposer._detect_template("Competitive analysis of rival firms") == "competitive_analysis"


def test_detect_default(decomposer):
    assert decomposer._detect_template("something random") == "campaign_build"


# =========================================
# PARAMETER EXTRACTION
# =========================================

def test_extract_program(decomposer):
    params = decomposer._extract_parameters("Research the DCGS program")
    assert params.get("program") == "DCGS"


def test_extract_organization(decomposer):
    params = decomposer._extract_parameters("Find contacts at Leidos")
    assert params.get("organization") == "Leidos"


def test_extract_location(decomposer):
    params = decomposer._extract_parameters("Jobs in Norfolk area")
    assert params.get("location") == "Norfolk"


def test_extract_empty(decomposer):
    params = decomposer._extract_parameters("hello world")
    assert len(params) == 0


# =========================================
# DECOMPOSITION
# =========================================

@pytest.mark.asyncio
async def test_decompose_campaign(decomposer):
    dag = await decomposer.decompose("Build a BD campaign for DCGS")
    assert isinstance(dag, TaskDAG)
    assert dag.dag_id != ""
    assert len(dag.nodes) == 10  # campaign_build has 10 tasks


@pytest.mark.asyncio
async def test_decompose_enrichment(decomposer):
    dag = await decomposer.decompose("", "contact_enrichment")
    assert len(dag.nodes) == 5


@pytest.mark.asyncio
async def test_decompose_has_edges(decomposer):
    dag = await decomposer.decompose("Build campaign", "campaign_build")
    assert len(dag.edges) > 0


@pytest.mark.asyncio
async def test_decompose_has_layers(decomposer):
    dag = await decomposer.decompose("Weekly briefing update", "weekly_briefing")
    assert len(dag.execution_layers) >= 1


@pytest.mark.asyncio
async def test_decompose_nodes_have_ids(decomposer):
    dag = await decomposer.decompose("Analyze program GBSD", "program_analysis")
    for node in dag.nodes:
        assert node.id != ""
        assert node.description != ""
        assert node.worker_type != ""


@pytest.mark.asyncio
async def test_decompose_dependencies_resolved(decomposer):
    dag = await decomposer.decompose("Campaign", "campaign_build")
    node_ids = {n.id for n in dag.nodes}
    for node in dag.nodes:
        for dep in node.depends_on:
            assert dep in node_ids


# =========================================
# DAG OPTIMIZATION
# =========================================

@pytest.mark.asyncio
async def test_optimize_dag(decomposer):
    dag = await decomposer.decompose("Campaign build", "campaign_build")
    optimized = await decomposer.optimize_dag(dag)
    assert len(optimized.execution_layers) >= 1


# =========================================
# COST ESTIMATION
# =========================================

@pytest.mark.asyncio
async def test_estimate_cost(decomposer):
    dag = await decomposer.decompose("Campaign build", "campaign_build")
    cost = await decomposer.estimate_cost(dag)
    assert isinstance(cost, CostEstimate)
    assert cost.total_tokens > 0
    assert cost.total_api_cost_usd > 0
    assert cost.num_workers == 10
    assert cost.num_parallel_groups >= 1


@pytest.mark.asyncio
async def test_estimate_worker_breakdown(decomposer):
    dag = await decomposer.decompose("", "campaign_build")
    cost = await decomposer.estimate_cost(dag)
    assert len(cost.worker_breakdown) > 0
    assert sum(cost.worker_breakdown.values()) == cost.total_tokens


# =========================================
# CRITICAL PATH
# =========================================

@pytest.mark.asyncio
async def test_critical_path_positive(decomposer):
    dag = await decomposer.decompose("Campaign build", "campaign_build")
    assert dag.critical_path_seconds > 0


@pytest.mark.asyncio
async def test_critical_path_less_than_total(decomposer):
    dag = await decomposer.decompose("Campaign build", "campaign_build")
    assert dag.critical_path_seconds <= dag.total_estimated_seconds


# =========================================
# HISTORY
# =========================================

@pytest.mark.asyncio
async def test_history(decomposer):
    await decomposer.decompose("Task 1")
    await decomposer.decompose("Task 2")
    assert len(decomposer.get_history()) == 2


# =========================================
# TEMPLATES VALIDITY
# =========================================

def test_all_templates_have_keywords():
    for name in TASK_TEMPLATES:
        assert name in TEMPLATE_KEYWORDS


def test_template_workers_are_valid():
    from src.agents.swarm.workers import DEFAULT_CAPABILITIES
    for name, tasks in TASK_TEMPLATES.items():
        for t in tasks:
            assert t["worker"] in DEFAULT_CAPABILITIES, \
                f"Template {name} references unknown worker: {t['worker']}"


# =========================================
# SINGLETON
# =========================================

def test_singleton():
    d1 = get_task_decomposer()
    d2 = get_task_decomposer()
    assert d1 is d2
