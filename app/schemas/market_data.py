from pydantic import BaseModel


# ============================================================
# STOCK
# ============================================================


class StockInfo(BaseModel):
    name: str
    symbol: str
    exchange: str
    currency: str


# ============================================================
# PRICE
# ============================================================


class PriceInfo(BaseModel):
    value: float
    currency: str
    symbol: str


# ============================================================
# HISTORICAL DATA
# ============================================================


class HistoricalPrice(BaseModel):
    date: str

    open: float
    high: float
    low: float
    close: float

    volume: int


# ============================================================
# PERFORMANCE
# ============================================================


class PerformanceMetrics(BaseModel):
    daily_return: float | None = None

    monthly_return: float | None = None

    six_month_return: float | None = None

    one_year_return: float | None = None


# ============================================================
# STABILITY
# ============================================================


class StabilityMetrics(BaseModel):
    annualized_volatility: float | None = None

    downside_volatility: float | None = None

    maximum_drawdown: float | None = None

    positive_days_ratio: float | None = None

    negative_days_ratio: float | None = None

    average_daily_return: float | None = None

    best_day: float | None = None

    worst_day: float | None = None

    classification: str = "Insufficient Data"


# ============================================================
# DATA QUALITY
# ============================================================


class DataQuality(BaseModel):
    rows_returned: int

    rows_removed: int

    start_date: str

    end_date: str


# ============================================================
# COMPLETE DATA AGENT OUTPUT
# ============================================================


class MarketData(BaseModel):
    """
    Complete contract produced by the Data Agent.

    This is the structure that can later be placed
    into LangGraph state and serialized to JSON.
    """

    stock: StockInfo

    price: PriceInfo

    requested_period: str

    historical_data: list[HistoricalPrice]

    performance: PerformanceMetrics

    stability: StabilityMetrics

    data_quality: DataQuality