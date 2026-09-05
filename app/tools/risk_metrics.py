import numpy as np
import pandas as pd


# ============================================================
# PREPARE RETURNS
# ============================================================

def prepare_returns(
    history: pd.DataFrame,
) -> pd.Series:
    """
    Calculate daily percentage returns from
    historical closing prices.
    """

    if history is None or history.empty:

        return pd.Series(
            dtype=float
        )

    if "Close" not in history.columns:

        raise ValueError(
            "Historical data must contain "
            "a Close column."
        )

    close_prices = pd.to_numeric(
        history["Close"],
        errors="coerce",
    )

    returns = (
        close_prices
        .pct_change()
        .dropna()
    )

    returns = returns.replace(
        [np.inf, -np.inf],
        np.nan,
    ).dropna()

    return returns


# ============================================================
# ANNUALIZED VOLATILITY
# ============================================================

def calculate_annualized_volatility(
    returns: pd.Series,
) -> float | None:
    """
    Annualized standard deviation of daily returns.
    """

    if len(returns) < 2:

        return None

    volatility = (
        returns.std()
        * np.sqrt(252)
    )

    return float(volatility)


# ============================================================
# DOWNSIDE VOLATILITY
# ============================================================

def calculate_downside_volatility(
    returns: pd.Series,
) -> float | None:
    """
    Annualized volatility considering only
    negative daily returns.
    """

    if returns.empty:

        return None

    negative_returns = returns[
        returns < 0
    ]

    if len(negative_returns) < 2:

        return 0.0

    downside_volatility = (
        negative_returns.std()
        * np.sqrt(252)
    )

    return float(
        downside_volatility
    )


# ============================================================
# MAXIMUM DRAWDOWN
# ============================================================

def calculate_maximum_drawdown(
    history: pd.DataFrame,
) -> float | None:
    """
    Calculate the maximum percentage decline
    from a historical peak.
    """

    if history is None or history.empty:

        return None

    if "Close" not in history.columns:

        raise ValueError(
            "Historical data must contain "
            "a Close column."
        )

    close_prices = pd.to_numeric(
        history["Close"],
        errors="coerce",
    ).dropna()

    if close_prices.empty:

        return None

    running_max = (
        close_prices
        .cummax()
    )

    drawdowns = (
        close_prices
        / running_max
        - 1
    )

    return float(
        drawdowns.min()
    )


# ============================================================
# VALUE AT RISK
# ============================================================

def calculate_var(
    returns: pd.Series,
    confidence: float,
) -> float | None:
    """
    Historical Value at Risk.

    Returns a negative value representing
    the estimated loss threshold.
    """

    if returns.empty:

        return None

    if not 0 < confidence < 1:

        raise ValueError(
            "Confidence must be between 0 and 1."
        )

    var = np.percentile(
        returns,
        (1 - confidence) * 100,
    )

    return float(var)


# ============================================================
# CONDITIONAL VALUE AT RISK
# ============================================================

def calculate_cvar(
    returns: pd.Series,
    confidence: float,
) -> float | None:
    """
    Historical Conditional Value at Risk.

    Calculates the average return of observations
    worse than the VaR threshold.
    """

    if returns.empty:

        return None

    var = calculate_var(
        returns,
        confidence,
    )

    if var is None:

        return None

    tail_losses = returns[
        returns <= var
    ]

    if tail_losses.empty:

        return float(var)

    return float(
        tail_losses.mean()
    )


# ============================================================
# SHARPE RATIO
# ============================================================

def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
) -> float | None:
    """
    Annualized Sharpe ratio.

    Assumption:
        Default annual risk-free rate = 0%.

    This can later be replaced with a dynamic
    risk-free rate source.
    """

    if len(returns) < 2:

        return None

    daily_risk_free_rate = (
        (1 + risk_free_rate) ** (1 / 252)
        - 1
    )

    excess_returns = (
        returns
        - daily_risk_free_rate
    )

    standard_deviation = (
        excess_returns.std()
    )

    if standard_deviation is None or not np.isfinite(standard_deviation) or standard_deviation < 1e-12:

        return None

    sharpe = (
        excess_returns.mean()
        / standard_deviation
        * np.sqrt(252)
    )

    return float(sharpe)


# ============================================================
# SORTINO RATIO
# ============================================================

def calculate_sortino_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0,
) -> float | None:
    """
    Annualized Sortino ratio.

    Uses only downside volatility
    as the risk measure.
    """

    if returns.empty:

        return None

    daily_risk_free_rate = (
        (1 + risk_free_rate) ** (1 / 252)
        - 1
    )

    excess_returns = (
        returns
        - daily_risk_free_rate
    )

    downside_returns = excess_returns[
        excess_returns < 0
    ]

    if len(downside_returns) < 2:

        return None

    downside_deviation = (
        downside_returns.std()
    )

    if downside_deviation == 0:

        return None

    sortino = (
        excess_returns.mean()
        / downside_deviation
        * np.sqrt(252)
    )

    return float(sortino)


# ============================================================
# BETA
# ============================================================

