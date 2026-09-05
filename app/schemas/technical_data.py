"""Technical Analysis Agent contracts."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class MovingAverageMetrics(BaseModel):
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_20: Optional[float] = None
    ema_50: Optional[float] = None


class RSIMetrics(BaseModel):
    value: Optional[float] = None
    method: str = "Wilder"
    interpretation: str = "Insufficient Data"


class MACDMetrics(BaseModel):
    macd: Optional[float] = None
    signal: Optional[float] = None
    histogram: Optional[float] = None
    interpretation: str = "Insufficient Data"


class BollingerBandMetrics(BaseModel):
    upper: Optional[float] = None
    middle: Optional[float] = None
    lower: Optional[float] = None
    percent_b: Optional[float] = None
    interpretation: str = "Insufficient Data"


class ATRMetrics(BaseModel):
    value: Optional[float] = None
    percent_of_price: Optional[float] = None
    method: str = "Wilder"


class SupportResistanceMetrics(BaseModel):
    support: Optional[float] = None
    resistance: Optional[float] = None
    position: str = "Insufficient Data"
    methodology: str = (
        "Approximation: rolling min(Low) / max(High) over the lookback window. "
        "Not market-level order-book detection."
    )


class TrendMetrics(BaseModel):
    price_position: str = "Insufficient Data"
    short_term: str = "Insufficient Data"     # 20 vs 50
    long_term: str = "Insufficient Data"      # 50 vs 200
    description: str = ""


class VolumeMetrics(BaseModel):
    latest_volume: Optional[float] = None
    average_volume_20: Optional[float] = None
    volume_ratio: Optional[float] = None
    interpretation: str = "Insufficient Data"


class TechnicalAnalysis(BaseModel):
    symbol: str
    company_name: Optional[str] = None
    current_price: Optional[float] = None
    currency: Optional[str] = None
    bars_analyzed: int = 0
    period: str = ""

    moving_averages: MovingAverageMetrics = Field(default_factory=MovingAverageMetrics)
    rsi: RSIMetrics = Field(default_factory=RSIMetrics)
    macd: MACDMetrics = Field(default_factory=MACDMetrics)
    bollinger_bands: BollingerBandMetrics = Field(default_factory=BollingerBandMetrics)
    atr: ATRMetrics = Field(default_factory=ATRMetrics)
    support_resistance: SupportResistanceMetrics = Field(default_factory=SupportResistanceMetrics)
    trend: TrendMetrics = Field(default_factory=TrendMetrics)
    volume: VolumeMetrics = Field(default_factory=VolumeMetrics)

    momentum: str = "Neutral"
    overall_signal: str = "Neutral"          # Bullish | Neutral | Bearish
    signal_reasons: list[str] = Field(default_factory=list)
    disclaimer: str = (
        "Rule-based technical interpretation of historical price data. "
        "Not financial advice."
    )

    def as_summary(self) -> dict:
        return {
            "trend": self.trend.price_position,
            "rsi": self.rsi.value,
            "macd": self.macd.interpretation,
            "bollinger": self.bollinger_bands.interpretation,
            "support": self.support_resistance.support,
            "resistance": self.support_resistance.resistance,
            "momentum": self.momentum,
            "overall_signal": self.overall_signal,
        }
