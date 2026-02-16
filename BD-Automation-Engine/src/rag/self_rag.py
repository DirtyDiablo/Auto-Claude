"""Phase 40A — Self-Reflective RAG (Self-RAG)

Implements the Self-RAG pattern: retrieve, evaluate relevance, decide if more
retrieval is needed, and only generate answers from supported passages.
"""

import logging
import re
import time
import uuid
from dataclasses import dataclass, field
from typing import Callable, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# DATA CLASSES
# =========================================


@dataclass
class RelevanceScore:
    """Relevance score for a passage against a query."""

    passage_index: int = 0
    passage_text: str = ""
    score: float = 0.0
    relevant: bool = False
    explanation: str = ""


@dataclass
class SupportScore:
    """Whether an answer is supported by the given passages."""

    score: float = 0.0  # 0-1, 1 = fully supported
    supported: bool = False
    unsupported_claims: List[str] = field(default_factory=list)
    explanation: str = ""


@dataclass
class UtilityScore:
    """Whether an answer is useful for the given query."""

    score: float = 0.0  # 0-1, 1 = fully useful
    useful: bool = False
    explanation: str = ""


@dataclass
class RetrievalRound:
    """Record of a single retrieval round."""

    round_number: int = 0
    query_used: str = ""
    passages_retrieved: int = 0
    passages_relevant: int = 0
    avg_relevance: float = 0.0
    latency_ms: float = 0.0


@dataclass
class SelfRAGResult:
    """Complete result from the Self-RAG pipeline."""

    query_id: str = ""
    answer: str = ""
    confidence: float = 0.0
    relevance_scores: List[RelevanceScore] = field(default_factory=list)
    support_score: Optional[SupportScore] = None
    utility_score: Optional[UtilityScore] = None
    rounds: List[RetrievalRound] = field(default_factory=list)
    total_passages_retrieved: int = 0
    relevant_passages_used: int = 0
    retrieval_needed: bool = True
    latency_ms: float = 0.0


# =========================================
# RELEVANCE EVALUATION
# =========================================


def _compute_token_overlap(query: str, text: str) -> float:
    """Compute normalized token overlap between query and text."""
    if not query or not text:
        return 0.0
    q_tokens = set(re.findall(r"\b\w+\b", query.lower()))
    t_tokens = set(re.findall(r"\b\w+\b", text.lower()))
    # Remove stopwords
    stopwords = {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "and",
        "or",
        "but",
        "not",
        "this",
        "that",
        "it",
        "i",
        "you",
        "we",
        "they",
        "he",
        "she",
        "what",
        "who",
        "how",
        "which",
        "do",
        "does",
        "did",
        "has",
        "have",
        "had",
    }
    q_tokens -= stopwords
    t_tokens -= stopwords
    if not q_tokens:
        return 0.0
    overlap = q_tokens & t_tokens
    return len(overlap) / len(q_tokens)


def _compute_entity_overlap(query: str, text: str) -> float:
    """Check if named entities from query appear in text."""
    # Extract capitalized words/phrases as potential entities
    q_entities = set(re.findall(r"\b[A-Z][a-zA-Z-]+(?:\s+[A-Z][a-zA-Z-]+)*\b", query))
    if not q_entities:
        return 1.0  # No entities to check
    found = 0
    text_lower = text.lower()
    for e in q_entities:
        if e.lower() in text_lower:
            found += 1
    return found / len(q_entities) if q_entities else 1.0


def _assess_retrieval_need(query: str) -> bool:
    """Decide if retrieval is needed for this query."""
    # Queries that likely don't need retrieval (greetings, simple math, etc.)
    no_retrieval_patterns = [
        re.compile(r"^(hi|hello|hey|thanks|thank you)\b", re.IGNORECASE),
        re.compile(r"^\d+\s*[+\-*/]\s*\d+", re.IGNORECASE),
        re.compile(r"^(what is|define)\s+(the meaning|the definition)", re.IGNORECASE),
    ]
    for p in no_retrieval_patterns:
        if p.search(query.strip()):
            return False
    return True


# =========================================
# QUERY REFORMULATION
# =========================================


def reformulate_query(original: str, gaps: List[str], round_num: int) -> str:
    """Reformulate query to address retrieval gaps."""
    # Strategy 1: Add entity emphasis
    entities = re.findall(r"\b[A-Z][a-zA-Z-]+(?:\s+[A-Z][a-zA-Z-]+)*\b", original)

    if round_num == 2:
        # Make query more specific by emphasizing entities
        if entities:
            return f"{original} specifically regarding {', '.join(entities[:3])}"
        return f"{original} detailed information"

    if round_num >= 3:
        # Broaden the query
        # Remove very specific terms and search more broadly
        broader = re.sub(
            r"\b(specific|exactly|precisely|only)\b", "", original, flags=re.IGNORECASE
        )
        return broader.strip() or original

    return original


