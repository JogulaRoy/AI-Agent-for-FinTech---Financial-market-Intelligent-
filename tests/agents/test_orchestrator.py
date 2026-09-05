"""Orchestrator wiring test with all providers + LLM stubbed (no network)."""

import pytest

from app.orchestrator import graph as graph_module
from app.reporting.markdown import report_to_markdown


@pytest.fixture
def stubbed_graph(monkeypatch, security, manager_factory, price_history):
    manager = manager_factory()
    monkeypatch.setattr(graph_module.nodes, "get_provider_manager", lambda: manager)
    monkeypatch.setattr(graph_module.nodes, "resolve_security", lambda q, m: security)
    # benchmark fetch -> reuse the synthetic history, no network
    monkeypatch.setattr(
        "app.agents.risk_agent.get_benchmark", lambda sec, period: ("TEST-IDX", price_history)
    )
    # LLM off -> reasoning agent uses its deterministic fallback
    monkeypatch.setattr("app.agents.reasoning_agent.get_llm_client", lambda: None)
    # fresh compiled graph so the monkeypatches take effect
    graph_module._compiled = None
    yield graph_module
    graph_module._compiled = None


def test_full_run_produces_complete_report(stubbed_graph):
    report = stubbed_graph.run_analysis("Testco", period="2y")

    assert report.security is not None
    assert report.data is not None and len(report.data.history) > 100
    assert report.technical is not None
    assert report.risk is not None
    assert report.news is not None
    assert report.overall_classification in {"Bullish", "Neutral", "Bearish"}

    names = {s.name for s in report.agent_status}
    assert {"Stock Resolver", "Data Agent", "Technical Agent", "Risk Agent",
            "News Agent", "Reasoning Agent"} <= names
    assert all(s.status in {"ok", "partial"} for s in report.agent_status)

    # sources recorded with provenance
    assert any(s.label == "Price history" for s in report.sources)

    # the 13-section markdown renders without error
    md = report_to_markdown(report)
    assert "## 1. Company Overview" in md
    assert "## 13. Data Sources / Freshness" in md


def test_stream_emits_progress_then_report(stubbed_graph):
    seen_nodes = []
    report = None
    for node, _statuses in stubbed_graph.stream_analysis("Testco", period="1y"):
        if node == "__report__":
            report = _statuses
        else:
            seen_nodes.append(node)
    assert "resolve" in seen_nodes and "data" in seen_nodes and "reason" in seen_nodes
    assert report is not None
    assert report.overall_classification is not None
