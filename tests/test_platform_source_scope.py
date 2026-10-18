"""Cross-layer contracts for native platform events and retained catalogs."""

from copy import deepcopy
from datetime import datetime, timezone
from html import escape
from types import SimpleNamespace

import pytest

from scripts import update_news as news
from scripts.ai_relevance import score_ai_relevance
from scripts.source_scope import platform_event_decision


NOW = datetime(2026, 10, 18, 14, tzinfo=timezone.utc)


def article(title, summary="", **overrides):
    return {"site_id": "tw_media", "source": "INSIDE", "title": title,
            "summary": summary, "url": "https://www.inside.com.tw/article/example",
            "published_at": "2026-10-18T12:00:00Z", **overrides}


def xml(rows):
    body = "".join(
        f'<item><title>{escape(r["title"])}</title><link>{escape(r["url"])}</link>'
        f'<pubDate>{r.get("published_at", "2026-10-18T12:00:00Z")}</pubDate>'
        f'<description>{escape(r.get("summary", ""))}</description></item>' for r in rows)
    return f'<rss version="2.0"><channel><title>News</title>{body}</channel></rss>'.encode()


@pytest.mark.parametrize("title,summary,event", [
    ("Zeabur 宣布停止營運！12月31日前全面關閉", "", "market"),
    ("雲端部署平台新星宣布年底停止營運", "", "market"),
    ("雲端平台新星停止服務", "客戶須遷移網站及資料庫。", "market"),
    ("新星公告事件", "應用託管平台新星遭入侵，導致資料外洩。", "security"),
    ("雲端部署平台正式取消既有基本方案", "既有使用者即日起改為付費方案。", "pricing"),
    ("雲端部署平台限制既有資料存取", "原有使用者的資料匯出權限將於11月1日生效。", None),
    ("雲端部署平台服務中斷已連續四天", "", None),
    ("雲端部署平台已連續中斷四天，預計明天恢復", "", None),
    ("雲端部署平台服務中斷", "已連續超過三天無法使用。", None),
    ("雲端部署平台服務中斷超過72小時", "", None),
    ("雲端部署平台已恢復服務", "雲端部署平台此前連續中斷80小時。", None),
    ("雲端部署平台持續中斷", "自2026-10-14T09:00:00+08:00開始，至今仍未恢復。", None),
])
def test_native_events_survive_relevance_and_receive_only_supported_badges(title, summary, event):
    row = article(title, summary)
    policy = platform_event_decision(row)
    assert policy.admitted
    relevance = score_ai_relevance(row)
    assert relevance["is_ai_related"] and relevance["score"] >= 0.65
    badges = news.business_event_score(row)
    if event:
        assert event in badges
    else:
        assert "market" not in badges


@pytest.mark.parametrize("title,summary", [
    ("雲端部署平台AI新方案限時半價", "新用戶免費試用，優惠碼便宜50%。"),
    ("雲端部署平台AI方案全面升級更划算", ""),
    ("雲端部署平台AI價格調整", ""),
    ("雲端部署平台AI可能漲價", "既有用戶考慮自11月1日起從100調整為200。"),
    ("雲端部署平台AI資料管理更安全，權限更彈性", ""),
    ("Dify AI雲端硬碟訂閱即日起漲價", "既有用戶原價100，改為200。"),
    ("AI雲端硬碟訂閱即日起漲價", "既有用戶原價100，改為200。"),
    ("AI個人相簿停止營運", ""),
    ("個人相簿雲端平台停止營運", "網站與資料庫由服務商管理。"),
    ("雲端部署平台服務中斷兩天", ""),
    ("雲端部署平台服務中斷三天", ""),
    ("雲端部署平台服務中斷72小時", ""),
    ("雲端部署平台預計中斷四天", ""),
    ("雲端部署平台累計停機四天", ""),
    ("雲端部署平台間歇中斷四天", ""),
    ("雲端部署平台服務中斷數天", ""),
    ("Zeabur否認停止營運", ""),
    ("Zeabur舊叢集停止營運", ""),
])
def test_insufficient_or_excluded_platform_claims_cannot_bypass_policy_with_ai(title, summary):
    row = article(title, summary)
    assert not score_ai_relevance(row)["is_ai_related"]
    assert not platform_event_decision(row).admitted


@pytest.mark.parametrize("title,summary", [
    ("台南鐵路地下化通車", ""),
    ("新創公司談經營心得", "延伸閱讀：Zeabur宣布停止營運。"),
    ("雲端機房硬體投資趨勢", ""),
    ("n8n使用教學：如何處理資料外洩", ""),
])
def test_background_and_tutorials_do_not_create_platform_admission(title, summary):
    assert not score_ai_relevance(article(title, summary))["is_ai_related"]


