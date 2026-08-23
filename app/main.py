from app.agents.data_agent import data_agent
from app.agents.technical_agent import technical_agent
from app.agents.news_agent import news_agent
from app.agents.risk_agent import risk_agent


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

    period = period_map.get(
        period_choice
    )

    if period is None:

        print(
            "\nInvalid period choice."
        )

        return None

    return period


# ============================================================
# DATA AGENT
# ============================================================

def run_data_agent(
    user_input: str,
    period: str,
):

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

    currency_symbol = CURRENCY_SYMBOLS.get(
        result.price.currency,
        result.price.currency,
    )

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

    print("\n" + "=" * 60)
    print("LATEST PRICE")
    print("=" * 60)

    print(
        f"{currency_symbol}"
        f"{result.price.value:,.2f}"
    )

    print("\n" + "=" * 60)
    print("PERFORMANCE")
    print("=" * 60)

    performance = result.performance

    metrics = [
        (
            "Daily Return",
            performance.daily_return,
        ),
        (
            "Monthly Return",
            performance.monthly_return,
        ),
        (
            "6-Month Return",
            performance.six_month_return,
        ),
        (
            "1-Year Return",
            performance.one_year_return,
        ),
    ]

    for name, value in metrics:

        if value is not None:

            print(
                f"{name}: "
                f"{value * 100:.2f}%"
            )

        else:

            print(
                f"{name}: Not available"
            )

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


# ============================================================
# TECHNICAL AGENT
# ============================================================

def run_technical_agent(
    user_input: str,
    period: str,
):

    print("\nFetching technical data...")

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

    print("\n" + "=" * 60)
    print("MOVING AVERAGES")
    print("=" * 60)

    moving_averages = result.moving_averages

    for name, value in [
        ("SMA 20", moving_averages.sma_20),
        ("SMA 50", moving_averages.sma_50),
        ("SMA 200", moving_averages.sma_200),
        ("EMA 20", moving_averages.ema_20),
        ("EMA 50", moving_averages.ema_50),
    ]:

        if value is not None:

            print(
                f"{name}: "
                f"{currency_symbol}"
                f"{value:,.2f}"
            )

        else:

            print(
                f"{name}: Not available"
            )

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
            "Bollinger Bands: Not available"
        )

    print("\n" + "=" * 60)
    print("TREND ANALYSIS")
    print("=" * 60)

    print(
        f"Price Position: "
        f"{result.trend.price_position}"
    )

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

    if support_resistance.resistance is not None:

        print(
            f"Resistance: "
            f"{currency_symbol}"
            f"{support_resistance.resistance:,.2f}"
        )

    print(
        f"Current Position: "
        f"{support_resistance.position}"
    )

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


# ============================================================
# NEWS AGENT
# ============================================================

def run_news_agent(
    user_input: str,
):

    print("\nFetching recent financial news...")

    try:

        result = news_agent(
            user_input=user_input,
            hours=168,
            limit=20,
        )

    except Exception as error:

        print(
            f"\nNews Agent Error: {error}"
        )

        return

    print("\n" + "=" * 60)
    print("NEWS AGENT — COMPANY")
    print("=" * 60)

    print(
        f"Name: {result.company_name}"
    )

    print(
        f"Symbol: {result.symbol}"
    )

    print(
        f"Exchange: {result.exchange}"
    )

    print("\n" + "=" * 60)
    print("NEWS SUMMARY")
    print("=" * 60)

    print(
        f"Articles Analyzed: "
        f"{result.articles_analyzed}"
    )

    print(
        f"Analysis Window: "
        f"{result.analysis_window_hours} hours"
    )

    sentiment = result.sentiment

    print("\n" + "=" * 60)
    print("NEWS SENTIMENT")
    print("=" * 60)

    print(
        f"Overall Sentiment: "
        f"{sentiment.overall_sentiment}"
    )

    print(
        f"Positive News: "
        f"{sentiment.positive_count}"
    )

    print(
        f"Negative News: "
        f"{sentiment.negative_count}"
    )

    print(
        f"Neutral News: "
        f"{sentiment.neutral_count}"
    )

    print(
        f"Positive Ratio: "
        f"{sentiment.positive_ratio * 100:.2f}%"
    )

    print(
        f"Negative Ratio: "
        f"{sentiment.negative_ratio * 100:.2f}%"
    )

    print(
        f"Neutral Ratio: "
        f"{sentiment.neutral_ratio * 100:.2f}%"
    )

    if (
        sentiment.average_sentiment_score
        is not None
    ):

        print(
            f"Average Sentiment Score: "
            f"{sentiment.average_sentiment_score:.4f}"
        )

    print("\n" + "=" * 60)
    print("RECENT NEWS")
    print("=" * 60)

    if not result.articles:

        print(
            "No recent news articles found."
        )

        return

    for index, article in enumerate(
        result.articles[:10],
        start=1,
    ):

        print(
            f"\n{index}. {article.title}"
        )

        print(
            f"   Source: "
            f"{article.source}"
        )

        print(
            f"   Published: "
            f"{article.published_at}"
        )

        print(
            f"   Sentiment: "
            f"{article.sentiment_label}"
        )

        if article.sentiment_score is not None:

            print(
                f"   Sentiment Score: "
                f"{article.sentiment_score:.4f}"
            )

        if article.summary:

            print(
                f"   Summary: "
                f"{article.summary[:300]}..."
            )

        print(
            f"   URL: "
            f"{article.url}"
        )


# ============================================================
# RISK AGENT
# ============================================================

