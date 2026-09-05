import pandas as pd
import pytest

from app.tools.technical_indicators import (
    validate_history,
    calculate_sma,
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_price_position,
    interpret_rsi,
    interpret_macd,
    calculate_technical_signal,
    calculate_support_resistance,
    calculate_support_resistance_position,
)


# ============================================================
# VALIDATION
# ============================================================

def test_validate_history_raises_on_empty():

    with pytest.raises(ValueError):
        validate_history(pd.DataFrame())


def test_validate_history_raises_without_close_column():

    frame = pd.DataFrame({"Open": [1.0, 2.0]})

    with pytest.raises(ValueError):
        validate_history(frame)


def test_validate_history_raises_on_single_row(single_row_history):

    with pytest.raises(ValueError):
        validate_history(single_row_history)


# ============================================================
# MOVING AVERAGES
# ============================================================

def test_sma_matches_manual_rolling_mean(sample_history):

    expected = (
        sample_history["Close"]
        .rolling(window=20)
        .mean()
        .iloc[-1]
    )

    assert calculate_sma(sample_history, period=20) == pytest.approx(expected)


def test_sma_none_when_fewer_rows_than_period(tiny_history):

    assert calculate_sma(tiny_history, period=20) is None


def test_ema_matches_manual_ewm(sample_history):

    expected = (
        sample_history["Close"]
        .ewm(span=20, adjust=False)
        .mean()
        .iloc[-1]
    )

    assert calculate_ema(sample_history, period=20) == pytest.approx(expected)


def test_ema_none_when_fewer_rows_than_period(tiny_history):

    assert calculate_ema(tiny_history, period=20) is None


# ============================================================
# RSI
# ============================================================

def test_rsi_within_bounds(sample_history):

    rsi = calculate_rsi(sample_history, period=14)

    assert rsi is not None
    assert 0.0 <= rsi <= 100.0


def test_rsi_is_100_for_strictly_rising_series(rising_history):

    assert calculate_rsi(rising_history, period=14) == pytest.approx(100.0)


def test_rsi_is_0_for_strictly_falling_series(falling_history):

    assert calculate_rsi(falling_history, period=14) == pytest.approx(0.0)


def test_rsi_none_when_insufficient_rows(tiny_history):

    assert calculate_rsi(tiny_history, period=14) is None


# ============================================================
# MACD
# ============================================================

def test_macd_histogram_equals_macd_minus_signal(sample_history):

    result = calculate_macd(sample_history)

    assert result["macd"] is not None

    assert result["histogram"] == pytest.approx(
        result["macd"] - result["signal"]
    )


def test_macd_all_none_when_insufficient_rows(tiny_history):

    result = calculate_macd(tiny_history)

    assert result == {"macd": None, "signal": None, "histogram": None}


# ============================================================
# BOLLINGER BANDS
# ============================================================

def test_bollinger_bands_ordering(sample_history):

    bands = calculate_bollinger_bands(sample_history)

    assert bands["lower"] < bands["middle"] < bands["upper"]


def test_bollinger_middle_matches_sma_20(sample_history):

    bands = calculate_bollinger_bands(sample_history, period=20)

    assert bands["middle"] == pytest.approx(
        calculate_sma(sample_history, period=20)
    )


def test_bollinger_bands_all_none_when_insufficient_rows(tiny_history):

    bands = calculate_bollinger_bands(tiny_history, period=20)

    assert bands == {"upper": None, "middle": None, "lower": None}


# ============================================================
# PRICE POSITION
# ============================================================

def test_price_position_bullish_when_above_all_averages(rising_history):

    result = calculate_price_position(
        rising_history,
        sma_20=100.0,
        sma_50=100.0,
        sma_200=100.0,
    )

    assert result == "Bullish"


def test_price_position_bearish_when_below_all_averages(rising_history):

    result = calculate_price_position(
        rising_history,
        sma_20=1000.0,
        sma_50=1000.0,
        sma_200=1000.0,
    )

    assert result == "Bearish"


def test_price_position_mixed_when_averages_disagree(rising_history):

    result = calculate_price_position(
        rising_history,
        sma_20=100.0,
        sma_50=1000.0,
        sma_200=None,
    )

    assert result == "Mixed"


def test_price_position_insufficient_data_when_no_averages(rising_history):

    result = calculate_price_position(
        rising_history,
        sma_20=None,
        sma_50=None,
        sma_200=None,
    )

    assert result == "Insufficient Data"


# ============================================================
# RSI / MACD INTERPRETATION
# ============================================================

@pytest.mark.parametrize(
    "rsi, expected",
    [
        (None, "Insufficient Data"),
        (85, "Overbought"),
        (70, "Overbought"),
        (10, "Oversold"),
        (30, "Oversold"),
        (55, "Bullish Momentum"),
        (50, "Bullish Momentum"),
        (49, "Bearish Momentum"),
    ],
)
def test_interpret_rsi(rsi, expected):

    assert interpret_rsi(rsi) == expected


@pytest.mark.parametrize(
    "macd, signal, expected",
    [
        (None, None, "Insufficient Data"),
        (1.0, 0.5, "Bullish"),
        (-1.0, -0.5, "Bearish"),
        (0.5, 1.0, "Bearish Crossover"),
        (-0.5, -1.0, "Bullish Crossover"),
        (1.0, 1.0, "Neutral"),
    ],
)
def test_interpret_macd(macd, signal, expected):

    assert interpret_macd(macd, signal) == expected


# ============================================================
# OVERALL TECHNICAL SIGNAL
# ============================================================

def test_technical_signal_bullish_needs_two_agreeing_signals():

    result = calculate_technical_signal(
        trend="Bullish",
        rsi_interpretation="Bullish Momentum",
        macd_interpretation="Neutral",
    )

    assert result == "Bullish"


def test_technical_signal_bearish_needs_two_agreeing_signals():

    result = calculate_technical_signal(
        trend="Bearish",
        rsi_interpretation="Overbought",
        macd_interpretation="Neutral",
    )

    assert result == "Bearish"


def test_technical_signal_neutral_when_signals_split():

    result = calculate_technical_signal(
        trend="Bullish",
        rsi_interpretation="Oversold",
        macd_interpretation="Bearish",
    )

    assert result == "Neutral"


# ============================================================
# SUPPORT / RESISTANCE
# ============================================================

def test_support_resistance_matches_trailing_window(sample_history):

    result = calculate_support_resistance(sample_history, lookback=60)

    window = sample_history.tail(60)

    assert result["support"] == pytest.approx(window["Low"].min())
    assert result["resistance"] == pytest.approx(window["High"].max())


def test_support_resistance_position_near_support():

    result = calculate_support_resistance_position(
        current_price=101.0,
        support=100.0,
        resistance=200.0,
    )

    assert result == "Near Support"


def test_support_resistance_position_near_resistance():

    result = calculate_support_resistance_position(
        current_price=199.0,
        support=100.0,
        resistance=200.0,
    )

    assert result == "Near Resistance"


def test_support_resistance_position_between():

    result = calculate_support_resistance_position(
        current_price=150.0,
        support=100.0,
        resistance=200.0,
    )

    assert result == "Between Support and Resistance"


def test_support_resistance_position_insufficient_data_when_inverted():

    result = calculate_support_resistance_position(
        current_price=150.0,
        support=200.0,
        resistance=100.0,
    )

    assert result == "Insufficient Data"
