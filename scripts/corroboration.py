"""Bounded public publisher identities, never a claim of factual verification.

No network, private feed mapping, redirect decoding, or arbitrary-domain votes.
Labels describe configured ingress; article hosts and exact Google News suffixes
can contradict them. Unknown/conflicting identities abstain.
"""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlsplit


LABELS = {
    "OpenAI News": "openai", "OpenAI Codex Changelog": "openai", "OpenAI Skills": "openai",
    "Google AI Blog": "google", "Google Gemini Blog": "google",
    "Google DeepMind": "google", "Google DeepMind Blog": "google",
    "Google Cloud Blog (Google News)": "google",
    "Hugging Face Blog": "huggingface", "NVIDIA Blog": "nvidia",
    "NVIDIA Generative AI Blog": "nvidia", "Microsoft Blog": "microsoft",
    "Microsoft AI Blog": "microsoft", "AWS News": "amazon",
    "Anthropic News": "anthropic", "Tencent Newsroom": "tencent",
    "Thinking Machines Lab": "thinkingmachines", "Mistral News": "mistral",
    "GitHub AI & ML": "github", "GitHub Changelog": "github", "ARC Prize": "arc_prize",
    "MCP Blog": "mcp_blog", "RuntimeWire": "runtimewire", "LLM Rumors": "llm_rumors",
    "LLM Stats Model Releases": "llm_stats", "INSIDE": "inside", "iThome": "ithome",
    "TechNews 科技新報": "technews", "數位時代 (Google News)": "bnext",
    "Reuters AI (Google News)": "reuters", "CNBC Technology": "cnbc",
    "The Information (Google News)": "the_information", "TechCrunch AI": "techcrunch",
    "The Verge": "the_verge", "The Decoder AI News": "the_decoder",
    "MarkTechPost Research": "marktechpost", "Wired AI": "wired",
    "AIBASE": "cn_aggregator", "36Kr": "cn_aggregator", "橘鴉AI早報": "cn_aggregator",
}
# Public configured publishers and A02's named publisher evidence. Hosts use
# label boundaries, so reuters.com.attacker.test never matches reuters.com.
HOSTS = {
    "openai.com": "openai", "deepmind.google": "google", "blog.google": "google",
    "cloud.google.com": "google", "huggingface.co": "huggingface",
    "blogs.nvidia.com": "nvidia", "nvidianews.nvidia.com": "nvidia",
    "blogs.microsoft.com": "microsoft", "aws.amazon.com": "amazon",
    "anthropic.com": "anthropic", "tencent.com": "tencent",
    "thinkingmachines.ai": "thinkingmachines", "mistral.ai": "mistral",
    "github.blog": "github", "arcprize.org": "arc_prize",
    "blog.modelcontextprotocol.io": "mcp_blog", "runtimewire.com": "runtimewire",
    "llmrumors.com": "llm_rumors", "llm-stats.com": "llm_stats",
    "inside.com.tw": "inside", "ithome.com.tw": "ithome", "technews.tw": "technews",
    "bnext.com.tw": "bnext", "reuters.com": "reuters", "cnbc.com": "cnbc",
    "theinformation.com": "the_information", "techcrunch.com": "techcrunch",
    "theverge.com": "the_verge", "the-decoder.com": "the_decoder",
    "marktechpost.com": "marktechpost", "wired.com": "wired",
    "aibase.com": "cn_aggregator", "aibase.com.tw": "cn_aggregator",
    "36kr.com": "cn_aggregator",
}
SUFFIXES = {
    "reuters": "reuters", "cnbc": "cnbc", "the information": "the_information",
    "techcrunch": "techcrunch", "the verge": "the_verge", "wired": "wired",
    "the decoder": "the_decoder", "數位時代": "bnext", "未來商務": "bnext",
    "未来商务": "bnext", "36kr": "cn_aggregator", "36氪": "cn_aggregator",
    "bloomberg": "bloomberg", "bloomberg.com": "bloomberg",
    "financial times": "financial_times", "yahoo finance": "yahoo_finance",
    "business insider": "business_insider", "forbes": "forbes", "fortune": "fortune",
    "the register": "the_register", "venturebeat": "venturebeat",
    "siliconangle": "siliconangle", "cointelegraph": "cointelegraph",
    "the block": "the_block", "decrypt": "decrypt", "coindesk": "coindesk",
    "tom's hardware": "toms_hardware", "tom’s hardware": "toms_hardware",
    "9to5mac": "9to5mac", "techradar": "techradar", "futurism": "futurism",
}
CONFIGURED_SITES = {"official_ai", "curated_media", "tw_media", "runtimewire",
                    "llm_rumors", "llm_stats_models", "arc_prize", "mcp_blog", "mistral_news"}
ECOSYSTEM_SITES = {"aibase", "kr36_ai", "juya_daily"}


def _legacy_identity(item: dict[str, Any]) -> tuple[str | None, str]:
    site = str(item.get("site_id") or "")
    source = str(item.get("source") or "").strip()
    if site in ECOSYSTEM_SITES or (site == "curated_media" and source.casefold() == "aibase"):
        return "cn_aggregator", "identified"
    try:
        parsed = urlsplit(str(item.get("url") or ""))
        host = (parsed.hostname or "").lower().rstrip(".")
        if parsed.scheme not in {"http", "https"} or parsed.username or parsed.password:
            return None, "unknown"
    except ValueError:
        return None, "unknown"
    by_host = next((pub for domain, pub in HOSTS.items()
                    if host == domain or host.endswith("." + domain)), None)
    if host == "github.com" and (parsed.path.rstrip("/") == "/openai/skills"
                                 or parsed.path.startswith("/openai/skills/")):
        by_host = "openai"
    # Private OPML labels are not authority. A known public article host is.
    by_label = LABELS.get(source) if site in CONFIGURED_SITES else None
    is_google = host == "news.google.com"
    title = str(item.get("title_original") or item.get("title") or "")
    parts = re.split(r"\s+[-–—]\s+", title)
    by_suffix = SUFFIXES.get(parts[-1].strip().casefold()) if is_google and len(parts) > 1 else None
    signals = {value for value in (by_host, by_label, by_suffix) if value}
    if len(signals) > 1:
        return None, "conflict"
    # Labels alone are allowed only on the configured Google News bridge;
    # an arbitrary unrecognized URL does not inherit a publisher's identity.
    publisher = by_host or by_suffix or (by_label if is_google else None)
    if not publisher:
        return None, "unknown"
    return (publisher if publisher == "cn_aggregator" else "publisher:" + publisher), "identified"


def identity(item: dict[str, Any]) -> tuple[str | None, str]:
    try:
        from scripts.publisher_identity import rss_conflict
    except ModuleNotFoundError:  # direct CLI
        from publisher_identity import rss_conflict
    key, status = _legacy_identity(item)
    if rss_conflict(item, key, HOSTS, LABELS, SUFFIXES):
        return None, "conflict"
    return key, status


def annotate(item: dict[str, Any]) -> dict[str, Any]:
    key, status = identity(item)
    return {**item, "corroboration_key": key, "corroboration_status": status}


def count(items: list[dict[str, Any]]) -> int:
    return len({key for item in items if (key := identity(item)[0]) is not None})


def story_count(story: dict[str, Any]) -> int:
    value = story.get("corroboration_count")
    if type(value) is int and 0 <= value <= 2**53 - 1:
        return value
    refs = story.get("sources")
    return len({x["corroboration_key"] for x in refs if isinstance(x, dict)
                and isinstance(x.get("corroboration_key"), str) and x["corroboration_key"]}) if isinstance(refs, list) else 0
