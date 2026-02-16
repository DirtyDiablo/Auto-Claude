#!/usr/bin/env python3
"""
Create Unified Qdrant Collections for BD-Automation-Engine.

This script creates the 12 unified collections with proper indexes
for the consolidated BD Intelligence Hub.

Usage:
    python scripts/create_unified_collections.py
"""

import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance,
        VectorParams,
        PayloadSchemaType,
        TextIndexParams,
        TokenizerType,
    )
except ImportError:
    print("Error: qdrant-client not installed. Run: pip install qdrant-client")
    sys.exit(1)


# Collection definitions with payload indexes
COLLECTIONS = {
    "contacts_unified": {
        "description": "All contacts from BD-Engine, N8N-Builder, ZoomInfo",
        "payload_indexes": [
            "program",
            "hierarchy_tier",
            "bd_priority",
            "location_hub",
            "company",
            "source_project",
        ],
    },
    "programs_unified": {
        "description": "Federal programs from all sources",
        "payload_indexes": [
            "agency_owner",
            "prime_contractor",
            "pts_involvement",
            "priority_level",
            "status",
        ],
    },
    "jobs_unified": {
        "description": "All scraped and tracked jobs",
        "payload_indexes": [
            "company",
            "detected_clearance",
            "location",
            "mapped_program",
            "status",
            "source_project",
        ],
    },
    "contracts_federal": {
        "description": "USASpending + FPDS federal contract data",
        "payload_indexes": [
            "agency",
            "contractor",
            "naics",
            "contract_type",
            "fiscal_year",
        ],
    },
    "activities_log": {
        "description": "All BD engagement activities",
        "payload_indexes": [
            "contact_name",
            "activity_type",
            "program",
            "author",
            "date",
        ],
    },
    "documents_kb": {
        "description": "Playbooks, reports, briefings",
        "payload_indexes": ["doc_type", "program", "author", "date"],
    },
    "bullhorn_history": {
        "description": "38K Bullhorn CRM records",
        "payload_indexes": ["candidate", "client", "role_type", "date", "outcome"],
    },
    "knowledge_graph": {
        "description": "LightRAG entity extractions",
        "payload_indexes": ["entity_type", "source", "relationship_type"],
    },
    "intelligence_briefs": {
        "description": "HUMINT reports and weekly updates",
        "payload_indexes": ["source_tier", "confidence", "program", "date"],
    },
    "email_templates": {
        "description": "Generated outreach content",
        "payload_indexes": ["contact_tier", "program", "template_type"],
    },
    "competitor_intel": {
        "description": "Competitor analysis data",
        "payload_indexes": ["competitor", "program", "location", "role_type"],
    },
    "pipeline_tracking": {
        "description": "Active BD opportunities",
        "payload_indexes": ["stage", "contact", "program", "probability"],
    },
}


def create_all_collections(qdrant_url: str = None, vector_size: int = 1536):
    """
    Create all unified collections with indexes.

    Args:
        qdrant_url: Qdrant server URL (defaults to QDRANT_URL env var or localhost)
        vector_size: Embedding dimension (default 1536 for text-embedding-3-small)
    """
    qdrant_url = qdrant_url or os.environ.get("QDRANT_URL", "http://localhost:6333")

    print(f"Connecting to Qdrant at {qdrant_url}...")
    client = QdrantClient(url=qdrant_url)

    # Get existing collections
    existing = [c.name for c in client.get_collections().collections]
    print(f"Found {len(existing)} existing collections")

    created_count = 0
    skipped_count = 0

    for name, config in COLLECTIONS.items():
        if name in existing:
            print(f"  [SKIP] Collection '{name}' already exists")
            skipped_count += 1
            continue

        try:
            # Create collection with vector config
            client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE,
                ),
            )

            # Create payload indexes for fast filtering
            for field in config["payload_indexes"]:
                try:
                    client.create_payload_index(
                        collection_name=name,
                        field_name=field,
                        field_schema=PayloadSchemaType.KEYWORD,
                    )
                except Exception as e:
                    print(f"    Warning: Could not create index for '{field}': {e}")

            # Add full-text index on 'content' field for hybrid search
            try:
                client.create_payload_index(
                    collection_name=name,
                    field_name="content",
                    field_schema=TextIndexParams(
                        type="text",
                        tokenizer=TokenizerType.WORD,
                        min_token_len=2,
                        max_token_len=20,
                        lowercase=True,
                    ),
                )
            except Exception as e:
                print(f"    Warning: Could not create full-text index: {e}")

            print(
                f"  [OK] Created collection '{name}' with {len(config['payload_indexes'])} indexes + full-text"
            )
            created_count += 1

        except Exception as e:
            print(f"  [ERROR] Failed to create '{name}': {e}")

    # Summary
    print(f"\n{'=' * 50}")
    print(f"Summary: Created {created_count}, Skipped {skipped_count}")
    print(f"{'=' * 50}")

    # Verify all collections
    print("\nVerifying collections:")
    for c in client.get_collections().collections:
        try:
            info = client.get_collection(c.name)
            print(f"  {c.name}: {info.points_count} vectors")
        except Exception as e:
            print(f"  {c.name}: Error - {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create unified Qdrant collections")
    parser.add_argument(
        "--url",
        default=None,
        help="Qdrant URL (default: QDRANT_URL env or localhost:6333)",
    )
    parser.add_argument(
        "--vector-size",
        type=int,
        default=1536,
        help="Embedding dimension (default: 1536)",
    )

    args = parser.parse_args()

    create_all_collections(qdrant_url=args.url, vector_size=args.vector_size)
