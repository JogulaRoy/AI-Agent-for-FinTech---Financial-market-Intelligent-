"""
Technical Analysis Agent.

Operates on the normalized OHLCV history supplied by the Data Agent. Uses
standard financial formulas (Wilder RSI/ATR, EMA-based MACD, SMA Bollinger).
Returns a structured result; it prints nothing and gives no advice.
"""

from __future__ import annotations

from app.data.normalizer import price_history_to_frame
from app.schemas.market_data import PriceHistory
from app.schemas.security import CanonicalSecurity
from app.schemas.technical_data import (
    ATRMetrics,
    BollingerBandMetrics,
    MACDMetrics,
    MovingAverageMetrics,
    RSIMetrics,
    SupportResistanceMetrics,
    TechnicalAnalysis,
    TrendMetrics,
    VolumeMetrics,
)
from app.tools.technical_indicators import (
    calculate_atr,
    calculate_bollinger_bands,
    calculate_ema,
    calculate_macd,
    calculate_price_position,
    calculate_rsi,
    calculate_sma,
    calculate_support_resistance,
    calculate_support_resistance_position,
    interpret_macd,
    interpret_rsi,
)


def _interpret_bbands(price: float, bands: dict) -> tuple[float | None, str]:
    upper, lower = bands.get("upper"), bands.get("lower")
    if upper is None or lower is None or upper == lower:
        return None, "Insufficient Data"
    percent_b = (price - lower) / (upper - lower)
    if percent_b >= 1:
        label = "Above upper band (stretched / strong momentum)"
    elif percent_b <= 0:
        label = "Below lower band (stretched / weak momentum)"
    elif percent_b >= 0.8:
        label = "Near upper band"
    elif percent_b <= 0.2:
        label = "Near lower band"
    else:
        label = "Within bands"
    return round(percent_b, 3), label


def run_technical_agent(
    security: CanonicalSecurity,
    history: PriceHistory,
    period: str = "",
) -> TechnicalAnalysis:
    frame = price_history_to_frame(history)
    result = TechnicalAnalysis(
        symbol=security.symbol,
        company_name=security.company_name,
        currency=history.currency or security.currency,
        bars_analyzed=len(frame),
        period=period,
    )

    if len(frame) < 20:
        result.overall_signal = "Insufficient Data"
        result.signal_reasons = ["Fewer than 20 price bars available."]
        return result

    close = frame["Close"]
    price = float(close.iloc[-1])
    result.current_price = price

    sma_20 = calculate_sma(frame, 20)
    sma_50 = calculate_sma(frame, 50)
    sma_200 = calculate_sma(frame, 200)
    ema_20 = calculate_ema(frame, 20)
    ema_50 = calculate_ema(frame, 50)
    result.moving_averages = MovingAverageMetrics(
        sma_20=sma_20, sma_50=sma_50, sma_200=sma_200, ema_20=ema_20, ema_50=ema_50
    )

    rsi_value = calculate_rsi(frame, 14)
    result.rsi = RSIMetrics(value=rsi_value, interpretation=interpret_rsi(rsi_value))

    macd_data = calculate_macd(frame)
    result.macd = MACDMetrics(
        macd=macd_data["macd"], signal=macd_data["signal"], histogram=macd_data["histogram"],
        interpretation=interpret_macd(macd_data["macd"], macd_data["signal"]),
    )

    bands = calculate_bollinger_bands(frame)
    percent_b, bb_label = _interpret_bbands(price, bands)
    result.bollinger_bands = BollingerBandMetrics(
        upper=bands["upper"], middle=bands["middle"], lower=bands["lower"],
        percent_b=percent_b, interpretation=bb_label,
    )

    atr_value = calculate_atr(frame, 14)
    result.atr = ATRMetrics(
        value=atr_value,
        percent_of_price=round(atr_value / price, 4) if atr_value else None,
    )

    sr = calculate_support_resistance(frame, lookback=60)
    result.support_resistance = SupportResistanceMetrics(
        support=sr["support"],
        resistance=sr["resistance"],
        position=calculate_support_resistance_position(price, sr["support"], sr["resistance"]),
    )

    # Trend
    price_position = calculate_price_position(frame, sma_20, sma_50, sma_200)
    short_term = _cross_label(sma_20, sma_50)
    long_term = _cross_label(sma_50, sma_200)
    result.trend = TrendMetrics(
        price_position=price_position,
        short_term=short_term,
        long_term=long_term,
        description=(
            f"Price is {price_position.lower()} relative to its moving averages; "
            f"short-term trend {short_term.lower()}, long-term trend {long_term.lower()}."
        ),
    )

    # Volume
    if "Volume" in frame.columns and frame["Volume"].tail(20).sum() > 0:
        latest_vol = float(frame["Volume"].iloc[-1])
        avg_vol = float(frame["Volume"].tail(20).mean())
        ratio = latest_vol / avg_vol if avg_vol else None
        vol_label = "Insufficient Data"
        if ratio is not None:
            vol_label = (
                "Above-average volume" if ratio >= 1.3
                else "Below-average volume" if ratio <= 0.7
                else "Average volume"
            )
        result.volume = VolumeMetrics(
            latest_volume=latest_vol, average_volume_20=avg_vol,
            volume_ratio=round(ratio, 2) if ratio else None, interpretation=vol_label,
        )

    # Momentum (10-day rate of change)
    if len(close) > 10:
        roc = (price / float(close.iloc[-11]) - 1) if float(close.iloc[-11]) else 0.0
        result.momentum = (
            "Strong Positive" if roc > 0.05 else "Positive" if roc > 0.01
            else "Strong Negative" if roc < -0.05 else "Negative" if roc < -0.01
            else "Flat"
        )

    result.overall_signal, result.signal_reasons = _overall_signal(result)
    return result


