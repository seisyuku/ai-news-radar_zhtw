#!/usr/bin/env python3
"""Run a staged, secret-safe Gemini API diagnostic.

This probe is deliberately separate from the Groq-backed production summary
path.  It uses only synthetic prompts and stops at the first failed layer so a
credential, model, transport, quota, or structured-output failure is not
misreported as a summary-quality problem.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import requests

try:
    from scripts.evaluate_ai_summaries import (
        DEFAULT_GEMINI_MODEL,
        DEFAULT_TIMEOUT_SECONDS,
        provider_error_details,
    )
except ModuleNotFoundError:  # pragma: no cover - direct `python scripts/diagnose_gemini.py`
    from evaluate_ai_summaries import (
        DEFAULT_GEMINI_MODEL,
        DEFAULT_TIMEOUT_SECONDS,
        provider_error_details,
    )


UTC = timezone.utc
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _model_id(value: str) -> str:
    clean = str(value or "").strip()
    return clean.removeprefix("models/")


def _error_reason(details: Mapping[str, Any]) -> str:
    return " ".join(
        str(details.get(key) or "")
        for key in ("provider_reason", "provider_status", "provider_code", "message", "type")
    ).casefold()


def classify_failure(details: Mapping[str, Any], *, stage: str) -> dict[str, str]:
    """Map a sanitized provider/transport failure to an operator action."""

    status = int(details.get("http_status") or 0)
    reason = _error_reason(details)
    if "api_key_invalid" in reason or status == 401 or "unauthenticated" in reason:
        return {
            "code": "invalid_api_key",
            "cause": "Gemini API 拒絕目前的 API key。",
            "action": "在 Google AI Studio 建立或更換 Gemini API key，確認貼入時沒有多餘空白。",
        }
    if "service_disabled" in reason or "api has not been used" in reason:
        return {
            "code": "api_not_enabled",
            "cause": "API key 所屬專案尚未啟用 Generative Language API。",
            "action": "在該 Google Cloud 專案啟用 generativelanguage.googleapis.com 後重測。",
        }
    if status == 403 or "permission_denied" in reason:
        return {
            "code": "permission_or_region_denied",
            "cause": "API key、專案權限、billing 或所在區域不允許這次呼叫。",
            "action": "核對 key 所屬專案、API restrictions、Google AI Studio billing 與區域可用性。",
        }
    if status == 429 or "resource_exhausted" in reason or "quota" in reason or "rate_limit" in reason:
        return {
            "code": "quota_or_rate_limit",
            "cause": "Gemini API 的 RPM、TPM、每日額度或 spend limit 已達上限。",
            "action": "查看 AI Studio usage/rate limits；等待重置或調整配額後再以同一流程重測。",
        }
    if status == 404 or "not_found" in reason or "modelunavailable" in reason:
        return {
            "code": "model_not_found",
            "cause": "指定模型不存在、已退役，或不對此 API key 開放。",
            "action": "以 model_discovery 回傳的 generateContent 模型更新 GEMINI_SUMMARY_MODEL。",
        }
    if stage == "structured_generation" and status == 400:
        return {
            "code": "structured_output_incompatible",
            "cause": "基本文字生成可用，但目前模型或 API 版本拒絕 structured JSON 設定。",
            "action": "核對 responseMimeType/responseSchema 支援；不要把此錯誤判成 key 或其他 provider 問題。",
        }
    if status == 400 or "invalid_argument" in reason:
        return {
            "code": "invalid_request",
            "cause": "Gemini API 認為請求參數或 API 版本不合法。",
            "action": "依報告中的 provider message 核對 v1beta generateContent 請求格式。",
        }
    if status in {408, 500, 502, 503, 504} or "timeout" in reason or "connection" in reason:
        return {
            "code": "transient_or_transport_failure",
            "cause": "網路、逾時或 Gemini 服務端暫時失敗。",
            "action": "保留本次報告，稍後重測；若持續發生再查 Gemini status。",
        }
    return {
        "code": "unclassified_provider_failure",
        "cause": "Gemini 呼叫失敗，但現有回應不足以唯一判定原因。",
        "action": "以報告中的 stage、HTTP status、provider status/reason/message 進一步查核。",
    }


def _http_error_details(response: requests.Response) -> dict[str, Any]:
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        return provider_error_details(exc)
    return {}


def _response_text(payload: Mapping[str, Any]) -> str:
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        feedback = payload.get("promptFeedback")
        if isinstance(feedback, Mapping) and feedback.get("blockReason"):
            raise ValueError(f"content_blocked:{feedback.get('blockReason')}")
        raise ValueError("provider response has no candidates")
    candidate = candidates[0]
    if not isinstance(candidate, Mapping):
        raise ValueError("provider response candidate is not an object")
    content = candidate.get("content")
    parts = content.get("parts") if isinstance(content, Mapping) else None
    if not isinstance(parts, list) or not parts or not isinstance(parts[0], Mapping):
        finish_reason = candidate.get("finishReason")
        raise ValueError(f"provider response has no text; finishReason={finish_reason or 'unknown'}")
    text = str(parts[0].get("text") or "").strip()
    if not text:
        raise ValueError("provider response text is empty")
    return text


def _failed_report(
    report: dict[str, Any],
    *,
    stage: str,
    details: Mapping[str, Any],
) -> dict[str, Any]:
    clean_details = dict(details)
    diagnosis = classify_failure(clean_details, stage=stage)
    report["steps"].append({"name": stage, "status": "failed", "error": clean_details})
    report["diagnosis"] = diagnosis
    report["ok"] = False
    return report


def diagnose_gemini(
    *,
    api_key: str,
    model: str = DEFAULT_GEMINI_MODEL,
    session: requests.Session | None = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Probe credentials, model visibility, plain generation, then JSON schema."""

    selected_model = _model_id(model) or DEFAULT_GEMINI_MODEL
    report: dict[str, Any] = {
        "generated_at": _utc_now(),
        "provider": "gemini",
        "scope": "diagnostic_only_no_provider_fallback",
        "model": selected_model,
        "ok": False,
        "steps": [],
    }
    clean_key = str(api_key or "").strip()
    if not clean_key:
        report["steps"].append({"name": "configuration", "status": "failed", "reason": "missing_GEMINI_API_KEY"})
        report["diagnosis"] = {
            "code": "missing_api_key",
            "cause": "目前執行環境沒有 GEMINI_API_KEY，因此尚未送出任何 Gemini 網路請求。",
            "action": "只在本機 shell 暫時 export GEMINI_API_KEY 後重跑；不要把 key 寫入 repo 或報告。",
        }
        return report

    report["steps"].append({"name": "configuration", "status": "passed", "credential": "present_redacted"})
    client = session or requests.Session()
    headers = {"x-goog-api-key": clean_key, "Content-Type": "application/json"}

    try:
        response = client.get(
            f"{GEMINI_API_BASE}/models",
            timeout=timeout,
            headers=headers,
            params={"pageSize": 1000},
        )
        if response.status_code >= 400:
            return _failed_report(report, stage="model_discovery", details=_http_error_details(response))
        payload = response.json()
    except Exception as exc:
        return _failed_report(report, stage="model_discovery", details=provider_error_details(exc))

    models = payload.get("models") if isinstance(payload, Mapping) else None
    models = models if isinstance(models, list) else []
    available: list[str] = []
    selected: Mapping[str, Any] | None = None
    for raw in models:
        if not isinstance(raw, Mapping):
            continue
        methods = [str(value) for value in raw.get("supportedGenerationMethods") or []]
        name = _model_id(str(raw.get("name") or raw.get("baseModelId") or ""))
        if "generateContent" in methods and name:
            available.append(name)
        if selected_model in {_model_id(str(raw.get("name") or "")), _model_id(str(raw.get("baseModelId") or ""))}:
            selected = raw

    if selected is None:
        suggestions = [name for name in available if "flash" in name][:5]
        details = {
            "type": "ModelUnavailable",
            "message": f"selected model is absent from models.list; {len(available)} generateContent models visible",
            "suggested_models": suggestions,
        }
        return _failed_report(report, stage="model_discovery", details=details)
    methods = [str(value) for value in selected.get("supportedGenerationMethods") or []]
    if "generateContent" not in methods:
        details = {"type": "UnsupportedGenerationMethod", "message": "selected model does not advertise generateContent"}
        return _failed_report(report, stage="model_discovery", details=details)
    report["steps"].append({
        "name": "model_discovery",
        "status": "passed",
        "selected_model_visible": True,
        "generate_content_supported": True,
        "visible_generate_content_model_count": len(available),
    })

    generation_url = f"{GEMINI_API_BASE}/models/{selected_model}:generateContent"
    plain_payload = {
        "contents": [{"parts": [{"text": "This is a synthetic connectivity test. Reply with exactly OK."}]}],
        "generationConfig": {"maxOutputTokens": 16},
    }
    try:
        response = client.post(generation_url, timeout=timeout, headers=headers, json=plain_payload)
        if response.status_code >= 400:
            return _failed_report(report, stage="plain_generation", details=_http_error_details(response))
        _response_text(response.json())
    except Exception as exc:
        return _failed_report(report, stage="plain_generation", details=provider_error_details(exc))
    report["steps"].append({"name": "plain_generation", "status": "passed"})

    structured_payload = {
        "contents": [{"parts": [{"text": "Synthetic format test. Return status equal to ok."}]}],
        "generationConfig": {
            "maxOutputTokens": 32,
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {"status": {"type": "STRING"}},
                "required": ["status"],
            },
        },
    }
    try:
        response = client.post(generation_url, timeout=timeout, headers=headers, json=structured_payload)
        if response.status_code >= 400:
            return _failed_report(report, stage="structured_generation", details=_http_error_details(response))
        text = _response_text(response.json())
        parsed = json.loads(text)
        if not isinstance(parsed, Mapping) or not str(parsed.get("status") or "").strip():
            raise ValueError("structured response JSON has no status")
    except Exception as exc:
        return _failed_report(report, stage="structured_generation", details=provider_error_details(exc))

    report["steps"].append({"name": "structured_generation", "status": "passed"})
    report["diagnosis"] = {
        "code": "gemini_api_usable",
        "cause": "目前 key、模型、generateContent 與 structured JSON 均可用。",
        "action": "可接著執行 Gemini-only 合成摘要評估；此診斷不改變 production provider 設定。",
    }
    report["ok"] = True
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a staged Gemini-only API diagnostic")
    parser.add_argument("--model", default=os.environ.get("GEMINI_SUMMARY_MODEL") or DEFAULT_GEMINI_MODEL)
    parser.add_argument("--output", type=Path, help="Optional secret-safe JSON report path")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    args = parser.parse_args(argv)

    report = diagnose_gemini(
        api_key=os.environ.get("GEMINI_API_KEY") or "",
        model=args.model,
        timeout=max(1, args.timeout),
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    if report["ok"]:
        return 0
    return 2 if report.get("diagnosis", {}).get("code") == "missing_api_key" else 1


if __name__ == "__main__":
    raise SystemExit(main())
