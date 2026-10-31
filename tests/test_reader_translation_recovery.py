"""Bounded recovery of rejected reader titles and monetary display facts."""
from datetime import datetime, timedelta, timezone
import json

import pytest

from scripts import update_news as u
from scripts.summary_facts import money_supported
from tests.test_translation_pipeline import gemini_response


NOW = datetime(2026, 10, 31, 12, 35, tzinfo=timezone.utc)
TITLE = "OpenAI raises just $11 billion of its $30 billion target as big investors lose their AI appetite"
ZH = "OpenAI 僅募得110億美元，未達300億美元目標，主要投資人的AI投資意願減弱"
SUMMARY = "OpenAI raised only about $11 billion, less than its $30 billion target, at a $1.25 trillion valuation."
SUMMARY_ZH = "OpenAI 募資約110億美元，低於300億美元目標，估值為1.25兆美元。"


class Translator:
    def __init__(self, reply):
        self.reply = reply
        self.calls = []

    def post(self, _url, json=None, **_kwargs):
        self.calls.append(json)
        items = __import__("json").loads(json["contents"][0]["parts"][0]["text"])["items"]
        return gemini_response([{"id": item["id"], "text": self.reply(item["text"], len(self.calls))} for item in items])


def translate(session, *, title=TITLE, summary="", cache=None, state=None, now=NOW, key="test-key", limit=80):
    row = {"title": title, "summary": summary, "url": "https://the-decoder.com/synthetic-translation"}
    status = {}
    ai, all_rows, cache = u.add_bilingual_fields([row], [row], session, cache if cache is not None else {}, limit,
        translation_state=state, translation_status=status, now=now, gemini_api_key=key)
    return ai[0], all_rows[0], cache, status


def test_invalid_title_gets_one_corrective_retry_without_echoing_rejected_output():
    session = Translator(lambda _text, call: "錯誤回應：品牌佔位符遺失" if call == 1 else ZH.replace("OpenAI", "ZXQ0QXZ"))
    state = u.empty_translation_state()
    row, all_row, cache, status = translate(session, state=state)
    assert row["title_zh"] == all_row["title_zh"] == ZH
    assert cache[TITLE] == ZH and state["rejections"] == {}
    assert status["request_count"] == 2 and status["validation_failed_count"] == 1
    assert status["translated_count"] == 1
    prompt = session.calls[1]["systemInstruction"]["parts"][0]["text"]
    assert "previous title translation failed" in prompt
    assert "錯誤回應" not in json.dumps(session.calls[1], ensure_ascii=False)


def test_exact_canonical_brand_is_accepted_without_spending_a_repair_request():
    session = Translator(lambda _text, _call: ZH)
    row, _, _, status = translate(session)
    assert row["title_zh"] == ZH and status["request_count"] == 1
    assert status["literal_placeholder_recoveries"] == 1


def test_summary_footer_never_enters_translation_and_raw_cache_key_survives():
    raw = "Researchers released a model and published evaluation results. The article Model update appeared first on Example News ."
    translated = "研究人員發布模型，並公開評估結果。"
    session = Translator(lambda _text, _call: translated + "文章（模型更新）最初發表於 Example News。")
    row, all_row, cache, status = translate(session, title="模型更新", summary=raw)
    payload = json.loads(session.calls[0]["contents"][0]["parts"][0]["text"])
    assert payload["items"][0]["text"] == "Researchers released a model and published evaluation results."
    assert row["summary"] == all_row["summary"] == raw
    assert row["summary_zh"] == all_row["summary_zh"] == translated
    assert cache["summary::" + raw] == translated
    assert status["request_count"] == status["translated_count"] == 1


