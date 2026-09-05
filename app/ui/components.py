"""HTML fragment builders for the dashboard (used with st.markdown(..., unsafe_allow_html=True))."""

from __future__ import annotations

import html
from typing import Optional

from app.schemas.intelligence import FinancialIntelligenceReport

_BADGE_CLASS = {"bullish": "bullish", "bearish": "bearish"}


def badge(label: Optional[str]) -> str:
    key = (label or "neutral").lower()
    cls = _BADGE_CLASS.get(key, "neutral")
    return f'<span class="fi-badge {cls}">{html.escape(label or "—")}</span>'


def pill(verdict: Optional[str]) -> str:
    v = (verdict or "unknown").lower()
    v = v if v in {"strong", "moderate", "weak", "unknown"} else "unknown"
    return f'<span class="fi-pill {v}">{html.escape((verdict or "unknown").title())}</span>'


def hero(report: FinancialIntelligenceReport, currency: Optional[str]) -> str:
    sec = report.security
    name = sec.company_name if sec else report.user_query
    chips = ""
    if sec:
        items = [
            sec.symbol,
            sec.exchange,
            sec.country,
            currency,
            f"ISIN {sec.isin}" if sec.isin else None,
            f"resolved via {sec.resolved_by}" if sec.resolved_by else None,
            f"match {sec.confidence:.0%}",
        ]
        chips = "".join(
            f'<span class="fi-chip">{html.escape(str(x))}</span>' for x in items if x
        )
    gen = report.generated_at.strftime("%Y-%m-%d %H:%M UTC")
    return f"""
<div class="fi-hero">
  <div class="fi-hero-top">
    <div>
      <h1>{html.escape(name)}</h1>
      <div class="sub">Query: &ldquo;{html.escape(report.user_query)}&rdquo; &middot; generated {gen}</div>
    </div>
    <div>{badge(report.overall_classification)}</div>
  </div>
  <div class="fi-chips">{chips}</div>
</div>
"""


def _num(value, digits: int = 2) -> str:
    return "—" if value is None else f"{value:,.{digits}f}"


def _pct(value, digits: int = 1) -> str:
    return "—" if value is None else f"{value * 100:+.{digits}f}%"


def signal_strip(report: FinancialIntelligenceReport) -> str:
    data = report.data
    tech = report.technical
    risk = report.risk
    news = report.news

    cards: list[str] = []

    # Fundamentals
    if data and data.fundamentals and data.fundamentals.available:
        h = data.fundamentals.health
        cls = {"Strong": "sig-pos", "Moderate": "sig-warn", "Weak": "sig-neg"}.get(
            h.classification, "sig-mut"
        )
        detail = f"score {_num(h.score, 0)} / 100" if h.score is not None else "metric-backed"
        cards.append(("Fundamental health", h.classification, detail, cls))
    else:
        cards.append(("Fundamental health", "N/A", "not on free tier", "sig-mut"))

    # Technical
    if tech and tech.current_price is not None:
        cls = {"Bullish": "sig-pos", "Bearish": "sig-neg"}.get(tech.overall_signal, "sig-warn")
        detail = f"RSI {_num(tech.rsi.value, 0)} · {tech.trend.price_position}"
        cards.append(("Technical signal", tech.overall_signal, detail, cls))
    else:
        cards.append(("Technical signal", "N/A", "insufficient history", "sig-mut"))

    # Risk
    if risk and risk.classification.level != "Insufficient Data":
        lvl = risk.classification.level
        cls = "sig-neg" if "High" in lvl else "sig-warn" if "Moderate" in lvl else "sig-pos"
        detail = f"score {_num(risk.classification.score, 0)} / 100 · vol {_pct(risk.risk_metrics.annualized_volatility)}"
        cards.append(("Risk level", lvl, detail, cls))
    else:
        cards.append(("Risk level", "N/A", "insufficient returns", "sig-mut"))

    # Sentiment
    if news and news.articles_analyzed:
        s = news.sentiment
        cls = {"Positive": "sig-pos", "Negative": "sig-neg"}.get(s.overall_sentiment, "sig-warn")
        detail = f"{news.articles_analyzed} articles · +{s.positive_count}/-{s.negative_count}"
        cards.append(("News sentiment", s.overall_sentiment, detail, cls))
    else:
        cards.append(("News sentiment", "No news", "limited coverage", "sig-mut"))

    inner = "".join(
        f'<div class="fi-signal {cls}"><div class="k">{html.escape(k)}</div>'
        f'<div class="v">{html.escape(str(v))}</div>'
        f'<div class="d">{html.escape(d)}</div></div>'
        for k, v, d, cls in cards
    )
    return f'<div class="fi-strip">{inner}</div>'


def landing() -> str:
    features = [
        ("Dynamic security resolution",
         "Type “TCS” or “Tata Consultancy Services”. No provider ticker formats — "
         "resolved from search APIs + the NSE master with source corroboration."),
        ("Provider abstraction",
         "FMP, Twelve Data and EODHD behind one interface with primary/fallback, "
         "caching, validation and per-value provenance. yfinance is a labelled fallback."),
        ("Specialised agents",
         "Data, Technical (Wilder RSI/ATR/MACD), Risk (VaR/CVaR/Sharpe/Sortino/beta) "
         "and News agents, each returning structured evidence."),
        ("LangGraph orchestration",
         "One shared state; Technical, Risk and News run in parallel after the Data "
         "Agent, with conditional skips and error aggregation."),
        ("LLM reasoning layer",
         "The LLM never computes numbers — it synthesises the agents' evidence, "
         "flags conflicting signals and explains the classification."),
        ("Explainable & exportable",
         "13-section report, transparent health/risk scores, downloadable as "
         "Markdown or JSON, with a persisted analysis history."),
    ]
    cards = "".join(
        f'<div class="fi-feature"><h4>{html.escape(t)}</h4><p>{html.escape(d)}</p></div>'
        for t, d in features
    )
    return f"""
<div class="fi-hero">
  <div class="fi-hero-top"><div>
    <h1>Agentic AI System for Financial Market Intelligence</h1>
    <div class="sub">Enter a company in the sidebar to run the multi-agent pipeline.</div>
  </div></div>
  <div class="fi-flow">
    User &rarr; Streamlit &rarr; Orchestrator &rarr; Resolver &rarr; Data Agent
    &rarr; (Technical &#124; Risk &#124; News) &rarr; LLM Reasoning &rarr; Financial Intelligence
  </div>
</div>
<div class="fi-features">{cards}</div>
"""