def run_risk_agent(
    user_input: str,
    period: str,
):

    print("\nCalculating risk metrics...")

    try:

        result = risk_agent(
            user_input=user_input,
            period=period,
        )

    except Exception as error:

        print(
            f"\nRisk Agent Error: {error}"
        )

        return

    risk = result.risk_metrics

    classification = (
        result.classification
    )

    print("\n" + "=" * 60)
    print("RISK AGENT — STOCK INFORMATION")
    print("=" * 60)

    print(
        f"Company: "
        f"{result.company_name}"
    )

    print(
        f"Symbol: "
        f"{result.symbol}"
    )

    print(
        f"Exchange: "
        f"{result.exchange}"
    )

    print(
        f"Analysis Period: "
        f"{result.analysis_period}"
    )

    print(
        f"Data Points: "
        f"{result.data_points}"
    )

    # ========================================================
    # RISK CLASSIFICATION
    # ========================================================

    print("\n" + "=" * 60)
    print("RISK CLASSIFICATION")
    print("=" * 60)

    print(
        f"Risk Level: "
        f"{classification.level}"
    )

    if classification.score is not None:

        print(
            f"Risk Score: "
            f"{classification.score:.2f}/100"
        )

    print(
        f"\n{classification.explanation}"
    )

    # ========================================================
    # VOLATILITY
    # ========================================================

    print("\n" + "=" * 60)
    print("VOLATILITY & DOWNSIDE RISK")
    print("=" * 60)

    if risk.annualized_volatility is not None:

        print(
            f"Annualized Volatility: "
            f"{risk.annualized_volatility * 100:.2f}%"
        )

    else:

        print(
            "Annualized Volatility: "
            "Not available"
        )

    if risk.downside_volatility is not None:

        print(
            f"Downside Volatility: "
            f"{risk.downside_volatility * 100:.2f}%"
        )

    else:

        print(
            "Downside Volatility: "
            "Not available"
        )

    if risk.maximum_drawdown is not None:

        print(
            f"Maximum Drawdown: "
            f"{risk.maximum_drawdown * 100:.2f}%"
        )

    else:

        print(
            "Maximum Drawdown: "
            "Not available"
        )

    # ========================================================
    # VALUE AT RISK
    # ========================================================

    print("\n" + "=" * 60)
    print("VALUE AT RISK")
    print("=" * 60)

    if risk.value_at_risk_95 is not None:

        print(
            f"95% VaR: "
            f"{risk.value_at_risk_95 * 100:.2f}%"
        )

    else:

        print(
            "95% VaR: Not available"
        )

    if risk.value_at_risk_99 is not None:

        print(
            f"99% VaR: "
            f"{risk.value_at_risk_99 * 100:.2f}%"
        )

    else:

        print(
            "99% VaR: Not available"
        )

    if risk.conditional_var_95 is not None:

        print(
            f"95% CVaR: "
            f"{risk.conditional_var_95 * 100:.2f}%"
        )

    else:

        print(
            "95% CVaR: Not available"
        )

    if risk.conditional_var_99 is not None:

        print(
            f"99% CVaR: "
            f"{risk.conditional_var_99 * 100:.2f}%"
        )

    else:

        print(
            "99% CVaR: Not available"
        )

    # ========================================================
    # RISK-ADJUSTED PERFORMANCE
    # ========================================================

    print("\n" + "=" * 60)
    print("RISK-ADJUSTED PERFORMANCE")
    print("=" * 60)

    if risk.sharpe_ratio is not None:

        print(
            f"Sharpe Ratio: "
            f"{risk.sharpe_ratio:.2f}"
        )

    else:

        print(
            "Sharpe Ratio: Not available"
        )

    if risk.sortino_ratio is not None:

        print(
            f"Sortino Ratio: "
            f"{risk.sortino_ratio:.2f}"
        )

    else:

        print(
            "Sortino Ratio: Not available"
        )

    # ========================================================
    # KEY RISKS
    # ========================================================

    print("\n" + "=" * 60)
    print("KEY HISTORICAL RISKS")
    print("=" * 60)

    for risk_item in result.key_risks:

        print(
            f"• {risk_item}"
        )

    # ========================================================
    # SUMMARY
    # ========================================================

    print("\n" + "=" * 60)
    print("RISK SUMMARY")
    print("=" * 60)

    print(
        result.risk_summary
    )

    print(
        "\nNote: Risk measurements are "
        "historical, rule-based indicators "
        "and are not financial advice."
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n" + "=" * 60)
    print("FINANCIAL MARKET INTELLIGENCE")
    print("=" * 60)

    print("\nSelect an agent:")

    print("1. Data Agent")
    print("2. Technical Agent")
    print("3. News Agent")
    print("4. Risk Agent")

    agent_choice = input(
        "\nEnter your choice (1-4): "
    ).strip()

    if agent_choice not in [
        "1",
        "2",
        "3",
        "4",
    ]:

        print(
            "\nInvalid agent choice."
        )

        return

    # ========================================================
    # STOCK INPUT
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
    # NEWS AGENT
    # ========================================================

    if agent_choice == "3":

        run_news_agent(
            user_input=user_input,
        )

        return

    # ========================================================
    # PERIOD FOR DATA / TECHNICAL / RISK
    # ========================================================

    period = get_period()

    if period is None:

        return

    # ========================================================
    # DATA AGENT
    # ========================================================

    if agent_choice == "1":

        run_data_agent(
            user_input=user_input,
            period=period,
        )

    # ========================================================
    # TECHNICAL AGENT
    # ========================================================

    elif agent_choice == "2":

        run_technical_agent(
            user_input=user_input,
            period=period,
        )

    # ========================================================
    # RISK AGENT
    # ========================================================

    elif agent_choice == "4":

        run_risk_agent(
            user_input=user_input,
            period=period,
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()