"""
Response Prediction Model — XGBoost classifier for contact response likelihood.

Predicts the probability that a contact will respond to BD outreach based on
contact tier, interaction history, channel, program context, and timing.
"""

import os
import logging
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score
from xgboost import XGBClassifier

logger = logging.getLogger(__name__)

# ─── Feature Definitions ────────────────────────────────────────────────────

FEATURE_NAMES = [
    "contact_tier",  # 1-6 (1=executive, 6=individual)
    "interaction_count",  # total past interactions
    "days_since_last",  # days since last interaction
    "channel_email",  # 1 if email channel
    "channel_linkedin",  # 1 if linkedin channel
    "channel_phone",  # 1 if phone channel
    "program_value_log",  # log10(contract value) to normalize
    "hiring_velocity",  # job postings per month for related program
    "day_of_week",  # 0=Monday .. 6=Sunday
]

CHANNEL_MAP = {"email": 0, "linkedin": 1, "phone": 2}

MODEL_DIR = Path(os.path.dirname(os.path.dirname(__file__))) / "data" / "models"


def _encode_channel(channel: str) -> tuple:
    """One-hot encode channel into (email, linkedin, phone)."""
    ch = channel.lower().strip()
    return (
        1.0 if ch == "email" else 0.0,
        1.0 if ch == "linkedin" else 0.0,
        1.0 if ch == "phone" else 0.0,
    )


def _safe_log_value(value) -> float:
    """Convert contract value string to log10 scale."""
    if not value:
        return 0.0
    try:
        v = (
            str(value)
            .replace("$", "")
            .replace(",", "")
            .replace("B", "e9")
            .replace("M", "e6")
            .replace("K", "e3")
        )
        num = float(v)
        return np.log10(max(num, 1.0))
    except (ValueError, TypeError):
        return 0.0


# ─── Synthetic Data Generator ───────────────────────────────────────────────


class SyntheticDataGenerator:
    """
    Generate realistic training data from Bullhorn activity patterns.

    Uses contact tier distributions and interaction patterns to build
    labeled examples where response = 1 when contact responded and 0 otherwise.
    """

    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)

    def generate(self, n_samples: int = 5000) -> tuple:
        """
        Generate synthetic features and labels.

        Returns:
            (X: np.ndarray of shape [n, 9], y: np.ndarray of shape [n])
        """
        X = np.zeros((n_samples, len(FEATURE_NAMES)), dtype=np.float32)
        y = np.zeros(n_samples, dtype=np.int32)

        for i in range(n_samples):
            # Contact tier (weighted: more lower-tier contacts exist)
            tier = self.rng.choice(
                [1, 2, 3, 4, 5, 6], p=[0.05, 0.10, 0.15, 0.25, 0.25, 0.20]
            )

            # Interaction count (higher for lower tiers = more active relationships)
            base_interactions = max(0, int(self.rng.normal(15 - tier * 2, 5)))
            interaction_count = min(base_interactions, 50)

            # Days since last interaction
            days_since = max(0, int(self.rng.exponential(30 + tier * 10)))

            # Channel selection (execs prefer email, juniors more varied)
            if tier <= 2:
                channel = self.rng.choice(
                    ["email", "linkedin", "phone"], p=[0.6, 0.25, 0.15]
                )
            else:
                channel = self.rng.choice(
                    ["email", "linkedin", "phone"], p=[0.35, 0.40, 0.25]
                )

            ch_email, ch_linkedin, ch_phone = _encode_channel(channel)

            # Program value (log scale, 6-10 range = $1M to $10B)
            program_value_log = float(self.rng.normal(8.5, 1.0))

            # Hiring velocity (0-20 postings/month)
            hiring_velocity = max(0, float(self.rng.exponential(3.0)))

            # Day of week
            day_of_week = self.rng.integers(0, 7)

            # Build feature vector
            X[i] = [
                tier,
                interaction_count,
                days_since,
                ch_email,
                ch_linkedin,
                ch_phone,
                program_value_log,
                hiring_velocity,
                day_of_week,
            ]

            # Generate label: response probability based on realistic factors
            # Higher tiers = lower base response rate
            # More interactions = higher response rate
            # Recent contact = higher response rate
            # Tuesday-Thursday = best days
            base_prob = 0.7 - (tier - 1) * 0.08
            interaction_bonus = min(interaction_count * 0.01, 0.15)
            recency_penalty = min(days_since * 0.002, 0.3)
            day_bonus = 0.05 if day_of_week in [1, 2, 3] else -0.02
            channel_bonus = 0.05 if channel == "email" and tier <= 3 else 0.0
            channel_bonus += 0.03 if channel == "linkedin" and tier >= 3 else 0.0
            velocity_bonus = min(hiring_velocity * 0.01, 0.1)

            prob = (
                base_prob
                + interaction_bonus
                - recency_penalty
                + day_bonus
                + channel_bonus
                + velocity_bonus
            )
            prob = np.clip(prob, 0.05, 0.95)

            # Add noise
            prob += self.rng.normal(0, 0.08)
            prob = np.clip(prob, 0.0, 1.0)

            y[i] = 1 if self.rng.random() < prob else 0

        return X, y


# ─── Response Predictor Model ───────────────────────────────────────────────


