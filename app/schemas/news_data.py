from typing import Optional

from pydantic import BaseModel, Field


# ============================================================
# NEWS ARTICLE
# ============================================================

class NewsArticle(BaseModel):
    """
    Represents one financial news article.
    """

    title: str

    source: str

    published_at: str

    url: str

    summary: str

    sentiment_label: Optional[str] = None

    sentiment_score: Optional[float] = None


# ============================================================
# NEWS SENTIMENT
# ============================================================

class NewsSentiment(BaseModel):
    """
    Aggregated sentiment from financial news.
    """

    positive_count: int = 0

    negative_count: int = 0

    neutral_count: int = 0

    total_articles: int = 0

    positive_ratio: float = 0.0

    negative_ratio: float = 0.0

    neutral_ratio: float = 0.0

    overall_sentiment: str = "Neutral"

    average_sentiment_score: Optional[float] = None


# ============================================================
# NEWS ANALYSIS
# ============================================================

class NewsAnalysis(BaseModel):
    """
    Complete structured output of the News Agent.

    This object will later be passed to the
    multi-agent orchestrator.
    """

    company_name: str

    symbol: str

    exchange: str

    currency: str

    articles: list[NewsArticle] = Field(
        default_factory=list
    )

    sentiment: NewsSentiment

    articles_analyzed: int = 0

    analysis_window_hours: int = 168