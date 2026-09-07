from pathlib import Path

from tests.js_bridge import extract_declarations, run_js


ROOT = Path(__file__).resolve().parent.parent


def test_only_valid_http_urls_produce_a_copy_payload():
    declaration = extract_declarations("buildCopyNewsUrlPayload")
    result = run_js(
        f"""{declaration}
        console.log(JSON.stringify({{
          item: buildCopyNewsUrlPayload({{id: '6b8d1ce6756fba7757f676f83fa006229b8f7c68', url: 'https://www.aibase.com/news/30864'}}),
          missing: buildCopyNewsUrlPayload({{}}),
          malformed: buildCopyNewsUrlPayload({{url: 'not a URL'}}),
          unsupported: buildCopyNewsUrlPayload({{url: 'ftp://example.com/news'}}),
        }}));"""
    )

    assert result == {
        "item": "URL＝https://www.aibase.com/news/30864",
        "missing": "",
        "malformed": "",
        "unsupported": "",
    }
    assert "6b8d1ce6756fba7757f676f83fa006229b8f7c68" not in result["item"]


def test_single_source_cards_render_the_copy_url_button_without_social_editor_text():
    source = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")

    assert 'button.className = "copy-id-btn"' in source
    assert 'button.textContent = "複製URL"' in source
    assert "const copyUrlButton = buildCopyNewsUrlButton(item);" in source
    assert "const cardActions = node.querySelector(\".card-actions\");" in source
    assert "if (copyUrlButton) cardActions.appendChild(copyUrlButton);" in source
    assert source.count("isCopyableNewsItemId(") == 1
    assert "Social Editor" not in source
