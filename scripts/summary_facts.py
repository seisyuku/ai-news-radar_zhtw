"""Bounded numeric equivalence for summary validation, without FX conversion.

Amounts, percentages and ordinary quantities are separate facts. Unsupported
identifiers must retain their source spelling; this is not a semantic fact
checker and does not establish which company a number belongs to.
"""
from __future__ import annotations

from decimal import Decimal
import re
import unicodedata


_SCALES = {
    "k": 1000, "thousand": 1000, "千": 1000,
    "m": 10**6, "million": 10**6, "百萬": 10**6, "百万": 10**6,
    "b": 10**9, "billion": 10**9, "十億": 10**9, "十亿": 10**9,
    "t": 10**12, "trillion": 10**12, "兆": 10**12,
    "萬": 10**4, "万": 10**4, "億": 10**8, "亿": 10**8,
}
_WORDS = dict(zip(
    "zero one two three four five six seven eight nine ten eleven twelve".split(),
    range(13),
))
_DIGITS = dict(zip("零〇一二兩两三四五六七八九", (0, 0, 1, 2, 2, 2, 3, 4, 5, 6, 7, 8, 9)))
_SMALL = {"十": 10, "百": 100, "千": 1000}
_LARGE = {"萬": 10**4, "万": 10**4, "億": 10**8, "亿": 10**8, "兆": 10**12}
_CURRENCIES = {
    "us$": "USD", "usd": "USD", "$": "USD", "美元": "USD", "美金": "USD",
    "dollars": "USD", "dollar": "USD", "€": "EUR", "eur": "EUR", "歐元": "EUR",
    "£": "GBP", "gbp": "GBP", "英鎊": "GBP", "nt$": "TWD", "twd": "TWD",
    "新台幣": "TWD", "新臺幣": "TWD", "台幣": "TWD", "臺幣": "TWD",
    "hk$": "HKD", "hkd": "HKD", "港元": "HKD", "港幣": "HKD",
    "a$": "AUD", "au$": "AUD", "aud": "AUD", "澳元": "AUD", "澳幣": "AUD",
    "c$": "CAD", "ca$": "CAD", "cad": "CAD", "加元": "CAD", "加幣": "CAD",
    "cny": "CNY", "rmb": "CNY", "人民幣": "CNY", "jpy": "JPY", "日圓": "JPY",
    "日元": "JPY", "¥": "YEN_SIGN", "元": "UNSPECIFIED_YUAN",
}
_UNITS = {
    "tokens": ("tokens", 1), "token": ("tokens", 1), "context": ("tokens", 1),
    "parameters": ("parameters", 1), "parameter": ("parameters", 1), "參數": ("parameters", 1),
    "hours": ("seconds", 3600), "hour": ("seconds", 3600), "小時": ("seconds", 3600),
    "days": ("seconds", 86400), "day": ("seconds", 86400), "天": ("seconds", 86400),
    "minutes": ("seconds", 60), "minute": ("seconds", 60), "分鐘": ("seconds", 60),
    "seconds": ("seconds", 1), "second": ("seconds", 1), "秒": ("seconds", 1),
}


def _alternatives(values) -> str:
    return "(?:" + "|".join(re.escape(v) for v in sorted(values, key=len, reverse=True)) + ")"


_CURRENCY = _alternatives(_CURRENCIES)
_SCALE = _alternatives(_SCALES) + r"(?![a-z])"
_WORD = r"(?<![a-z])" + _alternatives(_WORDS) + r"(?![a-z])"
_CHINESE = (r"(?:[零〇一二兩两三四五六七八九十百千]{1,12}[點点][零〇一二三四五六七八九]{1,12}"
    r"(?=\s*(?:" + _SCALE + "|" + _CURRENCY + r"))|"
    r"[零〇一二兩两三四五六七八九十][零〇一二兩两三四五六七八九十百千萬万億亿兆]{0,24}[百千萬万億亿兆][零〇一二兩两三四五六七八九十百千萬万億亿兆]{0,24}"
    r"|百萬|百万|[零〇一二兩两三四五六七八九十百]{1,12}(?=\s*" + _CURRENCY + "))")
