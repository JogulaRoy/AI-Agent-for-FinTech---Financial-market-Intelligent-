"""
Reasoning Agent (LLM layer).

Python has already done every calculation. This agent hands the structured
evidence to an LLM purely for synthesis, explanation, and conflict-spotting.
The LLM is instructed to use only the supplied evidence and to invent nothing.

A deterministic signal is computed here too, so the system still produces a
classification when the LLM is unavailable, and so we can flag disagreement.
"""

from __future__ import annotations

import json
from typing import Optional

from app.llm.base import LLMClient, LLMError
from app.llm.factory import get_llm_client
from app.schemas.fundamentals import Fundamentals
from app.schemas.intelligence import ReasoningOutput
from app.schemas.market_data import DataAgentResult
from app.schemas.news_data import NewsAnalysis
from app.schemas.risk_data import RiskAnalysis
from app.schemas.security import CanonicalSecurity
from app.schemas.technical_data import TechnicalAnalysis

_SYSTEM = """You are a financial-analysis reasoning assistant inside a multi-agent system.

You DO NOT calculate anything. Python has already computed every number (RSI, MACD,
VaR, volatility, ratios, returns). Your job is synthesis and explanation.

Rules:
- Use ONLY the evidence in the user message. Never invent numbers, prices, news,
  events, or dates.
- Clearly separate fact (a computed metric) from interpretation (what it may imply).
- Explicitly name conflicting signals between agents.
- Mention data limitations and freshness when they matter.
- No guaranteed predictions. No "buy/sell/hold" advice. No claims of certainty
  about future prices. Frame everything as analysis / intelligence, not advice.
- Be concise and specific. Reference the actual metric values.

Return ONLY a JSON object with these keys:
{
  "company_overview": string,
  "cross_agent_insights": string,
  "conflicting_signals": string,
  "overall_intelligence": string,
  "key_risks": [string, ...],
  "classification": "Bullish" | "Neutral" | "Bearish",
  "classification_rationale": string,
  "uncertainty_notes": string
}
"""


def _num(x, digits: int = 4):
    return round(x, digits) if isinstance(x, (int, float)) else x


def build_evidence(
    security: CanonicalSecurity,
    data: Optional[DataAgentResult],
    technical: Optional[TechnicalAnalysis],
    risk: Optional[RiskAnalysis],
    news: Optional[NewsAnalysis],
) -> dict:
    evidence: dict = {
        "security": {
            "company_name": security.company_name,
            "symbol": security.symbol,
            "exchange": security.exchange,
            "country": security.country,
            "currency": security.currency,
            "isin": security.isin,
            "resolution_confidence": security.confidence,
        }
    }

    if data:
        f: Fundamentals = data.fundamentals
        evidence["market"] = {
            "price": _num(data.quote.price, 2),
            "currency": data.quote.currency,
            "change_percent": _num(data.quote.change_percent),
            "week52_high": _num(data.quote.week52_high, 2),
            "week52_low": _num(data.quote.week52_low, 2),
            "as_of": data.quote.timestamp,
            "data_sources": data.sources_used,
        }
        evidence["performance"] = data.performance.model_dump()
        evidence["price_stability"] = data.stability.model_dump()
        evidence["fundamentals_available"] = f.available
        evidence["financial_health"] = {
            "classification": f.health.classification,
            "score": f.health.score,
            "reasons": f.health.reasons,
        }
        evidence["valuation"] = f.valuation.model_dump(exclude={"provenance"})
        if f.income_statement:
            evidence["income_statement_recent"] = [
                line.model_dump() for line in f.income_statement[:3]
            ]
        evidence["data_quality"] = {
            "rows": data.data_quality.rows_returned,
            "removed": data.data_quality.rows_removed,
            "range": [data.data_quality.start_date, data.data_quality.end_date],
            "warnings": data.warnings,
        }

    if technical:
        evidence["technical"] = technical.as_summary() | {
            "moving_averages": technical.moving_averages.model_dump(),
            "rsi_interpretation": technical.rsi.interpretation,
            "bollinger_percent_b": technical.bollinger_bands.percent_b,
            "atr_percent_of_price": technical.atr.percent_of_price,
            "trend": technical.trend.model_dump(),
            "volume": technical.volume.model_dump(),
            "signal_reasons": technical.signal_reasons,
            "bars_analyzed": technical.bars_analyzed,
        }

    if risk:
        evidence["risk"] = {
            "metrics": risk.risk_metrics.model_dump(),
            "level": risk.classification.level,
            "score_0_100": risk.classification.score,
            "risk_free_rate": risk.risk_free_rate,
            "key_risks": risk.key_risks,
        }

    if news:
        evidence["news"] = {
            "articles_analyzed": news.articles_analyzed,
            "window_hours": news.analysis_window_hours,
            "overall_sentiment": news.sentiment.overall_sentiment,
            "sentiment_basis": news.sentiment.sentiment_basis,
            "counts": {
                "positive": news.sentiment.positive_count,
                "negative": news.sentiment.negative_count,
                "neutral": news.sentiment.neutral_count,
            },
            "themes": news.themes,
            "coverage_note": news.coverage_note,
            "headlines": [a.title for a in news.articles[:8]],
        }

    return evidence


