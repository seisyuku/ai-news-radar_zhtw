"""Same-window citation grouping for the private digest; no I/O or providers.

Sharing an event, company or product is not sufficient to suppress a report.
Explicit citations and overlapping same-publisher product reports may remove
a slot. Different foreground aspects retain separate slots.
"""

from copy import deepcopy
from dataclasses import dataclass
import html
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

VERSION = "current-event-v2"
_LINK = re.compile(r"https?://[^\s<>\"\[\]]+", re.I)
_ASPECTS = {
    "api-key-use": r"\bAPI keys?\b|API\s*金鑰|API\s*金钥",
    "compute-tools": r"\b(?:Ascend|CUDA)\b|昇騰|昇腾",
    "acquisition": r"\b(?:acquisition|acquire[sd]?|in talks to buy)\b|收購|收购|併購",
    "investment": r"\b(?:investment|investing|invests?|funding round)\b|增資|增加投資|增加投资|融資",
    "software-jobs": r"\bsoftware (?:developer|engineer).*job|軟體.{0,8}職缺",
    "tech-jobs": r"\btech(?:nology)? (?:jobs|job openings)|科技業.{0,8}職缺",
    "pricing": r"\b(?:price cut|cuts? prices?|reduces? prices?|price increase)\b|降價|調漲",
    "release": r"\b(?:releases?|released|launch(?:es|ed|ing)?|ships?)\b|發布|发布|推出|釋出|上線|上线",
    "response": r"\b(?:responds?|denies?|investigation)\b|回應|回应|否認|調查",
}
_ROUNDUP = re.compile(r"\b(?:news roundup|daily digest|weekly roundup)\b|早報|早报|新聞彙整|一週回顧", re.I)
_MODEL = re.compile(r"\b(?:deepseek[-\s]+v?\d+(?:\.\d+)+(?:\s+flash)?|(?:gpt|qwen|gemini)[-\s]+\d+(?:\.\d+)*)\b", re.I)
_FOLLOWUP = re.compile(r"\b(?:follow.up|separate tests?|another test|new benchmark|in response)\b|後續|追加測試|另一次|新測試", re.I)


def url_key(value):
    """Keep article identity queries; remove only known tracking parameters."""
    if not isinstance(value, str):
        return None
    try:
        parsed = urlsplit(html.unescape(value.strip()))
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
            return None
        query = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
                 if not k.lower().startswith("utm_") and k.lower() not in {"fbclid", "gclid"}]
        return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path.rstrip("/"),
                           urlencode(sorted(query)), ""))
    except ValueError:
        return None


def heading(candidate):
    return str(candidate.get("title_original") or candidate.get("title") or "")


def aspect_keys(candidate):
    text = heading(candidate)
    return {key for key, pattern in _ASPECTS.items() if re.search(pattern, text, re.I)}


def different_aspects(a, b):
    """Protect explicit different angles, not just different versions."""
    left, right = aspect_keys(a), aspect_keys(b)
    versions_a = {re.sub(r"\s+", " ", m.group().lower()) for m in _MODEL.finditer(heading(a))}
    versions_b = {re.sub(r"\s+", " ", m.group().lower()) for m in _MODEL.finditer(heading(b))}
    return bool((left and right and left != right) or
                (versions_a and versions_b and versions_a.isdisjoint(versions_b)) or
                (bool(_FOLLOWUP.search(heading(a))) != bool(_FOLLOWUP.search(heading(b)))))


def _article_keys(candidate):
    return {key for url in [candidate.get("primary_url"),
                           *(ref.get("url") for ref in candidate.get("sources", []))]
            if (key := url_key(url))}


def _citations(candidate):
    # Use publisher original text only. Display translations and source labels
    # cannot create a citation, and HTML href values removed upstream are unknown.
    texts = [candidate.get("summary_original"),
             *(ref.get("summary_original") for ref in candidate.get("sources", []))]
    def captured_links(row):
        value = row.get("publisher_links")
        return value[:24] if isinstance(value, list) else []
    links = [*captured_links(candidate),
             *(url for ref in candidate.get("sources", []) for url in captured_links(ref))]
    return {key for url in links if (key := url_key(url))} | {key for text in texts if isinstance(text, str)
            for match in _LINK.finditer(html.unescape(text))
            if (key := url_key(match.group().rstrip(".,;:!?。；，)")))}