def test_scope_cannot_be_spoofed_by_source_name_or_transport():
    for overrides in ({"url": "https://example.com/article/test"},
                      {"site_id": "opmlrss"}, {"source": "數位時代 (Google News)"}):
        assert not platform_event_decision(article("Zeabur宣布停止營運", **overrides)).applies


def test_platform_background_cannot_borrow_another_company_event():
    assert not platform_event_decision(article("Zeabur介紹部署市場", "Dify遭入侵，資料外洩。")).admitted
    assert not platform_event_decision(article("新創市場訪談", "Zeabur談發展方向。另一家公司遭入侵。")).admitted
    denial = article("Zeabur否認停止營運", "Zeabur此前被指結束營運。")
    assert "market" not in news.business_event_score(denial)


def test_outage_uses_explicit_evidence_not_article_age_or_fetch_clock():
    row = article("雲端部署平台中斷兩小時", published_at="2026-10-01T00:00:00Z")
    assert not platform_event_decision(row).admitted
    row = article("雲端部署平台持續中斷", "自2026-10-15T12:00:00Z開始，至今仍未恢復。")
    assert not platform_event_decision(row).admitted  # exactly 72h at publication
    row["published_at"] = "2026-10-18T12:01:00Z"
    assert platform_event_decision(row).admitted


@pytest.mark.parametrize("source,host", [("INSIDE", "www.inside.com.tw"),
                                        ("iThome", "www.ithome.com.tw"),
                                        ("TechNews 科技新報", "technews.tw")])
def test_native_feed_filters_before_cap_and_agrees_with_downstream(monkeypatch, source, host):
    feed = {"source_id": "inside" if source == "INSIDE" else "example", "title": source,
            "xml_url": "https://example.test/feed", "max_entries": 1,
            "include_keywords": news.TW_MEDIA_INCLUDE_KEYWORDS, "strict_title_filter": True}
    monkeypatch.setattr(news, "TW_MEDIA_FEEDS", (feed,))
    rows = [article("台南鐵路新聞", url=f"https://{host}/noise{i}") for i in range(10)]
    rows += [article("雲端部署平台新星宣布停止營運", url=f"https://{host}/shutdown")]
    session = SimpleNamespace(get=lambda *_a, **_k: SimpleNamespace(content=xml(rows), raise_for_status=lambda: None))
    items, health = news.fetch_tw_media_with_status(session, NOW)
    assert len(items) == 1 and items[0].url.endswith("/shutdown")
    assert health["ok"] and not health["degraded"]
    row = {**items[0].__dict__, **items[0].meta}
    assert score_ai_relevance(row)["is_ai_related"]
    assert "market" in news.business_event_score(row)


def parse_runtime(rows):
    return news.parse_model_analysis_feed_items(xml(rows), news.RUNTIMEWIRE_MODEL_FEED, NOW,
                                               site_id="runtimewire", site_name="RuntimeWire AI媒體")


def test_runtimewire_filters_catalog_before_limit_and_admits_security():
    rows = [article("New model Qwen3-8B", url=f"https://runtimewire.com/models/{n}") for n in range(15)]
    rows += [article("OpenCode warns users to rotate provider keys after legacy-system intrusion",
                     url="https://runtimewire.com/article/opencode-security")]
    items = parse_runtime(rows)
    assert len(items) == 1 and items[0].url.endswith("/opencode-security")
    row = {**items[0].__dict__, **items[0].meta}
    assert score_ai_relevance(row)["is_ai_related"]
    assert "security" in news.business_event_score(row)


def test_catalog_only_is_healthy_zero_but_html_is_failure():
    assert parse_runtime([article("New model Qwen3", url="https://runtimewire.com/models/qwen")]) == []
    assert parse_runtime([]) == []
    with pytest.raises(ValueError):
        news.parse_model_analysis_feed_items(b"<html>not RSS</html>", news.RUNTIMEWIRE_MODEL_FEED, NOW,
                                            site_id="runtimewire", site_name="RuntimeWire AI媒體")


def test_retained_catalog_is_excluded_before_all_reader_and_translation_without_archive_mutation():
    row = article("New model GPT-6", site_id="runtimewire", source="RuntimeWire",
                  url="https://runtimewire.com/models/gpt-6")
    before = deepcopy(row)
    assert not news.is_within_reader_window(row, NOW, 24)
    assert not score_ai_relevance(row)["is_ai_related"]
    assert row == before


def test_security_does_not_wait_for_outage_threshold_and_shutdown_is_not_security():
    security = article("雲端部署平台遭入侵，服務中斷兩天", "")
    assert platform_event_decision(security).admitted
    shutdown = article("Zeabur宣布停止營運", "")
    assert "security" not in news.business_event_score(shutdown)
