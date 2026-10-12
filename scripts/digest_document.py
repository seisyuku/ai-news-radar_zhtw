"""Compose the offline digest stages into a JSON-safe versioned document."""

from dataclasses import asdict
from copy import deepcopy

if __package__:
    from .digest_json import canonical_json, document_identity
    from .digest_candidates import adapt_stories
    from .digest_health import summarize_digest_health
    from .digest_pipeline import build_digest_stories
    from .digest_selection import select_digest_candidates
    from .digest_news_policy import POLICY, select_news_candidates
    from .digest_article_excerpts import apply_excerpts
else:
    from digest_json import canonical_json, document_identity
    from digest_candidates import adapt_stories
    from digest_health import summarize_digest_health
    from digest_pipeline import build_digest_stories
    from digest_selection import select_digest_candidates
    from digest_news_policy import POLICY, select_news_candidates
    from digest_article_excerpts import apply_excerpts


PIPELINE_VERSION = "daily-digest-v2"
RENDER_VERSION = "markdown-v4"


def build_digest_document(snapshot, window, *, limit=None, same_source_penalty=0.03,
                          policy=POLICY, article_excerpts=None):
    stage = build_digest_stories(snapshot, window)
    candidates = adapt_stories(stage.stories, title_cache=snapshot.title_cache)
    if policy not in {POLICY, "existing_daily_brief"}:
        raise ValueError("invalid_digest_policy")
    legacy = policy == "existing_daily_brief"
    selector = select_digest_candidates if legacy else select_news_candidates
    limit = (20 if legacy else 10) if limit is None else limit
    selection = selector(stage, candidates, limit=limit,
                                         same_source_penalty=same_source_penalty)
    document = {
        "schema_version": 1,
        "pipeline_version": "daily-digest-v1" if legacy else PIPELINE_VERSION,
        "render_version": "markdown-v3" if legacy else RENDER_VERSION,
        "window": {"date": window.date, "timezone": window.timezone,
                   "start_utc": window.start_utc.isoformat().replace("+00:00", "Z"),
                   "end_utc": window.end_utc.isoformat().replace("+00:00", "Z")},
        "input_fingerprint": snapshot.fingerprint,
        "inputs": [asdict(row) for row in snapshot.inputs],
        "settings": asdict(selection.settings),
        "selection_counts": {"total_candidates": selection.total_candidates,
                             "eligible_count": selection.eligible_count,
                             "selected_count": len(selection.candidates)},
        "candidates": list(selection.candidates),
        "diagnostics": [asdict(row) for row in (*snapshot.diagnostics, *stage.diagnostics,
                                               *selection.diagnostics)],
        "health": asdict(summarize_digest_health(snapshot, window)),
    }
    if article_excerpts is not None:
        if legacy:
            raise ValueError("legacy_digest_has_no_article_excerpts")
        document["candidates"] = apply_excerpts(document["candidates"], article_excerpts)
        document["article_excerpts"] = deepcopy(article_excerpts)
    if not legacy:
        document["selection_diagnostics"] = {
            "candidate_count": selection.total_candidates,
            "eligible_count": selection.eligible_count,
            "selected_count": len(selection.candidates),
            "filtered_count": selection.total_candidates - selection.eligible_count,
            "empty_reason": (None if selection.candidates else
                             "no_candidates" if not selection.total_candidates else
                             "noise_or_no_concrete_information" if not selection.eligible_count else
                             "diversity_or_limit"),
        }
    document["input_identity"] = document_identity(document)
    return document
