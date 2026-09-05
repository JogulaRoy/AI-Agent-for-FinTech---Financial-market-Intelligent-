"""
News Agent.

Retrieves recent company news through the same provider layer the Data Agent
uses (EODHD primary, yfinance fallback), de-duplicates, and runs a lightweight
lexical sentiment pass. Provider-supplied sentiment and our computed sentiment
are kept as separate fields — one is never presented as the other.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timezone

from app.data.provider_manager import ProviderManager, get_provider_manager
from app.schemas.common import DataProvenance
from app.schemas.news_data import NewsAnalysis, NewsArticle, NewsSentiment
from app.schemas.security import CanonicalSecurity

_POSITIVE = {
    "beat", "beats", "surge", "surged", "jump", "jumps", "gain", "gains", "rise",
    "rises", "rally", "record", "profit", "growth", "upgrade", "upgraded", "strong",
    "outperform", "bullish", "positive", "boost", "expansion", "wins", "win",
    "approval", "approved", "raises", "raised", "soar", "soared", "high", "top",
}
_NEGATIVE = {
    "miss", "misses", "missed", "fall", "falls", "drop", "drops", "plunge",
    "plunged", "loss", "losses", "decline", "declines", "downgrade", "downgraded",
    "weak", "bearish", "negative", "cut", "cuts", "lawsuit", "probe", "fraud",
    "warning", "warns", "slump", "slumped", "layoff", "layoffs", "recall", "fine",
    "fined", "concern", "concerns", "risk", "slowdown", "low", "sell-off",
}
_THEME_KEYWORDS = {
    "earnings": ["earnings", "revenue", "profit", "quarter", "results", "guidance"],
    "regulation / legal": ["lawsuit", "regulator", "antitrust", "probe", "court", "fine", "ruling"],
    "products / launch": ["launch", "unveil", "product", "release", "announce"],
    "M&A": ["acquire", "acquisition", "merger", "buyout", "deal", "stake"],
    "leadership": ["ceo", "cfo", "resign", "appoint", "executive", "board"],
    "analyst view": ["upgrade", "downgrade", "price target", "rating", "analyst"],
    "macro": ["inflation", "tariff", "interest rate", "fed", "economy", "recession"],
}


def _lexical_sentiment(text: str) -> tuple[str, float]:
    words = re.findall(r"[a-z\-]+", (text or "").lower())
    if not words:
        return "Neutral", 0.0
    pos = sum(1 for w in words if w in _POSITIVE)
    neg = sum(1 for w in words if w in _NEGATIVE)
    if pos == neg:
        return "Neutral", 0.0
    score = (pos - neg) / max(1, pos + neg)
    label = "Positive" if score > 0 else "Negative"
    return label, round(score, 3)


def _themes(articles: list[NewsArticle]) -> list[str]:
    blob = " ".join(f"{a.title} {a.summary}" for a in articles).lower()
    hits = Counter()
    for theme, keywords in _THEME_KEYWORDS.items():
        count = sum(blob.count(k) for k in keywords)
        if count:
            hits[theme] = count
    return [theme for theme, _ in hits.most_common(5)]


def _dedupe(articles: list[NewsArticle]) -> list[NewsArticle]:
    seen: set[str] = set()
    out: list[NewsArticle] = []
    for article in articles:
        key = re.sub(r"[^a-z0-9]", "", article.title.lower())[:80]
        if key and key in seen:
            continue
        seen.add(key)
        out.append(article)
    return out


def run_news_agent(
    security: CanonicalSecurity,
    hours: int = 168,
    limit: int = 25,
    manager: ProviderManager | None = None,
) -> NewsAnalysis:
    manager = manager or get_provider_manager()

    analysis = NewsAnalysis(
        company_name=security.company_name,
        symbol=security.symbol,
        exchange=security.exchange,
        currency=security.currency,
        analysis_window_hours=hours,
    )

    outcome = manager.get_news(security, hours=hours, limit=limit)
    raw: list[NewsArticle] = list(outcome.value) if outcome.ok else []

    if not raw:
        analysis.coverage_note = (
            "No recent news found through the configured providers. "
            "Coverage for this market may be limited on the free API tier."
        )
        analysis.sentiment.overall_sentiment = "No Recent News"
        return analysis

    articles = _dedupe(raw)

    pos = neg = neu = 0
    provider_scores: list[float] = []
    computed_scores: list[float] = []

    for article in articles:
        label, score = _lexical_sentiment(f"{article.title}. {article.summary}")
        article.computed_sentiment_label = label
        article.computed_sentiment_score = score
        computed_scores.append(score)
        if article.provider_sentiment_score is not None:
            provider_scores.append(article.provider_sentiment_score)

        # Blend: prefer provider sentiment when present, else our lexical pass.
        effective = article.provider_sentiment_label or label
        if effective == "Positive":
            pos += 1
        elif effective == "Negative":
            neg += 1
        else:
            neu += 1

    total = len(articles)
    basis = "blended" if provider_scores else "computed"
    avg_score = None
    if provider_scores:
        avg_score = round(sum(provider_scores) / len(provider_scores), 3)
    elif computed_scores:
        avg_score = round(sum(computed_scores) / len(computed_scores), 3)

    overall = (
        "Positive" if pos > neg else "Negative" if neg > pos else "Neutral"
    )

    analysis.articles = sorted(
        articles, key=lambda a: a.published_at, reverse=True
    )
    analysis.articles_analyzed = total
    analysis.themes = _themes(articles)
    analysis.sentiment = NewsSentiment(
        positive_count=pos, negative_count=neg, neutral_count=neu, total_articles=total,
        positive_ratio=pos / total, negative_ratio=neg / total, neutral_ratio=neu / total,
        overall_sentiment=overall, average_sentiment_score=avg_score, sentiment_basis=basis,
    )
    analysis.provenance = DataProvenance(
        provider=outcome.provider or "news",
        endpoint="news",
        as_of=datetime.now(timezone.utc).isoformat(),
        note=(
            "Provider sentiment shown where available; otherwise a lightweight "
            "lexical estimate computed by this system."
        ),
    )
    if outcome.provider == "yfinance":
        analysis.coverage_note = "News retrieved via yfinance fallback."
    return analysis
