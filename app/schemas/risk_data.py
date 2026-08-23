from typing import Optional

from pydantic import BaseModel, Field


# ============================================================
# RISK METRICS
# ============================================================

class RiskMetrics(BaseModel):
    """
    Quantitative risk measurements calculated
    from historical stock returns.
    """

    annualized_volatility: Optional[float] = None

    downside_volatility: Optional[float] = None

    maximum_drawdown: Optional[float] = None

    value_at_risk_95: Optional[float] = None

    value_at_risk_99: Optional[float] = None

    conditional_var_95: Optional[float] = None

    conditional_var_99: Optional[float] = None

    sharpe_ratio: Optional[float] = None

    sortino_ratio: Optional[float] = None


# ============================================================
# RISK CLASSIFICATION
# ============================================================

class RiskClassification(BaseModel):
    """
    Human-readable interpretation of quantitative risk.
    """

    level: str = "Unknown"

    score: Optional[float] = None

    explanation: str = ""


# ============================================================
# RISK ANALYSIS
# ============================================================

class RiskAnalysis(BaseModel):
    """
    Complete structured output of the Risk Agent.

    This object is designed to be consumed later
    by the multi-agent orchestrator.
    """

    company_name: str

    symbol: str

    exchange: str

    currency: str

    analysis_period: str

    data_points: int = 0

    risk_metrics: RiskMetrics

    classification: RiskClassification

    key_risks: list[str] = Field(
        default_factory=list
    )

    risk_summary: str = ""