def test_current_summary_cache_footer_is_removed_without_retranslation():
    raw = "Researchers released a model. The post Model update appeared first on Example News ."
    body = "研究人員發布模型。"
    old_cache = {"summary::" + raw: body + "（模型更新）最初發表於 Example News。", "historical": "文章〈舊標題〉最初發表於網站。"}
    session = Translator(lambda *_: (_ for _ in ()).throw(AssertionError("must reuse cache")))
    row, _, cache, status = translate(session, title="模型更新", summary=raw, cache=old_cache)
    assert row["summary_zh"] == body and cache["summary::" + raw] == body
    assert cache["historical"] == "文章〈舊標題〉最初發表於網站。"
    assert status["request_count"] == 0 and session.calls == []


def test_footer_only_summary_is_not_a_translation_candidate():
    session = Translator(lambda *_: (_ for _ in ()).throw(AssertionError("no content")))
    row, _, _, status = translate(session, title="模型更新", summary="The post Model update appeared first on Example News .")
    assert "summary_zh" not in row and status["request_count"] == 0


@pytest.mark.parametrize("value,mapping,expected", [
    ("OpenAI 發布模型", {"ZXQ0QXZ": "OpenAI"}, "ZXQ0QXZ 發布模型"),
    ("OpenAIX 發布模型", {"ZXQ0QXZ": "OpenAI"}, "OpenAIX 發布模型"),
    ("OpenAI 與 OpenAI", {"ZXQ0QXZ": "OpenAI"}, "OpenAI 與 OpenAI"),
    ("OpenAI 發布模型", {"ZXQ0QXZ": "OpenAI", "ZXQ1QXZ": "OpenAI"}, "OpenAI 發布模型"),
    ("微軟發布模型", {"ZXQ0QXZ": "微軟"}, "ZXQ0QXZ發布模型"),
    ("微軟發布模型", {"ZXQ0QXZ": "Microsoft"}, "微軟發布模型"),
])
def test_literal_placeholder_recovery_is_exact_and_unambiguous(value, mapping, expected):
    assert u._restore_literal_translation_placeholders(value, mapping) == expected


def test_two_invalid_title_outputs_cool_down_instead_of_retrying_every_refresh():
    session = Translator(lambda text, _call: text)
    state = u.empty_translation_state()
    row, _, _, first = translate(session, state=state)
    row2, _, _, second = translate(session, state=state, now=NOW+timedelta(minutes=30))
    assert row["title_zh"] is None and row2["title_zh"] is None
    assert len(session.calls) == first["request_count"] == 2
    assert first["validation_failure_reasons"] == {"unchanged": 2}
    assert state["rejections"][TITLE]["title_retry_attempted"] is True
    assert second["request_count"] == 0 and second["negative_cache_hits"] == 1


def test_legacy_six_hour_title_rejection_has_one_recovery_after_thirty_minutes():
    session = Translator(lambda _text, _call: ZH.replace("OpenAI", "ZXQ0QXZ"))
    state = {"version": u.TRANSLATION_STATE_VERSION, "rejections": {
        TITLE: {"reason": "invalid_translation", "created_at": u.iso(NOW-timedelta(hours=3))}}}
    row, _, _, status = translate(session, state=state)
    assert row["title_zh"] == ZH and status["request_count"] == 1
    assert state["rejections"] == {}
    assert "previous title translation failed" in session.calls[0]["systemInstruction"]["parts"][0]["text"]


def test_request_cap_defers_repair_without_consuming_it_before_a_request(monkeypatch):
    monkeypatch.setattr(u, "TRANSLATION_MAX_REQUESTS", 1)
    session = Translator(lambda text, call: text if call == 1 else ZH.replace("OpenAI", "ZXQ0QXZ"))
    state = u.empty_translation_state()
    row, _, _, first = translate(session, state=state)
    assert row["title_zh"] is None and first["request_count"] == 1 and first["budget_exhausted"]
    assert state["rejections"][TITLE]["title_retry_attempted"] is False
    _, _, _, skipped = translate(session, state=state, now=NOW+timedelta(minutes=29))
    assert skipped["request_count"] == 0
    recovered, _, _, status = translate(session, state=state, now=NOW+timedelta(minutes=30))
    assert recovered["title_zh"] == ZH and status["request_count"] == 1


