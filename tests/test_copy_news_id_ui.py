from pathlib import Path

from tests.js_bridge import extract_declarations, run_js


ROOT = Path(__file__).resolve().parent.parent


def test_only_reader_item_ids_are_copyable():
    declaration = extract_declarations("isCopyableNewsItemId")
    result = run_js(
        f"""{declaration}
        console.log(JSON.stringify({{
          item: isCopyableNewsItemId({{id: '6b8d1ce6756fba7757f676f83fa006229b8f7c68'}}),
          story: isCopyableNewsItemId({{id: 'story_123456789abc'}}),
          sensor: isCopyableNewsItemId({{id: 'model_release::gemini-3.8-flash'}}),
          missing: isCopyableNewsItemId({{}}),
        }}));"""
    )

    assert result == {"item": True, "story": False, "sensor": False, "missing": False}


def test_single_source_cards_render_the_copy_button_only_for_item_ids():
    source = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")

    assert 'button.className = "copy-id-btn"' in source
    assert 'button.textContent = "複製新聞 ID"' in source
    assert "const copyIdButton = buildCopyNewsIdButton(item);" in source
    assert "if (copyIdButton) metaRow.appendChild(copyIdButton);" in source
