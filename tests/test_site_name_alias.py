from __future__ import annotations

import datetime as _dt
import unittest

from scripts.update_news import SITE_NAME_ALIASES, apply_site_name_alias, build_creator_hot_items


class SiteNameAliasTests(unittest.TestCase):
    def test_known_generic_english_pool_labels_are_aliased(self):
        self.assertEqual(apply_site_name_alias("Curated Media"), "精選媒體")
        self.assertEqual(apply_site_name_alias("Official AI Updates"), "官方更新")
        self.assertEqual(apply_site_name_alias("TW Media"), "台灣媒體")
        self.assertEqual(apply_site_name_alias("OPML RSS"), "OPML")

    def test_proper_noun_site_names_pass_through_unchanged(self):
        for name in ("TechURLs", "AIbase", "Hacker News", "TikHub Douyin", "36Kr AI (Watchlist)"):
            self.assertEqual(apply_site_name_alias(name), name)

    def test_alias_map_values_are_never_themselves_aliased(self):
        # Idempotency guard: running the alias twice must not chain-translate.
        for old_name, new_name in SITE_NAME_ALIASES.items():
            self.assertEqual(apply_site_name_alias(new_name), new_name)

    def test_build_creator_hot_items_shows_new_name_for_archived_old_name_record(self):
        now = _dt.datetime.fromisoformat("2026-07-15T12:00:00+00:00")
        archive = {
            "legacy-name-item": {
                "id": "legacy-name-item",
                "site_id": "tikhub_xiaohongshu",
                # Archived before the alias existed; archive.json keeps this as-is.
                "site_name": "Official AI Updates",
                "source": "AI作者",
                "title": "OpenAI 熱門內容",
                "url": "https://example.com/legacy-name-item",
                "published_at": (now - _dt.timedelta(hours=1)).isoformat(),
                "first_seen_at": now.isoformat(),
                "last_seen_at": now.isoformat(),
                "creator_metrics": {"likes": 10, "comments": 0, "collects": 0, "shares": 0},
            }
        }

        items = build_creator_hot_items(archive, now, ai_only=False)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["site_name"], "官方更新")
        # The archive record itself must stay untouched (never rewritten).
        self.assertEqual(archive["legacy-name-item"]["site_name"], "Official AI Updates")


if __name__ == "__main__":
    unittest.main()
