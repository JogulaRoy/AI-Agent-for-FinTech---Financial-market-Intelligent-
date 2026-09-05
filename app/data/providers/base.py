"""Abstract financial-data provider.

Every concrete provider implements the same surface. Methods it cannot serve
raise :class:`ProviderNotSupported`; the Provider Manager then falls back.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.data.http import ProviderNotSupported
from app.schemas.fundamentals import Fundamentals
from app.schemas.market_data import CompanyProfile, PriceHistory, Quote
from app.schemas.news_data import NewsArticle
from app.schemas.security import CanonicalSecurity, SecurityCandidate


@dataclass(frozen=True)
class ProviderCapabilities:
    search: bool = False
    profile: bool = False
    quote: bool = False
    history: bool = False
    fundamentals: bool = False
    news: bool = False
    # Markets the provider can actually serve on the configured plan.
    markets: tuple[str, ...] = ("US",)   # "US", "IN", "GLOBAL"


class FinancialDataProvider:
    name: str = "base"
    capabilities: ProviderCapabilities = ProviderCapabilities()

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    # --- identity --------------------------------------------------------

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def serves_market(self, market: str) -> bool:
        caps = self.capabilities.markets
        return "GLOBAL" in caps or market.upper() in caps

    # --- capability methods (override the ones you support) --------------

    def search(self, query: str) -> list[SecurityCandidate]:
        raise ProviderNotSupported(f"{self.name}: search not supported")

    def get_profile(self, security: CanonicalSecurity) -> CompanyProfile:
        raise ProviderNotSupported(f"{self.name}: profile not supported")

    def get_quote(self, security: CanonicalSecurity) -> Quote:
        raise ProviderNotSupported(f"{self.name}: quote not supported")

    def get_history(self, security: CanonicalSecurity, period: str = "5y") -> PriceHistory:
        raise ProviderNotSupported(f"{self.name}: history not supported")

    def get_fundamentals(self, security: CanonicalSecurity) -> Fundamentals:
        raise ProviderNotSupported(f"{self.name}: fundamentals not supported")

    def get_news(
        self, security: CanonicalSecurity, hours: int = 168, limit: int = 20
    ) -> list[NewsArticle]:
        raise ProviderNotSupported(f"{self.name}: news not supported")


# --- shared helpers -----------------------------------------------------

_PERIOD_TO_DAYS = {
    "1mo": 31,
    "3mo": 93,
    "6mo": 186,
    "1y": 366,
    "2y": 731,
    "5y": 1827,
    "10y": 3653,
    "max": 3653 * 3,
}


def period_to_days(period: str) -> int:
    return _PERIOD_TO_DAYS.get(period, 1827)
