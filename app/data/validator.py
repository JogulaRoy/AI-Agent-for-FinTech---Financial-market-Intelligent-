"""Data-quality checks for normalized price history.

The goal is to never silently pass bad data downstream. Problems are either
repaired (and reported) or flagged.
"""

from __future__ import annotations

from app.schemas.market_data import DataQualityReport, OHLCVBar, PriceHistory


def validate_price_history(history: PriceHistory) -> tuple[PriceHistory, DataQualityReport]:
    issues: list[str] = []
    original = len(history.bars)

    clean: list[OHLCVBar] = []
    seen_dates: set[str] = set()

    for bar in history.bars:
        # Missing / non-positive prices.
        if any(v is None for v in (bar.open, bar.high, bar.low, bar.close)):
            issues.append(f"{bar.date}: missing price field")
            continue
        if min(bar.open, bar.high, bar.low, bar.close) <= 0:
            issues.append(f"{bar.date}: non-positive price")
            continue
        # Impossible OHLC relationships.
        if bar.high < bar.low:
            issues.append(f"{bar.date}: high < low")
            continue
        if bar.high < max(bar.open, bar.close) or bar.low > min(bar.open, bar.close):
            # tolerate tiny float noise
            if bar.high < max(bar.open, bar.close) - 1e-6 or bar.low > min(bar.open, bar.close) + 1e-6:
                issues.append(f"{bar.date}: OHLC out of range")
                continue
        # Duplicate dates.
        if bar.date in seen_dates:
            issues.append(f"{bar.date}: duplicate date")
            continue
        seen_dates.add(bar.date)
        if bar.volume is None or bar.volume < 0:
            bar.volume = 0.0
        clean.append(bar)

    clean.sort(key=lambda b: b.date)

    # Ordering / gap sanity.
    if len(clean) < 2:
        issues.append("fewer than 2 valid bars")

    dates = [b.date for b in clean]
    if dates != sorted(dates):
        issues.append("date ordering was corrected")

    removed = original - len(clean)
    report = DataQualityReport(
        rows_returned=len(clean),
        rows_removed=removed,
        start_date=clean[0].date if clean else None,
        end_date=clean[-1].date if clean else None,
        issues=issues[:50],
        passed=len(clean) >= 2,
    )

    cleaned = history.model_copy(update={
        "bars": clean,
        "start_date": report.start_date,
        "end_date": report.end_date,
    })
    return cleaned, report
