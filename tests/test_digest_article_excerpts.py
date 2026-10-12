from copy import deepcopy
import json

import pytest

from scripts import digest_article_excerpts as excerpts


URL = "https://technews.tw/2026/10/11/example-article"
CANONICAL = URL + "/"
PARAGRAPH = "公司宣布推出新的 AI 自動實驗室，協助研究人員改善工作流程。"


def candidate(url=URL, summary="公司宣布推出新的 AI 自動實驗室 […]"):
    return {"primary_url": url, "primary_item_id": "one", "summary": summary,
            "summary_original": summary, "summary_kind": "publisher_translation",
            "summary_translation": {"key": summary}, "sources": [{"summary": summary}]}


def test_extracts_complete_first_paragraph_ignores_description_caption_and_scripts():
    page = f'''<meta property="og:description" content="摘要 […]">
    <div class="entry-content"><figure><p>圖片說明。</p></figure>
    <p><img src="photo.jpg"></p><p>{PARAGRAPH}<script>bad()</script></p>
    <p>第二段包含其他數據。</p></div>'''
    assert excerpts.first_paragraph(page) == PARAGRAPH


def test_does_not_truncate_long_first_paragraph_or_append_other_paragraphs():
    text = "完整句子。" * 200
    assert excerpts.first_paragraph(f'<div class="entry-content"><p>{text}</p><p>其他內容。</p></div>') == text


def test_inline_links_preserve_chinese_text_without_artificial_spaces():
    page = '<div class="entry-content"><p>公司<a href="x">宣布</a>推出 <strong>AI</strong>產品。</p></div>'
    assert excerpts.first_paragraph(page) == "公司宣布推出 AI產品。"


@pytest.mark.parametrize("page", ["<p>錯誤頁。</p>", '<div class="entry-content"><p>摘要 […]</p></div>', '<div class="entry-content"><p><img src="x"></p></div>'])
def test_missing_or_already_truncated_body_is_not_claimed_complete(page):
    with pytest.raises(ValueError):
        excerpts.first_paragraph(page)


@pytest.mark.parametrize("url", ["https://example.com/article", "https://technews.tw.evil.example/2026/10/11/a", "http://technews.tw/2026/10/11/a", "https://technews.tw/feed/", "https://user:password@technews.tw/2026/10/11/a"])
def test_other_hosts_non_articles_and_credentials_are_rejected(url):
    assert excerpts.article_url(url) is None


def test_main_and_security_subdomain_are_supported():
    assert excerpts.article_url(URL) == CANONICAL
    assert excerpts.article_url(URL.replace("technews.tw", "infosecu.technews.tw")) is not None


def test_reads_only_selected_clipped_technews_and_caches_for_repeat(tmp_path):
    calls = []
    def fetch(url):
        calls.append(url)
        return PARAGRAPH
    rows = [candidate(), candidate("https://example.com/a"), candidate(summary="完整的既有摘要。")]
    cache = tmp_path / "cache.json"
    capture, status = excerpts.capture_excerpts(rows, cache, fetcher=fetch)
    assert calls == [CANONICAL]
    assert status == {"fetched": 1, "cache_hits": 0}
    repeated, status = excerpts.capture_excerpts(rows, cache, fetcher=lambda url: pytest.fail("repeat fetched"))
    assert capture == repeated and status == {"fetched": 0, "cache_hits": 1}
    assert "html" not in json.loads(cache.read_text())


def test_receipt_replay_preserves_input_rss_and_other_candidates(tmp_path, monkeypatch):
    rows = [candidate(), candidate("https://example.com/a")]
    original = deepcopy(rows)
    captured, _ = excerpts.capture_excerpts(rows, tmp_path / "cache.json", fetcher=lambda url: PARAGRAPH)
    monkeypatch.setattr(excerpts.requests, "get", lambda *a, **k: pytest.fail("replay requested network"))
    output = excerpts.apply_excerpts(rows, captured)
    assert rows == original and output[1] == rows[1]
    assert output[0]["summary"] == output[0]["summary_original"] == PARAGRAPH
    assert output[0]["summary_translation"] is None
    assert output[0]["sources"] == rows[0]["sources"]
    assert output[0]["summary_origin"]["url"] == CANONICAL
    assert output == excerpts.apply_excerpts(rows, deepcopy(captured))


