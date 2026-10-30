"""Article revisions are history, not additional publisher evidence.

The archive keeps native records. Reader/event inputs use a deterministic
current version and suppress demonstrably stale pre-announcement summaries.
"""
from __future__ import annotations

import copy
import re
from collections import defaultdict

try:
    from scripts import evidence_policy
except ModuleNotFoundError:
    import evidence_policy
from datetime import datetime
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

PREVIEW = re.compile(r"\b(?:set to report|prepares? to report|will report|ahead of .{0,25}earnings|expected to report)\b|即將公布|即将公布|將公布財報|将公布财报", re.I)
RESULT = re.compile(r"\b(?:reports?|reported|results|sinks?|fell|grew|miss(?:es)?|beats?|rose|recorded)\b|公布|公佈|年增|下滑", re.I)
FINANCE = re.compile(r"earnings|revenue|cash flow|capex|financial results|營收|营收|財報|财报|現金流|现金流|資本支出|资本支出", re.I)
ROLLING = {"", "changelog", "news", "blog", "index.html", "default.aspx", "releases", "release-notes"}


def article_key(row):
    """Only standalone URLs; landing pages and versioned changelogs abstain."""
    try:
        u = urlsplit(str(row.get("url") or ""))
        path = u.path.rstrip("/")
        if u.scheme not in {"http", "https"} or not u.hostname or u.username or u.password:
            return None
        investor_article = u.hostname == 'abc.xyz' and path.startswith('/investor/news/news-details/')
        if (path.rsplit("/", 1)[-1].lower() in ROLLING and not investor_article) or re.search(r"/(?:changelog|release-notes)(?:/|$)", path, re.I):
            return None
        query = urlencode(sorted((k, v) for k, v in parse_qsl(u.query) if not k.startswith("utm_") and k not in {"fbclid", "gclid"}))
        return urlunsplit(("https", u.netloc.lower(), path, query, ""))
    except ValueError:
        return None


def stale_summary(row):
    title = str(row.get("title_original") or row.get("title") or "")
    return bool(FINANCE.search(title) and RESULT.search(title) and not PREVIEW.search(title)
                and PREVIEW.search(str(row.get("summary") or "")))


def revision_rank(row):
    # A late re-fetch of the old headline must not supersede a newer version.
    observed = timestamp(row.get("content_observed_at") or row.get("first_seen_at"))
    return (timestamp(row.get("source_updated_at")) or observed or timestamp(row.get("published_at")),
            observed, timestamp(row.get("published_at")), str(row.get("id") or ""))


def timestamp(value):
    try:
        t = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return t.timestamp() if t.tzinfo else 0
    except (ValueError, TypeError, OverflowError):
        return 0


def compatible_revisions(rows):
    # Reused live pages and a URL repurposed for another fiscal report abstain.
    times = [timestamp(r.get("published_at") or r.get("first_seen_at")) for r in rows]
    signatures = {s for r in rows if (s := earnings_signature(r))}
    quarters = {q.lower() for r in rows for q in re.findall(r'\bQ[1-4]\b', str(r.get('title_original') or r.get('title') or ''), re.I)}
    return all(times) and max(times) - min(times) <= 72 * 3600 and len(signatures) <= 1 and len(quarters) <= 1


def project(rows):
    """Return copies, with older IDs retained as resolvable historical aliases."""
    out = copy.deepcopy(list(rows))
    groups = defaultdict(list)
    for row in out:
        key = article_key(row)
        if key and not row.get("duplicate_of") and not evidence_policy.exclusion_reason(row):
            groups[key].append(row)
    for key, versions in groups.items():
        current = max(versions, key=revision_rank)
        # Simultaneous cross-ingress copies have no revision ordering evidence.
        # Keep those inputs for the existing matcher instead of choosing by ID.
        ordered_revision = len({revision_rank(v)[:-1] for v in versions}) > 1
        if len(versions) > 1 and ordered_revision and compatible_revisions(versions):
            current["article_version_ids"] = sorted(v["id"] for v in versions)
            first = min(versions, key=lambda v: timestamp(v.get("published_at") or v.get("first_seen_at")))
            current["article_first_published_at"] = first.get("published_at") or first.get("first_seen_at")
            for row in versions:
                if row is not current:
                    row["duplicate_of"] = current["id"]
                    row["article_superseded_by"] = current["id"]
        current["article_key"] = key
    for row in out:
        if stale_summary(row):
            row["summary_quality"] = "stale_preview"
            row["summary"] = ""
            for field in ("summary_zh", "reader_summary", "news_summary"):
                row.pop(field, None)
    return out


def current(rows):
    return [r for r in project(rows) if not r.get("duplicate_of") and not evidence_policy.exclusion_reason(r)]


def earnings_signature(row):
    """Same company + explicit fiscal quarter/year + results, not an outlook."""
    title = str(row.get('title_original') or row.get('title') or '')
    summary = str(row.get('summary') or '')
    if PREVIEW.search(title) or re.search(r'\b(?:outlook|forecast|guidance|preview|expected|may|could)\b|預測|預告|預計', title, re.I): return None
    if not FINANCE.search(title + '\n' + summary): return None
    companies = {('alphabet' if name.lower() in {'google','alphabet'} else name.lower())
                 for name in re.findall(r'\b(Alphabet|Google|Microsoft|NVIDIA|Amazon|Meta|AMD|Intel)\b', title, re.I)}
    if len(companies) != 1: return None
    text = title + '\n' + summary + '\n' + str(row.get('url') or '')
    periods = set(re.findall(r'\bQ([1-4])[\s-]*(20\d{2})\b', text, re.I))
    periods.update((q, year) for year, q in re.findall(r'\b(20\d{2})[\s-]*Q([1-4])\b', text, re.I))
    for ordinal, year in re.findall(r'\b(first|second|third|fourth) quarter (20\d{2})\b', text, re.I):
        periods.add((str(['first','second','third','fourth'].index(ordinal.lower())+1), year))
    if len(periods) != 1: return None
    # A bare calendar label or plans to release results do not assert a result.
    if not ((FINANCE.search(title) and RESULT.search(title))
            or re.search(r'announces? .{0,30}quarter .{0,60}results', title, re.I)
            or re.search(r'earnings (?:today|results)', summary, re.I)): return None
    return (next(iter(companies)), *next(iter(periods)))


def retain_change(existing, previous, now):
    """Keep same-ID content changes, including removal, with observation times."""
    fields = ("title", "summary", "published_at")
    if not previous or all(existing.get(k) == previous.get(k) for k in fields):
        return
    history = list(previous.get("article_history") or [])
    old = {k: previous.get(k) for k in fields}
    old["observed_at"] = previous.get("content_observed_at") or previous.get("last_seen_at")
    if not history or history[-1] != old:
        history.append(old)
    existing["article_history"] = history[-16:]
    existing["article_history_truncated"] = bool(previous.get("article_history_truncated") or len(history) > 16)
    existing["content_observed_at"] = now.isoformat().replace("+00:00", "Z")
    for field in ("summary_zh", "reader_summary", "news_summary"):
        existing.pop(field, None)
