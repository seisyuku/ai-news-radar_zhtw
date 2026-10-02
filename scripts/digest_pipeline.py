"""Build in-window stories from a captured digest input, without providers.

This stage returns existing story shapes. Candidate adaptation, selection,
health presentation and rendering belong to later digest stages.
"""

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

if __package__:
    from .digest_input import Diagnostic, DigestInput
    from .digest_window import DigestTimeError, DigestWindow, parse_published_at
    from . import update_news as news
else:
    from digest_input import Diagnostic, DigestInput
    from digest_window import DigestTimeError, DigestWindow, parse_published_at
    import update_news as news


@dataclass(frozen=True)
class DigestStories:
    """Owned working dictionaries; copy before downstream enrichment.

    Diagnostics cover this stage only, not the input loader's diagnostics.
    Items are the post-dedup evidence actually passed into story merging.
    """

    stories: tuple[dict[str, Any], ...]
    items: tuple[dict[str, Any], ...]
    diagnostics: tuple[Diagnostic, ...]


def _valid_source_url(value: object) -> bool:
    if not isinstance(value, str) or any(char.isspace() for char in value):
        return False
    try:
        parsed = urlsplit(value)
        return parsed.scheme.lower() in {"http", "https"} and bool(parsed.hostname)
    except ValueError:
        return False


def build_digest_stories(snapshot: DigestInput, window: DigestWindow) -> DigestStories:
    """Filter source publish timestamps first, then reuse reader AI/story rules.

    Never use first/last seen to admit a record; never pull evidence from
    outside the window. Ranking uses the fixed issue cutoff, not a wall clock.
    Archive order cannot choose equal-time merge anchors or duplicate winners.
    """
    counts: Counter[str] = Counter()
    eligible: list[dict[str, Any]] = []
    for item_id in sorted(snapshot.records):
        record = snapshot.records[item_id]
        if record.get("duplicate_of"):
            counts["duplicate_alias"] += 1
            continue
        try:
            published_at = parse_published_at(record.get("published_at"))
        except DigestTimeError as exc:
            counts[exc.code] += 1
            continue
        if not window.contains(published_at):
            counts["outside_window"] += 1
            continue
        title = record.get("title")
        if not isinstance(title, str) or not title.strip():
            counts["invalid_title"] += 1
            continue
        if not _valid_source_url(record.get("url")):
            counts["invalid_url"] += 1
            continue
        item = deepcopy(record)
        item["id"] = item_id
        item["published_at"] = published_at.isoformat().replace("+00:00", "Z")
        eligible.append(item)

    eligible.sort(key=lambda item: (-parse_published_at(item["published_at"]).timestamp(), item["id"]))
    prepared: list[dict[str, Any]] = []
    for item in eligible:
        item["title"] = news.to_zh_hant(news.maybe_fix_mojibake(item["title"].strip()))
        # The reader sets this before bilingual display. This stage uses no MT.
        item["title_original"] = item["title"]
        item.pop("title_bilingual", None)
        item["url"] = news.normalize_url(item["url"])
        if isinstance(item.get("summary"), str) and item["summary"]:
            item["summary"] = news.to_zh_hant(item["summary"])
        elif item.get("summary") is not None:
            item.pop("summary", None)
        source = item.get("source")
        item["source"] = news.maybe_fix_mojibake(news.normalize_source_for_display(
            str(item.get("site_id") or ""), source, item["url"],
        )) if isinstance(source, str) and source.strip() else "未標示來源"
        item["site_name"] = news.apply_site_name_alias(str(item.get("site_name") or ""))
        item["business_events"] = news.business_event_score(item)
        item = news.add_source_tier_fields(news.add_ai_relevance_fields(item))
        if item["ai_is_related"]:
            prepared.append(item)
        else:
            counts["not_ai_related"] += 1

    # Same deterministic reader policy, without translation or random all-mode.
    publisher_dedup = news.dedupe_same_publisher_items(prepared)
    limited = news.apply_reader_source_limits(publisher_dedup)
    dedup = news.suppress_near_duplicate_items(news.dedupe_items_by_title_url(limited, random_pick=False))
    items = news.apply_reader_source_limits(dedup)
    removed = len(prepared) - len(items)
    if removed:
        counts["reader_dedup_or_limit"] += removed
    # merge_story_items uses a stable time sort. Seed equal times with IDs.
    items.sort(key=lambda item: (parse_published_at(item["published_at"]), item["id"]))
    stories = news.merge_story_items(items, now=window.end_utc, window_hours=24)
    # Retain the existing story ranking; add only a final tie breaker.
    stories.sort(key=lambda story: (
        -float(story.get("score") or 0), str(story.get("latest_at") or ""),
        str(story.get("title") or ""), str(story.get("story_id") or ""),
    ))
    diagnostics = tuple(Diagnostic(code, count, "archive.json") for code, count in sorted(counts.items()))
    return DigestStories(tuple(stories), tuple(items), diagnostics)
