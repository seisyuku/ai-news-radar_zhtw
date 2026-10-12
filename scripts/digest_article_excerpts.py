"""Capture TechNews lead paragraphs after selection; replay without fetching.

This optional preparation step is separate from offline digest generation.
The cache contains excerpts, never full HTML, and belongs in private output.
"""

from copy import deepcopy
import json
from pathlib import Path
import re
from urllib.parse import urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup
import requests

if __package__:
    from .archive_output import atomic_write_text
else:
    from archive_output import atomic_write_text


EXTRACTOR_VERSION = "technews-first-paragraph-v2"
MAX_PAGE_BYTES = 1024 * 1024
MAX_PARAGRAPH_CHARS = 10000
TRUNCATED = re.compile(r"(?:\[\s*…\s*\]|\[\.\.\.\])\s*$")


def article_url(value):
    """Only publisher article URLs; normalize the site's trailing slash."""
    if not isinstance(value, str):
        return None
    try:
        parsed = urlsplit(value)
        host = parsed.hostname or ""
        if (parsed.scheme != "https" or parsed.username or parsed.password
                or parsed.port not in {None, 443}
                or not (host == "technews.tw" or host.endswith(".technews.tw"))
                or not re.fullmatch(r"/\d{4}/\d{2}/\d{2}/[^/]+/?", parsed.path)):
            return None
        return urlunsplit(("https", host, parsed.path.rstrip("/") + "/", "", ""))
    except ValueError:
        return None


def _valid_paragraph(text):
    return (isinstance(text, str) and bool(text.strip())
            and len(text) <= MAX_PARAGRAPH_CHARS and not TRUNCATED.search(text))


def first_paragraph(page):
    """Return a complete publisher paragraph, not a description or page text."""
    soup = BeautifulSoup(page, "html.parser")
    content = soup.select_one(".entry-content")
    if content is None:
        raise ValueError("article_body_missing")
    for node in content.select("script, style, iframe, object, figure, .wp-caption, aside"):
        node.decompose()
    for paragraph in content.find_all("p"):
        # Inline links/emphasis must not insert spaces into Chinese sentences.
        text = re.sub(r"\s+", " ", paragraph.get_text("", strip=False)).strip()
        if not text or re.match(r"^(?:圖片來源|圖片出處|Photo credit|Image credit)\s*[:：]", text, re.I):
            continue
        if not _valid_paragraph(text):
            raise ValueError("article_paragraph_invalid")
        return text
    raise ValueError("article_paragraph_missing")


def fetch_paragraph(url):
    """Fetch HTML only, with no browser, assets, credentials or retry loop."""
    current = article_url(url)
    if current is None:
        raise ValueError("unsupported_article_url")
    for _ in range(3):
        with requests.get(current, timeout=(5, 12), stream=True, allow_redirects=False,
                          headers={"User-Agent": "AI-News-Radar/1.0 (publisher excerpt)"}) as response:
            if response.status_code in {301, 302, 303, 307, 308}:
                target = article_url(urljoin(current, response.headers.get("Location", "")))
                if target is None or target == current:
                    raise ValueError("article_redirect_invalid")
                current = target
                continue
            response.raise_for_status()
            chunks, length = [], 0
            for chunk in response.iter_content(chunk_size=32768):
                length += len(chunk)
                if length > MAX_PAGE_BYTES:
                    raise ValueError("article_page_too_large")
                chunks.append(chunk)
            return first_paragraph(b"".join(chunks))
    raise ValueError("article_redirect_limit")


def _needs_excerpt(candidate):
    return (article_url(candidate.get("primary_url")) is not None
            and bool(TRUNCATED.search(str(candidate.get("summary_original") or candidate.get("summary") or ""))))


def capture_excerpts(candidates, cache_path, *, fetcher=None):
    """Capture at most ten selected articles; a failure falls back to title.

    Successful excerpts are cached once per canonical URL/extractor version.
    Only selected candidates with visibly clipped TechNews summaries are read.
    Returned receipts are explicit input to apply_excerpts; replays never fetch.
    """
    candidates = list(candidates)
    if len(candidates) > 10:
        raise ValueError("excerpt_selection_limit")
    path = Path(cache_path)
    cache = {"extractor_version": EXTRACTOR_VERSION, "entries": {}}
    if path.exists():
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict) or not isinstance(loaded.get("entries"), dict):
            raise ValueError("excerpt_cache_invalid")
        if loaded.get("extractor_version") == EXTRACTOR_VERSION:
            cache = loaded
    fetcher = fetcher or fetch_paragraph
    receipts, fetched, hits, changed = {}, 0, 0, False
    for candidate in candidates:
        if not _needs_excerpt(candidate):
            continue
        url = article_url(candidate["primary_url"])
        if url in receipts:
            continue
        text = cache["entries"].get(url)
        if _valid_paragraph(text):
            hits += 1
        else:
            fetched += 1
            try:
                text = fetcher(url)
                if not _valid_paragraph(text):
                    raise ValueError("article_paragraph_invalid")
                cache["entries"][url] = text
                changed = True
            except Exception:
                receipts[url] = {"status": "unavailable"}
                continue
        receipts[url] = {"status": "available", "text": text}
    if changed:
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(path, json.dumps(cache, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
        path.chmod(0o600)
    return {"extractor_version": EXTRACTOR_VERSION, "entries": receipts}, {"fetched": fetched, "cache_hits": hits}


def apply_excerpts(candidates, captured):
    """Copy selected evidence and apply captured paragraphs, without I/O.

    Source references retain the original RSS text. The replacement carries
    its own article URL/method; it is publisher text, not generated synthesis.
    """
    if (not isinstance(captured, dict) or captured.get("extractor_version") != EXTRACTOR_VERSION
            or not isinstance(captured.get("entries"), dict)):
        raise ValueError("excerpt_capture_invalid")
    output = deepcopy(list(candidates))
    for candidate in output:
        if not _needs_excerpt(candidate):
            continue
        url = article_url(candidate["primary_url"])
        entry = captured["entries"].get(url)
        if entry is None:
            continue
        if not isinstance(entry, dict) or entry.get("status") not in {"available", "unavailable"}:
            raise ValueError("excerpt_capture_invalid")
        text = entry.get("text") if entry["status"] == "available" else None
        if entry["status"] == "available" and not _valid_paragraph(text):
            raise ValueError("excerpt_capture_invalid")
        candidate.update(summary=text, summary_original=text,
                         summary_kind="publisher" if text else "none", summary_translation=None,
                         summary_source_item_id=candidate.get("primary_item_id") if text else None,
                         summary_origin={"method": EXTRACTOR_VERSION, "url": url, "status": entry["status"]})
    return output
