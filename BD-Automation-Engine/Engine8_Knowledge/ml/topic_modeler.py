"""Phase 28A — BERTopic Topic Modeler

BERTopic clustering for discovering hidden program clusters and hiring trends
across job postings, call notes, and BD documents.
"""

import structlog
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = structlog.get_logger(__name__)


@dataclass
class TopicInfo:
    topic_id: int
    name: str
    keywords: List[str]
    size: int
    representative_docs: List[str] = field(default_factory=list)


@dataclass
class TopicResult:
    topics: List[TopicInfo]
    total_documents: int
    total_topics: int
    outlier_count: int = 0
    model_type: str = "bertopic"


@dataclass
class TopicTrend:
    topic_id: int
    topic_name: str
    data_points: List[Dict]  # [{date, count}]
    trend: str = "stable"  # growing, declining, stable


class TopicModeler:
    """BERTopic-based topic modeler with keyword-clustering fallback.

    Clusters documents into coherent topics to surface hidden hiring trends,
    program groupings, and recurring themes in BD activity notes.
    """

    def __init__(self):
        self._model = None
        self._topic_cache: Dict[str, List[TopicInfo]] = {}
        self._initialize()

    def _initialize(self):
        """Attempt to load BERTopic; fall back to keyword clustering if unavailable."""
        try:
            from bertopic import BERTopic

            self._model = BERTopic(
                language="english",
                min_topic_size=3,
                nr_topics="auto",
            )
            logger.info("bertopic_initialized")
        except ImportError:
            logger.warning("bertopic_not_installed", fallback="keyword_clustering")
            self._model = None

    # ------------------------------------------------------------------
    # Public clustering methods
    # ------------------------------------------------------------------

    async def cluster_jobs(
        self, documents: Optional[List[str]] = None, days: int = 90
    ) -> TopicResult:
        """Cluster job posting texts into topics.

        Args:
            documents: List of job description strings.
            days: Lookback window (for future time-filtered queries).

        Returns:
            TopicResult with discovered topics.
        """
        if not documents:
            documents = []
        return await self._cluster(documents, "jobs")

    async def cluster_notes(
        self, documents: Optional[List[str]] = None, days: int = 180
    ) -> TopicResult:
        """Cluster call/meeting notes into topics.

        Args:
            documents: List of note text strings.
            days: Lookback window (for future time-filtered queries).

        Returns:
            TopicResult with discovered topics.
        """
        if not documents:
            documents = []
        return await self._cluster(documents, "notes")

    async def cluster_documents(
        self, documents: Optional[List[str]] = None, doc_type: str = "all"
    ) -> TopicResult:
        """Cluster arbitrary documents into topics.

        Args:
            documents: List of document text strings.
            doc_type: Category label for caching.

        Returns:
            TopicResult with discovered topics.
        """
        if not documents:
            documents = []
        return await self._cluster(documents, doc_type)

    # ------------------------------------------------------------------
    # Core clustering
    # ------------------------------------------------------------------

    async def _cluster(self, documents: List[str], source: str) -> TopicResult:
        """Run clustering via BERTopic or keyword fallback."""
        if not documents:
            return TopicResult(topics=[], total_documents=0, total_topics=0)

        if not self._model:
            return self._keyword_cluster(documents, source)

        try:
            topics, probs = self._model.fit_transform(documents)
            topic_info = self._model.get_topic_info()

            result_topics: List[TopicInfo] = []
            for _, row in topic_info.iterrows():
                tid = row["Topic"]
                if tid == -1:
                    continue

                keywords = [w for w, _ in self._model.get_topic(tid)][:10]
                rep_docs: List[str] = []
                if hasattr(self._model, "get_representative_docs"):
                    try:
                        rep_docs = self._model.get_representative_docs(tid)[:3]
                    except Exception:
                        rep_docs = []

                result_topics.append(
                    TopicInfo(
                        topic_id=tid,
                        name=f"Topic_{tid}",
                        keywords=keywords,
                        size=row["Count"],
                        representative_docs=rep_docs,
                    )
                )

            outliers = sum(1 for t in topics if t == -1)
            self._topic_cache[source] = result_topics

            logger.info(
                "clustering_complete",
                source=source,
                topics=len(result_topics),
                docs=len(documents),
                outliers=outliers,
            )

            return TopicResult(
                topics=result_topics,
                total_documents=len(documents),
                total_topics=len(result_topics),
                outlier_count=outliers,
            )
        except Exception as e:
            logger.error("clustering_error", error=str(e), source=source)
            return self._keyword_cluster(documents, source)

    def _keyword_cluster(self, documents: List[str], source: str) -> TopicResult:
        """Simple TF-IDF-like keyword extraction fallback when BERTopic is unavailable."""
        word_freq: Counter = Counter()
        for doc in documents:
            words = doc.lower().split()
            word_freq.update(w for w in words if len(w) > 3)

        top_keywords = [w for w, _ in word_freq.most_common(20)]

        clusters: Dict[str, List[str]] = {}
        for doc in documents:
            matched = False
            for kw in top_keywords[:5]:
                if kw in doc.lower():
                    clusters.setdefault(kw, []).append(doc)
                    matched = True
                    break
            if not matched:
                clusters.setdefault("other", []).append(doc)

        topics: List[TopicInfo] = []
        for tid, (name, docs) in enumerate(clusters.items()):
            topics.append(
                TopicInfo(
                    topic_id=tid,
                    name=name,
                    keywords=[name],
                    size=len(docs),
                    representative_docs=docs[:3],
                )
            )

        self._topic_cache[source] = topics

        logger.info(
            "keyword_clustering_complete",
            source=source,
            topics=len(topics),
            docs=len(documents),
        )

        return TopicResult(
            topics=topics,
            total_documents=len(documents),
            total_topics=len(topics),
            model_type="keyword_fallback",
        )

    # ------------------------------------------------------------------
    # Topic queries
    # ------------------------------------------------------------------

    async def get_topic_trends(self, topic_id: int, days: int = 90) -> TopicTrend:
        """Retrieve temporal trend data for a specific topic.

        Args:
            topic_id: The numeric topic identifier.
            days: Lookback window in days.

        Returns:
            TopicTrend with data points and trend direction.
        """
        for _source, topics in self._topic_cache.items():
            for t in topics:
                if t.topic_id == topic_id:
                    return TopicTrend(
                        topic_id=topic_id,
                        topic_name=t.name,
                        data_points=[],
                        trend="stable",
                    )
        return TopicTrend(
            topic_id=topic_id,
            topic_name="Unknown",
            data_points=[],
            trend="stable",
        )

    async def find_similar_items(self, text: str, top_k: int = 10) -> List[Dict]:
        """Find topics most similar to the given text.

        Args:
            text: Query text to match against discovered topics.
            top_k: Number of similar topics to return.

        Returns:
            List of dicts with topic_id and similarity score.
        """
        if not self._model:
            return []
        try:
            similar = self._model.find_topics(text, top_n=top_k)
            return [
                {"topic_id": t, "score": float(s)}
                for t, s in zip(similar[0], similar[1])
            ]
        except Exception:
            return []

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict:
        """Return modeler status and cache statistics."""
        return {
            "has_model": self._model is not None,
            "cached_sources": list(self._topic_cache.keys()),
            "total_cached_topics": sum(len(v) for v in self._topic_cache.values()),
        }


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_modeler: Optional[TopicModeler] = None


def get_topic_modeler() -> TopicModeler:
    """Return a module-level singleton TopicModeler instance."""
    global _modeler
    if _modeler is None:
        _modeler = TopicModeler()
    return _modeler
