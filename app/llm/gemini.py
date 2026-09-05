"""Google Gemini client (REST, no SDK dependency)."""

from __future__ import annotations

import json
import re

import httpx

from app.llm.base import LLMError

_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
_FALLBACK_MODELS = ["gemini-flash-lite-latest", "gemini-flash-latest", "gemini-3.6-flash"]


def _salvage_truncated_json(text: str) -> dict:
    """Best-effort recovery of a JSON object that got cut off mid-generation."""
    text = text.strip()
    depth = 0
    in_str = False
    escape = False
    buf = []
    for ch in text:
        buf.append(ch)
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_str = not in_str
        elif not in_str:
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
    if in_str:
        buf.append('"')
    buf.append("}" * max(0, depth))
    return json.loads("".join(buf))


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        return _salvage_truncated_json(text)


class GeminiClient:
    name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-flash-latest"):
        self.api_key = api_key
        self.model = model or "gemini-flash-latest"

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def generate_json(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.2,
        max_output_tokens: int = 4096,
    ) -> dict:
        if not self.available:
            raise LLMError("Gemini API key is not configured.")

        body = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_output_tokens,
                "responseMimeType": "application/json",
            },
        }

        models_to_try = [self.model] + [m for m in _FALLBACK_MODELS if m != self.model]
        last_error = "unknown error"

        for model in models_to_try:
            url = _ENDPOINT.format(model=model)
            try:
                with httpx.Client(timeout=45) as client:
                    response = client.post(url, params={"key": self.api_key}, json=body)
            except httpx.HTTPError as exc:
                last_error = f"network error: {exc}"
                continue

            if response.status_code == 404:
                last_error = f"model '{model}' not available"
                continue
            if response.status_code in (401, 403):
                raise LLMError(f"Gemini authentication failed ({response.status_code}).")
            if response.status_code == 429:
                raise LLMError("Gemini rate limit exceeded.")
            if response.status_code != 200:
                last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                continue

            data = response.json()
            try:
                parts = data["candidates"][0]["content"]["parts"]
                text = "".join(p.get("text", "") for p in parts)
            except (KeyError, IndexError):
                finish = (data.get("candidates") or [{}])[0].get("finishReason", "")
                raise LLMError(f"Gemini returned no usable content (finishReason={finish}).")

            if model != self.model:
                self.model = model  # remember the working model
            try:
                return _extract_json(text)
            except json.JSONDecodeError as exc:
                raise LLMError(f"Gemini did not return valid JSON: {exc}") from exc

        raise LLMError(f"Gemini request failed: {last_error}")
