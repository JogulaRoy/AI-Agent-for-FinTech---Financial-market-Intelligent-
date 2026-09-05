"""
Data Agent.

The foundation of the system. It turns a canonical security into accurate,
structured, provenance-tagged market data + fundamentals + a transparent
financial-health score. It performs no interpretation or advice.
"""

from __future__ import annotations

from typing import Optional

from app.analysis.fundamentals import assess_financial_health
from app.data.normalizer import price_history_to_frame
from app.data.provider_manager import ProviderManager, get_provider_manager
from app.data.resolver import resolve_security
from app.data.validator import validate_price_history
from app.schemas.fundamentals import Fundamentals
from app.schemas.market_data import (
    CompanyProfile,
    DataAgentResult,
    DataQualityReport,
    PerformanceMetrics,
    PriceHistory,
    Quote,
    StabilityMetrics,
)
from app.schemas.security import CanonicalSecurity
from app.tools.market_metrics import (
    calculate_annualized_volatility,
    calculate_average_daily_return,
    calculate_best_day,
    calculate_daily_return,
    calculate_downside_volatility,
    calculate_maximum_drawdown,
    calculate_monthly_return,
    calculate_negative_days_ratio,
    calculate_one_year_return,
    calculate_positive_days_ratio,
    calculate_six_month_return,
    calculate_worst_day,
    classify_stability,
)


class DataAgentError(RuntimeError):
    pass


def run_data_agent(
    security_or_query: CanonicalSecurity | str,
    period: str = "5y",
    manager: Optional[ProviderManager] = None,
) -> DataAgentResult:
    manager = manager or get_provider_manager()

    if isinstance(security_or_query, str):
        security = resolve_security(security_or_query, manager)
    else:
        security = security_or_query

    warnings: list[str] = []
    sources: set[str] = set()

    # --- history (required) ---------------------------------------
    hist_outcome = manager.get_history(security, period)
    if not hist_outcome.ok:
        raise DataAgentError(
            f"No historical price data for {security.company_name} "
            f"({security.symbol}). Tried: {', '.join(hist_outcome.attempts)}"
        )
    history: PriceHistory = hist_outcome.value  # type: ignore[assignment]
    sources.add(hist_outcome.provider or "")
    history, quality = validate_price_history(history)
    if not quality.passed:
        raise DataAgentError(
            f"Historical data for {security.symbol} failed validation: {quality.issues}"
        )
    if quality.rows_removed:
        warnings.append(
            f"{quality.rows_removed} price row(s) removed during validation."
        )

    frame = price_history_to_frame(history)

    # --- quote (best effort) -------------------------------------
    quote_outcome = manager.get_quote(security)
    if quote_outcome.ok:
        quote: Quote = quote_outcome.value  # type: ignore[assignment]
        sources.add(quote_outcome.provider or "")
    else:
        last = history.bars[-1]
        prev = history.bars[-2].close if len(history.bars) > 1 else None
        quote = Quote(
            price=last.close, open=last.open, high=last.high, low=last.low,
            close=last.close, previous_close=prev,
            change=(last.close - prev) if prev else None,
            change_percent=((last.close - prev) / prev) if prev else None,
            volume=last.volume, currency=security.currency, timestamp=last.date,
        )
        warnings.append("Live quote unavailable; using latest close from history.")
    if not quote.currency:
        quote.currency = security.currency

    # --- profile (best effort) ----------------------------------
    profile_outcome = manager.get_profile(security)
    if profile_outcome.ok:
        profile: CompanyProfile = profile_outcome.value  # type: ignore[assignment]
        sources.add(profile_outcome.provider or "")
    else:
        profile = CompanyProfile(
            company_name=security.company_name,
            symbol=security.symbol,
            exchange=security.exchange,
            country=security.country,
            currency=security.currency,
            isin=security.isin,
        )
        warnings.append("Detailed company profile unavailable from the configured providers.")
    # fill identity gaps from the canonical security
    profile.isin = profile.isin or security.isin
    profile.country = profile.country or security.country
    profile.currency = profile.currency or security.currency or quote.currency

    # --- fundamentals (best effort) ---------------------------
    fundamentals = _load_fundamentals(security, manager, sources, warnings)

    # --- derived metrics --------------------------------------
    performance = PerformanceMetrics(
        daily_return=calculate_daily_return(frame),
        monthly_return=calculate_monthly_return(frame),
        six_month_return=calculate_six_month_return(frame),
        one_year_return=calculate_one_year_return(frame),
    )
    ann_vol = calculate_annualized_volatility(frame)
    max_dd = calculate_maximum_drawdown(frame)
    stability = StabilityMetrics(
        annualized_volatility=ann_vol,
        downside_volatility=calculate_downside_volatility(frame),
        maximum_drawdown=max_dd,
        positive_days_ratio=calculate_positive_days_ratio(frame),
        negative_days_ratio=calculate_negative_days_ratio(frame),
        average_daily_return=calculate_average_daily_return(frame),
        best_day=calculate_best_day(frame),
        worst_day=calculate_worst_day(frame),
        classification=classify_stability(ann_vol, max_dd),
    )

    # financial health uses fundamentals + price stability together
    fundamentals.health = assess_financial_health(
        fundamentals, annualized_volatility=ann_vol, maximum_drawdown=max_dd
    )

    quality = DataQualityReport(**{
        **quality.model_dump(),
        "issues": quality.issues + (
            ["52-week high/low missing"] if quote.week52_high is None else []
        ),
    })

    return DataAgentResult(
        profile=profile,
        quote=quote,
        history=history,
        fundamentals=fundamentals,
        performance=performance,
        stability=stability,
        data_quality=quality,
        requested_period=period,
        sources_used=sorted(s for s in sources if s),
        warnings=warnings,
    )


def _load_fundamentals(
    security: CanonicalSecurity,
    manager: ProviderManager,
    sources: set[str],
    warnings: list[str],
) -> Fundamentals:
    outcome = manager.get_fundamentals(security)
    if outcome.ok:
        fundamentals: Fundamentals = outcome.value  # type: ignore[assignment]
        sources.add(outcome.provider or "")
        return fundamentals

    reason = "Fundamental statements are not available for this security on the "
    if security.is_indian:
        reason += "free API tier (Indian equities need a paid data plan)."
    else:
        reason += "configured providers/plan."
    warnings.append(reason)
    return Fundamentals(available=False, unavailable_reason=reason)
