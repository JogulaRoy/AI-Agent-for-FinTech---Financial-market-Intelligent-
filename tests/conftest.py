import numpy as np
import pandas as pd
import pytest


# ============================================================
# SHARED FIXTURES
#
# These build deterministic, synthetic OHLCV data so tests
# never depend on network access or real market data.
# ============================================================


@pytest.fixture
def sample_history() -> pd.DataFrame:
    """
    300 trading days of synthetic daily OHLCV data.

    Long enough to exercise every rolling window in the
    project (SMA200, MACD(26, 9), Bollinger(20), RSI(14), ...).

    Built from a fixed random seed so results are reproducible
    across runs and machines.
    """

    rng = np.random.default_rng(seed=42)

    periods = 300

    dates = pd.bdate_range(
        start="2025-01-02",
        periods=periods,
    )

    daily_returns = rng.normal(
        loc=0.0004,
        scale=0.015,
        size=periods,
    )

    close = 100 * np.cumprod(1 + daily_returns)

    high = close * (1 + rng.uniform(0.001, 0.02, size=periods))
    low = close * (1 - rng.uniform(0.001, 0.02, size=periods))
    open_ = np.concatenate([[100.0], close[:-1]])
    volume = rng.integers(1_000_000, 5_000_000, size=periods)

    return pd.DataFrame(
        {
            "Open": open_,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": volume,
        },
        index=dates,
    )


@pytest.fixture
def tiny_history(sample_history: pd.DataFrame) -> pd.DataFrame:
    """5 rows: enough to pass validation, too few for most indicators."""

    return sample_history.iloc[:5].copy()


@pytest.fixture
def single_row_history(sample_history: pd.DataFrame) -> pd.DataFrame:
    """1 row: fails the len(history) >= 2 validation everywhere."""

    return sample_history.iloc[:1].copy()


@pytest.fixture
def rising_history() -> pd.DataFrame:
    """20 strictly increasing closes: zero losses, zero drawdown."""

    dates = pd.bdate_range(start="2025-01-02", periods=20)

    close = np.linspace(100, 119, 20)

    return pd.DataFrame(
        {
            "Open": close,
            "High": close * 1.01,
            "Low": close * 0.99,
            "Close": close,
            "Volume": np.full(20, 1_000_000),
        },
        index=dates,
    )


@pytest.fixture
def falling_history() -> pd.DataFrame:
    """20 strictly decreasing closes: zero gains."""

    dates = pd.bdate_range(start="2025-01-02", periods=20)

    close = np.linspace(119, 100, 20)

    return pd.DataFrame(
        {
            "Open": close,
            "High": close * 1.01,
            "Low": close * 0.99,
            "Close": close,
            "Volume": np.full(20, 1_000_000),
        },
        index=dates,
    )


@pytest.fixture
def drawdown_history() -> pd.DataFrame:
    """
    4 closes with a known peak and trough: [100, 110, 80, 90].

    Peak = 110, trough = 80.
    Expected maximum drawdown = (80 - 110) / 110 = -0.272727...
    """

    dates = pd.bdate_range(start="2025-01-02", periods=4)

    close = [100.0, 110.0, 80.0, 90.0]

    return pd.DataFrame(
        {
            "Open": close,
            "High": [value * 1.01 for value in close],
            "Low": [value * 0.99 for value in close],
            "Close": close,
            "Volume": [1_000_000] * 4,
        },
        index=dates,
    )
