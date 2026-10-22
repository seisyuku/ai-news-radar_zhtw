"""Behavioral event identity, freshness and bounded history regressions."""
import copy
import json
from datetime import timedelta
from pathlib import Path

import pytest

from scripts import brief_events as b, update_news as u


@pytest.mark.parametrize("month,number", [("January",1),("Feb.",2),("March",3),("April",4),("May",5),("Jun",6),("July",7),("August",8),("Sep",9),("October",10),("Nov",11),("December",12)])
def test_security_announcement_calendar_is_not_specific_to_case_month(month, number):
    now = b.parse("2026-12-23T12:00:00Z")
    c = b.extract_claim({"id":"calendar-case","title":"OpenSSL vulnerability disclosure", "summary":f"Coordinated announcement on {month} 8.","url":"https://example.com/security","published_at":b.stamp(now)},now)
    assert f"announcement_day:2026-{number:02}-08" in c.facts


def test_security_announcement_calendar_rejects_impossible_day_and_resolves_year():
    now = b.parse("2026-01-05T12:00:00Z")
    c = b.extract_claim({"id":"calendar-case","title":"OpenSSL vulnerability disclosure", "summary":"Coordinated announcement on December 28; February 31.","url":"https://example.com/security","published_at":b.stamp(now)},now)
    assert "announcement_day:2025-12-28" in c.facts
    assert not any("02-31" in fact for fact in c.facts)

FIXTURE = json.loads((Path(__file__).parent / "fixtures/brief_events_development.json").read_text())
RECORDS = {r["id"]: r for r in FIXTURE["records"]}
CASES = [c for c in FIXTURE["expectations"] if c["evidence_type"] == "observed_development"]


def run(rows, *, history=None, now=None, previous=None):
    history = copy.deepcopy(history if history is not None else rows)
    if now is None:
        now = max(max(b.parse(r["published_at"]) or b.parse(r["first_seen_at"]),
                      b.parse(r["first_seen_at"]) or b.parse(r["published_at"])) for r in rows) + timedelta(hours=1)
    items = []
    for row in rows:
        r = u.add_source_tier_fields(u.add_ai_relevance_fields(copy.deepcopy(row)))
        r["business_events"] = u.business_event_score(r)
        items.append(r)
    stories = u.merge_story_items(items, now, 24)
    return u.build_brief_event_payloads(stories, history, previous or b.StateInput("missing"), now, 24,
                                      archive_meta=b.ArchiveMeta("valid", b.stamp(now)))


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["case_id"])
def test_development_partitions_and_phase_boundaries(case):
    rows = [RECORDS[i] for i in case["member_ids"]]
    history = list(RECORDS.values()) if case["case_id"] == "GEMINI_AMBIGUOUS_REPOST" else rows
    result = run(rows, history=history)
    assert result.projection["status"] != "unavailable", result.diagnostics
    expected = {frozenset(g) for g in case["expected_root_partition"]}
    ids = set(case["member_ids"])
    actual = {frozenset(ids & set(e["member_article_ids"])) for e in result.projection["events"]
              if ids & set(e["member_article_ids"])}
    assert actual == expected
    if case["expected_phase_count"] is not None:
        assert sum(len(e["phases"]) for e in result.next_state["events"]) == case["expected_phase_count"]
    for e in result.projection["events"]:
        assert set(e["member_article_ids"]) == {r["id"] for r in e["sources"]}
        assert e["duplicate_count"] == max(1, e["corroboration_count"])
        for r in e["sources"]:
            assert r["published_at"] == RECORDS[r["id"]]["published_at"]


def article(aid, title="Introducing GPT-6.1 Sol", *, day=1, summary="", source="OpenAI News", url=None):
    t = f"2026-10-{day:02}T10:00:00Z"
    return {"id": aid, "title": title, "summary": summary, "url": url or f"https://openai.com/index/{aid}/",
            "source": source, "site_id": "official_ai", "site_name": "Official",
            "published_at": t, "first_seen_at": t, "last_seen_at": t}


