"""Phase 36A — Revenue Intelligence Engine + Deal Analytics."""

from src.revenue.revenue_tracker import (
    RevenueTracker,
    Placement,
    RevenueRecord,
    RevenueSummary,
    MarginAnalysis,
    ConcentrationRisk,
    get_revenue_tracker,
)
from src.revenue.deal_lifecycle import (
    DealLifecycleEngine,
    Deal,
    DealStage,
    StageVelocity,
    DropOffAnalysis,
    WinRateAnalysis,
    StaleDeal,
    get_deal_engine,
)
from src.revenue.roi_calculator import (
    ROICalculator,
    CampaignROI,
    ContactROI,
    ProgramROI,
    ChannelROI,
    get_roi_calculator,
)
from src.revenue.executive_analytics import (
    ExecutiveAnalytics,
    ExecutiveSummary,
    QuotaAttainment,
    DiversificationScore,
    get_executive_analytics,
)

__all__ = [
    "RevenueTracker", "Placement", "RevenueRecord", "RevenueSummary",
    "MarginAnalysis", "ConcentrationRisk", "get_revenue_tracker",
    "DealLifecycleEngine", "Deal", "DealStage", "StageVelocity",
    "DropOffAnalysis", "WinRateAnalysis", "StaleDeal", "get_deal_engine",
    "ROICalculator", "CampaignROI", "ContactROI", "ProgramROI",
    "ChannelROI", "get_roi_calculator",
    "ExecutiveAnalytics", "ExecutiveSummary", "QuotaAttainment",
    "DiversificationScore", "get_executive_analytics",
]
