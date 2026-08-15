import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone
from unittest.mock import patch

from scripts.update_news import (
    KR36_AI_FALLBACK_FEED_URL,
    KR36_AI_FEED_URL,
    apply_source_health_history,
    fetch_kr36_ai,
    report_persistent_source_failures,
)


NOW = datetime(2026, 8, 16, tzinfo=timezone.utc)


def rss(title="AI芯片公司发布新模型", link="https://36kr.com/p/123"):
    return f"""<?xml version='1.0' encoding='UTF-8'?>
<rss><channel><item>
<title>{title}</title><link>{link}</link>
<pubDate>Sat, 15 Aug 2026 12:00:00 GMT</pubDate>
</item></channel></rss>""".encode("utf-8")


class FakeResponse:
    def __init__(self, content, content_type):
        self.content = content
        self.headers = {"Content-Type": content_type}

    def raise_for_status(self):
        return None


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.responses.pop(0)


class Kr36FallbackTests(unittest.TestCase):
    def test_direct_feed_is_preferred_when_it_is_valid(self):
        session = FakeSession([FakeResponse(rss(), "application/rss+xml")])

        items = fetch_kr36_ai(session, NOW)

        self.assertEqual([call[0] for call in session.calls], [KR36_AI_FEED_URL])
        self.assertEqual(items[0].meta["feed_path"], "direct")

    def test_html_waf_challenge_uses_google_news_fallback(self):
        session = FakeSession(
            [
                FakeResponse(b"<!DOCTYPE html><html>security check</html>", "text/html"),
                FakeResponse(rss(link="https://news.google.com/rss/articles/123"), "application/xml"),
            ]
        )

        items = fetch_kr36_ai(session, NOW)

        self.assertEqual([call[0] for call in session.calls], [KR36_AI_FEED_URL, KR36_AI_FALLBACK_FEED_URL])
        self.assertEqual(items[0].meta["feed_path"], "google_news_fallback")


class SourceHealthHistoryTests(unittest.TestCase):
    def test_failure_becomes_persistent_on_third_consecutive_run(self):
        previous = {
            "sites": [
                {
                    "site_id": "kr36_ai",
                    "ok": False,
                    "consecutive_failures": 2,
                    "first_failure_at": "2026-08-15T00:00:00Z",
                    "last_success_at": "2026-08-14T23:00:00Z",
                }
            ]
        }
        statuses = [{"site_id": "kr36_ai", "site_name": "36Kr AI", "ok": False, "error": "blocked"}]

        persistent = apply_source_health_history(statuses, previous, NOW, threshold=3)

        self.assertTrue(statuses[0]["persistent_failure"])
        self.assertEqual(statuses[0]["consecutive_failures"], 3)
        self.assertEqual(persistent[0]["first_failure_at"], "2026-08-15T00:00:00Z")

    def test_success_resets_failure_streak(self):
        previous = {"sites": [{"site_id": "kr36_ai", "ok": False, "consecutive_failures": 5}]}
        statuses = [{"site_id": "kr36_ai", "site_name": "36Kr AI", "ok": True, "error": None}]

        persistent = apply_source_health_history(statuses, previous, NOW)

        self.assertEqual(persistent, [])
        self.assertEqual(statuses[0]["consecutive_failures"], 0)
        self.assertFalse(statuses[0]["persistent_failure"])

    def test_persistent_failure_emits_annotation_and_job_summary(self):
        failures = [
            {
                "site_id": "kr36_ai",
                "consecutive_failures": 3,
                "first_failure_at": "2026-08-15T00:00:00Z",
                "error": "blocked | challenge",
            }
        ]
        with tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8") as summary_file:
            with patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": summary_file.name}):
                output = io.StringIO()
                with redirect_stdout(output):
                    report_persistent_source_failures(failures)
                summary_file.seek(0)
                summary = summary_file.read()

        self.assertIn("::warning file=data/source-status.json", output.getvalue())
        self.assertIn("Persistent source failures", summary)
        self.assertIn("blocked \\| challenge", summary)


if __name__ == "__main__":
    unittest.main()
