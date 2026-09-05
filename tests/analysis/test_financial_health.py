from app.analysis.fundamentals import assess_financial_health
from app.schemas.fundamentals import (
    Fundamentals,
    IncomeStatementLine,
    ValuationMetrics,
)


def _strong_company() -> Fundamentals:
    income = [
        IncomeStatementLine(period=f"FY202{y}", net_income=100 + y, revenue=1000 + 50 * y,
                            net_margin=0.20)
        for y in range(4, 0, -1)
    ]
    return Fundamentals(
        income_statement=income,
        valuation=ValuationMetrics(
            profit_margin=0.22, roe=0.28, revenue_growth=0.12, debt_to_equity=0.3,
            current_ratio=2.1, free_cash_flow=5_000_000,
        ),
        available=True,
    )


def _weak_company() -> Fundamentals:
    income = [
        IncomeStatementLine(period="FY2024", net_income=-50, revenue=800, net_margin=-0.06),
        IncomeStatementLine(period="FY2023", net_income=-20, revenue=900, net_margin=-0.02),
    ]
    return Fundamentals(
        income_statement=income,
        valuation=ValuationMetrics(
            profit_margin=-0.05, roe=-0.10, revenue_growth=-0.11, debt_to_equity=3.2,
            current_ratio=0.7, free_cash_flow=-2_000_000,
        ),
        available=True,
    )


def test_strong_company_scores_strong():
    health = assess_financial_health(_strong_company(), annualized_volatility=0.18,
                                     maximum_drawdown=-0.12)
    assert health.classification == "Strong"
    assert health.score >= 70
    assert any("strong" in r.lower() for r in health.reasons)


def test_weak_company_scores_weak():
    health = assess_financial_health(_weak_company(), annualized_volatility=0.6,
                                     maximum_drawdown=-0.55)
    assert health.classification == "Weak"
    assert health.score < 45


def test_insufficient_data_is_unknown():
    health = assess_financial_health(Fundamentals(available=False))
    assert health.classification == "Unknown"
    assert health.score is None
