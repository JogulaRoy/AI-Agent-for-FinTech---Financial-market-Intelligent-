import pytest

from app.agents.data_agent import DataAgentError, run_data_agent
from app.agents.news_agent import run_news_agent
from app.agents.reasoning_agent import run_reasoning_agent
from app.agents.risk_agent import run_risk_agent
from app.agents.technical_agent import run_technical_agent


# ---------------- Data Agent ----------------

def test_data_agent_builds_full_result(security, manager_factory):
    result = run_data_agent(security, period="2y", manager=manager_factory())
    assert result.profile.company_name == "Testco Inc."
    assert result.quote.price is not None
    assert len(result.history) > 200
    assert result.fundamentals.available
    assert result.fundamentals.health.classification in {"Strong", "Moderate", "Weak"}
    assert result.stability.annualized_volatility is not None
    assert "fmp" in result.sources_used


def test_data_agent_degrades_when_fundamentals_missing(security, manager_factory):
    result = run_data_agent(security, period="2y",
                            manager=manager_factory(fundamentals=None))
    assert not result.fundamentals.available
    assert result.fundamentals.health.classification == "Unknown"
    assert any("fundamental" in w.lower() for w in result.warnings)


def test_data_agent_raises_without_history(security, manager_factory):
    with pytest.raises(DataAgentError):
        run_data_agent(security, manager=manager_factory(history=None))


def test_data_agent_uses_last_close_when_quote_unavailable(security, manager_factory):
    result = run_data_agent(security, period="2y", manager=manager_factory(quote=None))
    assert result.quote.price == pytest.approx(result.history.bars[-1].close)
    assert any("quote" in w.lower() for w in result.warnings)


# ---------------- Technical Agent ----------------

def test_technical_agent_produces_structured_signal(security, price_history):
    result = run_technical_agent(security, price_history, period="2y")
    assert result.overall_signal in {"Bullish", "Neutral", "Bearish"}
    assert result.rsi.value is not None and 0 <= result.rsi.value <= 100
    assert result.rsi.method == "Wilder"
    assert result.macd.macd is not None
    assert result.atr.value is not None
    summary = result.as_summary()
    assert set(summary) >= {"trend", "rsi", "macd", "support", "resistance", "overall_signal"}


def test_technical_agent_insufficient_history(security):
    from app.schemas.market_data import OHLCVBar, PriceHistory
    tiny = PriceHistory(bars=[
        OHLCVBar(date=f"2024-01-0{i}", open=1, high=1, low=1, close=1, volume=1)
        for i in range(1, 6)
    ])
    result = run_technical_agent(security, tiny)
    assert result.overall_signal == "Insufficient Data"


# ---------------- Risk Agent ----------------

def test_risk_agent_full_metrics(security, price_history):
    result = run_risk_agent(security, price_history, period="2y",
                            benchmark_history=price_history, benchmark_name="TEST-IDX")
    rm = result.risk_metrics
    assert rm.annualized_volatility > 0
    assert rm.value_at_risk_95 is not None and rm.value_at_risk_99 is not None
    assert rm.conditional_var_95 <= rm.value_at_risk_95
    assert rm.beta == pytest.approx(1.0)  # benchmark == asset
    assert result.classification.level in {
        "Low Risk", "Moderate Risk", "High Risk", "Very High Risk"
    }
    assert "not a regulated" in result.classification.disclaimer.lower()


def test_risk_agent_reports_rate_assumption(security, price_history):
    result = run_risk_agent(security, price_history, benchmark_history=price_history)
    assert "RISK_FREE_RATE" in result.risk_free_rate_source


# ---------------- News Agent ----------------

def test_news_agent_separates_sentiment_provenance(security, manager_factory):
    result = run_news_agent(security, manager=manager_factory())
    assert result.articles_analyzed == 2
    for article in result.articles:
        assert article.computed_sentiment_label is not None   # our lexical pass
        assert article.provider_sentiment_label is not None    # provider's own
    assert result.sentiment.sentiment_basis in {"blended", "computed"}
    assert result.sentiment.total_articles == 2


def test_news_agent_handles_no_coverage(security, manager_factory):
    result = run_news_agent(security, manager=manager_factory(news=[]))
    assert result.articles_analyzed == 0
    assert "limited" in result.coverage_note.lower() or "no recent" in result.coverage_note.lower()


# ---------------- Reasoning Agent (deterministic path) ----------------

def test_reasoning_agent_flags_conflict_in_rule_mode(security, manager_factory, monkeypatch):
    monkeypatch.setattr("app.agents.reasoning_agent.get_llm_client", lambda: None)
    data = run_data_agent(security, period="2y", manager=manager_factory())
    tech = run_technical_agent(security, data.history)
    news = run_news_agent(security, manager=manager_factory())
    out = run_reasoning_agent(security, data=data, technical=tech, news=news)
    assert out.available is False
    assert out.classification in {"Bullish", "Neutral", "Bearish"}
