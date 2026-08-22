from app.agents.data_agent import data_agent


def main():

    # ============================================================
    # 1. USER STOCK INPUT
    # ============================================================

    user_input = input(
        "Enter a stock name or symbol: "
    ).strip()

    if not user_input:

        print(
            "Please enter a stock name or symbol."
        )

        return

    # ============================================================
    # 2. USER PERIOD
    # ============================================================

    print(
        "\nSelect historical data period:"
    )

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

    period = period_map.get(
        period_choice
    )

    if period is None:

        print(
            "Invalid period choice."
        )

        return

    # ============================================================
    # 3. RUN DATA AGENT
    # ============================================================

    print(
        "\nFetching market data..."
    )

    try:

        result = data_agent(

            user_input=user_input,

            period=period,
        )

    except Exception as error:

        print(
            f"\nError: {error}"
        )

        return

    # ============================================================
    # 4. STOCK INFORMATION
    # ============================================================

    print(
        "\n" + "=" * 60
    )

    print(
        "STOCK INFORMATION"
    )

    print(
        "=" * 60
    )

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

    print(
        f"Analysis Period: "
        f"{result.requested_period}"
    )

    # ============================================================
    # 5. LATEST PRICE
    # ============================================================

    print(
        "\n" + "=" * 60
    )

    print(
        "LATEST PRICE"
    )

    print(
        "=" * 60
    )

    print(

        f"{result.price.symbol}"

        f"{result.price.value:,.2f}"

    )

    # ============================================================
    # 6. PERFORMANCE
    # ============================================================

    print(
        "\n" + "=" * 60
    )

    print(
        "PERFORMANCE"
    )

    print(
        "=" * 60
    )

    if (
        result.performance.daily_return
        is not None
    ):

        print(

            f"Daily Return: "

            f"{result.performance.daily_return * 100:.2f}%"

        )

    else:

        print(
            "Daily Return: Not available"
        )

    if (
        result.performance.monthly_return
        is not None
    ):

        print(

            f"Monthly Return: "

            f"{result.performance.monthly_return * 100:.2f}%"

        )

    else:

        print(
            "Monthly Return: Not available"
        )

    if (
        result.performance.six_month_return
        is not None
    ):

        print(

            f"6-Month Return: "

            f"{result.performance.six_month_return * 100:.2f}%"

        )

    else:

        print(
            "6-Month Return: Not available"
        )

    if (
        result.performance.one_year_return
        is not None
    ):

        print(

            f"1-Year Return: "

            f"{result.performance.one_year_return * 100:.2f}%"

        )

    else:

        print(
            "1-Year Return: Not available"
        )

    # ============================================================
    # 7. STABILITY
    # ============================================================

    print(
        "\n" + "=" * 60
    )

    print(
        "STABILITY ANALYSIS"
    )

    print(
        "=" * 60
    )

    if (
        result.stability.annualized_volatility
        is not None
    ):

        print(

            f"Annualized Volatility: "

            f"{result.stability.annualized_volatility * 100:.2f}%"

        )

    else:

        print(
            "Annualized Volatility: Not available"
        )

    if (
        result.stability.downside_volatility
        is not None
    ):

        print(

            f"Downside Volatility: "

            f"{result.stability.downside_volatility * 100:.2f}%"

        )

    else:

        print(
            "Downside Volatility: Not available"
        )

    if (
        result.stability.maximum_drawdown
        is not None
    ):

        print(

            f"Maximum Drawdown: "

            f"{result.stability.maximum_drawdown * 100:.2f}%"

        )

    else:

        print(
            "Maximum Drawdown: Not available"
        )

    if (
        result.stability.positive_days_ratio
        is not None
    ):

        print(

            f"Positive Days: "

            f"{result.stability.positive_days_ratio * 100:.2f}%"

        )

    else:

        print(
            "Positive Days: Not available"
        )

    if (
        result.stability.negative_days_ratio
        is not None
    ):

        print(

            f"Negative Days: "

            f"{result.stability.negative_days_ratio * 100:.2f}%"

        )

    else:

        print(
            "Negative Days: Not available"
        )

    if (
        result.stability.average_daily_return
        is not None
    ):

        print(

            f"Average Daily Return: "

            f"{result.stability.average_daily_return * 100:.4f}%"

        )

    else:

        print(
            "Average Daily Return: Not available"
        )

    if (
        result.stability.best_day
        is not None
    ):

        print(

            f"Best Day: "

            f"{result.stability.best_day * 100:.2f}%"

        )

    else:

        print(
            "Best Day: Not available"
        )

    if (
        result.stability.worst_day
        is not None
    ):

        print(

            f"Worst Day: "

            f"{result.stability.worst_day * 100:.2f}%"

        )

    else:

        print(
            "Worst Day: Not available"
        )

    print(

        f"Stability Classification: "

        f"{result.stability.classification}"

    )

    # ============================================================
    # 8. DATA QUALITY
    # ============================================================

    print(
        "\n" + "=" * 60
    )

    print(
        "DATA QUALITY"
    )

    print(
        "=" * 60
    )

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

    # ============================================================
    # 9. HISTORICAL DATA PREVIEW
    # ============================================================

    print(
        "\n" + "=" * 60
    )

    print(
        "HISTORICAL DATA — FIRST 5 RECORDS"
    )

    print(
        "=" * 60
    )

    for record in result.historical_data[:5]:

        print(

            f"{record.date} | "

            f"Open: {record.open:.2f} | "

            f"High: {record.high:.2f} | "

            f"Low: {record.low:.2f} | "

            f"Close: {record.close:.2f} | "

            f"Volume: {record.volume}"

        )


if __name__ == "__main__":

    main()