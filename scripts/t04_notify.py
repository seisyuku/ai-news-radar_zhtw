#!/usr/bin/env python3
"""Email a sanitized terminal T04 run report from a separate Actions job."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
from urllib.request import Request, urlopen

try:
    from scripts import tw_source_email
except ModuleNotFoundError:  # direct script execution
    import tw_source_email


def github_json(path: str) -> dict:
    repository = os.environ["GITHUB_REPOSITORY"]
    request = Request(
        f"https://api.github.com/repos/{repository}/{path}",
        headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
                 "Accept": "application/vnd.github+json"},
    )
    with urlopen(request, timeout=20) as response:
        return json.load(response)


def stage_lines(path: str) -> list[str]:
    if not Path(path).is_file():
        return ["階段紀錄：未產生（請檢查 Actions 步驟）"]
    lines = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        entry = json.loads(line)
        name = entry["stage"]
        status = entry["status"]
        detail = ""
        if "counts" in entry:
            detail = " " + json.dumps(entry["counts"], ensure_ascii=False, sort_keys=True)
        elif "diagnosis_code" in entry:
            detail = " code=" + str(entry["diagnosis_code"])
        elif "missing_names" in entry:
            detail = " missing=" + ",".join(entry["missing_names"])
        elif "error_type" in entry:
            detail = " error_type=" + str(entry["error_type"])
        if "case_id" in entry:
            detail += " case=" + str(entry["case_id"])
        if "elapsed_seconds" in entry:
            detail += " seconds=" + str(entry["elapsed_seconds"])
        if entry.get("http_status") is not None:
            detail += " http=" + str(entry["http_status"])
        lines.append(f"- {name}: {status}{detail}")
    return lines


def report(run_id: str, stage_path: str) -> tuple[str, str]:
    response = github_json(f"actions/runs/{run_id}/jobs?per_page=100&filter=latest")
    jobs = [job for job in response["jobs"] if job["name"] == "synthetic-only"]
    if len(jobs) != 1:
        raise RuntimeError("evaluation_job_not_unique")
    job = jobs[0]
    conclusion = job.get("conclusion") or job["status"]
    result = "成功" if conclusion == "success" else "失敗或中斷"
    url = f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{run_id}"
    steps = [f"- {item['name']}: {item.get('conclusion') or item['status']}"
             for item in job.get("steps", [])]
    body = (f"T04 合成摘要實測：{result}\n"
            f"Actions run: {url}\n"
            f"評估 job: {conclusion}\n\n"
            "Actions 步驟：\n" + "\n".join(steps) + "\n\n"
            "安全階段紀錄：\n" + "\n".join(stage_lines(stage_path)) + "\n\n"
            "本信只確認 SMTP 伺服器是否接受；收件匣投遞仍以郵件服務為準。\n")
    return f"[AI News Radar][T04] {result} run {run_id}", body


def main() -> int:
    run_id = os.environ["GITHUB_RUN_ID"]
    receipt_path = Path(os.environ["T04_RECEIPT_PATH"])
    try:
        subject, body = report(run_id, os.environ.get("T04_EVENT_LOG", ""))
    except Exception as error:
        # API failures must still produce a failure notification.
        subject = f"[AI News Radar][T04] 狀態查詢失敗 run {run_id}"
        body = (f"T04 結果查詢失敗：{type(error).__name__}\n"
                f"Actions run: https://github.com/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{run_id}\n")
    payload = {"subject": subject, "body": body}
    payload["payload_hash"] = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    outcome = tw_source_email.send(payload, os.environ.get("TW_SOURCE_EMAIL_SETTINGS", ""))
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps({"run_id": run_id, "subject": subject,
                                        "delivery": outcome}, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(outcome))
    return 0 if outcome["status"] == "provider_accepted" else 1


if __name__ == "__main__":
    sys.exit(main())
