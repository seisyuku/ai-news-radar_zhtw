"""Render a bounded editorial digest as Traditional-Chinese Markdown.

This module only formats an already-built document. It does not fetch, rank,
translate, infer facts, or expose raw health payloads.
"""

from collections.abc import Mapping, Sequence
from datetime import datetime
import html
import re
from urllib.parse import quote, urlsplit

if __package__:
    from .digest_window import DigestTimeError, TAIPEI, parse_published_at, window_for_date
else:
    from digest_window import DigestTimeError, TAIPEI, parse_published_at, window_for_date


class RenderError(ValueError):
    """The document cannot be rendered without inventing content."""


_NOTICE_TEXT = {
    "health_not_window_coverage": "來源健康是單次觀測，不代表整個日報窗口的覆蓋率。",
    "archive_not_new_fetch": "留存新聞不代表本輪重新抓取。",
    "input_before_cutoff": "輸入快照早於本期截止時間，資料可能尚未涵蓋截止前的更新。",
    "archive_as_of_unknown": "archive 的資料時間未知。",
    "health_missing": "來源健康資料缺失，未提供健康統計。",
    "health_invalid": "來源健康資料無法使用，未提供健康統計。",
    "health_mismatched": "來源健康與新聞輸入不是同一時間快照，未附健康統計。",
    "health_unverifiable": "來源健康時間無法核對，未附健康統計。",
    "health_shape_unknown": "來源健康欄位不足，未提供健康統計。",
    "source_failures": "部分來源本輪失敗或部分失敗。",
    "source_status_unknown": "部分來源狀態未知。",
}
_URL = re.compile(r"^https?://[^\s<>]+$", re.IGNORECASE)


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _inline(value: object) -> str:
    # Escape Markdown syntax while retaining ordinary Unicode text.
    text = html.escape(" ".join(_text(value).split()), quote=False)
    return re.sub(r"([\\`*_[\]{}()>#+.!|~-])", r"\\\1", text)


def _url(value: object) -> str | None:
    value = _text(value)
    try:
        valid = _URL.fullmatch(value) and urlsplit(value).hostname
    except ValueError:
        valid = False
    return quote(value, safe="/:?#[]@!$&'*+,;=%~.-_") if valid else None


def _link(label: object, url: object) -> str:
    safe = _url(url)
    return f"[{_inline(label) or '原文'}]({safe})" if safe else _inline(label)


def _date(value: object) -> str:
    text = _text(value)
    if not text:
        return "日期未知"
    try:
        return parse_published_at(text).astimezone(TAIPEI).date().isoformat()
    except DigestTimeError:
        return "日期未知"


def _window(document: Mapping[str, object]) -> tuple[str, str]:
    window = document.get("window")
    if not isinstance(window, Mapping):
        raise RenderError("missing_window")
    date = _text(window.get("date"))
    start = _text(window.get("start_utc"))
    end = _text(window.get("end_utc"))
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date) or not start or not end:
        raise RenderError("invalid_window")
    try:
        expected = window_for_date(date)
        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
    except ValueError:
        raise RenderError("invalid_window") from None
    if (start_dt.tzinfo is None or end_dt.tzinfo is None
            or start_dt != expected.start_utc or end_dt != expected.end_utc):
        raise RenderError("invalid_window")
    local_start = start_dt.astimezone(TAIPEI).strftime("%Y-%m-%d %H:%M")
    local_end = end_dt.astimezone(TAIPEI).strftime("%Y-%m-%d %H:%M")
    return date, f"{local_start} 至 {local_end}（Asia/Taipei；起點含、終點不含）"


def _notice_lines(health: object) -> list[str]:
    if not isinstance(health, Mapping):
        return []
    notices = health.get("notices")
    if not isinstance(notices, Sequence) or isinstance(notices, (str, bytes)):
        return []
    lines = []
    for code in notices:
        if isinstance(code, str) and code in _NOTICE_TEXT and _NOTICE_TEXT[code] not in lines:
            lines.append(_NOTICE_TEXT[code])
    alignment = health.get("alignment")
    if alignment in {"mismatched", "unverifiable"}:
        code = f"health_{alignment}"
        if _NOTICE_TEXT[code] not in lines:
            lines.append(_NOTICE_TEXT[code])
    return lines


def _candidate_lines(candidate: Mapping[str, object], number: int) -> list[str]:
    title = _text(candidate.get("title")) or _text(candidate.get("title_original"))
    if not title:
        raise RenderError("candidate_missing_title")
    primary = _url(candidate.get("primary_url"))
    heading = _link(title, primary) if primary else _inline(title)
    lines = [f"### {number}. {heading}", ""]
    summary = _text(candidate.get("summary"))
    kind = candidate.get("summary_kind")
    if summary and kind not in {"publisher", "publisher_translation"}:
        raise RenderError("unsupported_summary_kind")
    label = "出版者摘要（既有快取譯文）：" if kind == "publisher_translation" else "出版者摘要："
    lines += [label + _inline(summary) if summary else "摘要：目前沒有可用的出版者摘要。", ""]
    date = _date(candidate.get("primary_published_at"))
    lines += [f"發布日期（臺北）：{date}", ""]
    sources = candidate.get("sources")
    refs = []
    if isinstance(sources, Sequence) and not isinstance(sources, (str, bytes)):
        for source in sources:
            if not isinstance(source, Mapping):
                continue
            link = _link(source.get("title") or source.get("title_original") or "原文", source.get("url"))
            publisher = _inline(source.get("source") or "未標示來源")
            refs.append(f"{link}（{publisher}，{_date(source.get('published_at'))}）")
    if refs:
        lines.append("來源：" + "；".join(refs))
    else:
        lines.append("來源：未標示來源")
    return lines


def render_digest(document: Mapping[str, object]) -> str:
    """Render one document; deterministic for the same JSON-safe input."""
    if not isinstance(document, Mapping):
        raise RenderError("invalid_document")
    date, interval = _window(document)
    lines = [f"# AI 新聞日報｜{_inline(date)}", "", f"涵蓋窗口：{interval}"]
    health_lines = _notice_lines(document.get("health"))
    if health_lines:
        lines += ["", "## 資料限制", ""] + [f"- {_inline(line)}" for line in health_lines]
    candidates = document.get("candidates", [])
    if not isinstance(candidates, Sequence) or isinstance(candidates, (str, bytes)):
        raise RenderError("invalid_candidates")
    lines += ["", "## 今日重點", ""]
    if not candidates:
        lines.append("本期沒有符合既有選題條件且可供刊出的新聞。")
    else:
        for number, candidate in enumerate(candidates, 1):
            if not isinstance(candidate, Mapping):
                raise RenderError("invalid_candidate")
            lines += _candidate_lines(candidate, number)
            lines.append("")
    diagnostics = document.get("diagnostics")
    if isinstance(diagnostics, Sequence) and not isinstance(diagnostics, (str, bytes)):
        safe = [d for d in diagnostics if isinstance(d, Mapping) and isinstance(d.get("code"), str)]
        if safe:
            lines += ["", "## 生成備註", "", "本段僅記錄生成階段的受控診斷，不代表新聞查證結果。"]
    return "\n".join(lines).rstrip() + "\n"
