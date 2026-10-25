"""Exercise D+ through the real generator, sensor parsers and output writes."""
import hashlib
import json
import sys

import pytest

from scripts import update_news as u, market_sensors as sensors, signal_selection as selection
from tests.js_bridge import run_js
from tests.test_market_sensors import price_payload
from tests.test_publisher_governance import article, NOW


@pytest.fixture
def generation(tmp_path, monkeypatch):
    output = tmp_path / "data"
    output.mkdir()
    stamp = u.iso(NOW)
    rows = [article("core", title="OpenAI releases GPT-6.1 Sol model for developers"), article("supplement",
        title="Microsoft announces new Copilot workspace integration",
        summary="Microsoft has added an AI collaboration workspace for business users.",
        site_id="curated_media", source="The Decoder AI News", url="https://the-decoder.com/synthetic-workspace")]
    for row in rows:
        row.update(id=hashlib.sha1(row["id"].encode()).hexdigest(), site_name="Synthetic integration",
                   last_seen_at=stamp)
    (output / "archive.json").write_text(json.dumps({"generated_at":stamp, "items":rows}))
    previous = {"schema_version":1, "price":sensors.build_price_snapshot(price_payload()),
        "canary":{"usage4claude":["old"]},
        "free_tier":{"retired_baseline":"preserve"}}
    (output / "market-sensor-state.json").write_text(json.dumps(previous))
    calls = []
    failures = set()

    class Response:
        def __init__(self, url):
            self.url = url
        def raise_for_status(self):
            if self.url in failures:
                raise RuntimeError("synthetic_source_failure")
        def json(self):
            assert self.url == sensors.PRICE_URL
            return price_payload(input_per_1m_usd=1.0)

    class Session:
        def get(self, url, **kwargs):
            calls.append(url)
            return Response(url)

    for key in ("X_BEARER_TOKEN", "SOCIALDATA_API_KEY", "TIKHUB_API_KEY", "GEMINI_API_KEY",
                "GROQ_API_KEY", "GOOGLE_TRANSLATE_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("TIKHUB_ENABLED", "0")
    monkeypatch.setattr(u, "utc_now", lambda: NOW)
    monkeypatch.setattr(u, "create_session", Session)
    monkeypatch.setattr(u, "collect_all", lambda *_: ([], [
        {"site_id":"official_ai", "site_name":"Synthetic official", "ok":True, "item_count":1},
        {"site_id":"curated_media", "site_name":"Synthetic media", "ok":True, "item_count":1}]))
    monkeypatch.setattr(sys, "argv", ["update_news.py", "--output-dir", str(output), "--translate-max-new", "0"])
    def deny(*args, **kwargs):
        raise AssertionError("external network forbidden")
    monkeypatch.setattr("requests.sessions.Session.request", deny)
    return output, calls, failures, previous


def read(output, name):
    return json.loads((output / name).read_text())


def browser_result(output):
    names = ["stories-merged.json", "daily-brief.json", "latest-24h.json", "latest-24h-all.json", "llm-radar.json"]
    payloads = [read(output, name) for name in names]
    return run_js("const G=require('./assets/publisher-governance.js');"
        + "const [parent,daily,latest,all,radar]=" + json.dumps(payloads) + ";"
        + "const now=Date.parse(latest.generated_at);Date.now=()=>now;"
        + "const state={storiesMerged:parent,dailyBrief:daily,latestGovernanceMeta:latest.publisher_governance_meta,"
        + "allGovernanceMeta:all.publisher_governance_meta,llmRadarGovernanceMeta:radar.publisher_governance_meta};"
        + "const r=G.resolve(state,now);console.log(JSON.stringify({ready:!!r.projection,"
        + "count:r.projection?.events.length||0,radar:G.radarEvents(radar.events,radar.publisher_governance_meta,state,now).length}));")


def test_main_writes_one_v2_bundle_and_preserves_price_sensor(generation):
    output, calls, _, previous = generation
    assert u.main() == 0
    parent, daily = read(output,"stories-merged.json"), read(output,"daily-brief.json")
    g = parent["publisher_governance"]
    assert g["status"] == "ready" and g["schema_version"] == 2
    assert selection.validate(g, parent["brief_events"])
    for name in ("latest-24h.json", "latest-24h-all.json", "llm-radar.json"):
        assert read(output, name)["publisher_governance_meta"] == daily["publisher_governance_meta"]
    assert {x["selection_class"] for x in daily["items"]} == {"core","supplement"}
    assert browser_result(output) == {"ready":True,"count":2,"radar":1}
    signals = read(output,"market-signals.json")["signals"]
    assert [x["event_type"] for x in signals].count("API_PRICE_CHANGE") == 1
    assert all(x["category"] == "price" for x in signals)
    assert all(x["verification_status"] != "official" for x in signals)
    assert read(output,"market-sensor-state.json")["free_tier"] == previous["free_tier"]
    assert "canary" not in read(output,"market-sensor-state.json")
    assert calls == [sensors.PRICE_URL]
    status = read(output,"source-status.json")
    assert status["brief_selection"] == daily["selection_diagnostics"]
    assert status["failed_sites"] == [] and status["successful_sites"] == 3
    assert status["translations"].get("request_count",0) == 0
    assert status["ai_summaries"]["enabled"] is False
    assert len(list((output/"items").glob("*.json"))) == 2


@pytest.mark.parametrize("failure", ["build", "state_write"])
def test_main_event_failure_keeps_general_price_but_disables_governed_views(generation, monkeypatch, failure):
    output, _, _, _ = generation
    if failure == "build":
        def fail_build(*args, **kwargs):
            raise RuntimeError("synthetic event failure")
        monkeypatch.setattr(u,"build_brief_event_payloads",fail_build)
    else:
        write = u.atomic_write_text
        def fail_state(path, text):
            if path.name == "brief-event-state.json":
                raise OSError("synthetic state write failure")
            return write(path,text)
        monkeypatch.setattr(u,"atomic_write_text",fail_state)
    assert u.main() == 0
    assert read(output,"stories-merged.json")["publisher_governance"]["status"] == "unavailable"
    assert read(output,"daily-brief.json")["items"] == []
    assert read(output,"latest-24h.json")["items_ai"]
    assert len(read(output,"market-signals.json")["signals"]) == 1
    assert browser_result(output) == {"ready":False,"count":0,"radar":0}


@pytest.mark.parametrize("name", ["stories-merged.json", "daily-brief.json"])
def test_partial_write_cannot_serve_new_generation_with_old_qualified_views(generation, monkeypatch, name):
    output, _, _, _ = generation
    assert u.main() == 0
    before = read(output,name)
    # Give the second write a new generation, while retaining all item clocks.
    from datetime import timedelta
    monkeypatch.setattr(u,"utc_now",lambda: NOW+timedelta(minutes=1))
    write = u.atomic_write_text
    def fail(path,text):
        if path.name == name:
            raise OSError("synthetic partial write")
        return write(path,text)
    monkeypatch.setattr(u,"atomic_write_text",fail)
    with pytest.raises(OSError):
        u.main()
    assert read(output,name) == before
    assert read(output,"latest-24h.json")["items_ai"]
    assert browser_result(output) == {"ready":False,"count":0,"radar":0}


def test_price_sensor_failure_isolated_from_dplus(generation):
    output, _, failures, _ = generation
    failures.add(sensors.PRICE_URL)
    assert u.main() == 0
    assert browser_result(output) == {"ready":True,"count":2,"radar":1}
    status = read(output,"source-status.json")
    assert len(status["failed_sites"]) == 1
    types = [x["event_type"] for x in read(output,"market-signals.json")["signals"]]
    assert types == []
