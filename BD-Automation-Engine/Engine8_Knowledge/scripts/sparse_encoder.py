"""
BM25 Sparse Vector Encoder for Qdrant.

Converts text to Qdrant SparseVector using term-frequency weights.
Qdrant's Modifier.IDF handles IDF server-side, so we only compute TF here.

Usage:
    encoder = BM25SparseEncoder()
    sparse = encoder.encode_document("DCGS analyst TS/SCI clearance")
    sparse_q = encoder.encode_query("DCGS analyst")
"""

import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional
from collections import Counter

from qdrant_client.models import SparseVector

logger = logging.getLogger(__name__)

# Common English stopwords (kept small for BD/defense domain relevance)
STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "shall",
        "can",
        "need",
        "dare",
        "ought",
        "and",
        "but",
        "or",
        "nor",
        "not",
        "so",
        "yet",
        "both",
        "either",
        "neither",
        "each",
        "every",
        "all",
        "any",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "no",
        "only",
        "own",
        "same",
        "than",
        "too",
        "very",
        "just",
        "because",
        "as",
        "until",
        "while",
        "of",
        "at",
        "by",
        "for",
        "with",
        "about",
        "against",
        "between",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "to",
        "from",
        "up",
        "down",
        "in",
        "out",
        "on",
        "off",
        "over",
        "under",
        "again",
        "further",
        "then",
        "once",
        "here",
        "there",
        "when",
        "where",
        "why",
        "how",
        "what",
        "which",
        "who",
        "whom",
        "this",
        "that",
        "these",
        "those",
        "i",
        "me",
        "my",
        "we",
        "our",
        "you",
        "your",
        "he",
        "him",
        "his",
        "she",
        "her",
        "it",
        "its",
        "they",
        "them",
        "their",
    }
)

DEFAULT_VOCAB_DIR = Path(__file__).parent.parent / "data" / "vocab"


class BM25SparseEncoder:
    """Converts text to Qdrant SparseVector using term-frequency weights.

    Vocabulary is a {term: integer_index} mapping persisted to JSON.
    Values are raw term frequencies; Qdrant's Modifier.IDF handles IDF server-side.
    """

    def __init__(self, vocab_path: Optional[Path] = None):
        self.vocab: Dict[str, int] = {}
        self._next_index: int = 0
        self.vocab_path = vocab_path
        if vocab_path and Path(vocab_path).exists():
            self._load_vocab(vocab_path)

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Lowercase, extract alphanumeric tokens, remove stopwords."""
        tokens = re.findall(r"[a-z0-9]+(?:[/\-][a-z0-9]+)*", text.lower())
        return [t for t in tokens if t not in STOPWORDS and len(t) > 1]

    def encode_document(self, text: str) -> SparseVector:
        """Encode document text into a sparse vector, adding new tokens to vocab."""
        tokens = self._tokenize(text)
        if not tokens:
            return SparseVector(indices=[], values=[])

        tf = Counter(tokens)
        indices = []
        values = []

        for token, count in tf.items():
            if token not in self.vocab:
                self.vocab[token] = self._next_index
                self._next_index += 1
            indices.append(self.vocab[token])
            values.append(float(count))

        return SparseVector(indices=indices, values=values)

    def encode_query(self, text: str) -> SparseVector:
        """Encode query text into a sparse vector, skipping unknown tokens."""
        tokens = self._tokenize(text)
        if not tokens:
            return SparseVector(indices=[], values=[])

        tf = Counter(tokens)
        indices = []
        values = []

        for token, count in tf.items():
            if token in self.vocab:
                indices.append(self.vocab[token])
                values.append(float(count))

        return SparseVector(indices=indices, values=values)

    def save_vocab(self, path: Optional[Path] = None):
        """Persist vocabulary to JSON file."""
        save_path = Path(path or self.vocab_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w") as f:
            json.dump(self.vocab, f)
        logger.info(f"Saved vocab ({len(self.vocab)} terms) to {save_path}")

    def _load_vocab(self, path: Path):
        """Load vocabulary from JSON file."""
        with open(path, "r") as f:
            self.vocab = json.load(f)
        self._next_index = max(self.vocab.values()) + 1 if self.vocab else 0
        logger.info(f"Loaded vocab ({len(self.vocab)} terms) from {path}")