def test_reposts_do_not_renew_initial_or_phase_clock():
    original = article("first")
    now = b.parse(original["published_at"]) + timedelta(hours=1)
    first = run([original], now=now)
    repeat = article("repeat", day=3)
    later = run([repeat], history=[original, repeat], now=b.parse(repeat["published_at"]),
                previous=b.StateInput("valid", first.next_state))
    assert len(later.projection["events"]) == 1
    e = later.projection["events"][0]
    assert not e["eligible"]
    assert e["initial_effective_at"] == original["published_at"]
    assert e["last_material_at"] is None
    assert e["last_reported_at"] == repeat["published_at"]
    assert first.projection["events"][0]["brief_event_id"] == e["brief_event_id"]


def test_real_update_then_repeated_update_keeps_first_report_time():
    rows = [RECORDS[i] for i in next(c for c in CASES if c["case_id"] == "PHP_EXPLOIT_UPDATE")["member_ids"]]
    result = run(rows)
    before = result.projection["events"][0]
    assert before["last_material_at"] == rows[1]["published_at"]
    rewrite = copy.deepcopy(rows[1])
    rewrite.update(id="later-update", url="https://wired.com/later-update", published_at="2026-10-23T03:00:00Z", last_seen_at="2026-10-23T03:00:00Z")
    later = run([rewrite], history=rows + [rewrite], previous=b.StateInput("valid", result.next_state))
    event = later.projection["events"][0]
    assert event["last_material_at"] == before["last_material_at"]
    assert not event["eligible"]


def test_poc_and_risk_warning_are_not_observed_exploitation():
    a = article("poc", "PHP security release", summary="Two unauthenticated RCE flaws. PoC exploits circulating since yesterday; attackers could exploit them.")
    claim = b.extract_claim(a, b.parse(a["published_at"]))
    assert claim.phase == "baseline"


def test_disjoint_vulnerability_batches_and_models_do_not_bridge():
    a = article("a", "PHP vulnerability CVE-2026-10001", summary="OpenAI found two flaws")
    c = article("c", "PHP vulnerability CVE-2026-20002", summary="OpenAI found two flaws", day=15)
    result = run([a, c])
    assert len(result.projection["events"]) == 2
    a = article("m1", "Introducing GPT-6.1 Sol")
    c = article("m2", "Introducing GPT-6 Astra")
    bridge = article("compare", "GPT-6.1 Sol and GPT-6 Astra compared")
    result = run([a, c, bridge])
    assert len(result.projection["events"]) == 3


def test_undated_is_system_first_observed_and_not_material_update():
    r = article("undated", "Example model update")
    r["published_at"] = None
    result = run([r])
    assert result.projection["events"][0]["initial_basis"] == "first_observed"
    assert result.projection["events"][0]["last_material_at"] is None


def test_permutation_purity_and_same_asof_rerun():
    rows = [RECORDS[i] for i in CASES[0]["member_ids"]]
    saved = copy.deepcopy(rows)
    now = b.parse("2026-10-22T12:13:58.089128Z")
    first = run(rows, now=now)
    reverse = run(list(reversed(rows)), now=now)
    assert first.projection == reverse.projection
    assert first.next_state == reverse.next_state
    repeat = run(rows, now=now, previous=b.StateInput("valid", first.next_state))
    # Recovery mode/generation changes from recovered to ready; semantic data don't.
    assert first.projection["events"] == repeat.projection["events"]
    assert first.next_state == repeat.next_state
    assert rows == saved


@pytest.mark.parametrize("status", ["missing", "corrupt"])
def test_history_recovery_uses_earliest_archive_report(status):
    old, new = article("old"), article("new", day=3)
    result = run([new], history=[old, new], previous=b.StateInput(status))
    assert result.projection["status"] == "recovered"
    assert not result.projection["events"][0]["eligible"]


def test_bad_history_and_future_schema_fail_closed():
    a = article("a")
    stories = u.merge_story_items([a], b.parse(a["published_at"]), 24)
    for state, meta in [(b.StateInput("unsupported"), b.ArchiveMeta("valid", a["published_at"])),
                        (b.StateInput("missing"), b.ArchiveMeta("missing"))]:
        result = b.build_brief_events(stories=stories, archive_records=[], archive_meta=meta,
                                     previous_state=state, now=b.parse(a["published_at"]))
        assert result.next_state is None
        assert not result.projection["events"] and not result.daily_items


