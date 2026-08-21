from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_market_and_breaking_surfaces_are_separate_and_optional():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert 'id="breakingSignalsWrap" hidden' in html
    assert 'id="marketSignalsWrap" hidden' in html
    assert "額度與政策速報" in html
    assert "價格與免費額度變更" in html


def test_ui_loads_sensor_payload_and_keeps_candidate_wording():
    js = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
    assert "data/market-signals.json" in js
    assert 'return "待確認"' in js
    assert 'signal.urgency === "breaking"' in js
    assert 'sortMode === "importance"' in js
    assert "renderMarketSignals();" in js
