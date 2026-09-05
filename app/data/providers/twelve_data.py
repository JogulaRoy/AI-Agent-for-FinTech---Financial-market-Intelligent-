"""Twelve Data provider.

Free plan: US ``/quote`` and ``/time_series`` plus a global ``/symbol_search``
(useful for resolution even where price data needs a paid plan).
"""

from __future__ import annotations

from typing import Any, Optional

from app.data.http import ProviderDataError, request_json
from app.data.providers.base import (
    FinancialDataProvider,
    ProviderCapabilities,
    period_to_days,
)
from app.schemas.common import DataProvenance
from app.schemas.market_data import CompanyProfile, OHLCVBar, PriceHistory, Quote
from app.schemas.security import CanonicalSecurity, SecurityCandidate

_BASE = "https://api.twelvedata.com"


def _f(value: Any) -> Optional[float]:
    try:
        if value in (None, "", "None"):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


class TwelveDataProvider(FinancialDataProvider):
    name = "twelve_data"
    capabilities = ProviderCapabilities(
        search=True,
        profile=True,
        quote=True,
        history=True,
        fundamentals=False,
        news=False,
        markets=("US",),
    )

    def _get(self, path: str, params: dict[str, Any], ttl: Optional[int] = None) -> Any:
        params = {**params, "apikey": self.api_key}
        return request_json(f"{_BASE}/{path}", params=params, provider=self.name, cache_ttl=ttl)

    def _symbol(self, security: CanonicalSecurity) -> str:
        return security.provider_symbols.get(self.name) or security.symbol

    # --- search --------------------------------------------------------

    def search(self, query: str) -> list[SecurityCandidate]:
        data = self._get("symbol_search", {"symbol": query, "outputsize": 20}, ttl=86400)
        rows = (data or {}).get("data", []) if isinstance(data, dict) else []
        out: list[SecurityCandidate] = []
        for row in rows:
            sym = (row.get("symbol") or "").strip()
            if not sym:
                continue
            exch = row.get("exchange")
            out.append(
                SecurityCandidate(
                    company_name=row.get("instrument_name") or sym,
                    symbol=sym,
                    exchange=exch,
                    country=row.get("country"),
                    currency=row.get("currency"),
                    asset_type=row.get("instrument_type") or "EQUITY",
                    source="twelve_data",
                    provider_symbols={"twelve_data": sym},
                )
            )
        return out

    # --- profile (from quote meta) ----------------------------------

    def get_profile(self, security: CanonicalSecurity) -> CompanyProfile:
        symbol = self._symbol(security)
        data = self._get("quote", {"symbol": symbol}, ttl=600)
        if not isinstance(data, dict) or "close" not in data:
            raise ProviderDataError(f"twelve_data: no profile for {symbol}")
        return CompanyProfile(
            company_name=data.get("name") or security.company_name,
            symbol=data.get("symbol") or symbol,
            exchange=data.get("exchange"),
            currency=data.get("currency"),
            provenance=DataProvenance(provider="twelve_data", endpoint="quote", as_of="latest"),
        )

    # --- quote --------------------------------------------------------

    def get_quote(self, security: CanonicalSecurity) -> Quote:
        symbol = self._symbol(security)
        data = self._get("quote", {"symbol": symbol}, ttl=120)
        if not isinstance(data, dict) or data.get("close") in (None, ""):
            raise ProviderDataError(f"twelve_data: no quote for {symbol}")
        fifty_two = data.get("fifty_two_week") or {}
        return Quote(
            price=_f(data.get("close")),
            open=_f(data.get("open")),
            high=_f(data.get("high")),
            low=_f(data.get("low")),
            close=_f(data.get("close")),
            previous_close=_f(data.get("previous_close")),
            volume=_f(data.get("volume")),
            change=_f(data.get("change")),
            change_percent=(lambda p: p / 100 if p is not None else None)(_f(data.get("percent_change"))),
            week52_high=_f(fifty_two.get("high")),
            week52_low=_f(fifty_two.get("low")),
            currency=data.get("currency") or security.currency,
            timestamp=str(data.get("datetime") or ""),
            provenance=DataProvenance(provider="twelve_data", endpoint="quote", as_of=str(data.get("datetime") or "latest")),
        )

    # --- history -----------------------------------------------------

    def get_history(self, security: CanonicalSecurity, period: str = "5y") -> PriceHistory:
        symbol = self._symbol(security)
        outputsize = min(5000, max(30, period_to_days(period) * 5 // 7))
        data = self._get(
            "time_series",
            {"symbol": symbol, "interval": "1day", "outputsize": outputsize, "order": "ASC"},
            ttl=3600,
        )
        values = (data or {}).get("values", []) if isinstance(data, dict) else []
        meta = (data or {}).get("meta", {}) if isinstance(data, dict) else {}
        bars: list[OHLCVBar] = []
        for row in values:
            try:
                bars.append(
                    OHLCVBar(
                        date=str(row["datetime"])[:10],
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        volume=_f(row.get("volume")) or 0.0,
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
        if not bars:
            raise ProviderDataError(f"twelve_data: no history for {symbol}")
        bars.sort(key=lambda b: b.date)
        return PriceHistory(
            bars=bars,
            frequency="daily",
            adjusted=False,
            currency=meta.get("currency") or security.currency,
            start_date=bars[0].date,
            end_date=bars[-1].date,
            provenance=DataProvenance(
                provider="twelve_data", endpoint="time_series", as_of=bars[-1].date,
                frequency="daily", adjusted=False,
            ),
        )
