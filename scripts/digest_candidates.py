"""Source-grounded candidate adaptation; no ranking, synthesis or providers."""

from collections.abc import Mapping, Sequence
import math
from typing import Any, Literal, TypedDict

if __package__:
    from .digest_window import DigestTimeError, parse_published_at
else:
    from digest_window import DigestTimeError, parse_published_at


class TranslationRef(TypedDict):
    input: str
    key: str
    alignment: Literal["unversioned"]


class SourceRef(TypedDict):
    item_id: str | None
    title: str | None
    title_original: str | None
    title_translation: TranslationRef | None
    url: str | None
    source: str | None
    site_id: str | None
    published_at: str | None
    summary: str | None
    summary_original: str | None
    summary_kind: Literal["publisher", "publisher_translation", "none"]
    summary_translation: TranslationRef | None


class EditorialCandidate(TypedDict):
    schema_version: Literal[1]
    story_id: str
    primary_item_id: str | None
    primary_url: str | None
    primary_published_at: str | None
    title: str | None
    title_original: str | None
    title_translation: TranslationRef | None
    title_origin: Literal["primary_source", "primary_item", "story"]
    sources: list[SourceRef]
    source_count: int
    summary: str | None
    summary_original: str | None
    summary_kind: Literal["publisher", "publisher_translation", "none"]
    summary_source_item_id: str | None
    summary_translation: TranslationRef | None
    importance: float | None
    business_events: list[str]
    reasons: list[str]
    verification: None


class CandidateError(ValueError):
    """Missing story identity cannot produce an addressable candidate."""


def _text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _publisher_text(value: object) -> str | None:
    # Preserve exact key material; no whitespace/case/fuzzy cache matching.
    return value if isinstance(value, str) and value.strip() else None


def _identity(value: object) -> str | None:
    # Legacy archive IDs need not be hex; never rewrite an existing identity.
    return value if isinstance(value, str) and value.strip() else None


def _display(original: str | None, cache: Mapping[str, str], prefix: str = "") -> tuple[str | None, TranslationRef | None]:
    if original is not None:
        key = prefix + original
        translated = _text(cache.get(key))
        if translated:
            return translated, {"input": "title-zh-cache.json", "key": key, "alignment": "unversioned"}
    return original, None


def _published_at(value: object) -> str | None:
    try:
        return parse_published_at(value).isoformat().replace("+00:00", "Z")
    except DigestTimeError:
        return None


def _strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for entry in value if (text := _text(entry)) is not None]


def _source_ref(row: Mapping[str, Any], cache: Mapping[str, str]) -> SourceRef:
    title_original = _publisher_text(row.get("title_original")) or _publisher_text(row.get("title"))
    title, title_translation = _display(title_original, cache)
    summary_original = _publisher_text(row.get("summary"))
    summary, summary_translation = _display(summary_original, cache, "summary::")
    return {
        "item_id": _identity(row.get("id")), "title": title, "title_original": title_original,
        "title_translation": title_translation, "url": _text(row.get("url")),
        "source": _text(row.get("source")), "site_id": _text(row.get("site_id")),
        "published_at": _published_at(row.get("published_at")),
        "summary": summary, "summary_original": summary_original,
        "summary_kind": "publisher_translation" if summary_translation else ("publisher" if summary_original else "none"),
        "summary_translation": summary_translation,
    }


def adapt_story(story: Mapping[str, Any], *, title_cache: Mapping[str, str] | None = None) -> EditorialCandidate:
    """Keep identity/order; adapt evidence and exact cached display translations.

    Missing optional legacy fields stay null. Primary date/summary require one
    unambiguous ID match in sources; neither latest_at nor another source fills
    the gap. Existing AI summaries, summary_zh and verification are not trusted
    as publisher evidence. No model or translation generator is invoked.
    """
    story_id = _identity(story.get("story_id"))
    if story_id is None:
        raise CandidateError("missing_story_id")
    cache = title_cache if title_cache is not None else {}
    rows = story.get("sources")
    if not isinstance(rows, list):
        rows = story.get("items")
    sources = [_source_ref(row, cache) for row in rows if isinstance(row, Mapping)] if isinstance(rows, list) else []
    primary = story.get("primary_item")
    primary = primary if isinstance(primary, Mapping) else {}
    primary_id = _identity(primary.get("id"))
    matches = [ref for ref in sources if primary_id is not None and ref["item_id"] == primary_id]
    resolved = matches[0] if len(matches) == 1 else None
    title_origin: Literal["primary_source", "primary_item", "story"]
    if resolved is not None:
        title, title_original, title_translation = resolved["title"], resolved["title_original"], resolved["title_translation"]
        title_origin = "primary_source"
    else:
        title_original = _publisher_text(primary.get("title_original")) or _publisher_text(primary.get("title"))
        title_origin = "primary_item"
        if title_original is None:
            title_original = _publisher_text(story.get("title"))
            title_origin = "story"
        # Unresolved metadata is not enough to borrow a publisher translation.
        title, title_translation = title_original, None
    raw_importance = next((story[key] for key in ("importance", "importance_score", "score") if story.get(key) is not None), None)
    try:
        importance = float(raw_importance) if isinstance(raw_importance, (int, float)) and not isinstance(raw_importance, bool) else None
    except OverflowError:
        importance = None
    if importance is not None and not math.isfinite(importance):
        importance = None
    return {
        "schema_version": 1, "story_id": story_id, "primary_item_id": primary_id,
        "primary_url": (resolved["url"] if resolved else None) or _text(primary.get("url")) or _text(story.get("primary_url")) or _text(story.get("url")),
        "primary_published_at": resolved["published_at"] if resolved else None,
        "title": title, "title_original": title_original, "title_translation": title_translation,
        "title_origin": title_origin, "sources": sources, "source_count": len(sources),
        "summary": resolved["summary"] if resolved else None,
        "summary_original": resolved["summary_original"] if resolved else None,
        "summary_kind": resolved["summary_kind"] if resolved else "none",
        "summary_source_item_id": primary_id if resolved and resolved["summary"] is not None else None,
        "summary_translation": resolved["summary_translation"] if resolved else None,
        "importance": importance, "business_events": _strings(story.get("business_events")),
        "reasons": _strings(story.get("reasons")), "verification": None,
    }


def adapt_stories(stories: Sequence[Mapping[str, Any]], *, title_cache: Mapping[str, str] | None = None) -> list[EditorialCandidate]:
    """Adapt all stories in their existing order; no selection or re-ranking."""
    return [adapt_story(story, title_cache=title_cache) for story in stories]
