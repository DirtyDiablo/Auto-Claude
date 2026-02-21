"""
Simple Knowledge API - Direct Qdrant access for BD Intelligence
Minimal dependencies: fastapi, uvicorn, qdrant-client, openai
"""

import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Add project root for canonical imports
sys.path.insert(0, str(Path(__file__).parent))

load_dotenv()

import openai
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

# Config
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536

# Initialize clients
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "") or None
qdrant = QdrantClient(url=QDRANT_URL, timeout=300, api_key=QDRANT_API_KEY)
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI(
    title="BD Knowledge API",
    description="Semantic search and RAG for BD Intelligence - 819K+ records",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Models
class SearchRequest(BaseModel):
    query: str
    collection: str = "contacts"
    limit: int = 10
    filters: Optional[Dict[str, Any]] = None


# Import unified Pydantic model from canonical models
try:
    from Engine8_Knowledge.models import SearchResultModel as SearchResult
except ImportError:
    class SearchResult(BaseModel):
        id: str
        score: float
        payload: Dict[str, Any] = {}


class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
    query: str
    collection: str


class RAGRequest(BaseModel):
    question: str
    collection: str = "contacts"
    top_k: int = 5


class RAGResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    question: str


class CollectionStats(BaseModel):
    name: str
    count: int
    status: str


class StatsResponse(BaseModel):
    total_records: int
    collections: Dict[str, int]
    status: str


# Helper functions
def get_embedding(text: str) -> List[float]:
    """Get OpenAI embedding for text."""
    response = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return response.data[0].embedding


def search_collection(
    collection: str, query_vector: List[float], limit: int = 10, filters: dict = None
) -> List[dict]:
    """Search a Qdrant collection."""
    query_filter = None
    if filters:
        conditions = []
        for key, value in filters.items():
            conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
        query_filter = Filter(must=conditions)

    results = qdrant.query_points(
        collection_name=collection,
        query=query_vector,
        limit=limit,
        with_payload=True,
        query_filter=query_filter,
    )
    return [
        {"id": str(r.id), "score": r.score, "payload": r.payload}
        for r in results.points
    ]


# Endpoints
@app.get("/")
async def root():
    return {
        "service": "BD Knowledge API",
        "version": "1.0.0",
        "collections": [
            "contacts",
            "activities",
            "programs",
            "documents",
            "jobs",
            "primes",
        ],
        "total_records": "819,000+",
        "embedding_model": EMBEDDING_MODEL,
    }


@app.get("/health")
async def health():
    try:
        collections = qdrant.get_collections()
        return {
            "status": "healthy",
            "qdrant": "connected",
            "collections": len(collections.collections),
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.get("/stats")
async def stats():
    """Dashboard-compatible stats endpoint - matches RawHubStats format."""
    try:
        collections = qdrant.get_collections()
        qdrant_stats = {}
        for coll in collections.collections:
            info = qdrant.get_collection(coll.name)
            qdrant_stats[coll.name] = {
                "vectors_count": info.indexed_vectors_count or info.points_count,
                "points_count": info.points_count,
                "status": str(info.status),
            }
        return {
            "qdrant": qdrant_stats,
            "memory": {"total_memories": 0, "by_type": {}, "backend": "none"},
            "graph": {"working_dir": "", "backend": "none", "files": 0},
            "cache": {"cached_queries": 0, "backend": "none", "threshold": 0.8},
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/collections")
async def list_collections() -> List[CollectionStats]:
    """List all collections with stats."""
    collections = qdrant.get_collections()
    stats = []
    for coll in collections.collections:
        info = qdrant.get_collection(coll.name)
        stats.append(
            CollectionStats(
                name=coll.name, count=info.points_count, status=str(info.status)
            )
        )
    return stats


@app.get("/collections/{collection}")
async def collection_info(collection: str):
    """Get detailed info about a collection."""
    try:
        info = qdrant.get_collection(collection)
        return {
            "name": collection,
            "points_count": info.points_count,
            "indexed_vectors_count": info.indexed_vectors_count,
            "status": str(info.status),
            "config": {
                "vector_size": info.config.params.vectors.size,
                "distance": str(info.config.params.vectors.distance),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Collection not found: {e}")


@app.post("/search", response_model=SearchResponse)
async def semantic_search(request: SearchRequest):
    """Semantic search across any collection."""
    try:
        # Get embedding for query
        query_vector = get_embedding(request.query)

        # Search
        results = search_collection(
            collection=request.collection,
            query_vector=query_vector,
            limit=request.limit,
            filters=request.filters,
        )

        return SearchResponse(
            results=[SearchResult(**r) for r in results],
            total=len(results),
            query=request.query,
            collection=request.collection,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search/{collection}")
async def search_get(
    collection: str,
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=100),
    tier: Optional[str] = None,
    company: Optional[str] = None,
):
    """GET-based semantic search with optional filters."""
    filters = {}
    if tier:
        filters["tier"] = tier
    if company:
        filters["company"] = company

    query_vector = get_embedding(q)
    results = search_collection(
        collection, query_vector, limit, filters if filters else None
    )

    return {
        "results": results,
        "total": len(results),
        "query": q,
        "collection": collection,
    }


@app.get("/search")
async def search_all(
    q: str = Query(..., description="Search query"),
    collection: str = Query("contacts", description="Collection to search"),
    limit: int = Query(10, ge=1, le=100),
):
    """Dashboard-compatible search endpoint - matches RawSearchResponse format."""
    query_vector = get_embedding(q)
    results = search_collection(collection, query_vector, limit)
    # Transform to dashboard expected format
    formatted_results = [
        {
            "id": r["id"],
            "score": r["score"],
            "payload": r["payload"],
            "collection": collection,
        }
        for r in results
    ]
    return {
        "query": q,
        "collection": collection,
        "results": formatted_results,
        "count": len(results),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/search/hybrid")
async def search_hybrid(request: SearchRequest):
    """Hybrid search - same as semantic for now."""
    return await semantic_search(request)


@app.post("/ask/smart")
async def ask_smart_post(request: RAGRequest):
    """Dashboard-compatible RAG Q&A endpoint (POST)."""
    return await ask_smart_internal(request.question, request.collection, request.top_k)


@app.get("/ask/smart")
async def ask_smart_get(
    q: str = Query(..., description="Question to ask"),
    collection: str = Query("contacts", description="Collection to search"),
    strategy: str = Query("auto", description="Search strategy"),
    top_k: int = Query(5, ge=1, le=20),
):
    """Dashboard-compatible GET-based RAG Q&A endpoint."""
    return await ask_smart_internal(q, collection, top_k)


async def ask_smart_internal(
    question: str, collection: str = "contacts", top_k: int = 5
):
    """Internal RAG implementation matching dashboard format."""
    try:
        # Get embedding and search for context
        query_vector = get_embedding(question)
        results = search_collection(collection, query_vector, top_k)

        # Build context from results
        context_parts = []
        for i, r in enumerate(results, 1):
            payload = r["payload"]
            if collection == "contacts":
                context_parts.append(
                    f"{i}. {payload.get('name', 'Unknown')} - {payload.get('title', '')} at {payload.get('company', '')} ({payload.get('tier', '')})"
                )
            elif collection == "activities":
                context_parts.append(
                    f"{i}. {payload.get('action', '')} - {payload.get('comments', '')[:200]}"
                )
            else:
                context_parts.append(f"{i}. {str(payload)[:300]}")

        context = "\n".join(context_parts)

        # Generate answer with OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a BD Intelligence assistant. Answer questions using the provided context from the {collection} database. Be concise and cite sources.",
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {question}",
                },
            ],
            temperature=0.3,
            max_tokens=500,
        )

        answer = response.choices[0].message.content

        # Format sources for dashboard
        formatted_sources = [
            {
                "id": r["id"],
                "score": r["score"],
                "payload": r["payload"],
                "collection": collection,
            }
            for r in results
        ]

        return {
            "answer": answer,
            "query_type": "semantic",
            "systems_used": ["qdrant", "openai"],
            "sources": formatted_sources,
            "cache_hit": False,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ask")
async def ask_get(
    q: str = Query(..., description="Question to ask"),
    collection: str = Query("contacts", description="Collection to search"),
    top_k: int = Query(5, ge=1, le=20),
):
    """GET-based RAG Q&A endpoint for dashboard."""
    try:
        query_vector = get_embedding(q)
        results = search_collection(collection, query_vector, top_k)

        # Build context
        context_parts = []
        for i, r in enumerate(results, 1):
            payload = r["payload"]
            if collection == "contacts":
                context_parts.append(
                    f"{i}. {payload.get('name', 'Unknown')} - {payload.get('title', '')} at {payload.get('company', '')}"
                )
            else:
                context_parts.append(f"{i}. {str(payload)[:300]}")

        context = "\n".join(context_parts)

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a BD Intelligence assistant. Answer using the provided context from {collection}. Be concise.",
                },
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {q}"},
            ],
            temperature=0.3,
            max_tokens=500,
        )

        answer = response.choices[0].message.content
        formatted_sources = [
            {
                "id": r["id"],
                "score": r["score"],
                "payload": r["payload"],
                "collection": collection,
            }
            for r in results
        ]

        return {"answer": answer, "sources": formatted_sources, "confidence": 0.85}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask", response_model=RAGResponse)
async def ask_question(request: RAGRequest):
    """RAG-powered Q&A - retrieves context and generates answer."""
    try:
        # Get embedding and search for context
        query_vector = get_embedding(request.question)
        results = search_collection(request.collection, query_vector, request.top_k)

        # Build context from results
        context_parts = []
        for i, r in enumerate(results, 1):
            payload = r["payload"]
            if request.collection == "contacts":
                context_parts.append(
                    f"{i}. {payload.get('name', 'Unknown')} - {payload.get('title', '')} at {payload.get('company', '')} ({payload.get('tier', '')})"
                )
            elif request.collection == "activities":
                context_parts.append(
                    f"{i}. {payload.get('action', '')} - {payload.get('comments', '')[:200]}"
                )
            else:
                context_parts.append(f"{i}. {str(payload)[:300]}")

        context = "\n".join(context_parts)

        # Generate answer with OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a BD Intelligence assistant. Answer questions using the provided context from the {request.collection} database. Be concise and cite sources.",
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {request.question}",
                },
            ],
            temperature=0.3,
            max_tokens=500,
        )

        answer = response.choices[0].message.content

        return RAGResponse(answer=answer, sources=results, question=request.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/contacts/search")
async def search_contacts(
    q: str = Query(..., description="Search query"),
    limit: int = 10,
    tier: Optional[str] = None,
):
    """Search contacts with optional tier filter."""
    filters = {"tier": tier} if tier else None
    query_vector = get_embedding(q)
    results = search_collection("contacts", query_vector, limit, filters)
    return {"results": results, "total": len(results)}


@app.get("/activities/search")
async def search_activities(
    q: str = Query(..., description="Search query"), limit: int = 10
):
    """Search activities (call notes, meetings, etc.)."""
    query_vector = get_embedding(q)
    results = search_collection("activities", query_vector, limit)
    return {"results": results, "total": len(results)}


@app.get("/programs/search")
async def search_programs(
    q: str = Query(..., description="Search query"), limit: int = 10
):
    """Search federal programs."""
    query_vector = get_embedding(q)
    results = search_collection("programs", query_vector, limit)
    return {"results": results, "total": len(results)}


# Sample data endpoints
@app.get("/sample/{collection}")
async def get_sample(collection: str, limit: int = 5):
    """Get sample records from a collection (no search, just scroll)."""
    try:
        results = qdrant.scroll(
            collection_name=collection, limit=limit, with_payload=True
        )
        return {
            "collection": collection,
            "samples": [{"id": str(p.id), "payload": p.payload} for p in results[0]],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 60)
    print("BD Knowledge API Starting...")
    print("=" * 60)
    print(f"Qdrant: {QDRANT_URL}")
    print(f"Embedding Model: {EMBEDDING_MODEL}")
    print("=" * 60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8100)
