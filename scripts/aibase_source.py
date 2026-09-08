"""Public AIBase news lists: publisher Traditional Chinese, then English gaps.

Both routes serve the same first-page window (20 articles). Read only the
server-rendered list data, never article bodies or the newsletter landing page.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

AIBASE_INDEXES = {
    "tw": "https://news.aibase.com/tw/news",
    "en": "https://news.aibase.com/news",
}


def aibase_article_key(url: str) -> str | None:
    """Match publisher IDs across old www and current news language URLs."""
    parsed = urlsplit(str(url or ""))
    if parsed.hostname not in {"aibase.com", "www.aibase.com", "news.aibase.com"}:
        return None
    match = re.fullmatch(r"/(?:zh|tw|en|zh-tw|zh-TW|zh_tw)?/?news/(\d+)/?", parsed.path)
    return match.group(1) if match else None


def _text(value: object) -> str:
    return BeautifulSoup(value, "html.parser").get_text(" ", strip=True) if isinstance(value, str) else ""


def _date(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        result = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    # Publisher list createTime is local China time, shared by both languages.
    return result.replace(tzinfo=timezone(timedelta(hours=8))) if result.tzinfo is None else result


def _list_rows(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    script = soup.select_one("script#__NUXT_DATA__")
    if script is None:
        raise ValueError("AIBase news list payload missing")
    table = json.loads(script.get_text())
    if not isinstance(table, list):
        raise ValueError("AIBase news payload is not a reference table")

    def resolve(index, depth=0):
        if not isinstance(index, int) or isinstance(index, bool) or index < 0 or index >= len(table) or depth > 12:
            raise ValueError("Invalid AIBase news data reference")
        value = table[index]
        if isinstance(value, dict):
            return {key: resolve(ref, depth + 1) for key, ref in value.items()}
        if isinstance(value, list):
            return [resolve(ref, depth + 1) for ref in value]
        return value

    # Resolve only the list response, not unrelated Nuxt app/session state.
    for entry in table:
        if isinstance(entry, dict) and "getAINewsList" in entry:
            response = resolve(entry["getAINewsList"])
            if response.get("code") != 200:
                raise ValueError("AIBase news list returned an error")
            rows = response.get("data", {}).get("list")
            if not isinstance(rows, list) or not rows or not all(isinstance(row, dict) for row in rows):
                raise ValueError("AIBase news list empty or malformed")
            return rows
    raise ValueError("AIBase news list response missing")


def fetch_aibase_payload(session, now: datetime) -> tuple[list[dict], dict]:
    """Return RawItem-ready dictionaries and health detail; never invent dates."""
    versions = {}
    health = {}
    for language, index_url in AIBASE_INDEXES.items():
        try:
            response = session.get(index_url, timeout=30)
            response.raise_for_status()
            rows = _list_rows(response.text)
            items = {}
            for row in rows:
                article_id = str(row.get("oid", ""))
                if not re.fullmatch(r"[1-9]\d*", article_id):
                    continue
                items[article_id] = {
                    "title": _text(row.get("title")),
                    "summary": _text(row.get("description")),
                    "published_at": _date(row.get("createTime")),
                    "url": f"{index_url}/{article_id}",
                }
            if not items:
                raise ValueError("AIBase news list contains no article IDs")
            versions[language] = items
            health[language] = {"status": "ok", "count": len(items), "url": index_url}
        except Exception as exc:
            health[language] = {"status": "failed", "count": 0, "url": index_url, "error": str(exc)}
    if not versions:
        raise ValueError("AIBase both language indexes failed: " + json.dumps(health, ensure_ascii=False))

    out = []
    supplemented = 0
    for article_id in dict.fromkeys([*versions.get("tw", {}), *versions.get("en", {})]):
        tw = versions.get("tw", {}).get(article_id, {})
        en = versions.get("en", {}).get(article_id, {})
        fields = {}
        languages = {}
        for field in ("title", "summary", "published_at"):
            if tw.get(field):
                fields[field], languages[field] = tw[field], "tw"
            elif en.get(field):
                fields[field], languages[field] = en[field], "en"
            else:
                fields[field] = None if field == "published_at" else ""
        if not fields["title"]:
            continue
        english_fields = [field for field, language in languages.items() if language == "en"]
        supplemented += bool(english_fields)
        content_language = languages["title"]
        fields["url"] = (tw if tw else en)["url"]
        languages["url"] = "tw" if tw else "en"
        fields["meta"] = {
            "aibase_article_id": article_id,
            "content_language": content_language,
            "field_languages": languages,
            "summary": fields["summary"],
            "english_supplemented_fields": english_fields,
            "aibase_available_languages": [lang for lang in ("tw", "en") if article_id in versions.get(lang, {})],
        }
        out.append(fields)
    if not out:
        raise ValueError("AIBase news lists contain no usable titles")
    mode = "english_fallback" if "tw" not in versions else "english_supplement" if supplemented else "traditional_chinese"
    return out, {"language_status": health, "language_mode": mode, "english_supplemented_count": supplemented,
                 "undated_count": sum(item["published_at"] is None for item in out),
                 "degraded": len(versions) < 2}
