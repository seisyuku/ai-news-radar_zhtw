from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_market_and_breaking_surfaces_are_separate_and_optional():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert 'id="breakingSignalsWrap" hidden' in html
    assert 'id="marketSignalsWrap" hidden' in html
    assert "額度與政策速報" in html
    assert "價格與免費額度變更" in html


def test_llm_radar_surface_is_optional_and_precedes_today_signals():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert 'id="llmRadarWrap" hidden' in html
    assert "LLM 發布與價格雷達" in html
    assert html.index('id="llmRadarWrap"') < html.index('id="briefPicksWrap"')


def test_ui_loads_sensor_payload_and_keeps_candidate_wording():
    js = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
    assert "data/market-signals.json" in js
    assert 'return "待確認"' in js
    assert 'signal.urgency === "breaking"' in js
    assert 'sortMode === "importance"' in js
    assert "renderMarketSignals();" in js
    assert "data/llm-radar.json" in js
    assert "renderLlmRadar();" in js
    assert 'if (status === "official") return "官方公告";' in js
    assert 'if (category === "model_release") return "模型釋出";' in js