def article_cites(a, b):
    """Read original archive rows before similarity merging discards identity."""
    citation_row = {**a, "summary_original": a.get("summary_original", a.get("summary"))}
    target = {**b, "primary_url": b.get("primary_url", b.get("url"))}
    return bool(_citations(citation_row) & _article_keys(target))


def confirmed_article_pairs(confirmations):
    pairs = []
    confirmations = [] if confirmations is None else confirmations
    if not isinstance(confirmations, list):
        raise ValueError("invalid_event_citations")
    for row in confirmations:
        if not isinstance(row, dict) or row.get("basis") != "user-confirmed-same-news":
            raise ValueError("invalid_event_citations")
        citing, cited = url_key(row.get("citing_url")), url_key(row.get("cited_url"))
        if not citing or not cited or citing == cited:
            raise ValueError("invalid_event_citations")
        pairs.append((citing, cited))
    return pairs


def _content_features(candidate):
    """Cheap recall from original material, without translations or providers."""
    title = heading(candidate)
    body = str(candidate.get("summary_original") or "")
    body = re.split(r"\bThe (?:article|post)\b", body, maxsplit=1, flags=re.I)[0]
    compact = re.sub(r"[^a-z0-9\u4e00-\u9fff]", "", body.casefold())
    if len(compact) < 80:
        return None
    primary = next((r for r in candidate.get("sources", [])
                    if r.get("item_id") == candidate.get("primary_item_id")), {})
    publisher = str(primary.get("source") or "").strip().casefold()
    if not publisher:
        return None
    names = set()
    normalized_title = re.sub(r"\s+", "", title.casefold())
    for name in re.findall(r'[“「『"‘]([^”」』"’]{2,32})[”」』"’]', title + "\n" + body):
        name = re.sub(r"\s+", "", name.casefold())
        # AI + a Chinese product name is an optional descriptive prefix.
        if re.fullmatch(r"ai[\u4e00-\u9fff]{2,}", name):
            name = name[2:]
        if (re.fullmatch(r"[a-z0-9\u4e00-\u9fff.-]{2,32}", name) and name in normalized_title and
                name not in {"ai", "model", "models", "agent", "人工智能", "人工智慧", "ai代理", "ai助手", "模型"}):
            names.add(name)
    if not names or not aspect_keys(candidate):
        return None
    return publisher, names, {compact[i:i+2] for i in range(len(compact)-1)}


def _same_content(a, b, left, right):
    if (left is None or right is None or left[0] != right[0] or not left[1] & right[1] or
            aspect_keys(a) != aspect_keys(b) or different_aspects(a, b) or
            _ROUNDUP.search(heading(a)) or _ROUNDUP.search(heading(b))):
        return False
    shared = len(left[2] & right[2])
    return shared >= 30 and shared / min(len(left[2]), len(right[2])) >= .45


@dataclass(frozen=True)
class EventGroups:
    representatives: tuple[str, ...]
    metadata: dict
    removed_count: int
    confirmation_count: int
    content_removed_count: int = 0


