"""
Transparent financial-health assessment.

Every input is a measurable fundamental figure. The output is a weighted score
with the contributing factors spelled out. This is deliberately NOT "ask an LLM
if the company is stable".
"""

from __future__ import annotations

from typing import Optional

from app.schemas.fundamentals import (
    FinancialHealth,
    Fundamentals,
    HealthFactor,
)

_VERDICT_SCORE = {"strong": 100.0, "moderate": 60.0, "weak": 20.0, "unknown": None}


def _band(
    value: Optional[float], strong: float, moderate: float, higher_is_better: bool = True
) -> str:
    if value is None:
        return "unknown"
    if higher_is_better:
        if value >= strong:
            return "strong"
        if value >= moderate:
            return "moderate"
        return "weak"
    else:
        if value <= strong:
            return "strong"
        if value <= moderate:
            return "moderate"
        return "weak"


def _consistency(values: list[Optional[float]]) -> tuple[str, str]:
    known = [v for v in values if v is not None]
    if len(known) < 2:
        return "unknown", "not enough reported periods"
    positive = sum(1 for v in known if v > 0)
    ratio = positive / len(known)
    if ratio == 1:
        return "strong", f"positive in all {len(known)} reported periods"
    if ratio >= 0.6:
        return "moderate", f"positive in {positive}/{len(known)} periods"
    return "weak", f"positive in only {positive}/{len(known)} periods"


def assess_financial_health(
    fundamentals: Fundamentals,
    annualized_volatility: Optional[float] = None,
    maximum_drawdown: Optional[float] = None,
) -> FinancialHealth:
    v = fundamentals.valuation
    income = fundamentals.income_statement
    cash = fundamentals.cash_flow

    factors: list[HealthFactor] = []

    # Profitability
    net_margin = v.profit_margin
    if net_margin is None and income:
        net_margin = income[0].net_margin
    verdict = _band(net_margin, 0.15, 0.05)
    factors.append(HealthFactor(
        name="Profitability (net margin)", value=net_margin, verdict=verdict, weight=1.2,
        detail=f"{net_margin:.1%} net profit margin" if net_margin is not None else "unavailable",
    ))

    # Return on equity
    verdict = _band(v.roe, 0.15, 0.08)
    factors.append(HealthFactor(
        name="Return on equity", value=v.roe, verdict=verdict, weight=1.0,
        detail=f"ROE {v.roe:.1%}" if v.roe is not None else "unavailable",
    ))

    # Revenue growth
    verdict = _band(v.revenue_growth, 0.08, 0.0)
    factors.append(HealthFactor(
        name="Revenue growth", value=v.revenue_growth, verdict=verdict, weight=1.0,
        detail=f"{v.revenue_growth:+.1%} YoY" if v.revenue_growth is not None else "unavailable",
    ))

    # Earnings consistency
    verdict, detail = _consistency([line.net_income for line in income])
    factors.append(HealthFactor(
        name="Earnings consistency", verdict=verdict, weight=1.1, detail=detail,
    ))

    # Free cash flow
    fcf = v.free_cash_flow if v.free_cash_flow is not None else (cash[0].free_cash_flow if cash else None)
    fcf_verdict = "unknown" if fcf is None else ("strong" if fcf > 0 else "weak")
    factors.append(HealthFactor(
        name="Free cash flow", value=fcf, verdict=fcf_verdict, weight=1.1,
        detail=("positive free cash flow" if (fcf or 0) > 0 else "negative free cash flow")
        if fcf is not None else "unavailable",
    ))

    # Leverage
    verdict = _band(v.debt_to_equity, 0.5, 1.5, higher_is_better=False)
    factors.append(HealthFactor(
        name="Leverage (debt/equity)", value=v.debt_to_equity, verdict=verdict, weight=1.1,
        detail=f"D/E {v.debt_to_equity:.2f}" if v.debt_to_equity is not None else "unavailable",
    ))

    # Liquidity
    verdict = _band(v.current_ratio, 1.5, 1.0)
    factors.append(HealthFactor(
        name="Liquidity (current ratio)", value=v.current_ratio, verdict=verdict, weight=0.9,
        detail=f"current ratio {v.current_ratio:.2f}" if v.current_ratio is not None else "unavailable",
    ))

    # Price stability (optional cross-input)
    if annualized_volatility is not None:
        verdict = _band(annualized_volatility, 0.25, 0.40, higher_is_better=False)
        factors.append(HealthFactor(
            name="Price stability (annualized volatility)", value=annualized_volatility,
            verdict=verdict, weight=0.6,
            detail=f"{annualized_volatility:.1%} annualized volatility",
        ))
    if maximum_drawdown is not None:
        verdict = _band(abs(maximum_drawdown), 0.20, 0.40, higher_is_better=False)
        factors.append(HealthFactor(
            name="Historical drawdown", value=maximum_drawdown, verdict=verdict, weight=0.5,
            detail=f"max drawdown {maximum_drawdown:.1%}",
        ))

    # --- aggregate ---
    weighted_sum = 0.0
    weight_total = 0.0
    reasons: list[str] = []
    for factor in factors:
        base = _VERDICT_SCORE.get(factor.verdict)
        if base is None:
            continue
        weighted_sum += base * factor.weight
        weight_total += factor.weight
        if factor.verdict == "strong":
            reasons.append(f"Strong: {factor.name.lower()} ({factor.detail})")
        elif factor.verdict == "weak":
            reasons.append(f"Weak: {factor.name.lower()} ({factor.detail})")

    known_factors = sum(1 for f in factors if f.verdict != "unknown")
    if weight_total == 0 or known_factors < 3:
        return FinancialHealth(
            classification="Unknown", score=None, factors=factors,
            reasons=["Not enough fundamental data on the free API tier to score financial health."],
        )

    score = round(weighted_sum / weight_total, 1)
    classification = "Strong" if score >= 70 else "Moderate" if score >= 45 else "Weak"
    if not reasons:
        reasons.append("Mixed fundamentals with no dominant strength or weakness.")

    return FinancialHealth(
        classification=classification,
        score=score,
        factors=factors,
        reasons=reasons[:8],
    )
