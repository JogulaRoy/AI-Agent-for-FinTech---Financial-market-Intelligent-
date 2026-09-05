import math

import numpy as np
import pandas as pd
import pytest

from app.tools.market_metrics import (
    calculate_daily_return,
    calculate_period_return,
    calculate_monthly_return,
    calculate_annualized_volatility,
    calculate_downside_volatility,
    calculate_maximum_drawdown,
    calculate_positive_days_ratio,
    calculate_negative_days_ratio,
    calculate_average_daily_return,
    calculate_best_day,
    calculate_worst_day,
    classify_stability,
)


# ============================================================
# DAILY RETURN
# ============================================================

def test_daily_return_matches_manual_pct_change(sample_history):

    expected = (
        sample_history["Close"].iloc[-1]
        / sample_history["Close"].iloc[-2]
        - 1
    )

    assert calculate_daily_return(sample_history) == pytest.approx(expected)


def test_daily_return_none_for_single_row(single_row_history):

    assert calculate_daily_return(single_row_history) is None


def test_daily_return_none_for_empty_history():

    empty = pd.DataFrame(columns=["Close"])

    assert calculate_daily_return(empty) is None


# ============================================================
# PERIOD RETURN
# ============================================================

def test_period_return_uses_closest_prior_trading_day(rising_history):

    # 10 calendar days back from the last row.
    result = calculate_period_return(rising_history, days=10)

    current_price = rising_history["Close"].iloc[-1]
    target_date = rising_history.index[-1] - pd.Timedelta(days=10)
    previous_price = rising_history[
        rising_history.index <= target_date
    ]["Close"].iloc[-1]

    expected = (current_price - previous_price) / previous_price

    assert result == pytest.approx(expected)


def test_period_return_none_when_no_data_before_target(rising_history):

    # The lookback window predates every row in the series.
    result = calculate_period_return(rising_history, days=10_000)

    assert result is None


def test_monthly_return_is_period_return_with_30_days(sample_history):

    assert calculate_monthly_return(sample_history) == pytest.approx(
        calculate_period_return(sample_history, days=30)
    )


# ============================================================
# VOLATILITY
# ============================================================

def test_annualized_volatility_matches_manual_formula(sample_history):

    returns = sample_history["Close"].pct_change().dropna()

    expected = returns.std() * math.sqrt(252)

    assert calculate_annualized_volatility(sample_history) == pytest.approx(
        expected
    )


def test_downside_volatility_zero_for_strictly_rising_series(rising_history):

    assert calculate_downside_volatility(rising_history) == 0.0


def test_downside_volatility_positive_when_losses_exist(falling_history):

    result = calculate_downside_volatility(falling_history)

    assert result is not None
    assert result >= 0.0


# ============================================================
# MAXIMUM DRAWDOWN
# ============================================================

def test_maximum_drawdown_known_value(drawdown_history):

    # Peak = 110, trough = 80 -> (80 - 110) / 110
    expected = (80.0 - 110.0) / 110.0

    assert calculate_maximum_drawdown(drawdown_history) == pytest.approx(
        expected
    )


def test_maximum_drawdown_zero_for_strictly_rising_series(rising_history):

    assert calculate_maximum_drawdown(rising_history) == pytest.approx(0.0)


# ============================================================
# CONSISTENCY RATIOS
# ============================================================

def test_positive_and_negative_ratio_cover_all_return_days(sample_history):

    returns = sample_history["Close"].pct_change().dropna()

    positive_ratio = calculate_positive_days_ratio(sample_history)
    negative_ratio = calculate_negative_days_ratio(sample_history)

    expected_positive = (returns > 0).mean()
    expected_negative = (returns < 0).mean()

    assert positive_ratio == pytest.approx(expected_positive)
    assert negative_ratio == pytest.approx(expected_negative)


def test_positive_ratio_is_one_for_strictly_rising_series(rising_history):

    assert calculate_positive_days_ratio(rising_history) == pytest.approx(1.0)
    assert calculate_negative_days_ratio(rising_history) == pytest.approx(0.0)


# ============================================================
# DAILY EXTREMES / AVERAGE
# ============================================================

def test_best_day_is_the_maximum_return(sample_history):

    returns = sample_history["Close"].pct_change().dropna()

    assert calculate_best_day(sample_history) == pytest.approx(returns.max())


def test_worst_day_is_the_minimum_return(sample_history):

    returns = sample_history["Close"].pct_change().dropna()

    assert calculate_worst_day(sample_history) == pytest.approx(returns.min())


def test_best_day_never_smaller_than_worst_day(sample_history):

    assert calculate_best_day(sample_history) >= calculate_worst_day(
        sample_history
    )


def test_average_daily_return_matches_manual_mean(sample_history):

    returns = sample_history["Close"].pct_change().dropna()

    assert calculate_average_daily_return(sample_history) == pytest.approx(
        returns.mean()
    )


# ============================================================
# STABILITY CLASSIFICATION
# ============================================================

@pytest.mark.parametrize(
    "volatility, drawdown, expected",
    [
        (0.10, -0.05, "Higher Stability"),
        (0.19, -0.19, "Higher Stability"),
        (0.25, -0.25, "Moderate Stability"),
        (0.40, -0.10, "Lower Stability"),
        (0.10, -0.45, "Lower Stability"),
    ],
)
def test_classify_stability_thresholds(volatility, drawdown, expected):

    assert classify_stability(volatility, drawdown) == expected


def test_classify_stability_insufficient_data_when_missing_inputs():

    assert classify_stability(None, -0.10) == "Insufficient Data"
    assert classify_stability(0.10, None) == "Insufficient Data"
