from datetime import datetime, timezone

import requests

from scripts.update_news import add_bilingual_fields, empty_translation_state


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_google_cloud_translation_is_batched_masked_and_observable():
    class GoogleSession:
        def __init__(self):
            self.calls = []

        def post(self, url, json=None, headers=None, **_kwargs):
            self.calls.append({"url": url, "headers": headers, "json": json})
            translated = [text.replace("releases a fresh model", "推出全新模型") for text in json["q"]]
            return FakeResponse({"data": {"translations": [{"translatedText": text} for text in translated]}})

    session = GoogleSession()
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
        now=datetime(2026, 8, 26, tzinfo=timezone.utc),
        google_api_key="test-google-key",
    )

    assert len(session.calls) == 1
    call = session.calls[0]
    assert call["url"] == "https://translation.googleapis.com/language/translate/v2"
    assert call["headers"] == {"x-goog-api-key": "test-google-key"}
    assert call["json"]["target"] == "zh-TW"
    assert isinstance(call["json"]["q"], list)
    assert all("OpenAI" not in value for value in call["json"]["q"])
    assert ai_items[0]["title_zh"] == "OpenAI 推出全新模型"
    assert status["provider_used"] == "google_cloud"
    assert status["translated_count"] == 1


def test_deepl_is_only_used_after_google_failure():
    class FallbackSession:
        def __init__(self):
            self.urls = []

        def post(self, url, json=None, **_kwargs):
            self.urls.append(url)
            if "translation.googleapis.com" in url:
                raise requests.Timeout("simulated Google outage")
            return FakeResponse({"translations": [{"text": "發布新模型"}]})

    session = FallbackSession()
    status = {}
    item = {"title": "A vendor releases a model", "url": "https://example.com/fallback"}

    ai_items, _, _ = add_bilingual_fields(
        [item],
        [item],
        session,
        {},
        10,
        translation_status=status,
        now=datetime(2026, 8, 26, tzinfo=timezone.utc),
        google_api_key="test-google-key",
        deepl_api_key="test-deepl-key:fx",
    )

    assert session.urls == [
        "https://translation.googleapis.com/language/translate/v2",
        "https://api-free.deepl.com/v2/translate",
    ]
    assert ai_items[0]["title_zh"] == "發布新模型"
    assert status["provider_used"] == "deepl"
    assert status["request_count"] == 2


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
    now = datetime(2026, 8, 26, tzinfo=timezone.utc)
    item = {"title": "A new model is released", "url": "https://example.com/outage"}

    first, _, _ = add_bilingual_fields(
        [item],
        [item],
        session,
        {},
        10,
        translation_state=state,
        translation_status=first_status,
        now=now,
        google_api_key="test-google-key",
    )
    second, _, _ = add_bilingual_fields(
        [item],
        [item],
        session,
        {},
        10,
        translation_state=state,
        translation_status=second_status,
        now=now,
        google_api_key="test-google-key",
    )

    assert first[0]["title_zh"] is None
    assert second[0]["title_zh"] is None
    assert session.calls == 1
    assert first_status["failed_count"] == 1
    assert second_status["candidate_count"] == 0
    assert second_status["negative_cache_hits"] == 1


def test_missing_translation_credentials_skips_without_a_network_request():
    class NoNetworkSession:
        def post(self, *_args, **_kwargs):
            raise AssertionError("translation should skip without credentials")

    status = {}
    item = {"title": "A new model is released", "url": "https://example.com/no-key"}
    ai_items, _, _ = add_bilingual_fields(
        [item],
        [item],
        NoNetworkSession(),
        {},
        10,
        translation_status=status,
        now=datetime(2026, 8, 26, tzinfo=timezone.utc),
        google_api_key="",
        deepl_api_key="",
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
        [item],
        [item],
        NoNetworkSession(),
        {},
        10,
        translation_status=status,
        now=datetime(2026, 8, 26, tzinfo=timezone.utc),
        google_api_key="test-google-key",
    )

    assert ai_items[0]["title_zh"] is None
    assert status["candidate_count"] == 1
    assert status["request_count"] == 0
