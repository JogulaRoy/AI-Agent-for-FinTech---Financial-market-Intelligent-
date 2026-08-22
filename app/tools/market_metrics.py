import pandas as pd
import numpy as np


# ============================================================
# PERFORMANCE METRICS
# ============================================================


def calculate_daily_return(
    history: pd.DataFrame,
) -> float | None:
    """
    Calculate the latest daily return.

    Formula:
        (Today's Close - Previous Close) / Previous Close
    """

    if history.empty or len(history) < 2:
        return None

    history = history.sort_index()

    returns = (
        history["Close"]
        .pct_change()
        .dropna()
    )

    if returns.empty:
        return None

    return float(returns.iloc[-1])


def calculate_period_return(
    history: pd.DataFrame,
    days: int,
) -> float | None:
    """
    Calculate return over a specified number
    of calendar days.

    The closest available trading day at or
    before the target date is used.
    """

    if history.empty or len(history) < 2:
        return None

    history = history.sort_index()

    current_price = float(
        history["Close"].iloc[-1]
    )

    current_date = history.index[-1]

    target_date = (
        current_date
        - pd.Timedelta(days=days)
    )

    previous_data = history[
        history.index <= target_date
    ]

    if previous_data.empty:
        return None

    previous_price = float(
        previous_data["Close"].iloc[-1]
    )

    if previous_price <= 0:
        return None

    return float(
        (current_price - previous_price)
        / previous_price
    )


def calculate_monthly_return(
    history: pd.DataFrame,
) -> float | None:

    return calculate_period_return(
        history,
        days=30,
    )


def calculate_six_month_return(
    history: pd.DataFrame,
) -> float | None:

    return calculate_period_return(
        history,
        days=182,
    )


def calculate_one_year_return(
    history: pd.DataFrame,
) -> float | None:

    return calculate_period_return(
        history,
        days=365,
    )


# ============================================================
# VOLATILITY
# ============================================================


def calculate_annualized_volatility(
    history: pd.DataFrame,
) -> float | None:
    """
    Calculate annualized historical volatility.

    Daily volatility × sqrt(252)
    """

    if history.empty or len(history) < 2:
        return None

    returns = (
        history["Close"]
        .pct_change()
        .dropna()
    )

    if returns.empty:
        return None

    daily_volatility = returns.std()

    return float(
        daily_volatility * np.sqrt(252)
    )


def calculate_downside_volatility(
    history: pd.DataFrame,
) -> float | None:
    """
    Calculate annualized volatility considering
    only negative daily returns.
    """

    if history.empty or len(history) < 2:
        return None

    returns = (
        history["Close"]
        .pct_change()
        .dropna()
    )

    negative_returns = returns[
        returns < 0
    ]

    if negative_returns.empty:
        return 0.0

    downside_volatility = (
        negative_returns.std()
        * np.sqrt(252)
    )

    return float(downside_volatility)


# ============================================================
# DRAWDOWN
# ============================================================


def calculate_maximum_drawdown(
    history: pd.DataFrame,
) -> float | None:
    """
    Calculate the maximum historical drawdown.

    Drawdown:
        (Current Price - Previous Peak)
        / Previous Peak
    """

    if history.empty:
        return None

    prices = history["Close"]

    running_peak = prices.cummax()

    drawdowns = (
        prices - running_peak
    ) / running_peak

    maximum_drawdown = drawdowns.min()

    if pd.isna(maximum_drawdown):
        return None

    return float(maximum_drawdown)


# ============================================================
# CONSISTENCY
# ============================================================


def calculate_positive_days_ratio(
    history: pd.DataFrame,
) -> float | None:
    """
    Percentage of trading days with positive returns.
    """

    if history.empty or len(history) < 2:
        return None

    returns = (
        history["Close"]
        .pct_change()
        .dropna()
    )

    if returns.empty:
        return None

    return float(
        (returns > 0).mean()
    )


def calculate_negative_days_ratio(
    history: pd.DataFrame,
) -> float | None:
    """
    Percentage of trading days with negative returns.
    """

    if history.empty or len(history) < 2:
        return None

    returns = (
        history["Close"]
        .pct_change()
        .dropna()
    )

    if returns.empty:
        return None

    return float(
        (returns < 0).mean()
    )


# ============================================================
# DAILY EXTREMES
# ============================================================


def calculate_best_day(
    history: pd.DataFrame,
) -> float | None:
    """
    Find the best single trading day return.
    """

    if history.empty or len(history) < 2:
        return None

    returns = (
        history["Close"]
        .pct_change()
        .dropna()
    )

    if returns.empty:
        return None

    return float(returns.max())


def calculate_worst_day(
    history: pd.DataFrame,
) -> float | None:
    """
    Find the worst single trading day return.
    """

    if history.empty or len(history) < 2:
        return None

    returns = (
        history["Close"]
        .pct_change()
        .dropna()
    )

    if returns.empty:
        return None

    return float(returns.min())


# ============================================================
# AVERAGE RETURN
# ============================================================


def calculate_average_daily_return(
    history: pd.DataFrame,
) -> float | None:
    """
    Calculate average daily return.
    """

    if history.empty or len(history) < 2:
        return None

    returns = (
        history["Close"]
        .pct_change()
        .dropna()
    )

    if returns.empty:
        return None

    return float(returns.mean())


# ============================================================
# STABILITY CLASSIFICATION
# ============================================================


def classify_stability(
    annualized_volatility: float | None,
    maximum_drawdown: float | None,
) -> str:
    """
    Classify historical price stability.

    This is an explainable project heuristic,
    not financial advice.

    Higher Stability:
        volatility < 20%
        AND
        drawdown < 20%

    Lower Stability:
        volatility >= 35%
        OR
        drawdown >= 40%

    Otherwise:
        Moderate Stability
    """

    if (
        annualized_volatility is None
        or maximum_drawdown is None
    ):
        return "Insufficient Data"

    volatility = annualized_volatility

    drawdown = abs(maximum_drawdown)

    if (
        volatility < 0.20
        and drawdown < 0.20
    ):
        return "Higher Stability"

    if (
        volatility >= 0.35
        or drawdown >= 0.40
    ):
        return "Lower Stability"

    return "Moderate Stability"