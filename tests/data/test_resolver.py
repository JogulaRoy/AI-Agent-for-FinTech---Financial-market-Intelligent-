"""Resolver scoring tests — no network, provider search is stubbed."""

import pytest

from app.data import resolver
from app.schemas.security import SecurityCandidate


class _FakeManager:
    def __init__(self, hits):
        self._hits = hits

    def search_all(self, query):
        return list(self._hits), ["fake"]


@pytest.fixture(autouse=True)
def _no_nse(monkeypatch):
    monkeypatch.setattr(resolver, "_india_candidate", lambda q: None)


def test_exact_ticker_beats_coincidental_name_match():
    hits = [
        SecurityCandidate(company_name="Apple Inc.", symbol="AAPL", exchange="NASDAQ",
                          currency="USD", source="fmp", provider_symbols={"fmp": "AAPL"}),
        SecurityCandidate(company_name="Apple Hospitality REIT, Inc.", symbol="APLE",
                          exchange="NYSE", currency="USD", source="fmp",
                          provider_symbols={"fmp": "APLE"}),
    ]
    result = resolver.resolve_security("AAPL", _FakeManager(hits))
    assert result.symbol == "AAPL"
    assert result.company_name == "Apple Inc."


def test_corroboration_across_sources_wins_for_ambiguous_ticker():
    hits = [
        SecurityCandidate(company_name="Tata Consultancy Services Ltd", symbol="TCS",
                          exchange="NSE", country="India", currency="INR", isin="INE467B01029",
                          source="eodhd", provider_symbols={"eodhd": "TCS.NSE"}),
        SecurityCandidate(company_name="Tata Consultancy Services Ltd", symbol="TCS",
                          exchange="NSE", country="India", currency="INR",
                          source="twelve_data", provider_symbols={"twelve_data": "TCS"}),
        SecurityCandidate(company_name="Tata Consultancy Services Ltd", symbol="TCS.NS",
                          exchange="NSE", country="India", currency="INR",
                          source="fmp", provider_symbols={"fmp": "TCS.NS"}),
        SecurityCandidate(company_name="TCS Group Holding PLC", symbol="TCS", exchange="LSE",
                          currency="USD", source="fmp", provider_symbols={"fmp": "TCS.L"}),
    ]
    result = resolver.resolve_security("TCS", _FakeManager(hits))
    assert "tata consultancy" in result.company_name.lower()
    assert result.is_indian
    # provider symbols for the chosen identity, not the LSE listing
    assert result.provider_symbols["fmp"].endswith(".NS")
    assert result.provider_symbols["eodhd"].endswith(".NSE")


def test_raises_when_nothing_matches():
    with pytest.raises(ValueError):
        resolver.resolve_security("zzzznotarealthing", _FakeManager([]))


def test_indian_abbreviation_beats_exact_ticker_fund(monkeypatch):
    """`SBI` must resolve to State Bank of India, not a US muni fund whose
    ticker happens to be exactly 'SBI'. Uses the real (offline, cached) NSE
    master for the Indian candidate."""
    monkeypatch.undo()  # drop the autouse _india_candidate stub for this test
    fund = SecurityCandidate(
        company_name="Western Asset Intermediate Muni Fund Inc.", symbol="SBI",
        exchange="NYSE", currency="USD", source="fmp,eodhd",
        provider_symbols={"fmp": "SBI", "eodhd": "SBI.US"},
    )
    result = resolver.resolve_security("SBI", _FakeManager([fund]))
    assert result.symbol == "SBIN"
    assert "state bank of india" in result.company_name.lower()
    assert result.is_indian
