"""
yfinance fallback provider.

Not a primary source. It exists so the system still works for markets the
free API tiers do not cover (notably Indian NSE/BSE equities). Every value it
returns is provenance-tagged ``provider="yfinance"`` so the UI can show it.
"""

from __future__ import annotations

from typing import Any, Optional

from app.data.http import ProviderDataError
from app.data.providers.base import (
    FinancialDataProvider,
    ProviderCapabilities,
    period_to_days,
)
from app.schemas.common import DataProvenance
from app.schemas.fundamentals import Fundamentals, ValuationMetrics
from app.schemas.market_data import CompanyProfile, OHLCVBar, PriceHistory, Quote
from app.schemas.security import CanonicalSecurity, SecurityCandidate

_PERIOD_MAP = {
    "1mo": "1mo", "3mo": "3mo", "6mo": "6mo", "1y": "1y",
    "2y": "2y", "5y": "5y", "10y": "10y", "max": "max",
}


def _f(value: Any) -> Optional[float]:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


class YFinanceProvider(FinancialDataProvider):
    name = "yfinance"
    capabilities = ProviderCapabilities(
        search=True, profile=True, quote=True, history=True,
        fundamentals=True, news=True, markets=("GLOBAL",),
    )

    def __init__(self, api_key: str = "yfinance"):
        super().__init__(api_key or "yfinance")

    @property
    def enabled(self) -> bool:
        return True

    def _yf(self):
        import yfinance as yf  # imported lazily; heavy dependency
        return yf

    def _yahoo_symbol(self, security: CanonicalSecurity) -> str:
        if security.provider_symbols.get(self.name):
            return security.provider_symbols[self.name]
        exch = (security.exchange or "").upper()
        if exch in {"NSE", "NSI"}:
            return f"{security.symbol}.NS"
        if exch in {"BSE", "BOM"}:
            return f"{security.symbol}.BO"
        return security.symbol

    # --- search --------------------------------------------------------

    def search(self, query: str) -> list[SecurityCandidate]:
        yf = self._yf()
        try:
            quotes = yf.Search(query, max_results=20, enable_fuzzy_query=True).quotes or []
        except Exception as exc:  # noqa: BLE001 - yfinance raises many things
            raise ProviderDataError(f"yfinance: search failed ({exc})")
        out: list[SecurityCandidate] = []
        for q in quotes:
            if (q.get("quoteType") or "").upper() != "EQUITY":
                continue
            sym = (q.get("symbol") or "").strip()
            if not sym:
                continue
            name = q.get("longname") or q.get("shortname") or sym
            exch = (q.get("exchange") or "").upper()
            country = None
            if sym.endswith(".NS") or sym.endswith(".NSI"):
                country, exch = "India", "NSE"
            elif sym.endswith(".BO"):
                country, exch = "India", "BSE"
            out.append(
                SecurityCandidate(
                    company_name=name,
                    symbol=sym.split(".")[0],
                    exchange=exch,
                    country=country,
                    currency="INR" if country == "India" else q.get("currency"),
                    source="yfinance",
                    provider_symbols={"yfinance": sym},
                )
            )
        return out

    # --- profile -----------------------------------------------------

    def get_profile(self, security: CanonicalSecurity) -> CompanyProfile:
        yf = self._yf()
        ticker = yf.Ticker(self._yahoo_symbol(security))
        try:
            info = ticker.get_info() or {}
        except Exception:  # noqa: BLE001
            info = {}
        if not info:
            raise ProviderDataError("yfinance: no profile")
        return CompanyProfile(
            company_name=info.get("longName") or info.get("shortName") or security.company_name,
            symbol=security.symbol,
            exchange=info.get("fullExchangeName") or security.exchange,
            country=info.get("country") or security.country,
            sector=info.get("sector"),
            industry=info.get("industry"),
            currency=info.get("currency") or security.currency,
            market_cap=_f(info.get("marketCap")),
            shares_outstanding=_f(info.get("sharesOutstanding")),
            description=info.get("longBusinessSummary"),
            website=info.get("website"),
            isin=security.isin,
            provenance=DataProvenance(provider="yfinance", endpoint="get_info", as_of="latest"),
        )

    # --- quote -----------------------------------------------------

    def get_quote(self, security: CanonicalSecurity) -> Quote:
        yf = self._yf()
        symbol = self._yahoo_symbol(security)
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="5d", interval="1d", auto_adjust=False)
        if hist is None or hist.empty:
            raise ProviderDataError(f"yfinance: no quote for {symbol}")
        last = hist.iloc[-1]
        prev_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else None
        price = float(last["Close"])
        currency = security.currency
        try:
            fi = ticker.fast_info
            currency = fi.get("currency") or currency
            w52h = _f(fi.get("year_high"))
            w52l = _f(fi.get("year_low"))
        except Exception:  # noqa: BLE001
            w52h = w52l = None
        change = (price - prev_close) if prev_close else None
        return Quote(
            price=price,
            open=float(last["Open"]),
            high=float(last["High"]),
            low=float(last["Low"]),
            close=price,
            previous_close=prev_close,
            volume=_f(last.get("Volume")),
            change=change,
            change_percent=(change / prev_close) if (change is not None and prev_close) else None,
            week52_high=w52h,
            week52_low=w52l,
            currency=currency,
            timestamp=str(hist.index[-1].date()),
            provenance=DataProvenance(provider="yfinance", endpoint="history", as_of=str(hist.index[-1].date())),
        )

    # --- history --------------------------------------------------

    def get_history(self, security: CanonicalSecurity, period: str = "5y") -> PriceHistory:
        yf = self._yf()
        symbol = self._yahoo_symbol(security)
        yperiod = _PERIOD_MAP.get(period, "5y")
        hist = yf.Ticker(symbol).history(period=yperiod, interval="1d", auto_adjust=False)
        if hist is None or hist.empty:
            raise ProviderDataError(f"yfinance: no history for {symbol}")
        hist = hist.dropna(subset=["Open", "High", "Low", "Close"])
        bars: list[OHLCVBar] = []
        for idx, row in hist.iterrows():
            bars.append(
                OHLCVBar(
                    date=idx.strftime("%Y-%m-%d"),
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    adjusted_close=_f(row.get("Adj Close")) or float(row["Close"]),
                    volume=_f(row.get("Volume")) or 0.0,
                )
            )
        if not bars:
            raise ProviderDataError(f"yfinance: unusable history for {symbol}")
        _ = period_to_days  # keep import symmetry
        return PriceHistory(
            bars=bars,
            frequency="daily",
            adjusted=False,
            currency=security.currency,
            start_date=bars[0].date,
            end_date=bars[-1].date,
            provenance=DataProvenance(
                provider="yfinance", endpoint="history", as_of=bars[-1].date,
                frequency="daily", adjusted=False,
            ),
        )

    # --- fundamentals (best effort from .info) -------------------

    def get_fundamentals(self, security: CanonicalSecurity) -> Fundamentals:
        yf = self._yf()
        try:
            info = yf.Ticker(self._yahoo_symbol(security)).get_info() or {}
        except Exception:  # noqa: BLE001
            info = {}
        if not info:
            raise ProviderDataError("yfinance: no fundamentals")
        # yfinance reports debtToEquity and (in recent versions) dividendYield as
        # percentages; normalise both to ratios/fractions to match the other providers.
        dte = _f(info.get("debtToEquity"))
        if dte is not None and dte > 5:
            dte = dte / 100
        # Current yfinance returns dividendYield as a percentage number
        # (e.g. 0.46 -> 0.46%). Normalise to a fraction.
        div_yield = _f(info.get("dividendYield"))
        if div_yield is not None:
            div_yield = div_yield / 100

        valuation = ValuationMetrics(
            pe_ratio=_f(info.get("trailingPE")),
            pb_ratio=_f(info.get("priceToBook")),
            ps_ratio=_f(info.get("priceToSalesTrailing12Months")),
            ev_to_ebitda=_f(info.get("enterpriseToEbitda")),
            roe=_f(info.get("returnOnEquity")),
            roa=_f(info.get("returnOnAssets")),
            debt_to_equity=dte,
            current_ratio=_f(info.get("currentRatio")),
            quick_ratio=_f(info.get("quickRatio")),
            profit_margin=_f(info.get("profitMargins")),
            operating_margin=_f(info.get("operatingMargins")),
            dividend_yield=div_yield,
            revenue_growth=_f(info.get("revenueGrowth")),
            earnings_growth=_f(info.get("earningsGrowth")),
            free_cash_flow=_f(info.get("freeCashflow")),
            provenance=DataProvenance(provider="yfinance", endpoint="get_info", as_of="ttm"),
        )
        return Fundamentals(
            valuation=valuation,
            available=True,
            unavailable_reason=(
                "yfinance provides summary ratios only; full statements not fetched."
            ),
            provenance=DataProvenance(provider="yfinance", endpoint="get_info", as_of="ttm"),
        )

    # --- news -----------------------------------------------------

    def get_news(self, security: CanonicalSecurity, hours: int = 168, limit: int = 20):
        yf = self._yf()
        from app.schemas.news_data import NewsArticle
        from datetime import datetime, timezone

        try:
            raw = yf.Ticker(self._yahoo_symbol(security)).news or []
        except Exception as exc:  # noqa: BLE001
            raise ProviderDataError(f"yfinance: news failed ({exc})")
        out: list[NewsArticle] = []
        for item in raw[:limit]:
            content = item.get("content", item) if isinstance(item, dict) else {}
            title = content.get("title") or item.get("title") or ""
            if not title:
                continue
            pub = content.get("pubDate") or ""
            provider = ((content.get("provider") or {}).get("displayName")
                        if isinstance(content.get("provider"), dict) else None)
            url = ""
            cu = content.get("canonicalUrl") or content.get("clickThroughUrl")
            if isinstance(cu, dict):
                url = cu.get("url", "")
            out.append(
                NewsArticle(
                    title=title,
                    source=provider or "Yahoo Finance",
                    published_at=str(pub),
                    url=url or item.get("link", ""),
                    summary=(content.get("summary") or "")[:500],
                    provider="yfinance",
                )
            )
        _ = (datetime, timezone)
        return out
