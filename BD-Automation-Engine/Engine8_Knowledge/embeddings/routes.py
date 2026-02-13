"""
Embeddings API Routes — Domain embeddings, corpus stats, benchmarks, query expansion.

Prefix: /embeddings
"""

import logging
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/embeddings", tags=["Domain Embeddings"])


# ─── Request models ───────────────────────────────────────

class EmbedRequest(BaseModel):
    text: str
    use_adapter: bool = True


class ExpandRequest(BaseModel):
    query: str


# ─── Corpus endpoints ────────────────────────────────────

@router.get("/corpus-stats")
async def corpus_stats():
    """Get domain corpus size and category distribution."""
    try:
        from Engine8_Knowledge.embeddings.corpus_builder import DomainCorpusBuilder
        builder = DomainCorpusBuilder()
        stats = builder.get_stats()
        if stats:
            return stats
        return {"total_documents": 0, "message": "Corpus not built yet. POST /embeddings/build-corpus to create."}
    except Exception as e:
        logger.error(f"Corpus stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/build-corpus")
async def build_corpus():
    """Build the domain corpus from all platform sources."""
    try:
        from Engine8_Knowledge.embeddings.corpus_builder import DomainCorpusBuilder
        builder = DomainCorpusBuilder()
        from dataclasses import asdict
        stats = builder.build_corpus()
        return asdict(stats)
    except Exception as e:
        logger.error(f"Build corpus error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/corpus-sample")
async def corpus_sample(n: int = Query(10, description="Number of samples")):
    """Get random sample from the corpus."""
    try:
        from Engine8_Knowledge.embeddings.corpus_builder import DomainCorpusBuilder
        builder = DomainCorpusBuilder()
        return {"samples": builder.get_corpus_sample(n)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Embedding endpoints ─────────────────────────────────

@router.post("/embed")
async def embed_text(data: EmbedRequest):
    """Embed text with domain adapter (or base embeddings if not trained)."""
    try:
        from Engine8_Knowledge.embeddings.domain_embedder import get_domain_embedder
        embedder = get_domain_embedder()
        vector = embedder.embed(data.text)
        return {
            "text": data.text[:100],
            "embedding_dim": len(vector),
            "adapter_used": embedder.config.trained and data.use_adapter,
        }
    except Exception as e:
        logger.error(f"Embed error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def embedder_status():
    """Get adapter model status, training date, improvement metrics."""
    try:
        from Engine8_Knowledge.embeddings.domain_embedder import get_domain_embedder
        embedder = get_domain_embedder()
        status = embedder.get_status()

        # Also get corpus stats
        from Engine8_Knowledge.embeddings.corpus_builder import DomainCorpusBuilder
        builder = DomainCorpusBuilder()
        corpus = builder.get_stats()
        status["corpus"] = corpus or {"total_documents": 0}

        # Also get benchmark results
        from Engine8_Knowledge.embeddings.search_benchmark import SearchBenchmark
        bench = SearchBenchmark()
        results = bench.load_results()
        status["benchmark"] = results

        return status
    except Exception as e:
        logger.error(f"Status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train")
async def train_adapter(epochs: int = Query(10)):
    """Train the domain adapter on the corpus."""
    try:
        from Engine8_Knowledge.embeddings.domain_embedder import get_domain_embedder
        from dataclasses import asdict
        embedder = get_domain_embedder()
        result = embedder.train_adapter(epochs=epochs)
        return asdict(result)
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Train error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── Query expansion endpoints ───────────────────────────

@router.post("/expand-query")
async def expand_query(data: ExpandRequest):
    """Expand a query with acronym resolutions and domain synonyms."""
    try:
        from Engine8_Knowledge.embeddings.query_expander import get_query_expander
        from dataclasses import asdict
        expander = get_query_expander()
        result = expander.expand_query(data.query)
        return asdict(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/expander-stats")
async def expander_stats():
    """Get query expander statistics."""
    try:
        from Engine8_Knowledge.embeddings.query_expander import get_query_expander
        expander = get_query_expander()
        return expander.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Benchmark endpoints ─────────────────────────────────

@router.get("/benchmark/queries")
async def benchmark_queries():
    """Get the golden test query set."""
    try:
        from Engine8_Knowledge.embeddings.search_benchmark import SearchBenchmark
        bench = SearchBenchmark()
        return {"queries": bench.get_golden_queries(), "total": len(bench.queries)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/benchmark/results")
async def benchmark_results():
    """Get latest benchmark comparison results."""
    try:
        from Engine8_Knowledge.embeddings.search_benchmark import SearchBenchmark
        bench = SearchBenchmark()
        results = bench.load_results()
        if results:
            return results
        return {"message": "No benchmark results yet. POST /embeddings/benchmark to run."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/benchmark")
async def run_benchmark():
    """Run search quality benchmark comparing base vs expanded search."""
    try:
        from Engine8_Knowledge.embeddings.search_benchmark import SearchBenchmark
        from Engine8_Knowledge.embeddings.query_expander import get_query_expander
        from dataclasses import asdict

        bench = SearchBenchmark()
        expander = get_query_expander()

        results = []

        # Try to get a search function from vector store
        try:
            from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore
            store = BDKnowledgeStore()

            def base_search(query: str, limit: int) -> list:
                hits = store.search(query, limit=limit)
                return [{"text": str(getattr(h, "payload", h))} for h in hits]

            def expanded_search(query: str, limit: int) -> list:
                eq = expander.expand_query(query)
                hits = store.search(eq.expanded, limit=limit)
                return [{"text": str(getattr(h, "payload", h))} for h in hits]

            r1 = bench.run_benchmark(base_search, "base_embeddings")
            results.append(r1)

            r2 = bench.run_benchmark(expanded_search, "query_expanded")
            results.append(r2)

        except ImportError:
            logger.warning("Vector store not available for benchmark")

        if results:
            comparison = bench.compare_methods(results)
            bench.save_results(comparison)
            return asdict(comparison)

        return {"message": "Vector store not available. Cannot run benchmark."}
    except Exception as e:
        logger.error(f"Benchmark error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
