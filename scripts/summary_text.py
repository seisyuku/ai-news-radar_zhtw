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
    r'\s+[^,;.!?]+(?:\.[^,;.!?\s]+)*\s*[.!]?$', re.I
)


def strip_summary_attribution(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return _ENGLISH_ATTRIBUTION.sub("", _CHINESE_ATTRIBUTION.sub("", text)).strip()
