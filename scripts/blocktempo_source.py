"""Bounded BlockTempo AI-category intake from its public WordPress JSON.

The category RSS has served stale cached pages. This declared JSON route reads
only titles, native publication dates and short excerpts, never article bodies.
It grants no publisher quality or featured/radar permissions.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit


SOURCE_ID = "blocktempo_ai"
SOURCE_NAME = "BlockTempo 動區動趨"
HOME_URL = "https://www.blocktempo.com/category/business/ai/"
API_URL = (
    "https://www.blocktempo.com/wp-json/wp/v2/posts?categories=309&per_page=30"
    "&_fields=id,date_gmt,link,title,excerpt,categories"
)
MAX_BYTES = 2_000_000
MAX_POSTS = 30
MAX_ITEMS = 8

# This source mixes speculative trading and lifestyle stories into category AI.
# Keep these exclusions local; financing, earnings and service policies remain
# eligible for the shared AI/news checks.
_TRADING = re.compile(r"巨鯨|巨鲸|空單|空单|爆倉|爆仓|槓桿|杠杆|美股開盤|美股开盘|大盤叩關|板卡|華強北|华强北", re.I)
_SIDE_TOPIC = re.compile(r"香菇山|巧克力|壽司師傅|寿司师傅|魚肉.*蛇肉|鱼肉.*蛇肉|數位極簡生活|数字极简生活|伴手禮|伴手礼|HackerTube|tokenmaxxing", re.I)


def _article_url(value) -> bool:
    if not isinstance(value, str):
        return False
    try:
        p = urlsplit(value)
        return (p.scheme == "https" and p.hostname == "www.blocktempo.com"
                and not p.username and not p.password and p.port in (None, 443)
                and not p.query and not p.fragment
                and bool(re.fullmatch(r"/[a-z0-9][a-z0-9-]*/", p.path)))
    except ValueError:
        return False


def parse_posts(content: bytes, now: datetime) -> list[dict]:
    """Require native GMT publication metadata; filter before the eight-item cap."""
    try:
        from . import update_news as u, candidate_feed_admission as admission
    except ImportError:  # direct scripts/update_news.py invocation
        import update_news as u
        import candidate_feed_admission as admission

    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now_must_have_timezone")
    if len(content) > MAX_BYTES:
        raise ValueError("blocktempo_response_too_large")
    try:
        posts = json.loads(content)
    except (ValueError, UnicodeError) as exc:
        raise ValueError("invalid_blocktempo_json") from exc
    if not isinstance(posts, list) or len(posts) > MAX_POSTS:
        raise ValueError("invalid_blocktempo_posts")
    eligible, candidates, valid = [], 0, 0
    for post in posts:
        if not isinstance(post, dict):
            candidates += 1
            continue
        categories = post.get("categories")
        if (isinstance(categories, list) and all(type(c) is int for c in categories)
                and 309 not in categories):
            continue
        candidates += 1
        title_obj, excerpt = post.get("title"), post.get("excerpt")
        date_gmt, url = post.get("date_gmt"), post.get("link")
        if (not isinstance(categories, list) or not all(type(c) is int for c in categories)
                or not isinstance(title_obj, dict) or not isinstance(title_obj.get("rendered"), str)
                or not isinstance(excerpt, dict) or not isinstance(excerpt.get("rendered"), str)
                or excerpt.get("protected") is not False or not _article_url(url)
                or not isinstance(date_gmt, str)
                or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", date_gmt)):
            continue
        try:
            published = datetime.fromisoformat(date_gmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        title = u.feed_entry_evidence({"summary": title_obj["rendered"]}, max_chars=500)["summary"]
        if not title:
            continue
        valid += 1
        if published < now - timedelta(days=5) or published > now:
            continue
        if (admission.title_rejection(SOURCE_ID, title)
                or _TRADING.search(title) or _SIDE_TOPIC.search(title)):
            continue
        evidence = u.feed_entry_evidence({"link": url, "summary": excerpt["rendered"]}, max_chars=320)
        record = {"site_id": "tw_media", "source": SOURCE_NAME, "title": title,
                  "url": u.normalize_url(url), "published_at": u.iso(published), **evidence}
        if not u.score_ai_relevance(record)["is_ai_related"]:
            continue
        eligible.append(record)
    if candidates and not valid:
        raise ValueError("invalid_blocktempo_fields")
    # Invalid, excluded and duplicate rows must not consume the cap.
    unique = {}
    for row in sorted(eligible, key=lambda row: row["published_at"], reverse=True):
        unique.setdefault(row["url"], row)
    return list(unique.values())[:MAX_ITEMS]


def fetch_posts(session, now: datetime) -> list[dict]:
    response = session.get(API_URL, timeout=20, headers={"Accept": "application/json"})
    response.raise_for_status()
    return parse_posts(response.content, now)