def calculate_beta(
    asset_returns: pd.Series,
    benchmark_returns: pd.Series,
) -> float | None:
    """
    Beta = Cov(asset, benchmark) / Var(benchmark), computed on the overlapping
    daily-return dates. Returns None when there is not enough shared history.
    """

    if asset_returns is None or benchmark_returns is None:
        return None

    joined = pd.concat(
        [asset_returns.rename("asset"), benchmark_returns.rename("benchmark")],
        axis=1,
        join="inner",
    ).dropna()

    if len(joined) < 30:
        return None

    benchmark_variance = joined["benchmark"].var()

    if benchmark_variance in (0, None) or pd.isna(benchmark_variance):
        return None

    covariance = joined["asset"].cov(joined["benchmark"])

    return float(covariance / benchmark_variance)


# ============================================================
# RISK SCORE
# ============================================================

def calculate_risk_score(
    annualized_volatility: float | None,
    maximum_drawdown: float | None,
    value_at_risk_95: float | None,
) -> float:
    """
    Create a simple normalized risk score from 0-100.

    Higher score = higher historical risk.

    This is a project-specific rule-based score,
    not a regulated financial risk rating.
    """

    score = 0.0

    # --------------------------------------------------------
    # VOLATILITY COMPONENT
    # --------------------------------------------------------

    if annualized_volatility is not None:

        volatility_percent = (
            annualized_volatility * 100
        )

        volatility_score = min(
            volatility_percent,
            60.0,
        )

        score += (
            volatility_score
            / 60.0
            * 40.0
        )

    # --------------------------------------------------------
    # DRAWDOWN COMPONENT
    # --------------------------------------------------------

    if maximum_drawdown is not None:

        drawdown_percent = abs(
            maximum_drawdown * 100
        )

        drawdown_score = min(
            drawdown_percent,
            60.0,
        )

        score += (
            drawdown_score
            / 60.0
            * 35.0
        )

    # --------------------------------------------------------
    # VAR COMPONENT
    # --------------------------------------------------------

    if value_at_risk_95 is not None:

        var_percent = abs(
            value_at_risk_95 * 100
        )

        var_score = min(
            var_percent,
            15.0,
        )

        score += (
            var_score
            / 15.0
            * 25.0
        )

    return round(
        min(score, 100.0),
        2,
    )


# ============================================================
# RISK LEVEL
# ============================================================

def classify_risk(
    risk_score: float,
) -> str:
    """
    Convert numerical risk score
    into a human-readable category.
    """

    if risk_score < 25:

        return "Low Risk"

    if risk_score < 50:

        return "Moderate Risk"

    if risk_score < 75:

        return "High Risk"

    return "Very High Risk"


# ============================================================
# RISK EXPLANATION
# ============================================================

def generate_risk_explanation(
    risk_level: str,
    annualized_volatility: float | None,
    maximum_drawdown: float | None,
    value_at_risk_95: float | None,
) -> str:
    """
    Generate a simple explanation
    for the risk classification.
    """

    parts = []

    if annualized_volatility is not None:

        parts.append(
            f"annualized volatility is "
            f"{annualized_volatility * 100:.2f}%"
        )

    if maximum_drawdown is not None:

        parts.append(
            f"maximum historical drawdown is "
            f"{abs(maximum_drawdown) * 100:.2f}%"
        )

    if value_at_risk_95 is not None:

        parts.append(
            f"95% historical VaR is "
            f"{abs(value_at_risk_95) * 100:.2f}%"
        )

    if not parts:

        return (
            "Insufficient historical data "
            "to explain the risk level."
        )

    metrics_text = ", ".join(
        parts
    )

    return (
        f"The stock is classified as "
        f"{risk_level.lower()} based on "
        f"{metrics_text}."
    )


# ============================================================
# KEY RISKS
# ============================================================

def identify_key_risks(
    annualized_volatility: float | None,
    downside_volatility: float | None,
    maximum_drawdown: float | None,
    value_at_risk_95: float | None,
    sharpe_ratio: float | None,
) -> list[str]:
    """
    Identify the main historical risk factors.
    """

    risks = []

    # --------------------------------------------------------
    # VOLATILITY
    # --------------------------------------------------------

    if (
        annualized_volatility is not None
        and annualized_volatility >= 0.40
    ):

        risks.append(
            "High historical price volatility"
        )

    elif (
        annualized_volatility is not None
        and annualized_volatility >= 0.25
    ):

        risks.append(
            "Moderately high price volatility"
        )

    # --------------------------------------------------------
    # DOWNSIDE
    # --------------------------------------------------------

    if (
        downside_volatility is not None
        and downside_volatility >= 0.30
    ):

        risks.append(
            "Elevated downside volatility"
        )

    # --------------------------------------------------------
    # DRAWDOWN
    # --------------------------------------------------------

    if (
        maximum_drawdown is not None
        and maximum_drawdown <= -0.30
    ):

        risks.append(
            "Significant historical drawdown"
        )

    elif (
        maximum_drawdown is not None
        and maximum_drawdown <= -0.15
    ):

        risks.append(
            "Moderate historical drawdown"
        )

    # --------------------------------------------------------
    # VAR
    # --------------------------------------------------------

    if (
        value_at_risk_95 is not None
        and value_at_risk_95 <= -0.04
    ):

        risks.append(
            "Elevated short-term loss potential"
        )

    # --------------------------------------------------------
    # SHARPE
    # --------------------------------------------------------

    if (
        sharpe_ratio is not None
        and sharpe_ratio < 0
    ):

        risks.append(
            "Poor historical risk-adjusted return"
        )

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    if not risks:

        risks.append(
            "No major historical risk signal "
            "detected by the current rule set"
        )

    return risks