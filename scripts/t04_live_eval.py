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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

try:
    from scripts.diagnose_gemini import diagnose_gemini
    from scripts.evaluate_ai_summaries import (
        DEFAULT_CASES_PATH,
        DEFAULT_GEMINI_MODEL,
        evaluate_cases,
        load_cases,
        provider_error_details,
    )
    from scripts.news_summaries import DEFAULT_GEMINI_TIMEOUT_SECONDS, make_gemini_generator, make_groq_generator
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from diagnose_gemini import diagnose_gemini
    from evaluate_ai_summaries import (
        DEFAULT_CASES_PATH,
        DEFAULT_GEMINI_MODEL,
        evaluate_cases,
        load_cases,
        provider_error_details,
    )
    from news_summaries import DEFAULT_GEMINI_TIMEOUT_SECONDS, make_gemini_generator, make_groq_generator


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
                "error_type": safe_error_type(row.get("provider_error") or {}),
            }
            for row in report["results"]
        ],
    }


def safe_error_type(details: Mapping[str, Any]) -> str | None:
    known = {"ReadTimeout", "ConnectTimeout", "Timeout", "ConnectionError", "HTTPError",
             "JSONDecodeError", "ValueError", "KeyError", "IndexError", "TypeError",
             "ChunkedEncodingError", "SSLError", "RequestException"}
    value = details.get("type")
    return value if value in known else "OtherError" if value else None


def stage(name: str, status: str, **details: Any) -> None:
    """Persist a sanitized checkpoint for Actions, without provider text."""
    path = os.environ.get("T04_EVENT_LOG")
    if not path:
        return
    record = {"at": datetime.now(timezone.utc).isoformat(), "stage": name,
              "status": status, **details}
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")


def observed(generate: Callable, provider: str, *, monotonic=time.monotonic) -> Callable:
    """Keep case latency and error class even if a later call or job fails."""
    def call(prompt: str, case: Mapping[str, Any]) -> str:
        started = monotonic()
        stage(provider + "_request", "started", case_id=case["id"])
        try:
            output = generate(prompt, case)
        except Exception as error:
            details = provider_error_details(error)
            stage(provider + "_request", "failed", case_id=case["id"],
                  elapsed_seconds=round(monotonic() - started, 3),
                  error_type=safe_error_type(details), http_status=details.get("http_status"))
            raise
        stage(provider + "_request", "passed", case_id=case["id"],
              elapsed_seconds=round(monotonic() - started, 3))
        return output
    return call


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="T04 synthetic-only Groq/Gemini acceptance")
    parser.add_argument("--gemini-interval-seconds", type=float, default=10.0)
    parser.add_argument("--groq-interval-seconds", type=float, default=2.0)
    parser.add_argument("--post-diagnostic-cooldown-seconds", type=float, default=60.0)
    args = parser.parse_args(argv)
    if min(args.gemini_interval_seconds, args.groq_interval_seconds,
           args.post_diagnostic_cooldown_seconds) < 0:
        parser.error("intervals must be non-negative")

    stage("evaluation", "started", gemini_timeout_seconds=DEFAULT_GEMINI_TIMEOUT_SECONDS)

    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    missing = [name for name, value in (("GEMINI_API_KEY", gemini_key),
                                       ("GROQ_API_KEY", groq_key)) if not value]
    if missing:
        stage("credentials", "failed", missing_names=missing)
        print(json.dumps({"status": "missing_credentials", "names": missing}))
        return 2
    stage("credentials", "passed")

    model = os.environ.get("GEMINI_SUMMARY_MODEL") or DEFAULT_GEMINI_MODEL
    stage("gemini_diagnostic", "started")
    diagnostic = diagnose_gemini(api_key=gemini_key, model=model, timeout=DEFAULT_GEMINI_TIMEOUT_SECONDS)
    diagnostic_steps = []
    for step in diagnostic.get("steps", []):
        details = step.get("error") or {}
        clean = {"name": step["name"], "status": step["status"],
                 "error_type": safe_error_type(details), "http_status": details.get("http_status")}
        diagnostic_steps.append(clean)
        stage("diagnostic_" + step["name"], step["status"],
              error_type=clean["error_type"], http_status=clean["http_status"])
    if not diagnostic["ok"]:
        failed_steps = [step["name"] for step in diagnostic["steps"] if step["status"] == "failed"]
        stage("gemini_diagnostic", "failed", diagnosis_code=diagnostic["diagnosis"]["code"],
              failed_steps=failed_steps)
        print(json.dumps({"status": "diagnostic_failed", "model": model,
                          "diagnosis_code": diagnostic["diagnosis"]["code"],
                          "failed_steps": failed_steps, "diagnostic_steps": diagnostic_steps}))
        return 1
    stage("gemini_diagnostic", "passed")

    time.sleep(args.post_diagnostic_cooldown_seconds)
    stage("cooldown", "passed")
    cases = load_cases(DEFAULT_CASES_PATH)
    stage("corpus", "passed", case_count=len(cases))
    gemini = evaluate_cases(
        cases, "gemini", paced(observed(make_gemini_generator(gemini_key, model=model), "gemini"),
                                args.gemini_interval_seconds),
    )
    stage("gemini_cases", "passed" if gemini["counts"]["failed"] == 0 else "failed",
          counts=gemini["counts"], cases=safe_report(gemini)["cases"])
    groq = evaluate_cases(
        cases, "groq", paced(observed(make_groq_generator(groq_key), "groq"), args.groq_interval_seconds),
    )
    stage("groq_cases", "passed" if groq["counts"]["failed"] == 0 else "comparison_miss",
          counts=groq["counts"], cases=safe_report(groq)["cases"])
    print(json.dumps({"status": "evaluated", "case_count": len(cases),
                      "model": model, "diagnostic": "passed",
                      "gemini_timeout_seconds": DEFAULT_GEMINI_TIMEOUT_SECONDS,
                      "gemini_acceptance_passed": gemini["counts"]["failed"] == 0,
                      "reports": [safe_report(gemini), safe_report(groq)]},
                     ensure_ascii=False))
    # T04 requires Gemini to pass; Groq is a same-corpus comparator whose
    # misses remain visible but do not invalidate Gemini's acceptance run.
    result = 1 if gemini["counts"]["failed"] else 0
    stage("evaluation", "passed" if result == 0 else "failed")
    return result


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        # Avoid printing provider responses or credential-bearing exceptions.
        stage("evaluation", "failed", error_type=type(error).__name__)
        print(json.dumps({"status": "unexpected_error", "error_type": type(error).__name__}))
        raise SystemExit(1) from None
