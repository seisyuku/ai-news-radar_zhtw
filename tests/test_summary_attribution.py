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