# =========================================
# SELF-REFLECTIVE RAG
# =========================================


class SelfReflectiveRAG:
    """Self-RAG: retrieve, evaluate, decide if more retrieval is needed."""

    def __init__(
        self,
        retrieval_fn: Optional[Callable] = None,
        relevance_threshold: float = 0.5,
        support_threshold: float = 0.6,
        utility_threshold: float = 0.5,
        max_rounds: int = 3,
    ):
        self._retrieval_fn = retrieval_fn
        self.relevance_threshold = relevance_threshold
        self.support_threshold = support_threshold
        self.utility_threshold = utility_threshold
        self.max_rounds = max_rounds
        self._history: List[SelfRAGResult] = []

    # -----------------------------------------
    # Evaluation methods
    # -----------------------------------------

    async def evaluate_relevance(
        self,
        query: str,
        passages: List[str],
    ) -> List[RelevanceScore]:
        """Score each passage for relevance to the query."""
        scores = []
        for i, passage in enumerate(passages):
            token_score = _compute_token_overlap(query, passage)
            entity_score = _compute_entity_overlap(query, passage)

            # Weight: 60% token overlap, 40% entity coverage
            combined = token_score * 0.6 + entity_score * 0.4

            # Bonus for longer passages (more likely to contain useful info)
            length_bonus = min(len(passage) / 500, 0.1)
            combined = min(combined + length_bonus, 1.0)

            scores.append(
                RelevanceScore(
                    passage_index=i,
                    passage_text=passage[:200],
                    score=round(combined, 4),
                    relevant=combined >= self.relevance_threshold,
                    explanation=f"token_overlap={token_score:.2f}, entity_overlap={entity_score:.2f}",
                )
            )
        return scores

    async def evaluate_support(
        self,
        answer: str,
        passages: List[str],
    ) -> SupportScore:
        """Check if the answer is supported by the passages."""
        if not answer or not passages:
            return SupportScore(
                score=0.0, supported=False, explanation="No answer or passages"
            )

        # Extract claims from answer (sentences)
        claims = [s.strip() for s in re.split(r"[.!?]+", answer) if len(s.strip()) > 10]
        if not claims:
            return SupportScore(
                score=1.0, supported=True, explanation="No verifiable claims"
            )

        all_passage_text = " ".join(passages).lower()
        supported_claims = 0
        unsupported = []

        for claim in claims:
            # Check if key terms from the claim appear in passages
            claim_tokens = set(re.findall(r"\b\w{3,}\b", claim.lower()))
            stopwords = {
                "the",
                "and",
                "for",
                "are",
                "was",
                "with",
                "this",
                "that",
                "from",
            }
            claim_tokens -= stopwords

            if not claim_tokens:
                supported_claims += 1
                continue

            passage_tokens = set(re.findall(r"\b\w{3,}\b", all_passage_text))
            overlap = claim_tokens & passage_tokens
            coverage = len(overlap) / len(claim_tokens) if claim_tokens else 0

            if coverage >= 0.5:
                supported_claims += 1
            else:
                unsupported.append(claim[:100])

        support_ratio = supported_claims / len(claims) if claims else 0.0

        return SupportScore(
            score=round(support_ratio, 4),
            supported=support_ratio >= self.support_threshold,
            unsupported_claims=unsupported,
            explanation=f"{supported_claims}/{len(claims)} claims supported",
        )

    async def evaluate_utility(
        self,
        query: str,
        answer: str,
    ) -> UtilityScore:
        """Score how useful the answer is for the query."""
        if not answer or not query:
            return UtilityScore(
                score=0.0, useful=False, explanation="Empty query or answer"
            )

        # Check if answer addresses query entities
        entity_coverage = _compute_entity_overlap(query, answer)

        # Check if answer is substantive (not just "I don't know")
        negative_patterns = [
            re.compile(
                r"\b(cannot|could not|don\'t know|no information|not found)\b",
                re.IGNORECASE,
            ),
            re.compile(r"\b(insufficient|unavailable|unable to)\b", re.IGNORECASE),
        ]
        is_negative = any(p.search(answer) for p in negative_patterns)
        substance_score = 0.2 if is_negative else min(len(answer) / 200, 1.0)

        # Token overlap between query and answer
        token_overlap = _compute_token_overlap(query, answer)

        # Combined utility: 40% entity, 40% substance, 20% token overlap
        utility = entity_coverage * 0.4 + substance_score * 0.4 + token_overlap * 0.2

        return UtilityScore(
            score=round(utility, 4),
            useful=utility >= self.utility_threshold,
            explanation=f"entity={entity_coverage:.2f}, substance={substance_score:.2f}, overlap={token_overlap:.2f}",
        )

    # -----------------------------------------
    # Retrieval
    # -----------------------------------------

    async def _retrieve(self, query: str, limit: int = 10) -> List[str]:
        """Execute retrieval using the configured function."""
        if self._retrieval_fn:
            try:
                results = await self._retrieval_fn(query, limit=limit)
                if isinstance(results, list):
                    return [
                        r.get("text", str(r)) if isinstance(r, dict) else str(r)
                        for r in results
                    ]
                return [str(results)]
            except Exception as e:
                logger.warning(f"Retrieval failed: {e}")
                return []
        return []

    # -----------------------------------------
    # Adaptive retrieval
    # -----------------------------------------

    async def adaptive_retrieve(
        self,
        query: str,
        max_rounds: Optional[int] = None,
    ) -> SelfRAGResult:
        """Full self-reflective retrieval loop."""
        start_time = time.time()
        query_id = uuid.uuid4().hex[:12]
        rounds_limit = max_rounds or self.max_rounds

        # Step 1: Decide if retrieval is needed
        needs_retrieval = _assess_retrieval_need(query)
        if not needs_retrieval:
            return SelfRAGResult(
                query_id=query_id,
                answer="This query does not require information retrieval.",
                confidence=1.0,
                retrieval_needed=False,
                latency_ms=round((time.time() - start_time) * 1000, 2),
            )

        all_relevance_scores: List[RelevanceScore] = []
        relevant_passages: List[str] = []
        rounds: List[RetrievalRound] = []
        current_query = query

        for round_num in range(1, rounds_limit + 1):
            round_start = time.time()

            # Step 2: Retrieve passages
            passages = await self._retrieve(current_query)

            # Step 3: Evaluate relevance
            relevance_scores = await self.evaluate_relevance(query, passages)
            all_relevance_scores.extend(relevance_scores)

            # Filter to relevant passages
            round_relevant = [
                passages[s.passage_index]
                for s in relevance_scores
                if s.relevant and s.passage_index < len(passages)
            ]
            relevant_passages.extend(round_relevant)

            avg_rel = (
                sum(s.score for s in relevance_scores) / len(relevance_scores)
                if relevance_scores
                else 0.0
            )

            rounds.append(
                RetrievalRound(
                    round_number=round_num,
                    query_used=current_query,
                    passages_retrieved=len(passages),
                    passages_relevant=len(round_relevant),
                    avg_relevance=round(avg_rel, 4),
                    latency_ms=round((time.time() - round_start) * 1000, 2),
                )
            )

            # Step 4: Check if we have enough relevant passages
            if len(relevant_passages) >= 3 and avg_rel >= self.relevance_threshold:
                break

            # Step 5: Reformulate query for next round
            gaps = []
            if avg_rel < self.relevance_threshold:
                gaps.append("low_relevance")
            if len(round_relevant) < 2:
                gaps.append("too_few_relevant")
            current_query = reformulate_query(query, gaps, round_num + 1)

        # Step 6: Generate answer from relevant passages
        if relevant_passages:
            answer = "\n\n".join(relevant_passages[:5])
        else:
            answer = (
                "Could not find sufficiently relevant information to answer this query."
            )

        # Step 7: Evaluate support and utility
        support = await self.evaluate_support(answer, relevant_passages)
        utility = await self.evaluate_utility(query, answer)

        # Compute confidence
        avg_relevance = sum(s.score for s in all_relevance_scores if s.relevant) / max(
            len([s for s in all_relevance_scores if s.relevant]), 1
        )
        confidence = avg_relevance * 0.4 + support.score * 0.3 + utility.score * 0.3

        elapsed_ms = (time.time() - start_time) * 1000

        result = SelfRAGResult(
            query_id=query_id,
            answer=answer,
            confidence=round(confidence, 4),
            relevance_scores=all_relevance_scores,
            support_score=support,
            utility_score=utility,
            rounds=rounds,
            total_passages_retrieved=sum(r.passages_retrieved for r in rounds),
            relevant_passages_used=len(relevant_passages),
            retrieval_needed=True,
            latency_ms=round(elapsed_ms, 2),
        )

        self._history.append(result)
        return result

    def get_history(self) -> List[SelfRAGResult]:
        return self._history


# =========================================
# SINGLETON
# =========================================

_self_rag: Optional[SelfReflectiveRAG] = None


def get_self_rag() -> SelfReflectiveRAG:
    global _self_rag
    if _self_rag is None:
        _self_rag = SelfReflectiveRAG()
    return _self_rag
