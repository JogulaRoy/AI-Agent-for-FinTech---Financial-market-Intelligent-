"""Render a FinancialIntelligenceReport as the 13-section Markdown document."""

from __future__ import annotations

from app.schemas.intelligence import FinancialIntelligenceReport


def _pct(value, digits: int = 2) -> str:
    return "n/a" if value is None else f"{value * 100:+.{digits}f}%"


def _num(value, digits: int = 2) -> str:
    return "n/a" if value is None else f"{value:,.{digits}f}"


def _big(value) -> str:
    if value is None:
        return "n/a"
    for unit, scale in (("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(value) >= scale:
            return f"{value / scale:,.2f}{unit}"
    return f"{value:,.0f}"


def report_to_markdown(r: FinancialIntelligenceReport) -> str:
    sec = r.security
    data = r.data
    tech = r.technical
    risk = r.risk
    news = r.news
    reasoning = r.reasoning
    ccy = (data.quote.currency if data else None) or (sec.currency if sec else "")

    out: list[str] = []
    w = out.append

    title = sec.company_name if sec else r.user_query
    w(f"# Financial Market Intelligence — {title}")
    w("")
    w(f"*Query:* `{r.user_query}`  ")
    w(f"*Generated:* {r.generated_at:%Y-%m-%d %H:%M UTC}  ")
    w(f"*System classification:* **{r.overall_classification or 'n/a'}**")
    w("")
    w("> Financial intelligence for educational use. Not investment advice. "
      "No guaranteed predictions.")
    w("")

    # 1. Company Overview
    w("## 1. Company Overview")
    if sec:
        w(f"- **Name:** {sec.company_name}")
        w(f"- **Symbol / Exchange:** {sec.symbol} · {sec.exchange or 'n/a'}")
        w(f"- **Country / Currency:** {sec.country or 'n/a'} · {sec.currency or 'n/a'}")
        w(f"- **ISIN:** {sec.isin or 'n/a'}")
        w(f"- **Resolved by:** {sec.resolved_by} (confidence {sec.confidence:.0%})")
    if data and data.profile:
        p = data.profile
        w(f"- **Sector / Industry:** {p.sector or 'n/a'} · {p.industry or 'n/a'}")
        w(f"- **Market cap:** {_big(p.market_cap)}")
        if p.description:
            w("")
            w(p.description.strip())
    w("")

    # 2. Current Market Snapshot
    w("## 2. Current Market Snapshot")
    if data:
        q = data.quote
        w(f"- **Price:** {ccy} {_num(q.price)} ({_pct(q.change_percent)})")
        w(f"- **Open / High / Low / Prev close:** {_num(q.open)} / {_num(q.high)} / "
          f"{_num(q.low)} / {_num(q.previous_close)}")
        w(f"- **Volume:** {_big(q.volume)}")
        w(f"- **52-week range:** {_num(q.week52_low)} – {_num(q.week52_high)}")
        w(f"- **As of:** {q.timestamp or 'n/a'} · source: "
          f"{q.provenance.provider if q.provenance else 'n/a'}")
    else:
        w("_Market data unavailable._")
    w("")

    # 3. Fundamental Health
    w("## 3. Fundamental Health")
    if data and data.fundamentals:
        f = data.fundamentals
        w(f"**Classification: {f.health.classification}** "
          f"(score {_num(f.health.score, 0)}/100 — project-specific, not a regulated rating)")
        w("")
        for factor in f.health.factors:
            w(f"- {factor.name}: **{factor.verdict}** — {factor.detail}")
        w("")
        v = f.valuation
        w("| Metric | Value | Metric | Value |")
        w("|---|---|---|---|")
        w(f"| P/E | {_num(v.pe_ratio)} | ROE | {_pct(v.roe)} |")
        w(f"| P/B | {_num(v.pb_ratio)} | ROA | {_pct(v.roa)} |")
        w(f"| P/S | {_num(v.ps_ratio)} | Debt/Equity | {_num(v.debt_to_equity)} |")
        w(f"| EV/EBITDA | {_num(v.ev_to_ebitda)} | Current ratio | {_num(v.current_ratio)} |")
        w(f"| Net margin | {_pct(v.profit_margin)} | Revenue growth | {_pct(v.revenue_growth)} |")
        if not f.available:
            w("")
            w(f"_{f.unavailable_reason or 'Full statements unavailable on the current data plan.'}_")
    w("")

    # 4. Financial Stability
    w("## 4. Financial Stability")
    if data:
        s = data.stability
        w(f"- **Classification:** {s.classification}")
        w(f"- Annualized volatility: {_pct(s.annualized_volatility)}")
        w(f"- Downside volatility: {_pct(s.downside_volatility)}")
        w(f"- Maximum drawdown: {_pct(s.maximum_drawdown)}")
        w(f"- Positive / negative days: {_pct(s.positive_days_ratio)} / {_pct(s.negative_days_ratio)}")
    w("")

    # 5. Historical Performance
    w("## 5. Historical Performance")
    if data:
        p = data.performance
        w(f"- 1-day: {_pct(p.daily_return)}")
        w(f"- 1-month: {_pct(p.monthly_return)}")
        w(f"- 6-month: {_pct(p.six_month_return)}")
        w(f"- 1-year: {_pct(p.one_year_return)}")
        w(f"- History window: {data.history.start_date} → {data.history.end_date} "
          f"({len(data.history)} bars)")
    w("")

    # 6. Technical Analysis
    w("## 6. Technical Analysis")
    if tech and tech.current_price is not None:
        m = tech.moving_averages
        w(f"**Overall signal: {tech.overall_signal}**")
        for reason in tech.signal_reasons:
            w(f"- {reason}")
        w("")
        w(f"- SMA 20/50/200: {_num(m.sma_20)} / {_num(m.sma_50)} / {_num(m.sma_200)}")
        w(f"- RSI(14, Wilder): {_num(tech.rsi.value)} — {tech.rsi.interpretation}")
        w(f"- MACD: {_num(tech.macd.macd, 3)} — {tech.macd.interpretation}")
        w(f"- Bollinger %B: {_num(tech.bollinger_bands.percent_b)} — {tech.bollinger_bands.interpretation}")
        w(f"- ATR %: {_pct(tech.atr.percent_of_price)}")
        w(f"- Support ≈ {_num(tech.support_resistance.support)} · "
          f"Resistance ≈ {_num(tech.support_resistance.resistance)} "
          f"({tech.support_resistance.position})")
        w(f"- _{tech.support_resistance.methodology}_")
    else:
        w("_Technical analysis unavailable._")
    w("")

    # 7. Risk Analysis
    w("## 7. Risk Analysis")
    if risk and risk.classification.level != "Insufficient Data":
        rm = risk.risk_metrics
        w(f"**Risk level: {risk.classification.level}** "
          f"(project score {_num(risk.classification.score, 0)}/100 — not a regulated rating)")
        w(f"- Annualized / downside volatility: {_pct(rm.annualized_volatility)} / {_pct(rm.downside_volatility)}")
        w(f"- Max drawdown: {_pct(rm.maximum_drawdown)}")
        w(f"- VaR 95% / 99% (1d): {_pct(rm.value_at_risk_95)} / {_pct(rm.value_at_risk_99)}")
        w(f"- CVaR 95% / 99%: {_pct(rm.conditional_var_95)} / {_pct(rm.conditional_var_99)}")
        w(f"- Sharpe / Sortino: {_num(rm.sharpe_ratio)} / {_num(rm.sortino_ratio)}")
        w(f"- Beta ({rm.benchmark or 'n/a'}): {_num(rm.beta)}")
        w(f"- Risk-free rate: {_pct(risk.risk_free_rate)} ({risk.risk_free_rate_source})")
    else:
        w("_Risk analysis unavailable._")
    w("")

    # 8. News & Sentiment
    w("## 8. News & Sentiment")
    if news and news.articles:
        s = news.sentiment
        w(f"**Overall: {s.overall_sentiment}** "
          f"(+{s.positive_count} / -{s.negative_count} / ~{s.neutral_count}, basis: {s.sentiment_basis})")
        if news.themes:
            w(f"- Themes: {', '.join(news.themes)}")
        w(f"- Source: {news.provenance.provider if news.provenance else 'n/a'}")
        w("")
        for a in news.articles[:10]:
            w(f"- [{a.title}]({a.url}) — {a.source}, {a.published_at}")
    else:
        w(f"_{news.coverage_note if news else 'No recent news found.'}_")
    w("")

    # 9. Cross-Agent Insights
    w("## 9. Cross-Agent Insights")
    w(reasoning.cross_agent_insights or reasoning.overall_intelligence or "_n/a_")
    w("")

    # 10. Conflicting Signals
    w("## 10. Conflicting Signals")
    w(reasoning.conflicting_signals or "_None identified._")
    w("")

    # 11. Overall AI Financial Intelligence
    w("## 11. Overall AI Financial Intelligence")
    w(f"**Classification: {reasoning.classification or r.overall_classification or 'n/a'}**")
    w("")
    w(reasoning.overall_intelligence or "_n/a_")
    if reasoning.classification_rationale:
        w("")
        w(f"*Rationale:* {reasoning.classification_rationale}")
    if reasoning.uncertainty_notes:
        w("")
        w(f"*Uncertainty:* {reasoning.uncertainty_notes}")
    if not reasoning.available:
        w("")
        w("_LLM reasoning layer unavailable; classification is rule-based._")
    w("")

    # 12. Key Risks
    w("## 12. Key Risks")
    key_risks = reasoning.key_risks or (risk.key_risks if risk else [])
    for k in key_risks:
        w(f"- {k}")
    if not key_risks:
        w("_None flagged._")
    w("")

    # 13. Data Sources / Freshness
    w("## 13. Data Sources / Freshness")
    if r.sources:
        w("| Data | Provider | As of | Note |")
        w("|---|---|---|---|")
        for s in r.sources:
            w(f"| {s.label} | {s.provider} | {s.as_of or 'n/a'} | {s.note} |")
    w("")
    w("### Agent run status")
    for st in r.agent_status:
        w(f"- {st.name}: {st.status} — {st.message} ({st.duration_ms} ms)")
    if r.errors:
        w("")
        w("### Errors")
        for e in r.errors:
            w(f"- {e}")
    w("")
    w("---")
    w(f"_{r.disclaimer}_")
    if reasoning.model:
        w(f"  \n_Reasoning model: {reasoning.model}_")

    return "\n".join(out)
