import os
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# CONFIGURATION
# ============================================================

ALPHA_VANTAGE_URL = (
    "https://www.alphavantage.co/query"
)


# ============================================================
# FETCH NEWS
# ============================================================

def fetch_news(
    symbol: str,
    hours: int = 168,
    limit: int = 20,
) -> list[dict]:
    """
    Fetch recent financial news for a stock.

    Args:
        symbol:
            Resolved stock ticker such as AAPL or MSFT.

        hours:
            Number of previous hours to search.
            Default = 168 hours = 7 days.

        limit:
            Maximum number of articles.

    Returns:
        List of raw news article dictionaries.
    """

    # ========================================================
    # 1. GET API KEY
    # ========================================================

    api_key = os.getenv(
        "ALPHA_VANTAGE_API_KEY"
    )

    if not api_key:

        raise ValueError(
            "ALPHA_VANTAGE_API_KEY is not configured "
            "in the .env file."
        )

    # ========================================================
    # 2. VALIDATE SYMBOL
    # ========================================================

    if not symbol or not symbol.strip():

        raise ValueError(
            "Stock symbol cannot be empty."
        )

    symbol = symbol.strip().upper()

    # ========================================================
    # 3. VALIDATE PARAMETERS
    # ========================================================

    if hours <= 0:

        raise ValueError(
            "hours must be greater than zero."
        )

    if limit <= 0:

        raise ValueError(
            "limit must be greater than zero."
        )

    # ========================================================
    # 4. CALCULATE START TIME
    # ========================================================

    current_time = datetime.now(
        timezone.utc
    )

    start_time = (
        current_time
        - timedelta(hours=hours)
    )

    time_from = start_time.strftime(
        "%Y%m%dT%H%M"
    )

    # ========================================================
    # 5. API PARAMETERS
    # ========================================================

    params = {

        "function": "NEWS_SENTIMENT",

        "tickers": symbol,

        "time_from": time_from,

        "sort": "LATEST",

        "limit": limit,

        "apikey": api_key,
    }

    # ========================================================
    # 6. SEND REQUEST
    # ========================================================

    try:

        response = requests.get(
            ALPHA_VANTAGE_URL,
            params=params,
            timeout=20,
        )

    except requests.RequestException as error:

        raise RuntimeError(
            f"Unable to connect to news service: {error}"
        ) from error

    # ========================================================
    # 7. HTTP STATUS
    # ========================================================

    if response.status_code != 200:

        raise RuntimeError(
            "News API request failed. "
            f"HTTP status: {response.status_code}"
        )

    # ========================================================
    # 8. PARSE JSON
    # ========================================================

    try:

        data = response.json()

    except ValueError as error:

        raise RuntimeError(
            "Alpha Vantage returned invalid JSON."
        ) from error

    # ========================================================
    # 9. API ERROR HANDLING
    # ========================================================

    if "Error Message" in data:

        raise RuntimeError(
            "Alpha Vantage error: "
            f"{data['Error Message']}"
        )

    if "Note" in data:

        raise RuntimeError(
            "Alpha Vantage API notice: "
            f"{data['Note']}"
        )

    if "Information" in data:

        raise RuntimeError(
            "Alpha Vantage information: "
            f"{data['Information']}"
        )

    # ========================================================
    # 10. GET NEWS FEED
    # ========================================================

    feed = data.get(
        "feed",
        []
    )

    # ========================================================
    # 11. VALIDATE RESPONSE
    # ========================================================

    if not isinstance(feed, list):

        raise RuntimeError(
            "Unexpected Alpha Vantage news response format."
        )

    # ========================================================
    # 12. RETURN NEWS
    # ========================================================

    return feed