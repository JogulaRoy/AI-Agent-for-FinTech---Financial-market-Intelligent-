from app.agents.stock_resolver import resolve_stock

from app.tools.market_data import fetch_market_data

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

from app.schemas.risk_data import (
    RiskAnalysis,
    RiskClassification,
    RiskMetrics,
)


# ============================================================
# RISK AGENT
# ============================================================

def risk_agent(
    user_input: str,
    period: str = "1y",
) -> RiskAnalysis:
    """
    Risk Agent

    Responsibilities:

    1. Understand the user's stock input.
    2. Resolve the company/symbol.
    3. Fetch historical market data.
    4. Calculate historical returns.
    5. Measure volatility.
    6. Measure downside risk.
    7. Calculate maximum drawdown.
    8. Calculate historical VaR and CVaR.
    9. Calculate Sharpe and Sortino ratios.
    10. Generate a rule-based risk score.
    11. Classify overall historical risk.
    12. Return structured Pydantic output.

    Args:
        user_input:
            Company name or stock symbol.

        period:
            Historical analysis period.

    Returns:
        RiskAnalysis
    """

    # ========================================================
    # 1. RESOLVE STOCK
    # ========================================================

    stock = resolve_stock(
        user_input
    )

    symbol = stock["symbol"]

    # ========================================================
    # 2. FETCH MARKET DATA
    # ========================================================

    market_data = fetch_market_data(
        symbol=symbol,
        period=period,
        interval="1d",
    )

    history = market_data["history"]

    # ========================================================
    # 3. PREPARE RETURNS
    # ========================================================

    returns = prepare_returns(
        history
    )

    # ========================================================
    # 4. CALCULATE RISK METRICS
    # ========================================================

    annualized_volatility = (
        calculate_annualized_volatility(
            returns
        )
    )

    downside_volatility = (
        calculate_downside_volatility(
            returns
        )
    )

    maximum_drawdown = (
        calculate_maximum_drawdown(
            history
        )
    )

    value_at_risk_95 = calculate_var(
        returns,
        confidence=0.95,
    )

    value_at_risk_99 = calculate_var(
        returns,
        confidence=0.99,
    )

    conditional_var_95 = calculate_cvar(
        returns,
        confidence=0.95,
    )

    conditional_var_99 = calculate_cvar(
        returns,
        confidence=0.99,
    )

    sharpe_ratio = calculate_sharpe_ratio(
        returns,
        risk_free_rate=0.0,
    )

    sortino_ratio = calculate_sortino_ratio(
        returns,
        risk_free_rate=0.0,
    )

    # ========================================================
    # 5. RISK SCORE
    # ========================================================

    risk_score = calculate_risk_score(
        annualized_volatility=(
            annualized_volatility
        ),
        maximum_drawdown=(
            maximum_drawdown
        ),
        value_at_risk_95=(
            value_at_risk_95
        ),
    )

    # ========================================================
    # 6. CLASSIFY RISK
    # ========================================================

    risk_level = classify_risk(
        risk_score
    )

    # ========================================================
    # 7. EXPLANATION
    # ========================================================

    explanation = (
        generate_risk_explanation(
            risk_level=risk_level,
            annualized_volatility=(
                annualized_volatility
            ),
            maximum_drawdown=(
                maximum_drawdown
            ),
            value_at_risk_95=(
                value_at_risk_95
            ),
        )
    )

    # ========================================================
    # 8. KEY RISKS
    # ========================================================

    key_risks = identify_key_risks(
        annualized_volatility=(
            annualized_volatility
        ),
        downside_volatility=(
            downside_volatility
        ),
        maximum_drawdown=(
            maximum_drawdown
        ),
        value_at_risk_95=(
            value_at_risk_95
        ),
        sharpe_ratio=(
            sharpe_ratio
        ),
    )

    # ========================================================
    # 9. CREATE RISK METRICS OBJECT
    # ========================================================

    risk_metrics = RiskMetrics(

        annualized_volatility=(
            annualized_volatility
        ),

        downside_volatility=(
            downside_volatility
        ),

        maximum_drawdown=(
            maximum_drawdown
        ),

        value_at_risk_95=(
            value_at_risk_95
        ),

        value_at_risk_99=(
            value_at_risk_99
        ),

        conditional_var_95=(
            conditional_var_95
        ),

        conditional_var_99=(
            conditional_var_99
        ),

        sharpe_ratio=(
            sharpe_ratio
        ),

        sortino_ratio=(
            sortino_ratio
        ),
    )

    # ========================================================
    # 10. CREATE CLASSIFICATION
    # ========================================================

    classification = RiskClassification(

        level=risk_level,

        score=risk_score,

        explanation=explanation,
    )

    # ========================================================
    # 11. RISK SUMMARY
    # ========================================================

    risk_summary = (
        f"{risk_level} with a "
        f"historical risk score of "
        f"{risk_score:.2f}/100."
    )

    # ========================================================
    # 12. RETURN STRUCTURED RESULT
    # ========================================================

    return RiskAnalysis(

        company_name=stock["name"],

        symbol=stock["symbol"],

        exchange=stock["exchange"],

        currency=market_data[
            "currency"
        ]["code"],

        analysis_period=period,

        data_points=len(
            returns
        ),

        risk_metrics=risk_metrics,

        classification=classification,

        key_risks=key_risks,

        risk_summary=risk_summary,
    )