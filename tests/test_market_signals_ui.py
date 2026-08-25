from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_market_and_breaking_surfaces_are_separate_and_optional():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert 'id="breakingSignalsWrap" hidden' in html
    assert 'id="marketSignalsWrap" hidden' in html
    assert "額度與政策速報" in html
    assert "價格與免費額度變更" in html


def test_llm_radar_surface_is_optional_between_today_signals_and_market_changes():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert 'id="llmRadarWrap" hidden' in html
    assert "LLM 發布雷達" in html
    assert html.index('id="briefPicksWrap"') < html.index('id="llmRadarWrap"') < html.index('id="marketSignalsWrap"')


def test_ui_loads_sensor_payload_and_keeps_candidate_wording():
    js = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
    assert "data/market-signals.json" in js
    assert 'return "待確認"' in js
    assert 'signal.urgency === "breaking"' in js
    assert 'sortMode === "importance"' in js
    assert "renderMarketSignals();" in js
    assert "data/llm-radar.json" in js
    assert "renderLlmRadar();" in js
    assert "renderCompactSignalGroup(" in js
    assert "buildCompactSignalLink(signal)" in js
    assert 'if (status === "official") return "官方公告";' in js
    assert 'if (category === "model_release") return "模型釋出";' in js


def test_compact_radar_lists_are_scroll_frames_and_render_all_messages():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    css = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
    js = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")

    assert 'id="llmRadarList" role="region"' in html
    assert 'id="marketSignalsList" role="region"' in html
    assert ".compact-signal-list" in css
    assert "max-height: 176px" in css
    assert "max-height: 168px" in css
    assert "overflow-y: auto" in css
    assert "scrollbar-gutter: stable" in css
    assert "scrollbar-width: thin" in css
    assert "function renderCompactSignalGroup(wrap, list, meta, signals, emptyMeta" in js
    assert "ordered.forEach((signal) => list.appendChild(buildCompactSignalLink(signal)))" in js
