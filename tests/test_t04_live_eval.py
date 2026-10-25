from scripts.t04_live_eval import main, paced, safe_report


def test_paced_provider_calls_are_spaced_even_after_failure():
    now = [0.0]
    starts = []

    def clock():
        return now[0]

    def sleep(seconds):
        now[0] += seconds

    def generate(_prompt, _case):
        starts.append(now[0])
        if len(starts) == 1:
            raise RuntimeError("synthetic failure")
        return "ok"

    call = paced(generate, 10, monotonic=clock, sleep=sleep)
    try:
        call("synthetic", {})
    except RuntimeError:
        pass
    assert call("synthetic", {}) == "ok"
    assert starts == [0.0, 10.0]


def test_safe_report_discards_provider_text_and_error_message():
    report = {
        "provider": "gemini",
        "counts": {"generated": 0, "failed": 1, "insufficient_context": 0},
        "results": [{
            "id": "synthetic-case", "status": "failed", "summary": "sensitive output",
            "validation": {"errors": ["missing_required:synthetic term"], "text": "sensitive output"},
            "provider_error": {"http_status": 429, "message": "sensitive provider text"},
        }],
    }
    result = safe_report(report)
    assert result["cases"] == [{"id": "synthetic-case", "status": "failed",
                                "error_codes": ["missing_required"], "http_status": 429}]
    assert "sensitive" not in str(result)


def test_missing_credentials_make_no_provider_calls(monkeypatch, capsys):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    assert main([]) == 2
    assert "missing_credentials" in capsys.readouterr().out
