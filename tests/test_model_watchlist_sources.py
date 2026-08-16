import json
import unittest
from datetime import datetime, timezone

from scripts.ai_relevance import score_ai_relevance
from scripts.update_news import (
    RUNTIMEWIRE_MODEL_FEED,
    build_model_releases_7d_items,
    business_event_score,
    extract_llm_stats_latest_models,
    parse_model_analysis_feed_items,
    source_tier_for_site,
    story_titles_can_merge,
)


NOW = datetime(2026, 8, 16, 6, 0, tzinfo=timezone.utc)


class LlmStatsModelReleaseTests(unittest.TestCase):
    def test_extracts_allowlisted_atomic_model_releases_from_escaped_payload(self):
        models = [
            {
                "model_id": "qwen3.8-27b",
                "name": "Qwen3.8-27B",
                "organization": "Alibaba Cloud / Qwen Team",
                "organization_id": "qwen",
                "release_date": "2026-08-14",
            },
            {
                "model_id": "grok-4.6",
                "name": "Grok 4.6",
                "organization": "xAI",
                "organization_id": "xai",
                "release_date": "2026-08-12",
            },
            {
                "model_id": "community-finetune",
                "name": "Community Fine-tune",
                "organization": "Unknown User",
                "organization_id": "unknown-user",
                "release_date": "2026-08-15",
            },
        ]
        escaped = json.dumps(models, separators=(",", ":")).replace('"', '\\"')
        html = f'<script>self.__next_f.push([1,"\\"latestModels\\":{escaped}"])</script>'

        items = extract_llm_stats_latest_models(html, NOW)

        self.assertEqual([item.meta["model_id"] for item in items], ["qwen3.8-27b", "grok-4.6"])
        self.assertEqual(items[0].url, "https://llm-stats.com/models/qwen3.8-27b")
        self.assertEqual(items[0].site_id, "llm_stats_models")
        self.assertEqual(business_event_score({"title": items[0].title}), ["model_release"])
        self.assertTrue(score_ai_relevance(items[0].__dict__)["is_ai_related"])

    def test_rejects_missing_latest_models_payload(self):
        with self.assertRaisesRegex(ValueError, "latestModels"):
            extract_llm_stats_latest_models("<html>no model payload</html>", NOW)

    def test_builds_seven_day_release_lane_without_faking_24h_timestamp(self):
        item = extract_llm_stats_latest_models(
            '"latestModels":[{"model_id":"qwen3.8-27b","name":"Qwen3.8-27B",'
            '"organization":"Alibaba Cloud / Qwen Team","organization_id":"qwen",'
            '"release_date":"2026-08-14"}]',
            NOW,
        )[0]
        archive = {
            "qwen": {
                "id": "qwen",
                "site_id": item.site_id,
                "site_name": item.site_name,
                "source": item.source,
                "title": item.title,
                "url": item.url,
                "published_at": item.published_at.isoformat(),
                "first_seen_at": NOW.isoformat(),
                **item.meta,
            }
        }

        weekly = build_model_releases_7d_items(archive, NOW)

        self.assertEqual(len(weekly), 1)
        self.assertEqual(weekly[0]["published_at"], "2026-08-14T00:00:00+00:00")
        self.assertEqual(weekly[0]["business_events"], ["model_release"])


class ModelAnalysisFeedTests(unittest.TestCase):
    def test_runtimewire_filter_keeps_model_analysis_and_drops_broad_startup_news(self):
        xml = b"""<?xml version='1.0' encoding='UTF-8'?>
<rss><channel><title>RuntimeWire</title>
<item><title>OpenAI lets GPT-5.6 delegate work to cheaper agents</title>
<link>https://runtimewire.com/article/openai-gpt-agents</link>
<pubDate>Sun, 16 Aug 2026 05:39:10 GMT</pubDate></item>
<item><title>A fintech startup raises a seed round</title>
<link>https://runtimewire.com/article/fintech-seed</link>
<pubDate>Sun, 16 Aug 2026 04:00:00 GMT</pubDate></item>
<item><title>DeepSeek cuts model pricing for hosted inference</title>
<link>https://runtimewire.com/article/deepseek-price</link>
<pubDate>Sun, 16 Aug 2026 03:00:00 GMT</pubDate></item>
</channel></rss>"""

        items = parse_model_analysis_feed_items(
            xml,
            RUNTIMEWIRE_MODEL_FEED,
            NOW,
            site_id="runtimewire",
            site_name="RuntimeWire 模型媒體",
        )

        self.assertEqual(len(items), 2)
        self.assertTrue(all(item.site_id == "runtimewire" for item in items))
        self.assertNotIn("fintech", " ".join(item.title.lower() for item in items))

    def test_new_sources_remain_low_weight_watchlists(self):
        for site_id in ("llm_stats_models", "llm_rumors", "runtimewire"):
            with self.subTest(site_id=site_id):
                self.assertEqual(source_tier_for_site(site_id)["source_tier"], "watchlist")

    def test_qwen_model_identity_blocks_cross_version_story_merge(self):
        self.assertFalse(
            story_titles_can_merge(
                "Qwen releases Qwen3.8-27B model",
                "Qwen releases Qwen3.8-2.4T-A95B model",
            )
        )


if __name__ == "__main__":
    unittest.main()
