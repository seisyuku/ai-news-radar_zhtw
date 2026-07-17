import unittest

from scripts.ai_relevance import add_ai_relevance_fields, is_ai_related_record, score_ai_relevance


class AiRelevanceScoringTests(unittest.TestCase):
    def test_scores_strong_ai_signal_with_reason(self):
        rec = {
            "site_id": "techurls",
            "site_name": "TechURLs",
            "source": "V2EX",
            "title": "OpenAI releases new GPT model",
            "url": "https://example.com/ai",
        }
        result = score_ai_relevance(rec)
        self.assertTrue(result["is_ai_related"])
        self.assertGreaterEqual(result["score"], 0.65)
        self.assertEqual(result["label"], "model_release")
        self.assertIn("openai", result["signals"])
        self.assertIn("matched_ai_signal", result["reason"])

    def test_rejects_broad_model_without_tech_context(self):
        rec = {
            "site_id": "buzzing",
            "site_name": "Buzzing",
            "source": "general",
            "title": "这个商业模型终于跑通了",
            "url": "https://example.com/model",
        }
        result = score_ai_relevance(rec)
        self.assertFalse(result["is_ai_related"])
        self.assertLess(result["score"], 0.65)
        self.assertEqual(result["reason"], "missing_meaningful_ai_signal")

    def test_accepts_broad_ai_plus_tech_context(self):
        rec = {
            "site_id": "techurls",
            "site_name": "TechURLs",
            "source": "GitHub",
            "title": "开源推理框架支持更多GPU后端",
            "url": "https://example.com/inference-gpu",
        }
        result = score_ai_relevance(rec)
        self.assertTrue(result["is_ai_related"])
        self.assertGreaterEqual(result["score"], 0.65)
        self.assertEqual(result["reason"], "matched_broad_ai_plus_tech_signal")
        self.assertIn("gpu", result["signals"])

    def test_accepts_agent_context_as_developer_tool(self):
        rec = {
            "site_id": "opmlrss",
            "site_name": "OPML RSS",
            "source": "BestBlogs.dev",
            "title": "分层记忆：Agent 中的上下文管理",
            "url": "https://example.com/agent-context",
        }
        result = score_ai_relevance(rec)
        self.assertTrue(result["is_ai_related"])
        self.assertGreaterEqual(result["score"], 0.65)
        self.assertEqual(result["label"], "agent_workflow")

    def test_trusted_ai_source_defaults_to_keep(self):
        rec = {
            "site_id": "aihot",
            "site_name": "AI HOT",
            "source": "AI HOT",
            "title": "今日值得关注的产品更新",
            "url": "https://aihot.virxact.com/post/1",
        }
        result = score_ai_relevance(rec)
        self.assertTrue(result["is_ai_related"])
        self.assertGreaterEqual(result["score"], 0.65)
        self.assertEqual(result["reason"], "trusted_ai_source_default_keep")

    def test_rejects_explicit_adult_promotion_even_with_ai_keyword(self):
        rec = {
            "site_id": "socialdata_x",
            "site_name": "SocialData X",
            "source": "@spam_account",
            "title": "AI virtual girlfriends with uncensored pictures and explicit promotion",
            "url": "https://x.com/spam_account/status/1",
        }
        result = score_ai_relevance(rec)
        self.assertFalse(result["is_ai_related"])
        self.assertEqual(result["reason"], "unsafe_promotional_content")

    def test_keeps_neutral_safety_news_with_single_adult_term(self):
        rec = {
            "site_id": "techurls",
            "site_name": "TechURLs",
            "source": "AI policy",
            "title": "OpenAI publishes a safety policy for detecting AI-generated pornography",
            "url": "https://example.com/ai-safety-policy",
        }
        result = score_ai_relevance(rec)
        self.assertTrue(result["is_ai_related"])

    def test_curated_media_keeps_trusted_ai_feed(self):
        rec = {
            "site_id": "curated_media",
            "site_name": "精選媒體",
            "source": "TechCrunch AI",
            "title": "Startup raises funding for enterprise workflow automation",
            "url": "https://techcrunch.com/example",
        }
        result = score_ai_relevance(rec)
        self.assertTrue(result["is_ai_related"])
        self.assertEqual(result["reason"], "curated_media_source_filter")
        self.assertEqual(result["label"], "industry_business")

    def test_curated_general_feed_requires_title_signal(self):
        rec = {
            "site_id": "curated_media",
            "site_name": "精選媒體",
            "source": "The Verge",
            "title": "A new phone accessory launches this week",
            "url": "https://www.theverge.com/example",
        }
        result = score_ai_relevance(rec)
        self.assertFalse(result["is_ai_related"])
        self.assertEqual(result["reason"], "curated_media_requires_ai_title_or_trusted_ai_feed")

    def test_curated_research_feed_is_research_labeled_and_capped(self):
        rec = {
            "site_id": "curated_media",
            "site_name": "精選媒體",
            "source": "MarkTechPost Research",
            "title": "A new benchmark evaluates multimodal LLM reasoning",
            "url": "https://www.marktechpost.com/example",
        }
        result = score_ai_relevance(rec)
        self.assertTrue(result["is_ai_related"])
        self.assertEqual(result["label"], "research_paper")
        self.assertLessEqual(result["score"], 0.76)

    def test_english_tutorial_title_is_excluded_even_from_trusted_source(self):
        rec = {
            "site_id": "curated_media",
            "site_name": "精選媒體",
            "source": "TechCrunch AI",
            "title": (
                "Patter SDK Guide to Building a Restaurant Booking Phone Agent "
                "with Dynamic Variables, Guardrails, Latency Dashboards, and Eval Checks"
            ),
            "url": "https://example.com/patter-sdk-guide",
        }
        result = score_ai_relevance(rec)
        self.assertFalse(result["is_ai_related"])
        self.assertEqual(result["reason"], "tutorial_title_pattern")
        self.assertEqual(result["label"], "tutorial_excluded")

    def test_how_to_tutorial_is_excluded_even_from_default_ai_source(self):
        rec = {
            "site_id": "aihot",
            "site_name": "AI HOT",
            "source": "AI HOT",
            "title": "How to fine-tune your own LLM in five easy steps",
            "url": "https://aihot.virxact.com/post/2",
        }
        result = score_ai_relevance(rec)
        self.assertFalse(result["is_ai_related"])
        self.assertEqual(result["reason"], "tutorial_title_pattern")

    def test_bare_jiaoxue_no_longer_hard_excludes_a_business_headline(self):
        # feature/tutorial-filter task 2: bare "教學"/"教学" was deliberately
        # dropped from the ZH keyword list because it also means "teaching"
        # as a plain noun, which was hard-killing real product/business news
        # like this one (a free-program announcement, not a how-to piece).
        rec = {
            "site_id": "aibase",
            "site_name": "AIbase",
            "source": "AIbase",
            "title": "Anthropic 免费推出 Claude for Teachers，助力美国教师智慧教学！",
            "url": "https://example.com/claude-for-teachers",
        }
        result = score_ai_relevance(rec)
        self.assertTrue(result["is_ai_related"])
        self.assertNotEqual(result["reason"], "tutorial_title_pattern")

    def test_chatgpt_skills_tutorial_is_a_known_accepted_residual(self):
        # feature/tutorial-filter task 2 decision: strict start-anchoring for
        # English phrases plus the compound-only ZH keyword list means this
        # genuine how-to article (教學 appears mid-title, not as one of the
        # compound forms, and no English anchor matches a Chinese-language
        # title) is no longer hard-excluded. Accepted as a known residual
        # rather than re-widening bare "教學"/"教学" (which would resurrect
        # the false-kill in the test above): it carries no business-event
        # keyword, so it gets no badge and never reaches the featured
        # section - just ordinary noise in the general list.
        rec = {
            "site_id": "tw_media",
            "site_name": "台灣媒體",
            "source": "數位時代",
            "title": "ChatGPT Skills怎麼用？3種建立方式教學、6組好用範例一次看",
            "url": "https://example.com/chatgpt-skills-tutorial",
        }
        result = score_ai_relevance(rec)
        self.assertTrue(result["is_ai_related"])
        self.assertNotEqual(result["reason"], "tutorial_title_pattern")

    def test_non_tutorial_ai_news_is_not_caught_by_tutorial_filter(self):
        rec = {
            "site_id": "techurls",
            "site_name": "TechURLs",
            "source": "V2EX",
            "title": "OpenAI releases new GPT model",
            "url": "https://example.com/ai",
        }
        result = score_ai_relevance(rec)
        self.assertTrue(result["is_ai_related"])
        self.assertNotEqual(result["reason"], "tutorial_title_pattern")

    def test_adds_public_debug_fields(self):
        rec = {
            "site_id": "official_ai",
            "site_name": "Official AI Updates",
            "source": "GitHub Changelog",
            "title": "GitHub Copilot adds a coding agent",
            "url": "https://example.com/copilot-agent",
        }
        out = add_ai_relevance_fields(rec)
        self.assertTrue(out["ai_is_related"])
        self.assertIn("ai_score", out)
        self.assertIn("ai_label", out)
        self.assertIn("ai_relevance_reason", out)
        self.assertIn("ai_signals", out)
        self.assertTrue(is_ai_related_record(rec))


if __name__ == "__main__":
    unittest.main()
