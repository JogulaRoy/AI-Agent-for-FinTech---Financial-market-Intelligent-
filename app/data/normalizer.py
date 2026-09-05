"""Adapters between the provider-neutral schemas and pandas."""

from __future__ import annotations

import pandas as pd

from app.schemas.market_data import PriceHistory


def price_history_to_frame(history: PriceHistory) -> pd.DataFrame:
    """
    Convert a :class:`PriceHistory` into the OHLCV DataFrame shape the existing
    calculation tools expect: a ``DatetimeIndex`` and ``Open/High/Low/Close/
    Volume`` columns (plus ``Adj Close`` when available).
    """
    if not history.bars:
        return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])

    rows = []
    index = []
    for bar in history.bars:
        index.append(pd.Timestamp(bar.date))
        rows.append(
            {
                "Open": bar.open,
                "High": bar.high,
                "Low": bar.low,
                "Close": bar.close,
                "Adj Close": bar.adjusted_close if bar.adjusted_close is not None else bar.close,
                "Volume": bar.volume or 0.0,
            }
        )
    frame = pd.DataFrame(rows, index=pd.DatetimeIndex(index, name="Date"))
    frame = frame[~frame.index.duplicated(keep="last")].sort_index()
    return frame
