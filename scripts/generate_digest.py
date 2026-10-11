"""Offline digest CLI. No fetch, translation, publishing or scheduler entrypoint."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

if __package__:
    from .digest_integrity import verify_digest_bytes
    from .archive_output import atomic_write_text
    from .digest_document import build_digest_document, document_identity
    from .digest_input import load_digest_input
    from .digest_render import render_digest
    from .digest_window import DigestTimeError, window_for_date
else:
    from digest_integrity import verify_digest_bytes
    from archive_output import atomic_write_text
    from digest_document import build_digest_document, document_identity
    from digest_input import load_digest_input
    from digest_render import render_digest
    from digest_window import DigestTimeError, window_for_date


class DigestOutputError(ValueError):
    pass


def _paths(output_dir, date):
    return (output_dir / f"digest-{date}.md", output_dir / f"digest-{date}.meta.json")


def verify_digest_pair(markdown_path, metadata_path):
    """Read the pair and reject incomplete, stale or altered handoff artifacts."""
    try:
        markdown = Path(markdown_path).read_bytes()
        metadata = verify_digest_bytes(markdown, Path(metadata_path).read_bytes())
    except (OSError, UnicodeError, ValueError, TypeError):
        raise DigestOutputError("digest_pair_invalid") from None
    return metadata


def write_digest(document, output_dir):
    """Build both complete payloads before writes; replacements are per-file."""
    if document_identity(document) != document.get("input_identity"):
        raise DigestOutputError("invalid_document_identity")
    window_for_date(document["window"]["date"])
    markdown = f"<!-- digest-identity: {document['input_identity']} -->\n" + render_digest(document)
    metadata = {**document, "markdown_sha256": hashlib.sha256(markdown.encode("utf-8")).hexdigest()}
    sidecar = json.dumps(metadata, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
    output_dir = Path(output_dir)
    md_path, meta_path = _paths(output_dir, document["window"]["date"])
    if md_path.is_dir() or meta_path.is_dir():
        raise DigestOutputError("invalid_output_target")
    output_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_text(md_path, markdown)
    atomic_write_text(meta_path, sidecar)
    verified = verify_digest_pair(md_path, meta_path)
    if verified["input_identity"] != document["input_identity"]:
        raise DigestOutputError("digest_pair_changed")
    return md_path, meta_path


def _nonnegative_int(value):
    try:
        result = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("limit must be a nonnegative integer") from None
    if result < 0:
        raise argparse.ArgumentTypeError("limit must be a nonnegative integer")
    return result


def _penalty(value):
    try:
        result = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError("penalty must be finite and nonnegative") from None
    if not math.isfinite(result) or result < 0:
        raise argparse.ArgumentTypeError("penalty must be finite and nonnegative")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate a local offline AI-news digest.")
    parser.add_argument("--date", help="Taipei issue date YYYY-MM-DD (default: today)")
    parser.add_argument("--input-dir", type=Path, required=True, help="directory containing archive.json")
    parser.add_argument("--output-dir", type=Path, default=Path.home() / "Downloads" / "ai-news-radar-digests")
    parser.add_argument("--limit", type=_nonnegative_int, default=20)
    parser.add_argument("--same-source-penalty", type=_penalty, default=0.03)
    args = parser.parse_args(argv)
    try:
        window = window_for_date(args.date)
    except DigestTimeError:
        parser.error("date must be a valid YYYY-MM-DD calendar date")
    try:
        output = args.output_dir.resolve()
        project = Path(__file__).resolve().parents[1]
        protected = (args.input_dir.resolve(), project / "data", project / "item")
        if any(output == path or path in output.parents for path in protected):
            parser.error("output directory must be outside inputs and project data/item")
        snapshot = load_digest_input(args.input_dir)
        document = build_digest_document(snapshot, window, limit=args.limit,
                                         same_source_penalty=args.same_source_penalty)
        write_digest(document, output)
    except Exception:
        # Never replay arbitrary filesystem/payload/provider exception text.
        print("digest_generation_failed: output may be incomplete; rerun and verify the pair", file=sys.stderr)
        return 1
    print(f"digest_generated: {window.date} {document['input_identity']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
