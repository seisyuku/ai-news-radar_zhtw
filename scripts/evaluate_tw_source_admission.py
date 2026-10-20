#!/usr/bin/env python3
"""Isolated, opt-in Taiwan source probes and offline admission review.

Never imported by the generator. Only publisher metadata/short feed descriptions
are retained; no article pages, full-content fields, bridges, credentials or LLMs.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import time
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

UTC = timezone.utc
ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = "RadarSourceAdmission/1.0 (+https://github.com/seisyuku/ai-news-radar_zhtw)"
SOURCES = (
    {"source_id": "informationsecurity", "publisher": "資安人科技網",
     "home": "https://www.informationsecurity.com.tw/", "group": "informationsecurity",
     "hosts": ["www.informationsecurity.com.tw"], "probes": ["/rss.xml", "/rss.aspx"]},
    {"source_id": "cyberq", "publisher": "CyberQ 賽博客", "home": "https://cyberq.tw/",
     "group": "cyberq", "hosts": ["cyberq.tw"], "probes": ["/feed/"]},
    {"source_id": "netadmin", "publisher": "網管人", "home": "https://www.netadmin.com.tw/",
     "group": "netadmin", "hosts": ["www.netadmin.com.tw"], "probes": ["/feed/"]},
    {"source_id": "digitimes_tw", "publisher": "DIGITIMES 電子時報",
     "home": "https://www.digitimes.com.tw/", "group": "digitimes",
     "hosts": ["www.digitimes.com.tw"], "probes": ["/tech/rss/rss.asp"]},
    {"source_id": "meet", "publisher": "Meet 創業小聚", "home": "https://meet.bnext.com.tw/",
     "group": "bnext_media", "hosts": ["meet.bnext.com.tw"],
     "probes": ["/feed", "/feed.xml", "/articles/rss"]},
)
AI = re.compile(r"(?i)(?<![a-z0-9])(?:ai|llm|agents?|agentic|rag|openai|claude|gemini|deepseek|chatgpt|opencode|codex|flux|minimax|gpt[- ]?\d)(?![a-z0-9])|人工智[慧能]|大[語语]言模型|生成式|機器學習|算力")
EXCLUSIONS = (
    ("roundup", r"產業精選|趨勢[周週]報|每日[彙汇]整|今日重點|DIGITIMES Today|daily roundup|weekly digest"),
    ("tutorial_or_evergreen", r"教學|指南|入門(?!檻)|攻略|懶人包|怎麼|如何|實戰|用 AI 來|\bhow to\b|tutorial|step.by.step"),
    ("hardware_review", r"開箱|選購|\bNAS\b|路由器|交換器"),
    ("sponsored", r"業配|廣編|合作推廣|贊助內容|新聞稿|sponsored|advertorial|press release"),
    ("proposal_or_forecast", r"倡議|呼籲|擬議|擬管制|提案|預測|傳出|恐介入|有望|可望|計[劃畫]|預計|可能|rumou?r|forecast|plans? to|could |may "),
)
EVENT = re.compile(r"(?i)發布|發表|推出|釋出|上市|開源|上線|調[降漲整]|降價|漲價|生效|募資|融資|收購|併購|停[業運]|關閉|遇駭|遭[駭攻]|漏洞|攻擊|外洩|[實实]測|採用|導入|營收|訂單|投資|動工|啟用|launch|releas|funding|acquir|breach|CVE-\d|benchmark")
EVIDENCE = re.compile(r"(?i)實測|測試資料|獨家專訪|採訪|原始數據|independent test|interview|dataset")


def iso(dt):
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def timestamp(value):
    """Require a complete date and explicit timezone; never fill in fetch time."""
    complete_date = r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}(?!\d)|\b\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}\b|\b[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}\b"
    if not value or not re.search(complete_date, str(value)):
        return None
    try:
        dt = dateparser.parse(str(value), default=datetime(1900, 1, 1))
        if dt.tzinfo is None or dt.utcoffset() is None or dt.year == 1900:
            return None
        return dt.astimezone(UTC)
    except (ValueError, TypeError, OverflowError):
        return None


def canonical_url(value):
    try:
        p = urlsplit(str(value or ""))
        if p.scheme not in {"https", "http"} or not p.hostname or re.search(r"\s", p.hostname) or p.username or p.password:
            return ""
        _ = p.port  # Reject malformed/out-of-range ports as unusable metadata.
        query = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
                 if not k.lower().startswith("utm_") and k.lower() not in {"fbclid", "gclid"}]
        return urlunsplit((p.scheme, p.netloc.lower(), p.path or "/", urlencode(query), ""))
    except ValueError:
        return ""


def plain(text, limit=800):
    if not re.search(r"<[/!?A-Za-z]", text or ""):
        return re.sub(r"\s+", " ", html.unescape(text or ""))[:limit].strip()
    soup = BeautifulSoup(text or "", "html.parser")
    for node in soup.select("script, style, iframe, object"):
        node.decompose()
    return re.sub(r"\s+", " ", soup.get_text(" ", strip=True))[:limit].strip()


def parse_feed(content, source, feed_url, max_entries=50):
    """Strict RSS/Atom XML, including bad entry diagnostics and valid-empty feeds."""
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        raise ValueError("invalid_xml") from exc
    kind = root.tag.split("}")[-1].lower()
    if kind not in {"rss", "rdf", "feed"} or (kind == "rss" and root.find("channel") is None):
        raise ValueError("not_rss_or_atom")
    nodes = [n for n in root.iter() if n.tag.split("}")[-1] in {"item", "entry"}]
    articles = []
    for index, node in enumerate(nodes[:max_entries]):
        fields = {child.tag.split("}")[-1]: child for child in node}

        def value(*names):
            return next(("".join(fields[n].itertext()).strip() for n in names if n in fields), "")

        links = [n for n in node if n.tag.split("}")[-1] == "link"
                 and n.get("rel", "alternate") == "alternate"]
        link = next((n.get("href") or n.text or "" for n in links), "")
        date = value("pubDate", "published", "date")  # updated is not publication
        dt = timestamp(date)
        title, url = plain(value("title"), 400), canonical_url(urljoin(feed_url, link)) if link else ""
        invalid = "missing_title" if not title else "missing_url" if not url else "missing_or_ambiguous_time" if dt is None else None
        articles.append({"source_id": source["source_id"], "publisher": source["publisher"],
                         "publisher_group": source["group"], "title": title,
                         "canonical_url": url, "canonical_method": "feed_alternate_link_unverified",
                         "published_at": iso(dt) if dt else None, "published_at_raw": date,
                         "summary_if_provided": plain(value("description", "summary")),
                         "feed_url": feed_url, "retrieval_status": "invalid_metadata" if invalid else "ok",
                         "filter_reason": invalid, "entry_index": index})
    return articles, {"entry_count": len(nodes), "sampled_entries": len(articles),
                      "truncated": len(nodes) > max_entries,
                      "status": "invalid_fields" if nodes and not any(a["retrieval_status"] == "ok" for a in articles) else "valid_feed" if nodes else "valid_empty"}


class ProbeClient:
    """Fixed publisher host boundary, robots checks and bounded HTTP without retries."""
    def __init__(self, hosts, session=None, pause=time.sleep):
        self.hosts, self.session, self.pause = hosts, session or requests.Session(), pause
        self.session.trust_env = False  # No ambient .netrc credentials or auth proxies.
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.robots, self.last, self.stopped, self.requests = {}, {}, set(), []

    def allowed(self, url):
        return bool(canonical_url(url)) and urlsplit(url).hostname in self.hosts

    def request(self, url, *, robots=False):
        started = time.monotonic()
        row = {"url": url, "http_status": None, "status": "not_attempted", "hops": []}
        self.requests.append(row)
        body = b""
        try:
            for _ in range(4):
                host = urlsplit(url).hostname
                if not self.allowed(url):
                    row["status"] = "outside_publisher_hosts"
                    break
                if host in self.stopped:
                    row["status"] = "origin_stopped"
                    break
                if not robots:
                    if host not in self.robots:
                        self.load_robots(url)
                    policy = self.robots[host]
                    if policy is None or not policy.can_fetch(USER_AGENT, url):
                        row["status"] = "robots_blocked_or_unavailable"
                        break
                delay = 1
                policy = self.robots.get(host)
                if policy:
                    rate = policy.request_rate(USER_AGENT)
                    delay = max(delay, policy.crawl_delay(USER_AGENT) or 0,
                                rate.seconds / rate.requests if rate and rate.requests else 0)
                if delay > 30:
                    row["status"] = "crawl_delay_requires_manual_run"
                    break
                self.pause(max(0, delay - (time.monotonic() - self.last.get(host, 0))))
                self.last[host] = time.monotonic()
                with self.session.get(url, timeout=(8, 12), allow_redirects=False, stream=True) as response:
                    row.update(http_status=response.status_code, final_url=url,
                               content_type=response.headers.get("Content-Type", ""))
                    row["hops"].append({"url": url, "http_status": response.status_code,
                                        "location": response.headers.get("Location")})
                    if response.status_code in {401, 403, 429}:
                        self.stopped.add(host)
                    if response.is_redirect:
                        url = urljoin(url, response.headers.get("Location", ""))
                        continue
                    chunks, size = [], 0
                    for chunk in response.iter_content(65536):
                        size += len(chunk)
                        if size > 2_000_000:
                            row["status"] = "response_too_large"
                            break
                        chunks.append(chunk)
                    else:
                        body = b"".join(chunks)
                        row.update(status="ok" if response.status_code == 200 else "http_error",
                                   bytes=size, sha256=hashlib.sha256(body).hexdigest())
                    break
            else:
                row["status"] = "redirect_limit"
        except requests.RequestException as exc:
            row["status"] = type(exc).__name__  # no exception strings/cookies
        row["duration_ms"] = round((time.monotonic() - started) * 1000)
        return body, row

    def load_robots(self, url):
        host = urlsplit(url).hostname
        body, row = self.request(urljoin(url, "/robots.txt"), robots=True)
        parser = RobotFileParser()
        if row["status"] == "ok" and not re.search(br"(?i)<(?:!doctype|html)\b", body[:512]):
            parser.parse(body.decode("utf-8", errors="replace").splitlines())
        elif row["http_status"] in {404, 410}:
            parser.parse(["User-agent: *", "Disallow:"])
        else:
            self.robots[host] = None
            return
        self.robots[host] = parser


def discover(content, url):
    soup = BeautifulSoup(content, "html.parser")
    feeds, pages, legal = [], [], []
    for node in soup.select("a[href], link[href]"):
        href = urljoin(url, node["href"])
        label = node.get_text(" ", strip=True)
        mime = node.get("type", "").lower()
        if "rss" in mime or "atom" in mime or re.search(r"(?i)(?:/feed/?$|\.(?:rss|xml)$)", href):
            feeds.append(href)
        elif re.search(r"(?i)rss|atom", href) or label.upper() in {"RSS", "ATOM"}:
            pages.append(href)
        if re.search(r"條款|著作|授權|terms|copyright", label, re.I):
            legal.append({"url": href, "label": label[:100]})
    return list(dict.fromkeys(feeds)), list(dict.fromkeys(pages)), legal[:8]


def collect_source(source):
    client = ProbeClient(source["hosts"])
    body, home = client.request(source["home"])
    result = {**source, "articles": [], "feed_results": [], "requests": client.requests,
              "status": "restricted_unverified", "legal_status": "public_metadata_only_license_not_granted"}
    if home["status"] != "ok":
        return result
    feeds, pages, legal = discover(body, home["final_url"])
    result["legal_links"] = legal
    # One publisher RSS directory, at most six feed URLs. No pagination/articles.
    for page in pages[:1]:
        if client.allowed(page):
            content, row = client.request(page)
            if row["status"] == "ok":
                more, _, _ = discover(content, row["final_url"])
                feeds.extend(more)
    declared = set(feeds)
    result["discovered_feed_urls"] = list(dict.fromkeys(feeds))[:30]
    feeds.extend(urljoin(source["home"], p) for p in source["probes"])
    for url in list(dict.fromkeys(feeds))[:6]:
        if not client.allowed(url):
            continue
        content, row = client.request(url)
        if row["status"] != "ok":
            continue
        try:
            articles, status = parse_feed(content, source, row["final_url"])
            result["feed_results"].append({"url": url, "discovery": "publisher_link" if url in declared else "conventional_path_probe", **status})
            if status["status"] in {"valid_feed", "valid_empty"}:
                result.update(articles=articles, status="verified_native_feed")
                break
        except ValueError as exc:
            result["feed_results"].append({"url": url, "status": str(exc)})
    if result["status"] != "verified_native_feed":
        result["status"] = "restricted_unverified" if client.stopped or any(r["status"] not in {"ok", "http_error"} for r in client.requests) else "no_usable_feed_found"
    return result


def filter_article(article, now, days):
    if article["retrieval_status"] != "ok":
        return article["filter_reason"]
    dt = timestamp(article["published_at"])
    if not dt or dt > now or dt < now - timedelta(days=days):
        return "outside_observation_window"
    title, summary = article["title"], article["summary_if_provided"]
    text = title + " " + summary
    for reason, pattern in EXCLUSIONS:
        if re.search(pattern, text if reason == "sponsored" else title, re.I):
            return reason
    if not AI.search(text):
        return "no_ai_relation"
    if not EVENT.search(text):
        return "no_concrete_event_signal"
    return "candidate_requires_review"


def title_tokens(title):
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]", "", title.lower())
    return {text[i:i+3] for i in range(len(text)-2)}


def event_anchors(text):
    """Search hints only: product/entity plus event type, never semantic proof."""
    entities = set(re.findall(r"[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*", text.lower()))
    entities -= {"ai", "the", "new", "and", "for", "with", "from", "users", "after", "model",
                 "models", "agent", "agents", "software", "release", "launch", "announces"}
    entities = {e for e in entities if len(e) >= 3}
    kinds = set()
    for kind, pattern in {
        "security": r"(?i)遇駭|遭駭|入侵|攻擊|外洩|漏洞|金鑰|breach|intrusion|attack|key.exposure|hacker",
        "release": r"(?i)發布|推出|釋出|開源|release|launch|ships",
        "funding": r"(?i)募資|融資|funding|raises",
        "pricing": r"(?i)降價|漲價|定價|price|pricing",
        "shutdown": r"(?i)停業|停運|停止營運|shutdown|shut.down|closure",
    }.items():
        if re.search(pattern, text):
            kinds.add(kind)
    return entities, kinds


def possible_matches(article, baseline):
    tokens = title_tokens(article["title"])
    matches = []
    dt = timestamp(article["published_at"])
    entities, kinds = event_anchors(article["title"] + " " + article["summary_if_provided"])
    for item in baseline:
        other = timestamp(item.get("published_at"))
        if not other or abs((dt - other).total_seconds()) > 3 * 86400:
            continue
        bt = title_tokens(item.get("title", ""))
        overlap = len(tokens & bt) / max(1, len(tokens | bt))
        score = SequenceMatcher(None, article["title"].lower(), item.get("title", "").lower()).ratio()
        be, bk = event_anchors(item.get("title", "") + " " + item.get("summary", ""))
        shared = sorted(entities & be)
        if overlap >= .12 or score >= .48 or (shared and kinds & bk):
            matches.append({"url": canonical_url(item.get("url")), "title": item.get("title"),
                            "published_at": item.get("published_at"), "title_score": round(score, 3),
                            "shared_entities": shared, "shared_event_types": sorted(kinds & bk),
                            "trigram_score": round(overlap, 3), "status": "possible_event_manual_review"})
    ordered = sorted(matches, key=lambda m: (-bool(m["shared_entities"] and m["shared_event_types"]), -m["trigram_score"], -m["title_score"], m["url"]))
    unique = {m["url"]: m for m in reversed(ordered) if m["url"]}
    return [m for m in ordered if unique.get(m["url"]) is m][:3]


def evaluate(capture, baseline, *, days=7, reviews=None, coverage=None):
    now = timestamp(capture["generated_at"])
    if now is None:
        raise ValueError("capture_requires_timestamp")
    rows = baseline.get("items", [])
    urls = {canonical_url(i.get("url")): i for i in rows if canonical_url(i.get("url"))}
    reviews = reviews or []
    review_index = {canonical_url(r["canonical_url"]): r for r in reviews}
    if len(review_index) != len(reviews) or "" in review_index:
        raise ValueError("duplicate_or_invalid_review_url")
    bounds = tuple(timestamp(v) for v in coverage) if coverage else None
    if bounds and (None in bounds or bounds[0] > bounds[1] or bounds[1] > now):
        raise ValueError("invalid_baseline_coverage")
    report = {"schema_version": 1, "mode": "shadow_only", "generated_at": capture["generated_at"],
              "window_start": iso(now - timedelta(days=days)), "baseline_generated_at": baseline.get("generated_at"),
              "baseline_sha256": hashlib.sha256(json.dumps(baseline, sort_keys=True).encode()).hexdigest(),
              "baseline_coverage_asserted": list(coverage) if coverage else None,
              "limitations": ["Single capture is not a 7–14 day reliability study.",
                              "Feed alternate URLs are not verified HTML canonical URLs.",
                              "No match does not prove a novel event; event decisions require human evidence.",
                              "Publisher group bnext_media includes Meet and 數位時代; no corroboration credit."],
              "sources": []}
    used_reviews = set()
    for source in capture["sources"]:
        articles, seen = [], set()
        metrics = Counter()
        events = {"novel_event": set(), "duplicate_event": set()}
        raw = source["articles"]
        valid = [a for a in raw if a["retrieval_status"] == "ok"]
        for original in raw:
            a = dict(original)
            reason = filter_article(a, now, days)
            if reason == "candidate_requires_review" and a["canonical_url"] in seen:
                reason = "duplicate_within_feed"
            if reason == "candidate_requires_review":
                seen.add(a["canonical_url"])
            a.update(filter_reason=reason, comparison="excluded", matches=[])
            if reason == "candidate_requires_review":
                metrics["candidate_articles"] += 1
                url = a["canonical_url"]
                dt = timestamp(a["published_at"])
                aligned = bool(bounds and bounds[0] <= dt <= bounds[1])
                a["baseline_time_aligned"] = aligned
                a["possible_new_evidence"] = bool(EVIDENCE.search(a["title"] + " " + a["summary_if_provided"]))
                if url in urls:
                    a["comparison"] = "duplicate_url"
                    metrics["duplicate_url_count"] += 1
                else:
                    a["matches"] = possible_matches(a, rows)
                    a["comparison"] = "needs_event_review" if aligned else "baseline_window_unverified"
                review = review_index.get(url)
                if review:
                    used_reviews.add(url)
                    decision = review.get("decision")
                    if decision not in {"novel_event", "duplicate_event", "new_evidence", "false_positive"} or not str(review.get("reason", "")).strip():
                        raise ValueError("review_requires_valid_decision_and_reason")
                    if decision in {"duplicate_event", "new_evidence"} and canonical_url(review.get("baseline_url")) not in urls:
                        raise ValueError("review_requires_existing_baseline_url")
                    if decision == "novel_event" and (not aligned or url in urls):
                        raise ValueError("novel_event_requires_aligned_coverage_and_nonduplicate_url")
                    if decision in events and not review.get("event_id"):
                        raise ValueError("event_count_requires_review_event_id")
                    if url in urls and decision in {"duplicate_event", "new_evidence"}:
                        raise ValueError("same_url_is_not_independent_evidence")
                    a.update(comparison=decision, review=review)
                    metrics["reviewed_articles"] += 1
                    if decision in events:
                        events[decision].add(review["event_id"])
                    else:
                        metrics[decision + "_count"] += 1
                if a["comparison"] in {"needs_event_review", "baseline_window_unverified"}:
                    metrics["unresolved_articles"] += 1
            articles.append(a)
        for key, values in events.items():
            metrics[key + "_count"] = len(values)
        for key in ("candidate_articles", "duplicate_url_count", "duplicate_event_count", "novel_event_count",
                    "new_evidence_count", "false_positive_count", "reviewed_articles", "unresolved_articles"):
            metrics.setdefault(key, 0)
        # False positives are unknown until someone actually reviews the sample.
        if not metrics["reviewed_articles"]:
            metrics["false_positive_count"] = None
        metrics["fetched_articles"] = len(valid)
        metadata = {"denominator": len(raw), **{field: sum(bool(a.get(field)) for a in raw)
                    for field in ("title", "canonical_url", "published_at", "summary_if_provided")}}
        report["sources"].append({k: v for k, v in source.items() if k != "articles"} | {
            "metrics": dict(metrics), "metadata_quality": metadata, "articles": articles,
            "feed_reliability": dict(Counter(r["status"] for r in source.get("feed_results", []))),
            "cost_and_risk": {"http_request_count": sum(len(r.get("hops", [])) for r in source["requests"]),
                              "operation_count": len(source["requests"]),
                              "duration_ms": sum(r.get("duration_ms", 0) for r in source["requests"] if not r["url"].endswith("/robots.txt")),
                              "retries": 0, "article_page_requests": 0,
                              "license": "No redistribution permission inferred from RSS or robots."},
            "recommendation": "continue_shadow_review" if valid else "hold_no_verified_sample"})
    if set(review_index) != used_reviews:
        raise ValueError("review_url_not_in_current_candidate_sample")
    return report


def markdown(report):
    lines = ["# 台灣來源影子准入評估", "", f"觀察：{report['window_start']} ～ {report['generated_at']}",
             "", "單次採樣；所有事件／證據數須人工確認。未分類文章不等於新事件。", "",
             "| 來源 | 入口狀態 | 有效文章 | 候選 | 同URL | 同事件 | 新事件 | 新證據 | 待查 | 誤收/人工樣本 |",
             "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |"]
    for s in report["sources"]:
        m = s["metrics"]
        lines.append(f"| {s['publisher']} | {s['status']} | {m['fetched_articles']} | {m['candidate_articles']} | {m['duplicate_url_count']} | {m['duplicate_event_count']} | {m['novel_event_count']} | {m['new_evidence_count']} | {m['unresolved_articles']} | {m['false_positive_count']}/{m['reviewed_articles']} |")
    for s in report["sources"]:
        lines += ["", f"## {s['publisher']}", "", f"建議：{s['recommendation']}；發布群組：{s['group']}", ""]
        for r in s["requests"]:
            lines.append(f"- 探測 {r['url']} → HTTP {r['http_status']} / {r['status']}")
        for a in s["articles"]:
            title = a['title'].replace('|', '／').replace('\n', ' ')
            lines.append(f"- [{title}]({a['canonical_url']}) — {a['published_at']} / {a['filter_reason']} / {a['comparison']}")
            if a.get("review"):
                lines.append(f"  人工理由：{a['review']['reason']}")
            for match in a["matches"]:
                lines.append(f"  疑似同事件（待查）：{match['url']} — {match['title']}")
    lines += ["", "## 限制", ""] + [f"- {v}" for v in report["limitations"]]
    return "\n".join(lines) + "\n"


def external_output(path):
    path = Path(path).expanduser().resolve()
    if path == ROOT or ROOT in path.parents:
        raise ValueError("output_must_be_outside_repository")
    path.mkdir(parents=True, exist_ok=True)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--live", action="store_true", help="Explicit bounded network probe of five native publishers")
    mode.add_argument("--replay", type=Path, help="Offline capture.json; performs zero HTTP requests")
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--reviews", type=Path)
    parser.add_argument("--baseline-start", help="Human asserted complete baseline start, timezone required")
    parser.add_argument("--baseline-end", help="Human asserted complete baseline end, timezone required")
    parser.add_argument("--lookback-days", type=int, choices=range(1, 31), default=7)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = external_output(args.output_dir)
    if bool(args.baseline_start) != bool(args.baseline_end):
        parser.error("baseline-start and baseline-end must be provided together")
    baseline = json.loads(args.baseline.read_text())
    if args.live:
        capture = {"generated_at": iso(datetime.now(UTC)), "sources": []}
        for source in SOURCES:
            capture["sources"].append(collect_source(source))
            print(source["source_id"], capture["sources"][-1]["status"], flush=True)
    else:
        capture = json.loads(args.replay.read_text())
    reviews = json.loads(args.reviews.read_text()) if args.reviews else None
    coverage = (args.baseline_start, args.baseline_end) if args.baseline_start else None
    report = evaluate(capture, baseline, days=args.lookback_days, reviews=reviews, coverage=coverage)
    for name, data in (("capture.json", capture), ("baseline.json", baseline), ("report.json", report)):
        (output / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    (output / "REPORT.md").write_text(markdown(report))
    print(output / "REPORT.md")


if __name__ == "__main__":
    main()
