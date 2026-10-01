"""Run the shipped browser loaders and initialization under controlled fetches."""

import subprocess
from pathlib import Path

import pytest


SCRIPT = Path(__file__).with_name("frontend_loader_scenarios.cjs")
DATA = [
    "./data/source-status.json", "./data/daily-brief.json",
    "./data/stories-merged.json", "./data/market-signals.json",
    "./data/llm-radar.json",
]


@pytest.mark.parametrize("asset", DATA)
def test_main_renders_while_one_auxiliary_is_pending(asset):
    result = subprocess.run(["node", str(SCRIPT), "aux-pending", asset], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("asset", DATA)
def test_auxiliary_rejection_does_not_hide_news(asset):
    result = subprocess.run(["node", str(SCRIPT), "aux-reject", asset], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("scenario", ["main-fail", "all-race", "all-error-race", "all-retry", "timeout-abort", "timeout-json", "stories-url"])
def test_loader_scenarios(scenario):
    result = subprocess.run(["node", str(SCRIPT), scenario], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr


def test_loader_module_direct_contracts():
    script = SCRIPT.with_name("frontend_loader_module.test.cjs")
    result = subprocess.run(["node", "--test", str(script)], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr


def test_selection_module_direct_contracts():
    script = SCRIPT.with_name("frontend_selection_module.test.cjs")
    result = subprocess.run(["node", "--test", str(script)], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr


def test_section_filters_keep_source_search_and_modes():
    result = subprocess.run(["node", str(SCRIPT), "section-filters"], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr
