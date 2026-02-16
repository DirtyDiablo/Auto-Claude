"""Phase 40A — Advanced Reranker with ColBERT + Hybrid Fusion

Multi-stage reranking pipeline: Reciprocal Rank Fusion → Cross-encoder →
ColBERT late interaction → Maximal Marginal Relevance diversity filtering.
"""

import logging
import math
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# DATA CLASSES
# =========================================


@dataclass
class ScoredDoc:
    """A document with a relevance score."""

    doc_id: str = ""
    text: str = ""
    score: float = 0.0
    source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RerankResult:
    """Result of the full reranking pipeline."""

    docs: List[ScoredDoc] = field(default_factory=list)
    stages_applied: List[str] = field(default_factory=list)
    latency_ms: float = 0.0
    input_count: int = 0
    output_count: int = 0


# =========================================
# SIMILARITY HELPERS
# =========================================


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _token_embeddings(text: str) -> List[List[float]]:
    """Lightweight per-token embedding (character-level hash vectors).

    This is a fast fallback when no real embedding model is available.
    In production, this would use ColBERT or sentence-transformers.
    """
    tokens = re.findall(r"\b\w+\b", text.lower())
    embeddings = []
    for token in tokens[:50]:  # Limit tokens
        # Simple character-based hash → 32-dim vector
        vec = [0.0] * 32
        for i, ch in enumerate(token):
            vec[ord(ch) % 32] += 1.0 / (i + 1)
        # Normalize
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        vec = [v / norm for v in vec]
        embeddings.append(vec)
    return embeddings


def _text_embedding(text: str) -> List[float]:
    """Simple bag-of-characters embedding for text (fallback)."""
    vec = [0.0] * 32
    tokens = re.findall(r"\b\w+\b", text.lower())
    for token in tokens:
        for i, ch in enumerate(token):
            vec[ord(ch) % 32] += 1.0 / (i + 1)
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _token_overlap_score(query: str, doc: str) -> float:
    """Compute token overlap relevance."""
    q_tokens = set(re.findall(r"\b\w+\b", query.lower()))
    d_tokens = set(re.findall(r"\b\w+\b", doc.lower()))
    stopwords = {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "and",
        "or",
        "but",
        "not",
        "this",
        "that",
        "it",
    }
    q_tokens -= stopwords
    d_tokens -= stopwords
    if not q_tokens:
        return 0.0
    return len(q_tokens & d_tokens) / len(q_tokens)


# =========================================
# ADVANCED RERANKER
# =========================================


