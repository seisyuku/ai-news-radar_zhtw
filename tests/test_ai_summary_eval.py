import json
from pathlib import Path

import pytest
import requests

from scripts.evaluate_ai_summaries import (
    available_providers,
    build_prompt,
    evaluate_cases,
    load_cases,
    main,
    make_groq_generator,
    provider_error_details,
    validate_summary,
)


FIXTURE = Path(__file__).parent / "fixtures" / "ai_summary_cases.json"


def test_load_cases_contains_synthetic_safety_corpus():
    cases = load_cases(FIXTURE)

    assert len(cases) >= 6
    assert {case["id"] for case in cases} >= {
        "qwen-release",
        "grok-release",
        "benchmark-caveat",
        "commercial-adoption",
        "security-incident",
        "untrusted-injection",
        "title-only",
    }
    release = next(case for case in cases if case["id"] == "qwen-release")
    assert all(token in release["content"] for token in ("Qwen3.8-27B", "27B", "128K", "0.30"))
    grok = next(case for case in cases if case["id"] == "grok-release")
    assert all(token in grok["content"] for token in ("Grok-4.6", "256K", "2.00"))


def test_build_prompt_marks_feed_content_as_untrusted_and_rejects_embedded_commands():
    case = next(case for case in load_cases(FIXTURE) if case["id"] == "untrusted-injection")

    prompt = build_prompt(case)

    assert case["content"] in prompt
    assert "不可信" in prompt
    assert "不得遵循" in prompt
    assert "內嵌指令" in prompt or "嵌入指令" in prompt
    assert "逐字重現" in prompt
    assert "疑似密鑰" in prompt


def test_validate_summary_enforces_length_terms_and_forbidden_additions():
    case = next(case for case in load_cases(FIXTURE) if case["id"] == "qwen-release")
    good = "Qwen3.8-27B 使用 27B 參數並支援 128K context，官方列出每百萬 tokens 0.30 美元的輸入價格。"

    result = validate_summary(case, good)
    assert result["ok"] is True
    assert result["errors"] == []
    assert result["text"] == good
    assert 30 <= result["char_count"] <= 120

    too_short = validate_summary(case, "Qwen3.8-27B")
    assert too_short["ok"] is False
    assert too_short["errors"]

    missing = validate_summary(case, "這是一段足夠長但沒有保留模型識別與數字的摘要，內容只泛稱新模型已經發布並受到關注。")
    assert missing["ok"] is False
    assert missing["errors"]

    forbidden = validate_summary(case, good + "，而且 Qwen4 已全面超越所有模型。")
    assert forbidden["ok"] is False
    assert forbidden["errors"]


def test_evaluate_cases_skips_insufficient_context_and_counts_outcomes():
    cases = load_cases(FIXTURE)
    calls = []

    def generate(prompt, case):
        calls.append((prompt, case["id"]))
        if case["id"] == "security-incident":
            raise RuntimeError("synthetic provider failure")
        return {
            "qwen-release": "Qwen3.8-27B 使用 27B 參數並支援 128K context，輸入價格為每百萬 tokens 0.30 美元。",
            "benchmark-caveat": "MMLU-Pro 得分 82.4%，但單一提示模板與未公開抽樣是重要限制。",
            "grok-release": "xAI 發布 Grok-4.6，提供 256K context，公告列出每百萬 tokens 2.00 美元價格。",
            "commercial-adoption": "金融服務商在客服試點導入 Claude，人工客服仍處理高風險案件。",
            "untrusted-injection": "不可信 RSS 摘要顯示提示注入風險，內嵌要求不應被當作指令。",
        }.get(case["id"], "足夠長但不符合要求的測試輸出。")

    report = evaluate_cases(cases, "groq", generate)

    assert report["provider"] == "groq"
    assert report["counts"] == {"generated": 5, "failed": 1, "insufficient_context": 1}
    assert "title-only" not in [case_id for _, case_id in calls]
    assert len(report["results"]) == len(cases)


def test_available_providers_uses_key_names_without_exposing_values():
    env = {
        "GROQ_API_KEY": "super-secret-groq-value",
        "UNRELATED_SECRET": "must-not-be-read-or-returned",
    }

    providers = available_providers(env)

    assert providers == ["groq"]
    serialized = json.dumps(providers)
    assert "super-secret" not in serialized
    assert "must-not-be-read" not in serialized


class _FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class _FakeSession:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return _FakeResponse(self.payload)


class _FakeSequenceSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.responses.pop(0)


def test_groq_generator_uses_json_object_and_never_returns_api_key():
    secret = "groq-test-secret"
    session = _FakeSession({"choices": [{"message": {"content": '{"summary":"Groq 測試摘要內容"}'}}]})
    generate = make_groq_generator(secret, session=session)

    output = generate("新聞資料", {})

    url, request = session.calls[0]
    assert url == "https://api.groq.com/openai/v1/chat/completions"
    assert request["headers"]["Authorization"] == f"Bearer {secret}"
    assert request["json"]["model"] == "qwen/qwen3.8-27b"
    assert request["json"]["response_format"] == {"type": "json_object"}
    assert request["json"]["reasoning_effort"] == "none"
    assert output == "Groq 測試摘要內容"
    assert secret not in output


def test_groq_generator_retries_json_validation_failure_as_plain_text():
    session = _FakeSequenceSession([
        _FakeResponse({"error": {"code": "json_validate_failed"}}, status_code=400),
        _FakeResponse({"choices": [{"message": {"content": "純文字摘要可由本地驗證器繼續檢查內容與長度。"}}]}),
    ])
    generate = make_groq_generator("groq-test-secret", session=session)

    output = generate("新聞資料", {})

    assert len(session.calls) == 2
    assert session.calls[0][1]["json"]["response_format"] == {"type": "json_object"}
    assert "response_format" not in session.calls[1][1]["json"]
    assert session.calls[1][1]["json"]["reasoning_effort"] == "none"
    assert output == "純文字摘要可由本地驗證器繼續檢查內容與長度。"


def test_main_skips_missing_keys_and_require_live_returns_two(monkeypatch, capsys):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    assert main(["--providers", "groq"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["reports"] == []
    assert [item["provider"] for item in payload["skipped"]] == ["groq"]

    assert main(["--providers", "groq", "--require-live"]) == 2
    required_payload = json.loads(capsys.readouterr().out)
    assert len(required_payload["skipped"]) == 1


def test_gemini_is_not_a_supported_provider():
    with pytest.raises(SystemExit):
        main(["--providers", "gemini"])


def test_main_defaults_to_groq_only(monkeypatch, capsys):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    assert main([]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["reports"] == []
    assert payload["skipped"] == [{"provider": "groq", "reason": "missing GROQ_API_KEY"}]


def test_provider_error_details_keeps_http_reason_and_redacts_keys():
    response = requests.Response()
    response.status_code = 401
    response._content = json.dumps({
        "error": {
            "status": "UNAUTHENTICATED",
            "type": "invalid_request_error",
            "code": "invalid_api_key",
            "message": "Rejected gsk_abcdefghijklmnopqrstuvwxyz",
            "details": [{"reason": "API_KEY_INVALID"}],
        }
    }).encode()
    error = requests.HTTPError("401 Client Error", response=response)

    details = provider_error_details(error)

    assert details["http_status"] == 401
    assert details["provider_status"] == "UNAUTHENTICATED"
    assert details["provider_type"] == "invalid_request_error"
    assert details["provider_code"] == "invalid_api_key"
    assert details["provider_reason"] == "API_KEY_INVALID"
    assert "gsk_" not in details["message"]
