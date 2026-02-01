"""
Populate LightRAG from Qdrant collections via API.

Reads all records from Qdrant via the API and inserts them
as text documents into LightRAG for graph-based reasoning.
"""

import sys
import time
import requests
from pathlib import Path
from typing import Dict, List, Any

# Configuration
API_URL = "http://localhost:8100"
BATCH_SIZE = 25  # Documents per insert request


def contact_to_text(contact: Dict[str, Any]) -> str:
    """Convert a contact record to a text document for LightRAG."""
    parts = []

    name = contact.get('name') or f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
    if name:
        parts.append(f"{name}")

    title = contact.get('title')
    company = contact.get('company')
    if title and company:
        parts.append(f"is {title} at {company}")
    elif company:
        parts.append(f"works at {company}")

    tier = contact.get('tier')
    if tier:
        parts.append(f"(Tier {tier} contact)")

    program = contact.get('program')
    if program and program != "Other Defense":
        parts.append(f"associated with {program} program")

    email = contact.get('email')
    if email and '@' in str(email):
        parts.append(f"email: {email}")

    linkedin = contact.get('linkedin')
    if linkedin and 'linkedin.com' in str(linkedin):
        parts.append(f"LinkedIn: {linkedin}")

    notes = contact.get('notes')
    if notes:
        parts.append(f"Notes: {notes}")

    return " ".join(parts) if parts else None


def program_to_text(program: Dict[str, Any]) -> str:
    """Convert a program record to a text document for LightRAG."""
    parts = []

    name = program.get('name')
    if name:
        parts.append(f"{name}")

    prime = program.get('prime_contractor')
    if prime:
        parts.append(f"is primed by {prime}")

    vehicle = program.get('contract_vehicle')
    if vehicle:
        parts.append(f"under {vehicle}")

    value = program.get('contract_value')
    if value:
        parts.append(f"valued at {value}")

    status = program.get('status')
    if status:
        parts.append(f"(Status: {status})")

    location = program.get('location')
    if location:
        parts.append(f"located in {location}")

    mission = program.get('mission_area')
    if mission:
        parts.append(f"mission area: {mission}")

    notes = program.get('notes')
    if notes:
        parts.append(f"Notes: {notes}")

    return " ".join(parts) if parts else None


def document_to_text(doc: Dict[str, Any]) -> str:
    """Convert a document record to text for LightRAG."""
    parts = []

    title = doc.get('title') or doc.get('name')
    if title:
        parts.append(f"Document: {title}")

    doc_type = doc.get('type') or doc.get('document_type')
    if doc_type:
        parts.append(f"Type: {doc_type}")

    content = doc.get('content') or doc.get('text') or doc.get('summary')
    if content:
        if len(content) > 2000:
            content = content[:2000] + "..."
        parts.append(content)

    company = doc.get('company')
    if company:
        parts.append(f"Company: {company}")

    return " ".join(parts) if parts else None


def activity_to_text(activity: Dict[str, Any]) -> str:
    """Convert an activity record to text for LightRAG."""
    parts = []

    activity_type = activity.get('type') or activity.get('activity_type')
    if activity_type:
        parts.append(f"{activity_type}:")

    subject = activity.get('subject') or activity.get('title')
    if subject:
        parts.append(subject)

    contact = activity.get('contact_name') or activity.get('contact')
    if contact:
        parts.append(f"with {contact}")

    company = activity.get('company')
    if company:
        parts.append(f"at {company}")

    notes = activity.get('notes') or activity.get('description')
    if notes:
        if len(notes) > 500:
            notes = notes[:500] + "..."
        parts.append(f"- {notes}")

    return " ".join(parts) if parts else None


def job_to_text(job: Dict[str, Any]) -> str:
    """Convert a job record to text for LightRAG."""
    parts = []

    title = job.get('title')
    if title:
        parts.append(f"Job: {title}")

    company = job.get('company')
    if company:
        parts.append(f"at {company}")

    location = job.get('location')
    if location:
        parts.append(f"in {location}")

    program = job.get('program_name') or job.get('program')
    if program:
        parts.append(f"for {program} program")

    clearance = job.get('clearance')
    if clearance:
        parts.append(f"requires {clearance} clearance")

    return " ".join(parts) if parts else None


CONVERTERS = {
    'contacts': contact_to_text,
    'programs': program_to_text,
    'documents': document_to_text,
    'activities': activity_to_text,
    'jobs': job_to_text,
}


