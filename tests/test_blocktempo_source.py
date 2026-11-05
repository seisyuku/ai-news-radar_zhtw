"""BlockTempo trial: native metadata, bounded intake and general-only use."""
import json
import sys
from datetime import datetime, timedelta, timezone

import pytest

from scripts import blocktempo_source as source
from scripts import update_news as u


NOW = datetime(2026, 11, 5, 6, 30, tzinfo=timezone.utc)


def post(slug="model-release", title="OpenAI 發布 ChatGPT Images 2.6", **changes):
    row = {"id": 555449, "date_gmt": "2026-11-05T03:07:49",
           "link": f"https://www.blocktempo.com/{slug}/", "categories": [309],
           "title": {"rendered": title},
           "excerpt": {"rendered": "<p>OpenAI 新增 GIF 動圖功能；API 價格不變。<a href='https://example.com/announcement'>來源</a></p>",
                       "protected": False}}
    row.update(changes)
    return row


def payload(*rows):
    return json.dumps(list(rows), ensure_ascii=False).encode()


class Response:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        pass


class Session:
    def __init__(self, content):
        self.content, self.calls = content, []

    def get(self, url, **kwargs):
        self.calls.append(url)
        assert url == source.API_URL  # Never fetch stale RSS, linked prose or media.
        return Response(self.content)


def trial_feed():
    return next(f for f in u.TW_MEDIA_FEEDS if f["source_id"] == source.SOURCE_ID)


def test_json_route_keeps_latest_native_time_and_excerpt_without_fetching_links():
    session = Session(payload(post()))
    rows = source.fetch_posts(session, NOW)
    assert session.calls == [source.API_URL]
    assert rows[0]["published_at"] == "2026-11-05T03:07:49Z"
    assert rows[0]["summary"] == "OpenAI 新增 GIF 動圖功能；API 價格不變。 來源"
    assert rows[0]["publisher_links"] == ["https://example.com/announcement"]
    assert trial_feed()["ingress_kind"] == "public_json"


@pytest.mark.parametrize("date", [None, "", "0000-00-00T00:00:00", "2026-02-30T03:07:49",
    "2026-11-05", "2026-11-05T03:07:49+08:00", "2026-11-05T03:07:49Z"])
def test_no_date_guessing_or_modified_date_fallback(date):
    with pytest.raises(ValueError, match="invalid_blocktempo_fields"):
        source.parse_posts(payload(post(date_gmt=date, modified_gmt="2026-11-05T03:07:49")), NOW)


@pytest.mark.parametrize("url", ["http://www.blocktempo.com/article/", "https://blocktempo.com/article/",
    "https://www.blocktempo.com.evil.example/article/", "https://evil.example/article/",
    "https://user@www.blocktempo.com/article/", "https://www.blocktempo.com:8443/article/",
    "https://www.blocktempo.com/category/business/ai/", "https://www.blocktempo.com/article/?redirect=evil",
    "https://www.blocktempo.com/article/#update"])
def test_only_native_canonical_article_urls(url):
    with pytest.raises(ValueError, match="invalid_blocktempo_fields"):
        source.parse_posts(payload(post(link=url)), NOW)


@pytest.mark.parametrize("content", [b"<html>challenge</html>", b"{}", b"null", b'[{"broken": true}]', b'[null]'])
def test_bad_structure_is_failure_not_healthy_empty(content):
    with pytest.raises(ValueError):
        source.parse_posts(content, NOW)


def test_valid_empty_excluded_old_and_future_are_healthy_zero():
    assert source.parse_posts(b"[]", NOW) == []
    assert source.parse_posts(payload(post(categories=[7])), NOW) == []
    assert source.parse_posts(payload(post(date_gmt="2026-10-29T03:07:49")), NOW) == []
    assert source.parse_posts(payload(post(date_gmt="2026-11-05T06:30:01")), NOW) == []


@pytest.mark.parametrize("change", [{"categories": ["309"]}, {"categories": None},
    {"title": {"rendered": None}}, {"excerpt": {"rendered": "private", "protected": True}},
    {"excerpt": {"protected": False}}])
def test_required_fields_fail_even_with_excluded_peers(change):
    with pytest.raises(ValueError, match="invalid_blocktempo_fields"):
        source.parse_posts(payload(post(categories=[7]), post(**change)), NOW)


@pytest.mark.parametrize("title", [
    "巨鯨做空Anthropic上市前合約，空單加到2,546萬鎂",
    "AI 股市槓桿交易爆倉", "RTX 50 系列板卡本週漲價",
    "明治巧克力香菇山 AI 耳機募資破億", "Grok Bot 最強教學：7個調教 Agent 的方式",
    "Claude Code 每日彙整與產業精選", "OpenAI 廣編合作推廣",
    "Andrej Karpathy 用 Claude 做出 HackerTube", "Gemini 把魚肉認成蛇肉",
])
def test_source_noise_is_filtered_before_cap(title):
    assert source.parse_posts(payload(post(title=title)), NOW) == []


@pytest.mark.parametrize("title", [
    "開發工具 Postman 會自動幫 AI 代理裝外掛，不需開發者批准同意",
    "英科技公司 Revolut 改用自架 GLM 寫程式，比Claude便宜九成",
    "Anthropic Q3 財報：營收增長與營業虧損",
    "ChatGPT 聊天與 Codex 開始共用額度，Plus 用戶不滿",
    "Claude 新規禁止用訂閱額度開中轉站",
])
def test_business_and_policy_news_still_reach_shared_checks(title):
    assert len(source.parse_posts(payload(post(title=title)), NOW)) == 1


