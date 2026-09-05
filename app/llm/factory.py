"""Selects the configured LLM client. Add new providers here only."""

from __future__ import annotations

from typing import Optional

from app.config.settings import settings
from app.llm.base import LLMClient


def get_llm_client() -> Optional[LLMClient]:
    provider = (settings.llm_provider or "gemini").lower()
    if not settings.llm_api_key:
        return None

    if provider == "gemini":
        from app.llm.gemini import GeminiClient

        return GeminiClient(settings.llm_api_key, settings.llm_model)

    # Future providers (openai, anthropic, ...) plug in here.
    raise ValueError(f"Unsupported LLM_PROVIDER: {provider!r}")
