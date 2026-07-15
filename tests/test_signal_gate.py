import unittest
from datetime import datetime, timedelta, timezone

from scripts.update_news import (
    add_source_tier_fields,
    build_story_record,
    _group_aware_duplicate_count,
)

NOW = datetime(2026, 7, 15, 12, 0, tzinfo=timezone.utc)


def make_item(idx: int, *, title: str, url: str, site_id: str = "aihot", hours_ago: int = 1, business_events=()) -> dict:
    item = {
        "id": f"item-{idx}",
        "site_id": site_id,
        "site_name": site_id.title(),
        "source": "Test Feed",
        "title": title,
        "url": url,
        "published_at": (NOW - timedelta(hours=hours_ago)).isoformat().replace("+00:00", "Z"),
        "ai_is_related": True,
        "ai_score": 0.9,
        "business_events": list(business_events),
    }
    return add_source_tier_fields(item)


class GroupAwareDuplicateCountTests(unittest.TestCase):
    def test_same_ecosystem_group_collapses_to_one(self):
        items = [
            make_item(1, title="t", url="https://a.example/1", site_id="aibase"),
            make_item(2, title="t", url="https://a.example/2", site_id="iris"),
            make_item(3, title="t", url="https://a.example/3", site_id="kr36_ai"),
        ]
        self.assertEqual(_group_aware_duplicate_count(items), 1)

    def test_mixed_group_and_independent_source_counts_both(self):
        items = [
            make_item(1, title="t", url="https://a.example/1", site_id="aibase"),
            make_item(2, title="t", url="https://a.example/2", site_id="iris"),
            make_item(3, title="t", url="https://a.example/3", site_id="official_ai"),
        ]
        self.assertEqual(_group_aware_duplicate_count(items), 2)

    def test_same_site_id_but_different_outlets_are_not_collapsed(self):
        # official_ai/curated_media/tw_media each cover many distinct feeds
        # under one internal site_id, so bare site_id must not be used as the
        # grouping key for sources outside the defined ecosystem groups.
        items = [
            make_item(1, title="t", url="https://openai.com/x", site_id="official_ai"),
            make_item(2, title="t", url="https://anthropic.com/y", site_id="official_ai"),
        ]
        self.assertEqual(_group_aware_duplicate_count(items), 2)

    def test_single_item(self):
        items = [make_item(1, title="t", url="https://a.example/1", site_id="aibase")]
        self.assertEqual(_group_aware_duplicate_count(items), 1)

    def test_ungrouped_sources_unaffected_matches_raw_count(self):
        items = [
            make_item(1, title="t", url="https://a.example/1", site_id="techurls"),
            make_item(2, title="t", url="https://a.example/2", site_id="techurls"),
        ]
        # techurls is not in SOURCE_ECOSYSTEM_GROUPS: two techurls items are
        # still two independent items, same as pre-Plan-B behavior.
        self.assertEqual(_group_aware_duplicate_count(items), 2)


class BuildStoryRecordGroupAwarenessTests(unittest.TestCase):
    def test_duplicate_count_field_reflects_group_aware_count(self):
        items = [
            make_item(1, title="t", url="https://a.example/1", site_id="aibase"),
            make_item(2, title="t", url="https://a.example/2", site_id="iris"),
        ]
        story = build_story_record("story_test", items, NOW, 24)
        self.assertEqual(story["duplicate_count"], 1)
        self.assertEqual(story["importance_breakdown"]["story_heat"], 0.0)
        # Raw display fields are unaffected: both items still listed.
        self.assertEqual(story["source_count"], 2)
        self.assertEqual(story["item_count"], 2)

    def test_independent_sources_still_earn_story_heat(self):
        items = [
            make_item(1, title="t", url="https://a.example/1", site_id="official_ai"),
            make_item(2, title="t", url="https://a.example/2", site_id="opmlrss"),
        ]
        story = build_story_record("story_test", items, NOW, 24)
        self.assertEqual(story["duplicate_count"], 2)
        self.assertGreater(story["importance_breakdown"]["story_heat"], 0.0)


if __name__ == "__main__":
    unittest.main()