def test_filter_dedup_and_sort_before_cap():
    noise = [post(f"noise-{i}", title="巨鯨做空Anthropic合約") for i in range(10)]
    good = [post(f"model-{i}", date_gmt=f"2026-11-05T03:{i:02}:00") for i in range(10)]
    rows = source.parse_posts(payload(*noise, *good, good[-1]), NOW)
    assert len(rows) == 8
    assert [r["url"] for r in rows] == [p["link"].rstrip("/") for p in reversed(good[2:])]


def test_response_and_row_limits():
    with pytest.raises(ValueError, match="too_large"):
        source.parse_posts(b" " * (source.MAX_BYTES + 1), NOW)
    with pytest.raises(ValueError, match="invalid_blocktempo_posts"):
        source.parse_posts(payload(*[post() for _ in range(31)]), NOW)


def test_untrusted_html_stays_text_only_and_content_field_is_not_evidence():
    row = post(title="OpenAI &amp; AI 發布 <b>新功能</b><script>bad()</script>",
               excerpt={"protected": False, "rendered": "<p>AI 摘要</p><script>bad()</script><table><tr><td>999億</td></tr></table>"},
               content={"rendered": "完整一手引用與大量新事實"})
    result = source.parse_posts(payload(row), NOW)[0]
    assert result["title"] == "OpenAI & AI 發布 新功能"
    assert result["summary"] == "AI 摘要"
    assert "999" not in str(result) and "完整一手" not in str(result)


def test_trial_cannot_inherit_tw_rank_or_grant_featured_or_radar(monkeypatch):
    monkeypatch.setattr(u, "TW_MEDIA_FEEDS", (trial_feed(),))
    raw, health = u.fetch_tw_media_with_status(Session(payload(post())), NOW)
    assert health["ok"] and health["subsources"][0]["source_id"] == "blocktempo_ai"
    r = raw[0]
    result = u.add_reader_source_policy_fields({"site_id": r.site_id, "source": r.source,
        "title": r.title, "url": r.url, "published_at": u.iso(r.published_at), **r.meta})
    assert result["ingress"]["source_id"] == "blocktempo_ai"
    assert result["source_policy"]["source_tier_rank"] == 6
    assert result["source_policy"]["admission_status"] == "unreviewed"
    assert result["source_policy"]["allow_general"]
    assert not result["source_policy"]["allow_featured"]
    assert not result["source_policy"]["allow_radar"]


def test_bad_json_degrades_group_without_dropping_healthy_rss_peer(monkeypatch):
    peer = {"source_id": "peer", "title": "Peer", "xml_url": "https://example.com/rss"}
    monkeypatch.setattr(u, "TW_MEDIA_FEEDS", (trial_feed(), peer))
    class MixedSession:
        def get(self, url, **kwargs):
            return Response(b"{}" if url == source.API_URL else b'<rss version="2.0"><channel><title>Peer</title></channel></rss>')
    rows, status = u.fetch_tw_media_with_status(MixedSession(), NOW)
    assert rows == [] and status["ok"] and status["degraded"]
    assert [(r["source_id"], r["ok"]) for r in status["subsources"]] == [("blocktempo_ai", False), ("peer", True)]
    assert status["subsources"][0]["error"] == "invalid_source"


@pytest.mark.parametrize("expired", [False, True])
def test_full_generator_keeps_archive_resolver_window_and_general_only(tmp_path, monkeypatch, expired):
    now = NOW + timedelta(days=2) if expired else NOW
    monkeypatch.setattr(u, "TW_MEDIA_FEEDS", (trial_feed(),))
    session = Session(payload(post()))
    monkeypatch.setattr(u, "create_session", lambda: session)
    monkeypatch.setattr(u, "utc_now", lambda: now)
    def collect(client, clock):
        rows, health = u.fetch_tw_media_with_status(client, clock)
        return rows, [{"site_id": "tw_media", "site_name": "TW Media", "item_count": len(rows), **health}]
    monkeypatch.setattr(u, "collect_all", collect)
    monkeypatch.setattr(u, "run_market_sensors", lambda *_: ({"generated_at": u.iso(now), "signals": []}, {}, []))
    for key in ("GEMINI_API_KEY", "GROQ_API_KEY", "GOOGLE_TRANSLATE_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr("requests.sessions.Session.request", lambda *_a, **_k: pytest.fail("live network forbidden"))
    out = tmp_path / "data"
    monkeypatch.setattr(sys, "argv", ["update_news.py", "--output-dir", str(out), "--translate-max-new", "0"])
    assert u.main() == 0
    read = lambda name: json.loads((out / name).read_text())
    row = read("archive.json")["items"][0]
    assert row["published_at"] == "2026-11-05T03:07:49Z"
    assert read("items/" + row["id"] + ".json")["url"] == row["url"]
    latest = read("latest-24h.json")
    assert bool(latest["items_ai"]) is (not expired)
    if not expired:
        assert latest["items_ai"][0]["source_policy"]["source_tier_rank"] == 6
        assert not latest["items_ai"][0]["source_policy"]["allow_featured"]
    assert read("source-status.json")["failed_sites"] == []
    assert read("llm-radar.json")["events"] == []
    assert read("daily-brief.json")["items"] == []
