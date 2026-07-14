import unittest
from datetime import datetime, timezone

from scripts.update_news import (
    BUSINESS_EVENT_KEYWORDS,
    build_story_record,
    business_event_score,
)

NOW = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)


class BusinessEventScoreTests(unittest.TestCase):
    def test_all_five_categories_have_keywords(self):
        self.assertEqual(
            set(BUSINESS_EVENT_KEYWORDS.keys()),
            {"earnings", "market", "security", "pricing", "benchmark"},
        )
        for category, keywords in BUSINESS_EVENT_KEYWORDS.items():
            self.assertTrue(keywords, f"{category} keyword list is empty")

    def test_no_match_returns_empty_list(self):
        item = {"title": "A quiet Tuesday for the AI coding assistant ecosystem", "summary": ""}
        self.assertEqual(business_event_score(item), [])

    def test_missing_fields_return_empty_list(self):
        self.assertEqual(business_event_score({}), [])

    # --- Traditional Chinese source ---
    def test_traditional_chinese_earnings(self):
        item = {"title": "輝達公布最新財報，營收季增二成", "summary": ""}
        self.assertEqual(business_event_score(item), ["earnings"])

    def test_traditional_chinese_security(self):
        item = {"title": "Google被爆重大資安漏洞，CVE編號已公布", "summary": ""}
        self.assertEqual(business_event_score(item), ["security"])

    def test_traditional_chinese_benchmark_via_summary(self):
        item = {"title": "新模型今日發布", "summary": "在 LMArena 排行榜上勝率大幅提升"}
        self.assertEqual(business_event_score(item), ["benchmark"])

    # --- Simplified Chinese source (must be matched via s2t normalization) ---
    def test_simplified_chinese_earnings(self):
        item = {"title": "阿里巴巴发布季度财报，营收超预期", "summary": ""}
        self.assertEqual(business_event_score(item), ["earnings"])

    def test_simplified_chinese_security(self):
        item = {"title": "微软遭遇零日漏洞攻击，官方紧急发布补丁", "summary": ""}
        self.assertEqual(business_event_score(item), ["security"])

    def test_simplified_chinese_market(self):
        item = {"title": "监管机构就该并购案启动反垄断审查", "summary": ""}
        self.assertEqual(business_event_score(item), ["market"])

    # --- English source ---
    def test_english_earnings(self):
        item = {"title": "OpenAI Reports Q3 Earnings, Revenue Beats Guidance", "summary": ""}
        self.assertEqual(business_event_score(item), ["earnings"])

    def test_english_pricing(self):
        item = {"title": "Anthropic Cuts API Pricing by 50%", "summary": ""}
        self.assertEqual(business_event_score(item), ["pricing"])

    def test_english_benchmark(self):
        item = {"title": "Model Achieves New SOTA on MMLU Benchmark", "summary": ""}
        self.assertEqual(business_event_score(item), ["benchmark"])

    # --- Multi-category and word-boundary safety ---
    def test_multiple_categories_can_match_same_item(self):
        item = {
            "title": "OpenAI財報顯示營收成長，同時宣布API降價方案",
            "summary": "",
        }
        self.assertEqual(business_event_score(item), ["earnings", "pricing"])

    def test_short_token_word_boundary_q1_does_not_match_substring(self):
        # "q1" must not fire inside an unrelated token that merely contains it.
        item = {"title": "Uniq1ue product codename leaked ahead of launch", "summary": ""}
        self.assertEqual(business_event_score(item), [])

    def test_short_token_q_quarter_matches_as_whole_word(self):
        item = {"title": "Company beats Q1 guidance on strong cloud demand", "summary": ""}
        self.assertEqual(business_event_score(item), ["earnings"])


class BusinessEventStoryRecordTests(unittest.TestCase):
    def _item(self, idx, *, business_events=(), site_id="official_ai"):
        return {
            "id": f"item-{idx}",
            "site_id": site_id,
            "site_name": "Official AI Updates",
            "source": "Test Feed",
            "title": f"Story item {idx}",
            "url": f"https://example.com/{idx}",
            "published_at": NOW.isoformat().replace("+00:00", "Z"),
            "ai_is_related": True,
            "ai_score": 0.9,
            "business_events": list(business_events),
        }

    def test_build_story_record_unions_business_events_across_merged_items(self):
        items = [
            self._item(1, business_events=["earnings"]),
            self._item(2, business_events=["security", "earnings"]),
        ]
        story = build_story_record("story_test", items, NOW, 24)
        self.assertEqual(story["business_events"], ["earnings", "security"])

    def test_build_story_record_empty_when_no_item_has_business_events(self):
        items = [self._item(1), self._item(2)]
        story = build_story_record("story_test", items, NOW, 24)
        self.assertEqual(story["business_events"], [])


if __name__ == "__main__":
    unittest.main()
