"""Filesystem and object bytes must share the existing pair identity checks."""

import json

import pytest

from scripts.generate_digest import DigestOutputError, verify_digest_pair, write_digest
from scripts.digest_integrity import verify_digest_bytes
from test_generate_digest import build, inputs


def test_object_bytes_and_filesystem_verify_the_same_pair(tmp_path):
    document = build(inputs(tmp_path / "in"))
    md, meta = write_digest(document, tmp_path / "out")
    assert verify_digest_bytes(md.read_bytes(), meta.read_bytes()) == verify_digest_pair(md, meta)


@pytest.mark.parametrize("damage", ["markdown", "metadata", "identity", "utf8", "bom"])
def test_both_boundaries_reject_altered_or_invalid_pairs(tmp_path, damage):
    document = build(inputs(tmp_path / "in"))
    md, meta = write_digest(document, tmp_path / "out")
    if damage == "markdown":
        md.write_bytes(md.read_bytes() + b"altered")
    elif damage == "metadata":
        value = json.loads(meta.read_bytes())
        value["health"] = {"altered": True}
        meta.write_text(json.dumps(value))
    elif damage == "identity":
        md.write_bytes(md.read_bytes().replace(document["input_identity"].encode(), b"0" * 64, 1))
    elif damage == "utf8":
        meta.write_bytes(b"\xff")
    else:
        meta.write_bytes(b"\xef\xbb\xbf" + meta.read_bytes())
    with pytest.raises((ValueError, UnicodeError)):
        verify_digest_bytes(md.read_bytes(), meta.read_bytes())
    with pytest.raises(DigestOutputError):
        verify_digest_pair(md, meta)