_NUMBER = r"(?:[+-]?\d+(?:,\d{3})*(?:\.\d+)?|" + _WORD + "|" + _CHINESE + ")"
_FACT = re.compile(
    r"(?P<currency>" + _CURRENCY + r")?\s*(?P<number>" + _NUMBER + r")"
    r"\s*(?P<scale>" + _SCALE + r")?\s*"
    r"(?P<unit>%|百分點|百分点|percent(?:age)?(?:\s+points)?(?![a-z])|per\s+cent(?![a-z])|" + _CURRENCY
    + "|" + _alternatives(_UNITS) + r"(?![a-z]))?",
    re.IGNORECASE,
)
_CHINESE_PERCENT = re.compile(r"百分之([+-]?\d+(?:\.\d+)?|[零〇一二兩两三四五六七八九十百千萬万億亿兆]{1,30}(?:[點点][零〇一二三四五六七八九]{1,12})?)(?:\s*(" + _SCALE + "))?", re.I)
_IDENTIFIER = re.compile(r"(?<![A-Za-z0-9._-])[A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*(?![A-Za-z0-9._-])")


def _chinese_value(text: str) -> Decimal:
    whole, *fraction = re.split(r"[點点.]", text)
    total = section = number = 0
    for char in whole:
        if char.isdigit():
            number = number * 10 + int(char)
        elif char in _DIGITS:
            number = _DIGITS[char]
        elif char in _SMALL:
            section += (number or 1) * _SMALL[char]
            number = 0
        elif char in _LARGE:
            section += number
            if _LARGE[char] >= 10**8:
                if total < _LARGE[char]:
                    total = (total + section or 1) * _LARGE[char]
                else:
                    total += section * _LARGE[char]
            else:
                total += (section or 1) * _LARGE[char]
            section = number = 0
    result = Decimal(total + section + number)
    if fraction:
        digits = "".join(str(_DIGITS.get(c, c)) for c in fraction[0])
        result += Decimal("0." + digits)
    return result


def _value(text: str) -> Decimal:
    folded = text.casefold()
    if folded in _WORDS:
        return Decimal(_WORDS[folded])
    if re.fullmatch(r"[+-]?\d[\d,.]*", text):
        return Decimal(text.replace(",", ""))
    return _chinese_value(text)


def numeric_facts(text: str) -> set[tuple[str, object]]:
    """Normalize only supported quantities; preserve opaque model identifiers."""
    text = unicodedata.normalize("NFKC", text).casefold().replace("−", "-")
    text = re.sub(r"([+-])\s*(" + _CURRENCY + r")\s*(?=\d)", r"\2\1", text)
    facts: set[tuple[str, object]] = set()
    masked = list(text)
    for match in _IDENTIFIER.finditer(text):
        token = match.group()
        if not any(c.isdigit() for c in token) or not re.search(r"[a-z]", token):
            continue
        # A standalone 27B/128K is a quantity, not a model name. Other
        # alphanumeric tokens must match exactly, including all version digits.
        if re.fullmatch(r"\d+(?:\.\d+)?[kmbt]", token):
            continue
        facts.add(("identifier", token))
        masked[match.start():match.end()] = " " * len(token)
    text = "".join(masked)
    for match in _CHINESE_PERCENT.finditer(text):
        value = _value(match.group(1)) * _SCALES.get((match.group(2) or "").casefold(), 1)
        facts.add(("percent", value))
        masked[match.start():match.end()] = " " * len(match.group())
    for match in _FACT.finditer("".join(masked)):
        raw = match.group("number")
        # Words such as "one" often have no numeric meaning in prose. Keep
        # them as source support, but don't demand them in Chinese output.
        value = _value(raw) * _SCALES.get((match.group("scale") or "").casefold(), 1)
        prefix = (match.group("currency") or "").casefold()
        unit = (match.group("unit") or "").casefold()
        currency = _CURRENCIES.get(prefix) or _CURRENCIES.get(unit)
        if prefix and unit in _CURRENCIES and _CURRENCIES[prefix] != _CURRENCIES[unit]:
            facts.add(("invalid_currency", match.group()))
        kind = currency or ("percent" if unit.startswith(("%", "percent", "per ")) else "number")
        if unit.endswith("points") or unit in {"百分點", "百分点"}:
            kind = "percentage_points"
        if not currency and unit in _UNITS:
            kind, multiplier = _UNITS[unit]
            value *= multiplier
        facts.add((kind, value))
    return facts


def numbers_supported(summary: str, source: str) -> bool:
    return numeric_facts(summary) <= numeric_facts(source)
