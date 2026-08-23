from app.agents.stock_resolver import resolve_stock
from app.tools.news_data import fetch_news

from app.schemas.news_data import (
    NewsAnalysis,
    NewsArticle,
    NewsSentiment,
)


# ============================================================
# NEWS AGENT
# ============================================================

def news_agent(
    user_input: str,
    hours: int = 168,
    limit: int = 20,
) -> NewsAnalysis:
    """
    News Agent

    Responsibilities:

    1. Understand the user's stock input.
    2. Resolve company name/symbol.
    3. Retrieve recent financial news.
    4. Extract article information.
    5. Analyze article sentiment.
    6. Aggregate overall market sentiment.
    7. Return structured Pydantic output.

    Args:
        user_input:
            Company name or stock symbol.

        hours:
            Number of previous hours to search.

        limit:
            Maximum number of articles.

    Returns:
        NewsAnalysis
    """

    # ========================================================
    # 1. RESOLVE STOCK
    # ========================================================

    stock = resolve_stock(
        user_input
    )

    symbol = stock["symbol"]

    # ========================================================
    # 2. FETCH NEWS
    # ========================================================

    raw_news = fetch_news(
        symbol=symbol,
        hours=hours,
        limit=limit,
    )

    # ========================================================
    # 3. PROCESS ARTICLES
    # ========================================================

    articles = []

    positive_count = 0
    negative_count = 0
    neutral_count = 0

    sentiment_scores = []

    for item in raw_news:

        # ----------------------------------------------------
        # BASIC ARTICLE INFORMATION
        # ----------------------------------------------------

        title = item.get(
            "title",
            "Unknown title",
        )

        source = item.get(
            "source",
            "Unknown source",
        )

        published_at = item.get(
            "time_published",
            "Unknown",
        )

        url = item.get(
            "url",
            "",
        )

        summary = item.get(
            "summary",
            "",
        )

        # ----------------------------------------------------
        # SENTIMENT
        # ----------------------------------------------------

        sentiment_label = item.get(
            "overall_sentiment_label"
        )

        sentiment_score = item.get(
            "overall_sentiment_score"
        )

        # ----------------------------------------------------
        # NORMALIZE SENTIMENT LABEL
        # ----------------------------------------------------

        if sentiment_label:

            label = sentiment_label.lower()

            if "bullish" in label:
                normalized_label = "Positive"

            elif "bearish" in label:
                normalized_label = "Negative"

            else:
                normalized_label = "Neutral"

        else:

            normalized_label = "Neutral"

        # ----------------------------------------------------
        # COUNT SENTIMENT
        # ----------------------------------------------------

        if normalized_label == "Positive":

            positive_count += 1

        elif normalized_label == "Negative":

            negative_count += 1

        else:

            neutral_count += 1

        # ----------------------------------------------------
        # SENTIMENT SCORE
        # ----------------------------------------------------

        numeric_score = None

        if sentiment_score is not None:

            try:

                numeric_score = float(
                    sentiment_score
                )

                sentiment_scores.append(
                    numeric_score
                )

            except (
                TypeError,
                ValueError,
            ):

                numeric_score = None

        # ----------------------------------------------------
        # CREATE STRUCTURED ARTICLE
        # ----------------------------------------------------

        article = NewsArticle(
            title=title,
            source=source,
            published_at=published_at,
            url=url,
            summary=summary,
            sentiment_label=normalized_label,
            sentiment_score=numeric_score,
        )

        articles.append(
            article
        )

    # ========================================================
    # 4. TOTAL ARTICLES
    # ========================================================

    total_articles = len(
        articles
    )

    # ========================================================
    # 5. CALCULATE SENTIMENT RATIOS
    # ========================================================

    if total_articles > 0:

        positive_ratio = (
            positive_count
            / total_articles
        )

        negative_ratio = (
            negative_count
            / total_articles
        )

        neutral_ratio = (
            neutral_count
            / total_articles
        )

    else:

        positive_ratio = 0.0
        negative_ratio = 0.0
        neutral_ratio = 0.0

    # ========================================================
    # 6. DETERMINE OVERALL SENTIMENT
    # ========================================================

    if total_articles == 0:

        overall_sentiment = (
            "No Recent News"
        )

    elif positive_count > negative_count:

        overall_sentiment = "Positive"

    elif negative_count > positive_count:

        overall_sentiment = "Negative"

    else:

        overall_sentiment = "Neutral"

    # ========================================================
    # 7. AVERAGE SENTIMENT SCORE
    # ========================================================

    if sentiment_scores:

        average_sentiment_score = (
            sum(sentiment_scores)
            / len(sentiment_scores)
        )

    else:

        average_sentiment_score = None

    # ========================================================
    # 8. CREATE SENTIMENT OBJECT
    # ========================================================

    sentiment = NewsSentiment(

        positive_count=positive_count,

        negative_count=negative_count,

        neutral_count=neutral_count,

        total_articles=total_articles,

        positive_ratio=positive_ratio,

        negative_ratio=negative_ratio,

        neutral_ratio=neutral_ratio,

        overall_sentiment=overall_sentiment,

        average_sentiment_score=(
            average_sentiment_score
        ),
    )

    # ========================================================
    # 9. RETURN COMPLETE NEWS ANALYSIS
    # ========================================================

    return NewsAnalysis(

        company_name=stock["name"],

        symbol=stock["symbol"],

        exchange=stock["exchange"],

        currency=stock.get(
            "currency",
            "USD",
        ),

        articles=articles,

        sentiment=sentiment,

        articles_analyzed=total_articles,

        analysis_window_hours=hours,
    )