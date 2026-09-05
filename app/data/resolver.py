"""
Security resolver.

Turns free-text ("TCS", "tata consultancy services", "AAPL", "Apple") into one
:class:`CanonicalSecurity`. It never hardcodes company->ticker maps: candidates
come from provider search endpoints and the public NSE security master, then a
transparent scorer picks the best and merges provider-specific identifiers.
"""

from __future__ import annotations

import re

from app.data.provider_manager import ProviderManager, get_provider_manager
from app.schemas.security import CanonicalSecurity, SecurityCandidate
from app.tools.indian_security_master import search_indian_equity

_INDIA_EXCH = {"NSE", "BSE", "NSI", "BOM"}
_PRIMARY_EXCH = {"NASDAQ", "NYSE", "NMS", "NGM", "NSE", "BSE"}
_SECONDARY_EXCH = {"LSE", "TSX", "ASX", "AMEX", "PCX"}
_SUFFIXES = {
    "INC", "INCORPORATED", "CORP", "CORPORATION", "CO", "COMPANY", "LTD",
    "LIMITED", "PLC", "LLC", "LP", "AG", "SA", "NV", "GROUP", "HOLDING",
    "HOLDINGS", "CLASS", "THE",
}


def _normalize(text: str) -> str:
    if not text or not text.strip():
        raise ValueError("Stock name or symbol cannot be empty.")
    return re.sub(r"\s+", " ", text.strip())


def _canonical_name(name: str) -> str:
    tokens = re.findall(r"[A-Za-z0-9]+", (name or "").upper())
    kept = [t for t in tokens if t not in _SUFFIXES]
    return " ".join(kept or tokens)


def _clean_symbol(symbol: str) -> str:
    return (symbol or "").upper().split(".")[0]


def _fill_provider_symbols(
    merged: dict[str, str], rep: SecurityCandidate
) -> dict[str, str]:
    """Guarantee every provider has a sensible ticker for the chosen identity."""
    symbol = _clean_symbol(rep.symbol)
    exch = (rep.exchange or "").upper()
    is_indian = exch in _INDIA_EXCH or (rep.country or "").lower() in {"india", "in"}
    result = dict(merged)
    if is_indian:
        suffix = ".BO" if exch in {"BSE", "BOM"} else ".NS"
        eod_suffix = ".BSE" if exch in {"BSE", "BOM"} else ".NSE"
        result.setdefault("yfinance", f"{symbol}{suffix}")
        result.setdefault("fmp", f"{symbol}{suffix}")
        result.setdefault("eodhd", f"{symbol}{eod_suffix}")
        result.setdefault("twelve_data", symbol)
    elif exch in _PRIMARY_EXCH or (rep.country or "").upper() in {"USA", "US", "UNITED STATES"}:
        # US tickers are uniform across providers; override any foreign-listing noise.
        for provider in ("yfinance", "fmp", "twelve_data"):
            result[provider] = symbol
        result["eodhd"] = f"{symbol}.US"
    else:
        for provider in ("yfinance", "fmp", "eodhd", "twelve_data"):
            result.setdefault(provider, f"{symbol}.US" if provider == "eodhd" else symbol)
    return result


def _india_candidate(query: str) -> SecurityCandidate | None:
    try:
        hit = search_indian_equity(query)
    except Exception:  # noqa: BLE001
        return None
    if not hit:
        return None
    symbol = hit["symbol"]
    return SecurityCandidate(
        company_name=hit["name"],
        symbol=symbol,
        exchange="NSE",
        country="India",
        currency="INR",
        isin=hit.get("isin") or None,
        source="nse_master",
        provider_symbols={
            "yfinance": f"{symbol}.NS",
            "eodhd": f"{symbol}.NSE",
            "fmp": f"{symbol}.NS",
            "twelve_data": symbol,
        },
    )


def _exchange_bonus(exchange: str | None) -> float:
    exch = (exchange or "").upper()
    if exch in _PRIMARY_EXCH:
        return 14
    if exch in _SECONDARY_EXCH:
        return 5
    return 0


def _is_tickerish(raw_query: str) -> bool:
    """A short, single-token query in ticker-style casing (ALL CAPS, or a very
    short all-lowercase string) — as opposed to a real company word like
    'Apple' or 'Reliance'."""
    q = raw_query.strip()
    if " " in q or "." in q or not 1 <= len(q) <= 6:
        return False
    return q.isupper() or (q.islower() and len(q) <= 4)


_FUND_WORDS = {"FUND", "TRUST", "ETF", "ETN", "INDEX", "SPDR", "ISHARES"}


