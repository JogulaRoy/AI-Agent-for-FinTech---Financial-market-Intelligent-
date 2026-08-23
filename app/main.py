from app.agents.data_agent import data_agent
from app.agents.technical_agent import technical_agent


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
}


# ============================================================
# PERIOD SELECTION
# ============================================================

def get_period():
    """
    Get historical analysis period from the user.
    """

    print("\nSelect historical data period:")

    print("1. 1 month")
    print("2. 6 months")
    print("3. 1 year")
    print("4. 2 years")
    print("5. 5 years")
    print("6. Maximum available")

    period_choice = input(
        "\nEnter your choice (1-6): "
    ).strip()

    period_map = {
        "1": "1mo",
        "2": "6mo",
        "3": "1y",
        "4": "2y",
        "5": "5y",
        "6": "max",
    }

    period = period_map.get(period_choice)

    if period is None:
        print("\nInvalid period choice.")
        return None

    return period


# ============================================================
# DATA AGENT
# ============================================================

def run_data_agent(
    user_input: str,
    period: str,
):
    """
    Run the Data Agent and display its result.
    """

    print("\nFetching market data...")

    try:

        result = data_agent(
            user_input=user_input,
            period=period,
        )

    except Exception as error:

        print(
            f"\nData Agent Error: {error}"
        )

        return

    # ========================================================
    # STOCK INFORMATION
    # ========================================================

    print("\n" + "=" * 60)
    print("DATA AGENT — STOCK INFORMATION")
    print("=" * 60)

    print(
        f"Name: {result.stock.name}"
    )

    print(
        f"Symbol: {result.stock.symbol}"
    )

    print(
        f"Exchange: {result.stock.exchange}"
    )

    print(
        f"Currency: {result.stock.currency}"
    )

    # ========================================================
    # LATEST PRICE
    # ========================================================

    currency_symbol = CURRENCY_SYMBOLS.get(
        result.price.currency,
        result.price.currency,
    )

    print("\n" + "=" * 60)
    print("LATEST PRICE")
    print("=" * 60)

    print(
        f"{currency_symbol}"
        f"{result.price.value:,.2f}"
    )

    # ========================================================
    # PERFORMANCE
    # ========================================================

    print("\n" + "=" * 60)
    print("PERFORMANCE")
    print("=" * 60)

    performance = result.performance

    if performance.daily_return is not None:

        print(
            f"Daily Return: "
            f"{performance.daily_return * 100:.2f}%"
        )

    else:

        print(
            "Daily Return: Not available"
        )

    if performance.monthly_return is not None:

        print(
            f"Monthly Return: "
            f"{performance.monthly_return * 100:.2f}%"
        )

    else:

        print(
            "Monthly Return: Not available"
        )

    if performance.six_month_return is not None:

        print(
            f"6-Month Return: "
            f"{performance.six_month_return * 100:.2f}%"
        )

    else:

        print(
            "6-Month Return: Not available"
        )

    if performance.one_year_return is not None:

        print(
            f"1-Year Return: "
            f"{performance.one_year_return * 100:.2f}%"
        )

    else:

        print(
            "1-Year Return: Not available"
        )

    # ========================================================
    # STABILITY
    # ========================================================

    print("\n" + "=" * 60)
    print("STABILITY ANALYSIS")
    print("=" * 60)

    stability = result.stability

    if stability.annualized_volatility is not None:

        print(
            f"Annualized Volatility: "
            f"{stability.annualized_volatility * 100:.2f}%"
        )

    if stability.downside_volatility is not None:

        print(
            f"Downside Volatility: "
            f"{stability.downside_volatility * 100:.2f}%"
        )

    if stability.maximum_drawdown is not None:

        print(
            f"Maximum Drawdown: "
            f"{stability.maximum_drawdown * 100:.2f}%"
        )

    if stability.positive_days_ratio is not None:

        print(
            f"Positive Days: "
            f"{stability.positive_days_ratio * 100:.2f}%"
        )

    if stability.negative_days_ratio is not None:

        print(
            f"Negative Days: "
            f"{stability.negative_days_ratio * 100:.2f}%"
        )

    if stability.average_daily_return is not None:

        print(
            f"Average Daily Return: "
            f"{stability.average_daily_return * 100:.4f}%"
        )

    if stability.best_day is not None:

        print(
            f"Best Day: "
            f"{stability.best_day * 100:.2f}%"
        )

    if stability.worst_day is not None:

        print(
            f"Worst Day: "
            f"{stability.worst_day * 100:.2f}%"
        )

    print(
        f"Stability Classification: "
        f"{stability.classification}"
    )

    # ========================================================
    # DATA QUALITY
    # ========================================================

    print("\n" + "=" * 60)
    print("DATA QUALITY")
    print("=" * 60)

    print(
        f"Valid Records: "
        f"{result.data_quality.rows_returned}"
    )

    print(
        f"Rows Removed: "
        f"{result.data_quality.rows_removed}"
    )

    print(
        f"Data Start: "
        f"{result.data_quality.start_date}"
    )

    print(
        f"Data End: "
        f"{result.data_quality.end_date}"
    )

    # ========================================================
    # STRUCTURED DATA
    # ========================================================

    print("\n" + "=" * 60)
    print("DATA AGENT STRUCTURED OUTPUT")
    print("=" * 60)

    print(
        result.model_dump_json(
            indent=2
        )
    )


