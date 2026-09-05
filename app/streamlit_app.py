"""
Agentic AI System for Financial Market Intelligence — Streamlit dashboard.

Run with:  streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import html
import sys
from pathlib import Path

# Allow `streamlit run app/streamlit_app.py` from anywhere: put the project
# root (the parent of this file's `app/` folder) on the import path.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd
import streamlit as st

from app.config.settings import settings
from app.data import store
from app.orchestrator.graph import stream_analysis
from app.reporting.markdown import report_to_markdown
from app.schemas.intelligence import FinancialIntelligenceReport
from app.ui.charts import health_gauge, price_chart, returns_bar, rsi_macd_chart
from app.ui.components import badge, hero, landing, pill, signal_strip
from app.ui.styles import CSS

st.set_page_config(
    page_title="Financial Market Intelligence",
    page_icon="📊",
    layout="wide",
)
st.markdown(CSS, unsafe_allow_html=True)

_PERIODS = {
    "1 year": "1y", "2 years": "2y", "5 years": "5y", "10 years": "10y", "Max": "max",
}
_CCY = {"USD": "$", "INR": "₹", "EUR": "€", "GBP": "£", "JPY": "¥"}


def _sym(currency: str | None) -> str:
    return _CCY.get((currency or "").upper(), f"{currency} " if currency else "")


def money(value, currency: str | None) -> str:
    if value is None:
        return "—"
    return f"{_sym(currency)}{value:,.2f}"


def pct(value, digits: int = 2) -> str:
    return "—" if value is None else f"{value * 100:+.{digits}f}%"


def num(value, digits: int = 2) -> str:
    return "—" if value is None else f"{value:,.{digits}f}"


def big_num(value) -> str:
    if value is None:
        return "—"
    for unit, scale in (("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(value) >= scale:
            return f"{value / scale:,.2f}{unit}"
    return f"{value:,.0f}"


def section(title: str) -> None:
    st.markdown(f'<div class="fi-section-title">{html.escape(title)}</div>', unsafe_allow_html=True)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown("### 📊 Market Intelligence")
st.sidebar.caption("Agentic AI · multi-agent · LangGraph")

query = st.sidebar.text_input(
    "Company name or ticker", value="", placeholder="e.g. TCS, Apple, Reliance"
)
period_label = st.sidebar.selectbox("History window", list(_PERIODS), index=2)
news_days = st.sidebar.slider("News look-back (days)", 3, 30, 7)
run = st.sidebar.button("Run analysis", type="primary", width="stretch")

with st.sidebar.expander("System status", expanded=False):
    missing = settings.missing_keys()
    st.write("**Providers:** " + ", ".join(settings.configured_providers()))
    st.write(
        "**LLM:** " + (f"{settings.llm_provider} ({settings.llm_model})"
                       if settings.has_llm() else "not configured")
    )
    if missing:
        st.warning("Missing in .env: " + ", ".join(missing))

# --- recent analyses (persisted, instant reload) ---
try:
    recent = store.list_runs(limit=12)
except Exception:  # noqa: BLE001
    recent = []
if recent:
    st.sidebar.markdown("---")
    hcol1, hcol2 = st.sidebar.columns([3, 1])
    hcol1.caption("RECENT ANALYSES")
    if hcol2.button("🗑", key="clear_hist", help="Clear saved history"):
        store.clear_runs()
        st.session_state.pop("report", None)
        st.rerun()
    for summary in recent:
        if st.sidebar.button(summary.label, key=f"recent_{summary.id}", width="stretch"):
            loaded = store.load_run(summary.id)
            if loaded is not None:
                st.session_state["report"] = loaded
                st.session_state["from_history"] = True

st.sidebar.markdown(
    '<div class="fi-disclaimer">Financial intelligence for educational use. '
    "Not investment advice. No guaranteed predictions.</div>",
    unsafe_allow_html=True,
)


# ============================================================
# RUN THE PIPELINE
# ============================================================

if run and query.strip():
    st.session_state.pop("report", None)
    st.session_state.pop("from_history", None)
    progress = st.status("Coordinating financial agents…", expanded=True)
    report: FinancialIntelligenceReport | None = None
    try:
        for node, statuses in stream_analysis(
            query.strip(), period=_PERIODS[period_label], news_hours=news_days * 24
        ):
            if node == "__report__":
                report = statuses  # type: ignore[assignment]
                break
            for s in statuses:
                icon = {"ok": "✅", "partial": "🟡", "failed": "❌", "skipped": "⏭️"}.get(s.status, "•")
                progress.write(f"{icon} **{s.name}** — {s.message}")
        progress.update(label="Analysis complete", state="complete", expanded=False)
    except Exception as exc:  # noqa: BLE001
        progress.update(label="Analysis failed", state="error")
        st.error(f"Something went wrong: {exc}")
    if report is not None:
        st.session_state["report"] = report
        try:
            store.save_run(report)
        except Exception:  # noqa: BLE001
            pass

report = st.session_state.get("report")

if report is None:
    st.markdown(landing(), unsafe_allow_html=True)
    st.stop()


# ============================================================
# RENDER REPORT
# ============================================================

r: FinancialIntelligenceReport = report
sec = r.security
data = r.data
tech = r.technical
risk = r.risk
news = r.news
reasoning = r.reasoning
currency = (data.quote.currency if data else None) or (sec.currency if sec else None)

st.markdown(hero(r, currency), unsafe_allow_html=True)
st.markdown(signal_strip(r), unsafe_allow_html=True)

if sec and sec.confidence < 0.6 and sec.alternatives:
    st.info(
        "Low-confidence match. Did you mean: "
        + " · ".join(f"**{a.company_name}** ({a.symbol})" for a in sec.alternatives[:3])
    )
if st.session_state.get("from_history"):
    st.caption("📁 Loaded from saved analysis history — no API calls made.")
for err in r.errors:
    st.warning(err)

_slug = (sec.symbol if sec else "report").lower()
dl1, dl2, _ = st.columns([1, 1, 4])
dl1.download_button(
    "⬇ Markdown report", report_to_markdown(r), file_name=f"{_slug}_intelligence.md",
    mime="text/markdown", width="stretch",
)
dl2.download_button(
    "⬇ JSON", r.model_dump_json(indent=2), file_name=f"{_slug}_intelligence.json",
    mime="application/json", width="stretch",
)

tabs = st.tabs([
    "📋 Overview", "📈 Market", "🏦 Fundamentals", "🧭 Technical", "⚠️ Risk",
    "📰 News", "🤖 AI Intelligence", "📄 Full report", "🔗 Sources",
])

# ---------------- Overview ----------------
with tabs[0]:
    if data:
        q = data.quote
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Price", money(q.price, currency), pct(q.change_percent))
        c2.metric("52-week range",
                  f"{money(q.week52_low, currency)} – {money(q.week52_high, currency)}"
                  if q.week52_high else "—")
        c3.metric("Market cap", big_num(data.profile.market_cap))
        c4.metric("1-year return", pct(data.performance.one_year_return))

    section("System classification")
    col_a, col_b = st.columns([1, 3])
    with col_a:
        st.markdown(badge(r.overall_classification), unsafe_allow_html=True)
        st.caption("Bullish / Neutral / Bearish — a system-generated analytical "
                   "signal, not a buy/sell recommendation.")
    with col_b:
        st.write(reasoning.overall_intelligence
                 or reasoning.classification_rationale
                 or "Run an analysis to see the AI synthesis.")

    if data and data.profile.description:
        with st.expander("About the company"):
            st.write(data.profile.description)
        meta = data.profile
        st.caption(
            f"Sector: {meta.sector or '—'} · Industry: {meta.industry or '—'} · "
            f"Website: {meta.website or '—'}"
        )
    st.markdown(f'<div class="fi-disclaimer">{r.disclaimer}</div>', unsafe_allow_html=True)

# ---------------- Market ----------------
with tabs[1]:
    if not data:
        st.info("No market data available.")
    else:
        q = data.quote
        cols = st.columns(6)
        for col, (label, value) in zip(cols, [
            ("Open", money(q.open, currency)), ("High", money(q.high, currency)),
            ("Low", money(q.low, currency)), ("Prev close", money(q.previous_close, currency)),
            ("Volume", big_num(q.volume)), ("Change", pct(q.change_percent)),
        ]):
            col.metric(label, value)
        st.caption(
            f"Quote: **{q.provenance.provider if q.provenance else '—'}** (as of {q.timestamp or '—'}) · "
            f"history: **{data.history.provenance.provider if data.history.provenance else '—'}** "
            f"{data.history.start_date} → {data.history.end_date} · {len(data.history)} bars"
        )
        st.plotly_chart(price_chart(data.history, tech), width="stretch")

        section("Historical performance & stability")
        p1, p2 = st.columns([1, 1])
        with p1:
            st.plotly_chart(returns_bar(data.performance), width="stretch")
        with p2:
            s = data.stability
            st.dataframe(pd.DataFrame({
                "Metric": ["Annualized volatility", "Downside volatility", "Max drawdown",
                           "Positive days", "Best day", "Worst day", "Stability"],
                "Value": [pct(s.annualized_volatility), pct(s.downside_volatility),
                          pct(s.maximum_drawdown), pct(s.positive_days_ratio),
                          pct(s.best_day), pct(s.worst_day), s.classification],
            }), hide_index=True, width="stretch")

# ---------------- Fundamentals ----------------
with tabs[2]:
    if not data:
        st.info("No fundamental data available.")
    else:
        f = data.fundamentals
        left, right = st.columns([1, 1.35])
        with left:
            st.plotly_chart(health_gauge(f.health.score, f.health.classification), width="stretch")
            st.markdown(f'<div class="fi-note">{f.health.disclaimer}</div>', unsafe_allow_html=True)
        with right:
            section("What drives the score")
            for x in f.health.factors:
                st.markdown(
                    f'{pill(x.verdict)} &nbsp;**{html.escape(x.name)}** — '
                    f'<span class="fi-note">{html.escape(x.detail)}</span>',
                    unsafe_allow_html=True,
                )
        if not f.available:
            st.warning(f.unavailable_reason
                       or "Full statements unavailable on the current data plan.")

        v = f.valuation
        section("Valuation & quality metrics")
        for row in ([
            ("P/E", num(v.pe_ratio)), ("P/B", num(v.pb_ratio)), ("P/S", num(v.ps_ratio)),
            ("EV/EBITDA", num(v.ev_to_ebitda)), ("ROE", pct(v.roe)), ("ROA", pct(v.roa)),
        ], [
            ("Debt/Equity", num(v.debt_to_equity)), ("Current ratio", num(v.current_ratio)),
            ("Net margin", pct(v.profit_margin)), ("Op margin", pct(v.operating_margin)),
            ("Rev growth", pct(v.revenue_growth)), ("Div yield", pct(v.dividend_yield)),
        ]):
            cols = st.columns(6)
            for col, (label, value) in zip(cols, row):
                col.metric(label, value)

        if f.income_statement:
            section("Income statement")
            st.dataframe(pd.DataFrame([
                {"Period": x.period, "Revenue": big_num(x.revenue), "Gross profit": big_num(x.gross_profit),
                 "Operating income": big_num(x.operating_income), "Net income": big_num(x.net_income),
                 "EPS": num(x.eps), "Net margin": pct(x.net_margin)}
                for x in f.income_statement
            ]), hide_index=True, width="stretch")
        if f.balance_sheet:
            section("Balance sheet")
            st.dataframe(pd.DataFrame([
                {"Period": x.period, "Total assets": big_num(x.total_assets),
                 "Total liabilities": big_num(x.total_liabilities), "Equity": big_num(x.total_equity),
                 "Cash": big_num(x.cash_and_equivalents), "Debt": big_num(x.total_debt)}
                for x in f.balance_sheet
            ]), hide_index=True, width="stretch")
        if f.cash_flow:
            section("Cash flow")
            st.dataframe(pd.DataFrame([
                {"Period": x.period, "Operating CF": big_num(x.operating_cash_flow),
                 "Investing CF": big_num(x.investing_cash_flow), "Financing CF": big_num(x.financing_cash_flow),
                 "CapEx": big_num(x.capital_expenditure), "Free cash flow": big_num(x.free_cash_flow)}
                for x in f.cash_flow
            ]), hide_index=True, width="stretch")

# ---------------- Technical ----------------
with tabs[3]:
    if not tech or tech.current_price is None:
        st.info("Technical analysis unavailable (insufficient price history).")
    else:
        m = tech.moving_averages
        st.markdown(f"**Overall signal** &nbsp; {badge(tech.overall_signal)}", unsafe_allow_html=True)
        for reason in tech.signal_reasons:
            st.markdown(f"- {reason}")
        section("Indicators")
        cols = st.columns(5)
        for col, (label, value) in zip(cols, [
            ("SMA 20", money(m.sma_20, currency)), ("SMA 50", money(m.sma_50, currency)),
            ("SMA 200", money(m.sma_200, currency)), ("EMA 20", money(m.ema_20, currency)),
            ("EMA 50", money(m.ema_50, currency)),
        ]):
            col.metric(label, value)
        cols2 = st.columns(5)
        cols2[0].metric("RSI (14, Wilder)", num(tech.rsi.value), tech.rsi.interpretation)
        cols2[1].metric("MACD", num(tech.macd.macd, 3), tech.macd.interpretation)
        cols2[2].metric("Bollinger %B", num(tech.bollinger_bands.percent_b, 2),
                        tech.bollinger_bands.interpretation)
        cols2[3].metric("ATR %", pct(tech.atr.percent_of_price))
        cols2[4].metric("Momentum", tech.momentum)
        st.caption(
            f"Support ≈ {money(tech.support_resistance.support, currency)} · "
            f"Resistance ≈ {money(tech.support_resistance.resistance, currency)} · "
            f"{tech.support_resistance.position}. {tech.support_resistance.methodology}"
        )
        st.plotly_chart(rsi_macd_chart(data.history), width="stretch")
        st.markdown(f'<div class="fi-note">{tech.disclaimer}</div>', unsafe_allow_html=True)

# ---------------- Risk ----------------
with tabs[4]:
    if not risk or risk.classification.level == "Insufficient Data":
        st.info("Risk analysis unavailable (insufficient return history).")
    else:
        rm = risk.risk_metrics
        st.markdown(f"**Risk level:** {risk.classification.level} — {risk.classification.explanation}")
        for label_row in ([
            ("Annualized volatility", pct(rm.annualized_volatility)),
            ("Downside volatility", pct(rm.downside_volatility)),
            ("Max drawdown", pct(rm.maximum_drawdown)),
            ("Project risk score", f"{num(risk.classification.score, 0)} / 100"),
        ], [
            ("VaR 95% (1d)", pct(rm.value_at_risk_95)), ("VaR 99% (1d)", pct(rm.value_at_risk_99)),
            ("CVaR 95%", pct(rm.conditional_var_95)), ("CVaR 99%", pct(rm.conditional_var_99)),
        ], [
            ("Sharpe ratio", num(rm.sharpe_ratio)), ("Sortino ratio", num(rm.sortino_ratio)),
            (f"Beta ({rm.benchmark or 'n/a'})", num(rm.beta)),
            ("Risk-free rate", pct(risk.risk_free_rate)),
        ]):
            cols = st.columns(4)
            for col, (label, value) in zip(cols, label_row):
                col.metric(label, value)
        st.caption(risk.risk_free_rate_source)
        if risk.key_risks:
            section("Key historical risks")
            for k in risk.key_risks:
                st.markdown(f"- {k}")
        st.markdown(f'<div class="fi-note">{risk.classification.disclaimer}</div>', unsafe_allow_html=True)

# ---------------- News ----------------
with tabs[5]:
    if not news or not news.articles:
        st.info(news.coverage_note if news and news.coverage_note else "No recent news found.")
    else:
        s = news.sentiment
        cols = st.columns(4)
        cols[0].metric("Overall", s.overall_sentiment)
        cols[1].metric("Positive", s.positive_count)
        cols[2].metric("Negative", s.negative_count)
        cols[3].metric("Neutral", s.neutral_count)
        st.caption(
            f"{news.articles_analyzed} articles · sentiment basis: **{s.sentiment_basis}** · "
            f"source: **{news.provenance.provider if news.provenance else '—'}**. "
            + (news.provenance.note if news.provenance else "")
        )
        if news.themes:
            st.markdown("**Themes:** " + " · ".join(f"`{t}`" for t in news.themes))
        section("Recent articles")
        for a in news.articles[:15]:
            tags = []
            if a.provider_sentiment_label:
                tags.append(f"provider: {a.provider_sentiment_label}")
            if a.computed_sentiment_label:
                tags.append(f"computed: {a.computed_sentiment_label}")
            st.markdown(
                f'<div class="fi-news"><a href="{html.escape(a.url)}" target="_blank">'
                f'{html.escape(a.title)}</a>'
                f'<div class="meta">{html.escape(a.source)} · {html.escape(str(a.published_at))}'
                f'{" · " + " · ".join(tags) if tags else ""}</div></div>',
                unsafe_allow_html=True,
            )

# ---------------- AI Intelligence ----------------
with tabs[6]:
    if not reasoning.available:
        st.warning(
            f"LLM reasoning layer unavailable ({reasoning.error or 'not configured'}). "
            "Showing the rule-based system classification only."
        )
    st.markdown(f"### Overall AI Financial Intelligence &nbsp; {badge(reasoning.classification)}",
                unsafe_allow_html=True)
    if reasoning.overall_intelligence:
        st.write(reasoning.overall_intelligence)

    blocks = [
        ("Company overview", reasoning.company_overview),
        ("Cross-agent insights", reasoning.cross_agent_insights),
        ("Conflicting signals", reasoning.conflicting_signals),
        ("Why this classification", reasoning.classification_rationale),
        ("Uncertainty & data caveats", reasoning.uncertainty_notes),
    ]
    for title, body in blocks:
        if body:
            section(title)
            st.write(body)
    if reasoning.key_risks:
        section("Key risks")
        for k in reasoning.key_risks:
            st.markdown(f"- {k}")
    st.markdown(
        f'<div class="fi-disclaimer">{reasoning.disclaimer} '
        f'Model: {reasoning.model or "n/a"}.</div>',
        unsafe_allow_html=True,
    )

# ---------------- Full report ----------------
with tabs[7]:
    st.caption("The complete 13-section Financial Intelligence report. "
               "Use the download buttons above the tabs to export.")
    st.markdown(report_to_markdown(r))

# ---------------- Sources ----------------
with tabs[8]:
    section("Data sources & freshness")
    if r.sources:
        st.dataframe(pd.DataFrame([
            {"Data": s.label, "Provider": s.provider, "As of": s.as_of or "—", "Note": s.note}
            for s in r.sources
        ]), hide_index=True, width="stretch")
    section("Agent run status")
    st.dataframe(pd.DataFrame([
        {"Agent": s.name, "Status": s.status, "Detail": s.message, "ms": s.duration_ms}
        for s in r.agent_status
    ]), hide_index=True, width="stretch")
    if data:
        section("Data quality")
        dq = data.data_quality
        st.write(
            f"Rows: {dq.rows_returned} · removed in validation: {dq.rows_removed} · "
            f"range {dq.start_date} → {dq.end_date}"
        )
        if dq.issues:
            with st.expander("Validation notes"):
                for issue in dq.issues:
                    st.markdown(f"- {issue}")