def deterministic_classification(
    data: Optional[DataAgentResult],
    technical: Optional[TechnicalAnalysis],
    risk: Optional[RiskAnalysis],
    news: Optional[NewsAnalysis],
) -> tuple[str, list[str]]:
    score = 0
    notes: list[str] = []

    if technical and technical.overall_signal in {"Bullish", "Bearish"}:
        delta = 1 if technical.overall_signal == "Bullish" else -1
        score += delta
        notes.append(f"Technical signal: {technical.overall_signal}")

    if data and data.fundamentals.available:
        hc = data.fundamentals.health.classification
        if hc == "Strong":
            score += 1
            notes.append("Financial health: Strong")
        elif hc == "Weak":
            score -= 1
            notes.append("Financial health: Weak")

    if data and data.performance.one_year_return is not None:
        r = data.performance.one_year_return
        if r > 0.10:
            score += 1
            notes.append(f"1-year return {r:+.1%}")
        elif r < -0.10:
            score -= 1
            notes.append(f"1-year return {r:+.1%}")

    if news and news.sentiment.overall_sentiment in {"Positive", "Negative"}:
        delta = 1 if news.sentiment.overall_sentiment == "Positive" else -1
        score += delta
        notes.append(f"News sentiment: {news.sentiment.overall_sentiment}")

    if risk and risk.classification.level in {"High Risk", "Very High Risk"}:
        notes.append(f"{risk.classification.level} — treat any directional read with caution")

    label = "Bullish" if score >= 2 else "Bearish" if score <= -2 else "Neutral"
    return label, notes


def run_reasoning_agent(
    security: CanonicalSecurity,
    data: Optional[DataAgentResult] = None,
    technical: Optional[TechnicalAnalysis] = None,
    risk: Optional[RiskAnalysis] = None,
    news: Optional[NewsAnalysis] = None,
    client: Optional[LLMClient] = None,
) -> ReasoningOutput:
    det_label, det_notes = deterministic_classification(data, technical, risk, news)
    evidence = build_evidence(security, data, technical, risk, news)

    if client is None:
        client = get_llm_client()

    if client is None or not client.available:
        return ReasoningOutput(
            available=False,
            classification=det_label,
            classification_rationale=(
                "Rule-based signal (LLM reasoning layer not configured). Basis: "
                + "; ".join(det_notes)
            ),
            error="LLM_API_KEY not configured.",
            overall_intelligence=(
                "The AI reasoning layer is not available. The system-generated "
                f"classification is '{det_label}' based on: " + "; ".join(det_notes) + "."
            ),
            key_risks=(risk.key_risks[:5] if risk else []),
        )

    user = (
        "EVIDENCE (all values pre-computed by the system):\n"
        + json.dumps(evidence, indent=2, default=str)
        + f"\n\nThe system's rule-based classification is '{det_label}' "
        + f"(basis: {'; '.join(det_notes)}). Weigh the full evidence yourself; "
        + "if you disagree, say so in conflicting_signals."
    )

    try:
        raw = client.generate_json(_SYSTEM, user, temperature=0.2, max_output_tokens=4096)
    except LLMError as exc:
        return ReasoningOutput(
            available=False,
            model=getattr(client, "model", None),
            classification=det_label,
            classification_rationale="Rule-based signal; LLM call failed.",
            error=str(exc),
            overall_intelligence=(
                f"AI reasoning unavailable ({exc}). System classification: {det_label}."
            ),
            key_risks=(risk.key_risks[:5] if risk else []),
        )

    key_risks = raw.get("key_risks") or []
    if isinstance(key_risks, str):
        key_risks = [key_risks]

    classification = str(raw.get("classification") or det_label).title()
    if classification not in {"Bullish", "Neutral", "Bearish"}:
        classification = det_label

    return ReasoningOutput(
        available=True,
        model=getattr(client, "model", None),
        company_overview=str(raw.get("company_overview", "")),
        cross_agent_insights=str(raw.get("cross_agent_insights", "")),
        conflicting_signals=str(raw.get("conflicting_signals", "")),
        overall_intelligence=str(raw.get("overall_intelligence", "")),
        key_risks=[str(k) for k in key_risks][:8],
        classification=classification,
        classification_rationale=str(raw.get("classification_rationale", "")),
        uncertainty_notes=str(raw.get("uncertainty_notes", "")),
    )
