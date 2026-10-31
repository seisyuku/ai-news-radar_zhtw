import json
import re
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from scripts.update_news import (
    add_bilingual_fields,
    add_source_tier_fields,
    build_latest_payloads,
    dedupe_items_by_title_url,
    is_ai_related_record,
    maybe_fix_mojibake,
    apply_canonical_reverse_fix,
    backfill_canonical_names,
    mask_canonical_names,
    normalize_source_for_display,
    parse_curated_ai_media_feed_items,
    parse_date_any,
    parse_feed_entries_via_xml,
    parse_anthropic_news_items,
    parse_tencent_newsroom_items,
    parse_openai_codex_changelog_items,
    redact_public_text,
    repair_zh_title_translation,
    source_tier_for_site,
    source_tier_sort_key,
)


class TopicFilterTests(unittest.TestCase):


    def test_accepts_ai_keyword(self):
        rec = {
            "site_id": "test_source",
            "site_name": "Test Source",
            "source": "V2EX",
            "title": "OpenAI releases new GPT model",
            "url": "https://example.com/ai",
        }
        self.assertTrue(is_ai_related_record(rec))

    def test_accepts_copilot_keyword(self):
        rec = {
            "site_id": "official_ai",
            "site_name": "Official AI Updates",
            "source": "GitHub Changelog",
            "title": "GitHub Copilot adds a new coding agent",
            "url": "https://example.com/copilot",
        }
        self.assertTrue(is_ai_related_record(rec))

    def test_accepts_robotics_keyword(self):
        rec = {
            "site_id": "test_source",
            "site_name": "Test Source",
            "source": "technology",
            "title": "Embodied robotics gets new funding",
            "url": "https://example.com/robotics",
        }
        self.assertTrue(is_ai_related_record(rec))

    def test_rejects_noise_topic(self):
        rec = {
            "site_id": "test_source",
            "site_name": "Test Source",
            "source": "微博热搜",
            "title": "明星八卦今日热搜",
            "url": "https://example.com/noise",
        }
        self.assertFalse(is_ai_related_record(rec))

    def test_rejects_commerce_noise(self):
        rec = {
            "site_id": "test_source",
            "site_name": "Test Source",
            "source": "淘宝 ‧ 天猫 · 热销总榜",
            "title": "白象拌面任选加码 券后¥29.96",
            "url": "https://example.com/shop",
        }
        self.assertFalse(is_ai_related_record(rec))

    def test_v2ex_domain_excluded_for_any_source(self):
        # The URL-host exclusion is independent of source identity.
        rec = {
            "site_id": "test_source",
            "site_name": "Test Source",
            "source": "V2EX (创意工作者社区)",
            "title": "[分享創造] 用 AI 給我基於真的終端搓了個假的終端",
            "url": "https://www.v2ex.com/t/1228366",
        }
        self.assertFalse(is_ai_related_record(rec))

    def test_v2ex_domain_exclusion_is_host_anchored_not_a_substring_match(self):
        # A URL host that merely contains "v2ex.com" as a substring (not the
        # actual domain or a subdomain of it) must not be excluded.
        rec = {
            "site_id": "test_source",
            "site_name": "Test Source",
            "source": "Test Source",
            "title": "OpenAI releases new GPT model",
            "url": "https://not-v2ex.com.example.net/article",
        }
        self.assertTrue(is_ai_related_record(rec))

    def test_v2ex_subdomain_also_excluded(self):
        rec = {
            "site_id": "test_source",
            "site_name": "Test Source",
            "source": "Test Source",
            "title": "OpenAI releases new GPT model",
            "url": "https://www.v2ex.com/go/ai",
        }
        self.assertFalse(is_ai_related_record(rec))

    def test_v2ex_exclusion_does_not_affect_other_content(self):
        rec = {
            "site_id": "test_source",
            "site_name": "Test Source",
            "source": "Test Source",
            "title": "OpenAI releases new GPT model",
            "url": "https://example.com/openai-gpt-model",
        }
        self.assertTrue(is_ai_related_record(rec))

    def test_fix_mojibake(self):
        raw = "è°å¨ç¼åä»£ç "
        self.assertEqual(maybe_fix_mojibake(raw), "谁在编写代码")

    def test_parse_feed_entries_via_xml(self):
        xml = b"""<?xml version='1.0' encoding='UTF-8'?>
<rss><channel>
<item><title>A</title><link>https://x/a</link><pubDate>2026-02-20</pubDate></item>
</channel></rss>"""
        items = parse_feed_entries_via_xml(xml)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "A")

    def test_parse_atom_feed_entries_via_xml(self):
        xml = b"""<?xml version='1.0' encoding='UTF-8'?>
<feed xmlns="http://www.w3.org/2005/Atom">
<entry><title>A</title><link href="https://x/a" /><updated>2026-02-20</updated></entry>
</feed>"""
        items = parse_feed_entries_via_xml(xml)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "A")
        self.assertEqual(items[0]["link"], "https://x/a")

    def test_parse_anthropic_news_items(self):
        html = """
        <a href="/news/claude-opus-4-7">
          <time>Apr 16, 2026</time>
          <h2>Introducing Claude Opus 4.7</h2>
        </a>
        <a href="/news">News</a>
        """
        items = parse_anthropic_news_items(html, now=None)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].source, "Anthropic News")
        self.assertEqual(items[0].title, "Introducing Claude Opus 4.7")
        self.assertEqual(items[0].url, "https://www.anthropic.com/news/claude-opus-4-7")

    def test_parse_tencent_newsroom_items(self):
        html = """
        <article class="tc-blog-grid">
          <h2 class="blog-title">
            <a href="/tencent-releases-and-open-sources-tencent-hy4-preview/">
              Tencent Releases and Open-Sources Tencent Hy4 preview
            </a>
          </h2>
          <div class="tc-blogpost-date card-text entry-meta">August 28, 2026</div>
        </article>
        <article class="tc-blog-grid">
          <h2 class="blog-title"><a href="/stale/">Older Tencent post</a></h2>
          <div class="tc-blogpost-date">May 1, 2026</div>
        </article>
        """
        now = datetime(2026, 8, 31, tzinfo=timezone.utc)
        items = parse_tencent_newsroom_items(html, now)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].source, "Tencent Newsroom")
        self.assertEqual(items[0].title, "Tencent Releases and Open-Sources Tencent Hy4 preview")
        self.assertEqual(items[0].url, "https://www.tencent.com/tencent-releases-and-open-sources-tencent-hy4-preview/")
        self.assertEqual(items[0].meta, {"provider": "Tencent"})

    def test_parse_openai_codex_changelog_items(self):
        html = """
        <div id="codex-changelog-content">
          <li id="codex-2026-05-01">
            <time>2026-05-01</time>
            <h3><span>Codex app adds workspace companions</span></h3>
          </li>
        </div>
        """
        items = parse_openai_codex_changelog_items(html, now=None)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].source, "OpenAI Codex Changelog")
        self.assertEqual(items[0].title, "Codex app adds workspace companions")
        self.assertEqual(items[0].url, "https://developers.openai.com/codex/changelog#codex-2026-05-01")

    def test_bilingual_fields_preserve_source_provided_title_pair_and_summary(self):
        class NoNetworkSession:
            def get(self, *args, **kwargs):
                raise AssertionError("source-provided bilingual titles must not be translated again")

        item = {
            "title": "Codex 加入 ChatGPT 桌面应用",
            "provided_title_zh": "Codex 加入 ChatGPT 桌面应用",
            "provided_title_en": "Codex joins the ChatGPT desktop app",
            "summary": "中文编辑摘要",
            "url": "https://example.com/codex",
        }
        ai_items, _, _ = add_bilingual_fields([item], [item], NoNetworkSession(), {}, 80)
        self.assertEqual(ai_items[0]["title_zh"], "Codex 加入 ChatGPT 桌面應用")
        self.assertEqual(ai_items[0]["title_en"], "Codex joins the ChatGPT desktop app")
        self.assertEqual(ai_items[0]["title_original"], "Codex joins the ChatGPT desktop app")
        self.assertEqual(ai_items[0]["summary"], "中文编辑摘要")
        self.assertNotIn("provided_title_en", ai_items[0])

        pseudo_english = {
            "title": "如何在低配置电脑运行 GLM-5.2",
            "provided_title_zh": "如何在低配置电脑运行 GLM-5.2",
            "provided_title_en": "Show HN：如何在我的低配置电脑上运行 GLM-5.2",
            "url": "https://example.com/glm",
        }
        pseudo_items, _, _ = add_bilingual_fields([pseudo_english], [pseudo_english], NoNetworkSession(), {}, 80)
        self.assertIsNone(pseudo_items[0]["title_en"])
        self.assertEqual(pseudo_items[0]["title_zh"], "如何在低配置电脑运行 GLM-5.2")

    def test_bilingual_fields_translates_english_rss_summary_but_preserves_native_traditional(self):
        class FakeResponse:
            def __init__(self, payload):
                self.payload = payload

            def raise_for_status(self):
                return None

            def json(self):
                return self.payload

        class FakeSession:
            def __init__(self):
                self.queries = []

            def post(self, _url, json=None, **_kwargs):
                items = __import__("json").loads(json["contents"][0]["parts"][0]["text"])["items"]
                self.queries.extend(item["text"] for item in items)
                return FakeResponse(
                    {
                        "candidates": [{"content": {"role": "model", "parts": [{"text": __import__("json").dumps({"translations": [{"id": items[0]["id"], "text": "AI 出現在近四成美國選舉中，資料中心對電力成本的影響是主要討論焦點。"}]}, ensure_ascii=False)}]}}],
                    }
                )

        session = FakeSession()
        english = {
            "title": "已翻譯標題",
            "summary": "AI shows up in nearly 40 percent of all US races.",
            "url": "https://example.com/english-rss",
        }
        traditional = {
            "title": "原生繁體標題",
            "summary": "Dynatrace將以9.15億美元併購Arize，交易預計於今年完成。",
            "url": "https://example.com/traditional-rss",
        }

        ai_items, _, cache = add_bilingual_fields(
            [english, traditional],
            [english, traditional],
            session,
            {},
            2,
            gemini_api_key="test-key",
        )

        self.assertEqual(len(session.queries), 1)
        self.assertEqual(ai_items[0]["summary_zh"], "AI 出現在近四成美國選舉中，資料中心對電力成本的影響是主要討論焦點。")
        self.assertEqual(ai_items[1]["summary_zh"], traditional["summary"])
        self.assertIn("summary::AI shows up in nearly 40 percent of all US races.", cache)

    def test_repairs_recurring_ai_title_translation_errors(self):
        self.assertEqual(
            repair_zh_title_translation("Codex CLI 0.144.0", "法典 CLI 0.144.0"),
            "Codex CLI 0.144.0",
        )
        self.assertEqual(
            repair_zh_title_translation("GPT-5.5 Bio Bug Bounty", "GPT-5.5 生物错误赏金"),
            "GPT-5.5 生物安全漏洞悬赏",
        )
        self.assertEqual(
            repair_zh_title_translation(
                "Top mathematicians say LLMs are strong calculators",
                "頂級數學家表示法學碩士的計算能力很強",
            ),
            "頂級數學家表示LLMs的計算能力很強",
        )

    def test_brand_glossary_relabels_morning_squawk_left_untranslated_by_mt(self):
        self.assertEqual(
            repair_zh_title_translation(
                "Grocery sales, United earnings, Anthropic's IPO prep and more in Morning Squawk",
                "Morning Squawk 中的杂货销售、美联航盈利、Anthropic 的 IPO 准备等更多内容",
            ),
            "晨間快評(Morning Squawk) 中的杂货销售、美联航盈利、Anthropic 的 IPO 准备等更多内容",
        )

    def test_brand_glossary_appends_when_term_missing_from_translated_result(self):
        self.assertEqual(
            repair_zh_title_translation("Morning Squawk: markets open lower", "市场开盘走低"),
            "市场开盘走低 晨間快評(Morning Squawk)",
        )

    def test_morning_squawk_repair_is_idempotent_and_cleans_nested_cache_value(self):
        original = "The Treasury's debt buyback and more in Morning Squawk"
        nested = "晨間快評(晨間快評(晨間快評(Morning Squawk))) 中的財政部債務回購"

        cleaned = repair_zh_title_translation(original, nested)

        self.assertEqual(cleaned, "晨間快評(Morning Squawk) 中的財政部債務回購")
        self.assertEqual(repair_zh_title_translation(original, cleaned), cleaned)

    def test_brand_glossary_leaves_unrelated_titles_untouched(self):
        self.assertEqual(
            repair_zh_title_translation("OpenAI releases new GPT model", "OpenAI 发布新的 GPT 模型"),
            "OpenAI 发布新的 GPT 模型",
        )

    def test_openai_canon_mistranslation_is_repaired_only_for_openai_source(self):
        self.assertEqual(
            repair_zh_title_translation(
                "OpenAI launches Astra, its powerful (and controversial) new model",
                "佳能推出其功能強大（且備受爭議）的新機型 Astra OpenAI",
            ),
            "OpenAI推出其功能強大（且備受爭議）的新機型 Astra",
        )

        # Canon is the Japanese company's proper name and must remain 佳能.
        self.assertEqual(
            repair_zh_title_translation(
                "Canon announces a new camera partnership",
                "佳能宣布建立新的相機合作關係",
            ),
            "佳能宣布建立新的相機合作關係",
        )

    def test_canon_proper_name_masks_but_lowercase_canon_remains_a_common_noun(self):
        masked, placeholders = mask_canonical_names("Canon launches a camera with AI features")
        self.assertNotIn("Canon", masked)
        self.assertEqual(set(placeholders.values()), {"佳能"})

        uppercase_masked, uppercase_placeholders = mask_canonical_names("CANON launches a camera")
        self.assertNotIn("CANON", uppercase_masked)
        self.assertEqual(set(uppercase_placeholders.values()), {"佳能"})

        lowercase_masked, lowercase_placeholders = mask_canonical_names("The film canon expands")
        self.assertEqual(lowercase_masked, "The film canon expands")
        self.assertEqual(lowercase_placeholders, {})

    # --- CANONICAL_NAMES: 出口修正 (exit-fix) ---------------------------

    def test_canonical_names_mixed_vendor_and_family_rendering(self):
        result = repair_zh_title_translation(
            "NVIDIA unveils Nemotron models for enterprise customers",
            "NVIDIA 推出面向企业客户的 Nemotron 模型",
        )
        self.assertIn("輝達", result)
        self.assertIn("Nemotron", result)
        self.assertNotIn("NVIDIA", result)

    def test_canonical_names_moonshot_ai_compound_always_converts(self):
        result = repair_zh_title_translation(
            "Moonshot AI launches Kimi K2 update",
            "Moonshot AI 推出 Kimi K2 更新",
        )
        self.assertIn("月之暗面", result)
        self.assertNotIn("Moonshot AI", result)

    def test_canonical_names_bare_moonshot_requires_ai_lab_context(self):
        with_context = repair_zh_title_translation(
            "Moonshot doubles down on Kimi's agent roadmap",
            "Moonshot 加倍投入 Kimi 的智能体路线图",
        )
        self.assertIn("月之暗面", with_context)

        without_context = repair_zh_title_translation(
            "Moonshot mission control approves next launch window",
            "Moonshot 任务控制中心批准下一个发射窗口",
        )
        self.assertNotIn("月之暗面", without_context)
        self.assertIn("Moonshot", without_context)

    def test_canonical_names_case_sensitive_false_positive_guards(self):
        lowercase_grok = repair_zh_title_translation(
            "Users grok the new onboarding flow quickly",
            "用户很快就 grok 了新的引导流程",
        )
        self.assertNotIn("Grok", lowercase_grok)

        lowercase_moonshot_with_lab_context = repair_zh_title_translation(
            "a moonshot bet by OpenAI on AGI safety",
            "OpenAI 押注 AGI 安全的一次 moonshot 豪赌",
        )
        self.assertNotIn("月之暗面", lowercase_moonshot_with_lab_context)

    # --- CANONICAL_NAMES: 反向修正 (reverse-fix, Table C) ----------------

    def test_canonical_reverse_fix_regresses_claude_fable_mistranslation(self):
        traditional = apply_canonical_reverse_fix("《克勞德寓言5》正式發表,不再只是模型代號")
        self.assertNotIn("克勞德", traditional)
        self.assertNotIn("寓言", traditional)
        self.assertNotIn("《", traditional)
        self.assertNotIn("》", traditional)
        self.assertIn("Claude Fable 5", traditional)

        simplified_cache_residual = apply_canonical_reverse_fix("《克劳德寓言5》正式发表")
        self.assertNotIn("克劳德", simplified_cache_residual)
        self.assertNotIn("寓言", simplified_cache_residual)
        self.assertIn("Claude Fable 5", simplified_cache_residual)

    def test_canonical_reverse_fix_prc_vendor_terms_to_taiwan_canonical(self):
        result = apply_canonical_reverse_fix("谷歌与英偉達同场竞技,英伟达股价大涨")
        self.assertNotIn("谷歌", result)
        self.assertNotIn("英偉達", result)
        self.assertNotIn("英伟达", result)
        self.assertIn("Google", result)
        self.assertEqual(result.count("輝達"), 2)

    def test_canonical_reverse_fix_bare_claude_without_subbrand(self):
        self.assertEqual(apply_canonical_reverse_fix("克勞德發布最新安全報告"), "Claude發布最新安全報告")

    def test_canonical_reverse_fix_leaves_unrelated_text_untouched(self):
        self.assertEqual(apply_canonical_reverse_fix("OpenAI 發布新的 GPT 模型"), "OpenAI 發布新的 GPT 模型")

    # --- 快取殘留 repair 掛載點：每次執行皆對快取值重新套用 exit-fix/
    # reverse-fix,但只有 exit-fix 的輸出會回寫快取（沿用既有「不改寫歷史」
    # 規則);reverse-fix 只作用於顯示值,不回寫快取。--------------------

    def test_cached_bad_translation_is_repaired_at_display_time_every_run(self):
        class NoNetworkSession:
            def get(self, *args, **kwargs):
                raise AssertionError("cache hit must not trigger a network translate call")

        title = "Claude Fable 5 launches new safety benchmark"
        cache = {title: "《克劳德寓言5》发布新的安全基准"}
        item = {"title": title, "url": "https://example.com/claude-fable-5"}

        ai_items, _, returned_cache = add_bilingual_fields([item], [item], NoNetworkSession(), cache, 80)

        title_zh = ai_items[0]["title_zh"]
        self.assertNotIn("克劳德", title_zh)
        self.assertNotIn("寓言", title_zh)
        self.assertIn("Claude Fable 5", title_zh)
        # Table C reverse-fix is display-only; the cached raw value (no
        # CANONICAL_NAMES Table A/B term for exit-fix to match on) is left
        # as-is, matching the pre-existing "don't rewrite history" rule.
        self.assertEqual(returned_cache[title], "《克劳德寓言5》发布新的安全基准")

    def test_cached_llm_degree_mistranslation_is_repaired_and_rewritten(self):
        class NoNetworkSession:
            def get(self, *args, **kwargs):
                raise AssertionError("cache hit must not trigger a network translate call")

        title = "The LLM Critics Are Right. I Use LLMs Anyway"
        cache = {title: "法学硕士的批评是正确的。我无论如何都使用法学硕士。"}
        item = {"title": title, "url": "https://example.com/llm-cache"}

        ai_items, _, returned_cache = add_bilingual_fields([item], [item], NoNetworkSession(), cache, 80)

        self.assertNotIn("法學碩士", ai_items[0]["title_zh"])
        self.assertIn("LLMs", ai_items[0]["title_zh"])
        self.assertNotIn("法学硕士", returned_cache[title])
        self.assertIn("LLMs", returned_cache[title])

    def test_cached_openai_canon_mistranslation_is_repaired_and_rewritten(self):
        class NoNetworkSession:
            def get(self, *args, **kwargs):
                raise AssertionError("cache hit must not trigger a network translate call")

        title = "OpenAI launches Astra, its powerful (and controversial) new model"
        cache = {title: "佳能推出其功能強大（且備受爭議）的新機型 Astra OpenAI"}
        item = {"title": title, "url": "https://example.com/openai-astra"}

        ai_items, _, returned_cache = add_bilingual_fields([item], [item], NoNetworkSession(), cache, 80)

        self.assertNotIn("佳能", ai_items[0]["title_zh"])
        self.assertIn("OpenAI", ai_items[0]["title_zh"])
        self.assertNotIn("佳能", returned_cache[title])
        self.assertIn("OpenAI", returned_cache[title])

    def test_openai_legacy_cache_repair_does_not_override_a_real_canon_reference(self):
        source = "OpenAI and Canon announce an AI camera partnership"
        translated = "佳能與佳能宣布 AI 相機合作 OpenAI"

        self.assertEqual(repair_zh_title_translation(source, translated), translated)

    def test_cached_openai_canon_mistranslation_is_repaired_in_rss_summary(self):
        class NoNetworkSession:
            def get(self, *args, **kwargs):
                raise AssertionError("cache hit must not trigger a network translate call")

        summary = "OpenAI says Astra sets a new frontier for computer use."
        cache_key = f"summary::{summary}"
        cache = {cache_key: "佳能表示 Astra 為電腦使用開啟新領域。"}
        item = {"title": "Astra 摘要", "summary": summary, "url": "https://example.com/openai-astra"}

        ai_items, _, returned_cache = add_bilingual_fields([item], [item], NoNetworkSession(), cache, 80)

        self.assertNotIn("佳能", ai_items[0]["summary_zh"])
        self.assertIn("OpenAI", ai_items[0]["summary_zh"])
        self.assertNotIn("佳能", returned_cache[cache_key])
        self.assertIn("OpenAI", returned_cache[cache_key])

    # --- CANONICAL_NAMES Step 2: 遮罩回填 (mask-and-backfill) ------------

    def test_mask_canonical_names_masks_vendor_and_family_hits(self):
        masked, placeholders = mask_canonical_names(
            "NVIDIA unveils Nemotron models for enterprise customers"
        )
        self.assertNotIn("NVIDIA", masked)
        self.assertNotIn("Nemotron", masked)
        self.assertEqual(len(placeholders), 2)
        self.assertEqual(set(placeholders.values()), {"輝達", "Nemotron"})

    def test_mask_canonical_names_preserves_llm_acronyms(self):
        masked, placeholders = mask_canonical_names("LLMs improve when an LLM has better context")
        self.assertNotIn("LLM", masked)
        self.assertEqual(set(placeholders.values()), {"LLMs", "LLM"})

    def test_mask_canonical_names_swallows_claude_subbrand_and_version_as_one_span(self):
        masked, placeholders = mask_canonical_names("Claude Fable 5 launches new safety benchmark")
        self.assertNotIn("Claude", masked)
        self.assertEqual(len(placeholders), 1)
        self.assertEqual(list(placeholders.values()), ["Claude Fable 5"])

    def test_mask_canonical_names_gates_high_risk_bare_terms_on_vendor_context(self):
        with_context, ph_with = mask_canonical_names("Amazon reveals Nova voice assistant upgrade")
        self.assertNotIn("Nova", with_context)
        self.assertIn("Nova", ph_with.values())

        without_context, ph_without = mask_canonical_names("Startup unveils Nova voice assistant upgrade")
        self.assertIn("Nova", without_context)
        self.assertEqual(ph_without, {})

    def test_mask_canonical_names_gates_bare_moonshot_on_ai_lab_context(self):
        with_context, ph_with = mask_canonical_names("Moonshot doubles down on Kimi's agent roadmap")
        self.assertNotIn("Moonshot", with_context)
        self.assertIn("月之暗面", ph_with.values())

        without_context, ph_without = mask_canonical_names(
            "Moonshot mission control approves next launch window"
        )
        self.assertIn("Moonshot", without_context)
        self.assertEqual(ph_without, {})

    def test_backfill_canonical_names_restores_untouched_placeholders(self):
        masked, placeholders = mask_canonical_names("Alibaba's Qwen team open-sources QwQ reasoning model")
        # Simulate MT translating the surrounding English but leaving the
        # opaque placeholder tokens untouched (the same MT behavior the old
        # BRAND_GLOSSARY comment already documented for short proper nouns).
        fake_translated = masked.replace("open-sources", "开源了").replace("reasoning model", "推理模型")
        result = backfill_canonical_names(fake_translated, placeholders)
        self.assertNotIn("ZXQ", result)
        self.assertIn("阿里巴巴", result)
        self.assertIn("Qwen", result)
        self.assertIn("QwQ", result)

    def test_backfill_canonical_names_never_leaks_a_dropped_placeholder(self):
        masked, placeholders = mask_canonical_names("NVIDIA unveils Nemotron models")
        token = next(iter(placeholders))
        mt_dropped_token = masked.replace(token, "")
        result = backfill_canonical_names(mt_dropped_token, placeholders)
        self.assertNotIn("ZXQ", result)
        self.assertIn(placeholders[token], result)

    def test_backfill_canonical_names_never_leaks_a_mangled_placeholder(self):
        masked, placeholders = mask_canonical_names("NVIDIA unveils Nemotron models")
        token = next(iter(placeholders))
        mt_mangled = masked.replace(token, "xyz-garbled-123")
        result = backfill_canonical_names(mt_mangled, placeholders)
        self.assertNotIn("ZXQ", result)

    def test_add_bilingual_fields_masks_before_network_call_and_backfills_arbitrary_combo(self):
        class FakeResponse:
            def __init__(self, payload):
                self.payload = payload

            def raise_for_status(self):
                return None

            def json(self):
                return self.payload

        class FakeSession:
            def __init__(self):
                self.queries = []

            def post(self, _url, json=None, **_kwargs):
                items = __import__("json").loads(json["contents"][0]["parts"][0]["text"])["items"]
                self.queries.extend(item["text"] for item in items)
                translated = [
                    item["text"].replace("unveils", "推出").replace(
                        "models for enterprise customers", "面向企业客户的模型"
                    )
                    for item in items
                ]
                return FakeResponse(
                    {"candidates": [{"content": {"role": "model", "parts": [{"text": __import__("json").dumps({"translations": [{"id": item["id"], "text": text} for item, text in zip(items, translated)]}, ensure_ascii=False)}]}}]}
                )

        session = FakeSession()
        item = {
            "title": "NVIDIA unveils Nemotron models for enterprise customers",
            "url": "https://example.com/nvidia-nemotron",
        }
        ai_items, _, _ = add_bilingual_fields([item], [item], session, {}, 80, gemini_api_key="test-key")

        # The network call must never have seen the raw brand tokens at all.
        self.assertTrue(session.queries)
        self.assertNotIn("NVIDIA", session.queries[0])
        self.assertNotIn("Nemotron", session.queries[0])
        self.assertNotIn("CANON", session.queries[0])

        title_zh = ai_items[0]["title_zh"]
        self.assertIn("輝達", title_zh)
        self.assertIn("Nemotron", title_zh)
        self.assertNotIn("ZXQ", title_zh)

    def test_add_bilingual_fields_placeholder_never_leaks_when_mt_drops_it(self):
        class FakeResponse:
            def __init__(self, payload):
                self.payload = payload

            def raise_for_status(self):
                return None

            def json(self):
                return self.payload

        class FakeSession:
            def post(self, _url, json=None, **_kwargs):
                item = __import__("json").loads(json["contents"][0]["parts"][0]["text"])["items"][0]
                q = item["text"]
                # Simulate MT dropping the opaque placeholder token entirely
                # while still translating the surrounding English.
                translated = re.sub(r"ZXQ\d+QXZ", "", q).replace("unveils", "推出").strip()
                return FakeResponse({"candidates": [{"content": {"role": "model", "parts": [{"text": __import__("json").dumps({"translations": [{"id": item["id"], "text": translated}]}, ensure_ascii=False)}]}}]})

        item = {
            "title": "NVIDIA unveils a new chip",
            "url": "https://example.com/nvidia-chip",
        }
        ai_items, _, _ = add_bilingual_fields([item], [item], FakeSession(), {}, 80, gemini_api_key="test-key")

        self.assertIsNone(ai_items[0]["title_zh"])

    # --- CANONICAL_NAMES Step 3: 非相鄰共現防護 ---------------------------

    def test_mask_canonical_names_masks_non_adjacent_claude_and_subbrand_separately(self):
        masked, placeholders = mask_canonical_names("Claude make Fable 5 permanent")
        self.assertNotIn("Claude", masked)
        self.assertNotIn("Fable", masked)
        self.assertEqual(len(placeholders), 2)
        self.assertEqual(set(placeholders.values()), {"Claude", "Fable 5"})

    def test_mask_canonical_names_adjacent_claude_subbrand_still_one_placeholder(self):
        # Regression: the Step 3 non-adjacent pass must not double-mask the
        # already-adjacent case handled by _MASK_SCAN_RE.
        masked, placeholders = mask_canonical_names("Claude Fable 5 launches new safety benchmark")
        self.assertEqual(len(placeholders), 1)
        self.assertEqual(list(placeholders.values()), ["Claude Fable 5"])

    def test_mask_canonical_names_does_not_mask_subbrand_word_with_no_ai_context_at_all(self):
        # True negative: no other CANONICAL_NAMES entity anywhere in the
        # title (as opposed to the Step 4 case below, where a co-occurring
        # entity like GPT-5.6 now DOES protect the isolated sub-brand word).
        masked, placeholders = mask_canonical_names(
            "Fable 5 review: is it worth the hype on an NP-Hard Problem?"
        )
        self.assertIn("Fable", masked)
        self.assertEqual(placeholders, {})

    def test_reverse_fix_repairs_non_adjacent_claude_subbrand_mistranslation(self):
        # Exact cache residual observed on the live site for "Claude make
        # Fable 5 permanent": Claude and its mistranslated sub-brand word
        # are in the same sentence but not adjacent.
        result = apply_canonical_reverse_fix("克劳德将《神鬼寓言5》永久化")
        self.assertNotIn("克劳德", result)
        self.assertNotIn("寓言", result)
        self.assertNotIn("神鬼", result)
        self.assertNotIn("《", result)
        self.assertIn("Claude", result)
        self.assertIn("Fable 5", result)

    def test_reverse_fix_non_adjacent_mythos_with_claude_context_elsewhere(self):
        result = apply_canonical_reverse_fix(
            "Anthropic 声称其新人工智能模型、神话是网络安全的清算"
        )
        self.assertNotIn("神话", result)
        self.assertIn("Mythos", result)

    def test_reverse_fix_uses_english_source_when_translation_drops_anthropic(self):
        # MT sometimes renders "Anthropic" as "人类"/"人择" instead of
        # keeping it literal, so the in-text context check alone would miss
        # it; the English source (when available) is a second signal.
        result = apply_canonical_reverse_fix(
            "尽管列入黑名单，美国国家安全局仍利用人类的神话",
            source="NSA Using Anthropic's Mythos Despite Blacklist",
        )
        self.assertNotIn("神话", result)
        self.assertIn("Mythos", result)

    def test_reverse_fix_leaves_unrelated_game_and_generic_word_usage_untouched(self):
        # False-positive guard (spec item 2): a real "Fable" game-franchise
        # headline, and generic "myth"/"masterpiece" vocabulary, must not be
        # rewritten when there is no Claude/Anthropic context at all.
        self.assertEqual(apply_canonical_reverse_fix("Xbox 公布《神鬼寓言》新作"), "Xbox 公布《神鬼寓言》新作")
        self.assertEqual(apply_canonical_reverse_fix("這是一部曠世傑作"), "這是一部曠世傑作")
        self.assertEqual(
            apply_canonical_reverse_fix("打破人工智慧經濟的最大神話"),
            "打破人工智慧經濟的最大神話",
        )

    def test_end_to_end_cached_non_adjacent_claude_fable_bug_self_heals(self):
        # The exact live regression this Step 3 ticket was opened for.
        class NoNetworkSession:
            def get(self, *args, **kwargs):
                raise AssertionError("cache hit must not trigger a network translate call")

        title = "Claude make Fable 5 permanent"
        cache = {title: "克劳德将《神鬼寓言5》永久化"}
        item = {"title": title, "url": "https://simonwillison.net/2026/Jul/18/claude-make-fable-5-permanent"}

        ai_items, _, _ = add_bilingual_fields([item], [item], NoNetworkSession(), cache, 80)

        title_zh = ai_items[0]["title_zh"]
        self.assertNotIn("寓言", title_zh)
        self.assertNotIn("神鬼", title_zh)
        self.assertNotIn("《", title_zh)
        self.assertIn("Claude", title_zh)
        self.assertIn("Fable 5", title_zh)

    def test_end_to_end_fresh_translation_masks_non_adjacent_claude_and_fable(self):
        class FakeResponse:
            def __init__(self, payload):
                self.payload = payload

            def raise_for_status(self):
                return None

            def json(self):
                return self.payload

        class FakeSession:
            def __init__(self):
                self.queries = []

            def post(self, _url, json=None, **_kwargs):
                items = __import__("json").loads(json["contents"][0]["parts"][0]["text"])["items"]
                self.queries.extend(item["text"] for item in items)
                translated = [item["text"].replace("make", "讓").replace("permanent", "永久化") for item in items]
                return FakeResponse(
                    {"candidates": [{"content": {"role": "model", "parts": [{"text": __import__("json").dumps({"translations": [{"id": item["id"], "text": text} for item, text in zip(items, translated)]}, ensure_ascii=False)}]}}]}
                )

        session = FakeSession()
        item = {
            "title": "Claude make Fable 5 permanent",
            "url": "https://simonwillison.net/2026/Jul/18/claude-make-fable-5-permanent",
        }
        ai_items, _, _ = add_bilingual_fields([item], [item], session, {}, 80, gemini_api_key="test-key")

        self.assertTrue(session.queries)
        self.assertNotIn("Claude", session.queries[0])
        self.assertNotIn("Fable", session.queries[0])

        title_zh = ai_items[0]["title_zh"]
        self.assertNotIn("寓言", title_zh)
        self.assertNotIn("《", title_zh)
        self.assertIn("Claude", title_zh)
        self.assertIn("Fable 5", title_zh)

    # --- CANONICAL_NAMES Step 4: 子系詞獨立出現防護 -------------------------

    def test_mask_canonical_names_protects_isolated_subbrand_with_other_entity_context(self):
        masked, placeholders = mask_canonical_names(
            "Moonshot's Kimi K3 outperforms Fable 5 in frontend code but lags far behind in complex math"
        )
        self.assertNotIn("Moonshot", masked)
        self.assertNotIn("Kimi", masked)
        self.assertNotIn("Fable", masked)
        self.assertEqual(set(placeholders.values()), {"月之暗面的", "Kimi", "Fable 5"})

    def test_mask_canonical_names_protects_isolated_subbrand_generalized_case(self):
        masked, placeholders = mask_canonical_names("Opus 4.8 tops coding benchmark against GPT-5.6")
        self.assertNotIn("Opus", masked)
        self.assertIn("Opus 4.8", placeholders.values())

    def test_mask_canonical_names_isolated_subbrand_excludes_generalist_conglomerates(self):
        masked, placeholders = mask_canonical_names("Microsoft sets Fable release date")
        self.assertIn("Fable", masked)
        # Microsoft itself still masks normally - only the co-occurrence
        # check for the *sub-brand word* excludes conglomerate entities.
        self.assertEqual(set(placeholders.values()), {"微軟"})

    def test_mask_canonical_names_isolated_subbrand_requires_a_version_tail(self):
        masked, placeholders = mask_canonical_names("Kimi and Fable are both popular names")
        self.assertIn("Fable", masked)
        self.assertEqual(set(placeholders.values()), {"Kimi"})

    def test_mask_canonical_names_possessive_suffix_never_leaks_onto_backfill(self):
        masked, placeholders = mask_canonical_names("Moonshot's Kimi K3 announcement")
        self.assertNotIn("'s", masked)
        self.assertIn("月之暗面的", placeholders.values())

    def test_reverse_fix_widened_gate_repairs_isolated_fable_with_other_entity(self):
        # Exact cache residual observed on the live site for "Moonshot's
        # Kimi K3 outperforms Fable 5..." - no Claude/Anthropic text
        # anywhere, but Kimi/Moonshot establish AI-industry context.
        cached = "月之暗面 的 Kimi K3 在前端代码方面优于《神鬼寓言 5》，但在复杂数学方面远远落后"
        result = apply_canonical_reverse_fix(cached)
        self.assertNotIn("寓言", result)
        self.assertNotIn("神鬼", result)
        self.assertNotIn("《", result)
        self.assertIn("Fable 5", result)
        self.assertIn("Kimi K3", result)

    def test_reverse_fix_widened_gate_still_requires_narrow_gate_for_other_subbrand_words(self):
        # 神話("myth")/傑作("masterpiece") keep the narrow Claude/Anthropic-
        # only gate even under Step 4 - widening to any entity would be far
        # too permissive for such common everyday vocabulary.
        result = apply_canonical_reverse_fix("Kimi K3 是一部曠世傑作")
        self.assertEqual(result, "Kimi K3 是一部曠世傑作")

    def test_reverse_fix_widened_gate_leaves_unrelated_game_news_untouched(self):
        self.assertEqual(apply_canonical_reverse_fix("Xbox 公布神鬼寓言新作"), "Xbox 公布神鬼寓言新作")

    def test_end_to_end_cached_isolated_fable_bug_self_heals(self):
        class NoNetworkSession:
            def get(self, *args, **kwargs):
                raise AssertionError("cache hit must not trigger a network translate call")

        title = "Moonshot's Kimi K3 outperforms Fable 5 in frontend code but lags far behind in complex math"
        cache = {title: "月之暗面 的 Kimi K3 在前端代码方面优于《神鬼寓言 5》，但在复杂数学方面远远落后"}
        item = {"title": title, "url": "https://example.com/moonshot-kimi-k3-vs-fable-5"}

        ai_items, _, _ = add_bilingual_fields([item], [item], NoNetworkSession(), cache, 80)

        title_zh = ai_items[0]["title_zh"]
        self.assertNotIn("寓言", title_zh)
        self.assertNotIn("《", title_zh)
        self.assertIn("Fable 5", title_zh)

    def test_end_to_end_fresh_translation_masks_isolated_kimi_and_fable(self):
        class FakeResponse:
            def __init__(self, payload):
                self.payload = payload

            def raise_for_status(self):
                return None

            def json(self):
                return self.payload

        class FakeSession:
            def __init__(self):
                self.queries = []

            def post(self, _url, json=None, **_kwargs):
                items = __import__("json").loads(json["contents"][0]["parts"][0]["text"])["items"]
                self.queries.extend(item["text"] for item in items)
                translated = [
                    item["text"].replace("outperforms", "表现优于").replace(
                        "in frontend code but lags far behind in complex math", "在前端代码方面，但在复杂数学方面远远落后"
                    )
                    for item in items
                ]
                return FakeResponse(
                    {"candidates": [{"content": {"role": "model", "parts": [{"text": __import__("json").dumps({"translations": [{"id": item["id"], "text": text} for item, text in zip(items, translated)]}, ensure_ascii=False)}]}}]}
                )

        session = FakeSession()
        item = {
            "title": "Moonshot's Kimi K3 outperforms Fable 5 in frontend code but lags far behind in complex math",
            "url": "https://example.com/moonshot-kimi-k3-vs-fable-5-fresh",
        }
        ai_items, _, _ = add_bilingual_fields([item], [item], session, {}, 80, gemini_api_key="test-key")

        self.assertTrue(session.queries)
        self.assertNotIn("Moonshot", session.queries[0])
        self.assertNotIn("Kimi", session.queries[0])
        self.assertNotIn("Fable", session.queries[0])

        title_zh = ai_items[0]["title_zh"]
        self.assertNotIn("寓言", title_zh)
        self.assertNotIn("《", title_zh)
        self.assertIn("月之暗面的", title_zh)
        self.assertIn("Kimi", title_zh)
        self.assertIn("Fable 5", title_zh)

    def test_parse_curated_media_feed_applies_strict_title_filter_and_cap(self):
        xml = """<?xml version='1.0' encoding='UTF-8'?>
<rss><channel><title>The Verge</title>
<item>
<title>OpenAI launches a new ChatGPT product</title>
<link>https://www.theverge.com/ai-product</link>
<pubDate>Mon, 15 Jun 2026 02:05:04 GMT</pubDate>
</item>
<item>
<title>A phone accessory launches this week</title>
<link>https://www.theverge.com/phone</link>
<pubDate>Mon, 15 Jun 2026 03:05:04 GMT</pubDate>
</item>
</channel></rss>""".encode("utf-8")
        feed = {
            "title": "The Verge",
            "xml_url": "https://www.theverge.com/rss/index.xml",
            "include_keywords": "openai,chatgpt,artificial intelligence",
            "strict_title_filter": True,
            "max_entries": 1,
        }
        items = parse_curated_ai_media_feed_items(xml, feed, now=parse_date_any("2026-06-16T00:00:00Z", None))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].site_id, "curated_media")
        self.assertEqual(items[0].source, "The Verge")
        self.assertIn("OpenAI", items[0].title)

    def test_dedupe_items_by_title_url_latest(self):
        items = [
            {
                "id": "1",
                "title": "Same",
                "title_original": "Same",
                "url": "https://example.com/a",
                "published_at": "2026-02-20T00:00:00Z",
            },
            {
                "id": "2",
                "title": "Same",
                "title_original": "Same",
                "url": "https://example.com/a",
                "published_at": "2026-02-20T01:00:00Z",
            },
        ]
        out = dedupe_items_by_title_url(items, random_pick=False)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["id"], "2")

    def test_rejects_broad_agent_noise_without_ai_context(self):
        rec = {
            "site_id": "test_source",
            "site_name": "Test Source",
            "source": "github.com",
            "title": "New travel agent marketplace launches in Europe",
            "url": "https://example.com/travel-agent",
        }
        self.assertFalse(is_ai_related_record(rec))

    def test_accepts_chinese_model_news_after_noise_tightening(self):
        rec = {
            "site_id": "test_source",
            "site_name": "Test Source",
            "source": "机器之心",
            "title": "新一代推理模型刷新多模态数学基准",
            "url": "https://example.com/reasoning-model",
        }
        self.assertTrue(is_ai_related_record(rec))

    def test_redacts_email_like_public_text(self):
        self.assertEqual(redact_public_text("Contact editor@example.com for access"), "Contact [redacted-email] for access")

    def test_build_latest_payloads_keeps_initial_payload_slim(self):
        latest_payload = {
            "generated_at": "2026-05-03T00:00:00Z",
            "window_hours": 24,
            "total_items": 1,
            "total_items_raw": 3,
            "total_items_all_mode": 2,
            "items_ai": [{"title": "AI post", "url": "https://example.com/a"}],
            "creator_items_ai": [{"title": "Hot creator post", "url": "https://example.com/hot"}],
            "items_all": [{"title": "All post", "url": "https://example.com/b"}],
            "items_all_raw": [{"title": "Raw post", "url": "https://example.com/c"}],
        }
        slim, all_payload = build_latest_payloads(latest_payload)
        self.assertIn("items_ai", slim)
        self.assertIn("creator_items_ai", slim)
        self.assertNotIn("items_all", slim)
        self.assertNotIn("items_all_raw", slim)
        self.assertEqual(slim["all_mode_data_url"], "data/latest-24h-all.json")
        self.assertEqual(slim["stories_data_url"], "data/stories-merged.json")
        self.assertEqual(all_payload["items_all"][0]["title"], "All post")
        self.assertEqual(all_payload["items_all_raw"][0]["title"], "Raw post")

    def test_source_tier_fields_and_sort_put_opml_after_core_sources(self):
        official = add_source_tier_fields(
            {
                "site_id": "official_ai",
                "site_name": "Official AI Updates",
                "source": "OpenAI News",
                "title": "OpenAI ships a model",
                "url": "https://example.com/openai",
                "published_at": "2026-05-03T00:00:00Z",
            }
        )
        opml = add_source_tier_fields(
            {
                "site_id": "opmlrss",
                "site_name": "OPML RSS",
                "source": "Reader feed",
                "title": "AI tool update",
                "url": "https://example.com/opml",
                "published_at": "2026-05-03T01:00:00Z",
            }
        )
        self.assertEqual(official["source_tier_label"], "官方一手源")
        self.assertEqual(opml["source_tier_label"], "RSS/OPML")
        self.assertLess(source_tier_sort_key(official), source_tier_sort_key(opml))

    def test_dedupe_prefers_core_source_over_newer_discussion_duplicate(self):
        official = add_source_tier_fields(
            {
                "id": "official",
                "site_id": "official_ai",
                "site_name": "Official AI Updates",
                "source": "OpenAI News",
                "title": "OpenAI ships a model",
                "url": "https://example.com/same",
                "published_at": "2026-05-03T00:00:00Z",
            }
        )
        discussion = add_source_tier_fields(
            {
                "id": "discussion",
                "site_id": "test_source",
                "site_name": "Test Source",
                "source": "Hacker News · 24h最热",
                "title": "OpenAI ships a model",
                "url": "https://example.com/same",
                "published_at": "2026-05-03T01:00:00Z",
            }
        )
        deduped = dedupe_items_by_title_url([discussion, official], random_pick=False)
        self.assertEqual(deduped[0]["id"], "official")

if __name__ == "__main__":
    unittest.main()
