"""Run the actual workflow guard against isolated local Git objects."""
import os
from pathlib import Path
import subprocess

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = yaml.safe_load((ROOT / ".github/workflows/update-news.yml").read_text())
STEPS = [s for job in WORKFLOW["jobs"].values() for s in job.get("steps", [])]
CAPTURE = next(s["run"] for s in STEPS if s.get("name") == "Remember input event history revision")
COMMIT = next(s["run"] for s in STEPS if s.get("name") == "Commit and push changes")
GUARD = COMMIT[COMMIT.index("remote_state_blob="):COMMIT.index("# Rebase's")]


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


@pytest.mark.parametrize("initial,remote,allowed", [(None, None, True), (None, "new", False),
                                                     ("same", "same", True), ("old", "new", False),
                                                     ("old", None, False)])
def test_state_guard_preserves_remote_history(tmp_path, initial, remote, allowed):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "--initial-branch=master")
    (repo / "README").write_text("guard fixture")
    state = repo / "data/brief-event-state.json"
    if initial is not None:
        state.parent.mkdir()
        state.write_text(initial)
    git(repo, "add", ".")
    git(repo, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
        "-c", "commit.gpgsign=false", "commit", "-m", "fixture")
    envfile = tmp_path / "env"
    capture = subprocess.run(["bash", "-e", "-c", CAPTURE], cwd=repo,
                             env={**os.environ, "GITHUB_ENV": str(envfile)}, capture_output=True, text=True)
    assert capture.returncode == 0, capture.stderr
    line = envfile.read_text().strip()
    assert len(line.splitlines()) == 1
    expected = line.split("=", 1)[1]
    if initial is None:
        assert expected == "MISSING"
    if remote != initial:
        state.parent.mkdir(exist_ok=True)
        if remote is None:
            state.unlink()
        else:
            state.write_text(remote)
        git(repo, "add", ".")
        git(repo, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
            "-c", "commit.gpgsign=false", "commit", "-m", "remote revision")
    git(repo, "update-ref", "refs/remotes/origin/master", git(repo, "rev-parse", "HEAD"))
    result = subprocess.run(["bash", "-e", "-c", GUARD], cwd=repo,
                            env={**os.environ, "BRIEF_INPUT_STATE_BLOB": expected}, capture_output=True, text=True)
    assert (result.returncode == 0) == allowed
    if not allowed:
        assert "history changed remotely" in result.stdout