def test_failed_fetch_is_title_only_and_does_not_block_other_news(tmp_path):
    def fail(url):
        raise requests_error()
    captured, status = excerpts.capture_excerpts([candidate()], tmp_path / "cache.json", fetcher=fail)
    output = excerpts.apply_excerpts([candidate()], captured)
    assert output[0]["summary"] is None and output[0]["summary_kind"] == "none"
    assert status == {"fetched": 1, "cache_hits": 0}
    assert "secret" not in json.dumps(captured)


def requests_error():
    return RuntimeError("secret raw error")


def test_selection_bound_and_duplicate_url_do_not_cause_extra_requests(tmp_path):
    with pytest.raises(ValueError, match="excerpt_selection_limit"):
        excerpts.capture_excerpts([candidate()] * 11, tmp_path / "cache.json")
    captured, status = excerpts.capture_excerpts([candidate(), candidate()], tmp_path / "cache.json", fetcher=lambda url: PARAGRAPH)
    assert len(captured["entries"]) == status["fetched"] == 1


def test_old_extractor_cache_is_not_reused(tmp_path):
    path = tmp_path / "cache.json"
    path.write_text(json.dumps({"extractor_version": "old-extractor", "entries": {CANONICAL: "舊內容。"}}))
    captured, status = excerpts.capture_excerpts([candidate()], path, fetcher=lambda url: PARAGRAPH)
    assert status["fetched"] == 1 and captured["entries"][CANONICAL]["text"] == PARAGRAPH


def test_captured_excerpt_renders_with_existing_digest_and_keeps_provenance(tmp_path):
    from scripts.digest_render import render_digest
    from scripts.digest_json import document_identity
    row = {**candidate(), "title": "AI 自動實驗室", "primary_published_at": "2026-10-11T07:00:00Z"}
    capture, _ = excerpts.capture_excerpts([row], tmp_path / "cache.json", fetcher=lambda url: PARAGRAPH)
    document = {"window": {"date": "2026-10-12", "start_utc": "2026-10-10T22:00:00Z", "end_utc": "2026-10-11T22:00:00Z"},
                "candidates": excerpts.apply_excerpts([row], capture), "article_excerpts": capture}
    output = render_digest(document)
    assert PARAGRAPH in output
    changed = deepcopy(document)
    changed["article_excerpts"]["entries"][CANONICAL]["text"] = "不同的來源內容。"
    assert document_identity(document) != document_identity(changed)


def test_external_redirect_is_rejected_before_following(monkeypatch):
    calls = []
    class Response:
        status_code = 302
        headers = {"Location": "https://other.example/article"}
        def __enter__(self): return self
        def __exit__(self, *args): pass
    def get(url, **kwargs):
        calls.append(url)
        assert kwargs["allow_redirects"] is False
        return Response()
    monkeypatch.setattr(excerpts.requests, "get", get)
    with pytest.raises(ValueError, match="article_redirect_invalid"):
        excerpts.fetch_paragraph(URL)
    assert calls == [CANONICAL]


def test_page_size_bound_prevents_large_body_parsing(monkeypatch):
    class Response:
        status_code = 200
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def raise_for_status(self): pass
        def iter_content(self, chunk_size): yield b"x" * (excerpts.MAX_PAGE_BYTES + 1)
    monkeypatch.setattr(excerpts.requests, "get", lambda *a, **k: Response())
    with pytest.raises(ValueError, match="article_page_too_large"):
        excerpts.fetch_paragraph(URL)
