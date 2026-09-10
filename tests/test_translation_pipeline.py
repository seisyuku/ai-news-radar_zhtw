import json
from datetime import datetime, timezone

import requests

from scripts.update_news import GEMINI_TRANSLATION_MODEL, add_bilingual_fields, empty_translation_state


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def gemini_response(translations):
    return FakeResponse(
        {
            "candidates": [
                {
                    "content": {
                        "role": "model",
                        "parts": [{"text": json.dumps({"translations": translations}, ensure_ascii=False)}],
                    },
                }
            ],
        }
    )


def test_gemini_translation_is_batched_masked_and_observable():
    class GeminiSession:
        def __init__(self):
            self.calls = []

        def post(self, url, json=None, headers=None, **_kwargs):
            self.calls.append({"url": url, "headers": headers, "json": json})
            items = json_module.loads(json["contents"][0]["parts"][0]["text"])["items"]
            translations = [
                {"id": item["id"], "text": item["text"].replace("releases a fresh model", "推出全新模型")}
                for item in items
            ]
            return gemini_response(translations)

    # The request payload parameter is intentionally named json above, so use
    # this module alias when decoding the nested JSON input.
    json_module = json
    session = GeminiSession()
    state = empty_translation_state()
    status = {}
    item = {"title": "OpenAI releases a fresh model", "url": "https://example.com/model"}

    ai_items, _, _ = add_bilingual_fields(
        [item],
        [item],
        session,
        {},
        10,
        translation_state=state,
        translation_status=status,
        now=datetime(2026, 9, 7, tzinfo=timezone.utc),
        gemini_api_key="test-gemini-key",
    )

    assert len(session.calls) == 1
    call = session.calls[0]
    assert call["url"] == (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_TRANSLATION_MODEL}:generateContent"
    )
    assert call["headers"] == {"x-goog-api-key": "test-gemini-key"}
    assert "untrusted source material" in call["json"]["systemInstruction"]["parts"][0]["text"]
    assert call["json"]["generationConfig"]["responseMimeType"] == "application/json"
    request_items = json.loads(call["json"]["contents"][0]["parts"][0]["text"])["items"]
    assert all("OpenAI" not in item["text"] for item in request_items)
    assert ai_items[0]["title_zh"] == "OpenAI 推出全新模型"
    assert status["provider_used"] == "gemini"
    assert status["model"] == GEMINI_TRANSLATION_MODEL
    assert status["translated_count"] == 1


def test_gemini_response_requires_exact_item_ids():
    class InvalidResponseSession:
        def post(self, *_args, **_kwargs):
            return gemini_response([{"id": "unexpected", "text": "發布新模型"}])

    state = empty_translation_state()
    status = {}
    item = {"title": "A vendor releases a model", "url": "https://example.com/invalid"}

    ai_items, _, _ = add_bilingual_fields(
        [item],
        [item],
        InvalidResponseSession(),
        {},
        10,
        translation_state=state,
        translation_status=status,
        now=datetime(2026, 9, 7, tzinfo=timezone.utc),
        gemini_api_key="test-gemini-key",
    )

    assert ai_items[0]["title_zh"] is None
    assert status["failed_count"] == 1
    assert status["last_error_type"] == "invalid_response"
    assert len(state["rejections"]) == 1


def test_provider_failure_uses_short_negative_cache_instead_of_retrying_every_run():
    class TimeoutSession:
        def __init__(self):
            self.calls = 0

        def post(self, *_args, **_kwargs):
            self.calls += 1
            raise requests.Timeout("simulated provider outage")

    session = TimeoutSession()
    state = empty_translation_state()
    first_status = {}
    second_status = {}
    now = datetime(2026, 9, 7, tzinfo=timezone.utc)
    item = {"title": "A new model is released", "url": "https://example.com/outage"}

    first, _, _ = add_bilingual_fields(
        [item], [item], session, {}, 10,
        translation_state=state, translation_status=first_status, now=now,
        gemini_api_key="test-gemini-key",
    )
    second, _, _ = add_bilingual_fields(
        [item], [item], session, {}, 10,
        translation_state=state, translation_status=second_status, now=now,
        gemini_api_key="test-gemini-key",
    )

    assert first[0]["title_zh"] is None
    assert second[0]["title_zh"] is None
    assert session.calls == 1
    assert first_status["failed_count"] == 1
    assert second_status["candidate_count"] == 0
    assert second_status["negative_cache_hits"] == 1


def test_rate_limit_is_not_stored_in_the_six_hour_negative_cache():
    class RateLimitedSession:
        def __init__(self):
            self.calls = 0

        def post(self, *_args, **_kwargs):
            self.calls += 1
            response = type("Response", (), {"status_code": 429, "headers": {"Retry-After": "90"}})()
            raise requests.HTTPError("rate limited", response=response)

    session = RateLimitedSession()
    state = empty_translation_state()
    status = {}
    item = {"title": "A new model is released", "url": "https://example.com/rate-limit"}

    ai_items, _, _ = add_bilingual_fields(
        [item], [item], session, {}, 10,
        translation_state=state, translation_status=status,
        now=datetime(2026, 9, 7, tzinfo=timezone.utc), gemini_api_key="test-gemini-key",
    )

    assert ai_items[0]["title_zh"] is None
    assert session.calls == 1
    assert status["rate_limited"] is True
    assert status["failed_count"] == 1
    assert state["rejections"] == {}


def test_missing_translation_credentials_skips_without_a_network_request():
    class NoNetworkSession:
        def post(self, *_args, **_kwargs):
            raise AssertionError("translation should skip without credentials")

    status = {}
    item = {"title": "A new model is released", "url": "https://example.com/no-key"}
    ai_items, _, _ = add_bilingual_fields(
        [item], [item], NoNetworkSession(), {}, 10,
        translation_status=status, now=datetime(2026, 9, 7, tzinfo=timezone.utc), gemini_api_key="",
    )

    assert ai_items[0]["title_zh"] is None
    assert ai_items[0]["title_en"] == item["title"]
    assert status["skipped"] is True
    assert status["skip_reason"] == "missing_translation_credentials"


def test_overlong_rss_text_is_not_sent_as_an_oversized_provider_request():
    class NoNetworkSession:
        def post(self, *_args, **_kwargs):
            raise AssertionError("oversized text must not be sent")

    status = {}
    item = {"title": "model " * 1_000, "url": "https://example.com/oversized"}
    ai_items, _, _ = add_bilingual_fields(
        [item], [item], NoNetworkSession(), {}, 10,
        translation_status=status, now=datetime(2026, 9, 7, tzinfo=timezone.utc), gemini_api_key="test-gemini-key",
    )

    assert ai_items[0]["title_zh"] is None
    assert status["candidate_count"] == 1
    assert status["request_count"] == 0