def test_state_revision_integrity_and_unknown_schema_load(tmp_path):
    result = run([article("a")])
    assert b.validate_state(result.next_state)
    p = tmp_path / b.STATE_FILE
    p.write_bytes(b.canonical(result.next_state))
    assert b.load_state(p).status == "valid"
    broken = copy.deepcopy(result.next_state)
    broken["events"][0]["initial_effective_at"] = "bad"
    p.write_bytes(b.canonical(broken))
    assert b.load_state(p).status == "corrupt"
    p.write_text('{"schema_version":2}')
    assert b.load_state(p).status == "unsupported"


def test_capacity_does_not_replace_history(monkeypatch):
    monkeypatch.setattr(b, "MAX_EVENTS", 0)
    result = run([article("a")])
    assert result.next_state is None and result.projection["status"] == "unavailable"
    assert result.diagnostics["errors"] == ["state_capacity"]


def test_same_publisher_and_old_phase_refs_are_not_extra_votes():
    ids = next(c["member_ids"] for c in CASES if c["case_id"] == "HAIKU_55_REPOST")
    rows = [RECORDS[i] for i in ids[1:]]
    result = run(rows)
    assert result.projection["events"][0]["corroboration_count"] == 1
    assert len(result.projection["events"][0]["sources"]) == 2


def test_future_publication_does_not_seed_brief():
    r = article("future", day=10)
    result = run([r], now=b.parse("2026-10-01T10:00:00Z"))
    assert not result.projection["events"]


def test_non_event_article_url_continuity_survives_long_bridge_urls():
    r = article("long", "AI company reports results", url="https://news.google.com/rss/articles/" + "a" * 800)
    result = run([r])
    assert result.projection["status"] != "unavailable" and len(result.projection["events"]) == 1
    assert not result.diagnostics["errors"]


def test_spacing_variants_and_price_conditions_are_concrete():
    a = article("a", "Introducing GPT-6.1Sol")
    c = article("c", "推出 GPT6.1 Sol")
    assert len(run([a, c]).projection["events"]) == 1
    a = article("p1", "GPT-6.1 Sol pricing changes", summary="Input price from $2 to $1 per million tokens, context 100k, effective 2026-10-01")
    c = article("p2", "GPT-6.1 Sol pricing changes", summary="Input price from $2 to $1 per million tokens, context 1000k, effective 2026-10-15", day=15)
    result = run([a, c])
    assert len(result.projection["events"]) == 2
    assert {e["identity"]["action"] for e in result.projection["events"]} == {"pricing_change"}


@pytest.mark.parametrize("text", ["AWS has not logged attempts", "PHP could be actively exploited", "No observed attacks exist", "Potential attackers may have observed exploitation"])
def test_negation_and_hypothetical_attacks_never_renew(text):
    r = article("negative", "PHP vulnerability report", summary=text)
    assert b.extract_claim(r, b.parse(r["published_at"])).phase == "baseline"


def test_unknown_publisher_cannot_qualify_material_update():
    r = article("untrusted", "PHP2Shell vulnerability report", summary="AWS logged attacks", source="Unknown", url="https://unknown.example/news")
    c = b.extract_claim(r, b.parse(r["published_at"]))
    assert c.unknown_update


def test_alias_references_survive_without_new_votes_or_primary():
    original = article("original")
    alias = {**original, "id": "alias", "duplicate_of": "original", "url": "https://openai.com/index/alias"}
    result = run([original], history=[original, alias])
    e = result.projection["events"][0]
    assert set(e["member_article_ids"]) == {"original", "alias"}
    assert e["corroboration_count"] == 1
    assert e["primary_item"]["id"] == "original"


def test_same_url_with_different_typed_action_is_not_erased():
    old = article("launch", "Introducing GPT-6.1 Sol")
    initial = run([old])
    newer = article("context", "GPT-6.1 Sol context grows", day=3,
                    summary="Default context changes from 272k to 500k", url=old["url"])
    result = run([newer], history=[newer], previous=b.StateInput("valid", initial.next_state))
    assert result.projection["events"][0]["brief_event_id"] != initial.projection["events"][0]["brief_event_id"]
    assert result.projection["events"][0]["eligible"]


