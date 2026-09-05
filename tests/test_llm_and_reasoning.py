from app.agents.reasoning_agent import deterministic_classification, run_reasoning_agent
from app.llm.gemini import _extract_json
from app.schemas.market_data import DataAgentResult, CompanyProfile, Quote, PriceHistory
from app.schemas.fundamentals import Fundamentals, FinancialHealth
from app.schemas.market_data import PerformanceMetrics
from app.schemas.security import CanonicalSecurity
from app.schemas.technical_data import TechnicalAnalysis


def test_extract_json_handles_code_fence():
    assert _extract_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_extract_json_salvages_truncated_object():
    truncated = '{"company_overview": "long text that got cut off mid sentence'
    result = _extract_json(truncated)
    assert result["company_overview"].startswith("long text")


def _data(health_class="Strong", one_year=0.2):
    return DataAgentResult(
        profile=CompanyProfile(company_name="X", symbol="X"),
        quote=Quote(price=1.0),
        history=PriceHistory(bars=[]),
        fundamentals=Fundamentals(available=True,
                                  health=FinancialHealth(classification=health_class, score=80)),
        performance=PerformanceMetrics(one_year_return=one_year),
    )


def test_deterministic_classification_bullish():
    tech = TechnicalAnalysis(symbol="X", overall_signal="Bullish")
    label, notes = deterministic_classification(_data(), tech, None, None)
    assert label == "Bullish"
    assert notes


def test_deterministic_classification_bearish():
    tech = TechnicalAnalysis(symbol="X", overall_signal="Bearish")
    label, _ = deterministic_classification(_data("Weak", -0.3), tech, None, None)
    assert label == "Bearish"


def test_reasoning_agent_without_llm_falls_back_to_rules(monkeypatch):
    monkeypatch.setattr("app.agents.reasoning_agent.get_llm_client", lambda: None)
    out = run_reasoning_agent(
        CanonicalSecurity(company_name="X", symbol="X"),
        data=_data(),
        technical=TechnicalAnalysis(symbol="X", overall_signal="Bullish"),
    )
    assert out.available is False
    assert out.classification in {"Bullish", "Neutral", "Bearish"}
    assert "rule-based" in out.classification_rationale.lower()
