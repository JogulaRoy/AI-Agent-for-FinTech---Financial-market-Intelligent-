"""Shared HTTP helper: timeouts, retries, cache, and typed errors."""

from __future__ import annotations

import hashlib
import json
import threading
import time
from typing import Any, Optional

import httpx

from app.data.cache import cache

# Minimum spacing between *uncached* calls to the same provider, seconds.
# Keeps the tightest free tiers (e.g. Twelve Data: 8 req/min) from tripping 429s.
_MIN_INTERVAL = {"twelve_data": 1.0, "fmp": 0.25, "eodhd": 0.25}
_last_call: dict[str, float] = {}
_rate_lock = threading.Lock()


def _throttle(provider: str) -> None:
    interval = _MIN_INTERVAL.get(provider)
    if not interval:
        return
    with _rate_lock:
        wait = interval - (time.monotonic() - _last_call.get(provider, 0.0))
        if wait > 0:
            time.sleep(wait)
        _last_call[provider] = time.monotonic()


class ProviderError(RuntimeError):
    """Base class for all provider-layer failures."""


class ProviderAuthError(ProviderError):
    """Invalid / missing API key."""


class ProviderRateLimitError(ProviderError):
    """Provider throttled the request."""


class ProviderUnavailableError(ProviderError):
    """Timeout, connection error, or 5xx."""


class ProviderNotSupported(ProviderError):
    """The provider cannot serve this capability / market."""


class ProviderDataError(ProviderError):
    """Response received but unusable (empty, malformed, 'not found')."""


_DEFAULT_TIMEOUT = 20.0
_RETRYABLE_STATUS = {500, 502, 503, 504}


def _cache_key(method: str, url: str, params: dict[str, Any] | None) -> str:
    raw = json.dumps({"m": method, "u": url, "p": params or {}}, sort_keys=True, default=str)
    return "http:" + hashlib.sha256(raw.encode()).hexdigest()


def request_json(
    url: str,
    *,
    params: Optional[dict[str, Any]] = None,
    method: str = "GET",
    headers: Optional[dict[str, str]] = None,
    timeout: float = _DEFAULT_TIMEOUT,
    retries: int = 2,
    cache_ttl: Optional[int] = None,
    provider: str = "provider",
) -> Any:
    """
    Perform a GET/POST and return parsed JSON.

    Results are cached (keyed by url+params) when ``cache_ttl`` is not 0.
    Raises a subclass of :class:`ProviderError` on any failure.
    """

    key = _cache_key(method, url, params)
    if cache_ttl != 0:
        cached = cache.get(key)
        if cached is not None:
            return cached

    _throttle(provider)

    last_exc: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                response = client.request(method, url, params=params, headers=headers)
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            last_exc = exc
            time.sleep(0.6 * (attempt + 1))
            continue

        if response.status_code in (401, 403):
            # Some providers use 403 for "endpoint not in your plan".
            body = response.text.lower()
            if "legacy" in body or "subscription" in body or "upgrade" in body or "restricted" in body:
                raise ProviderNotSupported(f"{provider}: endpoint not available on this plan")
            raise ProviderAuthError(f"{provider}: authentication failed ({response.status_code})")

        if response.status_code == 429:
            raise ProviderRateLimitError(f"{provider}: rate limit exceeded")

        if response.status_code in _RETRYABLE_STATUS:
            last_exc = ProviderUnavailableError(
                f"{provider}: HTTP {response.status_code}"
            )
            time.sleep(0.6 * (attempt + 1))
            continue

        if response.status_code != 200:
            raise ProviderUnavailableError(f"{provider}: HTTP {response.status_code}")

        text = response.text.strip()
        if not text:
            raise ProviderDataError(f"{provider}: empty response")

        # Providers frequently return a bare error string with HTTP 200.
        lowered = text.lower()
        if text[0] not in "[{":
            if any(t in lowered for t in ("rate limit", "too many requests", "per minute", "per day")):
                raise ProviderRateLimitError(f"{provider}: {text[:200]}")
            if any(
                t in lowered
                for t in (
                    "subscription", "premium", "upgrade", "not available",
                    "restricted", "legacy", "special parameters", "special endpoint",
                )
            ):
                raise ProviderNotSupported(f"{provider}: {text[:200]}")
            if any(t in lowered for t in ("not found", "error message", "invalid api", "no data")):
                raise ProviderDataError(f"{provider}: {text[:200]}")
            raise ProviderDataError(f"{provider}: {text[:200]}")

        try:
            data = response.json()
        except json.JSONDecodeError as exc:
            raise ProviderDataError(f"{provider}: invalid JSON") from exc

        if isinstance(data, dict) and data.get("status") == "error":
            msg = str(data.get("message", "unknown error"))
            if "plan" in msg.lower() or "upgrade" in msg.lower():
                raise ProviderNotSupported(f"{provider}: {msg}")
            raise ProviderDataError(f"{provider}: {msg}")

        if cache_ttl != 0:
            cache.set(key, data, ttl=cache_ttl)
        return data

    raise ProviderUnavailableError(f"{provider}: request failed after retries ({last_exc})")
