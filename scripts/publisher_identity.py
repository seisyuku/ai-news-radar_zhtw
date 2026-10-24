"""Public publisher identity only: no admission, scores, requests or new votes."""
from __future__ import annotations

import html
import ipaddress
import re
from typing import Any
from urllib.parse import urlsplit, urlunsplit


GOOGLE_ROUTES = {
    ("official_ai", "Google Cloud Blog (Google News)"): "google_cloud_blog_news",
    ("curated_media", "Reuters AI (Google News)"): "reuters_ai_news",
    ("curated_media", "The Information (Google News)"): "the_information_news",
    ("curated_media", "Meta AI (Google News)"): "meta_ai_news",
    ("curated_media", "DeepSeek (Google News)"): "deepseek_news",
    ("curated_media", "xAI / Grok (Google News)"): "xai_grok_news",
    ("curated_media", "Epoch AI (Google News)"): "epoch_ai_news",
    ("tw_media", "數位時代 (Google News)"): "bnext_news",
}
NAMES = {
    "openai": "OpenAI", "google": "Google", "huggingface": "Hugging Face",
    "nvidia": "NVIDIA", "microsoft": "Microsoft", "amazon": "AWS",
    "anthropic": "Anthropic", "tencent": "Tencent", "thinkingmachines": "Thinking Machines Lab",
    "mistral": "Mistral", "github": "GitHub", "arc_prize": "ARC Prize",
    "mcp_blog": "MCP Blog", "runtimewire": "RuntimeWire", "llm_rumors": "LLM Rumors",
    "llm_stats": "LLM Stats", "inside": "INSIDE", "ithome": "iThome",
    "technews": "TechNews 科技新報", "bnext": "數位時代", "reuters": "Reuters",
    "cnbc": "CNBC Technology", "the_information": "The Information", "techcrunch": "TechCrunch",
    "the_verge": "The Verge", "the_decoder": "The Decoder", "marktechpost": "MarkTechPost",
    "wired": "Wired", "aibase": "AIBASE", "kr36": "36Kr", "juya": "橘鴉AI早報",
    "epoch": "Epoch AI",
}


