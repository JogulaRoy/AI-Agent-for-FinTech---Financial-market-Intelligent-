import yfinance as yf


def resolve_stock(user_input: str) -> dict:
    """
    Convert a user's stock name or symbol into a stock ticker.
    """

    query = user_input.strip()

    if not query:
        raise ValueError("Stock input cannot be empty.")

    search = yf.Search(
        query,
        max_results=5,
        news_count=0,
        enable_fuzzy_query=True,
    )

    quotes = search.quotes

    if not quotes:
        raise ValueError(
            f"Could not find a stock for '{user_input}'."
        )

    first_result = quotes[0]

    return {
        "symbol": first_result.get("symbol"),
        "name": first_result.get("longname")
        or first_result.get("shortname"),
        "exchange": first_result.get("exchange"),
        "quote_type": first_result.get("quoteType"),
    }