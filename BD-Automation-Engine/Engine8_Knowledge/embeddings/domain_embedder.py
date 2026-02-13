"""
Domain Embedder — Contrastive learning adapter layer for defense/BD embeddings.

Instead of fine-tuning OpenAI embeddings directly (expensive), trains a small
2-layer MLP projection network (1536→1024→1536) that transforms base embeddings
into a domain-optimized vector space.

Training pairs:
  - Positive: (job desc, matching program), (contact, their program), (query, doc)
  - Negative: random pairs from different programs/domains
  - Loss: InfoNCE contrastive loss

Requires: pip install torch (just the adapter, not a full model)
"""

import os
import sys
import json
import logging
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

logger = logging.getLogger(__name__)

E8_DATA = Path(__file__).parent.parent / "data"
MODEL_DIR = E8_DATA / "models"
EMBEDDINGS_DIR = E8_DATA / "embeddings"

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not installed. pip install torch")


@dataclass
class TrainingResult:
    """Result of adapter training."""
    epochs: int = 0
    final_loss: float = 0.0
    training_pairs: int = 0
    training_time_seconds: float = 0.0
    model_path: str = ""
    trained_at: str = ""


@dataclass
class AdapterConfig:
    """Configuration for the domain adapter."""
    input_dim: int = 1536
    hidden_dim: int = 1024
    output_dim: int = 1536
    trained: bool = False
    training_pairs: int = 0
    trained_at: str = ""
    final_loss: float = 0.0


class DomainAdapter(nn.Module):
    """2-layer MLP projection network for domain adaptation."""

    def __init__(self, input_dim: int = 1536, hidden_dim: int = 1024, output_dim: int = 1536):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, x):
        return F.normalize(self.net(x), dim=-1)


def _info_nce_loss(anchor, positive, negatives, temperature=0.07):
    """InfoNCE contrastive loss."""
    pos_sim = F.cosine_similarity(anchor, positive, dim=-1) / temperature
    neg_sims = F.cosine_similarity(
        anchor.unsqueeze(1), negatives, dim=-1
    ) / temperature
    logits = torch.cat([pos_sim.unsqueeze(1), neg_sims], dim=1)
    labels = torch.zeros(logits.size(0), dtype=torch.long, device=logits.device)
    return F.cross_entropy(logits, labels)


