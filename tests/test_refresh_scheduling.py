"""Execute the shipped refresh guards with fixed clocks and mocked GitHub API."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

WORKFLOWS = Path(__file__).resolve().parents[1] / ".github" / "workflows"
UPDATE = yaml.safe_load((WORKFLOWS / "update-news.yml").read_text())
WATCHDOG = yaml.safe_load((WORKFLOWS / "watchdog.yml").read_text())
HEARTBEAT_STEP = UPDATE["jobs"]["freshness-check"]["steps"][0]
WATCHDOG_STEP = WATCHDOG["jobs"]["watchdog"]["steps"][0]


@pytest.fixture
def guards(tmp_path):
    # macOS date does not implement GNU date -d. Match the seconds returned by
    # the runner's date for an ISO timestamp and inject a deterministic clock.
    gh = tmp_path / "gh"
    gh.write_text(r"""#!/bin/bash
set -eu
echo "$*" >> "$CALLS"
case "$*" in
    *contents/data/daily-brief.json*) [ "$API_FAIL" != snapshot ]; printf '%s' "$SNAPSHOT" ;;
    *status=success*) [ "$API_FAIL" != runs ]; printf '%s' "$SUCCESS_AT" ;;
    *event=schedule*) [ "$API_FAIL" != runs ]; printf '%s' "$SCHEDULE_RUNS" | jq -r "${4}" ;;
    workflow\ run*) ;;
    *) exit 99 ;;
esac
""")
    date = tmp_path / "date"
    date.write_text("""#!/bin/bash
set -eu
if [ "$#" = 2 ]; then
    echo "$NOW_EPOCH"
else
    "$PYTHON_EXEC" -c 'from datetime import datetime; import sys; print(int(datetime.fromisoformat(sys.argv[1].replace("Z", "+00:00")).timestamp()))' "$3"
