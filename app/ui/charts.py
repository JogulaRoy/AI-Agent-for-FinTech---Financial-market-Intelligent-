"""Plotly chart builders for the dashboard."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from app.data.normalizer import price_history_to_frame
from app.schemas.market_data import PriceHistory
from app.schemas.technical_data import TechnicalAnalysis

_GRID = "rgba(128,128,128,0.15)"
_UP = "#16a34a"
_DOWN = "#dc2626"


def _base_layout(fig: go.Figure, height: int) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        xaxis=dict(gridcolor=_GRID, rangeslider=dict(visible=False)),
        yaxis=dict(gridcolor=_GRID),
        hovermode="x unified",
    )
    return fig


def price_chart(history: PriceHistory, technical: TechnicalAnalysis | None) -> go.Figure:
    frame = price_history_to_frame(history)
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04,
        row_heights=[0.72, 0.28], subplot_titles=("Price", "Volume"),
    )
    fig.add_trace(
        go.Candlestick(
            x=frame.index, open=frame["Open"], high=frame["High"],
            low=frame["Low"], close=frame["Close"], name="OHLC",
            increasing_line_color=_UP, decreasing_line_color=_DOWN,
        ),
        row=1, col=1,
    )
    for window, color in ((20, "#3b82f6"), (50, "#f59e0b"), (200, "#8b5cf6")):
        if len(frame) >= window:
            fig.add_trace(
                go.Scatter(
                    x=frame.index, y=frame["Close"].rolling(window).mean(),
                    name=f"SMA {window}", line=dict(width=1.2, color=color),
                ),
                row=1, col=1,
            )
    if technical and technical.support_resistance.support:
        fig.add_hline(
            y=technical.support_resistance.support, line=dict(color=_UP, dash="dot", width=1),
            annotation_text="support (approx)", row=1, col=1,
        )
    if technical and technical.support_resistance.resistance:
        fig.add_hline(
            y=technical.support_resistance.resistance, line=dict(color=_DOWN, dash="dot", width=1),
            annotation_text="resistance (approx)", row=1, col=1,
        )
    colors = [
        _UP if c >= o else _DOWN
        for o, c in zip(frame["Open"], frame["Close"])
    ]
    fig.add_trace(
        go.Bar(x=frame.index, y=frame["Volume"], name="Volume", marker_color=colors, opacity=0.5),
        row=2, col=1,
    )
    return _base_layout(fig, 520)


def rsi_macd_chart(history: PriceHistory) -> go.Figure:
    frame = price_history_to_frame(history)
    close = frame["Close"]

    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    rsi = 100 - 100 / (1 + gain / loss.replace(0, pd.NA))

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
        subplot_titles=("RSI (14, Wilder)", "MACD (12, 26, 9)"),
    )
    fig.add_trace(go.Scatter(x=frame.index, y=rsi, name="RSI", line=dict(color="#6366f1")), row=1, col=1)
    fig.add_hline(y=70, line=dict(color=_DOWN, dash="dash", width=1), row=1, col=1)
    fig.add_hline(y=30, line=dict(color=_UP, dash="dash", width=1), row=1, col=1)
    fig.update_yaxes(range=[0, 100], row=1, col=1)

    fig.add_trace(go.Bar(
        x=frame.index, y=hist, name="Histogram",
        marker_color=[_UP if v >= 0 else _DOWN for v in hist.fillna(0)], opacity=0.5,
    ), row=2, col=1)
    fig.add_trace(go.Scatter(x=frame.index, y=macd, name="MACD", line=dict(color="#3b82f6")), row=2, col=1)
    fig.add_trace(go.Scatter(x=frame.index, y=signal, name="Signal", line=dict(color="#f59e0b")), row=2, col=1)
    return _base_layout(fig, 420)


def health_gauge(score: float | None, classification: str) -> go.Figure:
    value = score if score is not None else 0
    color = {"Strong": _UP, "Moderate": "#f59e0b", "Weak": _DOWN}.get(classification, "#9ca3af")
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number=dict(suffix=" / 100", font=dict(size=26)),
        gauge=dict(
            axis=dict(range=[0, 100], tickwidth=1),
            bar=dict(color=color),
            steps=[
                dict(range=[0, 45], color="rgba(220,38,38,0.15)"),
                dict(range=[45, 70], color="rgba(245,158,11,0.15)"),
                dict(range=[70, 100], color="rgba(22,163,74,0.15)"),
            ],
        ),
        title=dict(text=f"Financial Health: <b>{classification}</b>", font=dict(size=15)),
    ))
    fig.update_layout(height=260, margin=dict(l=20, r=20, t=50, b=10),
                      paper_bgcolor="rgba(0,0,0,0)", font=dict(size=12))
    return fig


def returns_bar(performance) -> go.Figure:
    labels = ["1D", "1M", "6M", "1Y"]
    values = [
        performance.daily_return, performance.monthly_return,
        performance.six_month_return, performance.one_year_return,
    ]
    pairs = [(l, v * 100) for l, v in zip(labels, values) if v is not None]
    fig = go.Figure(go.Bar(
        x=[p[0] for p in pairs], y=[p[1] for p in pairs],
        marker_color=[_UP if p[1] >= 0 else _DOWN for p in pairs],
        text=[f"{p[1]:+.1f}%" for p in pairs], textposition="outside",
    ))
    fig.update_layout(
        height=260, margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(title="return %", gridcolor=_GRID), xaxis=dict(gridcolor=_GRID),
    )
    return fig
