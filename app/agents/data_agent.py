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


def data_agent(
    user_input: str,
    period: str = "1y",
) -> MarketData:
    """
    Data Agent for the Financial Market Intelligence system.

    Responsibilities:

    1. Resolve user stock input.
    2. Fetch historical market data.
    3. Validate and clean market data.
    4. Identify currency.
    5. Convert market history into structured data.
    6. Calculate historical performance.
    7. Calculate stability metrics.
    8. Return a JSON-compatible Pydantic object.

    The Data Agent does NOT:
        - provide investment advice
        - perform news analysis
        - perform sentiment analysis
        - calculate technical indicators
        - perform final investment decisions

    Those responsibilities belong to other agents.
    """

    # ============================================================
    # 1. RESOLVE USER STOCK INPUT
    # ============================================================

    if not user_input or not user_input.strip():
        raise ValueError(
            "Stock name or symbol cannot be empty."
        )

    stock = resolve_stock(
        user_input.strip()
    )

    symbol = stock["symbol"]

    # ============================================================
    # 2. FETCH MARKET DATA
    # ============================================================

    market_data = fetch_market_data(
        symbol=symbol,
        period=period,
        interval="1d",
    )

    history = market_data["history"]

    # ============================================================
    # 3. STOCK INFORMATION
    # ============================================================

    stock_info = StockInfo(
        name=stock["name"],
        symbol=stock["symbol"],
        exchange=stock["exchange"],
        currency=market_data[
            "currency"
        ]["code"],
    )

    # ============================================================
    # 4. LATEST PRICE
    # ============================================================

    price_info = PriceInfo(
        value=market_data[
            "latest_price"
        ],

        currency=market_data[
            "currency"
        ]["code"],

        symbol=market_data[
            "currency"
        ]["symbol"],
    )

    # ============================================================
    # 5. CONVERT HISTORY TO JSON-COMPATIBLE STRUCTURE
    # ============================================================

    historical_data = []

    for date, row in history.iterrows():

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

                volume=int(
                    row["Volume"]
                ),
            )
        )

    # ============================================================
    # 6. PERFORMANCE ANALYSIS
    # ============================================================

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

    # ============================================================
    # 7. STABILITY ANALYSIS
    # ============================================================

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

    # ============================================================
    # 8. DATA QUALITY
    # ============================================================

    quality = market_data[
        "data_quality"
    ]

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

    # ============================================================
    # 9. RETURN COMPLETE DATA AGENT RESULT
    # ============================================================

    return MarketData(

        stock=stock_info,

        price=price_info,

        requested_period=period,

        historical_data=historical_data,

        performance=performance,

        stability=stability,

        data_quality=data_quality,
    )