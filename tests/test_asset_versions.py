"""Enforce front-end cache busting without a manually maintained hash manifest."""

import os
import re
import subprocess
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
INDEX_HTML = ROOT / "index.html"
LEGACY_ASSET_FILES = ("app.js", "styles.css", "motion.js")
ASSET_FILES = (*LEGACY_ASSET_FILES, "loader.js")
ASSET_PATHS = tuple(f"assets/{name}" for name in ASSET_FILES)
REF_PATTERN = re.compile(r'assets/(' + '|'.join(re.escape(name) for name in ASSET_FILES) + r')\?v=([A-Za-z0-9._-]+)')


def asset_refs(html: str) -> list[tuple[str, str]]:
    return REF_PATTERN.findall(html)


def shared_version(html: str, source: str, *, required_assets=ASSET_FILES) -> str:
    refs = asset_refs(html)
    counts = Counter(name for name, _version in refs)
    if counts != Counter({name: 1 for name in required_assets}):
        raise AssertionError(
            f"{source} 必須各引用一次 {required_assets}，目前為 {dict(counts)}"
        )
    versions = {version for _name, version in refs}
    if len(versions) != 1:
        raise AssertionError(f"{source} 的資產必須共用同一個 ?v= tag，目前為 {sorted(versions)}")
    return versions.pop()


class AssetVersionTests(unittest.TestCase):
    def setUp(self):
        self.html = INDEX_HTML.read_text(encoding="utf-8")

    def test_index_html_references_each_asset_once_with_one_version(self):
        shared_version(self.html, "index.html")

    def test_loader_precedes_app_and_both_scripts_are_deferred(self):
        scripts = re.findall(r'<script\b[^>]*>', self.html)
        loader = next(tag for tag in scripts if "assets/loader.js?" in tag)
        app = next(tag for tag in scripts if "assets/app.js?" in tag)
        self.assertLess(scripts.index(loader), scripts.index(app))
        self.assertRegex(loader, r"\bdefer\b")
        self.assertRegex(app, r"\bdefer\b")

    def test_previous_three_asset_baseline_can_still_supply_its_version(self):
        old_html = '\n'.join(f'<script src="assets/{name}?v=old-tag"></script>' for name in LEGACY_ASSET_FILES)
        self.assertEqual(shared_version(old_html, "舊版", required_assets=LEGACY_ASSET_FILES), "old-tag")
        with self.assertRaises(AssertionError):
            shared_version(old_html, "目前版")

    def test_asset_change_bumps_version_from_git_baseline(self):
        baseline = os.environ.get("ASSET_VERSION_BASE", "HEAD")
        diff = subprocess.run(
            ["git", "diff", "--quiet", baseline, "--", *ASSET_PATHS],
            cwd=ROOT,
            check=False,
        )
        if diff.returncode == 0:
            return
        self.assertEqual(
            diff.returncode,
            1,
            f"無法比較資產與 Git baseline {baseline!r}；請確認該 ref 可用",
        )

        try:
            baseline_html = subprocess.run(
                ["git", "show", f"{baseline}:index.html"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout
        except subprocess.CalledProcessError as error:
            self.fail(f"無法讀取 {baseline}:index.html：{error.stderr.strip()}")

        current_version = shared_version(self.html, "目前 index.html")
        # Older comparison commits predate the loader; the current HTML still
        # requires all four assets. Preserve migration to the new asset set.
        baseline_assets = ASSET_FILES if "loader.js" in dict(asset_refs(baseline_html)) else LEGACY_ASSET_FILES
        baseline_version = shared_version(baseline_html, f"{baseline}:index.html", required_assets=baseline_assets)
        self.assertNotEqual(
            current_version,
            baseline_version,
            "assets/ 有內容變更，但 index.html 的共用 ?v= tag 沒有相對於 "
            f"{baseline} 更新",
        )


if __name__ == "__main__":
    unittest.main()
