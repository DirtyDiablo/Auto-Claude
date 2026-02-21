"""Feature 20 — Multi-Portfolio Expansion (Beyond DCGS).

Provides portfolio configuration, scoring, and registry for multiple
defense program portfolios.
"""

from Engine8_Knowledge.portfolios.portfolio_config import PortfolioConfig
from Engine8_Knowledge.portfolios.registry import PortfolioRegistry, get_portfolio_registry
from Engine8_Knowledge.portfolios.portfolio_scorer import PortfolioScorer

__all__ = [
    "PortfolioConfig",
    "PortfolioRegistry",
    "PortfolioScorer",
    "get_portfolio_registry",
]
