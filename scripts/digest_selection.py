"""Select existing stories, then retain the matching candidate evidence."""

from collections.abc import Sequence
from copy import deepcopy
from dataclasses import dataclass
import math

if __package__:
    from .digest_candidates import EditorialCandidate
    from .digest_input import Diagnostic
    from .digest_pipeline import DigestStories
    from . import update_news as news
else:
    from digest_candidates import EditorialCandidate
    from digest_input import Diagnostic
    from digest_pipeline import DigestStories
    import update_news as news


class SelectionError(ValueError):
    """Safe failure for invalid settings or mixed/ambiguous stage identities."""


@dataclass(frozen=True)
class SelectionSettings:
    limit: int
    same_source_penalty: float
    brief_score_gate: float
    policy: str = "existing_daily_brief"


@dataclass(frozen=True)
class DigestSelection:
    candidates: tuple[EditorialCandidate, ...]
    total_candidates: int
    eligible_count: int
    settings: SelectionSettings
    diagnostics: tuple[Diagnostic, ...]


def select_digest_candidates(
    stage: DigestStories, candidates: Sequence[EditorialCandidate], *,
    limit: int = 20, same_source_penalty: float = 0.03,
) -> DigestSelection:
    """Reuse the brief gate/diversity selector without inventing new scores.

    Inputs must be matching D04/D05 results. Identity gaps/duplicates fail,
    rather than silently substitute or fill a selected slot. Diagnostics
    belong to selection only; decoded input and pipeline diagnostics stay
    in their own stages. The returned evidence is independently owned.
    """
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
        raise SelectionError("invalid_limit")
    try:
        penalty = float(same_source_penalty) if isinstance(same_source_penalty, (int, float)) and not isinstance(same_source_penalty, bool) else float("nan")
    except OverflowError:
        penalty = float("nan")
    if not math.isfinite(penalty) or penalty < 0:
        raise SelectionError("invalid_source_penalty")
    stories = {}
    for story in stage.stories:
        story_id = story.get("story_id")
        if not isinstance(story_id, str) or not story_id.strip():
            raise SelectionError("invalid_story_id")
        if story_id in stories:
            raise SelectionError("duplicate_story_id")
        score = story.get("score")
        if score is not None:
            try:
                valid_score = not isinstance(score, bool) and math.isfinite(float(score))
            except (TypeError, ValueError, OverflowError):
                valid_score = False
            if not valid_score:
                raise SelectionError("invalid_story_score")
        stories[story_id] = story
    by_id = {}
    for candidate in candidates:
        story_id = candidate.get("story_id")
        if not isinstance(story_id, str) or not story_id.strip():
            raise SelectionError("invalid_candidate_id")
        if story_id in by_id:
            raise SelectionError("duplicate_candidate_id")
        by_id[story_id] = candidate
    if set(by_id) != set(stories):
        raise SelectionError("candidate_story_mismatch")

    # Existing selector sorts score/title stably; seed exact ties by story ID.
    eligible = [stories[key] for key in sorted(stories) if news.story_passes_brief_gate(stories[key])]
    selected = news.select_diverse_stories(eligible, limit, same_source_penalty=penalty)
    output = tuple(deepcopy(by_id[story["story_id"]]) for story in selected)
    diagnostics = []
    if len(stories) > len(eligible):
        diagnostics.append(Diagnostic("below_brief_gate", len(stories) - len(eligible), "digest_selection"))
    if len(eligible) > len(output):
        diagnostics.append(Diagnostic("diversity_or_limit", len(eligible) - len(output), "digest_selection"))
    return DigestSelection(
        output, len(stories), len(eligible),
        SelectionSettings(limit, penalty, news.BRIEF_SCORE_GATE), tuple(diagnostics),
    )
