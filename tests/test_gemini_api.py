import json

import pytest
import requests

from scripts.gemini_api import generate_json


class Response:
    def json(self):
        return {"candidates": [{"content": {"parts": [{"text": '{"status":"ok"}'}]}}]}

    def raise_for_status(self):
        pass


class Session:
    def __init__(self, error=None):
        self.calls = []
        self.error = error

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if self.error:
            raise self.error
        return Response()


def test_generic_connector_preserves_json_schema_and_bounded_request():
    session = Session()
    schema = {"type": "OBJECT", "properties": {"status": {"type": "STRING"}}, "required": ["status"]}
    result = generate_json("caller-defined synthetic task", api_key="synthetic-key", schema=schema,
                           max_output_tokens=32, session=session)
    assert result == {"status": "ok"}
    url, call = session.calls[0]
    assert url.endswith("/models/gemini-3.5-flash-lite:generateContent")
    assert call["timeout"] == 60
    assert call["headers"]["x-goog-api-key"] == "synthetic-key"
    assert call["json"]["generationConfig"]["responseSchema"] == schema
    assert call["json"]["generationConfig"]["maxOutputTokens"] == 32
    assert "summary" not in json.dumps(call["json"])


def test_missing_key_and_invalid_limits_stop_before_network():
    session = Session()
    with pytest.raises(ValueError, match="missing_GEMINI_API_KEY"):
        generate_json("task", api_key="", schema={}, max_output_tokens=32, session=session)
    with pytest.raises(ValueError, match="positive_request_limits_required"):
        generate_json("task", api_key="synthetic-key", schema={}, max_output_tokens=0, session=session)
    assert session.calls == []


def test_timeout_is_reported_without_automatic_retry():
    session = Session(requests.ReadTimeout("synthetic"))
    with pytest.raises(requests.ReadTimeout):
        generate_json("task", api_key="synthetic-key", schema={}, max_output_tokens=32, session=session)
    assert len(session.calls) == 1
