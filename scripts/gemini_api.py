"""Dormant JSON API connector for explicitly requested non-news uses.

No scheduler, news summarizer, automatic retry, or credential logging.
"""
from __future__ import annotations
import json
from typing import Any, Mapping
import requests

DEFAULT_MODEL = "gemini-3.5-flash-lite"
DEFAULT_TIMEOUT_SECONDS = 60
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"


def generate_json(prompt: str, *, api_key: str, schema: Mapping[str, Any],
                  max_output_tokens: int, model: str = DEFAULT_MODEL,
                  timeout: float = DEFAULT_TIMEOUT_SECONDS,
                  session: requests.Session | None = None) -> dict[str, Any]:
    """Call the existing structured-output interface for a caller-defined use."""
    if not str(api_key or "").strip():
        raise ValueError("missing_GEMINI_API_KEY")
    if max_output_tokens <= 0 or timeout <= 0:
        raise ValueError("positive_request_limits_required")
    client = session or requests.Session()
    response = client.post(
        f"{GEMINI_API_BASE}/models/{model}:generateContent",
        timeout=timeout,
        headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
        json={"contents": [{"parts": [{"text": prompt}]}],
              "generationConfig": {"maxOutputTokens": max_output_tokens,
                  "responseMimeType": "application/json", "responseSchema": dict(schema)}},
    )
    response.raise_for_status()
    raw = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("provider_response_is_not_a_json_object")
    return payload