class DomainEmbedder:
    """
    Domain-specific embedder using a trained adapter layer on top of
    base OpenAI embeddings for defense/BD domain optimization.
    """

    def __init__(self):
        self.adapter: Optional["DomainAdapter"] = None
        self.config = AdapterConfig()
        self._base_embedder = None
        self._load_adapter()

    def _load_adapter(self):
        """Load trained adapter if available."""
        if not TORCH_AVAILABLE:
            return

        model_path = MODEL_DIR / "domain_adapter.pt"
        config_path = MODEL_DIR / "adapter_config.json"

        if config_path.exists():
            with open(config_path, "r") as f:
                data = json.load(f)
                self.config = AdapterConfig(**data)

        if model_path.exists() and self.config.trained:
            self.adapter = DomainAdapter(
                self.config.input_dim,
                self.config.hidden_dim,
                self.config.output_dim,
            )
            self.adapter.load_state_dict(torch.load(model_path, map_location="cpu", weights_only=True))
            self.adapter.eval()
            logger.info("Domain adapter loaded from disk")

    def _get_base_embedding(self, text: str) -> List[float]:
        """Get base embedding from OpenAI."""
        try:
            if self._base_embedder is None:
                import openai
                self._base_embedder = openai.OpenAI()

            response = self._base_embedder.embeddings.create(
                model="text-embedding-3-small",
                input=text[:8000],
            )
            return response.data[0].embedding
        except Exception as e:
            logger.warning(f"Base embedding error: {e}")
            # Return zero vector as fallback
            return [0.0] * self.config.input_dim

    def _generate_training_pairs(self, corpus_path: str, max_pairs: int = 10000) -> List[Tuple[str, str]]:
        """
        Generate positive training pairs from corpus data.
        Pairs are (anchor_text, positive_text) from the same program/category.
        """
        # Load corpus
        docs_by_category: Dict[str, List[str]] = {}
        with open(corpus_path, "r", encoding="utf-8") as f:
            for line in f:
                doc = json.loads(line)
                cat = doc.get("category", "other")
                docs_by_category.setdefault(cat, []).append(doc["text"])

        pairs = []

        # Same-category pairs (positive)
        for category, texts in docs_by_category.items():
            if len(texts) < 2:
                continue
            # Sample pairs from same category
            n_pairs = min(len(texts) * 2, max_pairs // len(docs_by_category))
            for _ in range(n_pairs):
                a, b = random.sample(texts, 2)
                if len(a) > 20 and len(b) > 20:
                    pairs.append((a[:500], b[:500]))

        random.shuffle(pairs)
        return pairs[:max_pairs]

    def train_adapter(
        self, corpus_path: Optional[str] = None, epochs: int = 10, batch_size: int = 32
    ) -> TrainingResult:
        """
        Train the domain adapter using contrastive learning on the corpus.

        Args:
            corpus_path: Path to domain_corpus.jsonl (default: auto-detect)
            epochs: Number of training epochs
            batch_size: Training batch size

        Returns:
            TrainingResult with training metrics
        """
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch required for training. pip install torch")

        import time
        start = time.time()

        if corpus_path is None:
            corpus_path = str(EMBEDDINGS_DIR / "domain_corpus.jsonl")

        if not Path(corpus_path).exists():
            raise FileNotFoundError(f"Corpus not found at {corpus_path}. Run build_corpus() first.")

        logger.info("Generating training pairs...")
        pairs = self._generate_training_pairs(corpus_path)
        logger.info(f"Generated {len(pairs)} training pairs")

        if len(pairs) < 10:
            raise ValueError("Too few training pairs. Need at least 10.")

        # Get embeddings for all unique texts
        logger.info("Computing base embeddings for training data...")
        unique_texts = list(set(t for pair in pairs for t in pair))

        # Limit to manageable size for API calls
        if len(unique_texts) > 2000:
            unique_texts = random.sample(unique_texts, 2000)
            pairs = [(a, b) for a, b in pairs if a in set(unique_texts) and b in set(unique_texts)]

        text_to_idx = {t: i for i, t in enumerate(unique_texts)}

        # Batch embed
        embeddings = []
        for text in unique_texts:
            emb = self._get_base_embedding(text)
            embeddings.append(emb)

        emb_tensor = torch.tensor(embeddings, dtype=torch.float32)

        # Initialize adapter
        self.adapter = DomainAdapter(
            self.config.input_dim,
            self.config.hidden_dim,
            self.config.output_dim,
        )
        optimizer = torch.optim.Adam(self.adapter.parameters(), lr=1e-3)

        # Training loop
        self.adapter.train()
        final_loss = 0.0

        for epoch in range(epochs):
            random.shuffle(pairs)
            epoch_loss = 0.0
            n_batches = 0

            for i in range(0, len(pairs), batch_size):
                batch_pairs = pairs[i:i + batch_size]
                if len(batch_pairs) < 2:
                    continue

                anchor_idxs = []
                pos_idxs = []
                for a, b in batch_pairs:
                    if a in text_to_idx and b in text_to_idx:
                        anchor_idxs.append(text_to_idx[a])
                        pos_idxs.append(text_to_idx[b])

                if len(anchor_idxs) < 2:
                    continue

                anchor_emb = self.adapter(emb_tensor[anchor_idxs])
                pos_emb = self.adapter(emb_tensor[pos_idxs])

                # Generate negatives by shifting positives
                neg_idxs = pos_idxs[1:] + pos_idxs[:1]
                neg_emb = self.adapter(emb_tensor[neg_idxs]).unsqueeze(1)

                loss = _info_nce_loss(anchor_emb, pos_emb, neg_emb)

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                epoch_loss += loss.item()
                n_batches += 1

            avg_loss = epoch_loss / max(1, n_batches)
            final_loss = avg_loss
            if epoch % 2 == 0:
                logger.info(f"  Epoch {epoch+1}/{epochs}: loss={avg_loss:.4f}")

        # Save model
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        model_path = MODEL_DIR / "domain_adapter.pt"
        torch.save(self.adapter.state_dict(), model_path)

        self.config.trained = True
        self.config.training_pairs = len(pairs)
        self.config.trained_at = datetime.now().isoformat()
        self.config.final_loss = final_loss

        config_path = MODEL_DIR / "adapter_config.json"
        with open(config_path, "w") as f:
            json.dump(asdict(self.config), f, indent=2)

        self.adapter.eval()
        elapsed = time.time() - start

        result = TrainingResult(
            epochs=epochs,
            final_loss=final_loss,
            training_pairs=len(pairs),
            training_time_seconds=round(elapsed, 1),
            model_path=str(model_path),
            trained_at=self.config.trained_at,
        )

        logger.info(f"Adapter trained: {result.training_pairs} pairs, loss={result.final_loss:.4f}, {result.training_time_seconds}s")
        return result

    def embed(self, text: str) -> List[float]:
        """
        Embed text using domain adapter (or base embeddings if not trained).

        Returns:
            1536-dim embedding vector
        """
        base_emb = self._get_base_embedding(text)

        if self.adapter is not None and TORCH_AVAILABLE:
            with torch.no_grad():
                tensor = torch.tensor([base_emb], dtype=torch.float32)
                adapted = self.adapter(tensor)
                return adapted[0].tolist()

        return base_emb

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of texts."""
        return [self.embed(t) for t in texts]

    def get_status(self) -> Dict:
        """Get adapter status."""
        return {
            "torch_available": TORCH_AVAILABLE,
            "adapter_trained": self.config.trained,
            "training_pairs": self.config.training_pairs,
            "trained_at": self.config.trained_at,
            "final_loss": self.config.final_loss,
            "input_dim": self.config.input_dim,
            "hidden_dim": self.config.hidden_dim,
            "output_dim": self.config.output_dim,
        }


# Singleton
_embedder_instance: Optional[DomainEmbedder] = None


def get_domain_embedder() -> DomainEmbedder:
    """Get domain embedder singleton."""
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = DomainEmbedder()
    return _embedder_instance
