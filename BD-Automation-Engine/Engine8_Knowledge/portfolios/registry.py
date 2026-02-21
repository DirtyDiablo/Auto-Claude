"""Portfolio registry — singleton manager for available portfolio configurations."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from Engine8_Knowledge.portfolios.portfolio_config import PortfolioConfig, DEFAULT_PORTFOLIOS
from Engine8_Knowledge.portfolios.portfolio_scorer import PortfolioScorer

try:
    import structlog

    logger = structlog.get_logger("PortfolioRegistry")
except ImportError:
    logger = logging.getLogger("PortfolioRegistry")


class PortfolioRegistry:
    """Manages available portfolio configurations."""

    def __init__(self):
        self._portfolios: Dict[str, PortfolioConfig] = {}
        self._load_defaults()

    def _load_defaults(self) -> None:
        """Load the built-in default portfolios."""
        for portfolio in DEFAULT_PORTFOLIOS:
            self._portfolios[portfolio.id] = portfolio
        logger.info("Loaded default portfolios", count=len(self._portfolios))

    def get(self, portfolio_id: str) -> Optional[PortfolioConfig]:
        """Retrieve a portfolio by ID, or None if not found."""
        return self._portfolios.get(portfolio_id)

    def list_all(self) -> List[PortfolioConfig]:
        """Return all registered portfolios."""
        return list(self._portfolios.values())

    def register(self, config: PortfolioConfig) -> None:
        """Register or replace a portfolio configuration."""
        self._portfolios[config.id] = config
        logger.info("Registered portfolio", portfolio_id=config.id, name=config.name)

    def get_scorer(self, portfolio_id: str) -> Optional[PortfolioScorer]:
        """Return a PortfolioScorer for the given portfolio, or None."""
        config = self.get(portfolio_id)
        if config is None:
            return None
        return PortfolioScorer(config)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_registry: Optional[PortfolioRegistry] = None


def get_portfolio_registry() -> PortfolioRegistry:
    """Return the singleton PortfolioRegistry instance."""
    global _registry
    if _registry is None:
        _registry = PortfolioRegistry()
    return _registry
