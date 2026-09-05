"""Provider-agnostic LLM interface used by the reasoning layer."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


class LLMError(RuntimeError):
    pass


@runtime_checkable
class LLMClient(Protocol):
    name: str
    model: str

    @property
    def available(self) -> bool:
        ...

    def generate_json(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.2,
        max_output_tokens: int = 2048,
    ) -> dict:
        """Return a parsed JSON object. Raises :class:`LLMError` on failure."""
        ...
