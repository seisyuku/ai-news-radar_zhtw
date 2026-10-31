"""Exercise the same publication-footer boundary in Python and shipped JS."""
import json

import pytest

from scripts.summary_text import strip_summary_attribution
from tests.js_bridge import extract_declarations, run_js


BODY = "AI 代理自主選擇治療方案，但校準錯誤時拒絕繼續進行。"
FOOTERS = [
    "文章〈Claude 模型自主進行手術〉最初發表於 The Decoder。",
    "文章（Claude 模型自主進行手術）最初發表於 The Decoder。",
    "文章《Claude 模型自主進行手術》，最早刊登於 The Decoder。",
    "該文『Claude 模型自主進行手術』首發於 The Decoder。",
    "该文《Claude 模型自主进行手术》最初发布于 The Decoder。",
    "本文最先發表於 The Decoder。",
    "這篇文章 Claude 模型自主進行手術 首次發表於 The Decoder。",
    "這篇題為 Claude 模型的文章最初發表於 The Decoder。",
    "這篇名為「Claude 模型」的文章最初發表於 The Decoder。",
    "The article Could an AI agent operate on a mouse? appeared first on The Decoder .",
    "The post Droid 1.0: A new agent appeared first on MarkTechPost .",
    "This article was originally published on example.com.",
]
KEEP = [
    "本文討論估值風險，沒有宣布具體交易。",
    "文章指出，校準錯誤時代理拒絕繼續進行。",
    "文章研究首次發表於期刊的模型，並比較評估結果。",
    "該文討論首次發表於 Nature 的研究。",
    "研究最初發表於 Nature，這次新增公開資料。",
    "The article explains how the model works. It was originally published in Nature.",
    "The post discusses an article that appeared first on a research site, with new results.",
]
CASES = [(BODY + footer, BODY) for footer in FOOTERS]
CASES += [(BODY + "\n" + footer, BODY) for footer in FOOTERS]
CASES += [(footer, "") for footer in FOOTERS]
CASES += [(body, body) for body in KEEP]


@pytest.mark.parametrize("source,expected", CASES)
def test_python_publication_footer_boundary(source, expected):
    assert strip_summary_attribution(source) == expected


def test_frontend_and_pipeline_share_publication_footer_behavior():
    declarations = extract_declarations("stripSummaryAttribution", "itemSummaryText")
    sources = json.dumps([source for source, _ in CASES], ensure_ascii=False)
    result = run_js(f'''{declarations}
      console.log(JSON.stringify({sources}.map(summary => itemSummaryText({{summary}}, 10000))));''')
    assert result == [expected for _, expected in CASES]


NATIVE = "The model refused to continue after a calibration error. The article An AI performs surgery appeared first on The Decoder ."
LEGACY = [
    (BODY + "（Claude 模型自主進行手術）發表於 The Decoder。", NATIVE, BODY),
    (BODY + "《Claude 模型自主進行手術》一文最初發表於 The Decoder。", NATIVE, BODY),
    (BODY + "「模型為什麼拒絕？研究結果」一文最先發布於 The Decoder。", NATIVE, BODY),
    (BODY + "模型自主進行手術的文章首先出現在 The Decoder 上。", NATIVE, BODY),
    (BODY + "這篇模型手術報導最初發表在 The Decoder 網站上。", NATIVE, BODY),
    ("（Claude 模型自主進行手術）發表於 The Decoder。", NATIVE, ""),
    (BODY + "（模型手術）發表於 Example News。", NATIVE, BODY + "（模型手術）發表於 Example News。"),
    (BODY + "（模型手術）發表於 The Decoder。", "A research report without a publication footer.", BODY + "（模型手術）發表於 The Decoder。"),
    ("研究發表於 The Decoder，研究人員另提供方法與數據。", NATIVE, "研究發表於 The Decoder，研究人員另提供方法與數據。"),
    (BODY + "研究最初發表於 Nature。", NATIVE, BODY + "研究最初發表於 Nature。"),
    ("模型研究發表於 The Decoder。", NATIVE, "模型研究發表於 The Decoder。"),
    (BODY + "（模型 1.0 的結果）發表於 AI.News。", "The post Model results appeared first on AI.News .", BODY),
    (BODY + "（模型 1.0 的結果）發表於 AIXNews。", "The post Model results appeared first on AI.News .", BODY + "（模型 1.0 的結果）發表於 AIXNews。"),
]


@pytest.mark.parametrize("translated,native,expected", LEGACY)
def test_legacy_footer_uses_native_publisher_and_sentence_boundary(translated, native, expected):
    assert strip_summary_attribution(translated, source_text=native) == expected


def test_frontend_uses_the_same_native_publisher_boundary_for_legacy_translations():
    declarations = extract_declarations("stripSummaryAttribution", "itemSummaryText")
    rows = json.dumps([{"summary_zh": translated, "summary": native} for translated, native, _ in LEGACY], ensure_ascii=False)
    result = run_js(f'''{declarations}
      console.log(JSON.stringify({rows}.map(item => itemSummaryText(item, 10000))));''')
    assert result == [expected for _, _, expected in LEGACY]
