"""
Provider Manager.

Owns the concrete provider instances and, for each capability, tries them in a
sensible order (market-aware), returning the first usable result while
recording which source answered and what went wrong along the way.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from app.config.settings import settings
from app.data.http import ProviderError, ProviderNotSupported
from app.data.providers import (
    EODHDProvider,
    FMPProvider,
    FinancialDataProvider,
    TwelveDataProvider,
    YFinanceProvider,
)
from app.schemas.fundamentals import Fundamentals
from app.schemas.market_data import CompanyProfile, PriceHistory, Quote
from app.schemas.news_data import NewsArticle
from app.schemas.security import CanonicalSecurity, SecurityCandidate


@dataclass
class ProviderOutcome:
    """Result of a capability call plus the audit trail."""

    value: object = None
    provider: Optional[str] = None
    attempts: list[str] = field(default_factory=list)   # "fmp: ok" / "eodhd: not supported"

    @property
    def ok(self) -> bool:
        return self.value is not None


class ProviderManager:
    def __init__(self) -> None:
        self._providers: dict[str, FinancialDataProvider] = {}
        self._register(FMPProvider(settings.fmp_api_key))
        self._register(TwelveDataProvider(settings.twelve_data_api_key))
        self._register(EODHDProvider(settings.eodhd_api_key))
        if settings.enable_yfinance_fallback:
            self._register(YFinanceProvider())

    def _register(self, provider: FinancialDataProvider) -> None:
        if provider.enabled:
            self._providers[provider.name] = provider

    @property
    def available(self) -> list[str]:
        return list(self._providers)

    # --- ordering --------------------------------------------------

    def _order(self, capability: str, security: Optional[CanonicalSecurity]) -> list[str]:
        indian = bool(security and security.is_indian)
        table = {
            "profile": (
                ["yfinance", "fmp", "eodhd", "twelve_data"] if indian
                else ["fmp", "yfinance", "twelve_data", "eodhd"]
            ),
            "quote": (
                ["yfinance", "twelve_data", "fmp", "eodhd"] if indian
                else ["twelve_data", "fmp", "eodhd", "yfinance"]
            ),
            "history": (
                ["yfinance", "twelve_data", "fmp", "eodhd"] if indian
                else ["fmp", "twelve_data", "eodhd", "yfinance"]
            ),
            "fundamentals": (
                ["yfinance", "fmp"] if indian else ["fmp", "yfinance"]
            ),
            "news": ["eodhd", "yfinance"],
            "search": ["eodhd", "fmp", "twelve_data", "yfinance"],
        }
        names = table.get(capability, list(self._providers))
        market = "IN" if indian else "US"
        result = []
        for name in names:
            provider = self._providers.get(name)
            if not provider:
                continue
            if not getattr(provider.capabilities, capability, False):
                continue
            if capability in {"profile", "quote", "history", "fundamentals"}:
                if not provider.serves_market(market):
                    continue
            result.append(name)
        return result

    def _try(
        self,
        capability: str,
        security: Optional[CanonicalSecurity],
        call: Callable[[FinancialDataProvider], object],
    ) -> ProviderOutcome:
        outcome = ProviderOutcome()
        for name in self._order(capability, security):
            provider = self._providers[name]
            try:
                value = call(provider)
            except ProviderNotSupported as exc:
                outcome.attempts.append(f"{name}: not supported ({exc})")
                continue
            except ProviderError as exc:
                outcome.attempts.append(f"{name}: {exc}")
                continue
            except Exception as exc:  # noqa: BLE001 - provider libs can raise anything
                outcome.attempts.append(f"{name}: unexpected error ({exc})")
                continue
            if value is None or (isinstance(value, (list, dict)) and len(value) == 0):
                outcome.attempts.append(f"{name}: empty")
                continue
            outcome.value = value
            outcome.provider = name
            outcome.attempts.append(f"{name}: ok")
            return outcome
        return outcome

    # --- capability facades --------------------------------------

    def search_all(self, query: str) -> tuple[list[SecurityCandidate], list[str]]:
        candidates: list[SecurityCandidate] = []
        attempts: list[str] = []
        for name in self._order("search", None):
            provider = self._providers[name]
            try:
                found = provider.search(query) or []
                attempts.append(f"{name}: {len(found)} hits")
                candidates.extend(found)
            except ProviderError as exc:
                attempts.append(f"{name}: {exc}")
            except Exception as exc:  # noqa: BLE001
                attempts.append(f"{name}: unexpected error ({exc})")
        return candidates, attempts

    def get_profile(self, security: CanonicalSecurity) -> ProviderOutcome:
        return self._try("profile", security, lambda p: p.get_profile(security))

    def get_quote(self, security: CanonicalSecurity) -> ProviderOutcome:
        return self._try("quote", security, lambda p: p.get_quote(security))

    def get_history(self, security: CanonicalSecurity, period: str = "5y") -> ProviderOutcome:
        return self._try("history", security, lambda p: p.get_history(security, period))

    def get_fundamentals(self, security: CanonicalSecurity) -> ProviderOutcome:
        return self._try("fundamentals", security, lambda p: p.get_fundamentals(security))

    def get_news(
        self, security: CanonicalSecurity, hours: int = 168, limit: int = 20
    ) -> ProviderOutcome:
        return self._try("news", security, lambda p: p.get_news(security, hours, limit))


# Lightweight module-level singleton (safe: providers are stateless).
_manager: Optional[ProviderManager] = None


def get_provider_manager() -> ProviderManager:
    global _manager
    if _manager is None:
        _manager = ProviderManager()
    return _manager
