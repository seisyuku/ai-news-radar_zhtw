from datetime import datetime, timezone

import pytest

from scripts import corroboration as c
from scripts.update_news import build_story_record, story_passes_brief_gate
from tests.js_bridge import extract_declarations, run_js


def item(url, source="Test Feed", site="curated_media", **extra):
    return {"id": url, "url": url, "source": source, "site_id": site,
            "title": "AI product announcement", "published_at": "2026-10-22T00:00:00Z",
            "ai_is_related": True, "ai_score": .8, **extra}


@pytest.mark.parametrize("row,key,status", [
    (item("https://news.google.com/rss/articles/opaque", "Reuters AI (Google News)"), "publisher:reuters", "identified"),
    (item("https://news.google.com/rss/articles/opaque", "Meta AI (Google News)"), None, "unknown"),
    (item("https://news.google.com/a", "DeepSeek (Google News)", title_original="AI release - Reuters"), "publisher:reuters", "identified"),
    (item("https://news.google.com/a", "Reuters AI (Google News)", title_original="AI release - CNBC"), None, "conflict"),
    (item("https://cnbc.com/a", "Reuters AI (Google News)"), None, "conflict"),
    (item("https://reuters.com.attacker.test/a"), None, "unknown"),
    (item("https://fake-reuters.com/a"), None, "unknown"),
    (item("https://news.google.com.attacker.test/a", "Reuters AI (Google News)"), None, "unknown"),
    (item("https://unknown.test/a", "OpenAI News", "opmlrss"), None, "unknown"),
    (item("https://reuters.com/a", "private label", "opmlrss"), "publisher:reuters", "identified"),
    (item("https://github.com/random/project"), None, "unknown"),
    (item("https://github.com/openai/skills/commits/main.atom", "OpenAI Skills", "official_ai"), "publisher:openai", "identified"),
    (item("https://github.com/openai/skills/commit/abcdef", "OpenAI Skills", "official_ai"), "publisher:openai", "identified"),
    (item("https://github.com/openai/skills-fake/commit/abcdef", "OpenAI Skills", "official_ai"), None, "unknown"),
    (item("javascript:alert(1)", "Reuters AI (Google News)"), None, "unknown"),
])
def test_bounded_identity_and_conflicts(row, key, status):
    assert c.identity(row) == (key, status)
    assert row.get("corroboration_key") is None  # resolver doesn't mutate input


def test_versions_and_ingress_preserve_refs_but_not_votes():
    rows = [item(f"https://reuters.com/{i}") for i in range(5)]
    rows.append(item(rows[0]["url"], "private label", "opmlrss"))
    story = build_story_record("same", rows, datetime(2026, 10, 22, tzinfo=timezone.utc), 24)
    assert story["source_count"] == story["item_count"] == len(story["sources"]) == 6
    assert story["corroboration_count"] == story["duplicate_count"] == 1
    assert story["importance_breakdown"]["story_heat"] == 0
    assert not story_passes_brief_gate({**story, "score": .71})
    assert story_passes_brief_gate({**story, "score": .72})
    assert c.count(rows + [item("https://unknown.test/x")]) == 1
    assert c.count(rows + [item("https://cnbc.com/x")]) == 2
    assert not story_passes_brief_gate({"source_count": 99, "duplicate_count": 99, "score": .71})


def test_official_aliases_and_existing_ecosystem_are_not_extra_votes():
    assert c.count([item("https://openai.com/a"), item("https://openai.com/b"),
                    item("https://github.com/openai/skills")]) == 1
    assert c.count([item("https://blog.google/a"), item("https://deepmind.google/b"),
                    item("https://cloud.google.com/blog/c")]) == 1
    assert c.count([item("https://example.test/a", site="aibase"),
                    item("https://example.test/b", site="kr36_ai"),
                    item("https://example.test/c", site="juya_daily"),
                    item("https://aibase.com/d", site="opmlrss")]) == 1


@pytest.mark.parametrize("bad", [None, True, -1, 1.5, "2", float("inf"), 2**53])
def test_bad_new_counts_and_legacy_raw_counts_cannot_upgrade(bad):
    story = {"corroboration_count": bad, "source_count": 9, "duplicate_count": 9}
    assert c.story_count(story) == 0
    story["sources"] = [{"corroboration_key": "publisher:reuters"}] * 5
    assert c.story_count(story) == 1


def test_frontend_real_count_tag_and_merge_paths_agree():
    code = extract_declarations("storySourceCount", "rowSourceCount", "clusterBriefEvents",
                                "headlineClusterScore", "itemTagLabels")
    result = run_js(code + """
const state = {activeSection: 'hot'};
function itemSections() { return new Set(); }
function eventKey() { return 'same-event'; }
function sourceSignal(x) { return x.source; }
function sourcePriority() { return 0; }
function timelineMs() { return 0; }
function itemPriorityScore() { return 50; }
const x = {source: 'Reuters', corroboration_key: 'publisher:reuters'};
const y = {source: 'CNBC', corroboration_key: 'publisher:cnbc'};
const same = clusterBriefEvents(Array.from({length:5}, (_, index) => ({item:x,score:50,index})))[0];
const mixed = clusterBriefEvents([{item:x,score:50,index:0},{item:y,score:50,index:1}])[0];
console.log(JSON.stringify({
 sameCount: rowSourceCount(same), sameTags: itemTagLabels(x,same),
 sameScore: headlineClusterScore(same), oneScore: headlineClusterScore({...same,mergedCount:1}),
 mixedCount: rowSourceCount(mixed), mixedTags: itemTagLabels(x,mixed),
 legacy: storySourceCount({duplicate_count:9, source_count:9}),
 zero: storySourceCount({corroboration_count:0, sources:[x,y]}),
 malformed: [null,true,-1,1.5,'2',Infinity].map(corroboration_count => storySourceCount({corroboration_count, sources:[x,x]})),
 refs: same.rows.length
}));
""")
    assert result["sameCount"] == 1 and result["refs"] == 5
    assert result["sameTags"] == [] and result["mixedTags"] == ["多方報導"]
    assert result["mixedCount"] == 2
    assert result["sameScore"] == result["oneScore"]
    assert result["legacy"] == result["zero"] == 0
    assert result["malformed"] == [1] * 6
