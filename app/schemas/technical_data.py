from pydantic import BaseModel


# ============================================================
# MOVING AVERAGES
# ============================================================


class MovingAverageMetrics(BaseModel):

    sma_20: float | None = None
    sma_50: float | None = None
    sma_200: float | None = None

    ema_20: float | None = None
    ema_50: float | None = None


# ============================================================
# RSI
# ============================================================


class RSIMetrics(BaseModel):

    value: float | None = None

    interpretation: str = (
        "Insufficient Data"
    )


# ============================================================
# MACD
# ============================================================


class MACDMetrics(BaseModel):

    macd: float | None = None

    signal: float | None = None

    histogram: float | None = None

    interpretation: str = (
        "Insufficient Data"
    )


# ============================================================
# BOLLINGER BANDS
# ============================================================


class BollingerBandMetrics(BaseModel):

    upper: float | None = None

    middle: float | None = None

    lower: float | None = None


# ============================================================
# SUPPORT / RESISTANCE
# ============================================================


class SupportResistanceMetrics(BaseModel):

    support: float | None = None

    resistance: float | None = None

    position: str = (
        "Insufficient Data"
    )


# ============================================================
# TREND
# ============================================================


class TrendMetrics(BaseModel):

    price_position: str = (
        "Insufficient Data"
    )


# ============================================================
# COMPLETE TECHNICAL ANALYSIS
# ============================================================


class TechnicalAnalysis(BaseModel):
    """
    Complete structured output of the
    Technical Agent.
    """

    symbol: str

    current_price: float

    currency: str

    moving_averages: MovingAverageMetrics

    rsi: RSIMetrics

    macd: MACDMetrics

    bollinger_bands: BollingerBandMetrics

    support_resistance: SupportResistanceMetrics

    trend: TrendMetrics

    overall_signal: str = "Neutral"