fi
""")
    for path in (gh, date):
        path.chmod(0o755)
    calls = tmp_path / "calls"
    output = tmp_path / "output"

    def run(step, minutes=0, seconds=0, **overrides):
        for path in (calls, output):
            path.unlink(missing_ok=True)
        env = {
            **os.environ,
            **{key: str(value) for key, value in step["env"].items() if not str(value).startswith("${{")},
            "PATH": f"{tmp_path}:{os.environ['PATH']}",
            "PYTHON_EXEC": sys.executable,
            "CALLS": str(calls),
            "GITHUB_OUTPUT": str(output),
            "GITHUB_REPOSITORY": "example/news",
            "GITHUB_REF_NAME": "master",
            "SOURCE": "heartbeat",
            "NOW_EPOCH": str(1795802400 + minutes * 60 + seconds),  # 2026-11-27 18:00 UTC
            "SNAPSHOT": '{"generated_at":"2026-11-27T18:00:00.123456Z"}',
            "SUCCESS_AT": "2026-11-27T18:00:00Z",
            "SCHEDULE_RUNS": '{"workflow_runs":[{"created_at":"2026-11-27T18:00:00Z"}]}',
            "API_FAIL": "",
            **overrides,
        }
        script = step["run"].replace("${{ github.repository }}", "example/news")
        result = subprocess.run(["bash", "-c", script], env=env, capture_output=True, text=True)
        return result, output.read_text().strip() if output.exists() else "", (
            calls.read_text().splitlines() if calls.exists() else []
        )

    return run


@pytest.mark.parametrize("minutes,seconds,decision", [(24, 0, "false"), (24, 59, "false"),
                                                       (25, 0, "true"), (26, 0, "true")])
def test_heartbeat_threshold(guards, minutes, seconds, decision):
    result, output, calls = guards(HEARTBEAT_STEP, minutes, seconds)
    assert result.returncode == 0, result.stderr
    assert output == f"should_run={decision}"
    assert len(calls) == 1
    assert "contents/data/daily-brief.json" in calls[0]
    assert "ref=master" in calls[0]


def test_skipped_success_cannot_refresh_stale_snapshot(guards):
    # Saved Actions run 46046768857 succeeded with its update job skipped.
    # At 18:25 UTC that run was under 25 min old, but the last committed
    # snapshot (a35bdd1b) generated at 17:57:49 UTC was already stale.
    result, output, _ = guards(HEARTBEAT_STEP, 25, SUCCESS_AT="2026-11-27T18:05:10Z",
                              SNAPSHOT='{"generated_at":"2026-11-27T17:57:49.870248Z"}')
    assert result.returncode == 0, result.stderr
    assert output == "should_run=true"


@pytest.mark.parametrize("condition", [
    {"API_FAIL": "snapshot"}, {"SNAPSHOT": "{}"}, {"SNAPSHOT": ""},
    {"SNAPSHOT": "bad JSON"}, {"SNAPSHOT": '{"generated_at":7}'},
    {"SNAPSHOT": '{"generated_at":"2026-11-27T99:00:00Z"}'},
    {"SNAPSHOT": '{"generated_at":"2026-11-27T18:01:00Z"}'},
])
def test_heartbeat_refreshes_when_snapshot_cannot_prove_freshness(guards, condition):
    result, output, _ = guards(HEARTBEAT_STEP, **condition)
    assert result.returncode == 0, result.stderr
    assert output == "should_run=true"
    assert "::warning::" in result.stdout


@pytest.mark.parametrize("source", ["manual", "schedule", "watchdog"])
def test_normal_refresh_does_not_consult_heartbeat_guard(guards, source):
    result, output, calls = guards(HEARTBEAT_STEP, SOURCE=source, API_FAIL="snapshot")
    assert result.returncode == 0, result.stderr
    assert output == "should_run=true"
    assert not calls


def test_queued_heartbeat_rechecks_snapshot_after_previous_refresh(guards):
    # GitHub serializes the entire workflow. While the previous run has yet
    # to publish, the API only knows the old snapshot. The queued heartbeat
    # sees the new Git timestamp once it acquires the concurrency group.
    assert UPDATE["concurrency"] == {"group": "update-news", "cancel-in-progress": False}
    assert UPDATE["jobs"]["update"]["needs"] == "freshness-check"
    assert UPDATE["jobs"]["update"]["if"] == "needs.freshness-check.outputs.should_run == 'true'"
    result, output, _ = guards(HEARTBEAT_STEP, 26)
    assert result.returncode == 0
    assert output == "should_run=true"
    result, output, _ = guards(HEARTBEAT_STEP, 26, SNAPSHOT='{"generated_at":"2026-11-27T18:25:00Z"}')
    assert result.returncode == 0
    assert output == "should_run=false"


@pytest.mark.parametrize("run_conclusion", ["failure", None])
@pytest.mark.parametrize("minutes,seconds,dispatch", [(89, 59, False), (90, 0, False),
                                                      (90, 59, False), (91, 0, True)])
def test_watchdog_threshold_is_latest_schedule_even_if_failed_or_running(guards, minutes, seconds, dispatch, run_conclusion):
    runs = {"workflow_runs": [
        {"created_at": "2026-11-27T18:00:00Z", "conclusion": run_conclusion},
        {"created_at": "2026-11-27T17:15:00Z", "conclusion": "success"},
    ]}
    result, _, calls = guards(WATCHDOG_STEP, minutes, seconds, SCHEDULE_RUNS=json.dumps(runs))
    assert result.returncode == 0, result.stderr
    assert len(calls) == 1 + dispatch
    assert "event=schedule&per_page=1" in calls[0] and "status=" not in calls[0]
    if dispatch:
        assert calls[1] == "workflow run update-news.yml -R example/news"


@pytest.mark.parametrize("params,status", [({"SCHEDULE_RUNS": '{"workflow_runs":[]}'}, 0), ({"API_FAIL": "runs"}, 1)])
def test_watchdog_without_verified_schedule_does_not_dispatch(guards, params, status):
    result, _, calls = guards(WATCHDOG_STEP, 120, **params)
    assert result.returncode == status
    assert len(calls) == 1
