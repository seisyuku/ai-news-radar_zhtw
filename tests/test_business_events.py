import unittest
from datetime import datetime, timezone

from scripts.update_news import (
    BUSINESS_EVENT_KEYWORDS,
    build_story_record,
    business_event_score,
)

NOW = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)


class BusinessEventScoreTests(unittest.TestCase):
    def test_all_six_categories_have_keywords(self):
        self.assertEqual(
            set(BUSINESS_EVENT_KEYWORDS.keys()),
            {"earnings", "market", "security", "pricing", "benchmark", "model_release"},
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

    # --- feature/noise-gate: keyword tuning regressions ---
    def test_hackathon_does_not_trigger_security(self):
        item = {"title": "騰訊舉辦AI黑客松活動，吸引上千名開發者參加", "summary": ""}
        self.assertEqual(business_event_score(item), [])

    def test_hackathon_marathon_spelling_does_not_trigger_security(self):
        item = {"title": "公司舉辦駭客馬拉松活動慶祝十週年", "summary": ""}
        self.assertEqual(business_event_score(item), [])

    def test_genuine_security_still_matches_despite_hacker_substring(self):
        item = {"title": "Google被爆重大資安漏洞，CVE編號已公布", "summary": ""}
        self.assertEqual(business_event_score(item), ["security"])

    def test_gaming_leaderboard_does_not_trigger_benchmark(self):
        item = {"title": "《Marvel Rivals》最新版本推送，新增遊戲角色與排行榜賽季重置", "summary": ""}
        self.assertEqual(business_event_score(item), [])

    def test_genuine_leaderboard_still_matches_benchmark(self):
        item = {"title": "新模型在LMArena排行榜奪冠，勝率大幅提升", "summary": ""}
        self.assertEqual(business_event_score(item), ["benchmark"])

    def test_non_business_merger_does_not_trigger_market(self):
        item = {
            "title": "Section 219, the US-Israel Military Merger, Would Thwart American Democracy",
            "summary": "",
        }
        self.assertEqual(business_event_score(item), [])

    def test_code_merge_does_not_trigger_market(self):
        item = {"title": "我们合并了两个分支后重新部署", "summary": ""}
        self.assertEqual(business_event_score(item), [])

    def test_merger_with_business_context_triggers_market(self):
        item = {"title": "科技公司宣布合併計畫，雙方股東已批准這筆交易", "summary": ""}
        self.assertIn("market", business_event_score(item))

    def test_acquisition_keyword_alone_still_triggers_market(self):
        # "收购" ("acquisition") was never gated behind co-occurrence, only
        # merger/併購/合併 were - this pins that distinction.
        item = {"title": "Bun 被 Anthropic 收购后用 Rust 重写，月下载超 2200 万", "summary": ""}
        self.assertEqual(business_event_score(item), ["market"])

    # --- feature/tutorial-filter: eval/evals dev-context co-occurrence guard ---
    def test_eval_in_dev_guide_title_does_not_trigger_benchmark(self):
        item = {
            "title": (
                "Patter SDK Guide to Building a Restaurant Booking Phone Agent "
                "with Dynamic Variables, Guardrails, Latency Dashboards, and Eval Checks"
            ),
            "summary": "",
        }
        self.assertEqual(business_event_score(item), [])

    def test_chatgpt_skills_tutorial_residual_carries_no_badge(self):
        # Companion to test_chatgpt_skills_tutorial_is_a_known_accepted_residual
        # in test_ai_relevance.py: this title is now collected (task 2
        # decision) instead of hard-excluded, but it must still carry no
        # business-event badge and therefore never reach the featured
        # section - that's what makes the residual low-severity.
        item = {"title": "ChatGPT Skills怎麼用？3種建立方式教學、6組好用範例一次看", "summary": ""}
        self.assertEqual(business_event_score(item), [])

    def test_evals_with_building_does_not_trigger_benchmark(self):
        item = {"title": "Build an SDK eval harness for your agent", "summary": ""}
        self.assertEqual(business_event_score(item), [])

    def test_eval_alone_without_dev_context_still_triggers_benchmark(self):
        item = {"title": "New model tops the leaderboard in latest eval run", "summary": ""}
        self.assertEqual(business_event_score(item), ["benchmark"])

    def test_evals_alongside_benchmark_keyword_still_triggers_benchmark(self):
        # A stronger signal (benchmark/sota/leaderboard/...) in the same title
        # means the eval-dev-context guard should not suppress the match.
        item = {
            "title": "OpenAI publishes new evals for coding agents, sparking benchmark debate",
            "summary": "",
        }
        self.assertEqual(business_event_score(item), ["benchmark"])

    # --- feature/model-release-badge: model_release subject×verb×context gate ---
    def test_english_model_release_with_parameter_context(self):
        item = {
            "title": (
                "Ex-OpenAI CTO Murati's Thinking Machines drops Inkling, a 975B "
                "parameter model that leads US labs but trails China"
            ),
            "summary": "",
        }
        self.assertEqual(business_event_score(item), ["model_release"])

    def test_traditional_chinese_model_release(self):
        item = {"title": "Thinking Machines Lab釋出首款開放權重AI模型Inkling", "summary": ""}
        self.assertEqual(business_event_score(item), ["model_release"])

    def test_simplified_chinese_model_release_via_s2t_fabu_variant(self):
        # OpenCC s2t converts Simplified "发布" to "發佈" (not "發布") - this
        # pins that both Traditional spellings are matched.
        item = {"title": "穆拉蒂重磅回归：思维机器实验室发布首款多模态开源模型 Inkling", "summary": ""}
        self.assertEqual(business_event_score(item), ["model_release"])

    def test_lab_name_alone_without_release_verb_does_not_trigger_model_release(self):
        item = {
            "title": (
                "Thinking Machines amps up its bet against one-size-fits-all AI "
                "with its first open model, Inkling"
            ),
            "summary": "",
        }
        self.assertEqual(business_event_score(item), [])

    def test_release_verb_alone_without_model_context_does_not_trigger_model_release(self):
        item = {"title": "Inkling: Our open-weights model", "summary": ""}
        self.assertEqual(business_event_score(item), [])

    def test_lab_name_plus_verb_without_model_context_is_rejected(self):
        # Known adversarial pattern flagged during review: a lab-name
        # substring ("Grok") plus a release verb ("Open-Sources") in a
        # headline that isn't actually about a model release. The third-layer
        # MODEL_RELEASE_CONTEXT_TERMS guard exists specifically for this.
        item = {"title": "SpaceXAI Open-Sources Grok Build", "summary": ""}
        self.assertEqual(business_event_score(item), [])

    def test_model_release_only_scans_title_not_summary(self):
        # Unlike every other category, model_release deliberately does not
        # scan the summary - a lab name mentioned somewhere in a longer
        # summary isn't the same signal as being the subject of the headline.
        # (The summary text still legitimately triggers "benchmark" here,
        # since that category scans title+summary as normal - the point of
        # this test is that "model_release" specifically stays absent.)
        item = {
            "title": "Weekly AI roundup",
            "summary": "OpenAI releases a new flagship model with strong benchmark results.",
        }
        self.assertNotIn("model_release", business_event_score(item))


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
