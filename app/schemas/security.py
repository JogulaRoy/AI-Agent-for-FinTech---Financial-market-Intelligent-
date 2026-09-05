"""Canonical security identity produced by the resolver."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class SecurityCandidate(BaseModel):
    """One possible match for a user query, before disambiguation."""

    company_name: str
    symbol: str
    exchange: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = None
    isin: Optional[str] = None
    asset_type: Optional[str] = "EQUITY"
    source: str = ""
    score: float = 0.0
    # Provider-specific identifiers discovered during resolution, e.g.
    # {"fmp": "TCS.NS", "eodhd": "TCS.NSE", "twelve_data": "TCS:NSE", "yfinance": "TCS.NS"}
    provider_symbols: dict[str, str] = Field(default_factory=dict)


class CanonicalSecurity(BaseModel):
    """
    The single, stable identity every downstream agent references.

    Provider-specific ticker formats live in ``provider_symbols`` and are an
    internal detail — the rest of the system only knows this object.
    """

    company_name: str
    symbol: str                       # canonical display symbol (e.g. "TCS", "AAPL")
    exchange: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = None
    isin: Optional[str] = None
    asset_type: str = "EQUITY"

    provider_symbols: dict[str, str] = Field(default_factory=dict)

    resolved_by: str = ""             # provider/source that produced this identity
    confidence: float = 0.0
    alternatives: list[SecurityCandidate] = Field(default_factory=list)
    query: str = ""

    def symbol_for(self, provider: str) -> Optional[str]:
        """Provider-specific ticker, falling back to the canonical symbol."""
        return self.provider_symbols.get(provider) or self.symbol

    @property
    def is_indian(self) -> bool:
        return (self.country or "").lower() in {"india", "in"} or (
            (self.exchange or "").upper() in {"NSE", "BSE", "NSI", "BOM"}
        )