def clean_name(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = html.unescape(re.sub(r"<[^>]*>", "", value))
    value = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", value)
    return re.sub(r"\s+", " ", value).strip()[:160] or None


def public_url(value: Any) -> tuple[str | None, str | None]:
    """Normalize public HTTP metadata without requesting or decoding its URL."""
    if not isinstance(value, str) or len(value) > 2048 or re.search(r"[\s\\\x00-\x1f]", value):
        return None, None
    try:
        p = urlsplit(value)
        host = (p.hostname or "").rstrip(".").encode("idna").decode("ascii").lower()
        if p.scheme.lower() not in {"http", "https"} or p.username or p.password or not host:
            return None, None
        if len(host) > 253 or any(not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", s) for s in host.split(".")):
            return None, None
        try:
            ipaddress.ip_address(host)
            return None, None  # Literal IPs are not public publisher identities.
        except ValueError:
            pass
        if "." not in host or host.endswith((".localhost", ".local", ".internal", ".test", ".invalid")):
            return None, None
        port = p.port
        netloc = host + (f":{port}" if port is not None else "")
        return urlunsplit((p.scheme.lower(), netloc, p.path, p.query, "")), host
    except (ValueError, UnicodeError):
        return None, None


def feed_source(entry: dict[str, Any]) -> dict[str, str | None]:
    source = entry.get("source")
    if not isinstance(source, dict):
        return {"title": None, "href": None}
    href, _ = public_url(source.get("href") or source.get("url") or source.get("link"))
    return {"title": clean_name(source.get("title")), "href": href}


def ingress_for(record: dict[str, Any], feeds=()) -> dict[str, Any]:
    site, label = str(record.get("site_id") or "unknown"), str(record.get("source") or "")
    if site.startswith("opmlrss"):
        return {"kind": "private_opml", "site_id": site, "source_id": None,
                "name": "RSS/OPML", "feed_url": None}
    for sid, feed in feeds:
        if sid == site and feed.get("title") == label:
            url, host = public_url(feed.get("xml_url"))
            return {"kind": "google_news" if host == "news.google.com" else feed.get("ingress_kind", "public_feed"),
                    "site_id": site, "source_id": feed.get("source_id"),
                    "name": clean_name(label) or "來源", "feed_url": url}
    # No new authority from arbitrary stored ingress fields or private labels.
    return {"kind": "legacy_unknown", "site_id": site, "source_id": None,
            "name": clean_name(label) or "來源", "feed_url": None}


def trusted_rss_source(record: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    route = GOOGLE_ROUTES.get((str(record.get("site_id") or ""), str(record.get("source") or "")))
    ingress = record.get("ingress") or {}
    if not isinstance(ingress, dict):
        return None, None, None
    _, article_host = public_url(record.get("url"))
    _, feed_host = public_url(ingress.get("feed_url"))
    if not route or ingress.get("source_id") != route or ingress.get("kind") != "google_news" \
            or article_host != "news.google.com" or feed_host != "news.google.com":
        return None, None, None
    publisher = record.get("publisher") or {}
    evidence = publisher.get("evidence") if isinstance(publisher, dict) else {}
    if not isinstance(evidence, dict):
        return None, None, None
    url, host = public_url(evidence.get("rss_source_url"))
    return clean_name(evidence.get("rss_source_name")), url, host


def rss_conflict(record, legacy_key, hosts, labels, suffixes) -> bool:
    name, _, domain = trusted_rss_source(record)
    if not name or not domain:
        return False
    by_host = next((pub for host, pub in hosts.items() if domain == host or domain.endswith("." + host)), None)
    by_name = suffixes.get(name.casefold()) or labels.get(name)
    # This configured bridge had no legacy counting key; its identity scope
    # still must not silently accept a different returned publisher.
    if (record.get("ingress") or {}).get("source_id") == "epoch_ai_news":
        return domain not in {"epoch.ai", "www.epoch.ai"} or bool(by_name and by_name != "epoch")
    expected = (legacy_key or "").removeprefix("publisher:") or None
    signals = {x for x in (by_host, by_name, expected) if x}
    if len(signals) > 1:
        return True
    # A bounded known publisher cannot inherit an explicitly different host.
    expected_hosts = [h for h, pub in hosts.items() if pub == expected]
    return bool(expected_hosts and not any(domain == h or domain.endswith("." + h) for h in expected_hosts))


def fields(record: dict[str, Any], *, feeds=(), rss_source=None) -> dict[str, Any]:
    try:
        from scripts import corroboration as c
    except ModuleNotFoundError:  # direct CLI
        import corroboration as c

    ingress = ingress_for(record, feeds)
    cached = record.get("publisher") or {}
    previous = cached.get("evidence", {}) if isinstance(cached, dict) else {}
    previous = previous if isinstance(previous, dict) else {}
    source = rss_source if isinstance(rss_source, dict) else {
        "title": previous.get("rss_source_name"), "href": previous.get("rss_source_url")}
    rss = feed_source({"source": source})
    article_url, article_host = public_url(record.get("url"))
    evidence = {"rss_source_name": rss["title"], "rss_source_url": rss["href"],
                "article_url": None, "article_host": article_host,
                "expected_publisher_id": None, "conflicts": []}
    probe = {**record, "ingress": ingress, "publisher": {"evidence": evidence}}
    rss_name, rss_url, rss_host = trusted_rss_source(probe)
    # Preserve provenance on configured public feeds without granting it
    # Google's identity authority. Private/unknown routes expose no feed data.
    if ingress["kind"] in {"private_opml", "legacy_unknown"}:
        evidence.update(rss_source_name=None, rss_source_url=None)
    legacy_key, _ = c._legacy_identity(record)
    by_host = next((pub for host, pub in c.HOSTS.items()
                    if (rss_host or article_host) == host or (rss_host or article_host or "").endswith("." + host)), None)
    basis = []
    if rss_name and rss_host:
        basis.append("google_rss_source")
    key, status = c.identity(probe)
    publisher_id = (key or "").removeprefix("publisher:") or by_host
    if publisher_id == "cn_aggregator":
        domain = rss_host or article_host or ""
        is_aibase_host = any(domain == host or domain.endswith("." + host) for host in ("aibase.com", "aibase.com.tw"))
        is_kr36_host = domain == "36kr.com" or domain.endswith(".36kr.com")
        if is_aibase_host:
            publisher_id = "aibase"
        elif is_kr36_host:
            publisher_id = "kr36"
        elif str(record.get("source") or "").casefold() == "aibase" or record.get("site_id") == "aibase":
            publisher_id = "aibase"
        else:
            publisher_id = "kr36" if record.get("site_id") == "kr36_ai" else "juya"
        basis.append("explicit_group")
        if by_host and article_host != "news.google.com":
            evidence["article_url"] = article_url
    elif article_host and article_host != "news.google.com" and (by_host or legacy_key):
        basis.append("article_host")
        evidence["article_url"] = article_url
    elif publisher_id and legacy_key:
        basis.append("configured_bridge" if (record.get("source") in c.LABELS or publisher_id == "epoch") else "legacy_suffix")
    # Epoch is a configured identity scope, not a newly granted vote.
    if not publisher_id and ingress.get("source_id") == "epoch_ai_news" and rss_host in {"epoch.ai", "www.epoch.ai"}:
        publisher_id = "epoch"
        basis.append("configured_bridge")
    if status == "conflict":
        evidence["expected_publisher_id"] = (legacy_key or "").removeprefix("publisher:") or None
        evidence["conflicts"] = ["publisher_signals_disagree"]
        publisher_id = None
        name, identity_status = None, "conflict"
    elif publisher_id:
        title = str(record.get("title_original") or record.get("title") or "")
        suffix = re.split(r"\s+[-–—]\s+", title)[-1].strip()
        legacy_name = suffix if article_host == "news.google.com" and suffix.casefold() in c.SUFFIXES else None
        name, identity_status = rss_name or NAMES.get(publisher_id) or clean_name(legacy_name) or clean_name(record.get("source")), "identified"
    elif rss_name and rss_host:
        name, identity_status = rss_name, "reported"
    else:
        name, identity_status = None, "unknown"
    return {"ingress": ingress, "publisher": {"schema_version": 1,
            "publisher_id": publisher_id, "name": name,
            "domain": rss_host or (article_host if article_host != "news.google.com" else None),
            "status": identity_status, "basis": list(dict.fromkeys(basis)), "evidence": evidence}}
