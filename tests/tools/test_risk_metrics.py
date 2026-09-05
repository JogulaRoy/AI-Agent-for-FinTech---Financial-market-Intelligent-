import math

import numpy as np
import pandas as pd
import pytest

from app.tools.risk_metrics import (
    prepare_returns,
    calculate_annualized_volatility,
    calculate_downside_volatility,
    calculate_maximum_drawdown,
    calculate_var,
    calculate_cvar,
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    calculate_risk_score,
    classify_risk,
    generate_risk_explanation,
    identify_key_risks,
)


# ============================================================
# PREPARE RETURNS
# ============================================================

def test_prepare_returns_empty_for_empty_history():

    result = prepare_returns(pd.DataFrame())

    assert result.empty


def test_prepare_returns_matches_manual_pct_change(sample_history):

    expected = sample_history["Close"].pct_change().dropna()

    result = prepare_returns(sample_history)

    pd.testing.assert_series_equal(
        result,
        expected,
        check_names=False,
    )


def test_prepare_returns_raises_without_close_column():

    frame = pd.DataFrame({"Open": [1.0, 2.0, 3.0]})

    with pytest.raises(ValueError):
        prepare_returns(frame)


# ============================================================
# VOLATILITY
# ============================================================

def test_annualized_volatility_matches_manual_formula(sample_history):

    returns = prepare_returns(sample_history)

    expected = returns.std() * math.sqrt(252)

    assert calculate_annualized_volatility(returns) == pytest.approx(expected)


def test_annualized_volatility_none_for_short_series():

    assert calculate_annualized_volatility(pd.Series([0.01])) is None


def test_downside_volatility_zero_when_fewer_than_two_negative_returns():

    returns = pd.Series([0.01, 0.02, 0.03, -0.01])

    assert calculate_downside_volatility(returns) == 0.0


def test_downside_volatility_none_for_empty_series():

    assert calculate_downside_volatility(pd.Series(dtype=float)) is None


# ============================================================
# MAXIMUM DRAWDOWN
# ============================================================

def test_maximum_drawdown_known_value(drawdown_history):

    expected = (80.0 - 110.0) / 110.0

    assert calculate_maximum_drawdown(drawdown_history) == pytest.approx(
        expected
    )


def test_maximum_drawdown_none_for_empty_history():

    assert calculate_maximum_drawdown(pd.DataFrame()) is None


# ============================================================
# VALUE AT RISK / CONDITIONAL VaR
# ============================================================

def test_var_raises_for_out_of_range_confidence():

    returns = pd.Series([0.01, -0.02, 0.03])

    with pytest.raises(ValueError):
        calculate_var(returns, confidence=1.0)

    with pytest.raises(ValueError):
        calculate_var(returns, confidence=0.0)


def test_var_none_for_empty_series():

    assert calculate_var(pd.Series(dtype=float), confidence=0.95) is None


def test_cvar_is_at_least_as_extreme_as_var(sample_history):

    returns = prepare_returns(sample_history)

    var_95 = calculate_var(returns, confidence=0.95)
    cvar_95 = calculate_cvar(returns, confidence=0.95)

    # CVaR averages the tail beyond VaR, so it must be <= VaR
    # (i.e. represent an equal or larger loss).
    assert cvar_95 <= var_95 + 1e-9


def test_cvar_none_for_empty_series():

    assert calculate_cvar(pd.Series(dtype=float), confidence=0.95) is None


# ============================================================
# SHARPE / SORTINO
# ============================================================

def test_sharpe_ratio_matches_manual_formula(sample_history):

    returns = prepare_returns(sample_history)

    expected = (
        returns.mean()
        / returns.std()
        * math.sqrt(252)
    )

    assert calculate_sharpe_ratio(returns, risk_free_rate=0.0) == pytest.approx(
        expected
    )


def test_sharpe_ratio_none_for_zero_variance_returns():

    returns = pd.Series([0.01] * 10)

    assert calculate_sharpe_ratio(returns) is None


def test_sortino_ratio_none_when_fewer_than_two_downside_returns():

    returns = pd.Series([0.01, 0.02, 0.03, -0.01])

    assert calculate_sortino_ratio(returns) is None


def test_sortino_ratio_positive_for_upward_biased_returns():

    rng = np.random.default_rng(seed=7)

    returns = pd.Series(rng.normal(loc=0.002, scale=0.01, size=200))

    result = calculate_sortino_ratio(returns)

    assert result is not None
    assert result > 0


# ============================================================
# RISK SCORE
# ============================================================

def test_risk_score_is_zero_when_all_inputs_none():

    assert calculate_risk_score(None, None, None) == 0.0


def test_risk_score_matches_manual_weighted_formula():

    # 30% volatility, 20% drawdown, 5% VaR — all below their caps.
    score = calculate_risk_score(
        annualized_volatility=0.30,
        maximum_drawdown=-0.20,
        value_at_risk_95=-0.05,
    )

    expected = round(
        (30 / 60 * 40)
        + (20 / 60 * 35)
        + (5 / 15 * 25),
        2,
    )

    assert score == pytest.approx(expected)


def test_risk_score_is_capped_at_100():

    score = calculate_risk_score(
        annualized_volatility=5.0,
        maximum_drawdown=-5.0,
        value_at_risk_95=-5.0,
    )

    assert score == 100.0


# ============================================================
# RISK CLASSIFICATION
# ============================================================

@pytest.mark.parametrize(
    "score, expected",
    [
        (0, "Low Risk"),
        (24.99, "Low Risk"),
        (25, "Moderate Risk"),
        (49.99, "Moderate Risk"),
        (50, "High Risk"),
        (74.99, "High Risk"),
        (75, "Very High Risk"),
        (100, "Very High Risk"),
    ],
)
def test_classify_risk_thresholds(score, expected):

    assert classify_risk(score) == expected


# ============================================================
# RISK EXPLANATION
# ============================================================

def test_risk_explanation_insufficient_data_when_all_none():

    result = generate_risk_explanation(
        risk_level="Low Risk",
        annualized_volatility=None,
        maximum_drawdown=None,
        value_at_risk_95=None,
    )

    assert result == (
        "Insufficient historical data to explain the risk level."
    )


def test_risk_explanation_includes_available_metrics():

    result = generate_risk_explanation(
        risk_level="High Risk",
        annualized_volatility=0.42,
        maximum_drawdown=-0.30,
        value_at_risk_95=None,
    )

    assert "high risk" in result
    assert "42.00%" in result
    assert "30.00%" in result


# ============================================================
# KEY RISKS
# ============================================================

def test_identify_key_risks_fallback_when_nothing_flagged():

    result = identify_key_risks(
        annualized_volatility=0.05,
        downside_volatility=0.02,
        maximum_drawdown=-0.02,
        value_at_risk_95=-0.01,
        sharpe_ratio=1.5,
    )

    assert result == [
        "No major historical risk signal "
        "detected by the current rule set"
    ]


def test_identify_key_risks_flags_every_threshold():

    result = identify_key_risks(
        annualized_volatility=0.45,
        downside_volatility=0.35,
        maximum_drawdown=-0.35,
        value_at_risk_95=-0.05,
        sharpe_ratio=-0.2,
    )

    assert "High historical price volatility" in result
    assert "Elevated downside volatility" in result
    assert "Significant historical drawdown" in result
    assert "Elevated short-term loss potential" in result
    assert "Poor historical risk-adjusted return" in result
