"""
Index Engine3 OrgChart Data
Prime Contacts, Enriched Contacts, Master Contacts
"""

import os
import sys
import json
import csv
import uuid
import logging
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

import openai
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from utils.llm_retry import openai_retry

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
BATCH_SIZE = 100

BASE_DIR = Path(__file__).parent.parent.parent
ENGINE3_DIR = BASE_DIR / "Engine3_OrgChart" / "data"
ENGINE3_DATA = BASE_DIR / "engine_data" / "Engine3_OrgChart"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


@openai_retry
def get_embeddings_batch(texts: list) -> list:
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    truncated = [t[:8000] if t else "empty" for t in texts]
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=truncated)
    return [item.embedding for item in response.data]


def ensure_collection(client: QdrantClient, name: str):
    collections = [c.name for c in client.get_collections().collections]
    if name not in collections:
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )
        logger.info(f"Created collection: {name}")


def load_csv(path: Path) -> list:
    records = []
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(dict(row))
    except Exception as e:
        logger.error(f"Error loading {path}: {e}")
    return records


def load_json(path: Path) -> list:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return [data]
    except Exception as e:
        logger.error(f"Error loading {path}: {e}")
    return []


def build_contact_text(r: dict) -> str:
    parts = []
    for field in [
        "Name",
        "name",
        "First Name",
        "firstName",
        "Last Name",
        "lastName",
        "Title",
        "title",
        "Job Title",
        "jobTitle",
        "Company",
        "company",
        "companyName",
        "Organization",
        "Email",
        "email",
        "Phone",
        "phone",
        "LinkedIn",
        "linkedIn",
        "Program",
        "program",
        "Prime",
        "prime",
        "Location",
        "location",
        "City",
        "State",
        "Notes",
        "notes",
        "Tier",
        "tier",
        "Classification",
        "Skills",
        "Clearance",
        "clearance",
        "Department",
        "department",
        "Division",
        "division",
    ]:
        val = r.get(field)
        if val and isinstance(val, str) and val.strip():
            parts.append(f"{field}: {val}")
    return " | ".join(parts)


def index_records(
    qdrant: QdrantClient, records: list, collection: str, text_builder, source: str
):
    logger.info(f"Indexing {len(records)} records to {collection} from {source}")
    if not records:
        return 0

    indexed = 0
    points = []

    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i : i + BATCH_SIZE]
        texts = [text_builder(r) for r in batch]
        texts = [t if t.strip() else "empty" for t in texts]

        try:
            embeddings = get_embeddings_batch(texts)
            for r, emb, txt in zip(batch, embeddings, texts):
                points.append(
                    PointStruct(
                        id=str(uuid.uuid4()),
                        vector=emb,
                        payload={**r, "content": txt, "_source": source},
                    )
                )
            indexed += len(batch)

            if len(points) >= 500:
                qdrant.upsert(collection_name=collection, points=points, wait=False)
                logger.info(f"  Uploaded {len(points)} points | Total: {indexed}")
                points = []

            time.sleep(0.1)
        except Exception as e:
            logger.error(f"Batch error: {e}")
            time.sleep(1)

    if points:
        qdrant.upsert(collection_name=collection, points=points, wait=False)
        logger.info(f"  Uploaded final {len(points)} points")

    return indexed


def main():
    logger.info("=" * 60)
    logger.info("ENGINE3 ORGCHART CONTACTS INDEXER")
    logger.info("=" * 60)

    qdrant = QdrantClient(url=QDRANT_URL)
    ensure_collection(qdrant, "contacts")

    total = 0

    # Master All Contacts JSON
    for dir in [ENGINE3_DIR, ENGINE3_DATA]:
        master_json = dir / "Prime_Contacts" / "Master_All_Contacts.json"
        if master_json.exists():
            records = load_json(master_json)
            total += index_records(
                qdrant,
                records,
                "contacts",
                build_contact_text,
                "Master_All_Contacts.json",
            )
            break

    # Prime Contacts CSVs
    for dir in [ENGINE3_DIR, ENGINE3_DATA]:
        prime_dir = dir / "Prime_Contacts"
        if prime_dir.exists():
            for csv_file in prime_dir.glob("*.csv"):
                records = load_csv(csv_file)
                total += index_records(
                    qdrant, records, "contacts", build_contact_text, csv_file.name
                )

    # Enriched Contacts CSVs
    for dir in [ENGINE3_DIR, ENGINE3_DATA]:
        enriched_dir = dir / "Prime_Contacts_Enriched"
        if enriched_dir.exists():
            for csv_file in enriched_dir.glob("*.csv"):
                records = load_csv(csv_file)
                total += index_records(
                    qdrant,
                    records,
                    "contacts",
                    build_contact_text,
                    f"enriched_{csv_file.name}",
                )

    # Root level contact CSVs
    contact_files = [
        "DCGS_Contacts.csv",
        "DCGS_ContactsAll.csv",
        "GDIT_Other_Contacts.csv",
        "GDIT Other ContactsAll.csv",
        "GDIT PTS Contacts.csv",
        "GDIT PTS Contacts All.csv",
        "GBSD Contact Chart Updated 9 4.csv",
        "Lockheed Contact.csv",
        "Lockheed ContactAll.csv",
        "Contact_Search_List_MASTER.csv",
        "Bullhorn_Contact_Search.csv",
        "ZoomInfo_Contact_Search.csv",
    ]

    for fname in contact_files:
        for dir in [ENGINE3_DIR, ENGINE3_DATA]:
            path = dir / fname
            if path.exists():
                records = load_csv(path)
                total += index_records(
                    qdrant, records, "contacts", build_contact_text, fname
                )
                break

    logger.info(f"\nTotal indexed: {total}")

    # Show stats
    for coll in qdrant.get_collections().collections:
        info = qdrant.get_collection(coll.name)
        logger.info(f"{coll.name}: {info.points_count} points")


if __name__ == "__main__":
    main()
