"""Phase 57A — Cache Layer Manager.

Multi-tier caching with L1 memory, L2 Redis, L3 disk, and CDN layers.
Supports cascade lookups, eviction policies, and cache warming.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================
# DATA MODELS
# =========================================


class LayerType(Enum):
    L1_MEMORY = "l1_memory"
    L2_REDIS = "l2_redis"
    L3_DISK = "l3_disk"
    CDN = "cdn"


class EvictionPolicy(Enum):
    LRU = "lru"
    LFU = "lfu"
    TTL = "ttl"
    FIFO = "fifo"


@dataclass
class CacheEntry:
    key: str
    value: Any = None
    ttl_seconds: int = 300
    created_at: float = field(default_factory=time.time)
    hits: int = 0
    size_bytes: int = 64

    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.ttl_seconds

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "ttl_seconds": self.ttl_seconds,
            "created_at": self.created_at,
            "hits": self.hits,
            "size_bytes": self.size_bytes,
            "expired": self.is_expired(),
        }


@dataclass
class CacheLayer:
    name: str
    layer_type: LayerType
    max_entries: int = 1000
    current_entries: int = 0
    hit_rate: float = 0.0
    total_hits: int = 0
    total_misses: int = 0
    eviction_policy: EvictionPolicy = EvictionPolicy.LRU
    _entries: Dict[str, CacheEntry] = field(default_factory=dict, repr=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "layer_type": self.layer_type.value,
            "max_entries": self.max_entries,
            "current_entries": self.current_entries,
            "hit_rate": round(self.hit_rate, 4),
            "total_hits": self.total_hits,
            "total_misses": self.total_misses,
            "eviction_policy": self.eviction_policy.value,
        }

    def _update_hit_rate(self) -> None:
        total = self.total_hits + self.total_misses
        self.hit_rate = self.total_hits / total if total > 0 else 0.0


# =========================================
# CACHE LAYER MANAGER
# =========================================


class CacheLayerManager:
    """Multi-tier cache with L1→L2→L3→CDN cascade lookups,
    eviction, invalidation, and bulk warming.
    """

    def __init__(self):
        self._layers: Dict[str, CacheLayer] = {}
        self._layer_order: List[str] = []
        self._register_defaults()
        logger.info("CacheLayerManager initialized with %d layers", len(self._layers))

    def _register_defaults(self) -> None:
        defaults = [
            CacheLayer(
                name="l1_hot",
                layer_type=LayerType.L1_MEMORY,
                max_entries=1000,
                eviction_policy=EvictionPolicy.LRU,
            ),
            CacheLayer(
                name="l2_warm",
                layer_type=LayerType.L2_REDIS,
                max_entries=10000,
                eviction_policy=EvictionPolicy.LFU,
            ),
            CacheLayer(
                name="l3_cold",
                layer_type=LayerType.L3_DISK,
                max_entries=100000,
                eviction_policy=EvictionPolicy.TTL,
            ),
            CacheLayer(
                name="cdn_static",
                layer_type=LayerType.CDN,
                max_entries=5000,
                eviction_policy=EvictionPolicy.FIFO,
            ),
        ]
        for layer in defaults:
            self._layers[layer.name] = layer
        self._layer_order = ["l1_hot", "l2_warm", "l3_cold", "cdn_static"]

    # ----- get -----

    def get(self, key: str, layer_name: Optional[str] = None) -> Optional[CacheEntry]:
        """Look up a key. Without layer_name, cascades L1→L2→L3→CDN."""
        if layer_name:
            return self._get_from_layer(key, layer_name)

        # Cascade lookup
        for name in self._layer_order:
            entry = self._get_from_layer(key, name)
            if entry is not None:
                return entry

        # Miss on all layers
        for name in self._layer_order:
            layer = self._layers.get(name)
            if layer:
                layer.total_misses += 1
                layer._update_hit_rate()
        return None

    def _get_from_layer(self, key: str, layer_name: str) -> Optional[CacheEntry]:
        layer = self._layers.get(layer_name)
        if not layer:
            return None
        entry = layer._entries.get(key)
        if entry and not entry.is_expired():
            layer.total_hits += 1
            entry.hits += 1
            layer._update_hit_rate()
            return entry
        if entry and entry.is_expired():
            del layer._entries[key]
            layer.current_entries -= 1
        layer.total_misses += 1
        layer._update_hit_rate()
        return None

    # ----- put -----

    def put(
        self, key: str, value: Any, ttl: int = 300, layer_name: Optional[str] = None
    ) -> None:
        """Store a key-value pair. Default layer is L1."""
        target = layer_name or "l1_hot"
        layer = self._layers.get(target)
        if not layer:
            return

        # Evict if at capacity
        if layer.current_entries >= layer.max_entries and key not in layer._entries:
            self._evict(layer)

        entry = CacheEntry(
            key=key,
            value=value,
            ttl_seconds=ttl,
            size_bytes=max(64, len(str(value)) * 2),
        )
        layer._entries[key] = entry
        layer.current_entries = len(layer._entries)

    def _evict(self, layer: CacheLayer) -> None:
        """Evict one entry based on the layer's eviction policy."""
        if not layer._entries:
            return
        if layer.eviction_policy == EvictionPolicy.LRU:
            oldest_key = min(layer._entries, key=lambda k: layer._entries[k].created_at)
        elif layer.eviction_policy == EvictionPolicy.LFU:
            oldest_key = min(layer._entries, key=lambda k: layer._entries[k].hits)
        elif layer.eviction_policy == EvictionPolicy.FIFO:
            oldest_key = next(iter(layer._entries))
        else:  # TTL — evict the one closest to expiry
            oldest_key = min(
                layer._entries,
                key=lambda k: (
                    layer._entries[k].created_at + layer._entries[k].ttl_seconds
                ),
            )
        del layer._entries[oldest_key]
        layer.current_entries = len(layer._entries)

    # ----- invalidate -----

    def invalidate(self, key: str, layer_name: Optional[str] = None) -> None:
        """Remove a key from a specific layer or all layers."""
        if layer_name:
            layer = self._layers.get(layer_name)
            if layer and key in layer._entries:
                del layer._entries[key]
                layer.current_entries = len(layer._entries)
            return
        for layer in self._layers.values():
            if key in layer._entries:
                del layer._entries[key]
                layer.current_entries = len(layer._entries)

    # ----- queries -----

    def get_layer(self, name: str) -> Optional[CacheLayer]:
        return self._layers.get(name)

    def list_layers(self) -> List[CacheLayer]:
        return list(self._layers.values())

    def get_hit_rates(self) -> Dict[str, float]:
        return {name: round(layer.hit_rate, 4) for name, layer in self._layers.items()}

    # ----- warm -----

    def warm_cache(self, keys: List[str]) -> int:
        """Bulk-load entries (simulated). Returns count loaded."""
        count = 0
        for key in keys:
            self.put(key, f"warmed_{key}", ttl=600)
            count += 1
        return count

    # ----- stats -----

    def get_stats(self) -> Dict[str, Any]:
        total_entries = sum(l.current_entries for l in self._layers.values())
        total_hits = sum(l.total_hits for l in self._layers.values())
        total_misses = sum(l.total_misses for l in self._layers.values())
        overall_rate = (
            total_hits / (total_hits + total_misses)
            if (total_hits + total_misses) > 0
            else 0.0
        )
        return {
            "total_layers": len(self._layers),
            "total_entries": total_entries,
            "total_hits": total_hits,
            "total_misses": total_misses,
            "overall_hit_rate": round(overall_rate, 4),
        }


# =========================================
# SINGLETON
# =========================================

_instance: Optional[CacheLayerManager] = None


def get_cache_manager() -> CacheLayerManager:
    global _instance
    if _instance is None:
        _instance = CacheLayerManager()
    return _instance
