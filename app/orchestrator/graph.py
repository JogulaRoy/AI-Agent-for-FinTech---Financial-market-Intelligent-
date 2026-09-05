"""
LangGraph orchestration.

    START
      -> resolve
      -> data
      -> (technical | risk | news)   [parallel branches]
      -> reason
      -> END

If resolution fails the graph jumps straight to the end. If the Data Agent
fails, technical/risk still can't run but news + reasoning still produce a
(clearly degraded) report.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from langgraph.graph import END, START, StateGraph

from app.orchestrator import nodes
from app.orchestrator.state import FinancialAnalysisState
from app.schemas.intelligence import (
    FinancialIntelligenceReport,
    ReasoningOutput,
    SourceRecord,
)

_ANALYSIS_NODES = ["technical", "risk", "news"]


def _route_after_resolve(state: FinancialAnalysisState):
    return "data" if state.get("security") else "reason"


def _route_after_data(state: FinancialAnalysisState):
    if state.get("market_data") is not None:
        return _ANALYSIS_NODES
    # No price data: still try news + reasoning.
    return ["news"]


def build_graph():
    graph = StateGraph(FinancialAnalysisState)

    graph.add_node("resolve", nodes.resolve_node)
    graph.add_node("data", nodes.data_node)
    graph.add_node("technical", nodes.technical_node)
    graph.add_node("risk", nodes.risk_node)
    graph.add_node("news", nodes.news_node)
    graph.add_node("reason", nodes.reason_node)

    graph.add_edge(START, "resolve")
    graph.add_conditional_edges("resolve", _route_after_resolve, ["data", "reason"])
    graph.add_conditional_edges("data", _route_after_data, _ANALYSIS_NODES)
    for name in _ANALYSIS_NODES:
        graph.add_edge(name, "reason")
    graph.add_edge("reason", END)

    return graph.compile()


_compiled = None


def _get_compiled():
    global _compiled
    if _compiled is None:
        _compiled = build_graph()
    return _compiled


def run_analysis(
    user_query: str,
    period: str = "5y",
    news_hours: int = 168,
) -> FinancialIntelligenceReport:
    initial: FinancialAnalysisState = {
        "user_query": user_query,
        "period": period,
        "news_hours": news_hours,
        "errors": [],
        "agent_status": [],
        "sources": [],
    }
    final = _get_compiled().invoke(initial)
    return assemble_report(final)


def stream_analysis(
    user_query: str,
    period: str = "5y",
    news_hours: int = 168,
):
    """
    Generator that yields ``(node_name, agent_status_list)`` as each graph node
    finishes, then yields ``("__report__", FinancialIntelligenceReport)`` last.
    """
    initial: FinancialAnalysisState = {
        "user_query": user_query,
        "period": period,
        "news_hours": news_hours,
        "errors": [],
        "agent_status": [],
        "sources": [],
    }
    accumulated: FinancialAnalysisState = dict(initial)  # type: ignore[assignment]
    compiled = _get_compiled()

    for chunk in compiled.stream(initial, stream_mode="updates"):
        for node_name, update in chunk.items():
            if not isinstance(update, dict):
                continue
            for key, value in update.items():
                if key in ("errors", "agent_status", "sources"):
                    accumulated[key] = list(accumulated.get(key, [])) + list(value)
                else:
                    accumulated[key] = value
            yield node_name, update.get("agent_status", [])

    yield "__report__", assemble_report(accumulated)


def assemble_report(state: FinancialAnalysisState) -> FinancialIntelligenceReport:
    data = state.get("market_data")
    reasoning: Optional[ReasoningOutput] = state.get("financial_reasoning")

    # Backfill identity gaps on the canonical security from the richer profile
    # (search endpoints often omit country / sector / ISIN).
    security = state.get("security")
    if security is not None and data is not None and data.profile is not None:
        updates = {}
        if not security.country and data.profile.country:
            updates["country"] = data.profile.country
        if not security.isin and data.profile.isin:
            updates["isin"] = data.profile.isin
        if not security.currency and data.profile.currency:
            updates["currency"] = data.profile.currency
        if updates:
            security = security.model_copy(update=updates)

    sources: list[SourceRecord] = []
    if data:
        if data.history.provenance:
            sources.append(SourceRecord(
                label="Price history", provider=data.history.provenance.provider,
                as_of=data.history.provenance.as_of,
                note=data.history.provenance.note or "",
            ))
        if data.quote.provenance:
            sources.append(SourceRecord(
                label="Quote", provider=data.quote.provenance.provider,
                as_of=data.quote.provenance.as_of or "",
            ))
        if data.profile.provenance:
            sources.append(SourceRecord(
                label="Company profile", provider=data.profile.provenance.provider,
                as_of=data.profile.provenance.as_of or "",
            ))
        if data.fundamentals.available and data.fundamentals.provenance:
            sources.append(SourceRecord(
                label="Fundamentals", provider=data.fundamentals.provenance.provider,
                as_of=data.fundamentals.provenance.as_of or "",
            ))
    news = state.get("news_analysis")
    if news and news.provenance:
        sources.append(SourceRecord(
            label="News", provider=news.provenance.provider, as_of=news.provenance.as_of or "",
        ))

    return FinancialIntelligenceReport(
        generated_at=datetime.now(timezone.utc),
        user_query=state.get("user_query", ""),
        security=security,
        data=data,
        fundamentals=state.get("fundamentals"),
        technical=state.get("technical_analysis"),
        risk=state.get("risk_analysis"),
        news=news,
        reasoning=reasoning or ReasoningOutput(available=False),
        agent_status=state.get("agent_status", []),
        sources=sources,
        errors=state.get("errors", []),
        overall_classification=state.get("overall_classification"),
    )