def test_budget_exhaustion_does_not_send_repair_outside_existing_limits(monkeypatch):
    monkeypatch.setattr(u, "TRANSLATION_TOTAL_BUDGET_SECONDS", 0)
    session = Translator(lambda *_: pytest.fail("must not call provider"))
    row, _, _, status = translate(session)
    assert row["title_zh"] is None and status["request_count"] == 0 and status["budget_exhausted"]


@pytest.mark.parametrize("bad", [
    "OpenAI 募資約11百萬美元，目標30億美元，估值1.25兆美元。",
    "OpenAI 募資約110億歐元，目標300億美元，估值1.25兆美元。",
])
def test_invalid_summary_money_is_not_displayed_or_retried_in_a_loop(bad):
    session = Translator(lambda _text, _call: bad.replace("OpenAI", "ZXQ0QXZ"))
    state = u.empty_translation_state()
    row, all_row, cache, status = translate(session, title="募資消息", summary=SUMMARY, state=state)
    assert row.get("summary_zh") is None and all_row.get("summary_zh") is None
    assert row["summary"] == SUMMARY and len(session.calls) == 1
    assert "summary::"+SUMMARY not in cache
    _, _, _, second = translate(session, title="募資消息", summary=SUMMARY, state=state, now=NOW+timedelta(minutes=30))
    assert second["request_count"] == 0 and second["negative_cache_hits"] == 1


def test_current_invalid_money_cache_recovers_together_with_the_missing_title():
    invalid = "OpenAI 在最新一輪融資中籌集11百萬美元，低於30億美元目標。"
    cache = {"summary::"+SUMMARY: invalid, "summary::historical": "保留歷史快取"}
    state = {"version": u.TRANSLATION_STATE_VERSION, "rejections": {
        TITLE: {"reason": "invalid_translation", "created_at": u.iso(NOW-timedelta(hours=3))}}}
    session = Translator(lambda text, _: (SUMMARY_ZH if "raised only" in text else ZH).replace("OpenAI", "ZXQ0QXZ"))
    row, all_row, cache, status = translate(session, summary=SUMMARY, cache=cache, state=state)
    assert row["title_zh"] == all_row["title_zh"] == ZH
    assert row["summary_zh"] == all_row["summary_zh"] == SUMMARY_ZH
    assert cache["summary::historical"] == "保留歷史快取" and not state["rejections"]
    assert status["candidate_count"] == 2 and status["request_count"] == 1


def test_invalid_cached_money_and_stale_display_are_hidden_without_credentials():
    cache = {TITLE: ZH, "summary::"+SUMMARY: "OpenAI 募資11百萬美元。"}
    row = {"title": TITLE, "summary": SUMMARY, "summary_zh": "OpenAI 募資11百萬美元。", "url": "https://example.com/native"}
    session = Translator(lambda *_: pytest.fail("no credentials"))
    ai, all_rows, _ = u.add_bilingual_fields([row], [row], session, cache, 0, gemini_api_key="")
    assert ai[0]["title_zh"] == ZH and all_rows[0].get("summary_zh") is None
    assert ai[0].get("summary_zh") is None and ai[0]["summary"] == SUMMARY
    assert not session.calls


@pytest.mark.parametrize("source,translated,expected", [
    ("$11 billion and $30 billion", "110億美元與300億美元", True),
    ("$11 billion and $30 billion", "11百萬美元與30億美元", False),
    ("$1.25 trillion", "1.25兆美元", True),
    ("$11 billion", "110億歐元", False),
    ("No price announced", "價格是25美元", False),
    ("$11 billion", "11 billion美元", True),
    ("Big Tech is pouring billions into AI infrastructure", "科技公司投入數十億美元", False),
    ("Big Tech is pouring billions into AI infrastructure", "科技公司投入數十億資金", True),
])
def test_reader_monetary_values_keep_currency_and_scale(source, translated, expected):
    assert money_supported(translated, source) is expected