class AdvancedReranker:
    """Multi-stage reranking pipeline: RRF → Cross-encoder → ColBERT → MMR."""

    def __init__(
        self,
        cross_encoder_fn: Optional[Callable] = None,
        colbert_fn: Optional[Callable] = None,
        embedding_fn: Optional[Callable] = None,
        rrf_k: int = 60,
        mmr_lambda: float = 0.5,
        cross_encoder_available: bool = False,
        colbert_available: bool = False,
    ):
        self._cross_encoder_fn = cross_encoder_fn
        self._colbert_fn = colbert_fn
        self._embedding_fn = embedding_fn
        self.rrf_k = rrf_k
        self.mmr_lambda = mmr_lambda
        self.cross_encoder_available = cross_encoder_available or (
            cross_encoder_fn is not None
        )
        self.colbert_available = colbert_available or (colbert_fn is not None)

    # -----------------------------------------
    # Stage 1: Reciprocal Rank Fusion
    # -----------------------------------------

    async def fuse_rankings(
        self,
        channel_results: Dict[str, List[ScoredDoc]],
    ) -> List[ScoredDoc]:
        """Reciprocal Rank Fusion across multiple retrieval channels.

        RRF score = Σ 1/(k + rank_i) for each channel where doc appears.
        k=60 is the standard constant (reduces impact of outlier rankings).
        """
        doc_scores: Dict[str, float] = {}
        doc_map: Dict[str, ScoredDoc] = {}

        for channel, docs in channel_results.items():
            for rank, doc in enumerate(docs):
                key = doc.doc_id or doc.text[:100]
                rrf_score = 1.0 / (self.rrf_k + rank + 1)  # +1 for 0-indexed

                if key in doc_scores:
                    doc_scores[key] += rrf_score
                else:
                    doc_scores[key] = rrf_score
                    doc_map[key] = ScoredDoc(
                        doc_id=doc.doc_id,
                        text=doc.text,
                        score=0.0,
                        source=f"{channel}+{doc.source}" if doc.source else channel,
                        metadata={**doc.metadata, "channels": [channel]},
                    )

                # Track which channels contributed
                channels = doc_map[key].metadata.get("channels", [])
                if channel not in channels:
                    channels.append(channel)
                    doc_map[key].metadata["channels"] = channels

        # Set fused scores
        for key, score in doc_scores.items():
            doc_map[key].score = round(score, 6)

        # Sort by fused score
        fused = sorted(doc_map.values(), key=lambda d: d.score, reverse=True)
        return fused

    # -----------------------------------------
    # Stage 2: Cross-encoder reranking
    # -----------------------------------------

    async def cross_encode(
        self,
        query: str,
        docs: List[str],
    ) -> List[float]:
        """Cross-encoder scoring (BGE-reranker-v2-m3 or fallback).

        Cross-encoders process (query, doc) pairs jointly with full attention,
        giving much better relevance scores than bi-encoder similarity.
        """
        if self._cross_encoder_fn:
            try:
                return await self._cross_encoder_fn(query, docs)
            except Exception as e:
                logger.warning(f"Cross-encoder failed, using fallback: {e}")

        # Fallback: token overlap + embedding similarity
        scores = []
        q_emb = _text_embedding(query)
        for doc in docs:
            token_score = _token_overlap_score(query, doc)
            emb_score = _cosine_similarity(q_emb, _text_embedding(doc))
            # Weighted combination
            combined = token_score * 0.6 + emb_score * 0.4
            scores.append(round(combined, 4))
        return scores

    # -----------------------------------------
    # Stage 3: ColBERT late interaction
    # -----------------------------------------

    async def colbert_rerank(
        self,
        query: str,
        docs: List[str],
    ) -> List[float]:
        """ColBERT late interaction reranking.

        ColBERT computes per-token embeddings for query and document,
        then uses MaxSim: for each query token, find the max similarity
        to any document token, then sum across query tokens.
        """
        if self._colbert_fn:
            try:
                return await self._colbert_fn(query, docs)
            except Exception as e:
                logger.warning(f"ColBERT failed, using fallback: {e}")

        # Fallback: MaxSim with character-hash token embeddings
        q_tokens = _token_embeddings(query)
        if not q_tokens:
            return [0.0] * len(docs)

        scores = []
        for doc in docs:
            d_tokens = _token_embeddings(doc)
            if not d_tokens:
                scores.append(0.0)
                continue

            # MaxSim: for each query token, find max similarity to any doc token
            total = 0.0
            for q_emb in q_tokens:
                max_sim = max(_cosine_similarity(q_emb, d_emb) for d_emb in d_tokens)
                total += max_sim

            # Normalize by number of query tokens
            score = total / len(q_tokens)
            scores.append(round(score, 4))

        return scores

    # -----------------------------------------
    # Stage 4: Maximal Marginal Relevance
    # -----------------------------------------

    async def diversify(
        self,
        docs: List[ScoredDoc],
        lambda_param: Optional[float] = None,
    ) -> List[ScoredDoc]:
        """Maximal Marginal Relevance for result diversity.

        MMR = λ * relevance(d) - (1-λ) * max_sim(d, selected)
        Balances relevance with diversity to avoid redundant results.
        """
        lam = lambda_param if lambda_param is not None else self.mmr_lambda
        if not docs:
            return []

        # Compute embeddings for all docs
        embeddings = [_text_embedding(d.text) for d in docs]

        selected: List[int] = []
        remaining = list(range(len(docs)))

        # Always pick the highest-scored doc first
        selected.append(remaining.pop(0))

        while remaining and len(selected) < len(docs):
            best_idx = -1
            best_mmr = -float("inf")

            for idx in remaining:
                relevance = docs[idx].score

                # Max similarity to already selected docs
                max_sim = 0.0
                for sel_idx in selected:
                    sim = _cosine_similarity(embeddings[idx], embeddings[sel_idx])
                    max_sim = max(max_sim, sim)

                mmr = lam * relevance - (1 - lam) * max_sim
                if mmr > best_mmr:
                    best_mmr = mmr
                    best_idx = idx

            if best_idx >= 0:
                selected.append(best_idx)
                remaining.remove(best_idx)
            else:
                break

        return [docs[i] for i in selected]

    # -----------------------------------------
    # Full pipeline
    # -----------------------------------------

    async def full_rerank(
        self,
        query: str,
        channel_results: Dict[str, List[ScoredDoc]],
        top_k: int = 10,
    ) -> RerankResult:
        """Full pipeline: fuse → cross-encode → (colbert) → diversify → top_k."""
        start = time.time()
        stages = []

        # Stage 1: RRF fusion
        fused = await self.fuse_rankings(channel_results)
        stages.append("rrf_fusion")
        input_count = sum(len(docs) for docs in channel_results.values())

        if not fused:
            return RerankResult(
                stages_applied=stages,
                latency_ms=round((time.time() - start) * 1000, 2),
                input_count=input_count,
                output_count=0,
            )

        # Stage 2: Cross-encoder reranking
        doc_texts = [d.text for d in fused[:50]]  # Limit to top 50 for efficiency
        ce_scores = await self.cross_encode(query, doc_texts)
        for i, score in enumerate(ce_scores):
            if i < len(fused):
                # Blend RRF and cross-encoder scores
                fused[i].score = round(fused[i].score * 0.3 + score * 0.7, 4)
        fused.sort(key=lambda d: d.score, reverse=True)
        stages.append("cross_encoder")

        # Stage 3: ColBERT (if available)
        if self.colbert_available:
            colbert_scores = await self.colbert_rerank(query, doc_texts[:30])
            for i, score in enumerate(colbert_scores):
                if i < len(fused):
                    fused[i].score = round(fused[i].score * 0.6 + score * 0.4, 4)
            fused.sort(key=lambda d: d.score, reverse=True)
            stages.append("colbert")

        # Stage 4: MMR diversity
        diversified = await self.diversify(fused[: top_k * 2])
        stages.append("mmr_diversity")

        elapsed = (time.time() - start) * 1000
        return RerankResult(
            docs=diversified[:top_k],
            stages_applied=stages,
            latency_ms=round(elapsed, 2),
            input_count=input_count,
            output_count=min(top_k, len(diversified)),
        )


# =========================================
# SINGLETON
# =========================================

_reranker: Optional[AdvancedReranker] = None


def get_reranker() -> AdvancedReranker:
    global _reranker
    if _reranker is None:
        _reranker = AdvancedReranker()
    return _reranker
