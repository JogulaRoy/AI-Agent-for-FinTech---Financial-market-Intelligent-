"""News Agent contracts."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import DataProvenance


class NewsArticle(BaseModel):
    title: str
    source: str
    published_at: str
    url: str
    summary: str = ""

    # Sentiment provenance is explicit: we never pass off a provider's label
    # as our own analysis.
    provider_sentiment_label: Optional[str] = None      # from the news provider, if any
    provider_sentiment_score: Optional[float] = None
    computed_sentiment_label: Optional[str] = None       # our lexical pass
    computed_sentiment_score: Optional[float] = None

    relevance: Optional[float] = None
    provider: str = ""


class NewsSentiment(BaseModel):
    positive_count: int = 0
    negative_count: int = 0
    neutral_count: int = 0
    total_articles: int = 0
    positive_ratio: float = 0.0
    negative_ratio: float = 0.0
    neutral_ratio: float = 0.0
    overall_sentiment: str = "Neutral"
    average_sentiment_score: Optional[float] = None
    sentiment_basis: str = "computed"   # "computed" | "provider" | "blended"


class NewsAnalysis(BaseModel):
    company_name: str
    symbol: str
    exchange: Optional[str] = None
    currency: Optional[str] = None

    articles: list[NewsArticle] = Field(default_factory=list)
    sentiment: NewsSentiment = Field(default_factory=NewsSentiment)
    themes: list[str] = Field(default_factory=list)
    articles_analyzed: int = 0
    analysis_window_hours: int = 168
    coverage_note: str = ""
    provenance: Optional[DataProvenance] = None
