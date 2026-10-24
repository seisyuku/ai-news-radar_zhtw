"""Candidate source identity and reader eligibility, without collector registration."""
import json
from datetime import datetime, timedelta, timezone

from scripts import candidate_feed_admission as candidate
from scripts import publisher_governance, publisher_policy, update_news
from tests.js_bridge import extract_declarations, run_js


CASES = (
    ("cyberq", "OpenAI 發布 AI 模型更新", "https://cyberq.tw/example-openai-model", 0.76, True),
    ("alphalab", "Anthropic 發布 AI Agent 工具", "https://www.alphalab.site/example-anthropic-agent", 0.71, False),
)


def test_planned_tw_media_subsources_compete_in_reader_selection_without_featured_grant():
    now = datetime(2026, 10, 25, 0, 30, tzinfo=timezone.utc)
    feeds = update_news.publisher_feed_configs() + [
        ("tw_media", {"title": spec["title"], "source_id": sid, "xml_url": spec["url"]})
        for sid, spec in candidate.FEEDS.items()
    ]
    public_rows = []
    for sid, title, url, ai_score, _selected in CASES:
        record = {"site_id": "tw_media", "site_name": "TW Media", "source": candidate.FEEDS[sid]["title"],
                  "title": title, "title_original": title, "summary": "", "url": url,
                  "published_at": "2026-10-24T12:00:00Z"}
        scored = update_news.add_ai_relevance_fields(record)
        annotated = publisher_policy.annotate(scored, feeds=feeds)
        qualified = publisher_governance.qualify(annotated, publisher_governance.source_material(record))
        assert annotated["ingress"]["source_id"] == sid
        assert scored["ai_is_related"] and qualified["scope"] == "in_scope"
        policy = annotated["source_policy"]
        assert policy["scope_id"] == sid
        assert policy["source_tier_rank"] == 6
        assert policy["allow_general"] and not policy["allow_featured"] and not policy["allow_radar"]
        assert update_news.corroboration.identity(annotated)[0] is None
        assert update_news.is_within_reader_window(record, now, 24)
        public_rows.append({**scored, "ai_score": ai_score, "source_tier_rank": policy["source_tier_rank"]})

    declarations = extract_declarations(
        "scorePercent", "sourceTierPercent", "editorialPercent", "freshnessPercent",
        "itemPriorityScore", "timelineIso", "timelineMs", "highPriorityScore", "isHighPriorityItem",
    )
    script = declarations + "\nconst state={generatedAt:'2026-10-25T00:30:00Z'};\n"
    script += "Date.now=()=>Date.parse('2026-10-25T00:30:00Z');\n"
    script += "const rows=" + json.dumps(public_rows, ensure_ascii=False) + ";\n"
    script += "console.log(JSON.stringify(rows.map(row=>({selected:isHighPriorityItem(row),priority:itemPriorityScore(row)}))));"
    browser = run_js(script)
    assert [row["selected"] for row in browser] == [expected for *_rest, expected in CASES]
    assert all(row["priority"] < 82 for row in browser)


def test_candidate_sources_follow_sitewide_24_hour_reader_window():
    now = datetime(2026, 10, 25, 0, 30, tzinfo=timezone.utc)
    for sid, title, url, *_ in CASES:
        record = {"site_id": "tw_media", "source": candidate.FEEDS[sid]["title"],
                  "title": title, "url": url,
                  "published_at": (now - timedelta(hours=24)).isoformat()}
        assert update_news.is_within_reader_window(record, now, 24)
        record["published_at"] = (now - timedelta(hours=24, seconds=1)).isoformat()
        assert not update_news.is_within_reader_window(record, now, 24)
