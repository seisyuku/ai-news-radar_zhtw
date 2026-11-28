"""Exercise the scheduled publisher against a local bare remote and two checkouts."""
import os
from pathlib import Path
import subprocess

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = yaml.safe_load((ROOT / ".github/workflows/update-news.yml").read_text())
STEPS = WORKFLOW["jobs"]["update"]["steps"]
CAPTURE = next(s["run"] for s in STEPS if "GITHUB_ENV" in s.get("run", ""))
PUBLISH = next(s["run"] for s in STEPS if s.get("name") == "Commit and push changes")
STATE = "data/brief-event-state.json"


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def write(repo, path, value):
    target = repo / path
    target.parent.mkdir(exist_ok=True, parents=True)
    target.write_text(value)


def commit(repo, message):
    git(repo, "add", "-A")
    git(repo, "commit", "-m", message)
    return git(repo, "rev-parse", "HEAD")


@pytest.fixture
def clones(tmp_path, monkeypatch):
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    for role in ("AUTHOR", "COMMITTER"):
        monkeypatch.setenv(f"GIT_{role}_NAME", "Fixture")
        monkeypatch.setenv(f"GIT_{role}_EMAIL", "fixture@example.invalid")
    remote, peer, runner = [tmp_path / name for name in ("remote.git", "peer", "runner")]
    git(tmp_path, "init", "--bare", "--initial-branch=master", str(remote))
    git(tmp_path, "clone", remote.as_uri(), str(peer))
    for path in ("data/archive.json", "data/market-sensor-state.json", STATE, "item/id/index.html"):
        write(peer, path, "original")
    commit(peer, "initial")
    git(peer, "push", "origin", "master")
    git(tmp_path, "clone", "--depth=1", remote.as_uri(), str(runner))
    return runner, peer, remote


def capture(runner):
    envfile = runner.parent / "generation.env"
    subprocess.run(["bash", "-eu", "-c", CAPTURE], cwd=runner, check=True,
                   env={**os.environ, "GITHUB_ENV": str(envfile)})
    return dict(line.split("=", 1) for line in envfile.read_text().splitlines())


def publish(runner, env):
    return subprocess.run(["bash", "-eo", "pipefail", "-c", PUBLISH], cwd=runner,
                          env={**os.environ, **env}, capture_output=True, text=True)


def generate(runner):
    write(runner, "data/archive.json", "generated")
    write(runner, "item/new/index.html", "resolver")
    write(runner, "unrelated.tmp", "local only")


@pytest.mark.parametrize("path,operation", [
    (STATE, "add"), (STATE, "delete"), (STATE, "change"),
    ("data/archive.json", "change"), ("data/market-sensor-state.json", "change"),
    ("item/id/index.html", "change"), ("scripts/update_news.py", "add"),
    ("config/publisher-policy.json", "add"), ("requirements.txt", "add"),
    ("feeds/follow.example.opml", "add"), (".github/workflows/update-news.yml", "add"),
    ("future-input", "add"),
])
def test_changed_inputs_preserve_remote_tip(clones, path, operation):
    runner, peer, remote = clones
    if operation == "add" and path == STATE:
        git(peer, "rm", STATE)
        commit(peer, "before history exists")
        git(peer, "push")
        git(runner, "pull", "--ff-only")
    env = capture(runner)
    generate(runner)
    if operation == "delete":
        git(peer, "rm", path)
    else:
        write(peer, path, "newer remote")
    tip = commit(peer, "concurrent input")
    git(peer, "push")
    result = publish(runner, env)
    assert result.returncode != 0, result.stdout
    assert git(remote, "rev-parse", "master") == tip
    assert "input" in result.stdout.lower()


def test_clean_base_publishes_new_and_retired_resolvers(clones):
    runner, _, remote = clones
    env = capture(runner)
    original = git(remote, "rev-parse", "master")
    generate(runner)
    (runner / "item/id/index.html").unlink()
    result = publish(runner, env)
    assert result.returncode == 0, result.stderr
    assert git(remote, "rev-parse", "master^") == original
    assert git(remote, "ls-tree", "-r", "--name-only", "master", "item") == "item/new/index.html"
    assert git(remote, "show", "master:data/archive.json") == "generated"


@pytest.mark.parametrize("document", ["docs/OPERATIONS.md", "docs/nested/guide.md", "README.md"])
def test_document_change_allows_fast_forward_retry(clones, document):
    runner, peer, remote = clones
    env = capture(runner)
    generate(runner)
    write(peer, document, "concurrent docs")
    tip = commit(peer, "docs")
    git(peer, "push")
    result = publish(runner, env)
    assert result.returncode == 0, result.stderr
    assert git(remote, "rev-parse", "master^") == tip
    assert git(remote, "show", f"master:{document}") == "concurrent docs"
    assert git(remote, "show", "master:data/archive.json") == "generated"
    assert git(remote, "show", "master:item/new/index.html") == "resolver"
    assert "unrelated.tmp" not in git(remote, "ls-tree", "--name-only", "master")


@pytest.mark.parametrize("second_path,allowed", [("docs/second.md", True), ("data/archive.json", False)])
def test_second_race_rechecks_original_inputs(clones, second_path, allowed):
    runner, peer, remote = clones
    env = capture(runner)
    generate(runner)
    write(peer, "docs/guide.md", "race one")
    first = commit(peer, "race one")
    git(peer, "push")
    # Land a second commit immediately after the first rebase, before its push.
    hook = runner / ".git/hooks/post-rewrite"
    hook.write_text("""#!/bin/sh
set -eu
test "$1" = rebase || exit 0
unset $(git rev-parse --local-env-vars)
cd "$PEER"
test ! -f .git/second-race || exit 0
touch .git/second-race
echo 'race two' > "$SECOND_PATH"
git add -- "$SECOND_PATH"
git commit -qm 'race two'
git push -q
""")
    hook.chmod(0o755)
    result = publish(runner, {**env, "PEER": str(peer), "SECOND_PATH": second_path})
    assert (result.returncode == 0) == allowed, result.stderr
    assert git(peer, "rev-parse", "HEAD^") == first
    assert git(remote, "show", f"master:{second_path}") == "race two"
    assert git(remote, "rev-parse", "master^" if allowed else "master") == git(peer, "rev-parse", "HEAD")
    if allowed:
        assert git(remote, "show", "master:data/archive.json") == "generated"


def test_no_generated_diff_does_not_commit_or_push(clones):
    runner, _, remote = clones
    original = git(remote, "rev-parse", "master")
    result = publish(runner, capture(runner))
    assert result.returncode == 0, result.stderr
    assert "No changes" in result.stdout
    assert git(runner, "rev-parse", "HEAD") == git(remote, "rev-parse", "master") == original


def test_push_rejection_is_bounded(clones):
    runner, _, remote = clones
    original = git(remote, "rev-parse", "master")
    env = capture(runner)
    generate(runner)
    hook = remote / "hooks/pre-receive"
    hook.write_text("#!/bin/sh\necho rejected >> attempts\nexit 1\n")
    hook.chmod(0o755)
    result = publish(runner, env)
    assert result.returncode != 0
    assert (remote / "attempts").read_text().splitlines() == ["rejected"] * 3
    assert git(remote, "rev-parse", "master") == original
