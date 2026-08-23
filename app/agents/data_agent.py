from app.agents.stock_resolver import resolve_stock

from app.tools.market_data import fetch_market_data

from app.tools.market_metrics import (
    calculate_daily_return,
    calculate_monthly_return,
    calculate_six_month_return,
    calculate_one_year_return,
    calculate_annualized_volatility,
    calculate_downside_volatility,
    calculate_maximum_drawdown,
    calculate_positive_days_ratio,
    calculate_negative_days_ratio,
    calculate_average_daily_return,
    calculate_best_day,
    calculate_worst_day,
    classify_stability,
)

from app.schemas.market_data import (
    StockInfo,
    PriceInfo,
    HistoricalPrice,
    PerformanceMetrics,
    StabilityMetrics,
    DataQuality,
    MarketData,
)


# ============================================================
# DATA AGENT
# ============================================================

def data_agent(
    user_input: str,
    period: str = "1y",
) -> MarketData:
    """
    Data Agent

    Responsibilities:

    1. Resolve the user's stock dynamically.
    2. Prefer Indian NSE/BSE equities when applicable.
    3. Determine the correct Yahoo Finance symbol.
    4. Fetch historical market data.
    5. Validate and clean market data.
    6. Identify latest price and currency.
    7. Convert history into structured records.
    8. Calculate performance metrics.
    9. Calculate stability metrics.
    10. Report data quality.
    11. Return structured Pydantic data.

    The Data Agent does NOT:

        - make investment decisions
        - provide financial advice
        - analyze news
        - perform sentiment analysis
        - calculate technical indicators
        - perform portfolio risk decisions
    """

    # ========================================================
    # 1. VALIDATE USER INPUT
    # ========================================================

    if not user_input or not user_input.strip():

        raise ValueError(
            "Stock name or symbol cannot be empty."
        )

    user_input = user_input.strip()

    # ========================================================
    # 2. RESOLVE STOCK
    # ========================================================
    #
    # Example:
    #
    # SBI
    # ↓
    # NSE Security Master
    # ↓
    # State Bank of India
    # ↓
    # SBIN
    # ↓
    # SBIN.NS
    #
    # Apple
    # ↓
    # International resolver
    # ↓
    # AAPL
    #
    # ========================================================

    stock = resolve_stock(
        user_input
    )

    # ========================================================
    # 3. DETERMINE DATA SYMBOL
    # ========================================================
    #
    # THIS IS THE CRITICAL FIX.
    #
    # For Indian stocks:
    #
    # stock["symbol"]      = SBIN
    # stock["yahoo_symbol"] = SBIN.NS
    #
    # We use yahoo_symbol for fetching.
    #
    # For international stocks:
    #
    # stock["symbol"] = AAPL
    #
    # No yahoo_symbol is required.
    #
    # ========================================================

    data_symbol = stock.get(
        "yahoo_symbol"
    )

    if not data_symbol:

        data_symbol = stock["symbol"]

    # ========================================================
    # 4. FETCH MARKET DATA
    # ========================================================

    market_data = fetch_market_data(
        symbol=data_symbol,
        period=period,
        interval="1d",
    )

    history = market_data["history"]

    # ========================================================
    # 5. SAFETY CHECK
    # ========================================================

    if history is None or history.empty:

        raise ValueError(
            f"No historical market data available "
            f"for {stock['name']} "
            f"({data_symbol})."
        )

    # ========================================================
    # 6. CURRENCY
    # ========================================================

    currency_code = (
        market_data[
            "currency"
        ][
            "code"
        ]
    )

    currency_symbol = (
        market_data[
            "currency"
        ][
            "symbol"
        ]
    )

    # ========================================================
    # 7. STOCK INFORMATION
    # ========================================================
    #
    # IMPORTANT:
    #
    # Display the user's actual market identity:
    #
    # State Bank of India
    # SBIN
    # NSE
    # INR
    #
    # Do NOT display SBIN.NS as the stock's public symbol.
    #
    # SBIN.NS is only the Yahoo Finance data symbol.
    #
    # ========================================================

    stock_info = StockInfo(
        name=stock["name"],
        symbol=stock["symbol"],
        exchange=stock["exchange"],
        currency=currency_code,
    )

    # ========================================================
    # 8. LATEST PRICE
    # ========================================================

    latest_price = float(
        market_data[
            "latest_price"
        ]
    )

    price_info = PriceInfo(
        value=latest_price,
        currency=currency_code,
        symbol=currency_symbol,
    )

    # ========================================================
    # 9. CONVERT HISTORY
    # ========================================================

    historical_data = []

    for date, row in history.iterrows():

        # ----------------------------------------------------
        # Volume safety
        # ----------------------------------------------------

        volume = row.get(
            "Volume",
            0,
        )

        if volume is None:

            volume = 0

        try:

            volume = int(
                volume
            )

        except (
            TypeError,
            ValueError,
        ):

            volume = 0

        # ----------------------------------------------------
        # Create structured record
        # ----------------------------------------------------

        historical_data.append(
            HistoricalPrice(

                date=date.strftime(
                    "%Y-%m-%d"
                ),

                open=float(
                    row["Open"]
                ),

                high=float(
                    row["High"]
                ),

                low=float(
                    row["Low"]
                ),

                close=float(
                    row["Close"]
                ),

                volume=volume,
            )
        )

    # ========================================================
    # 10. PERFORMANCE METRICS
    # ========================================================

    daily_return = (
        calculate_daily_return(
            history
        )
    )

    monthly_return = (
        calculate_monthly_return(
            history
        )
    )

    six_month_return = (
        calculate_six_month_return(
            history
        )
    )

    one_year_return = (
        calculate_one_year_return(
            history
        )
    )

    performance = PerformanceMetrics(

        daily_return=daily_return,

        monthly_return=monthly_return,

        six_month_return=six_month_return,

        one_year_return=one_year_return,
    )

    # ========================================================
    # 11. STABILITY METRICS
    # ========================================================

    annualized_volatility = (
        calculate_annualized_volatility(
            history
        )
    )

    downside_volatility = (
        calculate_downside_volatility(
            history
        )
    )

    maximum_drawdown = (
        calculate_maximum_drawdown(
            history
        )
    )

    positive_days_ratio = (
        calculate_positive_days_ratio(
            history
        )
    )

    negative_days_ratio = (
        calculate_negative_days_ratio(
            history
        )
    )

    average_daily_return = (
        calculate_average_daily_return(
            history
        )
    )

    best_day = calculate_best_day(
        history
    )

    worst_day = calculate_worst_day(
        history
    )

    stability_classification = (
        classify_stability(
            annualized_volatility,
            maximum_drawdown,
        )
    )

    stability = StabilityMetrics(

        annualized_volatility=(
            annualized_volatility
        ),

        downside_volatility=(
            downside_volatility
        ),

        maximum_drawdown=(
            maximum_drawdown
        ),

        positive_days_ratio=(
            positive_days_ratio
        ),

        negative_days_ratio=(
            negative_days_ratio
        ),

        average_daily_return=(
            average_daily_return
        ),

        best_day=best_day,

        worst_day=worst_day,

        classification=(
            stability_classification
        ),
    )

    # ========================================================
    # 12. DATA QUALITY
    # ========================================================

    quality = market_data.get(
        "data_quality"
    )

    if quality is None:

        data_quality = DataQuality(

            rows_returned=len(
                history
            ),

            rows_removed=0,

            start_date=(
                history.index[0]
                .strftime("%Y-%m-%d")
            ),

            end_date=(
                history.index[-1]
                .strftime("%Y-%m-%d")
            ),
        )

    else:

        data_quality = DataQuality(

            rows_returned=quality[
                "rows_returned"
            ],

            rows_removed=quality[
                "rows_removed"
            ],

            start_date=quality[
                "start_date"
            ],

            end_date=quality[
                "end_date"
            ],
        )

    # ========================================================
    # 13. RETURN COMPLETE DATA AGENT RESULT
    # ========================================================

    return MarketData(

        stock=stock_info,

        price=price_info,

        requested_period=period,

        historical_data=historical_data,

        performance=performance,

        stability=stability,

        data_quality=data_quality,
    )