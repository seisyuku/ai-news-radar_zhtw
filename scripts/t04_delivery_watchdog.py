#!/usr/bin/env python3
"""One-time independent T04 deadline check; email if no accepted run receipt exists."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import io
import json
import os
from urllib.request import Request, urlopen
import zipfile

try:
    from scripts import tw_source_email
except ModuleNotFoundError:  # direct script execution
    import tw_source_email


WINDOW_START = datetime(2026, 10, 27, 0, 45, tzinfo=timezone.utc)
DEADLINE = datetime(2026, 10, 27, 2, 17, tzinfo=timezone.utc)
BRANCH = "codex/t04-gemini-summary"


def get(path: str, *, binary: bool = False):
    request = Request(
        f"https://api.github.com/repos/{os.environ['GITHUB_REPOSITORY']}/{path}",
        headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
                 "Accept": "application/vnd.github+json"},
    )
    with urlopen(request, timeout=20) as response:
        data = response.read()
    return data if binary else json.loads(data)


def relevant_runs(now: datetime) -> list[dict]:
    query = "actions/runs?per_page=100&event=workflow_dispatch&branch=" + BRANCH
    response = get(query)
    if response["total_count"] > 100:
        raise RuntimeError("run_history_truncated")
    return [run for run in response["workflow_runs"]
            if run["name"] == "T04 synthetic summary evaluation"
            and WINDOW_START <= datetime.fromisoformat(run["created_at"].replace("Z", "+00:00")) <= now]


def earlier_watchdog_succeeded(now: datetime) -> bool:
    response = get("actions/workflows/t04-delivery-watchdog.yml/runs?per_page=100")
    if response["total_count"] > 100:
        raise RuntimeError("watchdog_history_truncated")
    current = int(os.environ["GITHUB_RUN_ID"])
    return any(run["id"] != current and run["conclusion"] == "success"
               and DEADLINE <= datetime.fromisoformat(run["created_at"].replace("Z", "+00:00")) <= now
               for run in response["workflow_runs"])


def accepted_receipt(run_id: int) -> bool:
    response = get(f"actions/runs/{run_id}/artifacts?per_page=100")
    if response["total_count"] > 100:
        raise RuntimeError("artifact_history_truncated")
    for artifact in response["artifacts"]:
        if artifact["name"] != "t04-email-receipt" or artifact["expired"]:
            continue
        data = get(f"actions/artifacts/{artifact['id']}/zip", binary=True)
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            receipt = json.loads(archive.read("t04-receipt.json"))
        if receipt.get("run_id") == str(run_id) and receipt.get("delivery", {}).get("status") == "provider_accepted":
            return True
    # Artifact upload may fail after the email was accepted. The script only
    # exits successfully for provider_accepted, so its step is valid evidence.
    jobs = get(f"actions/runs/{run_id}/jobs?per_page=100&filter=latest")
    for job in jobs["jobs"]:
        if job["name"] != "notify":
            continue
        if any(step["name"] == "Email terminal result" and step.get("conclusion") == "success"
               for step in job.get("steps", [])):
            return True
    return False


def compose(runs: list[dict], error_type: str | None = None) -> dict:
    repository = os.environ["GITHUB_REPOSITORY"]
    if error_type:
        title = "查核失敗"
        reason = f"獨立查核發生 {error_type}；請人工檢查 T04 執行與通知紀錄。"
    elif not runs:
        title = "排程未啟動"
        reason = "臺北 2026-10-27 08:45～10:17 間沒有 T04 workflow_dispatch run。"
    else:
        title = "執行或通知異常"
        reason = "T04 有 run，但截至期限沒有可驗證的 SMTP 接受收據。"
    links = "\n".join(f"- {run['html_url']} ({run['status']}/{run.get('conclusion')})" for run in runs)
    body = (f"T04 獨立查核：{title}\n{reason}\n"
            f"查核期限：2026-10-27 10:17 Asia/Taipei\n"
            f"候選執行：\n{links or '- 無'}\n"
            f"倉庫：https://github.com/{repository}/actions\n\n"
            "這是獨立於 Codex 本地排程的逾期告警；SMTP 接受不等於收件匣投遞。\n")
    payload = {"subject": f"[AI News Radar][T04] {title}", "body": body}
    payload["payload_hash"] = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    return payload


def main() -> int:
    now = datetime.now(timezone.utc)
    if now < DEADLINE:
        print(json.dumps({"status": "before_deadline"}))
        return 0
    if now.date() != DEADLINE.date():
        print(json.dumps({"status": "outside_one_time_window"}))
        return 0
    runs = []
    error_type = None
    try:
        if earlier_watchdog_succeeded(now):
            print(json.dumps({"status": "earlier_watchdog_completed"}))
            return 0
        runs = relevant_runs(now)
        if runs and all(accepted_receipt(run["id"]) for run in runs):
            print(json.dumps({"status": "notification_verified", "run_count": len(runs)}))
            return 0
    except Exception as error:
        error_type = type(error).__name__
    payload = compose(runs, error_type)
    result = tw_source_email.send(payload, os.environ.get("TW_SOURCE_EMAIL_SETTINGS", ""))
    print(json.dumps({"status": "watchdog_notified" if result["status"] == "provider_accepted" else "watchdog_email_failed",
                      "run_count": len(runs), "error_type": error_type, "delivery": result}))
    return 0 if result["status"] == "provider_accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
