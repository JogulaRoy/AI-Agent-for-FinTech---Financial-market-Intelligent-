"""Fake ProviderManager + synthetic data for agent-level tests (no network)."""

from __future__ import annotations

import numpy as np
import pytest

from app.data.provider_manager import ProviderOutcome
from app.schemas.common import DataProvenance
from app.schemas.fundamentals import (
    Fundamentals,
    IncomeStatementLine,
    ValuationMetrics,
)
from app.schemas.market_data import CompanyProfile, OHLCVBar, PriceHistory, Quote
from app.schemas.news_data import NewsArticle
from app.schemas.security import CanonicalSecurity


@pytest.fixture
def security() -> CanonicalSecurity:
    return CanonicalSecurity(
        company_name="Testco Inc.", symbol="TST", exchange="NASDAQ",
        country="USA", currency="USD", isin="US0000000001",
        provider_symbols={"fmp": "TST", "yfinance": "TST"}, resolved_by="fmp",
        confidence=0.9,
    )


@pytest.fixture
def price_history() -> PriceHistory:
    rng = np.random.default_rng(7)
    n = 400
    rets = rng.normal(0.0005, 0.014, n)
    close = 50 * np.cumprod(1 + rets)
    bars = []
    for i in range(n):
        c = float(close[i])
        o = float(close[i - 1]) if i else 50.0
        bars.append(OHLCVBar(
            date=f"2024-{(i % 12) + 1:02d}-{(i % 27) + 1:02d}" if False else _date(i),
            open=o, high=max(o, c) * 1.01, low=min(o, c) * 0.99, close=c,
            adjusted_close=c, volume=1_000_000 + i * 10,
        ))
    return PriceHistory(
        bars=bars, currency="USD", start_date=bars[0].date, end_date=bars[-1].date,
        provenance=DataProvenance(provider="fmp", endpoint="history", as_of=bars[-1].date),
    )


def _date(i: int) -> str:
    import datetime
    return (datetime.date(2023, 1, 2) + datetime.timedelta(days=i)).isoformat()


@pytest.fixture
def fundamentals() -> Fundamentals:
    income = [
        IncomeStatementLine(period=f"FY202{y}", net_income=200 + y * 10,
                            revenue=2000 + y * 100, net_margin=0.15, eps=2.0 + y * 0.1)
        for y in (4, 3, 2, 1)
    ]
    return Fundamentals(
        income_statement=income,
        valuation=ValuationMetrics(
            pe_ratio=18, pb_ratio=3, ps_ratio=4, roe=0.22, roa=0.11,
            debt_to_equity=0.4, current_ratio=1.8, profit_margin=0.16,
            revenue_growth=0.10, free_cash_flow=3_000_000,
        ),
        available=True,
        provenance=DataProvenance(provider="fmp", endpoint="fundamentals", as_of="FY2024"),
    )


class FakeManager:
    """Implements only what the agents call."""

    def __init__(self, history, fundamentals=None, quote=None, profile=None, news=None):
        self._history = history
        self._fundamentals = fundamentals
        self._quote = quote
        self._profile = profile
        self._news = news if news is not None else []

    def _ok(self, value, provider="fmp"):
        return ProviderOutcome(value=value, provider=provider, attempts=[f"{provider}: ok"])

    def _fail(self):
        return ProviderOutcome(value=None, provider=None, attempts=["all providers failed"])

    def get_history(self, security, period="5y"):
        return self._ok(self._history) if self._history is not None else self._fail()

    def get_quote(self, security):
        return self._ok(self._quote) if self._quote is not None else self._fail()

    def get_profile(self, security):
        return self._ok(self._profile) if self._profile is not None else self._fail()

    def get_fundamentals(self, security):
        return self._ok(self._fundamentals) if self._fundamentals is not None else self._fail()

    def get_news(self, security, hours=168, limit=20):
        return self._ok(list(self._news), provider="eodhd") if self._news else self._fail()


@pytest.fixture
def manager_factory(price_history, fundamentals):
    def _make(**overrides):
        base = dict(
            history=price_history,
            fundamentals=fundamentals,
            quote=Quote(price=float(price_history.bars[-1].close), previous_close=float(
                price_history.bars[-2].close), currency="USD", week52_high=99, week52_low=40,
                change_percent=0.004),
            profile=CompanyProfile(company_name="Testco Inc.", symbol="TST", sector="Technology",
                                   industry="Software", currency="USD", market_cap=5.0e10),
            news=[
                NewsArticle(title="Testco beats earnings and raises guidance", source="Wire",
                            published_at="2024-06-01", url="http://x/1",
                            summary="strong growth and profit", provider="eodhd",
                            provider_sentiment_label="Positive", provider_sentiment_score=0.4),
                NewsArticle(title="Testco faces regulatory probe over data", source="Wire",
                            published_at="2024-06-02", url="http://x/2",
                            summary="lawsuit and decline risk", provider="eodhd",
                            provider_sentiment_label="Negative", provider_sentiment_score=-0.3),
            ],
        )
        base.update(overrides)
        return FakeManager(**base)
    return _make
