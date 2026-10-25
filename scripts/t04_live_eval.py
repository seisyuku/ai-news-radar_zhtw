#!/usr/bin/env python3
"""Run T04 synthetic-only provider acceptance from GitHub Actions secrets.

No publisher feed, snapshot, private OPML, or generated provider text is logged.
This is an explicit evaluation command, never part of the news refresh job.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from typing import Any, Callable, Mapping

try:
    from scripts.diagnose_gemini import diagnose_gemini
    from scripts.evaluate_ai_summaries import (
        DEFAULT_CASES_PATH,
        DEFAULT_GEMINI_MODEL,
        evaluate_cases,
        load_cases,
    )
    from scripts.news_summaries import make_gemini_generator, make_groq_generator
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from diagnose_gemini import diagnose_gemini
    from evaluate_ai_summaries import (
        DEFAULT_CASES_PATH,
        DEFAULT_GEMINI_MODEL,
        evaluate_cases,
        load_cases,
    )
    from news_summaries import make_gemini_generator, make_groq_generator


def paced(
    generate: Callable[[str, Mapping[str, Any]], str],
    interval: float,
    *,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> Callable[[str, Mapping[str, Any]], str]:
    """Space provider calls by at least interval seconds, including failures."""

    last_started: float | None = None

    def call(prompt: str, case: Mapping[str, Any]) -> str:
        nonlocal last_started
        now = monotonic()
        if last_started is not None:
            delay = interval - (now - last_started)
            if delay > 0:
                sleep(delay)
                now = monotonic()
        last_started = now
        return generate(prompt, case)

    return call


def safe_report(report: Mapping[str, Any]) -> dict[str, Any]:
    """Discard model output and provider error messages before logging."""

    return {
        "provider": report["provider"],
        "counts": report["counts"],
        "cases": [
            {
                "id": row["id"],
                "status": row["status"],
                "error_codes": [
                    str(error).split(":", 1)[0]
                    for error in (row.get("validation") or {}).get("errors", [])
                ],
                "http_status": (row.get("provider_error") or {}).get("http_status"),
            }
            for row in report["results"]
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="T04 synthetic-only Groq/Gemini acceptance")
    parser.add_argument("--gemini-interval-seconds", type=float, default=10.0)
    parser.add_argument("--groq-interval-seconds", type=float, default=2.0)
    parser.add_argument("--post-diagnostic-cooldown-seconds", type=float, default=60.0)
    args = parser.parse_args(argv)
    if min(args.gemini_interval_seconds, args.groq_interval_seconds,
           args.post_diagnostic_cooldown_seconds) < 0:
        parser.error("intervals must be non-negative")

    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    missing = [name for name, value in (("GEMINI_API_KEY", gemini_key),
                                       ("GROQ_API_KEY", groq_key)) if not value]
    if missing:
        print(json.dumps({"status": "missing_credentials", "names": missing}))
        return 2

    model = os.environ.get("GEMINI_SUMMARY_MODEL") or DEFAULT_GEMINI_MODEL
    diagnostic = diagnose_gemini(api_key=gemini_key, model=model)
    if not diagnostic["ok"]:
        failed_steps = [step["name"] for step in diagnostic["steps"] if step["status"] == "failed"]
        print(json.dumps({"status": "diagnostic_failed", "model": model,
                          "diagnosis_code": diagnostic["diagnosis"]["code"],
                          "failed_steps": failed_steps}))
        return 1

    time.sleep(args.post_diagnostic_cooldown_seconds)
    cases = load_cases(DEFAULT_CASES_PATH)
    gemini = evaluate_cases(
        cases, "gemini", paced(make_gemini_generator(gemini_key, model=model),
                                args.gemini_interval_seconds),
    )
    groq = evaluate_cases(
        cases, "groq", paced(make_groq_generator(groq_key), args.groq_interval_seconds),
    )
    print(json.dumps({"status": "evaluated", "case_count": len(cases),
                      "model": model, "diagnostic": "passed",
                      "gemini_acceptance_passed": gemini["counts"]["failed"] == 0,
                      "reports": [safe_report(gemini), safe_report(groq)]},
                     ensure_ascii=False))
    # T04 requires Gemini to pass; Groq is a same-corpus comparator whose
    # misses remain visible but do not invalidate Gemini's acceptance run.
    return 1 if gemini["counts"]["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
