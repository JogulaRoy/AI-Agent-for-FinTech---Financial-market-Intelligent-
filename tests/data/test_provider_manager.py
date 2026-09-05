"""Provider-manager fallback behaviour with stub providers."""

from app.data.http import ProviderNotSupported, ProviderUnavailableError
from app.data.provider_manager import ProviderManager
from app.data.providers.base import FinancialDataProvider, ProviderCapabilities
from app.schemas.market_data import Quote
from app.schemas.security import CanonicalSecurity


class _Boom(FinancialDataProvider):
    name = "boom"
    capabilities = ProviderCapabilities(quote=True, markets=("US",))

    def get_quote(self, security):
        raise ProviderUnavailableError("boom down")


class _NotSupported(FinancialDataProvider):
    name = "nope"
    capabilities = ProviderCapabilities(quote=True, markets=("US",))

    def get_quote(self, security):
        raise ProviderNotSupported("nope: no US")


class _Good(FinancialDataProvider):
    name = "good"
    capabilities = ProviderCapabilities(quote=True, markets=("US",))

    def get_quote(self, security):
        return Quote(price=42.0, currency="USD")


def _manager(*providers):
    mgr = ProviderManager.__new__(ProviderManager)
    mgr._providers = {p.name: p for p in providers}
    return mgr


def _sec():
    return CanonicalSecurity(company_name="Test", symbol="TST", exchange="NASDAQ", country="USA")


def test_falls_through_to_working_provider(monkeypatch):
    mgr = _manager(_Boom(), _NotSupported(), _Good())
    monkeypatch.setattr(
        mgr, "_order", lambda cap, sec: ["boom", "nope", "good"]
    )
    outcome = mgr.get_quote(_sec())
    assert outcome.ok
    assert outcome.provider == "good"
    assert outcome.value.price == 42.0
    assert any("boom down" in a for a in outcome.attempts)
    assert any("not supported" in a for a in outcome.attempts)


def test_reports_failure_when_all_providers_fail(monkeypatch):
    mgr = _manager(_Boom(), _NotSupported())
    monkeypatch.setattr(mgr, "_order", lambda cap, sec: ["boom", "nope"])
    outcome = mgr.get_quote(_sec())
    assert not outcome.ok
    assert outcome.provider is None
