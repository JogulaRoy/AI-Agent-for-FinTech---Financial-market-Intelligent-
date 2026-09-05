"""Tests for the indicators added in the multi-agent rework."""

import numpy as np
import pandas as pd
import pytest

from app.tools.risk_metrics import calculate_beta
from app.tools.technical_indicators import calculate_atr, calculate_rsi


def test_wilder_rsi_matches_reference_series():
    # Classic Wilder worked example (first 14 diffs then a few more).
    closes = [
        44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08,
        45.89, 46.03, 45.61, 46.28, 46.28, 46.00, 46.03, 46.41, 46.22, 45.64,
    ]
    frame = pd.DataFrame({"Close": closes})
    frame["Open"] = frame["Close"]
    frame["High"] = frame["Close"] * 1.001
    frame["Low"] = frame["Close"] * 0.999
    rsi = calculate_rsi(frame, period=14)
    # Reference RSI for this series after 20 points is ~ 56.5 (Wilder).
    assert rsi == pytest.approx(56.5, abs=2.5)


def test_rsi_bounds_on_random_walk(sample_history):
    rsi = calculate_rsi(sample_history, period=14)
    assert 0 <= rsi <= 100


def test_atr_is_positive_and_scales_with_range(sample_history):
    atr = calculate_atr(sample_history, period=14)
    assert atr is not None and atr > 0
    wide = sample_history.copy()
    wide["High"] = wide["High"] * 1.05
    wide["Low"] = wide["Low"] * 0.95
    assert calculate_atr(wide, period=14) > atr


def test_beta_of_series_against_itself_is_one():
    rng = np.random.default_rng(0)
    returns = pd.Series(rng.normal(0, 0.01, 300),
                        index=pd.bdate_range("2024-01-01", periods=300))
    assert calculate_beta(returns, returns) == pytest.approx(1.0)


def test_beta_of_double_series_is_two():
    rng = np.random.default_rng(1)
    idx = pd.bdate_range("2024-01-01", periods=300)
    bench = pd.Series(rng.normal(0, 0.01, 300), index=idx)
    asset = bench * 2
    assert calculate_beta(asset, bench) == pytest.approx(2.0)


def test_beta_none_without_enough_overlap():
    a = pd.Series([0.01, 0.02], index=pd.bdate_range("2024-01-01", periods=2))
    b = pd.Series([0.01, 0.02], index=pd.bdate_range("2024-06-01", periods=2))
    assert calculate_beta(a, b) is None
