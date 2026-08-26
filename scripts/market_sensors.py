"""Deterministic market and usage-policy sensors for AI News Radar.

The module intentionally keeps observations separate from reader-facing news
items.  Structured sources produce exact old/new values; public GitHub commit
feeds only produce candidates and never claim an official policy change.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import html
import json
import re
import time
import xml.etree.ElementTree as ET
from typing import Any

import requests


UTC = timezone.utc
PRICE_URL = "https://cdn.jsdelivr.net/gh/llerandi/llm-price-tracker@main/data/prices.json"
PRICE_HOME = "https://github.com/llerandi/llm-price-tracker"
FREE_TIER_URL = "https://raw.githubusercontent.com/xyzs996/free-llm-api/main/data/providers.json"
FREE_TIER_HOME = "https://github.com/xyzs996/free-llm-api"
MARKET_SIGNAL_WINDOW_HOURS = 24

PRICE_FIELDS: dict[str, tuple[str, str]] = {
    "input_per_1m_usd": ("輸入價格", "USD / 1M tokens"),
    "output_per_1m_usd": ("輸出價格", "USD / 1M tokens"),
    "batch_input_per_1m_usd": ("Batch 輸入價格", "USD / 1M tokens"),
    "batch_output_per_1m_usd": ("Batch 輸出價格", "USD / 1M tokens"),
    "cache_read_per_1m_usd": ("Cache read 價格", "USD / 1M tokens"),
    "cache_write_per_1m_usd": ("Cache write 價格", "USD / 1M tokens"),
}

CANARY_FEEDS: tuple[dict[str, str], ...] = (
    {
        "id": "usage4claude",
        "name": "Usage4Claude",
        "url": "https://github.com/f-is-h/Usage4Claude/commits/main.atom",
        "home": "https://github.com/f-is-h/Usage4Claude",
    },
    {
        "id": "usage_monitor_claude",
        "name": "Claude Usage Monitor",
        "url": "https://github.com/jens-duttke/usage-monitor-for-claude/commits/main.atom",
        "home": "https://github.com/jens-duttke/usage-monitor-for-claude",
    },
)

CANARY_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bquota(?:s)?\b",
        r"\brate[ -]?limits?\b",
        r"\b(?:weekly|daily|monthly|5-hour|five-hour)\s+(?:limit|quota|window)s?\b",
        r"\b(?:extra usage|overage|usage credits?)\b",
        r"\bmodel-specific\s+(?:limit|quota)s?\b",
        r"\bdouble(?:d)?\s+(?:the\s+)?limits?\b",
        r"\busage\s+window\b",
        r"\breset\s+(?:time|window|schedule)\b",
    )
)


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _parse_iso(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _signal_id(*parts: Any) -> str:
    raw = json.dumps(parts, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _signal(
    *,
    event_type: str,
    category: str,
    title: str,
    summary: str,
    detected_at: str,
    effective_at: str | None,
    source_name: str,
    source_url: str,
    evidence_url: str,
    provider: str = "",
    product: str = "",
    field: str = "",
    old_value: Any = None,
    new_value: Any = None,
    unit: str = "",
    verification_status: str = "reported",
) -> dict[str, Any]:
    urgency = "breaking" if category == "usage_policy" else "standard"
    importance_rank = {"price": 1, "free_tier": 2, "usage_policy": 3}[category]
    timeliness_rank = {"usage_policy": 1, "free_tier": 2, "price": 3}[category]
    signal = {
        "event_type": event_type,
        "category": category,
        "urgency": urgency,
        "importance_rank": importance_rank,
        "timeliness_rank": timeliness_rank,
        "verification_status": verification_status,
        "title": title,
        "summary": summary,
        "provider": provider,
        "product": product,
        "field": field,
        "old_value": old_value,
        "new_value": new_value,
        "unit": unit,
        "detected_at": detected_at,
        "effective_at": effective_at,
        "source_name": source_name,
        "source_url": source_url,
        "evidence_url": evidence_url,
    }
    signal["id"] = _signal_id(
        event_type, provider, product, field, old_value, new_value, effective_at, evidence_url
    )
    return signal


def build_price_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    models: dict[str, dict[str, Any]] = {}
    for raw in payload.get("models") or []:
        if not isinstance(raw, dict):
            continue
        provider = str(raw.get("provider") or "").strip()
        model_id = str(raw.get("model_id") or "").strip()
        if not provider or not model_id:
            continue
        key = f"{provider.lower()}::{model_id.lower()}"
        model = {
            "provider": provider,
            "model_id": model_id,
            "model_name": str(raw.get("model_name") or model_id).strip(),
        }
        for field in PRICE_FIELDS:
            model[field] = raw.get(field)
        models[key] = model
    return {
        "source_last_updated": str(payload.get("last_updated") or "").strip(),
        "models": models,
    }


def diff_price_snapshots(
    previous: dict[str, Any], current: dict[str, Any], detected_at: str
) -> list[dict[str, Any]]:
    old_models = previous.get("models") if isinstance(previous, dict) else None
    new_models = current.get("models") if isinstance(current, dict) else None
    if not isinstance(old_models, dict) or not old_models or not isinstance(new_models, dict):
        return []
    effective_at = current.get("source_last_updated") or detected_at
    out: list[dict[str, Any]] = []
    for key in sorted(set(old_models) | set(new_models)):
        old = old_models.get(key)
        new = new_models.get(key)
        if old is None:
            out.append(
                _signal(
                    event_type="MODEL_PRICE_ADDED",
                    category="price",
                    title=f"{new['provider']} 新增 {new['model_name']} 價格資料",
                    summary="結構化價格追蹤器新增此模型；請由來源連結核對官方定價。",
                    detected_at=detected_at,
                    effective_at=effective_at,
                    source_name="LLM Price Tracker",
                    source_url=PRICE_HOME,
                    evidence_url=PRICE_URL,
                    provider=new["provider"],
                    product=new["model_name"],
                    verification_status="reported",
                )
            )
            continue
        if new is None:
            out.append(
                _signal(
                    event_type="MODEL_PRICE_REMOVED",
                    category="price",
                    title=f"{old['provider']} 的 {old['model_name']} 價格資料移除",
                    summary="資料自第三方追蹤器移除，不等同官方確認模型下架。",
                    detected_at=detected_at,
                    effective_at=effective_at,
                    source_name="LLM Price Tracker",
                    source_url=PRICE_HOME,
                    evidence_url=PRICE_URL,
                    provider=old["provider"],
                    product=old["model_name"],
                    verification_status="candidate",
                )
            )
            continue
        for field, (label, unit) in PRICE_FIELDS.items():
            old_value = old.get(field)
            new_value = new.get(field)
            if old_value == new_value:
                continue
            event_type = "API_PRICE_CHANGE" if old_value is not None and new_value is not None else "PRICE_TERM_CHANGE"
            out.append(
                _signal(
                    event_type=event_type,
                    category="price",
                    title=f"{new['provider']} {new['model_name']}：{label}異動",
                    summary="系統以結構化資料比對得到此差異；第三方追蹤結果仍應連回官方價格頁確認。",
                    detected_at=detected_at,
                    effective_at=effective_at,
                    source_name="LLM Price Tracker",
                    source_url=PRICE_HOME,
                    evidence_url=PRICE_URL,
                    provider=new["provider"],
                    product=new["model_name"],
                    field=field,
                    old_value=old_value,
                    new_value=new_value,
                    unit=unit,
                    verification_status="reported",
                )
            )
    return out


def build_free_tier_snapshot(payload: Any) -> dict[str, Any]:
    providers: dict[str, dict[str, Any]] = {}
    for raw in payload if isinstance(payload, list) else []:
        if not isinstance(raw, dict):
            continue
        provider_id = str(raw.get("id") or "").strip()
        if not provider_id:
            continue
        limits = raw.get("limits") if isinstance(raw.get("limits"), dict) else {}
        availability = raw.get("availability") if isinstance(raw.get("availability"), dict) else {}
        sources = raw.get("official_sources") if isinstance(raw.get("official_sources"), list) else []
        official_url = next(
            (str(item.get("url")) for item in sources if isinstance(item, dict) and item.get("url")),
            FREE_TIER_HOME,
        )
        providers[provider_id] = {
            "name": str(raw.get("name") or provider_id).strip(),
            "category": str(raw.get("category") or "").strip(),
            "models": sorted(str(model).strip() for model in raw.get("models") or [] if str(model).strip()),
            "requests_per_minute": limits.get("requests_per_minute"),
            "requests_per_day": limits.get("requests_per_day"),
            "availability_status": availability.get("status"),
            "accepting_new_users": availability.get("accepting_new_users"),
            "source_checked_at": str(raw.get("source_checked_at") or "").strip(),
            "official_url": official_url,
        }
    return {"providers": providers}


def diff_free_tier_snapshots(
    previous: dict[str, Any], current: dict[str, Any], detected_at: str
) -> list[dict[str, Any]]:
    old_providers = previous.get("providers") if isinstance(previous, dict) else None
    new_providers = current.get("providers") if isinstance(current, dict) else None
    if not isinstance(old_providers, dict) or not old_providers or not isinstance(new_providers, dict):
        return []
    out: list[dict[str, Any]] = []
    for provider_id in sorted(set(new_providers) - set(old_providers)):
        new = new_providers[provider_id]
        out.append(
            _signal(
                event_type="FREE_TIER_CHANGE",
                category="free_tier",
                title=f"免費額度目錄新增 {new['name']}",
                summary="社群目錄新增此 provider；請由卡片連結確認官方資格與限制。",
                detected_at=detected_at,
                effective_at=new.get("source_checked_at") or detected_at,
                source_name="Free LLM APIs",
                source_url=FREE_TIER_HOME,
                evidence_url=new.get("official_url") or FREE_TIER_HOME,
                provider=new["name"],
                field="provider",
                old_value="absent",
                new_value="listed",
                verification_status="reported",
            )
        )
    for provider_id in sorted(set(old_providers) - set(new_providers)):
        old = old_providers[provider_id]
        out.append(
            _signal(
                event_type="FREE_TIER_CHANGE",
                category="free_tier",
                title=f"免費額度目錄移除 {old['name']}",
                summary="社群目錄移除不等同官方立即取消，必須由官方來源確認。",
                detected_at=detected_at,
                effective_at=detected_at,
                source_name="Free LLM APIs",
                source_url=FREE_TIER_HOME,
                evidence_url=old.get("official_url") or FREE_TIER_HOME,
                provider=old["name"],
                field="provider",
                old_value="listed",
                new_value="absent",
                verification_status="candidate",
            )
        )
    for provider_id in sorted(set(old_providers) & set(new_providers)):
        old = old_providers[provider_id]
        new = new_providers[provider_id]
        effective_at = new.get("source_checked_at") or detected_at
        for field, label, unit in (
            ("requests_per_minute", "RPM", "requests / minute"),
            ("requests_per_day", "RPD", "requests / day"),
            ("availability_status", "可用狀態", ""),
            ("accepting_new_users", "新使用者註冊", ""),
        ):
            if old.get(field) == new.get(field):
                continue
            out.append(
                _signal(
                    event_type="RATE_LIMIT_CHANGE" if field.startswith("requests_") else "FREE_TIER_CHANGE",
                    category="free_tier",
                    title=f"{new['name']} 免費額度：{label}異動",
                    summary="社群目錄偵測到變更；卡片連結保留其引用的官方資料頁。",
                    detected_at=detected_at,
                    effective_at=effective_at,
                    source_name="Free LLM APIs",
                    source_url=FREE_TIER_HOME,
                    evidence_url=new.get("official_url") or FREE_TIER_HOME,
                    provider=new["name"],
                    field=field,
                    old_value=old.get(field),
                    new_value=new.get(field),
                    unit=unit,
                    verification_status="reported",
                )
            )
        old_models = set(old.get("models") or [])
        new_models = set(new.get("models") or [])
        for model in sorted(new_models - old_models):
            out.append(
                _signal(
                    event_type="FREE_MODEL_ADDED",
                    category="free_tier",
                    title=f"{new['name']} 免費清單新增 {model}",
                    summary="此為社群目錄變動，仍需由官方來源確認實際資格與額度。",
                    detected_at=detected_at,
                    effective_at=effective_at,
                    source_name="Free LLM APIs",
                    source_url=FREE_TIER_HOME,
                    evidence_url=new.get("official_url") or FREE_TIER_HOME,
                    provider=new["name"],
                    product=model,
                    verification_status="reported",
                )
            )
        for model in sorted(old_models - new_models):
            out.append(
                _signal(
                    event_type="FREE_MODEL_REMOVED",
                    category="free_tier",
                    title=f"{new['name']} 免費清單移除 {model}",
                    summary="清單移除不必然代表官方立即取消，請由官方來源確認。",
                    detected_at=detected_at,
                    effective_at=effective_at,
                    source_name="Free LLM APIs",
                    source_url=FREE_TIER_HOME,
                    evidence_url=new.get("official_url") or FREE_TIER_HOME,
                    provider=new["name"],
                    product=model,
                    verification_status="candidate",
                )
            )
    return out


def parse_canary_atom(content: bytes) -> list[dict[str, str]]:
    root = ET.fromstring(content)
    entries: list[dict[str, str]] = []
    for node in root.findall(".//{*}entry"):
        link_node = node.find("{*}link")
        raw_content = node.findtext("{*}content") or node.findtext("{*}summary") or ""
        plain = re.sub(r"<[^>]+>", " ", html.unescape(raw_content))
        entries.append(
            {
                "id": str(node.findtext("{*}id") or "").strip(),
                "title": " ".join(str(node.findtext("{*}title") or "").split()),
                "url": str(link_node.get("href") if link_node is not None else "").strip(),
                "updated": str(node.findtext("{*}updated") or "").strip(),
                "content": " ".join(plain.split()),
            }
        )
    return [entry for entry in entries if entry["id"] and entry["title"] and entry["url"]]


def is_usage_policy_candidate(entry: dict[str, str]) -> bool:
    text = f"{entry.get('title', '')} {entry.get('content', '')}"
    return any(pattern.search(text) for pattern in CANARY_PATTERNS)


def canary_signal(entry: dict[str, str], feed: dict[str, str], detected_at: str) -> dict[str, Any]:
    return _signal(
        event_type="USAGE_POLICY_CANDIDATE",
        category="usage_policy",
        title=f"速報候選：{feed['name']} 偵測到額度相關變更",
        summary=entry["title"],
        detected_at=detected_at,
        effective_at=entry.get("updated") or detected_at,
        source_name=feed["name"],
        source_url=feed["home"],
        evidence_url=entry["url"],
        verification_status="candidate",
    )


def _fetch_json(session: requests.Session, url: str) -> Any:
    response = session.get(url, timeout=20, headers={"Accept": "application/json"})
    response.raise_for_status()
    return response.json()


def _fetch_canary(session: requests.Session, feed: dict[str, str]) -> list[dict[str, str]]:
    response = session.get(
        feed["url"], timeout=20, headers={"Accept": "application/atom+xml, application/xml, text/xml"}
    )
    response.raise_for_status()
    return parse_canary_atom(response.content)


def _kept_signals(previous: Any, now: datetime) -> list[dict[str, Any]]:
    signals = previous.get("signals") if isinstance(previous, dict) else []
    kept: list[dict[str, Any]] = []
    for signal in signals if isinstance(signals, list) else []:
        if not isinstance(signal, dict):
            continue
        detected = _parse_iso(signal.get("detected_at"))
        # Public signal lanes use the same 24-hour reader window as the main
        # news board and LLM release radar. Sensor state itself remains
        # separate so future comparisons still have a baseline.
        retention = timedelta(hours=MARKET_SIGNAL_WINDOW_HOURS)
        if detected and detected >= now - retention:
            kept.append(signal)
    return kept


def run_market_sensors(
    session: requests.Session,
    now: datetime,
    previous_state: Any,
    previous_payload: Any,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    detected_at = _iso(now)
    state = dict(previous_state) if isinstance(previous_state, dict) else {"schema_version": 1}
    signals = _kept_signals(previous_payload, now)
    statuses: list[dict[str, Any]] = []

    started = time.perf_counter()
    try:
        current_price = build_price_snapshot(_fetch_json(session, PRICE_URL))
        old_price = state.get("price") if isinstance(state.get("price"), dict) else {}
        price_signals = diff_price_snapshots(old_price, current_price, detected_at)
        if old_price and len(current_price.get("models") or {}) < max(1, int(len(old_price.get("models") or {}) * 0.8)):
            raise ValueError("Price dataset shrank below the 80% safety gate")
        state["price"] = current_price
        signals.extend(price_signals)
        statuses.append({"site_id": "market_price", "site_name": "LLM Price Tracker", "ok": True,
                         "item_count": len(current_price.get("models") or {}), "signal_count": len(price_signals),
                         "duration_ms": int((time.perf_counter() - started) * 1000), "error": None})
    except Exception as exc:
        statuses.append({"site_id": "market_price", "site_name": "LLM Price Tracker", "ok": False,
                         "item_count": 0, "signal_count": 0,
                         "duration_ms": int((time.perf_counter() - started) * 1000), "error": str(exc)})

    started = time.perf_counter()
    try:
        current_free = build_free_tier_snapshot(_fetch_json(session, FREE_TIER_URL))
        old_free = state.get("free_tier") if isinstance(state.get("free_tier"), dict) else {}
        free_signals = diff_free_tier_snapshots(old_free, current_free, detected_at)
        if old_free and len(current_free.get("providers") or {}) < max(1, int(len(old_free.get("providers") or {}) * 0.8)):
            raise ValueError("Free-tier dataset shrank below the 80% safety gate")
        state["free_tier"] = current_free
        signals.extend(free_signals)
        statuses.append({"site_id": "market_free_tier", "site_name": "Free LLM APIs", "ok": True,
                         "item_count": len(current_free.get("providers") or {}), "signal_count": len(free_signals),
                         "duration_ms": int((time.perf_counter() - started) * 1000), "error": None})
    except Exception as exc:
        statuses.append({"site_id": "market_free_tier", "site_name": "Free LLM APIs", "ok": False,
                         "item_count": 0, "signal_count": 0,
                         "duration_ms": int((time.perf_counter() - started) * 1000), "error": str(exc)})

    canary_state = dict(state.get("canary") or {})
    for feed in CANARY_FEEDS:
        started = time.perf_counter()
        try:
            entries = _fetch_canary(session, feed)
            old_seen = set(canary_state.get(feed["id"]) or [])
            new_signals = [
                canary_signal(entry, feed, detected_at)
                for entry in entries
                if old_seen and entry["id"] not in old_seen and is_usage_policy_candidate(entry)
            ]
            canary_state[feed["id"]] = [entry["id"] for entry in entries][:100]
            signals.extend(new_signals)
            statuses.append({"site_id": f"canary_{feed['id']}", "site_name": feed["name"], "ok": True,
                             "item_count": len(entries), "signal_count": len(new_signals),
                             "duration_ms": int((time.perf_counter() - started) * 1000), "error": None})
        except Exception as exc:
            statuses.append({"site_id": f"canary_{feed['id']}", "site_name": feed["name"], "ok": False,
                             "item_count": 0, "signal_count": 0,
                             "duration_ms": int((time.perf_counter() - started) * 1000), "error": str(exc)})
    state["canary"] = canary_state
    state["schema_version"] = 1
    state["updated_at"] = detected_at

    deduped = {str(signal.get("id")): signal for signal in signals if isinstance(signal, dict) and signal.get("id")}
    ordered = sorted(
        deduped.values(),
        key=lambda signal: (
            int(signal.get("timeliness_rank") or 9),
            str(signal.get("detected_at") or ""),
        ),
        reverse=False,
    )
    payload = {
        "schema_version": 1,
        "generated_at": detected_at,
        "cadence_minutes": 30,
        "signals": ordered,
    }
    return payload, state, statuses