# ============================================================
# TECHNICAL AGENT
# ============================================================

def run_technical_agent(
    user_input: str,
    period: str,
):
    """
    Run the Technical Agent and display
    complete technical analysis.
    """

    print(
        "\nFetching technical data..."
    )

    try:

        result = technical_agent(
            user_input=user_input,
            period=period,
        )

    except Exception as error:

        print(
            f"\nTechnical Agent Error: {error}"
        )

        return

    currency_symbol = CURRENCY_SYMBOLS.get(
        result.currency,
        result.currency,
    )

    # ========================================================
    # STOCK INFORMATION
    # ========================================================

    print("\n" + "=" * 60)
    print("TECHNICAL AGENT — STOCK INFORMATION")
    print("=" * 60)

    print(
        f"Symbol: {result.symbol}"
    )

    print(
        f"Currency: {result.currency}"
    )

    print(
        f"Current Price: "
        f"{currency_symbol}"
        f"{result.current_price:,.2f}"
    )

    # ========================================================
    # MOVING AVERAGES
    # ========================================================

    print("\n" + "=" * 60)
    print("MOVING AVERAGES")
    print("=" * 60)

    moving_averages = result.moving_averages

    if moving_averages.sma_20 is not None:

        print(
            f"SMA 20: "
            f"{currency_symbol}"
            f"{moving_averages.sma_20:,.2f}"
        )

    else:

        print(
            "SMA 20: Not available"
        )

    if moving_averages.sma_50 is not None:

        print(
            f"SMA 50: "
            f"{currency_symbol}"
            f"{moving_averages.sma_50:,.2f}"
        )

    else:

        print(
            "SMA 50: Not available"
        )

    if moving_averages.sma_200 is not None:

        print(
            f"SMA 200: "
            f"{currency_symbol}"
            f"{moving_averages.sma_200:,.2f}"
        )

    else:

        print(
            "SMA 200: Not available"
        )

    if moving_averages.ema_20 is not None:

        print(
            f"EMA 20: "
            f"{currency_symbol}"
            f"{moving_averages.ema_20:,.2f}"
        )

    else:

        print(
            "EMA 20: Not available"
        )

    if moving_averages.ema_50 is not None:

        print(
            f"EMA 50: "
            f"{currency_symbol}"
            f"{moving_averages.ema_50:,.2f}"
        )

    else:

        print(
            "EMA 50: Not available"
        )

    # ========================================================
    # RSI
    # ========================================================

    print("\n" + "=" * 60)
    print("RSI")
    print("=" * 60)

    if result.rsi.value is not None:

        print(
            f"RSI (14): "
            f"{result.rsi.value:.2f}"
        )

    else:

        print(
            "RSI (14): Not available"
        )

    print(
        f"Interpretation: "
        f"{result.rsi.interpretation}"
    )

    # ========================================================
    # MACD
    # ========================================================

    print("\n" + "=" * 60)
    print("MACD")
    print("=" * 60)

    if result.macd.macd is not None:

        print(
            f"MACD: "
            f"{result.macd.macd:.4f}"
        )

        print(
            f"Signal: "
            f"{result.macd.signal:.4f}"
        )

        print(
            f"Histogram: "
            f"{result.macd.histogram:.4f}"
        )

    else:

        print(
            "MACD: Not available"
        )

    print(
        f"Interpretation: "
        f"{result.macd.interpretation}"
    )

    # ========================================================
    # BOLLINGER BANDS
    # ========================================================

    print("\n" + "=" * 60)
    print("BOLLINGER BANDS")
    print("=" * 60)

    bands = result.bollinger_bands

    if bands.upper is not None:

        print(
            f"Upper Band: "
            f"{currency_symbol}"
            f"{bands.upper:,.2f}"
        )

        print(
            f"Middle Band: "
            f"{currency_symbol}"
            f"{bands.middle:,.2f}"
        )

        print(
            f"Lower Band: "
            f"{currency_symbol}"
            f"{bands.lower:,.2f}"
        )

    else:

        print(
            "Bollinger Bands: "
            "Not available"
        )

    # ========================================================
    # TREND
    # ========================================================

    print("\n" + "=" * 60)
    print("TREND ANALYSIS")
    print("=" * 60)

    print(
        f"Price Position: "
        f"{result.trend.price_position}"
    )

    # ========================================================
    # SUPPORT / RESISTANCE
    # ========================================================

    print("\n" + "=" * 60)
    print("SUPPORT / RESISTANCE")
    print("=" * 60)

    support_resistance = (
        result.support_resistance
    )

    if support_resistance.support is not None:

        print(
            f"Support: "
            f"{currency_symbol}"
            f"{support_resistance.support:,.2f}"
        )

    else:

        print(
            "Support: Not available"
        )

    if support_resistance.resistance is not None:

        print(
            f"Resistance: "
            f"{currency_symbol}"
            f"{support_resistance.resistance:,.2f}"
        )

    else:

        print(
            "Resistance: Not available"
        )

    print(
        f"Current Position: "
        f"{support_resistance.position}"
    )

    # ========================================================
    # OVERALL TECHNICAL SIGNAL
    # ========================================================

    print("\n" + "=" * 60)
    print("OVERALL TECHNICAL SIGNAL")
    print("=" * 60)

    print(
        result.overall_signal
    )

    print(
        "\nNote: This is a rule-based "
        "technical interpretation, "
        "not financial advice."
    )

    # ========================================================
    # STRUCTURED JSON OUTPUT
    # ========================================================

    print("\n" + "=" * 60)
    print("TECHNICAL AGENT STRUCTURED OUTPUT")
    print("=" * 60)

    print(
        result.model_dump_json(
            indent=2
        )
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "\n" + "=" * 60
    )

    print(
        "FINANCIAL MARKET INTELLIGENCE"
    )

    print(
        "=" * 60
    )

    # ========================================================
    # AGENT SELECTION
    # ========================================================

    print(
        "\nSelect an agent:"
    )

    print(
        "1. Data Agent"
    )

    print(
        "2. Technical Agent"
    )

    agent_choice = input(
        "\nEnter your choice (1-2): "
    ).strip()

    if agent_choice not in ["1", "2"]:

        print(
            "\nInvalid agent choice."
        )

        return

    # ========================================================
    # USER STOCK INPUT
    # ========================================================

    user_input = input(
        "\nEnter a stock name or symbol: "
    ).strip()

    if not user_input:

        print(
            "\nPlease enter a stock name "
            "or symbol."
        )

        return

    # ========================================================
    # USER PERIOD
    # ========================================================

    period = get_period()

    if period is None:

        return

    # ========================================================
    # RUN SELECTED AGENT
    # ========================================================

    if agent_choice == "1":

        run_data_agent(
            user_input=user_input,
            period=period,
        )

    elif agent_choice == "2":

        run_technical_agent(
            user_input=user_input,
            period=period,
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()