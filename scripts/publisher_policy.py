"""Scoped publisher admission for public output copies, never event matching.

The local registry is the only admission authority. RSS names, legacy votes,
cached policies and query labels cannot grant a publisher a source tier.
"""
from __future__ import annotations

from functools import lru_cache
from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import unquote, urlsplit

try:
    from scripts import publisher_identity as identity
except ModuleNotFoundError:  # direct generator CLI
    import publisher_identity as identity


POLICY_ID = "publisher-governance-v1"
REGISTRY_PATH = Path(__file__).resolve().parents[1] / "config/publisher-policy.json"
TIER_FIELDS = ("source_tier", "source_tier_label", "source_tier_rank")
PERMISSIONS = ("allow_general", "allow_featured", "allow_radar")
TIERS = {"official", "benchmark", "ai_vertical", "professional_media", "ai_media",
         "community", "builders", "user_opml", "self_media", "advanced",
         "discussion", "tw_media", "watchlist", "other"}
KINDS = {"official", "benchmark", "media", "aggregator", "control", "unknown"}


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def registry_revision(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical({k: v for k, v in payload.items() if k != "revision"})).hexdigest()


class Registry:
    """Validate local policy before any output is written; no silent fallback."""
    def __init__(self, payload: dict[str, Any]):
        if not isinstance(payload, dict) or type(payload.get("schema_version")) is not int or payload["schema_version"] != 1 or payload.get("policy_id") != POLICY_ID:
            raise ValueError("unsupported_publisher_policy")
        self.revision = registry_revision(payload)
        if payload.get("revision") != self.revision:
            raise ValueError("publisher_policy_revision_mismatch")
        scopes = payload.get("scopes")
        if not isinstance(scopes, list) or not 1 <= len(scopes) <= 1000:
            raise ValueError("invalid_publisher_policy_scopes")
        self.default = payload.get("default")
        self._validate_policy(self.default)
        if self.default.get("admission_status") != "unreviewed" or not self.default.get("allow_general"):
            raise ValueError("invalid_publisher_policy_default")
        ids, matches = set(), set()
        for scope in scopes:
            self._validate_policy(scope)
            sid = scope.get("scope_id")
            if not isinstance(sid, str) or not re.fullmatch(r"[a-z0-9_./-]{1,120}", sid) or sid in ids:
                raise ValueError("invalid_publisher_policy_scope_id")
            ids.add(sid)
            pid = scope.get("publisher_id")
            if pid is not None and (not isinstance(pid, str) or not re.fullmatch(r"[a-z0-9_-]{1,120}", pid)):
                raise ValueError("invalid_publisher_policy_publisher_id")
            if scope["admission_status"] in {"approved", "limited"} and not pid:
                raise ValueError("missing_publisher_policy_identity")
            rules = scope.get("hosts")
            if not isinstance(rules, list) or not 1 <= len(rules) <= 32:
                raise ValueError("invalid_publisher_policy_hosts")
            for rule in rules:
                if not isinstance(rule, dict) or set(rule) != {"host", "path_prefix"}:
                    raise ValueError("invalid_publisher_policy_host_rule")
                host, prefix = rule["host"], rule["path_prefix"]
                if not isinstance(host, str) or identity.public_url("https://" + host)[1] != host or ":" in host or "/" in host:
                    raise ValueError("invalid_publisher_policy_host")
                if not isinstance(prefix, str) or not prefix.startswith("/") or re.search(r"[%?#\\\s]", prefix) or any(p in {".", ".."} for p in prefix.split("/")):
                    raise ValueError("invalid_publisher_policy_path")
                match = (host, prefix.rstrip("/") or "/")
                if match in matches:
                    raise ValueError("ambiguous_publisher_policy_scope")
                matches.add(match)
        # Copy caller-owned objects so later mutations cannot bypass validation.
        self.scopes = json.loads(json.dumps(scopes))
        self.default = dict(self.default)

    @staticmethod
    def _validate_policy(policy):
        if not isinstance(policy, dict) or policy.get("publisher_kind") not in KINDS or policy.get("admission_status") not in {"approved", "limited", "unreviewed", "excluded"}:
            raise ValueError("invalid_publisher_policy_status")
        if policy.get("source_tier") not in TIERS or not isinstance(policy.get("source_tier_label"), str) or not 1 <= len(policy["source_tier_label"]) <= 80:
            raise ValueError("invalid_publisher_policy_tier")
        if type(policy.get("source_tier_rank")) is not int or not 0 <= policy["source_tier_rank"] <= 9 or any(type(policy.get(k)) is not bool for k in PERMISSIONS):
            raise ValueError("invalid_publisher_policy_permissions")
        if policy["admission_status"] == "unreviewed" and (policy["source_tier"] != "watchlist" or policy["source_tier_rank"] != 6 or policy["allow_featured"] or policy["allow_radar"]):
            raise ValueError("invalid_unreviewed_publisher_policy")
        if policy["admission_status"] == "excluded" and any(policy[k] for k in PERMISSIONS):
            raise ValueError("invalid_excluded_publisher_policy")
        if policy["publisher_kind"] == "control" and any(policy[k] for k in PERMISSIONS):
            raise ValueError("invalid_control_publisher_policy")


