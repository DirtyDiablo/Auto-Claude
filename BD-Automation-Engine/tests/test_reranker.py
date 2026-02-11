"""Tests for Phase 40A — Advanced Reranker."""

import pytest

from src.rag.reranker import (
    AdvancedReranker,
    ScoredDoc,
    RerankResult,
    get_reranker,
    _cosine_similarity,
    _token_embeddings,
    _text_embedding,
    _token_overlap_score,
)


# =========================================
# FIXTURES
# =========================================

@pytest.fixture
def reranker():
    return AdvancedReranker()


@pytest.fixture
def colbert_reranker():
    return AdvancedReranker(colbert_available=True)


@pytest.fixture
def sample_channel_results():
    return {
        "vector": [
            ScoredDoc(doc_id="v1", text="GDIT works on DCGS-A at Langley.", score=0.9),
            ScoredDoc(doc_id="v2", text="Leidos has a contract for NGEN.", score=0.8),
            ScoredDoc(doc_id="v3", text="SAIC provides ISR solutions.", score=0.7),
        ],
        "bm25": [
            ScoredDoc(doc_id="b1", text="DCGS-A program is managed by GDIT.", score=0.85),
            ScoredDoc(doc_id="v1", text="GDIT works on DCGS-A at Langley.", score=0.8),
            ScoredDoc(doc_id="b2", text="Hiring 5 analysts for DCGS.", score=0.75),
        ],
    }


# =========================================
# SIMILARITY HELPERS
# =========================================

def test_cosine_similarity_identical():
    vec = [1.0, 0.0, 0.5]
    assert _cosine_similarity(vec, vec) == pytest.approx(1.0, abs=0.001)


def test_cosine_similarity_orthogonal():
    a = [1.0, 0.0]
    b = [0.0, 1.0]
    assert _cosine_similarity(a, b) == pytest.approx(0.0, abs=0.001)


def test_cosine_similarity_empty():
    assert _cosine_similarity([], []) == 0.0


def test_token_embeddings():
    embeddings = _token_embeddings("hello world")
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 32


def test_text_embedding():
    emb = _text_embedding("hello world")
    assert len(emb) == 32
    # Should be normalized (unit vector)
    import math
    norm = math.sqrt(sum(v * v for v in emb))
    assert norm == pytest.approx(1.0, abs=0.01)


def test_token_overlap_score():
    score = _token_overlap_score("DCGS program", "DCGS-A program status update")
    assert score > 0.0


def test_token_overlap_score_no_match():
    score = _token_overlap_score("hello world", "completely different")
    assert score == 0.0


# =========================================
# RRF FUSION
# =========================================

@pytest.mark.asyncio
async def test_fuse_rankings(reranker, sample_channel_results):
    fused = await reranker.fuse_rankings(sample_channel_results)
    assert len(fused) >= 3  # At least 3 unique docs
    # v1 appears in both channels, should have highest score
    v1_doc = next((d for d in fused if d.doc_id == "v1"), None)
    assert v1_doc is not None
    assert v1_doc.score > 0


@pytest.mark.asyncio
async def test_fuse_rankings_empty(reranker):
    fused = await reranker.fuse_rankings({})
    assert fused == []


@pytest.mark.asyncio
async def test_fuse_rankings_single_channel(reranker):
    results = {"vector": [ScoredDoc(doc_id="d1", text="test", score=0.9)]}
    fused = await reranker.fuse_rankings(results)
    assert len(fused) == 1


# =========================================
# CROSS-ENCODER
# =========================================

@pytest.mark.asyncio
async def test_cross_encode(reranker):
    scores = await reranker.cross_encode(
        "DCGS program at GDIT",
        ["GDIT manages the DCGS-A program.", "Weather is sunny today."],
    )
    assert len(scores) == 2
    assert scores[0] > scores[1]  # DCGS text should score higher


@pytest.mark.asyncio
async def test_cross_encode_empty(reranker):
    scores = await reranker.cross_encode("test", [])
    assert scores == []


# =========================================
# COLBERT
# =========================================

@pytest.mark.asyncio
async def test_colbert_rerank(reranker):
    scores = await reranker.colbert_rerank(
        "DCGS program",
        ["DCGS-A program at Langley.", "Weather forecast for today."],
    )
    assert len(scores) == 2
    assert scores[0] > scores[1]


@pytest.mark.asyncio
async def test_colbert_rerank_empty(reranker):
    scores = await reranker.colbert_rerank("test", [])
    assert scores == []


# =========================================
# MMR DIVERSITY
# =========================================

@pytest.mark.asyncio
async def test_diversify(reranker):
    docs = [
        ScoredDoc(doc_id="d1", text="DCGS-A program details.", score=0.9),
        ScoredDoc(doc_id="d2", text="DCGS-A program overview.", score=0.85),
        ScoredDoc(doc_id="d3", text="NGEN contract information.", score=0.8),
    ]
    diversified = await reranker.diversify(docs)
    assert len(diversified) == 3
    # First doc should still be the highest scored
    assert diversified[0].doc_id == "d1"


@pytest.mark.asyncio
async def test_diversify_empty(reranker):
    diversified = await reranker.diversify([])
    assert diversified == []


# =========================================
# FULL PIPELINE
# =========================================

@pytest.mark.asyncio
async def test_full_rerank(reranker, sample_channel_results):
    result = await reranker.full_rerank("DCGS program at GDIT", sample_channel_results, top_k=3)
    assert isinstance(result, RerankResult)
    assert len(result.docs) <= 3
    assert "rrf_fusion" in result.stages_applied
    assert "cross_encoder" in result.stages_applied
    assert "mmr_diversity" in result.stages_applied
    assert result.latency_ms >= 0


@pytest.mark.asyncio
async def test_full_rerank_with_colbert(colbert_reranker, sample_channel_results):
    result = await colbert_reranker.full_rerank("DCGS", sample_channel_results, top_k=5)
    assert "colbert" in result.stages_applied


@pytest.mark.asyncio
async def test_full_rerank_empty(reranker):
    result = await reranker.full_rerank("test", {}, top_k=5)
    assert result.output_count == 0


# =========================================
# SINGLETON
# =========================================

def test_get_reranker_singleton():
    r1 = get_reranker()
    r2 = get_reranker()
    assert r1 is r2
