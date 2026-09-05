"""LangGraph node functions. Each wraps one agent and updates shared state."""

from __future__ import annotations

import time

from app.agents.data_agent import run_data_agent
from app.agents.news_agent import run_news_agent
from app.agents.reasoning_agent import run_reasoning_agent
from app.agents.risk_agent import run_risk_agent
from app.agents.technical_agent import run_technical_agent
from app.data.provider_manager import get_provider_manager
from app.data.resolver import resolve_security
from app.orchestrator.state import FinancialAnalysisState
from app.schemas.intelligence import AgentRunStatus


def _status(name: str, status: str, message: str, started: float) -> AgentRunStatus:
    return AgentRunStatus(
        name=name, status=status, message=message,
        duration_ms=int((time.perf_counter() - started) * 1000),
    )


# ============================================================
# RESOLVE
# ============================================================


def resolve_node(state: FinancialAnalysisState) -> dict:
    started = time.perf_counter()
    query = state["user_query"]
    try:
        security = resolve_security(query, get_provider_manager())
    except Exception as exc:  # noqa: BLE001
        return {
            "security": None,
            "errors": [f"Stock resolution failed: {exc}"],
            "agent_status": [_status("Stock Resolver", "failed", str(exc), started)],
        }
    msg = f"{security.company_name} ({security.symbol}) on {security.exchange or 'n/a'}"
    if security.confidence < 0.6:
        msg += f" — low confidence ({security.confidence:.0%})"
    return {
        "security": security,
        "agent_status": [_status("Stock Resolver", "ok", msg, started)],
        "sources": [f"resolver:{security.resolved_by}"],
    }


# ============================================================
# DATA
# ============================================================


def data_node(state: FinancialAnalysisState) -> dict:
    started = time.perf_counter()
    security = state.get("security")
    if security is None:
        return {"agent_status": [_status("Data Agent", "skipped", "no security", started)]}
    try:
        result = run_data_agent(
            security, period=state.get("period", "5y"), manager=get_provider_manager()
        )
    except Exception as exc:  # noqa: BLE001
        return {
            "market_data": None,
            "errors": [f"Data Agent failed: {exc}"],
            "agent_status": [_status("Data Agent", "failed", str(exc), started)],
        }
    status = "ok"
    if not result.fundamentals.available:
        status = "partial"
    return {
        "market_data": result,
        "fundamentals": result.fundamentals,
        "agent_status": [_status(
            "Data Agent", status,
            f"{len(result.history)} bars via {', '.join(result.sources_used)}", started,
        )],
        "sources": [f"data:{s}" for s in result.sources_used],
    }


# ============================================================
# TECHNICAL / RISK / NEWS  (parallel)
# ============================================================


def technical_node(state: FinancialAnalysisState) -> dict:
    started = time.perf_counter()
    security, data = state.get("security"), state.get("market_data")
    if not security or not data:
        return {"agent_status": [_status("Technical Agent", "skipped", "no market data", started)]}
    try:
        result = run_technical_agent(security, data.history, period=state.get("period", ""))
    except Exception as exc:  # noqa: BLE001
        return {
            "errors": [f"Technical Agent failed: {exc}"],
            "agent_status": [_status("Technical Agent", "failed", str(exc), started)],
        }
    return {
        "technical_analysis": result,
        "agent_status": [_status("Technical Agent", "ok", f"signal: {result.overall_signal}", started)],
    }


def risk_node(state: FinancialAnalysisState) -> dict:
    started = time.perf_counter()
    security, data = state.get("security"), state.get("market_data")
    if not security or not data:
        return {"agent_status": [_status("Risk Agent", "skipped", "no market data", started)]}
    try:
        result = run_risk_agent(security, data.history, period=state.get("period", ""))
    except Exception as exc:  # noqa: BLE001
        return {
            "errors": [f"Risk Agent failed: {exc}"],
            "agent_status": [_status("Risk Agent", "failed", str(exc), started)],
        }
    return {
        "risk_analysis": result,
        "agent_status": [_status("Risk Agent", "ok", result.classification.level, started)],
    }


def news_node(state: FinancialAnalysisState) -> dict:
    started = time.perf_counter()
    security = state.get("security")
    if not security:
        return {"agent_status": [_status("News Agent", "skipped", "no security", started)]}
    try:
        result = run_news_agent(
            security, hours=state.get("news_hours", 168), manager=get_provider_manager()
        )
    except Exception as exc:  # noqa: BLE001
        return {
            "errors": [f"News Agent failed: {exc}"],
            "agent_status": [_status("News Agent", "failed", str(exc), started)],
        }
    status = "ok" if result.articles_analyzed else "partial"
    return {
        "news_analysis": result,
        "agent_status": [_status(
            "News Agent", status,
            f"{result.articles_analyzed} articles, {result.sentiment.overall_sentiment}", started,
        )],
    }


# ============================================================
# REASONING
# ============================================================


def reason_node(state: FinancialAnalysisState) -> dict:
    started = time.perf_counter()
    security = state.get("security")
    if security is None:
        return {"agent_status": [_status("Reasoning Agent", "skipped", "no security", started)]}
    reasoning = run_reasoning_agent(
        security,
        data=state.get("market_data"),
        technical=state.get("technical_analysis"),
        risk=state.get("risk_analysis"),
        news=state.get("news_analysis"),
    )
    status = "ok" if reasoning.available else "partial"
    return {
        "financial_reasoning": reasoning,
        "overall_classification": reasoning.classification,
        "agent_status": [_status(
            "Reasoning Agent", status,
            f"classification: {reasoning.classification}"
            + ("" if reasoning.available else " (rule-based; LLM unavailable)"),
            started,
        )],
    }
