"""Compose the offline digest stages into a JSON-safe versioned document."""

from dataclasses import asdict

if __package__:
    from .digest_json import canonical_json, document_identity
    from .digest_candidates import adapt_stories
    from .digest_health import summarize_digest_health
    from .digest_pipeline import build_digest_stories
    from .digest_selection import select_digest_candidates
else:
    from digest_json import canonical_json, document_identity
    from digest_candidates import adapt_stories
    from digest_health import summarize_digest_health
    from digest_pipeline import build_digest_stories
    from digest_selection import select_digest_candidates


PIPELINE_VERSION = "daily-digest-v1"
RENDER_VERSION = "markdown-v3"


def build_digest_document(snapshot, window, *, limit=20, same_source_penalty=0.03):
    stage = build_digest_stories(snapshot, window)
    candidates = adapt_stories(stage.stories, title_cache=snapshot.title_cache)
    selection = select_digest_candidates(stage, candidates, limit=limit,
                                         same_source_penalty=same_source_penalty)
    document = {
        "schema_version": 1,
        "pipeline_version": PIPELINE_VERSION,
        "render_version": RENDER_VERSION,
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
    document["input_identity"] = document_identity(document)
    return document
