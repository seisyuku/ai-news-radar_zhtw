# Archive and resolver I/O contract

`scripts/archive_output.py` owns validated archive loading, single-file text
replacement, JSON/HTML item resolvers and resolver retention cleanup. It uses
only the Python standard library and never imports `update_news` or source
adapters. `update_news.py` remains the CLI and generation coordinator.

## Record and file shapes

| Shape | Contract |
| --- | --- |
| `ArchiveRecord` | A `TypedDict` describing known generated fields. `id` is required; source/title/URL, timestamps, summary and AIBASE language/alias metadata are optional. Historical and extension keys remain in the underlying dictionaries. |
| `Archive` | Internal `dict[item_id, ArchiveRecord]`. Loading a legacy keyed archive makes the key authoritative for the record's `id`. |
| `ArchiveSnapshot` | Canonical generated JSON has `generated_at`, `total_items` and an `items` list. Loading also accepts a legacy `items` object keyed by ID. |
| `PublicItemResolver` | The public archive record, including extension fields after sanitization; an alias of `ArchiveRecord`, not a separate item schema. JSON filename, lookup key and record `id` agree. |

Annotations describe generated records; they do not impose new validation on
old optional fields or remove extension keys. The loader retains the existing
checks: root object with `items`, dictionary records and non-empty string IDs;
duplicate IDs in list input fail. A missing archive permits first generation;
malformed/unreadable existing input raises before the main fetch/output phase.
The loader accepts historical non-hex IDs; resolver writers accept only
40-character hexadecimal keys, as before.

## Module API and policy boundary

| API | Behavior |
| --- | --- |
| `load_archive(path, *, normalize_record)` | Validate the existing input structure, then apply the supplied record identity policy. |
| `archive_from_payload(payload, *, normalize_record, label="archive")` | Apply the same structural/ID validation and identity policy to an already decoded payload; no file access. The path loader delegates here after its existing read/decode step. |
| `atomic_write_text(path, text)` | UTF-8 text to a same-directory temporary file, close, then replace. The target directory must already exist. |
| `write_item_resolvers(output_dir, archive, *, sanitize_record, prune=True)` | Write `output_dir/items/<id>.json`, using the supplied public policy, and return the valid ID count. |
| `write_item_html_adapters(output_dir, archive, *, sanitize_record, prune=True)` | Write `output_dir.parent/item/<id>/index.html` from the same record, escaping displayed fields/links, and return the valid ID count. |
| `prune_item_outputs(output_dir, archive, *, json_resolvers=True, html_adapters=True)` | Apply the existing valid-filename cleanup rules against the already-retained archive. |

Normalization and sanitization are required keyword arguments on the module's
policy-dependent APIs. Production callers use the compatibility wrappers in
`update_news`: those pass `normalize_reader_source_identity` and
`sanitize_public_payload` respectively, preserving AIBASE migration and public
redaction. Existing `update_news.load_archive`, `write_item_resolvers` and
`write_item_html_adapters` signatures remain available. `atomic_write_text` and
`prune_item_outputs` are also re-exported there.

Dependency direction is `update_news -> archive_output -> standard library`.
Policies are invoked as callables; the I/O module does not look them up by
importing the generator. Package imports (`scripts.archive_output`) and direct
script imports (`archive_output` from the scripts directory) both work.

The digest loader captures each of its three input files once, decodes those
bytes, and calls `archive_from_payload`; it never reopens the archive to validate
another generation. This adds an input entrypoint, not a second archive validator.
The path loader still treats a missing file as first generation and preserves
its existing errors. The digest separately makes missing archive input fatal.

## Retained behavior and boundaries

JSON resolver serialization remains `ensure_ascii=False, indent=2`; HTML keeps
its existing structure and trailing newline. The main coordinator retains the
serialization options for all other snapshots/state/caches. Source status is
published last, before cleanup, to include observed output duration.
Standalone writers prune after their own writes succeed. Main passes
`prune=False` to both and cleans up only after all snapshot, resolver, state and
optional cache writes succeed.

The existing last-seen archive retention policy, raw-item merge, stable IDs,
AIBASE language/alias handling, metadata promotion and timestamp parsing remain
in `update_news.py`. Source adapters, ranking, translation and health policies
also stay there. This extraction does not change their semantics or move them
into the I/O layer.

Atomic replacement remains per file; later failures do not roll back earlier
complete replacements. Cleanup is not transactional, and there is no power-loss
durability guarantee. See [Operations](OPERATIONS.md#generated-file-replacement-and-resolver-cleanup).
