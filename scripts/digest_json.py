"""Stable digest JSON and identity rules without generator/runtime imports."""

import hashlib
import json


def canonical_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def document_identity(document):
    material = {key: value for key, value in document.items()
                if key not in {"input_identity", "markdown_sha256"}}
    return hashlib.sha256(canonical_json(material).encode("utf-8")).hexdigest()
