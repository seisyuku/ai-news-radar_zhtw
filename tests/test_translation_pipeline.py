import json
from datetime import datetime, timedelta, timezone

import pytest
import requests
from urllib3.response import HTTPResponse

from scripts import update_news as u
from scripts.update_news import (
    GEMINI_TRANSLATION_MODEL,
    add_bilingual_fields,
    create_session,
    empty_translation_state,
)


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


def test_gemini_endpoint_does_not_inherit_feed_post_retries():
    session = create_session()
    try:
        adapter = session.get_adapter("https://generativelanguage.googleapis.com/v1beta/models")
        assert adapter.max_retries.total == 0
    finally:
        session.close()


def test_feed_retries_honor_retry_after_and_backoff(monkeypatch):
    waits = []
    monkeypatch.setattr("urllib3.util.retry.time.sleep", waits.append)
    with create_session() as session:
        retry = session.get_adapter("https://example.test/feed").max_retries
        assert retry.is_retry("GET", 503)
        assert not retry.is_retry("GET", 404)
        throttled = HTTPResponse(status=429, headers={"Retry-After": "2"})
        retry = retry.increment("GET", "/feed", response=throttled)
        retry.sleep(throttled)
        unavailable = HTTPResponse(status=503)
        retry = retry.increment("GET", "/feed", response=unavailable)
        retry.sleep(unavailable)
    assert waits == [2, 1.6]
    assert retry.total == 1


@pytest.mark.parametrize("reason,ttl", [
    ("invalid_translation", u.TRANSLATION_REJECTION_TTL_SECONDS),
    ("provider_unavailable", u.TRANSLATION_PROVIDER_FAILURE_TTL_SECONDS),
])
def test_translation_cooldown_uses_half_open_window(reason, ttl):
    now = datetime(2026, 11, 20, tzinfo=timezone.utc)
    for age, fresh in [(-0.001, False), (0, True), (ttl - 0.001, True), (ttl, False)]:
        entry = {"reason": reason, "created_at": u.iso(now - timedelta(seconds=age))}
        assert u._translation_rejection_is_fresh(entry, now) is fresh


@pytest.mark.parametrize("retry_after,oversleep,expected_waits,expected_timeouts", [
    (1, 0, [1], [2, 0.5]),
    (1.5, 0, [], [2]),
    (1, 0.5, [1], [2]),
])
def test_gemini_rate_limit_at_budget_boundary(
    monkeypatch, retry_after, oversleep, expected_waits, expected_timeouts,
):
    clock = [0.0]
    waits, timeouts = [], []
    now = datetime(2026, 11, 20, tzinfo=timezone.utc)
    state = empty_translation_state()

    def sleep(delay):
        waits.append(delay)
        clock[0] += delay + oversleep

    def translate(_session, _texts, _key, timeout):
        timeouts.append(timeout)
        if len(timeouts) == 1:
            clock[0] += 0.5
            response = requests.Response()
            response.status_code = 429
            response.headers["Retry-After"] = str(retry_after)
            raise requests.HTTPError(response=response)
        return ["新模型已發布"]

    monkeypatch.setattr(u, "TRANSLATION_TOTAL_BUDGET_SECONDS", 2)
    monkeypatch.setattr(u.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(u.time, "sleep", sleep)
    monkeypatch.setattr(u, "_translate_gemini_batch", translate)

    translated, status = u.translate_candidate_batches(
        object(), [{"text": "A new model is released", "cache_key": "title", "kind": "title"}],
        gemini_api_key="test-key", state=state, now=now,
    )

    assert timeouts == expected_timeouts and waits == expected_waits
    assert status["request_count"] == len(expected_timeouts)
    assert status.get("rate_limited", False) is (len(expected_timeouts) == 1)
    assert state["rejections"] == {}
    assert translated == ({"title": "新模型已發布"} if len(expected_timeouts) == 2 else {})


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


def test_provider_failure_retries_after_thirty_minutes_and_recovers():
    class RecoveringSession:
        def __init__(self):
            self.calls = 0

        def post(self, _url, json=None, **_kwargs):
            self.calls += 1
            if self.calls == 1:
                raise requests.Timeout("simulated provider outage")
            items = json_module.loads(json["contents"][0]["parts"][0]["text"])["items"]
            return gemini_response(
                [{"id": item["id"], "text": "新模型已發布"} for item in items]
            )

    json_module = json
    session = RecoveringSession()
    state = empty_translation_state()
    item = {"title": "A new model is released", "url": "https://example.com/recovery"}
    now = datetime(2026, 9, 7, tzinfo=timezone.utc)

    add_bilingual_fields(
        [item], [item], session, {}, 10,
        translation_state=state, now=now, gemini_api_key="test-gemini-key",
    )
    skipped_status = {}
    add_bilingual_fields(
        [item], [item], session, {}, 10,
        translation_state=state, translation_status=skipped_status,
        now=now + timedelta(minutes=29), gemini_api_key="test-gemini-key",
    )
    recovered_status = {}
    recovered, _, _ = add_bilingual_fields(
        [item], [item], session, {}, 10,
        translation_state=state, translation_status=recovered_status,
        now=now + timedelta(minutes=30), gemini_api_key="test-gemini-key",
    )

    assert session.calls == 2
    assert skipped_status["negative_cache_hits"] == 1
    assert recovered_status["translated_count"] == 1
    assert recovered[0]["title_zh"] == "新模型已發布"
    assert state["rejections"] == {}


def test_rate_limit_is_not_stored_in_the_six_hour_negative_cache():
    class RateLimitedSession:
        def __init__(self):
            self.calls = 0

        def post(self, *_args, **_kwargs):
            self.calls += 1
            response = type("Response", (), {"status_code": 429, "headers": {"Retry-After": "180"}})()
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
