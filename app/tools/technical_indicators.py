import pandas as pd
import numpy as np


# ============================================================
# HELPER
# ============================================================


def validate_history(
    history: pd.DataFrame,
) -> pd.DataFrame:
    """
    Validate and prepare historical market data
    for technical analysis.
    """

    if history.empty:
        raise ValueError(
            "Historical market data is empty."
        )

    if "Close" not in history.columns:
        raise ValueError(
            "Historical data must contain a Close column."
        )

    history = history.copy()

    history = history.sort_index()

    history = history.dropna(
        subset=["Close"]
    )

    if len(history) < 2:
        raise ValueError(
            "Not enough historical data "
            "for technical analysis."
        )

    return history


# ============================================================
# SIMPLE MOVING AVERAGE
# ============================================================


def calculate_sma(
    history: pd.DataFrame,
    period: int = 20,
) -> float | None:
    """
    Calculate the latest Simple Moving Average.

    SMA = Average of closing prices over N periods.
    """

    history = validate_history(history)

    if len(history) < period:
        return None

    sma = (
        history["Close"]
        .rolling(window=period)
        .mean()
    )

    latest_sma = sma.iloc[-1]

    if pd.isna(latest_sma):
        return None

    return float(latest_sma)


# ============================================================
# EXPONENTIAL MOVING AVERAGE
# ============================================================


def calculate_ema(
    history: pd.DataFrame,
    period: int = 20,
) -> float | None:
    """
    Calculate the latest Exponential Moving Average.

    EMA gives more weight to recent prices.
    """

    history = validate_history(history)

    if len(history) < period:
        return None

    ema = (
        history["Close"]
        .ewm(
            span=period,
            adjust=False,
        )
        .mean()
    )

    latest_ema = ema.iloc[-1]

    if pd.isna(latest_ema):
        return None

    return float(latest_ema)


# ============================================================
# RSI
# ============================================================


def calculate_rsi(
    history: pd.DataFrame,
    period: int = 14,
) -> float | None:
    """
    Calculate the latest Relative Strength Index.

    RSI range:
        0 - 100

    Common interpretation:
        RSI >= 70 → overbought
        RSI <= 30 → oversold
    """

    history = validate_history(history)

    if len(history) < period + 1:
        return None

    delta = history["Close"].diff()

    gains = delta.clip(
        lower=0
    )

    losses = -delta.clip(
        upper=0
    )

    average_gain = (
        gains
        .rolling(window=period)
        .mean()
    )

    average_loss = (
        losses
        .rolling(window=period)
        .mean()
    )

    if average_loss.iloc[-1] == 0:

        if average_gain.iloc[-1] > 0:
            return 100.0

        return 50.0

    rs = (
        average_gain.iloc[-1]
        / average_loss.iloc[-1]
    )

    rsi = 100 - (
        100 / (1 + rs)
    )

    return float(rsi)


# ============================================================
# MACD
# ============================================================


