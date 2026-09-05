"""
Central configuration.

All secrets and tunables are read from environment variables (loaded from a
local .env file). Nothing sensitive is ever hardcoded here.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


# Load .env from the project root regardless of the current working directory.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_PROJECT_ROOT / ".env")


def _get(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


def _get_bool(name: str, default: bool = False) -> bool:
    raw = _get(name).lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def _get_float(name: str, default: float) -> float:
    try:
        return float(_get(name) or default)
    except (TypeError, ValueError):
        return default


def _get_int(name: str, default: int) -> int:
    try:
        return int(_get(name) or default)
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class Settings:
    # --- Provider API keys ---
    eodhd_api_key: str = field(default_factory=lambda: _get("EODHD_API_KEY"))
    fmp_api_key: str = field(default_factory=lambda: _get("FMP_API_KEY"))
    twelve_data_api_key: str = field(default_factory=lambda: _get("TWELVE_DATA_API_KEY"))
    alpha_vantage_api_key: str = field(default_factory=lambda: _get("ALPHA_VANTAGE_API_KEY"))

    # --- LLM ---
    llm_provider: str = field(default_factory=lambda: _get("LLM_PROVIDER", "gemini").lower())
    llm_api_key: str = field(default_factory=lambda: _get("LLM_API_KEY"))
    llm_model: str = field(default_factory=lambda: _get("LLM_MODEL", "gemini-flash-latest"))

    # --- Behaviour ---
    enable_yfinance_fallback: bool = field(
        default_factory=lambda: _get_bool("ENABLE_YFINANCE_FALLBACK", True)
    )
    cache_ttl_seconds: int = field(default_factory=lambda: _get_int("CACHE_TTL_SECONDS", 900))
    risk_free_rate: float = field(default_factory=lambda: _get_float("RISK_FREE_RATE", 0.0))

    # --- Paths ---
    project_root: Path = field(default_factory=lambda: _PROJECT_ROOT)
    cache_db_path: Path = field(default_factory=lambda: _PROJECT_ROOT / ".cache" / "data_cache.db")

    # --- Derived helpers ---------------------------------------------------

    def has_llm(self) -> bool:
        return bool(self.llm_api_key)

    def configured_providers(self) -> list[str]:
        names: list[str] = []
        if self.fmp_api_key:
            names.append("fmp")
        if self.twelve_data_api_key:
            names.append("twelve_data")
        if self.eodhd_api_key:
            names.append("eodhd")
        if self.enable_yfinance_fallback:
            names.append("yfinance")
        return names

    def missing_keys(self) -> list[str]:
        missing = []
        for label, value in (
            ("EODHD_API_KEY", self.eodhd_api_key),
            ("FMP_API_KEY", self.fmp_api_key),
            ("TWELVE_DATA_API_KEY", self.twelve_data_api_key),
            ("LLM_API_KEY", self.llm_api_key),
        ):
            if not value:
                missing.append(label)
        return missing


settings = Settings()