def test_late_backdated_available_report_is_not_fresh():
    earlier = article("teaser", "GPT-6.1 Sol Ultrafast coming soon", day=1)
    recap = article("recap", "GPT-6.1 Sol Ultrafast now available for developers", day=15,
                    summary="OpenAI launched the speed tier on October 8th.")
    result = run([recap], history=[earlier, recap])
    e = result.projection["events"][0]
    assert not e["eligible"]
    assert b.parse(e["last_material_at"]) <= b.parse("2026-10-09T12:00:00Z")


def test_unresolved_article_promotes_to_anchor_without_losing_identity():
    weak = article("same", "PHP vulnerability report", summary="Security report")
    first = run([weak])
    richer = {**weak, "summary": "CVE-2026-12345 was found; two flaws"}
    result = run([richer], previous=b.StateInput("valid", first.next_state))
    assert result.projection["events"][0]["brief_event_id"] == first.projection["events"][0]["brief_event_id"]
    assert b.validate_state(result.next_state)


def test_public_projection_checksum_is_after_redaction():
    r = article("public", summary="Contact editor@example.invalid about this AI launch")
    result = run([r])
    projection = result.projection
    assert "editor@example.invalid" not in b.canonical(projection).decode()
    assert projection["generation_id"] == "bg1_" + b.digest({k: v for k, v in projection.items() if k != "generation_id"})[:24]


def test_root_overflow_keeps_previous_history_and_isolates_root(monkeypatch):
    rows = [RECORDS[i] for i in next(c for c in CASES if c["case_id"] == "PHP_EXPLOIT_UPDATE")["member_ids"]]
    first = run(rows[:1])
    monkeypatch.setattr(b, "MAX_PHASES", 1)
    later = run(rows, previous=b.StateInput("valid", first.next_state))
    assert not later.projection["events"]
    assert later.next_state["events"] == first.next_state["events"]
    assert any(e.startswith("history_overflow") for e in later.diagnostics["errors"])


def test_bundle_state_write_failure_does_not_publish_unpersisted_events(tmp_path, monkeypatch):
    now = b.parse("2026-10-01T11:00:00Z")
    result = run([article("a")], now=now)
    daily, merged = {"items": [], "selection_diagnostics": {}}, {"stories": [{"story_id": "original"}]}
    u.apply_brief_event_result(result, daily, merged)
    paths = {"state_path": tmp_path / b.STATE_FILE, "merged_path": tmp_path / "stories.json", "daily_path": tmp_path / "daily.json"}
    paths["state_path"].write_text("previous-state-bytes")
    writer = u.atomic_write_text
    def fail_state(path, text):
        if path == paths["state_path"]:
            raise OSError("synthetic write failure")
        return writer(path, text)
    monkeypatch.setattr(u, "atomic_write_text", fail_state)
    out = u.write_brief_event_bundle(result, daily, merged, **paths, now=now)
    assert out.projection["status"] == "unavailable"
    assert paths["state_path"].read_text() == "previous-state-bytes"
    assert json.loads(paths["merged_path"].read_text())["stories"] == [{"story_id": "original"}]
    assert not json.loads(paths["daily_path"].read_text())["items"]


def test_partial_bundle_keeps_newer_state_for_retry(tmp_path, monkeypatch):
    now = b.parse("2026-10-01T11:00:00Z")
    result = run([article("a")], now=now)
    daily, merged = {}, {"stories": []}
    u.apply_brief_event_result(result, daily, merged)
    paths = {"state_path": tmp_path / b.STATE_FILE, "merged_path": tmp_path / "stories.json", "daily_path": tmp_path / "daily.json"}
    writer = u.atomic_write_text
    def fail_projection(path, text):
        if path == paths["merged_path"]:
            raise OSError("synthetic interruption")
        return writer(path, text)
    monkeypatch.setattr(u, "atomic_write_text", fail_projection)
    with pytest.raises(OSError):
        u.write_brief_event_bundle(result, daily, merged, **paths, now=now)
    newer_state = b.load_state(paths["state_path"])
    assert newer_state.status == "valid"
    retry = run([article("a")], now=now, previous=newer_state)
    assert retry.projection["events"] == result.projection["events"]