def calculate_macd(
    history: pd.DataFrame,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> dict:
    """
    Calculate MACD.

    MACD Line:
        EMA(12) - EMA(26)

    Signal Line:
        EMA(9) of MACD Line

    Histogram:
        MACD Line - Signal Line
    """

    history = validate_history(history)

    minimum_required = (
        slow_period + signal_period
    )

    if len(history) < minimum_required:
        return {
            "macd": None,
            "signal": None,
            "histogram": None,
        }

    close = history["Close"]

    fast_ema = (
        close
        .ewm(
            span=fast_period,
            adjust=False,
        )
        .mean()
    )

    slow_ema = (
        close
        .ewm(
            span=slow_period,
            adjust=False,
        )
        .mean()
    )

    macd_line = (
        fast_ema - slow_ema
    )

    signal_line = (
        macd_line
        .ewm(
            span=signal_period,
            adjust=False,
        )
        .mean()
    )

    histogram = (
        macd_line - signal_line
    )

    return {
        "macd": float(
            macd_line.iloc[-1]
        ),

        "signal": float(
            signal_line.iloc[-1]
        ),

        "histogram": float(
            histogram.iloc[-1]
        ),
    }


# ============================================================
# BOLLINGER BANDS
# ============================================================


def calculate_bollinger_bands(
    history: pd.DataFrame,
    period: int = 20,
    standard_deviations: float = 2.0,
) -> dict:
    """
    Calculate Bollinger Bands.

    Middle Band:
        SMA(20)

    Upper Band:
        SMA + 2 × Standard Deviation

    Lower Band:
        SMA - 2 × Standard Deviation
    """

    history = validate_history(history)

    if len(history) < period:
        return {
            "upper": None,
            "middle": None,
            "lower": None,
        }

    close = history["Close"]

    middle = (
        close
        .rolling(window=period)
        .mean()
    )

    standard_deviation = (
        close
        .rolling(window=period)
        .std()
    )

    upper = (
        middle
        + (
            standard_deviation
            * standard_deviations
        )
    )

    lower = (
        middle
        - (
            standard_deviation
            * standard_deviations
        )
    )

    return {
        "upper": float(
            upper.iloc[-1]
        ),

        "middle": float(
            middle.iloc[-1]
        ),

        "lower": float(
            lower.iloc[-1]
        ),
    }


# ============================================================
# PRICE POSITION
# ============================================================


def calculate_price_position(
    history: pd.DataFrame,
    sma_20: float | None,
    sma_50: float | None,
    sma_200: float | None,
) -> str:
    """
    Determine price position relative to
    major moving averages.
    """

    history = validate_history(history)

    current_price = float(
        history["Close"].iloc[-1]
    )

    available_averages = [
        value
        for value in [
            sma_20,
            sma_50,
            sma_200,
        ]
        if value is not None
    ]

    if not available_averages:
        return "Insufficient Data"

    if all(
        current_price > average
        for average in available_averages
    ):
        return "Bullish"

    if all(
        current_price < average
        for average in available_averages
    ):
        return "Bearish"

    return "Mixed"


# ============================================================
# RSI INTERPRETATION
# ============================================================


def interpret_rsi(
    rsi: float | None,
) -> str:
    """
    Interpret RSI using standard thresholds.
    """

    if rsi is None:
        return "Insufficient Data"

    if rsi >= 70:
        return "Overbought"

    if rsi <= 30:
        return "Oversold"

    if rsi >= 50:
        return "Bullish Momentum"

    return "Bearish Momentum"


# ============================================================
# MACD INTERPRETATION
# ============================================================


def interpret_macd(
    macd: float | None,
    signal: float | None,
) -> str:
    """
    Interpret the relationship between
    MACD and Signal lines.
    """

    if macd is None or signal is None:
        return "Insufficient Data"

    if macd > signal and macd > 0:
        return "Bullish"

    if macd < signal and macd < 0:
        return "Bearish"

    if macd > signal:
        return "Bullish Crossover"

    if macd < signal:
        return "Bearish Crossover"

    return "Neutral"


# ============================================================
# OVERALL TECHNICAL SIGNAL
# ============================================================


def calculate_technical_signal(
    trend: str,
    rsi_interpretation: str,
    macd_interpretation: str,
) -> str:
    """
    Produce an explainable overall technical signal.

    This is a rule-based technical interpretation,
    not financial advice.
    """

    bullish_signals = 0
    bearish_signals = 0

    # Trend
    if trend == "Bullish":
        bullish_signals += 1

    elif trend == "Bearish":
        bearish_signals += 1

    # RSI
    if rsi_interpretation in [
        "Bullish Momentum",
    ]:
        bullish_signals += 1

    elif rsi_interpretation in [
        "Bearish Momentum",
        "Overbought",
    ]:
        bearish_signals += 1

    # MACD
    if macd_interpretation in [
        "Bullish",
        "Bullish Crossover",
    ]:
        bullish_signals += 1

    elif macd_interpretation in [
        "Bearish",
        "Bearish Crossover",
    ]:
        bearish_signals += 1

    if bullish_signals >= 2:
        return "Bullish"

    if bearish_signals >= 2:
        return "Bearish"

    return "Neutral"
# ============================================================
# SUPPORT AND RESISTANCE
# ============================================================


def calculate_support_resistance(
    history: pd.DataFrame,
    lookback: int = 60,
) -> dict:
    """
    Estimate historical support and resistance levels.

    Support:
        Recent historical low over the lookback period.

    Resistance:
        Recent historical high over the lookback period.

    This is a simplified quantitative estimate.
    It is not intended to identify exact market levels.
    """

    history = validate_history(history)

    if len(history) < 2:
        return {
            "support": None,
            "resistance": None,
        }

    recent_history = history.tail(
        min(lookback, len(history))
    )

    support = recent_history["Low"].min()

    resistance = recent_history["High"].max()

    if pd.isna(support) or pd.isna(resistance):
        return {
            "support": None,
            "resistance": None,
        }

    return {
        "support": float(support),
        "resistance": float(resistance),
    }


def calculate_support_resistance_position(
    current_price: float,
    support: float | None,
    resistance: float | None,
) -> str:
    """
    Determine where the current price sits relative
    to the estimated support and resistance levels.
    """

    if support is None or resistance is None:
        return "Insufficient Data"

    if resistance <= support:
        return "Insufficient Data"

    price_range = resistance - support

    support_zone = (
        support + price_range * 0.20
    )

    resistance_zone = (
        resistance - price_range * 0.20
    )

    if current_price <= support_zone:
        return "Near Support"

    if current_price >= resistance_zone:
        return "Near Resistance"

    return "Between Support and Resistance"