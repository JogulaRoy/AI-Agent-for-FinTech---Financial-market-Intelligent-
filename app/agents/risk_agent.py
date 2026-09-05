"""
Risk Agent.

Consumes normalized historical price/return data and produces structured risk
measurements. The 0-100 score is explicitly a project-specific signal, not a
regulated rating. The risk-free-rate assumption is surfaced, never hidden.
"""

from __future__ import annotations

from typing import Optional

from app.analysis.benchmarks import get_benchmark
from app.config.settings import settings
from app.data.normalizer import price_history_to_frame
from app.schemas.market_data import PriceHistory
from app.schemas.risk_data import RiskAnalysis, RiskClassification, RiskMetrics
from app.schemas.security import CanonicalSecurity
from app.tools.risk_metrics import (
    calculate_annualized_volatility,
    calculate_beta,
    calculate_cvar,
    calculate_downside_volatility,
    calculate_maximum_drawdown,
    calculate_risk_score,
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    calculate_var,
    classify_risk,
    generate_risk_explanation,
    identify_key_risks,
    prepare_returns,
)


def run_risk_agent(
    security: CanonicalSecurity,
    history: PriceHistory,
    period: str = "",
    benchmark_history: Optional[PriceHistory] = None,
    benchmark_name: Optional[str] = None,
) -> RiskAnalysis:
    frame = price_history_to_frame(history)
    returns = prepare_returns(frame)

    rf = settings.risk_free_rate

    analysis = RiskAnalysis(
        company_name=security.company_name,
        symbol=security.symbol,
        exchange=security.exchange,
        currency=history.currency or security.currency,
        analysis_period=period,
        data_points=len(returns),
        risk_free_rate=rf,
        risk_free_rate_source=(
            f"assumption: {rf:.2%} annual (configurable via RISK_FREE_RATE)"
        ),
    )

    if len(returns) < 20:
        analysis.classification = RiskClassification(
            level="Insufficient Data",
            explanation="Not enough return history to measure risk.",
        )
        analysis.risk_summary = "Insufficient historical data for a risk assessment."
        return analysis

    ann_vol = calculate_annualized_volatility(returns)
    max_dd = calculate_maximum_drawdown(frame)
    var_95 = calculate_var(returns, 0.95)
    var_99 = calculate_var(returns, 0.99)

    # Beta vs a market benchmark (best effort).
    beta = None
    if benchmark_history is None:
        benchmark_name, benchmark_history = get_benchmark(security, period or "5y")
    if benchmark_history is not None:
        bench_returns = prepare_returns(price_history_to_frame(benchmark_history))
        beta = calculate_beta(returns, bench_returns)

    metrics = RiskMetrics(
        annualized_volatility=ann_vol,
        downside_volatility=calculate_downside_volatility(returns),
        maximum_drawdown=max_dd,
        value_at_risk_95=var_95,
        value_at_risk_99=var_99,
        conditional_var_95=calculate_cvar(returns, 0.95),
        conditional_var_99=calculate_cvar(returns, 0.99),
        sharpe_ratio=calculate_sharpe_ratio(returns, risk_free_rate=rf),
        sortino_ratio=calculate_sortino_ratio(returns, risk_free_rate=rf),
        beta=beta,
        benchmark=benchmark_name if beta is not None else None,
    )

    score = calculate_risk_score(ann_vol, max_dd, var_95)
    level = classify_risk(score)

    analysis.risk_metrics = metrics
    analysis.classification = RiskClassification(
        level=level,
        score=score,
        explanation=generate_risk_explanation(level, ann_vol, max_dd, var_95),
    )
    analysis.key_risks = identify_key_risks(
        ann_vol, metrics.downside_volatility, max_dd, var_95, metrics.sharpe_ratio
    )
    if beta is not None:
        if beta > 1.2:
            analysis.key_risks.append(
                f"Higher-than-market systematic risk (beta {beta:.2f} vs {benchmark_name})."
            )
        elif beta < 0.8:
            analysis.key_risks.append(
                f"Lower-than-market systematic risk (beta {beta:.2f} vs {benchmark_name})."
            )
    analysis.risk_summary = (
        f"{level} — project risk score {score:.0f}/100, "
        f"annualized volatility {ann_vol:.1%}"
        + (f", beta {beta:.2f} vs {benchmark_name}" if beta is not None else "")
        + "."
    )
    return analysis
