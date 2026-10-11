"""The same digest pair verification for filesystem and object-storage bytes."""

import hashlib
import json
import re

if __package__:
    from .digest_json import document_identity
else:
    from digest_json import document_identity


def verify_digest_bytes(markdown: bytes, metadata_bytes: bytes):
    if not isinstance(markdown, bytes) or not isinstance(metadata_bytes, bytes):
        raise ValueError("digest_pair_invalid")
    metadata = json.loads(metadata_bytes.decode("utf-8"))
    match = re.match(rb"<!-- digest-identity: ([0-9a-f]{64}) -->\n", markdown)
    if (not isinstance(metadata, dict) or not match
            or match.group(1).decode() != metadata.get("input_identity")
            or hashlib.sha256(markdown).hexdigest() != metadata.get("markdown_sha256")
            or document_identity(metadata) != metadata.get("input_identity")):
        raise ValueError("digest_pair_mismatch")
    return metadata
