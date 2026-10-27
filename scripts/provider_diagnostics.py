"""Shared redacted provider error metadata; no calls or scheduled work."""
from __future__ import annotations
import re
from typing import Any
import requests
MAX_PROVIDER_ERROR_CHARS = 300

def _redact_provider_error_text(value: Any) -> str:
    """Keep provider diagnostics useful without copying credentials to reports."""

    text = re.sub(r"\s+", " ", str(value or "")).strip()
    text = re.sub(r"AIza[0-9A-Za-z_-]{20,}", "[REDACTED_GEMINI_KEY]", text)
    text = re.sub(r"gsk_[0-9A-Za-z_-]{20,}", "[REDACTED_GROQ_KEY]", text)
    return text[:MAX_PROVIDER_ERROR_CHARS]


def provider_error_details(exc: Exception) -> dict[str, Any]:
    """Return a compact, redacted provider failure suitable for JSON reports."""

    details: dict[str, Any] = {"type": type(exc).__name__}
    if not isinstance(exc, requests.HTTPError) or exc.response is None:
        return details

    details["http_status"] = int(exc.response.status_code)
    try:
        payload = exc.response.json()
    except (ValueError, TypeError):
        payload = None

    error = payload.get("error") if isinstance(payload, dict) else None
    if isinstance(error, dict):
        for source_key, target_key in (("status", "provider_status"), ("type", "provider_type"), ("code", "provider_code")):
            value = error.get(source_key)
            if value not in (None, ""):
                details[target_key] = _redact_provider_error_text(value)
        if error.get("message"):
            details["message"] = _redact_provider_error_text(error["message"])
        provider_details = error.get("details")
        if isinstance(provider_details, list):
            reasons = [
                _redact_provider_error_text(item.get("reason"))
                for item in provider_details
                if isinstance(item, dict) and item.get("reason")
            ]
            if reasons:
                details["provider_reason"] = ",".join(reasons[:3])
    elif error:
        details["message"] = _redact_provider_error_text(error)
    return details
