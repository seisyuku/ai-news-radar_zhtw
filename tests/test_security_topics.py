"""Security topic, event evidence, public copies and retired source boundary."""
import json
from pathlib import Path

import pytest

from scripts import security_topics as security, update_news as news
from tests.test_signal_integration import generation, read, browser_result


@pytest.mark.parametrize("title,summary,topic,event", [
    ("Codex prompt injection flaw allows unauthorized access", "", True, True),
    ("OpenAI patches ChatGPT vulnerability", "", True, True),
    ("AI加快漏洞發現，CSA提出VulnOps模式改善企業漏洞管理", "", True, False),
    ("恶意Markdown指引文件诱使Codex安装恶意软件包", "", True, True),
    ("中國駭客利用DeepSeek AI攻擊超過200個組織", "", True, True),
    ("AI Security Agents Compared: Claude, Codex, Mantis, Cloudflare", "", True, False),
    ("Chinese Hackers Use DeepSeek AI to Target More Than 200 Organizations", "", True, True),
    ("AI vulnerability management", "AI加快漏洞發現速度，但企業測試修補程式及部署更新仍需要時間。", True, False),
    ("AI Halloween exploit costume", "", False, False),
    ("AI security agent comparison", "Researchers evaluated detection results and limitations.", True, False),
    ("AI網路安全研究", "研究提出防禦方法，實驗結果顯示偵測率提高。", True, False),
    ("AI安全代理比較：Claude、Codex、Mantis", "", True, False),
    ("PHP CVE-2026-12345", "", False, True),
    ("AI security", "", False, False),
    ("AI安全研究", "研究模型對齊與有害內容的安全評估。", False, False),
    ("AI cybersecurity research", "", False, False),
    ("AI company update", "Last year Codex vulnerability was patched.", False, False),
    ("AI vulnerability", "", False, False),
    ("Last-minute Halloween costumes for tech nerds", "Just be a cute AI agent icon or a PHP vulnerability.", False, False),
    ("社群安全報告與青少年的新保護措施", "OpenAI introduces parental controls and content safety.", False, False),
    ("騰訊舉辦AI黑客松活動", "", False, False),
    ("OpenAI denies a data breach", "No confirmed vulnerability was discovered.", False, False),
    ("OpenAI並未發現漏洞或資料外洩", "", False, False),
    ("How to jailbreak an AI agent", "Step-by-step prompt injection tutorial.", False, False),
    ("Qwen model weights released", "", False, False),
    ("Cloud platform outage", "The platform was offline for four days.", False, False),
    ("AI product launches", "Related articles: Codex vulnerability permits remote code execution.", False, False),
    ("ChatGPT teen protections", "OpenAI also patched a Codex vulnerability allowing remote code execution.", True, True),
    ("AI hackathon", "Researchers disclosed a prompt injection flaw allowing unauthorized access.", True, True),
])
def test_native_material_boundaries(title, summary, topic, event):
    result = security.classify({"title": title, "summary": summary})
    assert (result.topic, result.event) == (topic, event)


def test_generated_or_translated_text_cannot_supply_security_evidence():
    row = {"title": "Qwen model released", "summary": "New model weights.",
           "title_zh": "Codex漏洞修補", "summary_zh": "AI prompt injection discovered",
           "news_summary": "AI exploit disclosed", "security_topic": True}
    assert security.classify(row) == security.SecurityDecision()
    assert security.annotate(row)["security_topic"] is False
    # Prefer native title_original over the bilingual display title.
    assert security.classify({**row, "title_original": row["title"],
                              "title": "AI vulnerability disclosed"}) == security.SecurityDecision()


def test_platform_exception_does_not_admit_generic_non_ai_security():
    row = {"title": "Deployment platform patches authentication bypass vulnerability"}
    assert security.classify(row) == security.SecurityDecision(False, True)
    assert security.classify(row, platform_admitted=True) == security.SecurityDecision(True, True)


@pytest.mark.parametrize("title", ["雲端部署平台憑證外洩", "n8n intrusion reported", "應用託管平台遭入侵"])
def test_existing_major_platform_security_exception_keeps_topic_and_badge(title):
    row = {"title": title, "summary": "", "site_id": "tw_media", "source": "iThome",
           "url": "https://www.ithome.com.tw/news/180000"}
    platform = news.platform_event_decision(row)
    assert platform.admitted and "security" in platform.events
    assert security.classify(row, platform_admitted=True) == security.SecurityDecision(True, True)
    assert news.add_reader_source_policy_fields(row)["security_topic"] is True
    assert "security" in news.business_event_score(row)


def test_security_topic_does_not_create_business_event_or_erase_genuine_event():
    assert news.business_event_score({"title": "AI security agent comparison"}) == []
    assert "security" in news.business_event_score({"title": "AI hackathon",
        "summary": "Codex vulnerability permits remote code execution."})
    assert news.business_event_score({"title": "Halloween AI costume", "summary": "A PHP vulnerability."}) == []


def test_generation_carries_topic_through_public_copies_and_cannot_call_retired_sources(generation, monkeypatch):
    output, calls, _, _ = generation
    payload = read(output, "archive.json")
    payload["items"][0].update(title="Codex vulnerability permits remote code execution",
        summary="OpenAI disclosed a use-after-free flaw. Unauthenticated attackers can execute arbitrary code.",
        business_events=["security"])
    (output / "archive.json").write_text(json.dumps(payload))
    # These are inert legacy settings, not real credentials. The real main
    # flow may call only the existing price sensor in the fixture.
    for prefix, key in [("X_API", "X_BEARER_TOKEN"), ("SOCIALDATA", "SOCIALDATA_API_KEY"), ("TIKHUB", "TIKHUB_API_KEY")]:
        monkeypatch.setenv(prefix + "_ENABLED", "1")
        monkeypatch.setenv(prefix + "_FORCE_RUN", "1")
        monkeypatch.setenv(key, "retired-test-credential")
    legacy_state = b'{"schema_version":1,"sources":{"historical":"keep"}}'
    (output / "paid-source-state.json").write_bytes(legacy_state)
    assert news.main() == 0
    assert browser_result(output)["ready"] is True
    rid = payload["items"][0]["id"]
    copies = []
    def visit(value):
        if isinstance(value, dict):
            if value.get("id") == rid and value.get("title"):
                copies.append(value)
            for v in value.values():
                visit(v)
        elif isinstance(value, list):
            for v in value:
                visit(v)
    for name in ["archive.json", "latest-24h.json", "latest-24h-all.json", "stories-merged.json", "daily-brief.json", "llm-radar.json", f"items/{rid}.json"]:
        visit(read(output, name))
    assert len(copies) >= 10
    assert all(r.get("security_topic") is True for r in copies)
    assert (output.parent / "item" / rid / "index.html").is_file()
    assert (output / "paid-source-state.json").read_bytes() == legacy_state
    status = read(output, "source-status.json")
    assert not {"x_api", "socialdata", "tikhub", "empty_advanced_sources"} & status.keys()
    assert not {"x_api", "socialdata", "tikhub"} & status["metrics"]["phases"].keys()
    assert status["failed_sites"] == []
    assert len(calls) == 1


def test_retired_workflow_and_frontend_entrypoints_are_absent():
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github/workflows/update-news.yml").read_text()
    for term in ["force_tikhub", "X_BEARER_TOKEN", "SOCIALDATA_API_KEY", "TIKHUB_API_KEY"]:
        assert term not in workflow
