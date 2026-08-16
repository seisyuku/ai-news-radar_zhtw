from pathlib import Path

from tests.js_bridge import extract_declarations, run_js


ROOT = Path(__file__).resolve().parent.parent
DECLARATION = extract_declarations("newsSummaryText")


def test_news_summary_text_uses_generated_story_summary_only():
    result = run_js(
        f"""{DECLARATION}
        console.log(JSON.stringify({{
          present: newsSummaryText({{story: {{news_summary: '  模型發布摘要  '}}}}),
          absent: newsSummaryText({{story: {{business_events: ['model_release']}}}}),
        }}));"""
    )

    assert result == {"present": "模型發布摘要", "absent": ""}


def test_fixed_why_important_copy_is_removed_from_shipped_ui():
    source = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")

    assert "為什麼重要" not in source
    assert "whyImportantText" not in source
    assert "AI 新聞摘要" in source


def test_workflow_configures_optional_groq_qwen_summary_runtime():
    workflow = (ROOT / ".github" / "workflows" / "update-news.yml").read_text(encoding="utf-8")

    assert "GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}" in workflow
    assert "qwen/qwen3.6-27b" in workflow
    assert "GROQ_SUMMARY_MAX_NEW" in workflow
