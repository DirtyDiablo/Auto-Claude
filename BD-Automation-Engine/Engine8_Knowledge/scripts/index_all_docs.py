"""
Index All Documentation Files
All markdown and text documentation across the entire project
"""
import os
import sys
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
BATCH_SIZE = 50  # Smaller batches for longer docs

BASE_DIR = Path(__file__).parent.parent.parent

# Directories to skip
SKIP_DIRS = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', '.auto-claude'}

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')
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
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE)
        )
        logger.info(f"Created collection: {name}")

def find_all_docs(base_dir: Path) -> list:
    """Find all documentation files."""
    docs = []

    for root, dirs, files in os.walk(base_dir):
        # Skip unwanted directories
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        root_path = Path(root)

        for file in files:
            if file.endswith(('.md', '.txt', '.rst')):
                file_path = root_path / file
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    if len(content.strip()) > 50:  # Skip very short files
                        docs.append({
                            'filename': file,
                            'filepath': str(file_path.relative_to(base_dir)),
                            'content': content[:15000],
                            'type': 'documentation',
                            'directory': str(root_path.relative_to(base_dir))
                        })
                except Exception as e:
                    logger.warning(f"Could not read {file_path}: {e}")

    return docs

def index_records(qdrant: QdrantClient, records: list, collection: str, source: str):
    logger.info(f"Indexing {len(records)} documents to {collection}")
    if not records:
        return 0

    indexed = 0
    points = []

    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i+BATCH_SIZE]
        texts = []
        for r in batch:
            text = f"File: {r.get('filename', '')}\nPath: {r.get('filepath', '')}\n\n{r.get('content', '')}"
            texts.append(text)

        try:
            embeddings = get_embeddings_batch(texts)
            for r, emb, txt in zip(batch, embeddings, texts):
                points.append(PointStruct(
                    id=str(uuid.uuid4()),
                    vector=emb,
                    payload={**r, "content": txt[:5000], "_source": source}
                ))
            indexed += len(batch)

            if len(points) >= 200:
                qdrant.upsert(collection_name=collection, points=points, wait=False)
                logger.info(f"  Uploaded {len(points)} docs | Total: {indexed}")
                points = []

            time.sleep(0.2)  # Slightly longer pause for docs
        except Exception as e:
            logger.error(f"Batch error: {e}")
            time.sleep(1)

    if points:
        qdrant.upsert(collection_name=collection, points=points, wait=False)
        logger.info(f"  Uploaded final {len(points)} docs")

    return indexed

def main():
    logger.info("=" * 60)
    logger.info("ALL DOCUMENTATION INDEXER")
    logger.info("=" * 60)

    qdrant = QdrantClient(url=QDRANT_URL)
    ensure_collection(qdrant, "documents")

    # Find all documentation files
    logger.info(f"Scanning {BASE_DIR} for documentation...")
    docs = find_all_docs(BASE_DIR)
    logger.info(f"Found {len(docs)} documentation files")

    # Group by directory for logging
    dirs = {}
    for doc in docs:
        d = doc['directory']
        dirs[d] = dirs.get(d, 0) + 1

    logger.info("Files by directory:")
    for d, count in sorted(dirs.items(), key=lambda x: -x[1])[:15]:
        logger.info(f"  {d}: {count}")

    # Index all docs
    total = index_records(qdrant, docs, "documents", "project_docs")

    logger.info(f"\nTotal indexed: {total}")

    # Show stats
    for coll in qdrant.get_collections().collections:
        info = qdrant.get_collection(coll.name)
        logger.info(f"{coll.name}: {info.points_count} points")

if __name__ == "__main__":
    main()
