from app.agents.stock_resolver import resolve_stock

from app.tools.market_data import fetch_market_data

from app.tools.technical_indicators import (
    calculate_sma,
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_price_position,
    interpret_rsi,
    interpret_macd,
    calculate_technical_signal,
    calculate_support_resistance,
    calculate_support_resistance_position,
)

from app.schemas.technical_data import (
    MovingAverageMetrics,
    RSIMetrics,
    MACDMetrics,
    BollingerBandMetrics,
    SupportResistanceMetrics,
    TrendMetrics,
    TechnicalAnalysis,
)


def technical_agent(
    user_input: str,
    period: str = "1y",
) -> TechnicalAnalysis:
    """
    Technical Agent

    Responsibilities:

    1. Resolve user stock input.
    2. Fetch historical market data.
    3. Calculate technical indicators.
    4. Analyse price trend.
    5. Estimate support and resistance.
    6. Interpret technical indicators.
    7. Produce an overall technical signal.
    8. Return structured Pydantic output.

    This agent provides quantitative technical
    analysis only.

    It does NOT provide investment advice.
    """

    # ========================================================
    # 1. VALIDATE INPUT
    # ========================================================

    if not user_input or not user_input.strip():

        raise ValueError(
            "Stock name or symbol cannot be empty."
        )

    # ========================================================
    # 2. RESOLVE STOCK
    # ========================================================

    stock = resolve_stock(
        user_input.strip()
    )

    symbol = stock["symbol"]

    # ========================================================
    # 3. FETCH MARKET DATA
    # ========================================================

    market_data = fetch_market_data(
        symbol=symbol,
        period=period,
        interval="1d",
    )

    history = market_data["history"]

    current_price = float(
        market_data["latest_price"]
    )

    currency = market_data[
        "currency"
    ]["code"]

    # ========================================================
    # 4. MOVING AVERAGES
    # ========================================================

    sma_20 = calculate_sma(
        history,
        period=20,
    )

    sma_50 = calculate_sma(
        history,
        period=50,
    )

    sma_200 = calculate_sma(
        history,
        period=200,
    )

    ema_20 = calculate_ema(
        history,
        period=20,
    )

    ema_50 = calculate_ema(
        history,
        period=50,
    )

    moving_averages = MovingAverageMetrics(

        sma_20=sma_20,

        sma_50=sma_50,

        sma_200=sma_200,

        ema_20=ema_20,

        ema_50=ema_50,
    )

    # ========================================================
    # 5. RSI
    # ========================================================

    rsi_value = calculate_rsi(
        history,
        period=14,
    )

    rsi_interpretation = interpret_rsi(
        rsi_value
    )

    rsi = RSIMetrics(

        value=rsi_value,

        interpretation=rsi_interpretation,
    )

    # ========================================================
    # 6. MACD
    # ========================================================

    macd_data = calculate_macd(
        history
    )

    macd_value = macd_data[
        "macd"
    ]

    signal_value = macd_data[
        "signal"
    ]

    histogram_value = macd_data[
        "histogram"
    ]

    macd_interpretation = interpret_macd(
        macd_value,
        signal_value,
    )

    macd = MACDMetrics(

        macd=macd_value,

        signal=signal_value,

        histogram=histogram_value,

        interpretation=macd_interpretation,
    )

    # ========================================================
    # 7. BOLLINGER BANDS
    # ========================================================

    bollinger_data = (
        calculate_bollinger_bands(
            history
        )
    )

    bollinger_bands = (
        BollingerBandMetrics(

            upper=bollinger_data[
                "upper"
            ],

            middle=bollinger_data[
                "middle"
            ],

            lower=bollinger_data[
                "lower"
            ],
        )
    )

    # ========================================================
    # 8. SUPPORT / RESISTANCE
    # ========================================================

    support_resistance_data = (
        calculate_support_resistance(
            history,
            lookback=60,
        )
    )

    support = (
        support_resistance_data[
            "support"
        ]
    )

    resistance = (
        support_resistance_data[
            "resistance"
        ]
    )

    support_resistance_position = (
        calculate_support_resistance_position(
            current_price=current_price,
            support=support,
            resistance=resistance,
        )
    )

    support_resistance = (
        SupportResistanceMetrics(

            support=support,

            resistance=resistance,

            position=(
                support_resistance_position
            ),
        )
    )

    # ========================================================
    # 9. TREND
    # ========================================================

    price_position = (
        calculate_price_position(

            history=history,

            sma_20=sma_20,

            sma_50=sma_50,

            sma_200=sma_200,
        )
    )

    trend = TrendMetrics(

        price_position=price_position
    )

    # ========================================================
    # 10. OVERALL TECHNICAL SIGNAL
    # ========================================================

    overall_signal = (
        calculate_technical_signal(

            trend=price_position,

            rsi_interpretation=(
                rsi_interpretation
            ),

            macd_interpretation=(
                macd_interpretation
            ),
        )
    )

    # ========================================================
    # 11. RETURN STRUCTURED RESULT
    # ========================================================

    return TechnicalAnalysis(

        symbol=symbol,

        current_price=current_price,

        currency=currency,

        moving_averages=moving_averages,

        rsi=rsi,

        macd=macd,

        bollinger_bands=bollinger_bands,

        support_resistance=(
            support_resistance
        ),

        trend=trend,

        overall_signal=(
            overall_signal
        ),
    )