class ResponsePredictor:
    """
    XGBoost-based contact response prediction model.

    Predicts the probability that a contact will respond to BD outreach.
    """

    def __init__(self):
        self.model: Optional[XGBClassifier] = None
        self.trained_at: Optional[str] = None
        self.accuracy: Optional[float] = None
        self.auc: Optional[float] = None
        self.model_path = MODEL_DIR / "response_predictor.joblib"

    @property
    def is_loaded(self) -> bool:
        return self.model is not None

    def train(self, n_samples: int = 5000) -> Dict[str, Any]:
        """
        Train the model on synthetic data.

        Returns:
            Training metrics dict
        """
        logger.info(f"Generating {n_samples} synthetic training samples...")
        gen = SyntheticDataGenerator()
        X, y = gen.generate(n_samples)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        logger.info("Training XGBoost classifier...")
        self.model = XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric="logloss",
        )
        self.model.fit(X_train, y_train)

        # Evaluate
        y_pred = self.model.predict(X_test)
        y_prob = self.model.predict_proba(X_test)[:, 1]

        self.accuracy = float(accuracy_score(y_test, y_pred))
        self.auc = float(roc_auc_score(y_test, y_prob))
        self.trained_at = datetime.now().isoformat()

        logger.info(f"Model trained: accuracy={self.accuracy:.3f}, AUC={self.auc:.3f}")

        # Save
        self._save()

        return {
            "accuracy": self.accuracy,
            "auc": self.auc,
            "trained_at": self.trained_at,
            "n_samples": n_samples,
            "n_features": len(FEATURE_NAMES),
            "positive_rate": float(y.mean()),
        }

    def _save(self):
        """Save model to disk."""
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "model": self.model,
            "trained_at": self.trained_at,
            "accuracy": self.accuracy,
            "auc": self.auc,
        }
        joblib.dump(data, self.model_path)
        logger.info(f"Model saved to {self.model_path}")

    def load(self) -> bool:
        """Load model from disk. Returns True if successful."""
        if not self.model_path.exists():
            logger.info("No saved model found, training new model...")
            self.train()
            return True

        try:
            data = joblib.load(self.model_path)
            self.model = data["model"]
            self.trained_at = data["trained_at"]
            self.accuracy = data["accuracy"]
            self.auc = data["auc"]
            logger.info(
                f"Model loaded from {self.model_path} (trained: {self.trained_at})"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    def predict(self, features: Dict[str, Any]) -> float:
        """
        Predict response probability for a single contact.

        Args:
            features: Dict with keys matching FEATURE_NAMES concepts:
                - contact_tier: int (1-6)
                - interaction_count: int
                - days_since_last: int
                - channel: str ("email", "linkedin", "phone")
                - program_value: str or float
                - hiring_velocity: float
                - day_of_week: int (0-6, 0=Monday)

        Returns:
            Response probability (0.0 to 1.0)
        """
        if not self.is_loaded:
            self.load()

        x = self._features_to_array(features)
        prob = self.model.predict_proba(x.reshape(1, -1))[0, 1]
        return float(prob)

    def batch_predict(self, contacts_list: List[Dict[str, Any]]) -> List[float]:
        """
        Predict response probabilities for multiple contacts.

        Args:
            contacts_list: List of feature dicts

        Returns:
            List of probabilities
        """
        if not self.is_loaded:
            self.load()

        if not contacts_list:
            return []

        X = np.array([self._features_to_array(f) for f in contacts_list])
        probs = self.model.predict_proba(X)[:, 1]
        return [float(p) for p in probs]

    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores from the trained model."""
        if not self.is_loaded:
            return {}

        importances = self.model.feature_importances_
        return {name: float(imp) for name, imp in zip(FEATURE_NAMES, importances)}

    def get_status(self) -> Dict[str, Any]:
        """Get model status info."""
        return {
            "loaded": self.is_loaded,
            "trained_at": self.trained_at,
            "accuracy": self.accuracy,
            "auc": self.auc,
            "model_path": str(self.model_path),
            "feature_names": FEATURE_NAMES,
            "feature_importance": self.get_feature_importance()
            if self.is_loaded
            else {},
        }

    def _features_to_array(self, features: Dict[str, Any]) -> np.ndarray:
        """Convert feature dict to numpy array."""
        channel = features.get("channel", "email")
        ch_email, ch_linkedin, ch_phone = _encode_channel(channel)

        return np.array(
            [
                float(features.get("contact_tier", 3)),
                float(features.get("interaction_count", 0)),
                float(features.get("days_since_last", 30)),
                ch_email,
                ch_linkedin,
                ch_phone,
                _safe_log_value(features.get("program_value", 0)),
                float(features.get("hiring_velocity", 0)),
                float(features.get("day_of_week", datetime.now().weekday())),
            ],
            dtype=np.float32,
        )


# ─── Singleton ──────────────────────────────────────────────────────────────

_predictor: Optional[ResponsePredictor] = None


def get_response_predictor() -> ResponsePredictor:
    """Get or create the singleton ResponsePredictor."""
    global _predictor
    if _predictor is None:
        _predictor = ResponsePredictor()
        _predictor.load()
    return _predictor