def test_opposite_undated_actions_are_not_same_restatement():
    enabled = article("enable", "GPT-6.1 Sol access enabled in TW")
    disabled = article("disable", "GPT-6.1 Sol access disabled in TW")
    assert len(run([enabled, disabled]).projection["events"]) == 2


def test_late_earlier_evidence_moves_initial_backward_only():
    newer = article("newer", day=3)
    initial = run([newer])
    earlier = article("earlier", day=1)
    earlier["first_seen_at"] = newer["first_seen_at"]
    result = run([newer], history=[newer, earlier], previous=b.StateInput("valid", initial.next_state))
    e = result.projection["events"][0]
    assert e["initial_effective_at"] == earlier["published_at"]
    assert e["brief_event_id"] == initial.projection["events"][0]["brief_event_id"]
    assert not e["eligible"]


def test_unsupported_state_bytes_are_not_overwritten_by_bundle(tmp_path):
    now = b.parse("2026-10-01T11:00:00Z")
    result = b.unavailable(now, "unsupported_state_schema")
    daily, merged = {}, {"stories": []}
    u.apply_brief_event_result(result, daily, merged)
    paths = {"state_path": tmp_path / b.STATE_FILE, "merged_path": tmp_path / "stories.json", "daily_path": tmp_path / "daily.json"}
    paths["state_path"].write_text('{"schema_version":2}')
    u.write_brief_event_bundle(result, daily, merged, **paths, now=now)
    assert paths["state_path"].read_text() == '{"schema_version":2}'


def test_generated_summary_survives_only_for_the_exact_same_primary():
    row = article("a")
    now = b.parse("2026-10-01T11:00:00Z")
    stories = u.merge_story_items([u.add_ai_relevance_fields(row)], now, 24)
    stories[0]["news_summary"] = "既有模型發布摘要"
    result = u.build_brief_event_payloads(stories, [row], b.StateInput("missing"), now, 24,
                                         archive_meta=b.ArchiveMeta("valid", b.stamp(now)))
    assert result.projection["events"][0]["news_summary"] == "既有模型發布摘要"


def test_distinct_scope_expansions_each_survive_as_a_phase_not_extra_cards():
    first = article("first")
    tw = article("tw", "OpenAI expands GPT-6.1 Sol to Taiwan", day=3)
    eu = article("eu", "OpenAI expands GPT-6.1 Sol to Europe", day=5)
    result = run([first, tw, eu])
    assert len(result.projection["events"]) == 1
    assert len(result.next_state["events"][0]["phases"]) == 3
    assert result.projection["events"][0]["last_material_at"] == eu["published_at"]
    repeat = {**eu, "id": "eu-again", "url": "https://openai.com/index/eu-again", "published_at": "2026-10-07T10:00:00Z", "last_seen_at": "2026-10-07T10:00:00Z"}
    later = run([repeat], history=[first, tw, eu, repeat], previous=b.StateInput("valid", result.next_state))
    assert not later.projection["events"][0]["eligible"]
    assert len(later.next_state["events"][0]["phases"]) == 3


def test_known_unpatched_to_patch_available_is_real_progress():
    first = article("disclosure", "PHP vulnerability CVE-2026-12345", summary="No patch is available.")
    fixed = article("fixed", "PHP vulnerability CVE-2026-12345", summary="A patch is now available.", day=3)
    result = run([first, fixed])
    assert len(result.projection["events"]) == 1
    assert result.projection["events"][0]["last_material_at"] == fixed["published_at"]
    assert len(result.next_state["events"][0]["phases"]) == 2


def test_same_url_cross_ingress_does_not_create_a_second_unresolved_root():
    typed = article("structured")
    other = article("unstructured", "AI developer news", url=typed["url"] + "?utm_source=feed")
    first = run([typed, other])
    assert len(first.projection["events"]) == 1
    assert len(first.projection["events"][0]["member_article_ids"]) == 2
    again = run([typed, other], previous=b.StateInput("valid", first.next_state))
    assert first.projection["events"] == again.projection["events"]
    assert first.next_state == again.next_state
