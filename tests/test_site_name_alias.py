from __future__ import annotations

import unittest

from scripts.update_news import SITE_NAME_ALIASES, apply_site_name_alias


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

if __name__ == "__main__":
    unittest.main()
