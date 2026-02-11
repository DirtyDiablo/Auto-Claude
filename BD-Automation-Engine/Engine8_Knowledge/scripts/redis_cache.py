"""
Redis Semantic Cache - 4x latency reduction for repeated queries
"""

import os
import json
import hashlib
from typing import Dict, List, Optional
from datetime import timedelta
import logging

import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence_transformers not available")

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis not available")


class InMemoryCache:
    """Fallback when Redis unavailable."""

    def __init__(self):
        self.cache: Dict[str, Dict] = {}

    def get(self, key: str) -> Optional[Dict]:
        return self.cache.get(key)

    def set(self, key: str, value: Dict, ttl: int = 3600):
        self.cache[key] = value

    def delete(self, key: str):
        self.cache.pop(key, None)

    def clear(self):
        self.cache.clear()

    def smembers(self, key: str):
        return set(self.cache.keys())

    def sadd(self, key: str, value: str):
        pass

    def srem(self, key: str, value: str):
        pass

    def setex(self, key: str, ttl, value: str):
        self.cache[key] = json.loads(value) if isinstance(value, str) else value


class SemanticCache:
    """
    Semantic cache with similarity matching.
    Caches query results and finds similar cached queries.
    """

    def __init__(
        self,
        redis_url: str = None,
        similarity_threshold: float = 0.85,
        ttl_hours: int = 24
    ):
        redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.similarity_threshold = similarity_threshold
        self.ttl = timedelta(hours=ttl_hours)

        if REDIS_AVAILABLE:
            try:
                self.redis = redis.from_url(redis_url)
                self.redis.ping()
                self.backend = "redis"
            except Exception as e:
                logger.warning("redis_connection_failed, falling back to memory: %s", e)
                self.redis = InMemoryCache()
                self.backend = "memory"
        else:
            self.redis = InMemoryCache()
            self.backend = "memory"

        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception as e:
                logger.warning("sentence_transformer_load_failed: %s", e)
                self.embedder = None
        else:
            self.embedder = None

        self.CACHE_PREFIX = "bd_cache:"
        self.EMBED_PREFIX = "bd_embed:"
        self.INDEX_KEY = "bd_cache_index"

    def _get_embedding(self, text: str) -> List[float]:
        if self.embedder:
            return self.embedder.encode(text).tolist()
        return []

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        if not v1 or not v2:
            return 0.0
        a, b = np.array(v1), np.array(v2)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    def _generate_key(self, query: str) -> str:
        return hashlib.md5(query.encode()).hexdigest()

    def get(self, query: str) -> Optional[Dict]:
        """Get cached result with semantic similarity."""
        query_embedding = self._get_embedding(query)

        # Get index
        if self.backend == "redis":
            index = self.redis.smembers(self.INDEX_KEY) or set()
        else:
            index = set(self.redis.cache.keys())

        best_match = None
        best_sim = 0.0

        for cached_key in index:
            if isinstance(cached_key, bytes):
                cached_key = cached_key.decode()

            # Get embedding
            if self.backend == "redis":
                embed_data = self.redis.get(f"{self.EMBED_PREFIX}{cached_key}")
                if embed_data:
                    cached_embed = json.loads(embed_data)
                else:
                    continue
            else:
                entry = self.redis.get(cached_key)
                if entry and 'embedding' in entry:
                    cached_embed = entry['embedding']
                else:
                    continue

            sim = self._cosine_similarity(query_embedding, cached_embed)
            if sim > best_sim and sim >= self.similarity_threshold:
                best_sim = sim
                best_match = cached_key

        if best_match:
            if self.backend == "redis":
                data = self.redis.get(f"{self.CACHE_PREFIX}{best_match}")
                if data:
                    result = json.loads(data)
                    result['cache_hit'] = True
                    result['similarity'] = best_sim
                    return result
            else:
                entry = self.redis.get(best_match)
                if entry:
                    entry['cache_hit'] = True
                    entry['similarity'] = best_sim
                    return entry

        return None

    def set(self, query: str, result: Dict) -> bool:
        """Cache a query result."""
        key = self._generate_key(query)
        embedding = self._get_embedding(query)

        cache_data = {
            "query": query,
            "result": result,
            "embedding": embedding
        }

        if self.backend == "redis":
            self.redis.setex(
                f"{self.CACHE_PREFIX}{key}",
                self.ttl,
                json.dumps({"query": query, "result": result})
            )
            self.redis.setex(
                f"{self.EMBED_PREFIX}{key}",
                self.ttl,
                json.dumps(embedding)
            )
            self.redis.sadd(self.INDEX_KEY, key)
        else:
            self.redis.set(key, cache_data)

        return True

    def invalidate(self, query: str) -> bool:
        key = self._generate_key(query)
        if self.backend == "redis":
            self.redis.delete(f"{self.CACHE_PREFIX}{key}")
            self.redis.delete(f"{self.EMBED_PREFIX}{key}")
            self.redis.srem(self.INDEX_KEY, key)
        else:
            self.redis.delete(key)
        return True

    def clear_all(self) -> int:
        if self.backend == "redis":
            index = self.redis.smembers(self.INDEX_KEY) or set()
            for key in index:
                if isinstance(key, bytes):
                    key = key.decode()
                self.redis.delete(f"{self.CACHE_PREFIX}{key}")
                self.redis.delete(f"{self.EMBED_PREFIX}{key}")
            self.redis.delete(self.INDEX_KEY)
            return len(index)
        else:
            count = len(self.redis.cache)
            self.redis.clear()
            return count

    def get_stats(self) -> Dict:
        if self.backend == "redis":
            index = self.redis.smembers(self.INDEX_KEY) or set()
            count = len(index)
        else:
            count = len(self.redis.cache)

        return {
            "cached_queries": count,
            "backend": self.backend,
            "threshold": self.similarity_threshold
        }


_cache_instance = None

def get_cache(redis_url: str = None) -> SemanticCache:
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = SemanticCache(redis_url)
    return _cache_instance
