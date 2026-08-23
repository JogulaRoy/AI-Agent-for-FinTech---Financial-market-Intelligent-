import yfinance as yf


# ============================================================
# CURRENCY SYMBOLS
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
# FETCH MARKET DATA
# ============================================================

def fetch_market_data(
    symbol: str,
    period: str = "1y",
    interval: str = "1d",
) -> dict:
    """
    Fetch historical market data using Yahoo Finance.

    Important:
        The symbol passed here must already be a Yahoo Finance
        symbol.

    Examples:

        Indian NSE:
            SBIN.NS
            INFY.NS
            TCS.NS

        Indian BSE:
            SBIN.BO

        US:
            AAPL
            MSFT

    This function does NOT resolve company names.
    Stock resolution belongs to stock_resolver.py.
    """

    # ========================================================
    # 1. VALIDATE SYMBOL
    # ========================================================

    if not symbol or not symbol.strip():
        raise ValueError(
            "Market data symbol is required."
        )

    symbol = symbol.strip().upper()

    # ========================================================
    # 2. CREATE YAHOO TICKER
    # ========================================================

    ticker = yf.Ticker(symbol)

    # ========================================================
    # 3. DOWNLOAD HISTORY
    # ========================================================

    try:

        history = ticker.history(
            period=period,
            interval=interval,
            auto_adjust=False,
        )

    except Exception as error:

        raise ValueError(
            f"Unable to fetch market data for "
            f"{symbol}: {error}"
        )

    # ========================================================
    # 4. CHECK DATA
    # ========================================================

    if history is None or history.empty:

        raise ValueError(
            f"No market data available for "
            f"{symbol}."
        )

    # ========================================================
    # 5. REQUIRED COLUMNS
    # ========================================================

    required_columns = [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in history.columns
    ]

    if missing_columns:

        raise ValueError(
            f"Market data for {symbol} is missing "
            f"required columns: {missing_columns}"
        )

    # ========================================================
    # 6. COUNT ORIGINAL ROWS
    # ========================================================

    rows_before_cleaning = len(history)

    # ========================================================
    # 7. REMOVE INVALID PRICE ROWS
    # ========================================================

    history = history.dropna(
        subset=[
            "Open",
            "High",
            "Low",
            "Close",
        ]
    )

    if history.empty:

        raise ValueError(
            f"Market data for {symbol} contains "
            "no valid price records."
        )

    # ========================================================
    # 8. CLEAN VOLUME
    # ========================================================

    history["Volume"] = (
        history["Volume"]
        .fillna(0)
    )

    # ========================================================
    # 9. LATEST PRICE
    # ========================================================

    latest_price = float(
        history["Close"].iloc[-1]
    )

    # ========================================================
    # 10. CURRENCY
    # ========================================================
    #
    # Exchange suffix is authoritative for Indian listings.
    #
    # .NS → NSE → INR
    # .BO → BSE → INR
    #
    # International stocks use Yahoo metadata.
    # ========================================================

    if (
        symbol.endswith(".NS")
        or symbol.endswith(".BO")
    ):

        currency_code = "INR"
        currency_symbol = "₹"

    else:

        currency_code = ""

        # ----------------------------------------------------
        # Yahoo history metadata
        # ----------------------------------------------------

        try:

            metadata = ticker.history_metadata

            if metadata:

                currency_code = (
                    metadata.get(
                        "currency"
                    )
                    or ""
                ).upper()

        except Exception:

            currency_code = ""

        # ----------------------------------------------------
        # Yahoo fast_info fallback
        # ----------------------------------------------------

        if not currency_code:

            try:

                fast_info = ticker.fast_info

                currency_code = (
                    fast_info.get(
                        "currency"
                    )
                    or ""
                ).upper()

            except Exception:

                currency_code = ""

        # ----------------------------------------------------
        # Final fallback
        # ----------------------------------------------------

        if not currency_code:

            currency_code = "USD"

        currency_symbol = (
            CURRENCY_SYMBOLS.get(
                currency_code,
                currency_code,
            )
        )

    # ========================================================
    # 11. DATA QUALITY
    # ========================================================

    rows_after_cleaning = len(history)

    rows_removed = (
        rows_before_cleaning
        - rows_after_cleaning
    )

    start_date = (
        history.index[0]
        .strftime("%Y-%m-%d")
    )

    end_date = (
        history.index[-1]
        .strftime("%Y-%m-%d")
    )

    # ========================================================
    # 12. RETURN STRUCTURED DATA
    # ========================================================

    return {
        # ----------------------------------------------------
        # Yahoo symbol actually used for fetching
        # ----------------------------------------------------

        "symbol": symbol,

        # ----------------------------------------------------
        # Latest price
        # ----------------------------------------------------

        "latest_price": latest_price,

        # ----------------------------------------------------
        # Currency
        # ----------------------------------------------------

        "currency": {
            "code": currency_code,
            "symbol": currency_symbol,
        },

        # ----------------------------------------------------
        # Historical Pandas DataFrame
        #
        # This stays inside the tools layer.
        # Data Agent converts it to Pydantic objects.
        # ----------------------------------------------------

        "history": history,

        # ----------------------------------------------------
        # Data quality
        # ----------------------------------------------------

        "data_quality": {
            "rows_returned": rows_after_cleaning,
            "rows_removed": rows_removed,
            "start_date": start_date,
            "end_date": end_date,
        },
    }