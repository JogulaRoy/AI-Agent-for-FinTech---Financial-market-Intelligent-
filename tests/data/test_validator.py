from app.data.validator import validate_price_history
from app.schemas.market_data import OHLCVBar, PriceHistory


def _hist(bars):
    return PriceHistory(bars=[OHLCVBar(**b) for b in bars])


def test_drops_nonpositive_and_impossible_rows():
    history = _hist([
        {"date": "2024-01-01", "open": 10, "high": 11, "low": 9, "close": 10, "volume": 1},
        {"date": "2024-01-02", "open": 0, "high": 1, "low": 0, "close": 0, "volume": 1},       # non-positive
        {"date": "2024-01-03", "open": 10, "high": 8, "low": 12, "close": 10, "volume": 1},    # high < low
        {"date": "2024-01-04", "open": 10, "high": 11, "low": 9, "close": 10.5, "volume": 1},
        {"date": "2024-01-04", "open": 10, "high": 11, "low": 9, "close": 10.5, "volume": 1},  # duplicate
    ])
    clean, report = validate_price_history(history)
    assert report.rows_returned == 2
    assert report.rows_removed == 3
    assert report.passed
    assert len(report.issues) == 3


def test_ordering_is_corrected():
    history = _hist([
        {"date": "2024-01-05", "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1},
        {"date": "2024-01-01", "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1},
    ])
    clean, report = validate_price_history(history)
    assert [b.date for b in clean.bars] == ["2024-01-01", "2024-01-05"]


def test_fails_when_too_few_valid_bars():
    history = _hist([
        {"date": "2024-01-01", "open": 10, "high": 11, "low": 9, "close": 10, "volume": 1},
    ])
    _clean, report = validate_price_history(history)
    assert not report.passed
