"""Source-specific RSS preselection for CyberQ and AlphaLab.

The production Taiwan-media collector calls this module for these two feeds;
the standalone probe uses the same rules without writing public snapshots.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlsplit

import requests

try:
    from . import update_news
except ImportError:  # direct scripts/update_news.py invocation
    import update_news


FEEDS = {
    "cyberq": {
        "url": "https://cyberq.tw/feed/", "host": "cyberq.tw",
        "title": "CyberQ 賽博客", "max_entries": 8,
    },
    "alphalab": {
        "url": "https://www.alphalab.site/feed.xml", "host": "www.alphalab.site",
        "title": "AlphaLab", "max_entries": 8,
    },
}

_ROUNDUP = re.compile(r"產業精選|趨勢[周週]報|每日[彙汇]整|今日重點|weekly digest", re.I)
_TUTORIAL = re.compile(r"教學|指南|入門|攻略|懶人包|怎麼做|怎麼辦|四步排查|五步驗收|用 AI 來|\bhow to\b", re.I)
_PROMOTION = re.compile(r"業配|廣編|合作推廣|贊助內容|sponsored|advertorial", re.I)
# These two already-reviewed CyberQ headlines used AI as incidental context.
_CYBERQ_SIDE_TOPIC = re.compile(r"iPhone.*(?:越獄|遭攻破)|黃金.*(?:出口|央行)", re.I)


def _published_at(entry: dict) -> datetime | None:
    """Require an explicit publication date and timezone; ignore updated."""
    raw = str(entry.get("published") or entry.get("pubDate") or "").strip()
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
    except (TypeError, ValueError, IndexError):
        try:
            if not re.match(r"^\d{4}-\d{2}-\d{2}T", raw):
                return None
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
    return dt.astimezone(timezone.utc) if dt.tzinfo and dt.utcoffset() is not None else None


def _article_url(url: str, host: str) -> bool:
    try:
        parsed = urlsplit(url)
        return (parsed.scheme == "https" and parsed.hostname == host
                and not parsed.username and not parsed.password
                and parsed.port in (None, 443) and bool(parsed.path.strip("/")))
    except ValueError:
        return False


def _alphalab_ai_category(entry: dict) -> bool:
    for tag in entry.get("tags") or []:
        scheme = str(tag.get("scheme") or "") if isinstance(tag, dict) else ""
        try:
            parsed = urlsplit(scheme)
        except ValueError:
            continue
        path = parsed.path.rstrip("/")
        if (parsed.scheme == "https" and parsed.hostname == "www.alphalab.site"
                and (path == "/category/ai" or path.startswith("/category/ai/"))):
            return True
    return False


def title_rejection(source_id: str, title: str) -> str | None:
    """Source-only exclusions, applied before the per-feed article cap."""
    if _ROUNDUP.search(title):
        return "roundup"
    if _TUTORIAL.search(title):
        return "tutorial"
    if _PROMOTION.search(title):
        return "promotion"
    if source_id == "cyberq" and _CYBERQ_SIDE_TOPIC.search(title):
        return "incidental_ai"
    return None


def preselect_feed(content: bytes, source_id: str, now: datetime) -> tuple[list[dict], dict]:
    """Parse one public feed into bounded candidates and reason counts.

    This is an admission prefilter, not an AI score or a publisher grant.
    Shared AI and publisher governance still apply during generation.
    """
    if source_id not in FEEDS:
        raise ValueError("unknown_source")
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now_must_have_timezone")
    spec = FEEDS[source_id]
    entries = update_news.parse_group_feed_entries(content, now)
    kept: list[dict] = []
    reasons: Counter[str] = Counter()
    seen: set[str] = set()
    valid_metadata = False
    for entry in entries:
        title = str(entry.get("title") or "").strip()
        url = str(entry.get("link") or "").strip()
        published = _published_at(entry)
        if not title or not url or published is None:
            reasons["invalid_metadata"] += 1
            continue
        valid_metadata = True
        if not _article_url(url, spec["host"]):
            reasons["wrong_article_host"] += 1
            continue
        if published < now - timedelta(days=5) or published > now + timedelta(minutes=5):
            reasons["outside_five_days"] += 1
            continue
        if source_id == "alphalab" and not _alphalab_ai_category(entry):
            reasons["outside_ai_category"] += 1
            continue
        rejection = title_rejection(source_id, title)
        if rejection:
            reasons[rejection] += 1
            continue
        if source_id == "alphalab":
            # The publisher's AI-category scheme is a scope boundary, not an
            # AI grant. The shared scorer can recognize named models and
            # agent standards that the generic Taiwan-media keyword list misses.
            ai = update_news.score_ai_relevance({
                "site_id": source_id, "source": spec["title"], "site_name": spec["title"],
                "title": title, "url": url,
            })
            if not ai["is_ai_related"]:
                reasons["no_ai_signal"] += 1
                continue
        else:
            generic_title = update_news.curated_feed_entry_allowed(
                {"include_keywords": update_news.TW_MEDIA_INCLUDE_KEYWORDS,
                 "strict_title_filter": True}, title, url
            )
            # The generic list omits some model names. A CyberQ firsthand
            # test can still enter the candidate pool when the shared AI
            # scorer recognizes its title; unrelated Prompt prose cannot.
            firsthand_ai = title.startswith(("實測", "深度實測")) and update_news.score_ai_relevance({
                "site_id": source_id, "source": spec["title"], "site_name": spec["title"],
                "title": title, "url": url,
            })["is_ai_related"]
            if not generic_title and not firsthand_ai:
                reasons["no_ai_title_signal"] += 1
                continue
        normalized = update_news.normalize_url(url)
        if normalized in seen:
            reasons["duplicate"] += 1
            continue
        seen.add(normalized)
        evidence = update_news.feed_entry_evidence(entry, max_chars=320)
        kept.append({
            "source_id": source_id, "source": spec["title"], "title": title,
            "url": normalized, "published_at": update_news.iso(published),
            "summary": evidence["summary"], "feed_url": spec["url"],
        })
        if len(kept) >= spec["max_entries"]:
            break
    if entries and not valid_metadata:
        raise ValueError("invalid_feed_fields")
    return kept, {"source_id": source_id, "feed_entries": len(entries),
                  "candidate_count": len(kept), "rejected": dict(sorted(reasons.items()))}


def probe_live(output_dir: Path, now: datetime, session: requests.Session | None = None) -> dict:
    """Explicit shadow probe; writes only short candidates and health status."""
    client = session or requests.Session()
    statuses = []
    candidates = []
    for source_id, spec in FEEDS.items():
        try:
            response = client.get(
                spec["url"], timeout=20,
                headers={"User-Agent": update_news.BROWSER_UA,
                         "Accept": "application/rss+xml, application/atom+xml, application/xml"},
            )
            response.raise_for_status()
            if len(response.content) > 2_000_000:
                raise ValueError("feed_too_large")
            rows, status = preselect_feed(response.content, source_id, now)
            candidates.extend(rows)
            statuses.append({**status, "status": "ok", "feed_url": spec["url"]})
        except (requests.RequestException, ValueError) as exc:
            statuses.append({"source_id": source_id, "status": "failed",
                             "reason": str(exc) if isinstance(exc, ValueError) else type(exc).__name__,
                             "feed_url": spec["url"]})
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = update_news.iso(now)
    result = {"generated_at": stamp, "mode": "isolated_candidate_probe", "sources": statuses}
    (output_dir / "source-status.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "candidate-items.json").write_text(
        json.dumps({"generated_at": stamp, "items": candidates}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Opt-in isolated CyberQ/AlphaLab RSS probe")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = probe_live(args.output_dir, datetime.now(timezone.utc))
    print(json.dumps(result, ensure_ascii=False))
    return 1 if any(row["status"] != "ok" for row in result["sources"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