def _cross_label(fast: float | None, slow: float | None) -> str:
    if fast is None or slow is None:
        return "Insufficient Data"
    if fast > slow * 1.005:
        return "Uptrend"
    if fast < slow * 0.995:
        return "Downtrend"
    return "Sideways"


def _overall_signal(r: TechnicalAnalysis) -> tuple[str, list[str]]:
    bull = 0
    bear = 0
    reasons: list[str] = []

    tp = r.trend.price_position
    if tp == "Bullish":
        bull += 1
        reasons.append("Price above key moving averages.")
    elif tp == "Bearish":
        bear += 1
        reasons.append("Price below key moving averages.")

    if r.trend.long_term == "Uptrend":
        bull += 1
        reasons.append("50-day SMA above 200-day SMA (long-term uptrend).")
    elif r.trend.long_term == "Downtrend":
        bear += 1
        reasons.append("50-day SMA below 200-day SMA (long-term downtrend).")

    rsi_i = r.rsi.interpretation
    if rsi_i == "Bullish Momentum":
        bull += 1
        reasons.append(f"RSI {r.rsi.value:.0f} shows bullish momentum.")
    elif rsi_i == "Oversold":
        reasons.append(f"RSI {r.rsi.value:.0f} is oversold (potential mean reversion).")
    elif rsi_i in {"Bearish Momentum", "Overbought"}:
        bear += 1
        reasons.append(f"RSI {r.rsi.value:.0f} shows {rsi_i.lower()}.")

    mi = r.macd.interpretation
    if mi in {"Bullish", "Bullish Crossover"}:
        bull += 1
        reasons.append(f"MACD is {mi.lower()}.")
    elif mi in {"Bearish", "Bearish Crossover"}:
        bear += 1
        reasons.append(f"MACD is {mi.lower()}.")

    if r.momentum in {"Positive", "Strong Positive"}:
        bull += 1
    elif r.momentum in {"Negative", "Strong Negative"}:
        bear += 1

    if bull - bear >= 2:
        return "Bullish", reasons
    if bear - bull >= 2:
        return "Bearish", reasons
    return "Neutral", reasons or ["Mixed technical signals."]
