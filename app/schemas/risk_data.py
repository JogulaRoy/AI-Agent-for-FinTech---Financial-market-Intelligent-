"""Risk Agent contracts."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class RiskMetrics(BaseModel):
    annualized_volatility: Optional[float] = None
    downside_volatility: Optional[float] = None
    maximum_drawdown: Optional[float] = None
    value_at_risk_95: Optional[float] = None
    value_at_risk_99: Optional[float] = None
    conditional_var_95: Optional[float] = None
    conditional_var_99: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    beta: Optional[float] = None
    benchmark: Optional[str] = None


class RiskClassification(BaseModel):
    level: str = "Unknown"
    score: Optional[float] = None
    explanation: str = ""
    disclaimer: str = (
        "Project-specific risk score (0-100) derived from historical price "
        "behaviour. Not a regulated financial rating."
    )


class RiskAnalysis(BaseModel):
    company_name: str
    symbol: str
    exchange: Optional[str] = None
    currency: Optional[str] = None
    analysis_period: str = ""
    data_points: int = 0

    risk_free_rate: float = 0.0
    risk_free_rate_source: str = "assumption: 0% (configurable via RISK_FREE_RATE)"

    risk_metrics: RiskMetrics = Field(default_factory=RiskMetrics)
    classification: RiskClassification = Field(default_factory=RiskClassification)
    key_risks: list[str] = Field(default_factory=list)
    risk_summary: str = ""
