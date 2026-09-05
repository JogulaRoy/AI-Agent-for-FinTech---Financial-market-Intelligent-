"""Market benchmark history for beta calculations."""

from __future__ import annotations

from typing import Optional

from app.config.settings import settings
from app.schemas.market_data import PriceHistory
from app.schemas.security import CanonicalSecurity

# Index -> (display name, yahoo symbol)
_BENCHMARKS = {
    "IN": ("NIFTY 50", "^NSEI"),
    "US": ("S&P 500", "^GSPC"),
}


def get_benchmark(security: CanonicalSecurity, period: str = "5y") -> tuple[Optional[str], Optional[PriceHistory]]:
    if not settings.enable_yfinance_fallback:
        return None, None
    market = "IN" if security.is_indian else "US"
    name, ysym = _BENCHMARKS[market]
    try:
        from app.data.providers.yfinance_provider import YFinanceProvider

        proxy = CanonicalSecurity(
            company_name=name, symbol=ysym, exchange=None, country=None,
            currency=None, provider_symbols={"yfinance": ysym},
        )
        history = YFinanceProvider().get_history(proxy, period)
        return name, history
    except Exception:  # noqa: BLE001
        return name, None
