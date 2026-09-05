"""Market data contracts produced by the Data Agent's provider layer."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import DataProvenance
from app.schemas.fundamentals import Fundamentals


# ============================================================
# COMPANY PROFILE
# ============================================================


class CompanyProfile(BaseModel):
    company_name: str
    symbol: str
    exchange: Optional[str] = None
    country: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    currency: Optional[str] = None
    market_cap: Optional[float] = None
    shares_outstanding: Optional[float] = None
    description: Optional[str] = None
    website: Optional[str] = None
    isin: Optional[str] = None

    provenance: Optional[DataProvenance] = None


# ============================================================
# CURRENT QUOTE
# ============================================================


class Quote(BaseModel):
    price: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    previous_close: Optional[float] = None
    volume: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    week52_high: Optional[float] = None
    week52_low: Optional[float] = None
    currency: Optional[str] = None
    timestamp: Optional[str] = None

    provenance: Optional[DataProvenance] = None


# ============================================================
# HISTORICAL OHLCV
# ============================================================


class OHLCVBar(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    adjusted_close: Optional[float] = None
    volume: float = 0.0


class PriceHistory(BaseModel):
    bars: list[OHLCVBar] = Field(default_factory=list)
    frequency: str = "daily"
    adjusted: bool = False
    currency: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    provenance: Optional[DataProvenance] = None

    def __len__(self) -> int:  # convenience
        return len(self.bars)


# ============================================================
# DATA QUALITY REPORT
# ============================================================


class DataQualityReport(BaseModel):
    rows_returned: int = 0
    rows_removed: int = 0
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    issues: list[str] = Field(default_factory=list)
    passed: bool = True


# ============================================================
# PERFORMANCE / STABILITY (kept from the original Data Agent)
# ============================================================


class PerformanceMetrics(BaseModel):
    daily_return: Optional[float] = None
    monthly_return: Optional[float] = None
    six_month_return: Optional[float] = None
    one_year_return: Optional[float] = None


class StabilityMetrics(BaseModel):
    annualized_volatility: Optional[float] = None
    downside_volatility: Optional[float] = None
    maximum_drawdown: Optional[float] = None
    positive_days_ratio: Optional[float] = None
    negative_days_ratio: Optional[float] = None
    average_daily_return: Optional[float] = None
    best_day: Optional[float] = None
    worst_day: Optional[float] = None
    classification: str = "Insufficient Data"


# ============================================================
# COMPLETE DATA AGENT OUTPUT
# ============================================================


class DataAgentResult(BaseModel):
    """Everything the Data Agent supplies to the rest of the system."""

    profile: CompanyProfile
    quote: Quote
    history: PriceHistory
    fundamentals: Fundamentals = Field(default_factory=Fundamentals)
    performance: PerformanceMetrics = Field(default_factory=PerformanceMetrics)
    stability: StabilityMetrics = Field(default_factory=StabilityMetrics)
    data_quality: DataQualityReport = Field(default_factory=DataQualityReport)
    requested_period: str = "5y"
    sources_used: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
