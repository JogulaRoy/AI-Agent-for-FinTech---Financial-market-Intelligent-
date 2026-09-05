"""Financial Modeling Prep provider (uses the current ``/stable`` API)."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Optional

from app.data.http import ProviderDataError, ProviderNotSupported, request_json
from app.data.providers.base import (
    FinancialDataProvider,
    ProviderCapabilities,
    period_to_days,
)
from app.schemas.common import DataProvenance
from app.schemas.fundamentals import (
    BalanceSheetLine,
    CashFlowLine,
    Fundamentals,
    IncomeStatementLine,
    ValuationMetrics,
)
from app.schemas.market_data import CompanyProfile, OHLCVBar, PriceHistory, Quote
from app.schemas.security import CanonicalSecurity, SecurityCandidate

_BASE = "https://financialmodelingprep.com/stable"


def _f(value: Any) -> Optional[float]:
    try:
        if value in (None, "", "None"):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_div(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b in (None, 0):
        return None
    return a / b


def _pct_to_fraction(value: Optional[float]) -> Optional[float]:
    """Providers report change % as a percent number (e.g. -0.05 for -0.05%)."""
    return None if value is None else value / 100


class FMPProvider(FinancialDataProvider):
    name = "fmp"
    capabilities = ProviderCapabilities(
        search=True,
        profile=True,
        quote=True,
        history=True,
        fundamentals=True,
        news=False,
        markets=("US",),           # free plan: US listings only
    )

    def _get(self, path: str, params: dict[str, Any], ttl: Optional[int] = None) -> Any:
        params = {**params, "apikey": self.api_key}
        return request_json(f"{_BASE}/{path}", params=params, provider=self.name, cache_ttl=ttl)

    # --- search ---------------------------------------------------------

    def search(self, query: str) -> list[SecurityCandidate]:
        out: list[SecurityCandidate] = []
        seen: set[str] = set()
        for path in ("search-symbol", "search-name"):
            try:
                rows = self._get(path, {"query": query, "limit": 20})
            except (ProviderDataError, ProviderNotSupported):
                continue
            for row in rows or []:
                sym = (row.get("symbol") or "").strip()
                if not sym or sym in seen:
                    continue
                seen.add(sym)
                out.append(
                    SecurityCandidate(
                        company_name=row.get("name") or sym,
                        symbol=sym,
                        exchange=row.get("exchange"),
                        currency=row.get("currency"),
                        source="fmp",
                        provider_symbols={"fmp": sym},
                    )
                )
        return out

    # --- profile -------------------------------------------------------

    def get_profile(self, security: CanonicalSecurity) -> CompanyProfile:
        symbol = security.symbol_for(self.name)
        rows = self._get("profile", {"symbol": symbol})
        if not rows:
            raise ProviderDataError(f"fmp: no profile for {symbol}")
        row = rows[0]
        return CompanyProfile(
            company_name=row.get("companyName") or security.company_name,
            symbol=row.get("symbol") or symbol,
            exchange=row.get("exchangeFullName") or row.get("exchange"),
            country=row.get("country"),
            sector=row.get("sector"),
            industry=row.get("industry"),
            currency=row.get("currency"),
            market_cap=_f(row.get("marketCap")),
            description=row.get("description"),
            website=row.get("website"),
            isin=row.get("isin"),
            provenance=DataProvenance(
                provider="fmp", endpoint="profile", as_of="latest",
                currency=row.get("currency"),
            ),
        )

    # --- quote --------------------------------------------------------

    def get_quote(self, security: CanonicalSecurity) -> Quote:
        symbol = security.symbol_for(self.name)
        rows = self._get("quote", {"symbol": symbol}, ttl=120)
        if not rows:
            raise ProviderDataError(f"fmp: no quote for {symbol}")
        row = rows[0]
        price = _f(row.get("price"))
        prev = _f(row.get("previousClose"))
        return Quote(
            price=price,
            open=_f(row.get("open")),
            high=_f(row.get("dayHigh")),
            low=_f(row.get("dayLow")),
            close=price,
            previous_close=prev,
            volume=_f(row.get("volume")),
            change=_f(row.get("change")),
            change_percent=_pct_to_fraction(_f(row.get("changePercentage"))),
            week52_high=_f(row.get("yearHigh")),
            week52_low=_f(row.get("yearLow")),
            currency=security.currency,
            timestamp=str(row.get("timestamp") or ""),
            provenance=DataProvenance(provider="fmp", endpoint="quote", as_of="latest"),
        )

    # --- history -----------------------------------------------------

    def get_history(self, security: CanonicalSecurity, period: str = "5y") -> PriceHistory:
        symbol = security.symbol_for(self.name)
        days = period_to_days(period)
        start = (date.today() - timedelta(days=days)).isoformat()
        rows = self._get(
            "historical-price-eod/full",
            {"symbol": symbol, "from": start, "to": date.today().isoformat()},
            ttl=3600,
        )
        if not rows:
            raise ProviderDataError(f"fmp: no history for {symbol}")
        bars: list[OHLCVBar] = []
        for row in rows:
            try:
                bars.append(
                    OHLCVBar(
                        date=str(row["date"])[:10],
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        adjusted_close=_f(row.get("adjClose") or row.get("close")),
                        volume=_f(row.get("volume")) or 0.0,
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
        bars.sort(key=lambda b: b.date)
        if not bars:
            raise ProviderDataError(f"fmp: unusable history for {symbol}")
        return PriceHistory(
            bars=bars,
            frequency="daily",
            adjusted=False,
            currency=security.currency,
            start_date=bars[0].date,
            end_date=bars[-1].date,
            provenance=DataProvenance(
                provider="fmp", endpoint="historical-price-eod/full",
                as_of=bars[-1].date, frequency="daily", adjusted=False,
            ),
        )

    # --- fundamentals ----------------------------------------------

    def get_fundamentals(self, security: CanonicalSecurity) -> Fundamentals:
        symbol = security.symbol_for(self.name)

        def _try_get(path: str) -> list:
            try:
                return self._get(path, {"symbol": symbol, "limit": 5}, ttl=86400) or []
            except (ProviderDataError, ProviderNotSupported):
                return []

        income = _try_get("income-statement")
        balance = _try_get("balance-sheet-statement")
        cash = _try_get("cash-flow-statement")
        try:
            ratios = (self._get("ratios-ttm", {"symbol": symbol}, ttl=86400) or [{}])[0]
        except (ProviderDataError, ProviderNotSupported):
            ratios = {}
        try:
            keym = (self._get("key-metrics-ttm", {"symbol": symbol}, ttl=86400) or [{}])[0]
        except (ProviderDataError, ProviderNotSupported):
            keym = {}

        if not income and not balance:
            raise ProviderDataError(f"fmp: no fundamentals for {symbol}")

        income_lines = [
            IncomeStatementLine(
                period=str(r.get("fiscalYear") or r.get("date")),
                fiscal_year=str(r.get("fiscalYear") or ""),
                reported_currency=r.get("reportedCurrency"),
                revenue=_f(r.get("revenue")),
                gross_profit=_f(r.get("grossProfit")),
                operating_income=_f(r.get("operatingIncome") or r.get("ebit")),
                ebitda=_f(r.get("ebitda")),
                net_income=_f(r.get("netIncome")),
                eps=_f(r.get("epsDiluted") or r.get("eps")),
                gross_margin=_safe_div(_f(r.get("grossProfit")), _f(r.get("revenue"))),
                operating_margin=_safe_div(
                    _f(r.get("operatingIncome") or r.get("ebit")), _f(r.get("revenue"))
                ),
                net_margin=_safe_div(_f(r.get("netIncome")), _f(r.get("revenue"))),
            )
            for r in income
        ]
        balance_lines = [
            BalanceSheetLine(
                period=str(r.get("fiscalYear") or r.get("date")),
                fiscal_year=str(r.get("fiscalYear") or ""),
                total_assets=_f(r.get("totalAssets")),
                total_liabilities=_f(r.get("totalLiabilities")),
                total_equity=_f(r.get("totalStockholdersEquity") or r.get("totalEquity")),
                cash_and_equivalents=_f(r.get("cashAndCashEquivalents")),
                total_debt=_f(r.get("totalDebt")),
                current_assets=_f(r.get("totalCurrentAssets")),
                current_liabilities=_f(r.get("totalCurrentLiabilities")),
            )
            for r in balance
        ]
        cash_lines = [
            CashFlowLine(
                period=str(r.get("fiscalYear") or r.get("date")),
                fiscal_year=str(r.get("fiscalYear") or ""),
                operating_cash_flow=_f(r.get("operatingCashFlow")
                                       or r.get("netCashProvidedByOperatingActivities")),
                investing_cash_flow=_f(r.get("netCashProvidedByInvestingActivities")),
                financing_cash_flow=_f(r.get("netCashProvidedByFinancingActivities")),
                capital_expenditure=_f(r.get("capitalExpenditure")),
                free_cash_flow=_f(r.get("freeCashFlow")),
            )
            for r in cash
        ]

        rev_growth = None
        earn_growth = None
        if len(income_lines) >= 2:
            rev_growth = _pct_change(income_lines[0].revenue, income_lines[1].revenue)
            earn_growth = _pct_change(income_lines[0].net_income, income_lines[1].net_income)

        valuation = ValuationMetrics(
            pe_ratio=_f(ratios.get("priceToEarningsRatioTTM")),
            pb_ratio=_f(ratios.get("priceToBookRatioTTM")),
            ps_ratio=_f(ratios.get("priceToSalesRatioTTM")),
            ev_to_ebitda=_f(keym.get("evToEBITDATTM") or ratios.get("enterpriseValueMultipleTTM")),
            roe=_f(keym.get("returnOnEquityTTM")),
            roa=_f(keym.get("returnOnAssetsTTM")),
            debt_to_equity=_f(ratios.get("debtToEquityRatioTTM")),
            current_ratio=_f(ratios.get("currentRatioTTM")),
            quick_ratio=_f(ratios.get("quickRatioTTM")),
            profit_margin=_f(ratios.get("netProfitMarginTTM")),
            operating_margin=_f(ratios.get("operatingProfitMarginTTM")),
            dividend_yield=_f(ratios.get("dividendYieldTTM")),
            revenue_growth=rev_growth,
            earnings_growth=earn_growth,
            free_cash_flow=cash_lines[0].free_cash_flow if cash_lines else None,
            provenance=DataProvenance(provider="fmp", endpoint="ratios-ttm", as_of="ttm"),
        )

        return Fundamentals(
            income_statement=income_lines,
            balance_sheet=balance_lines,
            cash_flow=cash_lines,
            valuation=valuation,
            available=True,
            provenance=DataProvenance(
                provider="fmp", endpoint="income/balance/cash-flow",
                as_of=income_lines[0].period if income_lines else "latest",
                frequency="annual",
            ),
        )


def _pct_change(new: Optional[float], old: Optional[float]) -> Optional[float]:
    if new is None or old in (None, 0):
        return None
    return (new - old) / abs(old)
