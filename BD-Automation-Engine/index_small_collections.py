#!/usr/bin/env python3
"""
Index small collections (jobs, programs, documents) with OpenAI embeddings.
Source: bullhorn_master.db tables
"""

import sys
import os
import sqlite3
import uuid
from datetime import datetime
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
os.chdir(r"C:\Users\gtmar\Projects\Auto-Claude\BD-Automation-Engine")
load_dotenv()

import openai
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Configuration
QDRANT_URL = "http://localhost:6333"
DB_PATH = "Engine7_BullhornETL/data/bullhorn_master.db"
OPENAI_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536

client_openai = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
NAMESPACE = uuid.UUID('fedcba98-7654-3210-fedc-ba9876543210')


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Get embeddings from OpenAI API."""
    texts = [t if t.strip() else "empty" for t in texts]
    try:
        response = client_openai.embeddings.create(model=OPENAI_MODEL, input=texts)
        return [item.embedding for item in response.data]
    except Exception as e:
        print(f"  [ERROR] OpenAI API error: {e}")
        return [[0.0] * EMBEDDING_DIM] * len(texts)


def string_to_uuid(s: str) -> str:
    return str(uuid.uuid5(NAMESPACE, s))


def index_jobs(qdrant, conn):
    """Index jobs table."""
    print("\n" + "=" * 50)
    print("INDEXING JOBS")
    print("=" * 50)

    # Create collection
    try:
        qdrant.delete_collection("jobs")
    except:
        pass
    qdrant.create_collection(
        collection_name="jobs",
        vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE)
    )

    cursor = conn.execute("""
        SELECT id, title, description, location, client_corporation,
               prime_contractor, salary, status, date_added, skills, clearance_required
        FROM jobs
    """)

    points = []
    texts = []
    payloads = []
    for row in cursor:
        text = f"{row[1] or ''} {row[2] or ''} {row[3] or ''} {row[4] or ''} {row[5] or ''} {row[9] or ''}"
        payload = {
            'id': str(row[0]),
            'title': row[1] or '',
            'description': row[2] or '',
            'location': row[3] or '',
            'client': row[4] or '',
            'prime_contractor': row[5] or '',
            'salary': row[6],
            'status': row[7] or '',
            'date_added': row[8] or '',
            'skills': row[9] or '',
            'clearance': row[10] or '',
            '_embedding_model': OPENAI_MODEL,
            '_indexed_at': datetime.now().isoformat()
        }
        texts.append(text)
        payloads.append(payload)

    if texts:
        embeddings = get_embeddings(texts)
        for emb, payload in zip(embeddings, payloads):
            points.append(PointStruct(id=string_to_uuid(f"job_{payload['id']}"), vector=emb, payload=payload))
        qdrant.upsert(collection_name="jobs", points=points)
    print(f"  Indexed: {len(points)} jobs")


def index_programs(qdrant, conn):
    """Index programs table."""
    print("\n" + "=" * 50)
    print("INDEXING PROGRAMS")
    print("=" * 50)

    try:
        qdrant.delete_collection("programs")
    except:
        pass
    qdrant.create_collection(
        collection_name="programs",
        vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE)
    )

    cursor = conn.execute("""
        SELECT id, name, acronym, description, agency, sub_agency,
               contract_value, prime_contractor_name, location
        FROM programs
    """)

    points = []
    texts = []
    payloads = []
    for row in cursor:
        text = f"{row[1] or ''} {row[2] or ''} {row[3] or ''} {row[4] or ''} {row[5] or ''} {row[7] or ''}"
        payload = {
            'id': str(row[0]),
            'name': row[1] or '',
            'acronym': row[2] or '',
            'description': row[3] or '',
            'agency': row[4] or '',
            'sub_agency': row[5] or '',
            'contract_value': row[6],
            'prime_contractor': row[7] or '',
            'location': row[8] or '',
            '_embedding_model': OPENAI_MODEL,
            '_indexed_at': datetime.now().isoformat()
        }
        texts.append(text)
        payloads.append(payload)

    if texts:
        embeddings = get_embeddings(texts)
        for emb, payload in zip(embeddings, payloads):
            points.append(PointStruct(id=string_to_uuid(f"program_{payload['id']}"), vector=emb, payload=payload))
        qdrant.upsert(collection_name="programs", points=points)
    print(f"  Indexed: {len(points)} programs")


def index_documents(qdrant, conn):
    """Index past_performance as documents."""
    print("\n" + "=" * 50)
    print("INDEXING DOCUMENTS (past_performance)")
    print("=" * 50)

    try:
        qdrant.delete_collection("documents")
    except:
        pass
    qdrant.create_collection(
        collection_name="documents",
        vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE)
    )

    cursor = conn.execute("""
        SELECT id, prime_contractor_name, program_name, total_jobs, total_placements,
               total_revenue, fill_rate, performance_score, notes
        FROM past_performance
    """)

    points = []
    texts = []
    payloads = []

    for row in cursor:
        text = f"{row[1] or ''} {row[2] or ''} {row[8] or ''}"
        payload = {
            'id': str(row[0]),
            'prime_contractor': row[1] or '',
            'program': row[2] or '',
            'total_jobs': row[3],
            'total_placements': row[4],
            'total_revenue': row[5],
            'fill_rate': row[6],
            'performance_score': row[7],
            'notes': row[8] or '',
            'type': 'past_performance',
            '_embedding_model': OPENAI_MODEL,
            '_indexed_at': datetime.now().isoformat()
        }
        texts.append(text)
        payloads.append(payload)

    # Batch embed
    if texts:
        embeddings = get_embeddings(texts)
        for emb, payload in zip(embeddings, payloads):
            points.append(PointStruct(
                id=string_to_uuid(f"doc_{payload['id']}"),
                vector=emb,
                payload=payload
            ))
        qdrant.upsert(collection_name="documents", points=points)
    print(f"  Indexed: {len(points)} documents")


def index_primes(qdrant, conn):
    """Index prime_contractors."""
    print("\n" + "=" * 50)
    print("INDEXING PRIME CONTRACTORS")
    print("=" * 50)

    try:
        qdrant.delete_collection("primes")
    except:
        pass
    qdrant.create_collection(
        collection_name="primes",
        vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE)
    )

    cursor = conn.execute("""
        SELECT id, name, aliases, headquarters, naics_codes, contract_vehicles,
               total_jobs, total_placements, total_revenue, notes, category
        FROM prime_contractors
    """)

    points = []
    texts = []
    payloads = []

    for row in cursor:
        text = f"{row[1] or ''} {row[2] or ''} {row[3] or ''} {row[4] or ''} {row[5] or ''} {row[9] or ''}"
        payload = {
            'id': str(row[0]),
            'name': row[1] or '',
            'aliases': row[2] or '',
            'headquarters': row[3] or '',
            'naics_codes': row[4] or '',
            'contract_vehicles': row[5] or '',
            'total_jobs': row[6],
            'total_placements': row[7],
            'total_revenue': row[8],
            'notes': row[9] or '',
            'category': row[10] or '',
            '_embedding_model': OPENAI_MODEL,
            '_indexed_at': datetime.now().isoformat()
        }
        texts.append(text)
        payloads.append(payload)

    if texts:
        embeddings = get_embeddings(texts)
        for emb, payload in zip(embeddings, payloads):
            points.append(PointStruct(
                id=string_to_uuid(f"prime_{payload['id']}"),
                vector=emb,
                payload=payload
            ))
        qdrant.upsert(collection_name="primes", points=points)
    print(f"  Indexed: {len(points)} prime contractors")


def main():
    print("=" * 50)
    print("SMALL COLLECTIONS INDEXER (OpenAI Embeddings)")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    qdrant = QdrantClient(url=QDRANT_URL, timeout=300)
    conn = sqlite3.connect(DB_PATH)

    index_jobs(qdrant, conn)
    index_programs(qdrant, conn)
    index_documents(qdrant, conn)
    index_primes(qdrant, conn)

    conn.close()

    print("\n" + "=" * 50)
    print("ALL SMALL COLLECTIONS INDEXED")
    print("=" * 50)

    # Show final counts
    for coll in ['jobs', 'programs', 'documents', 'primes']:
        try:
            info = qdrant.get_collection(coll)
            print(f"  {coll}: {info.points_count} points ({EMBEDDING_DIM} dims)")
        except:
            print(f"  {coll}: error")


if __name__ == "__main__":
    main()
