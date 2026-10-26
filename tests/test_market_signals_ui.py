from pathlib import Path
from tests.js_bridge import extract_declarations, run_js


ROOT = Path(__file__).resolve().parent.parent


def test_only_price_sensor_surface_remains_optional():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert 'id="breakingSignalsWrap"' not in html
    assert 'id="marketSignalsWrap" hidden' in html
    assert "價格變更" in html
    assert "價格與免費額度變更" not in html


def test_llm_radar_surface_is_optional_between_today_signals_and_market_changes():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert 'id="llmRadarWrap" hidden' in html
    assert "LLM 發布雷達" in html
    assert html.index('id="briefPicksWrap"') < html.index('id="llmRadarWrap"') < html.index('id="marketSignalsWrap"')


def test_ui_loads_price_sensor_payload():
    js = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
    loader = (ROOT / "assets" / "loader.js").read_text(encoding="utf-8")
    assert "data/market-signals.json" in loader
    assert "loadMarketSignalsData().then" in js
    assert 'signal.category === "price"' in js
    assert 'breakingSignalsWrapEl' not in js
    assert 'sortMode === "importance"' in js
    assert "renderMarketSignals();" in js
    assert "data/llm-radar.json" in loader
    assert "loadLlmRadarData().then" in js
    assert "renderLlmRadar();" in js
    assert "renderCompactSignalGroup(" in js
    assert "buildCompactSignalLink(signal)" in js


def test_old_canary_payload_cannot_reappear_in_price_list():
    script = extract_declarations("renderMarketSignals") + "\n" + """
const state = {marketSignals: [
  {id: 'old-canary', category: 'usage_policy', urgency: 'breaking'},
  {id: 'old-free', category: 'free_tier', urgency: 'standard'},
  {id: 'price', category: 'price', urgency: 'standard'},
]};
const marketSignalsWrapEl = {}, marketSignalsListEl = {}, marketSignalsMetaEl = {};
function renderCompactSignalGroup(_wrap, _list, _meta, signals) {
  console.log(JSON.stringify(signals.map((signal) => signal.id)));
}
renderMarketSignals();
"""
    assert run_js(script) == ["price"]


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
