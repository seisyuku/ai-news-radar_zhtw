"""Exercise D+ through the real generator, sensor parsers and output writes."""
import hashlib
import json
import sys
import subprocess
from datetime import timedelta
from pathlib import Path

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
    rows = [article("core", title="OpenAI releases GPT-6.1 Sol model for developers", summary="The AI model adds tool calling and supports enterprise customers using longer context windows."), article("supplement",
        title="Cedar AI secures $150 million funding for inference infrastructure",
        summary="Cedar AI now operates 2,000 additional inference GPUs for enterprise customers.",
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


@pytest.mark.parametrize("case", ["healthy", "degraded", "mixed-all"])
def test_app_governance_is_independent_of_auxiliary_arrival_order(generation, monkeypatch, case):
    output, *_ = generation
    if case == "degraded":
        write = u.atomic_write_text

        def fail_history(path, text):
            if path.name == "brief-event-state.json":
                raise OSError("event history unavailable")
            return write(path, text)

        monkeypatch.setattr(u, "atomic_write_text", fail_history)
    assert u.main() == 0
    subprocess.run(["node", str(Path(__file__).with_name("frontend_loader_scenarios.cjs")),
                    "governance-arrivals", str(output), "2" if case == "healthy" else "-1",
                    "1" if case == "healthy" else "0", case], check=True, timeout=30)


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
    assert status['news_quality']['counts']['selected_events'] == len(daily['items'])
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
    quality = read(output,'source-status.json')['news_quality']
    assert quality['counts']['selected_events'] == 0
    assert quality['event_generation_status'] == 'unavailable'
    assert all('event_projection_unavailable' in r['reason_codes'] for r in quality['articles'])
    assert read(output,"latest-24h.json")["items_ai"]
    assert len(read(output,"market-signals.json")["signals"]) == 1
    assert browser_result(output) == {"ready":False,"count":0,"radar":0}


@pytest.mark.parametrize("name", ["stories-merged.json", "daily-brief.json"])
def test_partial_write_cannot_serve_new_generation_with_old_qualified_views(generation, monkeypatch, name):
    output, _, _, _ = generation
    assert u.main() == 0
    before = read(output,name)
    # Give the second write a new generation, while retaining all item clocks.
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


def test_history_write_failure_hides_governed_views_and_keeps_price_signal(generation, monkeypatch):
    output, *_ = generation
    write = u.atomic_write_text

    def fail_state(path, text):
        if path.name == "brief-event-state.json":
            raise OSError("synthetic event history failure")
        return write(path, text)

    with monkeypatch.context() as fault:
        fault.setattr(u, "atomic_write_text", fail_state)
        assert u.main() == 0
    assert browser_result(output) == {"ready": False, "count": 0, "radar": 0}
    assert read(output, "market-signals.json")["signals"]
    assert read(output, "latest-24h.json")["items_ai"]
    assert u.main() == 0
    assert browser_result(output) == {"ready": True, "count": 2, "radar": 1}


def test_price_sensor_failure_isolated_from_dplus(generation):
    output, _, failures, _ = generation
    baseline = (output / "market-sensor-state.json").read_bytes()
    failures.add(sensors.PRICE_URL)
    assert u.main() == 0
    assert browser_result(output) == {"ready":True,"count":2,"radar":1}
    status = read(output,"source-status.json")
    assert len(status["failed_sites"]) == 1
    types = [x["event_type"] for x in read(output,"market-signals.json")["signals"]]
    assert types == []
    assert (output / "market-sensor-state.json").read_bytes() == baseline


@pytest.mark.parametrize("broken", [b"{", b"\xff", b'{"price":{"models":[]}}', b'{"schema_version":2}', None],
                         ids=["json", "encoding", "shape", "version", "read-error"])
def test_main_protects_unreadable_price_baseline_and_resumes_from_verified_copy(
    generation, monkeypatch, broken,
):
    output, calls, _, _ = generation
    state_path = output / "market-sensor-state.json"
    saved = state_path.read_bytes()
    if broken is not None:
        state_path.write_bytes(broken)
    before = state_path.read_bytes()
    (output / "market-signals.json").write_text(json.dumps({"signals": [
        {"id": "recent", "category": "price", "detected_at": u.iso(NOW - timedelta(hours=1))},
        {"id": "boundary", "category": "price", "detected_at": u.iso(NOW - timedelta(hours=24))},
        {"id": "expired", "category": "price", "detected_at": u.iso(NOW - timedelta(hours=24, seconds=1))},
    ]}))
    original_read = Path.read_text

    def fail_baseline_read(path, *args, **kwargs):
        if path == state_path:
            raise PermissionError("simulated read failure")
        return original_read(path, *args, **kwargs)

    with monkeypatch.context() as failed:
        if broken is None:
            failed.setattr(Path, "read_text", fail_baseline_read)
        assert u.main() == 0

    assert state_path.read_bytes() == before
    assert calls == []
    status = read(output, "source-status.json")
    assert status["failed_sites"] == ["market_price"]
    assert status["degraded_sites"] == ["market_price"]
    price = next(row for row in status["sites"] if row["site_id"] == "market_price")
    assert price["error"] == "price_baseline_unavailable"
    assert read(output, "latest-24h.json")["items_ai"]
    assert {row["id"] for row in read(output, "market-signals.json")["signals"]} == {"recent", "boundary"}

    if broken is not None:
        state_path.write_bytes(saved)
    monkeypatch.setattr(u, "utc_now", lambda: NOW + timedelta(minutes=1))
    assert u.main() == 0
    assert calls == [sensors.PRICE_URL]
    recovered = read(output, "market-signals.json")["signals"]
    assert len(recovered) == 2
    assert any(row["id"] == "recent" for row in recovered)
    assert not any(row["id"] == "boundary" for row in recovered)
    change = next(row for row in recovered if row.get("event_type") == "API_PRICE_CHANGE")
    assert (change["old_value"], change["new_value"]) == (1.5, 1.0)
    status = read(output, "source-status.json")
    price = next(row for row in status["sites"] if row["site_id"] == "market_price")
    assert price["ok"] and price["consecutive_failures"] == 0
    assert status["degraded_sites"] == []


def test_main_establishes_missing_price_baseline_only_after_success(generation, monkeypatch):
    output, _, _, _ = generation
    state_path = output / "market-sensor-state.json"
    state_path.unlink()
    with monkeypatch.context() as failed:
        failed.setattr(sensors, "_fetch_json", lambda *_: {"models": []})
        assert u.main() == 0
    assert not state_path.exists()
    assert read(output, "market-signals.json")["signals"] == []
    assert read(output, "latest-24h.json")["items_ai"]

    assert u.main() == 0
    state = read(output, state_path.name)
    assert state["price"] == sensors.build_price_snapshot(price_payload(input_per_1m_usd=1.0))
    assert read(output, "market-signals.json")["signals"] == []


def test_main_keeps_price_baseline_when_catalog_shrinks(generation, monkeypatch):
    output, _, _, previous = generation
    state_path = output / "market-sensor-state.json"
    catalog = price_payload()
    first = catalog["models"][0]
    catalog["models"].extend({**first, "model_id": f"example-{n}"} for n in range(2, 6))
    state_path.write_text(json.dumps({**previous, "price": sensors.build_price_snapshot(catalog)}))
    baseline = state_path.read_bytes()

    smaller = {**catalog, "models": catalog["models"][:3]}
    with monkeypatch.context() as failed:
        failed.setattr(sensors, "_fetch_json", lambda *_: smaller)
        assert u.main() == 0
    assert state_path.read_bytes() == baseline
    assert read(output, "market-signals.json")["signals"] == []
    assert read(output, "source-status.json")["failed_sites"] == ["market_price"]
    assert read(output, "latest-24h.json")["items_ai"]

    valid = {**catalog, "models": [{**first, "input_per_1m_usd": 1.0}, *catalog["models"][1:4]]}
    monkeypatch.setattr(sensors, "_fetch_json", lambda *_: valid)
    assert u.main() == 0
    signals = read(output, "market-signals.json")["signals"]
    assert {row["event_type"] for row in signals} == {"API_PRICE_CHANGE", "MODEL_PRICE_REMOVED"}
    change = next(row for row in signals if row["event_type"] == "API_PRICE_CHANGE")
    assert (change["old_value"], change["new_value"]) == (1.5, 1.0)
    assert read(output, state_path.name)["price"] == sensors.build_price_snapshot(valid)