@lru_cache(maxsize=4)
def _parse_registry(text: str) -> Registry:
    return Registry(json.loads(text))


def load_registry(path: Path = REGISTRY_PATH) -> Registry:
    # Read current bytes each call: a changed registry never reuses old grants.
    return _parse_registry(path.read_text(encoding="utf-8"))


_GENERATION_REGISTRY: ContextVar[Registry | None] = ContextVar("publisher_policy_registry", default=None)


@contextmanager
def generation():
    """One revision per refresh; the next refresh reads current policy bytes."""
    token = _GENERATION_REGISTRY.set(load_registry())
    try:
        yield
    finally:
        _GENERATION_REGISTRY.reset(token)


def current_registry() -> Registry:
    return _GENERATION_REGISTRY.get() or load_registry()


def _target(record):
    url, host = identity.public_url(record.get("url"))
    google = host == "news.google.com"
    if google:
        _, url, host = identity.trusted_rss_source(record)
    if not url or not host:
        return None
    parsed = urlsplit(url)
    if parsed.port not in {None, 80 if parsed.scheme == "http" else 443}:
        return None
    path = unquote(parsed.path) or "/"
    if re.search(r"%(?:2f|5c|25)", parsed.path, re.I) or "\\" in path or any(p in {".", ".."} for p in path.split("/")):
        return None
    return host, path, google


def policy_for(record: dict[str, Any], registry: Registry) -> dict[str, Any]:
    """Consume freshly rebuilt PG02 identity, not an archive admission flag."""
    publisher = record["publisher"]
    status = publisher["status"]
    target = _target(record)
    base, sid = registry.default, "unreviewed"
    reasons = ["identity_conflict" if status == "conflict" else
               "missing_identity" if status == "unknown" else
               "reported_rss_source" if status == "reported" else "legacy_identity"]
    if (record["ingress"].get("source_id") == "juya_daily"):
        base = next(s for s in registry.scopes if s["scope_id"] == "juya")
        sid, reasons = base["scope_id"], ["control_only"]
    elif target and status != "conflict":
        host, path, google = target
        candidates = [(len(rule["path_prefix"]), scope) for scope in registry.scopes for rule in scope["hosts"]
                      if host == rule["host"] and (rule["path_prefix"] == "/"
                          or (not rule["path_prefix"].endswith("/") and path == rule["path_prefix"])
                          or (path.startswith(rule["path_prefix"].rstrip("/") + "/")
                              and len(path) > len(rule["path_prefix"].rstrip("/")) + 1))]
        if candidates:
            scope = max(candidates, key=lambda pair: pair[0])[1]
            if scope["admission_status"] in {"unreviewed", "excluded"} or (status == "identified" and publisher["publisher_id"] == scope["publisher_id"]):
                base, sid = scope, scope["scope_id"]
                reasons = ["identified_bridge" if google else "identified_host"] if status == "identified" else reasons
            else:
                reasons.append("scope_mismatch")
        else:
            reasons.append("scope_mismatch")
    else:
        reasons.append("scope_unknown")
    reasons.append({"approved": "approved_scope", "limited": "limited_scope", "excluded": "excluded_scope", "unreviewed": "unreviewed_publisher"}[base["admission_status"]])
    if not base["allow_featured"]:
        reasons.append("not_permitted_for_featured")
    if not base["allow_radar"]:
        reasons.append("not_permitted_for_radar")
    return {"schema_version": 1, "policy_id": POLICY_ID, "registry_revision": registry.revision,
            "scope_id": sid, **{k: base[k] for k in ("publisher_kind", "admission_status", *TIER_FIELDS, *PERMISSIONS)},
            "reason_codes": list(dict.fromkeys(reasons))}


def annotate(record: dict[str, Any], *, feeds=(), registry: Registry | None = None,
             effective_tier: bool = True) -> dict[str, Any]:
    """Return a public copy. Archive/claim rows and caller objects stay intact."""
    rebuilt = {**record, **identity.fields(record, feeds=feeds)}
    policy = policy_for(rebuilt, registry or current_registry())
    out = {**rebuilt, "source_policy": policy}
    if effective_tier:
        out.update({key: policy[key] for key in TIER_FIELDS})
    return out
