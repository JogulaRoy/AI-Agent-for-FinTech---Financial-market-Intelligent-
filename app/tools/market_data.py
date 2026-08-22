import yfinance as yf
import pandas as pd


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
}


def clean_historical_data(
    history: pd.DataFrame,
) -> tuple[pd.DataFrame, int]:
    """
    Clean and validate historical market data.

    Returns:
        Cleaned DataFrame
        Number of rows removed during cleaning
    """

    if history.empty:
        raise ValueError(
            "Historical market data is empty."
        )

    original_row_count = len(history)

    history = history.copy()

    # Remove duplicate dates
    history = history[
        ~history.index.duplicated(
            keep="last"
        )
    ]

    # Sort chronologically
    history = history.sort_index()

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
            "Missing required market data columns: "
            f"{missing_columns}"
        )

    # Remove missing OHLC values
    history = history.dropna(
        subset=[
            "Open",
            "High",
            "Low",
            "Close",
        ]
    )

    # Remove missing volume
    history = history.dropna(
        subset=["Volume"]
    )

    # Remove invalid prices
    history = history[
        (history["Open"] > 0)
        & (history["High"] > 0)
        & (history["Low"] > 0)
        & (history["Close"] > 0)
    ]

    # Remove invalid volume
    history = history[
        history["Volume"] >= 0
    ]

    if history.empty:
        raise ValueError(
            "No valid market data remains "
            "after cleaning."
        )

    rows_removed = (
        original_row_count
        - len(history)
    )

    return history, rows_removed


def fetch_market_data(
    symbol: str,
    period: str = "1y",
    interval: str = "1d",
) -> dict:
    """
    Fetch and clean historical market data.

    The Data Agent does not directly depend on
    the provider implementation.
    """

    ticker = yf.Ticker(symbol)

    history = ticker.history(
        period=period,
        interval=interval,
        auto_adjust=False,
    )

    if history.empty:
        raise ValueError(
            f"No historical market data found "
            f"for {symbol}."
        )

    history, rows_removed = (
        clean_historical_data(history)
    )

    # Currency
    try:
        currency = (
            ticker.fast_info.get(
                "currency",
                "USD",
            )
        )
    except Exception:
        currency = "USD"

    currency = str(currency).upper()

    currency_symbol = (
        CURRENCY_SYMBOLS.get(
            currency,
            currency,
        )
    )

    # Latest valid price
    latest = history.iloc[-1]

    latest_price = float(
        latest["Close"]
    )

    return {
        "symbol": symbol,

        "history": history,

        "latest_price": latest_price,

        "currency": {
            "code": currency,
            "symbol": currency_symbol,
        },

        "data_quality": {
            "rows_returned": len(history),
            "rows_removed": rows_removed,
            "start_date": (
                history.index[0]
                .strftime("%Y-%m-%d")
            ),
            "end_date": (
                history.index[-1]
                .strftime("%Y-%m-%d")
            ),
        },
    }