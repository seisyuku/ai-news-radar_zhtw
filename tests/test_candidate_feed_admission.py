"""Fixed source examples for the isolated CyberQ/AlphaLab admission stage."""
import json
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from scripts import candidate_feed_admission as admission
from scripts import update_news


NOW = datetime(2026, 10, 25, 0, 30, tzinfo=timezone.utc)
AI_CATEGORY = "https://www.alphalab.site/category/ai/"


def test_formal_feed_routes_match_isolated_admission_contract():
    configured = {feed["source_id"]: feed for feed in update_news.TW_MEDIA_FEEDS
                  if feed.get("candidate_prefilter")}
    assert set(configured) == set(admission.FEEDS)
    for sid, feed in configured.items():
        assert feed["xml_url"] == admission.FEEDS[sid]["url"]
        assert feed["title"] == admission.FEEDS[sid]["title"]
        assert feed["max_entries"] == admission.FEEDS[sid]["max_entries"]


def rss(*items):
    root = ET.Element("rss", version="2.0")
    channel = ET.SubElement(root, "channel")
    ET.SubElement(channel, "title").text = "Candidate feed"
    ET.SubElement(channel, "link").text = "https://www.alphalab.site/"
    ET.SubElement(channel, "description").text = "Public short descriptions"
    for title, link, published, category in items:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = title
        ET.SubElement(item, "link").text = link
        if published is not None:
            ET.SubElement(item, "pubDate").text = published
        else:
            ET.SubElement(item, "updated").text = "Sun, 25 Oct 2026 00:00:00 GMT"
        ET.SubElement(item, "description").text = "<p>公開短摘要；不保留全文。</p>"
        if category:
            ET.SubElement(item, "category", domain=category).text = "AI"
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def article(title, slug, category=AI_CATEGORY, published="Sat, 24 Oct 2026 16:01:00 GMT", source="alphalab"):
    host = "www.alphalab.site" if source == "alphalab" else "cyberq.tw"
    return title, f"https://{host}/{slug}", published, category


def test_alphalab_requires_real_ai_category_and_rejects_howto_before_cap():
    rejected = [article(f"【2026 最新】Claude Code 教學 {n}", f"guide-{n}") for n in range(9)]
    accepted = article("OpenAI Google Cloud 合作解析：模型與 Codex 進入雲端採購", "cloud-partnership")
    missed_by_generic_title = article("Kimi K3.1 Pro 解析：評測升至 55 分，API 已上線", "kimi-analysis")
    ai_standard = article("Agent Skills 移交 AAIF：標準走向共管", "agent-skills")
    not_ai = article("企業年度營收解析", "revenue")
    wrong_category = article("Anthropic 發布 AI 模型", "finance-ai", "https://www.alphalab.site/category/finance/")
    spoofed_category = article("Anthropic 發布 AI 模型", "fake-ai", "https://other.example/category/ai/")
    rows, status = admission.preselect_feed(rss(*rejected, wrong_category, spoofed_category,
                                                not_ai, accepted, missed_by_generic_title, ai_standard), "alphalab", NOW)
    assert [row["title"] for row in rows] == [accepted[0], missed_by_generic_title[0], ai_standard[0]]
    assert status["rejected"] == {"outside_ai_category": 2, "no_ai_signal": 1, "tutorial": 9}
    assert rows[0]["summary"] == "公開短摘要；不保留全文。"


def test_cyberq_known_roundup_and_incidental_titles_leave_independent_test():
    items = [
        article("GitHub 趨勢周報 Vol.39：Anthropic 官方外掛庫、DeepSeek 推論框架開源", "weekly", source="cyberq"),
        article("OpenAI 兆元估值挑戰 IPO｜產業精選 10.23", "roundup", source="cyberq"),
        article("Calif 以 AI 協助破解 iPhone：iPhone Duo 上市當天遭攻破", "iphone", source="cyberq"),
        article("黃金躍升美國最大出口品，各國央行金庫與 AI 伺服器搶材料", "gold", source="cyberq"),
        article("資安用拉丁文防禦、駭客用俚語攻擊？從 K8s 到 Prompt 的科技字根", "prompt-etymology", source="cyberq"),
        article("實測 DeepSeek-V4.1-Flash-1017 雙機 DGX Spark：TensorFold 比 vLLM 快 2.2 倍", "deepseek", source="cyberq"),
        article("實測 FLUX 3 Image Klein：單張 16 秒，prompt 擴寫器不能省", "flux", source="cyberq"),
    ]
    rows, status = admission.preselect_feed(rss(*items), "cyberq", NOW)
    assert [row["title"] for row in rows] == [items[-2][0], items[-1][0]]
    assert status["rejected"] == {"incidental_ai": 2, "no_ai_title_signal": 1, "roundup": 2}