def group_cited_reports(candidates, *, rank_key, confirmations=None):
    """Group only eligible same-window candidates, with complete-link checks.

    Confirmations are optional maintainer inputs keyed by exact article URLs,
    never data-specific rules or a cross-day event store. Stale URLs do nothing.
    A reference alone can be background: automatic citations additionally need
    the same explicit foreground aspect and overlapping headline tokens.
    Content matching requires a shared publisher, quoted product in both
    headlines, matching foreground aspects and substantial publisher summary.
    """
    rows = {c["story_id"]: c for c in candidates}
    keys = {key: _article_keys(c) for key, c in rows.items()}
    citations = {key: _citations(c) for key, c in rows.items()}
    url_ids = {}
    for sid, urls in keys.items():
        for url in urls:
            url_ids.setdefault(url, set()).add(sid)
    links = {}
    for citing, cited in confirmed_article_pairs(confirmations):
        origin, target = url_ids.get(citing, set()), url_ids.get(cited, set())
        if len(origin) == len(target) == 1:
            a, b = next(iter(origin)), next(iter(target))
            if (a != b and not _ROUNDUP.search(heading(rows[a])) and
                    not _ROUNDUP.search(heading(rows[b])) and not different_aspects(rows[a], rows[b])):
                links[(a, b)] = "user-confirmed-same-news"
    # Import lazily to keep this module independent of the selector.
    if __package__:
        from . import update_news as news
    else:
        import update_news as news
    for a, candidate in rows.items():
        if _ROUNDUP.search(heading(candidate)):
            continue
        for url in sorted(citations[a]):
            targets = url_ids.get(url, set())
            if len(targets) != 1:
                continue
            b = next(iter(targets))
            if (a == b or _ROUNDUP.search(heading(rows[b])) or different_aspects(candidate, rows[b]) or
                    _FOLLOWUP.search(heading(candidate))):
                continue
            left, right = news.title_tokens(heading(candidate)), news.title_tokens(heading(rows[b]))
            common = left & right
            proper = lambda c: {word.casefold() for word in re.findall(r"\b[A-Z][A-Za-z]{2,}\b", heading(c))
                                if word.casefold() not in {"the", "new", "model", "models", "api", "two", "report", "releases"}}
            vendors_a, models_a = news.title_entities(heading(candidate))
            vendors_b, models_b = news.title_entities(heading(rows[b]))
            same_subject = bool(vendors_a & vendors_b or models_a & models_b or proper(candidate) & proper(rows[b]))
            if (aspect_keys(candidate) and aspect_keys(candidate) == aspect_keys(rows[b]) and
                    same_subject and news.story_titles_can_merge(heading(candidate), heading(rows[b])) and
                    ((len(common) >= 3 and len(common) / max(1, len(left | right)) >= .25) or
                     bool(models_a & models_b))):
                links.setdefault((a, b), "publisher-article-link")
    features = {sid: _content_features(candidate) for sid, candidate in rows.items()}
    ordered_ids = sorted(rows)
    for index, a in enumerate(ordered_ids):
        if features[a] is None:
            continue
        for b in ordered_ids[index+1:]:
            if ((a, b) not in links and (b, a) not in links and
                    _same_content(rows[a], rows[b], features[a], features[b])):
                links[(a, b)] = "same-publisher-content"
    groups = []
    for sid in sorted(rows):
        if _ROUNDUP.search(heading(rows[sid])):
            groups.append([sid])
            continue
        for group in groups:
            if all((sid, other) in links or (other, sid) in links for other in group):
                group.append(sid)
                break
        else:
            groups.append([sid])
    representatives, metadata, content_removed = [], {}, 0
    for group in groups:
        # Keep the higher existing editorial rank; never boost a score because
        # another report repeats the same news. IDs break exact ranking ties.
        chosen = min(group, key=lambda sid: rank_key(sid))
        representatives.append(chosen)
        if len(group) > 1:
            metadata[chosen] = {
                "policy": VERSION, "representative_story_id": chosen,
                "citations": [{"citing_story_id": a, "cited_story_id": b, "basis": basis}
                              for (a, b), basis in sorted(links.items())
                              if a in group and b in group and basis != "same-publisher-content"],
                "content_duplicates": [{"story_ids": [a, b], "basis": basis}
                                       for (a, b), basis in sorted(links.items())
                                       if a in group and b in group and basis == "same-publisher-content"],
                "related_reports": [deepcopy(rows[sid]) for sid in sorted(group) if sid != chosen],
            }
            content_removed += sum((links.get((sid, chosen)) or links.get((chosen, sid))) == "same-publisher-content"
                                   for sid in group if sid != chosen)
            # Counts/scores/source refs of the representative stay unchanged.
            # Other reports stay separate, never promoted to independent proof.
    return EventGroups(tuple(representatives), metadata, len(rows) - len(groups),
                       sum(citation["basis"] == "user-confirmed-same-news"
                           for group in metadata.values() for citation in group["citations"]), content_removed)
