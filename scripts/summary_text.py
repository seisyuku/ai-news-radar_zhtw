"""Remove publisher publication footers from model input and reader copy.

Raw source records remain intact. Keep the reader-side equivalent in
assets/app.js aligned through test_summary_attribution.py's shared cases.
"""
from __future__ import annotations

import re
from typing import Any


_CHINESE_ATTRIBUTION = re.compile(
    r'(?:本文|本篇(?:文章)?|[這这]篇(?:文章|(?=題為|题为|名為|名为))|文章|[該该]文)'
    r'(?:(?:\s*[《〈「『（(“"][^。！？]*?[》〉」』）)”"]|\s+[^。！？]*?|'
    r'(?:題為|题为|名為|名为)[^。！？]*?)(?:的文章)?)?\s*[，,]?\s*'
    r'(?:最先|最初|首次|初次|最早|首先)?(?:發表|发表|發布|发布|刊登|刊載|刊载|首發|首发)'
    r'(?:於|于|在)\s*[^。！？，,；;]+[。.]?$'
)
_ENGLISH_ATTRIBUTION = re.compile(
    r'\b(?:The|This) (?:article|post)\b(?:[^.!?]|\.(?=\S)|[!?](?=\s+(?:appeared|first|was)))*?'
    r'\b(?:appeared first on|first appeared on|was (?:first|originally) published (?:on|in))'
    r'\s+(?P<publisher>[^,;.!?]+(?:\.[^,;.!?\s]+)*)\s*[.!]?$', re.I
)


def strip_summary_attribution(value: Any, *, source_text: str = "") -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    clean = _ENGLISH_ATTRIBUTION.sub("", _CHINESE_ATTRIBUTION.sub("", text)).strip()
    if clean != text:
        return clean

    # A native publication footer establishes the publisher. For legacy
    # translations, identify its terminal publication clause rather than
    # guessing every possible translation of "The article <title>".
    native = _ENGLISH_ATTRIBUTION.search(re.sub(r"\s+", " ", source_text).strip())
    if not native:
        return text
    publisher = re.escape(native.group("publisher").strip())
    clause = re.search(
        r'(?:發表|发表|發布|发布|發佈|刊登|刊載|刊载|出現|出现|首發|首发)\s*'
        r'(?:於|于|在)\s*[《〈「]?' + publisher +
        r'[》〉」]?\s*(?:網站|网站)?\s*上?[。.!]?$', text, re.I
    )
    if not clause:
        return text
    # Find the sentence boundary outside title quotes/parentheses. Do not
    # split at decimal points or punctuation inside a quoted headline.
    pairs = {"《": "》", "〈": "〉", "「": "」", "『": "』", "（": "）", "(": ")", "“": "”", '"': '"'}
    stack: list[str] = []
    start = 0
    for index, char in enumerate(text[:clause.start()]):
        if stack and char == stack[-1]:
            stack.pop()
        elif char in pairs:
            stack.append(pairs[char])
        elif not stack and char in "。！？!?":
            start = index + 1
    # With no body boundary, only a clearly marked title/metadata opening
    # can be discarded. Ambiguous prose remains intact.
    if start == 0 and not re.match(r'^(?:[《〈「『（(“"]|本文|本篇|[這这]篇|文章|[該该]文)', text):
        return text
    return text[:start].strip()