def test_metadata_host_time_and_deduplication():
    good = article("OpenAI 發布新 AI 模型", "release")
    rows, status = admission.preselect_feed(rss(
        article("OpenAI 發布新 AI 模型", "wrong", source="cyberq"),
        article("OpenAI 發布新 AI 模型", "old", published="Sun, 18 Oct 2026 00:00:00 GMT"),
        article("OpenAI 發布新 AI 模型", "future", published="Sun, 25 Oct 2026 01:00:00 GMT"),
        good, good,
    ), "alphalab", NOW)
    assert len(rows) == 1
    assert status["rejected"] == {"duplicate": 1, "outside_five_days": 2, "wrong_article_host": 1}


def test_updated_is_not_publication_and_invalid_feed_is_failure():
    with pytest.raises(ValueError, match="invalid_feed_fields"):
        admission.preselect_feed(rss(article("OpenAI 發布 AI 模型", "updated-only", published=None)), "alphalab", NOW)
    with pytest.raises(ValueError, match="invalid_feed"):
        admission.preselect_feed(b"<html>not a feed</html>", "cyberq", NOW)
    rows, status = admission.preselect_feed(rss(), "alphalab", NOW)
    assert rows == [] and status["feed_entries"] == 0


def test_xml_fallback_preserves_category_scheme(monkeypatch):
    monkeypatch.setattr(update_news, "feedparser", None)
    row = article("Claude 形式驗證解析：AI 安全證明", "formal-proof")
    rows, _ = admission.preselect_feed(rss(row), "alphalab", NOW)
    assert len(rows) == 1


def test_shadow_probe_writes_status_without_promoting_sources(tmp_path):
    class Response:
        def __init__(self, content):
            self.content = content

        def raise_for_status(self):
            pass

    class Session:
        def get(self, url, **_kwargs):
            if "cyberq.tw" in url:
                return Response(rss(article("OpenAI 發布 AI 模型", "release", source="cyberq")))
            return Response(rss())

    result = admission.probe_live(tmp_path, NOW, Session())
    assert [row["status"] for row in result["sources"]] == ["ok", "ok"]
    assert [row["candidate_count"] for row in result["sources"]] == [1, 0]
    saved = json.loads((tmp_path / "candidate-items.json").read_text(encoding="utf-8"))
    assert [row["source_id"] for row in saved["items"]] == ["cyberq"]
    assert json.loads((tmp_path / "source-status.json").read_text(encoding="utf-8")) == result


def test_production_tw_media_route_keeps_candidate_filters_and_subsource_health(monkeypatch):
    feeds = tuple(feed for feed in update_news.TW_MEDIA_FEEDS
                  if feed["source_id"] in {"alphalab", "cyberq"})
    monkeypatch.setattr(update_news, "TW_MEDIA_FEEDS", feeds)
    bodies = {
        "alphalab": rss(
            article("OpenAI 發布 AI 模型更新", "model"),
            article("OpenAI 發布 AI 模型更新", "finance", category="https://www.alphalab.site/category/finance/"),
        ),
        "cyberq": rss(
            article("實測 DeepSeek-V4.1 雙機推論：延遲下降", "deepseek", source="cyberq"),
            article("OpenAI 產業精選：本週十則新聞", "roundup", source="cyberq"),
        ),
    }

    class Response:
        def __init__(self, content):
            self.content = content

        def raise_for_status(self):
            pass

    class Session:
        def get(self, url, **_kwargs):
            sid = next(feed["source_id"] for feed in feeds if feed["xml_url"] == url)
            return Response(bodies[sid])

    items, health = update_news.fetch_tw_media_with_status(Session(), NOW)
    assert [(item.source, item.url) for item in items] == [
        ("AlphaLab", "https://www.alphalab.site/model"),
        ("CyberQ 賽博客", "https://cyberq.tw/deepseek"),
    ]
    assert {row["source_id"]: (row["ok"], row["item_count"])
            for row in health["subsources"]} == {"alphalab": (True, 1), "cyberq": (True, 1)}
    assert all(update_news.is_within_reader_window(
        {"site_id": item.site_id, "published_at": update_news.iso(item.published_at)}, NOW, 24)
        for item in items)
