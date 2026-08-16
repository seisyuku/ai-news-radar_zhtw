import json

from scripts.diagnose_gemini import classify_failure, diagnose_gemini, main


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code
        self._content = json.dumps(payload).encode()

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests

            error = requests.HTTPError(f"{self.status_code} error")
            error.response = self
            raise error


class FakeSession:
    def __init__(self, get_response, post_responses=()):
        self.get_response = get_response
        self.post_responses = list(post_responses)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append(("GET", url, kwargs))
        return self.get_response

    def post(self, url, **kwargs):
        self.calls.append(("POST", url, kwargs))
        return self.post_responses.pop(0)


def model_list(name="gemini-3.5-flash-lite"):
    return FakeResponse({
        "models": [{
            "name": f"models/{name}",
            "baseModelId": name,
            "supportedGenerationMethods": ["generateContent"],
        }]
    })


def generation(text):
    return FakeResponse({"candidates": [{"content": {"parts": [{"text": text}]}}]})


def test_missing_key_stops_before_network_and_returns_actionable_diagnosis():
    session = FakeSession(model_list())

    report = diagnose_gemini(api_key="", session=session)

    assert report["ok"] is False
    assert report["diagnosis"]["code"] == "missing_api_key"
    assert session.calls == []
    assert "GEMINI_API_KEY" in report["steps"][0]["reason"]


def test_success_probes_model_plain_and_structured_generation_without_groq():
    secret = "AIza_secret_must_never_appear_in_report"
    session = FakeSession(model_list(), [generation("OK"), generation('{"status":"ok"}')])

    report = diagnose_gemini(api_key=secret, session=session)

    assert report["ok"] is True
    assert report["diagnosis"]["code"] == "gemini_api_usable"
    assert [step["name"] for step in report["steps"]] == [
        "configuration", "model_discovery", "plain_generation", "structured_generation"
    ]
    assert [call[0] for call in session.calls] == ["GET", "POST", "POST"]
    assert all("temperature" not in call[2]["json"]["generationConfig"] for call in session.calls[1:])
    assert "groq" not in json.dumps(report).casefold()
    assert secret not in json.dumps(report)


def test_invalid_key_is_classified_from_nested_google_error_reason():
    response = FakeResponse({
        "error": {
            "code": 400,
            "message": "API key not valid",
            "status": "INVALID_ARGUMENT",
            "details": [{"reason": "API_KEY_INVALID"}],
        }
    }, 400)
    session = FakeSession(response)

    report = diagnose_gemini(api_key="not-valid", session=session)

    assert report["diagnosis"]["code"] == "invalid_api_key"
    assert report["steps"][-1]["name"] == "model_discovery"
    assert len(session.calls) == 1


def test_model_absence_reports_suggestions_and_does_not_generate():
    session = FakeSession(model_list("gemini-current-flash"))

    report = diagnose_gemini(api_key="test", model="gemini-retired", session=session)

    assert report["diagnosis"]["code"] == "model_not_found"
    assert report["steps"][-1]["error"]["suggested_models"] == ["gemini-current-flash"]
    assert len(session.calls) == 1


def test_structured_failure_is_separate_from_plain_generation_failure():
    structured_error = FakeResponse({
        "error": {"code": 400, "status": "INVALID_ARGUMENT", "message": "responseSchema is not supported"}
    }, 400)
    session = FakeSession(model_list(), [generation("OK"), structured_error])

    report = diagnose_gemini(api_key="test", session=session)

    assert report["diagnosis"]["code"] == "structured_output_incompatible"
    assert report["steps"][-2] == {"name": "plain_generation", "status": "passed"}
    assert report["steps"][-1]["name"] == "structured_generation"


def test_quota_and_permission_failures_have_distinct_codes():
    assert classify_failure({"http_status": 429, "provider_status": "RESOURCE_EXHAUSTED"}, stage="plain_generation")["code"] == "quota_or_rate_limit"
    assert classify_failure({"http_status": 403, "provider_status": "PERMISSION_DENIED"}, stage="plain_generation")["code"] == "permission_or_region_denied"


def test_cli_without_key_returns_two_and_writes_secret_safe_report(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    output = tmp_path / "gemini.json"

    assert main(["--output", str(output)]) == 2
    printed = json.loads(capsys.readouterr().out)
    saved = json.loads(output.read_text())
    assert printed == saved
    assert saved["diagnosis"]["code"] == "missing_api_key"
