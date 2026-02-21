"""
BD Score Validation & Calibration Engine

Validates BD scoring accuracy against historical placement outcomes
from Bullhorn data. Uses XGBoost to learn optimal weights and compares
against the manual rule-based scoring.
"""

import json
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("bd-score-validator")

PROJECT_ROOT = Path(__file__).parent.parent.parent

# Clearance levels mapped to numeric values for feature encoding
CLEARANCE_LEVELS = {
    "TS/SCI w/ Poly": 6,
    "TS/SCI w/ Full Scope Poly": 6,
    "TS/SCI w/ CI Poly": 5,
    "TS/SCI": 4,
    "Top Secret": 3,
    "Secret": 2,
    "Public Trust": 1,
}


@dataclass
class ValidationResult:
    """Result of a validation run comparing manual vs ML scoring."""

    timestamp: str
    manual_accuracy: float
    ml_accuracy: float
    manual_mae: float
    ml_mae: float
    sample_size: int
    feature_importance: dict
    recommendations: list = field(default_factory=list)


def _encode_clearance(clearance_str: str) -> int:
    """Convert clearance string to numeric level."""
    if not clearance_str:
        return 0
    upper = clearance_str.upper()
    for level_name, value in CLEARANCE_LEVELS.items():
        if level_name.upper() in upper:
            return value
    return 0


def _compute_recency_days(date_str: str) -> int:
    """Compute days since a date string, returning 9999 if unparseable."""
    if not date_str:
        return 9999
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return (datetime.now() - datetime.strptime(date_str, fmt)).days
        except ValueError:
            continue
    return 9999


