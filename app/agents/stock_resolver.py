import re

import yfinance as yf

from app.tools.indian_security_master import (
    search_indian_equity,
)


# ============================================================
# STOCK RESOLVER
# ============================================================
#
# Indian market is FIRST PRIORITY.
#
# Indian:
#
#     NSE Security Master
#          ↓
#     SBIN
#          ↓
#     SBIN.NS
#
# International:
#
#     Yahoo Finance Search
#          ↓
#     AAPL
#
# This prevents global ticker collisions such as:
#
#     SBI
#
# which can refer to a US security while the user actually
# means State Bank of India.
# ============================================================


# ============================================================
# CURRENCY
# ============================================================

CURRENCY_SYMBOLS = {
    "USD": "$",
    "INR": "₹",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
    "CNY": "¥",
    "CAD": "C$",
    "AUD": "A$",
    "CHF": "CHF",
    "HKD": "HK$",
    "SGD": "S$",
}


# ============================================================
# NORMALIZE INPUT
# ============================================================

def normalize_input(
    user_input: str,
) -> str:

    if not user_input:

        raise ValueError(
            "Stock name or symbol cannot be empty."
        )

    value = (
        user_input
        .strip()
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value


# ============================================================
# YAHOO SEARCH
# ============================================================

def search_yahoo(
    query: str,
) -> list[dict]:

    try:

        search = yf.Search(
            query,
            max_results=50,
            news_count=0,
            lists_count=0,
            include_nav_links=False,
            enable_fuzzy_query=True,
        )

        return (
            search.quotes
            or []
        )

    except Exception as error:

        raise RuntimeError(
            f"Yahoo Finance search failed: {error}"
        )


# ============================================================
# CHECK YAHOO EQUITY
# ============================================================

def is_equity(
    quote: dict,
) -> bool:

    quote_type = (
        quote.get("quoteType")
        or ""
    ).upper()

    return quote_type == "EQUITY"


# ============================================================
# GET COMPANY NAME
# ============================================================

def get_name(
    quote: dict,
) -> str:

    return (
        quote.get("longname")
        or quote.get("longName")
        or quote.get("shortname")
        or quote.get("shortName")
        or quote.get("symbol")
        or ""
    ).strip()


# ============================================================
# GET CURRENCY
# ============================================================

def get_currency(
    symbol: str,
    quote: dict,
) -> tuple[str, str]:

    symbol = symbol.upper()

    if (
        symbol.endswith(".NS")
        or symbol.endswith(".BO")
    ):

        return (
            "INR",
            "₹",
        )

    currency = (
        quote.get("currency")
        or ""
    ).upper()

    return (
        currency,
        CURRENCY_SYMBOLS.get(
            currency,
            currency,
        ),
    )


# ============================================================
# NORMALIZE YAHOO RESULT
# ============================================================

def normalize_yahoo_candidate(
    quote: dict,
) -> dict | None:

    # --------------------------------------------------------
    # Only normal equities
    # --------------------------------------------------------

    if not is_equity(quote):

        return None

    symbol = (
        quote.get("symbol")
        or ""
    ).upper().strip()

    if not symbol:

        return None

    name = get_name(
        quote
    )

    exchange = (
        quote.get("exchange")
        or ""
    ).upper()

    currency, currency_symbol = (
        get_currency(
            symbol,
            quote,
        )
    )

    # --------------------------------------------------------
    # Reject obvious funds / ETFs
    # --------------------------------------------------------

    suspicious = [
        "ETF",
        "MUTUAL FUND",
        "MUNICIPAL FUND",
        "INDEX FUND",
    ]

    combined = (
        f"{symbol} {name}"
        .upper()
    )

    for word in suspicious:

        if word in combined:

            return None

    return {
        "name": name,
        "symbol": symbol,
        "exchange": exchange,
        "currency": currency,
        "currency_symbol": currency_symbol,
        "market": "International",
        "asset_type": "EQUITY",
    }


# ============================================================
# SCORE INTERNATIONAL RESULT
# ============================================================

def score_yahoo_candidate(
    candidate: dict,
    user_input: str,
) -> int:

    query = (
        user_input
        .strip()
        .upper()
    )

    symbol = candidate[
        "symbol"
    ].upper()

    name = candidate[
        "name"
    ].upper()

    score = 0

    if query == symbol:

        score += 3000

    if query == name:

        score += 2500

    if name.startswith(query):

        score += 1000

    if query in name:

        score += 500

    return score


# ============================================================
# RESOLVE INTERNATIONAL
# ============================================================

def resolve_international(
    user_input: str,
) -> dict:

    quotes = search_yahoo(
        user_input
    )

    candidates = []

    for quote in quotes:

        candidate = (
            normalize_yahoo_candidate(
                quote
            )
        )

        if candidate:

            candidates.append(
                candidate
            )

    if not candidates:

        raise ValueError(
            f"No stock found for "
            f"'{user_input}'."
        )

    scored = []

    for candidate in candidates:

        score = (
            score_yahoo_candidate(
                candidate,
                user_input,
            )
        )

        candidate_copy = (
            candidate.copy()
        )

        candidate_copy[
            "score"
        ] = score

        scored.append(
            candidate_copy
        )

    scored.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    best = scored[0]

    if best["score"] < 500:

        raise ValueError(
            f"Could not confidently identify "
            f"'{user_input}'. "
            f"Please enter a clearer company "
            f"name or symbol."
        )

    best.pop(
        "score",
        None,
    )

    best[
        "confidence"
    ] = 0.90

    best[
        "source"
    ] = "Yahoo Finance"

    return best


# ============================================================
# EXPLICIT YAHOO SYMBOL
# ============================================================

def resolve_explicit_symbol(
    user_input: str,
) -> dict | None:

    value = (
        user_input
        .upper()
        .strip()
    )

    if not (
        value.endswith(".NS")
        or value.endswith(".BO")
    ):

        return None

    try:

        ticker = yf.Ticker(
            value
        )

        history = ticker.history(
            period="5d",
            interval="1d",
            auto_adjust=False,
        )

        if history.empty:

            return None

        try:

            info = ticker.get_info()

        except Exception:

            info = {}

        quote_type = (
            info.get("quoteType")
            or "EQUITY"
        ).upper()

        if quote_type != "EQUITY":

            return None

        name = (
            info.get("longName")
            or info.get("shortName")
            or value
        )

        if value.endswith(".NS"):

            exchange = "NSE"

        else:

            exchange = "BSE"

        return {
            "name": name,
            "symbol": value,
            "exchange": exchange,
            "currency": "INR",
            "currency_symbol": "₹",
            "market": "India",
            "asset_type": "EQUITY",
            "confidence": 0.99,
            "source": "Yahoo Finance",
        }

    except Exception:

        return None


# ============================================================
# MAIN RESOLVER
# ============================================================

def resolve_stock(
    user_input: str,
) -> dict:

    user_input = normalize_input(
        user_input
    )

    # ========================================================
    # 1. EXPLICIT EXCHANGE SYMBOL
    # ========================================================

    explicit = (
        resolve_explicit_symbol(
            user_input
        )
    )

    if explicit:

        return explicit

    # ========================================================
    # 2. INDIA FIRST
    # ========================================================
    #
    # THIS IS THE IMPORTANT PART.
    #
    # SBI
    # ↓
    # NSE security master
    # ↓
    # SBIN
    # ↓
    # SBIN.NS
    #
    # Yahoo global search is NOT consulted first.
    # ========================================================

    indian_result = (
        search_indian_equity(
            user_input
        )
    )

    if indian_result:

        indian_result[
            "yahoo_symbol"
        ] = (
            indian_result["symbol"]
            + ".NS"
        )

        return indian_result

    # ========================================================
    # 3. INTERNATIONAL FALLBACK
    # ========================================================

    return resolve_international(
        user_input
    )