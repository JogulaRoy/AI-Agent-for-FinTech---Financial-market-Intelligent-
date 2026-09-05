import pandas as pd

from app.data.normalizer import price_history_to_frame
from app.schemas.market_data import OHLCVBar, PriceHistory


def _history(rows):
    return PriceHistory(bars=[OHLCVBar(**r) for r in rows])


def test_frame_has_expected_columns_and_sorted_index():
    history = _history([
        {"date": "2024-01-03", "open": 3, "high": 3.5, "low": 2.9, "close": 3.2, "volume": 10},
        {"date": "2024-01-01", "open": 1, "high": 1.5, "low": 0.9, "close": 1.2, "volume": 5},
        {"date": "2024-01-02", "open": 2, "high": 2.5, "low": 1.9, "close": 2.2, "volume": 7},
    ])
    frame = price_history_to_frame(history)
    assert list(frame.columns) == ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
    assert list(frame.index) == sorted(frame.index)
    assert isinstance(frame.index, pd.DatetimeIndex)
    assert frame["Close"].iloc[-1] == 3.2


def test_empty_history_returns_empty_frame():
    frame = price_history_to_frame(PriceHistory(bars=[]))
    assert frame.empty


def test_duplicate_dates_collapsed_keeping_last():
    history = _history([
        {"date": "2024-01-01", "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1},
        {"date": "2024-01-01", "open": 2, "high": 2, "low": 2, "close": 9, "volume": 1},
    ])
    frame = price_history_to_frame(history)
    assert len(frame) == 1
    assert frame["Close"].iloc[0] == 9
