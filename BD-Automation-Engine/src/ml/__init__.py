"""
Phase 32A: Predictive Intelligence Engine.

ML models that forecast BD outcomes, win probabilities, and optimal timing:
- WinProbabilityModel: XGBoost-based placement probability with SHAP explanations
- OpportunityScorer: Composite 6-dimension scoring + pipeline ranking
- HiringForecaster: Time-series forecasting for hiring patterns
- BudgetCyclePredictor: Federal budget cycle intelligence + recompete timing
"""

from src.ml.win_probability import WinProbabilityModel, WinPrediction, get_win_model
from src.ml.opportunity_scorer import OpportunityScorer, ScoredOpportunity
from src.ml.hiring_forecaster import HiringForecaster, HiringForecast
from src.ml.budget_predictor import BudgetCyclePredictor, SpendingWindow

__all__ = [
    "WinProbabilityModel",
    "WinPrediction",
    "get_win_model",
    "OpportunityScorer",
    "ScoredOpportunity",
    "HiringForecaster",
    "HiringForecast",
    "BudgetCyclePredictor",
    "SpendingWindow",
]