class BDScoreValidator:
    """Validates and calibrates BD scores against placement outcomes."""

    def __init__(self, bullhorn_db_path: Optional[str] = None):
        self.db_path = bullhorn_db_path or str(
            PROJECT_ROOT / "Engine7_BullhornETL" / "data" / "bullhorn.db"
        )
        self.results_dir = PROJECT_ROOT / "outputs" / "validation"
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """Open a read-only connection to Bullhorn SQLite."""
        conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        return conn

    def _tables_exist(self, conn: sqlite3.Connection) -> bool:
        """Check that the required tables are present."""
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('placements', 'candidates', 'jobs')"
        )
        found = {row["name"] for row in cursor.fetchall()}
        return {"placements", "candidates", "jobs"}.issubset(found)

    def extract_training_data(self) -> list[dict]:
        """Extract placement data from Bullhorn SQLite and correlate with BD signals.

        Joins placements with candidates and jobs to build a feature set:
        - clearance_level (encoded 0-6)
        - program_match (1 if job maps to a known DCGS program, 0 otherwise)
        - location_match (1 if location is a priority site, 0 otherwise)
        - tier (contact tier 1-6, default 5)
        - recency_days (days since placement date)
        - confidence (pay_rate / bill_rate ratio as proxy for margin confidence)
        - outcome (1.0 for completed placement, 0.0 for cancelled/no-show)
        """
        conn = self._get_connection()
        try:
            if not self._tables_exist(conn):
                logger.warning(
                    "Bullhorn database missing required tables (placements, candidates, jobs). "
                    "Returning empty training data."
                )
                return []

            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    p.id AS placement_id,
                    p.placement_date,
                    p.start_date,
                    p.status AS placement_status,
                    p.outcome,
                    p.pay_rate AS p_pay_rate,
                    p.bill_rate AS p_bill_rate,
                    p.client_name,
                    p.job_title AS p_job_title,
                    c.clearance_level,
                    c.city AS candidate_city,
                    c.state AS candidate_state,
                    c.job_title AS candidate_title,
                    j.title AS job_title,
                    j.location AS job_location,
                    j.clearance_required,
                    j.client_corporation,
                    j.prime_contractor,
                    j.pay_rate AS j_pay_rate,
                    j.bill_rate AS j_bill_rate
                FROM placements p
                LEFT JOIN candidates c ON p.candidate_id = c.id
                LEFT JOIN jobs j ON p.job_id = j.id
                ORDER BY p.placement_date DESC
                LIMIT 10000
            """)
            rows = cursor.fetchall()

            if not rows:
                logger.info("No placement records found in Bullhorn database.")
                return []

            priority_locations = {"san diego", "hampton", "dayton"}
            dcgs_keywords = {"dcgs", "distributed common ground"}

            training_data = []
            for row in rows:
                clearance = row["clearance_level"] or row["clearance_required"] or ""
                clearance_level = _encode_clearance(clearance)

                job_title = row["job_title"] or row["p_job_title"] or ""
                prime = row["prime_contractor"] or row["client_corporation"] or row["client_name"] or ""
                program_text = f"{job_title} {prime}".lower()
                program_match = 1 if any(kw in program_text for kw in dcgs_keywords) else 0

                location = row["job_location"] or ""
                candidate_loc = f"{row['candidate_city'] or ''} {row['candidate_state'] or ''}"
                full_location = f"{location} {candidate_loc}".lower()
                location_match = 1 if any(loc in full_location for loc in priority_locations) else 0

                # Default tier (no tier data in placements, use 5 for IC)
                tier = 5

                date_str = row["placement_date"] or row["start_date"] or ""
                recency_days = _compute_recency_days(str(date_str))

                pay = row["p_pay_rate"] or row["j_pay_rate"] or 0
                bill = row["p_bill_rate"] or row["j_bill_rate"] or 0
                if bill and bill > 0 and pay:
                    confidence = min(float(pay) / float(bill), 1.0)
                else:
                    confidence = 0.5

                status = (row["placement_status"] or "").lower()
                outcome_str = (row["outcome"] or "").lower()
                if "complet" in status or "approved" in status or "active" in status:
                    outcome = 1.0
                elif "cancel" in status or "terminated" in status or "fail" in outcome_str:
                    outcome = 0.0
                else:
                    outcome = 0.5

                training_data.append({
                    "clearance_level": clearance_level,
                    "program_match": program_match,
                    "location_match": location_match,
                    "tier": tier,
                    "recency_days": recency_days,
                    "confidence": round(confidence, 4),
                    "outcome": outcome,
                })

            logger.info(f"Extracted {len(training_data)} training samples from Bullhorn placements.")
            return training_data
        finally:
            conn.close()

    def _compute_manual_scores(self, training_data: list[dict]) -> list[float]:
        """Compute rule-based BD scores for each sample, normalised to 0-1."""
        from Engine5_Scoring.scripts.bd_scoring import BD_SCORE_CONFIG

        scores = []
        for sample in training_data:
            score = BD_SCORE_CONFIG["base_score"]

            clearance_boosts = list(BD_SCORE_CONFIG["clearance_boosts"].values())
            if sample["clearance_level"] > 0 and sample["clearance_level"] <= len(clearance_boosts):
                score += clearance_boosts[sample["clearance_level"] - 1]

            if sample["program_match"]:
                score += 15  # DCGS program boost

            if sample["location_match"]:
                score += 10

            multiplier = BD_SCORE_CONFIG["tier_multipliers"].get(sample["tier"], 1.0)
            score = int(score * multiplier)

            score += int(sample["confidence"] * BD_SCORE_CONFIG["match_confidence_weight"])

            scores.append(min(score, 100) / 100.0)
        return scores

    def train_xgboost_model(self, training_data: list[dict]) -> dict:
        """Train XGBoost model on historical outcomes.

        Returns dict with: model, accuracy, mae, feature_importance, predictions.
        """
        import numpy as np
        import xgboost as xgb
        from sklearn.model_selection import cross_val_predict, StratifiedKFold

        feature_names = [
            "clearance_level",
            "program_match",
            "location_match",
            "tier",
            "recency_days",
            "confidence",
        ]
        X = np.array([[s[f] for f in feature_names] for s in training_data], dtype=np.float32)
        y_raw = np.array([s["outcome"] for s in training_data], dtype=np.float32)

        # Binarise: >= 0.5 is positive
        y = (y_raw >= 0.5).astype(int)

        # Handle edge case: if all labels are the same, skip training
        if len(np.unique(y)) < 2:
            logger.warning("All outcomes are identical; cannot train XGBoost classifier.")
            uniform_pred = float(np.mean(y))
            return {
                "model": None,
                "accuracy": 1.0 if uniform_pred >= 0.5 else 0.0,
                "mae": 0.0,
                "feature_importance": {name: 0.0 for name in feature_names},
                "predictions": np.full(len(y), uniform_pred),
            }

        model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            eval_metric="logloss",
            use_label_encoder=False,
            random_state=42,
        )

        n_splits = min(5, len(y))
        if n_splits < 2:
            # Too few samples for cross-validation
            model.fit(X, y)
            preds = model.predict_proba(X)[:, 1]
            accuracy = float(np.mean((preds >= 0.5).astype(int) == y))
            mae = float(np.mean(np.abs(preds - y_raw)))
        else:
            cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
            preds = cross_val_predict(model, X, y, cv=cv, method="predict_proba")[:, 1]
            accuracy = float(np.mean((preds >= 0.5).astype(int) == y))
            mae = float(np.mean(np.abs(preds - y_raw)))
            # Fit on full data for feature importances
            model.fit(X, y)

        importance = model.feature_importances_
        feature_importance = {
            name: round(float(imp), 4)
            for name, imp in zip(feature_names, importance)
        }

        return {
            "model": model,
            "accuracy": round(accuracy, 4),
            "mae": round(mae, 4),
            "feature_importance": feature_importance,
            "predictions": preds,
        }

    def _generate_recommendations(
        self, feature_importance: dict, manual_mae: float, ml_mae: float
    ) -> list[str]:
        """Generate weight adjustment suggestions from XGBoost feature importances."""
        recommendations = []

        if ml_mae < manual_mae:
            improvement = round((manual_mae - ml_mae) / manual_mae * 100, 1)
            recommendations.append(
                f"XGBoost outperforms rule-based scoring by {improvement}% MAE. "
                "Consider adopting ML-assisted scoring."
            )
        else:
            recommendations.append(
                "Rule-based scoring performs comparably to ML. "
                "Current weight configuration is well-calibrated."
            )

        sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        top_feature_name, top_feature_weight = sorted_features[0]
        recommendations.append(
            f"Most predictive feature: '{top_feature_name}' "
            f"(importance={top_feature_weight}). Increase its weight in BD_SCORE_CONFIG."
        )

        least_name, least_weight = sorted_features[-1]
        if least_weight < 0.05:
            recommendations.append(
                f"Feature '{least_name}' has negligible predictive value "
                f"(importance={least_weight}). Consider removing or replacing it."
            )

        return recommendations

    def validate(self) -> ValidationResult:
        """Run full validation: extract data, train model, compare accuracies."""
        import numpy as np

        training_data = self.extract_training_data()

        if not training_data:
            return ValidationResult(
                timestamp=datetime.now().isoformat(),
                manual_accuracy=0.0,
                ml_accuracy=0.0,
                manual_mae=0.0,
                ml_mae=0.0,
                sample_size=0,
                feature_importance={},
                recommendations=[
                    "No training data available. Populate Bullhorn database with "
                    "placement records and re-run validation."
                ],
            )

        # Manual scoring baseline
        manual_scores = self._compute_manual_scores(training_data)
        outcomes = [s["outcome"] for s in training_data]
        manual_preds = np.array(manual_scores)
        y_raw = np.array(outcomes)
        y_binary = (y_raw >= 0.5).astype(int)

        manual_accuracy = float(np.mean((manual_preds >= 0.5).astype(int) == y_binary))
        manual_mae = float(np.mean(np.abs(manual_preds - y_raw)))

        # XGBoost model
        ml_result = self.train_xgboost_model(training_data)
        ml_accuracy = ml_result["accuracy"]
        ml_mae = ml_result["mae"]
        feature_importance = ml_result["feature_importance"]

        recommendations = self._generate_recommendations(feature_importance, manual_mae, ml_mae)

        return ValidationResult(
            timestamp=datetime.now().isoformat(),
            manual_accuracy=round(manual_accuracy, 4),
            ml_accuracy=ml_accuracy,
            manual_mae=round(manual_mae, 4),
            ml_mae=ml_mae,
            sample_size=len(training_data),
            feature_importance=feature_importance,
            recommendations=recommendations,
        )

    def save_report(self, result: ValidationResult) -> str:
        """Save validation report as JSON and return the file path."""
        timestamp_slug = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.results_dir / f"validation_report_{timestamp_slug}.json"

        report_data = {
            "timestamp": result.timestamp,
            "sample_size": result.sample_size,
            "manual_scoring": {
                "accuracy": result.manual_accuracy,
                "mean_absolute_error": result.manual_mae,
            },
            "xgboost_scoring": {
                "accuracy": result.ml_accuracy,
                "mean_absolute_error": result.ml_mae,
            },
            "feature_importance": result.feature_importance,
            "recommendations": result.recommendations,
        }

        with open(report_path, "w") as f:
            json.dump(report_data, f, indent=2)

        logger.info(f"Validation report saved: {report_path}")
        return str(report_path)
