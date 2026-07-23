"""Minimal helper for unit-testing pure functions defined in assets/app.js.

There is no JS test runner in this repo (only `node --check` for syntax, per
skills/ai-news-radar/SKILL.md) and app.js is a browser script that calls
init() at module scope, so it cannot be `require()`d/executed wholesale in
Node without a DOM. Instead, extract_declarations() pulls specific named
top-level `function NAME(...) { ... }` / `const NAME = ...;` declarations
out of the real assets/app.js source by name (so tests exercise the actual
shipped code, not a duplicated copy), and run_js() hands a combined script -
those declarations plus a caller-supplied test harness - to a `node`
subprocess.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_JS_PATH = ROOT / "assets" / "app.js"


def _extract_one(source: str, name: str) -> str:
    pattern = re.compile(rf"(?m)^(function\s+{re.escape(name)}\s*\(|const\s+{re.escape(name)}\b)")
    match = pattern.search(source)
    if not match:
        raise ValueError(f"declaration not found in assets/app.js: {name}")
    is_function = match.group(1).startswith("function")

    i = match.end()
    n = len(source)
    depth = 0
    body_started = False
    while i < n:
        c = source[i]
        if c == "\\":
            i += 2
            continue
        if c in ("'", '"', "`"):
            quote = c
            i += 1
            while i < n and source[i] != quote:
                if source[i] == "\\":
                    i += 2
                else:
                    i += 1
            i += 1
            continue
        if source.startswith("//", i):
            nl = source.find("\n", i)
            i = nl if nl != -1 else n
            continue
        if source.startswith("/*", i):
            end = source.find("*/", i + 2)
            i = end + 2 if end != -1 else n
            continue
        if c == "{":
            depth += 1
            body_started = True
            i += 1
            continue
        if c == "}":
            depth -= 1
            i += 1
            if is_function and body_started and depth == 0:
                return source[match.start():i]
            continue
        if not is_function and c == ";" and depth == 0:
            return source[match.start():i]
        i += 1
    raise ValueError(f"unterminated declaration in assets/app.js: {name}")


def extract_declarations(*names: str) -> str:
    """Return the named top-level declarations from assets/app.js, in the
    order they appear in the source (so dependency-before-use holds for the
    generated const/function ordering)."""
    source = APP_JS_PATH.read_text(encoding="utf-8")
    blocks = [_extract_one(source, name) for name in dict.fromkeys(names)]
    blocks.sort(key=source.index)
    return "\n\n".join(blocks)


def run_js(script: str) -> dict:
    """Run `script` (which must end by printing exactly one JSON value to
    stdout) under `node` and return the parsed result. Raises AssertionError
    with node's stderr/stdout on a non-zero exit or invalid JSON, so a
    failing scenario inside the JS harness shows up as a normal pytest
    failure."""
    proc = subprocess.run(
        ["node", "-e", script],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc.returncode != 0:
        raise AssertionError(f"node exited {proc.returncode}\nstdout: {proc.stdout}\nstderr: {proc.stderr}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"node did not print valid JSON\nstdout: {proc.stdout}\nstderr: {proc.stderr}") from exc
