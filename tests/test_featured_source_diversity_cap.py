"""Unit tests for assets/app.js's applyFeaturedSourceDiversityCap(), the
今日重點訊號 source-diversity cap (N=2) added per
.claude-reports/2026-07-21-aibase-signal-area-diagnosis.md /
fix/featured-source-diversity-cap-0721.

The cap only withholds a same-source row's seat when it ties the next
different-source candidate on both of boleStorySortCompare's first two
tiers (business-event badge, hotScore) - the exact degenerate condition the
diagnosis identified as letting storyScore's source_tier component decide
ranking among otherwise-equal single-source candidates. A genuine hotScore
edge is never overridden, and a withheld seat is only ever filled by
another candidate already present in the (badge-first) sorted pool - never
backfilled with a lower-quality item.

Runs the real function via tests/js_bridge.py (extracted straight out of
assets/app.js and executed under node), not a reimplementation, so these
tests fail if the shipped logic regresses.
"""
from __future__ import annotations

import pytest

from tests.js_bridge import extract_declarations, run_js

DECLARATIONS = extract_declarations(
    "BUSINESS_EVENT_LABELS",
    "businessEventBadges",
    "storyBusinessEvents",
    "storyHasBusinessEvent",
    "HOT_DECAY_HOURS",
    "HOT_SCORE_SCALE",
    "storyHotness",
    "storyHotScore",
    "storySourceCount",
    "storyTimeMs",
    "storyCandidateSiteId",
    "FEATURED_DIVERSITY_VISIBLE_SLOTS",
    "FEATURED_DIVERSITY_SOURCE_CAP",
    "applyFeaturedSourceDiversityCap",
)

# JS-side story-row builder shared by every scenario:
# mk(site, {hot: true}) -> a real-heat row (duplicate_count 2, latest_at now)
# mk(site)              -> a single-source, hotScore=0 badged row (the
#                           degenerate case the whole cap exists for)
HELPERS = """
function mk(site, opts) {
  opts = opts || {};
  const row = { site_id: site, business_events: ["model_release"] };
  if (opts.hot) {
    row.duplicate_count = 2;
    row.latest_at = new Date().toISOString();
  }
  return row;
}
function siteSeq(rows) { return rows.map((r) => r.site_id); }
"""


def _run(scenario_js: str) -> dict:
    script = f"{DECLARATIONS}\n\n{HELPERS}\n\n{scenario_js}"
    return run_js(script)


class TestTieDefersToDiversity:
    """同源 3 條平手 -> 第 3 條被讓出，讓不同來源候選遞補。"""

    def test_third_same_source_seat_is_deferred_behind_alternative(self):
        result = _run(
            """
            const rows = [mk('aibase'), mk('aibase'), mk('aibase'), mk('curated_media')];
            const out = applyFeaturedSourceDiversityCap(rows, 5, 2);
            console.log(JSON.stringify({ seq: siteSeq(out), length: out.length }));
            """
        )
        assert result["seq"][:3] == ["aibase", "aibase", "curated_media"]
        assert result["length"] == 4
        assert result["seq"].count("aibase") == 3  # nothing lost - the deferred row still shows up later


class TestRealHeatIsExempt:
    """同源第 3 條有真熱度（hotScore>0）-> 保留，不受上限約束。"""

    def test_third_same_source_seat_kept_when_it_has_real_heat(self):
        result = _run(
            """
            const rows = [mk('aibase'), mk('aibase'), mk('aibase', { hot: true }), mk('curated_media')];
            const out = applyFeaturedSourceDiversityCap(rows, 5, 2);
            console.log(JSON.stringify({ seq: siteSeq(out) }));
            """
        )
        assert result["seq"][:3] == ["aibase", "aibase", "aibase"]
        assert result["seq"][3] == "curated_media"


class TestNoQualifiedBackfillLeavesSeatEmpty:
    """讓出後無合格候選可遞補 -> 該格留空（不補位、不降級）。"""

    def test_pool_shorter_than_capacity_is_not_padded(self):
        # Only 4 qualified candidates total (3 aibase + 1 curated_media): the
        # 3rd aibase seat is deferred behind curated_media exactly as in the
        # tie scenario, but there is nothing left afterwards to fill a 5th
        # seat with, so the result must stay at 4 rows rather than being
        # padded out (no duplication, no invented candidate).
        result = _run(
            """
            const rows = [mk('aibase'), mk('aibase'), mk('aibase'), mk('curated_media')];
            const out = applyFeaturedSourceDiversityCap(rows, 5, 2);
            console.log(JSON.stringify({ seq: siteSeq(out), length: out.length }));
            """
        )
        assert result["length"] == 4
        assert result["seq"] == ["aibase", "aibase", "curated_media", "aibase"]

    def test_lone_source_with_no_alternative_anywhere_is_not_dropped(self):
        # No other source exists at all - diversity has nothing to swap in,
        # so the cap must not manufacture an empty seat by discarding a
        # perfectly qualified candidate; it keeps everything.
        result = _run(
            """
            const rows = [mk('aibase'), mk('aibase'), mk('aibase')];
            const out = applyFeaturedSourceDiversityCap(rows, 5, 2);
            console.log(JSON.stringify({ seq: siteSeq(out), length: out.length }));
            """
        )
        assert result["length"] == 3
        assert result["seq"] == ["aibase", "aibase", "aibase"]


class TestNormalFiveSourcesCapNotTriggered:
    """正常 5 個不同來源各 1 條 -> 上限完全不觸發，順序不變。"""

    def test_five_distinct_sources_pass_through_unchanged(self):
        result = _run(
            """
            const sites = ['aibase', 'curated_media', 'tw_media', 'official_ai', 'iris'];
            const rows = sites.map((s) => mk(s));
            const out = applyFeaturedSourceDiversityCap(rows, 5, 2);
            console.log(JSON.stringify({ seq: siteSeq(out) }));
            """
        )
        assert result["seq"] == ["aibase", "curated_media", "tw_media", "official_ai", "iris"]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
