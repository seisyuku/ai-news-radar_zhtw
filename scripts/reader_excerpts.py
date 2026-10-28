"""Bounded Hugging Face lead paragraphs for display translation only."""

import re
import time
from urllib.parse import urlsplit

from bs4 import BeautifulSoup


def article_url(value):
    try:
        url = urlsplit(str(value or ""))
        if (url.scheme == "https" and url.netloc == "huggingface.co"
                and re.fullmatch(r"/blog/(?:[A-Za-z0-9_-]+/)?[A-Za-z0-9_-]+", url.path)
                and not url.query and not url.fragment):
            return url.geturl()
    except ValueError:
        pass
    return None


def lead_paragraph(page):
    soup = BeautifulSoup(page, "html.parser")
    body = soup.select_one(".blog-content")
    if body is None:
        raise ValueError("article_body_missing")
    for node in body.select("script, style, aside, nav, pre, table, figure, blockquote"):
        node.decompose()
    for p in body.select("p"):
        text = re.sub(r"\s+", " ", p.get_text(" ", strip=True)).strip()
        # Skip resource/link menus and captions; retain one complete paragraph.
        if len(text) >= 80 and len(text) <= 1600 and not p.find("img"):
            return text
    raise ValueError("article_paragraph_missing")


def fetch_lead(session, url):
    if article_url(url) is None:
        raise ValueError("unsupported_article_url")
    with session.get(url, timeout=(4, 8), stream=True, allow_redirects=False,
                     headers={"User-Agent": "AI-News-Radar/1.0 (reader excerpt)"}) as response:
        if response.status_code != 200:
            raise ValueError("article_http_error")
        chunks, size = [], 0
        for chunk in response.iter_content(chunk_size=32768):
            size += len(chunk)
            if size > 1024 * 1024:
                raise ValueError("article_page_too_large")
            chunks.append(chunk)
        return lead_paragraph(b"".join(chunks))


def enrich(items_ai, items_all, session, cache, *, fetcher=None):
    """Never replace native summary or alter archive/scoring/event inputs."""
    cache = dict(cache) if isinstance(cache, dict) else {}
    fetcher = fetcher or (lambda url: fetch_lead(session, url))
    texts = {}
    status = {"attempted": 0, "cache_hits": 0, "available": 0, "failed": 0}
    started = time.monotonic()
    for item in items_ai:
        url = article_url(item.get("url"))
        if not url or item.get("summary") or url in texts:
            continue
        cached = cache.get(url)
        if isinstance(cached, str) and 80 <= len(cached) <= 1600:
            texts[url] = cached
            status["cache_hits"] += 1
            continue
        if status["attempted"] >= 6 or time.monotonic() - started >= 20:
            continue
        status["attempted"] += 1
        try:
            text = fetcher(url)
            if not isinstance(text, str) or not 80 <= len(text) <= 1600:
                raise ValueError("article_paragraph_invalid")
            texts[url] = cache[url] = text
        except Exception:
            status["failed"] += 1
    status["available"] = len(texts)

    def copy(item):
        out = dict(item)
        text = texts.get(item.get("url"))
        if text and not item.get("summary"):
            out["reader_summary"] = text
            out["reader_summary_kind"] = "publisher_lead"
        return out

    # Only current-window excerpts persist; the source archive is untouched.
    return [copy(i) for i in items_ai], [copy(i) for i in items_all], texts, status