def _score_member(candidate: SecurityCandidate, query: str, tickerish: bool) -> float:
    q = query.upper().strip()
    sym = candidate.symbol.upper()
    clean = _clean_symbol(sym)
    cname = _canonical_name(candidate.company_name)
    raw_name = (candidate.company_name or "").upper()
    is_fund = any(w in raw_name for w in _FUND_WORDS) or (
        (candidate.asset_type or "").upper() in {"FUND", "ETF", "MUTUALFUND", "MUTUAL FUND"}
    )
    from_nse = "nse_master" in candidate.source
    score = 0.0

    if q == sym and "." not in sym:
        score += 90 if is_fund else 120
    elif q == clean:
        score += 85
    elif clean.startswith(q):
        # Indian users routinely abbreviate (SBI->SBIN, M&M->M&M, LT->LT). Trust
        # the authoritative NSE master when its symbol extends the query.
        score += 60 if from_nse else 35

    if "." in sym and "." not in q:
        score -= 12

    if is_fund:
        score -= 45

    # A short all-caps query that happens to equal a company's whole (suffix-
    # stripped) name is almost always a coincidental ticker collision, so the
    # name match earns nothing in that case.
    name_weight = 0.0 if (tickerish and len(cname) <= 5) else (0.5 if tickerish else 1.0)
    if q == cname:
        score += 110 * name_weight
    elif cname.startswith(q):
        score += 45 * name_weight
    elif q in cname:
        score += 18 * name_weight

    q_tokens = set(re.findall(r"[A-Z0-9]+", q))
    n_tokens = set(re.findall(r"[A-Z0-9]+", cname))
    if q_tokens and not tickerish:
        score += 30 * len(q_tokens & n_tokens) / len(q_tokens)

    if not is_fund and (candidate.asset_type or "EQUITY").upper() in {"EQUITY", "COMMON STOCK"}:
        score += 8
    if candidate.isin:
        score += 6
    if from_nse:
        score += 18
    score += _exchange_bonus(candidate.exchange)
    return score


def _member_rank(candidate: SecurityCandidate, score: float, query: str) -> tuple:
    q = query.upper()
    return (
        round(score, 1),
        _exchange_bonus(candidate.exchange),
        _clean_symbol(candidate.symbol) == q,
        "." not in candidate.symbol,
        -len(candidate.symbol),
    )


class _Group:
    def __init__(self, candidate: SecurityCandidate, score: float, query: str, tickerish: bool):
        self.query = query
        self.tickerish = tickerish
        self.members: list[tuple[SecurityCandidate, float]] = [(candidate, score)]
        self.sources: set[str] = set(s for s in candidate.source.split(",") if s)

    def add(self, candidate: SecurityCandidate, score: float) -> None:
        self.members.append((candidate, score))
        self.sources.update(s for s in candidate.source.split(",") if s)

    @property
    def rep(self) -> SecurityCandidate:
        return max(
            self.members, key=lambda ms: _member_rank(ms[0], ms[1], self.query)
        )[0]

    @property
    def best_score(self) -> float:
        return max(s for _, s in self.members)

    @property
    def final_score(self) -> float:
        per_source = 16.0 if self.tickerish else 8.0
        cap = 55.0 if self.tickerish else 30.0
        return self.best_score + min(cap, per_source * (len(self.sources) - 1))

    def provider_symbols(self) -> dict[str, str]:
        rep = self.rep
        rep_exch = (rep.exchange or "").upper()
        rep_country = (rep.country or "").lower()

        def match_rank(member: SecurityCandidate) -> tuple:
            return (
                (member.exchange or "").upper() == rep_exch,
                (member.country or "").lower() == rep_country,
                "nse_master" in member.source,
                "." not in member.symbol,
            )

        merged: dict[str, str] = {}
        for member, _ in sorted(
            self.members, key=lambda ms: match_rank(ms[0]), reverse=True
        ):
            for provider, sym in member.provider_symbols.items():
                merged.setdefault(provider, sym)
        return _fill_provider_symbols(merged, rep)


def resolve_security(
    user_query: str, manager: ProviderManager | None = None
) -> CanonicalSecurity:
    query = _normalize(user_query)
    tickerish = _is_tickerish(query)
    manager = manager or get_provider_manager()

    raw: list[SecurityCandidate] = []
    india = _india_candidate(query)
    if india:
        raw.append(india)
    provider_hits, _attempts = manager.search_all(query)
    raw.extend(provider_hits)

    if not raw:
        raise ValueError(
            f"Could not find any security matching '{user_query}'. "
            "Try a ticker symbol or the full company name."
        )

    groups: dict[str, _Group] = {}
    for cand in raw:
        score = _score_member(cand, query, tickerish)
        gkey = _canonical_name(cand.company_name) or _clean_symbol(cand.symbol)
        if gkey in groups:
            groups[gkey].add(cand, score)
        else:
            groups[gkey] = _Group(cand, score, query, tickerish)

    ranked = sorted(groups.values(), key=lambda g: g.final_score, reverse=True)
    best = ranked[0]

    runner = ranked[1].final_score if len(ranked) > 1 else 0.0
    spread = best.final_score - runner
    confidence = 0.5 + min(0.45, spread / 120) if best.final_score >= 45 else 0.4

    rep = best.rep
    alternatives = [
        SecurityCandidate(
            company_name=g.rep.company_name,
            symbol=_clean_symbol(g.rep.symbol),
            exchange=g.rep.exchange,
            country=g.rep.country,
            currency=g.rep.currency,
            isin=g.rep.isin,
            source=",".join(sorted(s for s in g.sources if s)),
            score=round(g.final_score, 1),
        )
        for g in ranked[1:5]
    ]

    return CanonicalSecurity(
        company_name=rep.company_name,
        symbol=_clean_symbol(rep.symbol),
        exchange=rep.exchange,
        country=rep.country,
        currency=rep.currency
        or ("INR" if (rep.exchange or "").upper() in _INDIA_EXCH else None),
        isin=rep.isin,
        asset_type=rep.asset_type or "EQUITY",
        provider_symbols=best.provider_symbols(),
        resolved_by=",".join(sorted(s for s in best.sources if s)),
        confidence=round(confidence, 2),
        alternatives=alternatives,
        query=query,
    )
