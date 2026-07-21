"""Enforces docs/OPERATIONS.md's front-end cache-busting rule.

If assets/app.js, assets/styles.css, or assets/motion.js change without a
matching ?v= bump in index.html (or the bump lands without updating
tests/asset_manifest.json), this test suite fails.
"""
import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_HTML = ROOT / "index.html"
MANIFEST_PATH = Path(__file__).resolve().parent / "asset_manifest.json"
ASSET_FILES = ("app.js", "styles.css", "motion.js")

REF_PATTERN = re.compile(r'assets/(app\.js|styles\.css|motion\.js)\?v=([A-Za-z0-9._-]+)')


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class AssetVersionManifestTests(unittest.TestCase):
    def setUp(self):
        self.html = INDEX_HTML.read_text(encoding="utf-8")
        self.refs = dict(REF_PATTERN.findall(self.html))
        with open(MANIFEST_PATH, encoding="utf-8") as f:
            self.manifest = json.load(f)

    def test_index_html_references_all_three_assets(self):
        self.assertEqual(set(self.refs.keys()), set(ASSET_FILES))

    def test_all_asset_references_share_one_version_tag(self):
        versions = set(self.refs.values())
        self.assertEqual(
            len(versions), 1,
            f"assets/{{app.js,styles.css,motion.js}} must share one ?v= tag, found: {self.refs}",
        )

    def test_current_version_tag_is_recorded_in_manifest(self):
        version = next(iter(self.refs.values()))
        self.assertIn(
            version, self.manifest,
            f"?v={version} referenced in index.html but missing from tests/asset_manifest.json "
            "- add an entry recording the sha256 of each asset file for this version.",
        )

    def test_manifest_holds_exactly_one_entry(self):
        self.assertEqual(
            len(self.manifest), 1,
            f"tests/asset_manifest.json has {len(self.manifest)} entries: {sorted(self.manifest)} - "
            "it must hold only the current ?v= tag's entry. When bumping the ?v= tag, REPLACE the "
            "existing entry with the new one instead of adding a new key alongside it; historical "
            "audit belongs to `git log -- tests/asset_manifest.json`, not to old entries left in "
            "this file.",
        )

    def test_asset_hashes_match_manifest_for_current_version(self):
        version = next(iter(self.refs.values()))
        entry = self.manifest.get(version, {})
        for name in ASSET_FILES:
            actual = _sha256(ROOT / "assets" / name)
            expected = entry.get(name)
            self.assertEqual(
                actual, expected,
                f"assets/{name} content does not match tests/asset_manifest.json[{version}][{name}] "
                "- either the file changed without bumping ?v=, or ?v= was bumped without "
                "updating the manifest.",
            )


if __name__ == "__main__":
    unittest.main()
