"""EOD Historical Data provider.

Free-plan reality: global ``/search`` (rich identity incl. ISIN), US end-of-day
prices (limited to ~1 year), a real-time US quote, and a working news feed.
Fundamentals require a paid plan.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

from app.data.http import ProviderDataError, request_json
from app.data.providers.base import (
    FinancialDataProvider,
    ProviderCapabilities,
    period_to_days,
)
from app.schemas.common import DataProvenance
from app.schemas.market_data import CompanyProfile, OHLCVBar, PriceHistory, Quote
from app.schemas.news_data import NewsArticle
from app.schemas.security import CanonicalSecurity, SecurityCandidate

_BASE = "https://eodhd.com/api"


def _f(value: Any) -> Optional[float]:
    try:
        if value in (None, "", "NA"):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


class EODHDProvider(FinancialDataProvider):
    name = "eodhd"
    capabilities = ProviderCapabilities(
        search=True,
        profile=True,
        quote=True,
        history=True,
        fundamentals=False,
        news=True,
        markets=("US", "GLOBAL"),   # search + news are global; prices are US-only on free
    )

    def _get(self, path: str, params: dict[str, Any], ttl: Optional[int] = None) -> Any:
        params = {**params, "api_token": self.api_key, "fmt": "json"}
        return request_json(f"{_BASE}/{path}", params=params, provider=self.name, cache_ttl=ttl)

    def _eod_symbol(self, security: CanonicalSecurity) -> str:
        if security.provider_symbols.get(self.name):
            return security.provider_symbols[self.name]
        exch = (security.exchange or "US").upper()
        mapping = {"NSE": "NSE", "BSE": "BSE", "NASDAQ": "US", "NYSE": "US"}
        return f"{security.symbol}.{mapping.get(exch, 'US')}"

    # --- search --------------------------------------------------------

    def search(self, query: str) -> list[SecurityCandidate]:
        rows = self._get(f"search/{query}", {"limit": 30}, ttl=86400)
        out: list[SecurityCandidate] = []
        for row in rows or []:
            code = (row.get("Code") or "").strip()
            exch = (row.get("Exchange") or "").strip()
            if not code:
                continue
            out.append(
                SecurityCandidate(
                    company_name=row.get("Name") or code,
                    symbol=code,
                    exchange=exch,
                    country=row.get("Country"),
                    currency=row.get("Currency"),
                    isin=row.get("ISIN"),
                    asset_type=row.get("Type") or "EQUITY",
                    source="eodhd",
                    provider_symbols={"eodhd": f"{code}.{exch}" if exch else code},
                )
            )
        return out

    # --- profile (thin, from search) ---------------------------------

    def get_profile(self, security: CanonicalSecurity) -> CompanyProfile:
        rows = self._get(f"search/{security.company_name or security.symbol}", {"limit": 5}, ttl=86400)
        match = None
        for row in rows or []:
            if (row.get("Code") or "").upper() == security.symbol.upper():
                match = row
                break
        match = match or (rows[0] if rows else None)
        if not match:
            raise ProviderDataError("eodhd: no profile")
        return CompanyProfile(
            company_name=match.get("Name") or security.company_name,
            symbol=match.get("Code") or security.symbol,
            exchange=match.get("Exchange"),
            country=match.get("Country"),
            currency=match.get("Currency"),
            isin=match.get("ISIN"),
            provenance=DataProvenance(provider="eodhd", endpoint="search", as_of="latest"),
        )

    # --- quote --------------------------------------------------------

    def get_quote(self, security: CanonicalSecurity) -> Quote:
        symbol = self._eod_symbol(security)
        row = self._get(f"real-time/{symbol}", {}, ttl=120)
        if not isinstance(row, dict) or row.get("close") in (None, "NA"):
            raise ProviderDataError(f"eodhd: no quote for {symbol}")
        ts = row.get("timestamp")
        return Quote(
            price=_f(row.get("close")),
            open=_f(row.get("open")),
            high=_f(row.get("high")),
            low=_f(row.get("low")),
            close=_f(row.get("close")),
            previous_close=_f(row.get("previousClose")),
            volume=_f(row.get("volume")),
            change=_f(row.get("change")),
            change_percent=(lambda p: p / 100 if p is not None else None)(_f(row.get("change_p"))),
            currency=security.currency,
            timestamp=(
                datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
                if isinstance(ts, (int, float))
                else ""
            ),
            provenance=DataProvenance(provider="eodhd", endpoint="real-time", as_of="latest"),
        )

    # --- history -----------------------------------------------------

    def get_history(self, security: CanonicalSecurity, period: str = "5y") -> PriceHistory:
        symbol = self._eod_symbol(security)
        start = (date.today() - timedelta(days=period_to_days(period))).isoformat()
        rows = self._get(
            f"eod/{symbol}",
            {"from": start, "to": date.today().isoformat(), "period": "d"},
            ttl=3600,
        )
        bars: list[OHLCVBar] = []
        for row in rows or []:
            try:
                bars.append(
                    OHLCVBar(
                        date=str(row["date"])[:10],
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        adjusted_close=_f(row.get("adjusted_close")),
                        volume=_f(row.get("volume")) or 0.0,
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
        if not bars:
            raise ProviderDataError(f"eodhd: no history for {symbol}")
        bars.sort(key=lambda b: b.date)
        return PriceHistory(
            bars=bars,
            frequency="daily",
            adjusted=True,
            currency=security.currency,
            start_date=bars[0].date,
            end_date=bars[-1].date,
            provenance=DataProvenance(
                provider="eodhd", endpoint="eod", as_of=bars[-1].date,
                frequency="daily", adjusted=True,
                note="Free plan limits history to ~1 year.",
            ),
        )

    # --- news --------------------------------------------------------

    def get_news(
        self, security: CanonicalSecurity, hours: int = 168, limit: int = 20
    ) -> list[NewsArticle]:
        symbol = self._eod_symbol(security)
        frm = (datetime.now(timezone.utc) - timedelta(hours=hours)).date().isoformat()
        rows = self._get(
            "news",
            {"s": symbol, "limit": limit, "from": frm, "offset": 0},
            ttl=1800,
        )
        articles: list[NewsArticle] = []
        for row in rows or []:
            sentiment = row.get("sentiment") or {}
            polarity = _f(sentiment.get("polarity"))
            label = None
            if polarity is not None:
                label = "Positive" if polarity > 0.1 else "Negative" if polarity < -0.1 else "Neutral"
            content = (row.get("content") or "").strip()
            articles.append(
                NewsArticle(
                    title=row.get("title") or "Untitled",
                    source="EODHD",
                    published_at=str(row.get("date") or ""),
                    url=row.get("link") or "",
                    summary=content[:500],
                    provider_sentiment_label=label,
                    provider_sentiment_score=polarity,
                    provider="eodhd",
                )
            )
        return articles
