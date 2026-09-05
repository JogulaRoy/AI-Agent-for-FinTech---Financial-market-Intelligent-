"""Fundamental data + derived financial-health contracts."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import DataProvenance


class IncomeStatementLine(BaseModel):
    period: str                        # e.g. "FY2025" or "2025-09-27"
    fiscal_year: Optional[str] = None
    reported_currency: Optional[str] = None
    revenue: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_income: Optional[float] = None
    ebitda: Optional[float] = None
    net_income: Optional[float] = None
    eps: Optional[float] = None
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None


class BalanceSheetLine(BaseModel):
    period: str
    fiscal_year: Optional[str] = None
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    total_equity: Optional[float] = None
    cash_and_equivalents: Optional[float] = None
    total_debt: Optional[float] = None
    current_assets: Optional[float] = None
    current_liabilities: Optional[float] = None


class CashFlowLine(BaseModel):
    period: str
    fiscal_year: Optional[str] = None
    operating_cash_flow: Optional[float] = None
    investing_cash_flow: Optional[float] = None
    financing_cash_flow: Optional[float] = None
    capital_expenditure: Optional[float] = None
    free_cash_flow: Optional[float] = None


class ValuationMetrics(BaseModel):
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    ps_ratio: Optional[float] = None
    ev_to_ebitda: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    profit_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    dividend_yield: Optional[float] = None
    revenue_growth: Optional[float] = None
    earnings_growth: Optional[float] = None
    free_cash_flow: Optional[float] = None

    provenance: Optional[DataProvenance] = None


class HealthFactor(BaseModel):
    name: str
    value: Optional[float] = None
    verdict: str                       # "strong" | "moderate" | "weak" | "unknown"
    weight: float = 1.0
    detail: str = ""


class FinancialHealth(BaseModel):
    """Transparent, metric-backed stability assessment. NOT a regulated rating."""

    classification: str = "Unknown"    # "Strong" | "Moderate" | "Weak" | "Unknown"
    score: Optional[float] = None       # 0-100, project-specific
    factors: list[HealthFactor] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    disclaimer: str = (
        "Project-specific financial-health assessment derived from measurable "
        "fundamentals. Not a regulated financial rating or investment advice."
    )


class Fundamentals(BaseModel):
    income_statement: list[IncomeStatementLine] = Field(default_factory=list)
    balance_sheet: list[BalanceSheetLine] = Field(default_factory=list)
    cash_flow: list[CashFlowLine] = Field(default_factory=list)
    valuation: ValuationMetrics = Field(default_factory=ValuationMetrics)
    health: FinancialHealth = Field(default_factory=FinancialHealth)
    available: bool = False
    unavailable_reason: Optional[str] = None
    provenance: Optional[DataProvenance] = None