def fetch_all_from_collection(collection: str, limit: int = 10000) -> List[Dict]:
    """Fetch all records from a collection via multiple search queries."""
    all_records = []
    seen_ids = set()

    # Search terms to cover most records
    search_terms = {
        'contacts': ['GDIT', 'Leidos', 'SAIC', 'Northrop', 'Lockheed', 'Raytheon', 'BAE', 'CACI', 'ManTech', 'Peraton', 'L3Harris', 'Booz', 'Jacobs', 'KBR', 'AECOM', 'defense', 'manager', 'director', 'engineer', 'analyst', 'architect', 'consultant'],
        'programs': ['GDIT', 'Leidos', 'SAIC', 'Northrop', 'contract', 'defense', 'army', 'navy', 'air force', 'DCGS', 'ISR', 'cyber'],
        'documents': ['document', 'report', 'brief', 'proposal', 'performance', 'technical'],
        'activities': ['call', 'meeting', 'email', 'note', 'discussion', 'outreach'],
        'jobs': ['analyst', 'engineer', 'manager', 'developer', 'architect', 'GDIT'],
    }

    terms = search_terms.get(collection, ['defense', 'federal'])
    print(f"    Searching with {len(terms)} terms...")

    for i, term in enumerate(terms):
        try:
            url = f"{API_URL}/search"
            payload = {
                "query": term,
                "collection": collection,
                "limit": 50
            }
            response = requests.post(url, json=payload, timeout=60)

            if i == 0:
                print(f"    First search '{term}': status={response.status_code}")

            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                if i == 0:
                    print(f"    First search returned {len(results)} results")
                new_count = 0
                for result in results:
                    record_id = result.get('id')
                    if record_id and record_id not in seen_ids:
                        seen_ids.add(record_id)
                        payload = result.get('payload', result)
                        all_records.append(payload)
                        new_count += 1
                if i == 0:
                    print(f"    Added {new_count} new records")
            else:
                print(f"    Search '{term}' failed: {response.status_code} - {response.text[:100]}")

            if len(all_records) >= limit:
                break
        except Exception as e:
            print(f"    Warning: search for '{term}' failed: {e}")
            import traceback
            traceback.print_exc()

    return all_records


def insert_batch(documents: List[str]) -> Dict:
    """Insert a batch of documents into LightRAG."""
    response = requests.post(
        f"{API_URL}/lightrag/insert",
        json={
            "documents": documents,
            "enrich_entities": True
        },
        timeout=300
    )
    response.raise_for_status()
    return response.json()


def populate_collection(collection: str, converter: callable, expected_count: int) -> Dict[str, int]:
    """Populate LightRAG from a single Qdrant collection."""
    print(f"\n[*] Processing {collection} (expected ~{expected_count} records)...")

    # Fetch records via API
    records = fetch_all_from_collection(collection)
    print(f"    Retrieved {len(records)} records via API")

    # Convert to text documents
    documents = []
    skipped = 0
    for record in records:
        text = converter(record)
        if text and len(text) > 10:
            documents.append(text)
        else:
            skipped += 1

    print(f"    Converted {len(documents)} documents ({skipped} skipped)")

    if not documents:
        return {"collection": collection, "inserted": 0, "skipped": skipped}

    # Insert in batches
    inserted = 0
    total_batches = (len(documents) - 1) // BATCH_SIZE + 1

    for i in range(0, len(documents), BATCH_SIZE):
        batch = documents[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        try:
            print(f"    Inserting batch {batch_num}/{total_batches} ({len(batch)} docs)...", end=" ", flush=True)
            result = insert_batch(batch)
            inserted += len(batch)
            print("OK")
        except Exception as e:
            print(f"ERROR: {e}")

    return {"collection": collection, "inserted": inserted, "skipped": skipped}


def main():
    """Main entry point."""
    print("=" * 60)
    print("LightRAG Population from Qdrant (via API)")
    print("=" * 60)

    # Check API health
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)
        response.raise_for_status()
        print("[OK] API is healthy")
    except Exception as e:
        print(f"[ERROR] API not available at {API_URL}: {e}")
        return

    # Get stats
    print("\n[*] Fetching collection stats...")
    try:
        response = requests.get(f"{API_URL}/stats", timeout=30)
        stats = response.json()
        qdrant_stats = stats.get('qdrant', {})
        for coll, info in qdrant_stats.items():
            print(f"    - {coll}: {info.get('points_count', 0)} records")
    except Exception as e:
        print(f"    Warning: Could not fetch stats: {e}")
        qdrant_stats = {}

    # Process each collection
    results = []
    for collection, converter in CONVERTERS.items():
        expected = qdrant_stats.get(collection, {}).get('points_count', 0)
        if expected > 0:
            result = populate_collection(collection, converter, expected)
            results.append(result)
        else:
            print(f"\n[SKIP] {collection}: no records")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    total_inserted = 0
    for r in results:
        print(f"  {r['collection']}: {r['inserted']} inserted, {r['skipped']} skipped")
        total_inserted += r['inserted']

    print(f"\n  TOTAL: {total_inserted} documents inserted into LightRAG")

    # Test query
    print("\n[*] Testing query...")
    try:
        response = requests.post(
            f"{API_URL}/lightrag/query",
            json={"query": "GDIT contacts in defense programs", "mode": "hybrid"},
            timeout=60
        )
        result = response.json()
        answer = result.get('answer', 'No answer')
        if 'failed' not in answer.lower():
            print(f"    [OK] Query working!")
            print(f"    Answer: {answer[:400]}...")
        else:
            print(f"    [WARN] {answer}")
    except Exception as e:
        print(f"    [ERROR] {e}")


if __name__ == "__main__":
    main()
