import json
from pathlib import Path

import pytest

from tests.js_bridge import extract_declarations, run_js


ROOT = Path(__file__).resolve().parent.parent
SOURCE_SUMMARY_DECLARATIONS = extract_declarations("stripSummaryAttribution", "itemSummaryText")
DECLARATIONS = "\n".join(
    [
        extract_declarations("storyNewsSummaryText"),
        extract_declarations("newsSummaryText"),
    ]
)


def test_news_summary_text_uses_generated_story_summary_only():
    result = run_js(
        f"""{DECLARATIONS}
        console.log(JSON.stringify({{
          present: newsSummaryText({{story: {{news_summary: '  模型發布摘要  '}}}}),
          absent: newsSummaryText({{story: {{business_events: ['model_release']}}}}),
        }}));"""
    )

    assert result == {"present": "模型發布摘要", "absent": ""}


def test_item_summary_prefers_translated_rss_copy_when_available():
    declarations = SOURCE_SUMMARY_DECLARATIONS
    result = run_js(
        f"""{declarations}
        console.log(JSON.stringify({{
          translated: itemSummaryText({{summary: 'English RSS copy', summary_zh: '繁體中文 RSS 摘要'}}),
          fallback: itemSummaryText({{summary: 'English RSS copy'}}),
        }}));"""
    )

    assert result == {"translated": "繁體中文 RSS 摘要", "fallback": "English RSS copy"}


@pytest.mark.parametrize("footer", [
    "本文最先發表於 The Decoder。",
    "本文《OpenAI raises $11 billion》最初發布於 The Decoder。",
    "本文（標題）首次刊登於來源網站。",
    "本文「安全更新」首次發表於 The Decoder。",
    "這篇文章 Google Deepmind 利用衛星資料與 AI 建立全球森林地圖 首次發表於 The Decoder。",
    "這篇題為 Google's AI Mode「不會為任何人」帶來流量 的文章最初發表於 The Decoder。",
    "這篇名為「認識 Droid 1.0」的文章最初發表於 MarkTechPost。",
    "本文最初发布于來源網站。",
    "The article Meet Droid 1.0: An AI Agent appeared first on MarkTechPost .",
    "The post AI model update appeared first on Example News.",
    "This article was originally published on Example News.",
    "The article AI model update first appeared on Example News.",
])
@pytest.mark.parametrize("field", ["summary_zh", "summary", "reader_summary"])
def test_source_summary_removes_publisher_footer_before_truncation(footer, field):
    body = "模型更新已發布。"
    item = json.dumps({field: f"{body} {footer}"}, ensure_ascii=False)
    result = run_js(f'''{SOURCE_SUMMARY_DECLARATIONS}
      console.log(JSON.stringify(itemSummaryText({item}, 20)));''')
    assert result == body


@pytest.mark.parametrize("body", [
    "本文討論估值風險，沒有宣布具體交易。",
    "本文研究首次發表於期刊的模型，並比較評估結果。",
    "研究最初發表於 Nature，這次新增公開資料。",
    "The article explains how the model works. It was originally published in Nature.",
    "The post discusses an article that appeared first on a research site, with new results.",
])
def test_source_summary_keeps_substantive_publication_discussion(body):
    result = run_js(f'''{SOURCE_SUMMARY_DECLARATIONS}
      console.log(JSON.stringify(itemSummaryText({{summary: {json.dumps(body)}}}, 500)));''')
    assert result == body


def test_source_summary_footer_only_becomes_empty_without_mutating_source():
    result = run_js(f'''{SOURCE_SUMMARY_DECLARATIONS}
      const item = {{summary_zh: '本文最先發表於 The Decoder。', summary: 'Original source copy'}};
      console.log(JSON.stringify({{display: itemSummaryText(item), stored: item.summary_zh}}));''')
    assert result == {"display": "", "stored": "本文最先發表於 The Decoder。"}


def test_followup_story_rows_render_generated_summary_when_present():
    source = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")

    assert 'summary.className = "story-ai-summary"' in source
    assert "storyNewsSummaryText(story)" in source
    assert "AI 摘要 · ${generatedSummary}" in source


def test_top_card_renders_generated_or_attributed_publisher_copy():
    source = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")

    assert "function signalSummaryText" not in source
    assert "已進入 24 小時 AI 強相關池" not in source
    assert "if (displaySummary.text)" in source
    assert 'whyLabel.textContent = displaySummary.label' in source


def test_top_card_fallback_is_primary_article_only_and_never_labeled_ai():
    declarations = DECLARATIONS + SOURCE_SUMMARY_DECLARATIONS + extract_declarations("topStorySummary")
    result = run_js(f'''{declarations}
      console.log(JSON.stringify([
        topStorySummary({{story: {{news_summary: 'AI摘要'}}, item: {{summary_zh: '來源譯文'}}}}),
        topStorySummary({{story: {{}}, item: {{summary: 'original', summary_zh: '來源譯文'}}}}),
        topStorySummary({{story: {{sources: [{{summary: '別篇摘要'}}]}}, item: {{}}}})
      ]));''')
    assert result == [dict(label="AI 摘要", text="AI摘要"),
                      dict(label="來源摘要", text="來源譯文"), dict(label="來源摘要", text="")]


def test_fixed_why_important_copy_is_removed_from_shipped_ui():
    source = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")

    assert "為什麼重要" not in source
    assert "whyImportantText" not in source
    assert "AI 摘要" in source


def test_workflow_configures_optional_groq_qwen_summary_runtime():
    workflow = (ROOT / ".github" / "workflows" / "update-news.yml").read_text(encoding="utf-8")

    assert "GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}" in workflow
    assert "qwen/qwen3.8-27b" in workflow
    assert "GROQ_SUMMARY_MAX_NEW" in workflow
