"""Bounded, clock-explicit brief event projection. No providers or network I/O.

Original stories and archive records are inputs, never mutated. Matching uses
source text, not translated/generated summaries. See the BR02 v1 contract.
"""
from __future__ import annotations

import copy
import calendar
import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

try:
    from scripts import corroboration
except ModuleNotFoundError:  # direct generator invocation
    import corroboration

UTC = timezone.utc
VERSION = "brief-event-v1"
STATE_FILE = "brief-event-state.json"
MAX_BYTES = 8 * 1024 * 1024
MAX_EVENTS = 10_000
MAX_PHASES = 16
RETENTION_DAYS = 21
TIME_BASES = {"source_report", "first_observed", "reported_day_upper_bound"}
PHASE_KINDS = {"baseline", "announced", "available", "expanded_availability", "patched", "observed_exploitation", "value_changed"}
ACTION_KINDS = {"model_release", "speed_tier_release", "context_change", "capability_change", "platform_availability", "security_disclosure", "pricing_change", "legacy_story", "article"}


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def parse(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return result.astimezone(UTC) if result.tzinfo else None
    except (ValueError, OverflowError):
        return None


def stamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def normalized(value: Any) -> str:
    return unicodedata.normalize("NFKC", str(value or "")).lower().replace("—", "-").replace("–", "-")


def asserted_match(pattern: str, text: str):
    for match in re.finditer(pattern, text):
        prefix = re.split(r"[。.;]", text[:match.start()])[-1][-40:]
        if not re.search(r"\b(?:not|never|no|could|might|may|would|hypothetical|potential)\b|尚未|並未|并未|未曾|沒有|没有|可能", prefix):
            return match
    return None


def url_key(value: Any) -> str:
    try:
        p = urlsplit(str(value or ""))
        if p.scheme not in {"https", "http"} or not p.hostname:
            return ""
        query = [(k, v) for k, v in parse_qsl(p.query) if not k.lower().startswith("utm_")
                 and k.lower() not in {"fbclid", "gclid", "ref"}]
        return urlunsplit(("https", p.netloc.lower(), p.path.rstrip("/"), urlencode(sorted(query)), ""))
    except ValueError:
        return ""


def key_for(subject: str, action: str, **parts: Any) -> str:
    return canonical({"v": 1, "subject": subject, "action": action, **parts}).decode()


def event_id(key: str) -> str:
    return "be1_" + hashlib.sha256(key.encode()).hexdigest()[:24]


@dataclass(frozen=True)
class StateInput:
    status: str
    payload: dict[str, Any] | None = None
    error_code: str | None = None


@dataclass(frozen=True)
class ArchiveMeta:
    status: str
    generated_at: str | None = None


@dataclass
class BriefEventResult:
    projection: dict[str, Any]
    next_state: dict[str, Any] | None
    daily_items: list[dict[str, Any]]
    diagnostics: dict[str, Any]


def validate_state(state: Any) -> bool:
    """Validate retained history before trusting it; never replace failure by {}."""
    try:
        if not isinstance(state, dict) or state.get("schema_version") != 1:
            return False
        if state.get("record_type") != "brief_event_state" or state.get("matcher_version") != VERSION:
            return False
        if state.get("history_complete") is not False or len(canonical(state)) > MAX_BYTES:
            return False
        if not parse(state["generated_at"]) or not parse(state["archive_generated_at"]):
            return False
        if state["revision"] != digest({k: v for k, v in state.items() if k != "revision"}):
            return False
        entries = state["events"]
        if not isinstance(entries, list) or len(entries) > MAX_EVENTS:
            return False
        ids, aliases = set(), set()
        for e in entries:
            eid = e["brief_event_id"]
            if eid in ids or eid != event_id(e["identity"]["key"]) or len(canonical(e["identity"])) > 1024:
                return False
            ids.add(eid)
            ident = e["identity"]
            if (ident["action"] not in ACTION_KINDS or not isinstance(ident["subject"], str)
                    or not 0 < len(ident["subject"]) <= 160
                    or ident["version"] is not None and not isinstance(ident["version"], str)
                    or ident["batch_key"] is not None and not isinstance(ident["batch_key"], str)
                    or e["initial_basis"] not in TIME_BASES):
                return False
            for values, bound in [(ident["scope"], 16), (ident["facts"], 32), (e["match_keys"], 16)]:
                if not isinstance(values, list) or len(values) > bound or len(values) != len(set(values)) or any(not isinstance(v, str) for v in values):
                    return False
            if any(not re.fullmatch("[0-9a-f]{64}", k) for k in e["match_keys"]):
                return False
            for name in ("initial_effective_at", "first_observed_at", "last_mentioned_at"):
                if not parse(e[name]):
                    return False
            for name in ("last_material_at", "last_reported_at"):
                if e[name] is not None and not parse(e[name]):
                    return False
            if any(parse(e[name]) > parse(state["generated_at"]) + timedelta(hours=6)
                   for name in ("initial_effective_at", "first_observed_at", "last_mentioned_at")):
                return False
            if len(e["alias_event_ids"]) > 16 or len(e["match_keys"]) > 16 or len(e["phases"]) > MAX_PHASES:
                return False
            if len(set(e["alias_event_ids"])) != len(e["alias_event_ids"]) or aliases.intersection(e["alias_event_ids"]):
                return False
            aliases.update(e["alias_event_ids"])
            phase_ids = set()
            if not e["phases"]:
                return False
            for p in e["phases"]:
                if (p["phase_id"] in phase_ids or p["phase_id"] != "bp1_" + p["fingerprint"][:24]
                        or not re.fullmatch("[0-9a-f]{64}", p["fingerprint"])
                        or not parse(p["effective_at"]) or len(p["evidence_ids"]) > 8
                        or len(p["fact_keys"]) > 16 or p["kind"] not in PHASE_KINDS
                        or p["time_basis"] not in TIME_BASES
                        or parse(p["effective_at"]) < parse(e["initial_effective_at"])
                        or parse(p["effective_at"]) > parse(state["generated_at"]) + timedelta(hours=6)
                        or len(p["evidence_ids"]) != len(set(p["evidence_ids"]))):
                    return False
                phase_ids.add(p["phase_id"])
            if e["last_material_at"] is not None and not any(
                    p["effective_at"] == e["last_material_at"] and p["kind"] in {"available", "expanded_availability", "patched", "observed_exploitation", "value_changed"}
                    for p in e["phases"]):
                return False
        return not bool(ids & aliases)
    except (KeyError, TypeError, ValueError, OverflowError):
        return False


def load_state(path: Path) -> StateInput:
    if not path.exists():
        return StateInput("missing")
    try:
        if path.stat().st_size > MAX_BYTES:
            return StateInput("corrupt", error_code="state_too_large")
        value = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(value, dict) and value.get("schema_version") not in (None, 1):
            return StateInput("unsupported", error_code="unsupported_schema")
        if validate_state(value):
            return StateInput("valid", value)
        return StateInput("corrupt", error_code="state_invalid")
    except (OSError, ValueError, TypeError):
        return StateInput("corrupt", error_code="state_unreadable")


MODEL_RE = re.compile(
    r"gpt[-\s]*\d+(?:\.\d+)*(?:[-\s]*(?:astra|sol|luna|ultrafast|mini|nano|pro|max|preview))*(?![a-z])"
    r"|claude[-\s]*(?:(?:haiku|sonnet|opus|fable)[-\s]*)?\d+(?:\.\d+)*(?:[-\s]*(?:max|preview))?"
    r"|gemini[-\s]*\d+(?:\.\d+)*(?:[-\s]*(?:argon|carbon|pro|flash|lite|preview))*"
    r"|(?:qwen|deepseek|glm|kimi|minimax|voxtral|mistral|llama|mellum|vidu|grok|ling|ming)[-\s]*[vrkqm]?\d+(?:\.\d+)*(?:[-\s]*(?:vl|coder|omni|flash|preview|pro|lite|\d+b))*",
    re.I,
)
RELEASE = re.compile(r"發[佈表]|发布|推出|甩出|亮出|端出|擴大|擴展|扩展|拓展|上[線线]|登場|开放|開放|\badds\b|\bexpands?\b|launch|releas|introduc|arriv|comes to|now available|available for|bring|next era|in github copilot|on amazon bedrock", re.I)
SOFTWARE = re.compile(r"(?<![a-z])(php|openssl|openssh|wordpress|linux|chrome|firefox|node\.?js|python|redis|curl|apache|nginx)(?![a-z])", re.I)
SECURITY = re.compile(r"漏洞|資安|安全漏洞|vulnerabilit|\bflaws?\b|\bholes\b|\bsecurity (?:release|issue)\b|\bcve-", re.I)


@dataclass
class Claim:
    row: dict[str, Any]
    key: str
    subject: str
    action: str
    facts: set[str] = field(default_factory=set)
    cves: set[str] = field(default_factory=set)
    names: set[str] = field(default_factory=set)
    rule: str = "R6"
    strength: str = "unresolved"
    phase: str = "baseline"
    phase_facts: tuple[str, ...] = ()
    effective: datetime | None = None
    basis: str = "source_report"
    unknown_update: bool = False
    scope: tuple[str, ...] = ()
    version: str | None = None
    spans: list[str] = field(default_factory=list)


def _number(value: str, unit: str) -> int:
    return round(float(value) * {"k": 1000, "m": 1000000, "萬": 10000, "万": 10000}.get(unit.lower(), 1))


def _extract_claim(row: dict[str, Any], now: datetime) -> Claim:
    title = normalized(row.get("title_original") or row.get("title"))[:2048]
    summary = normalized(row.get("summary"))[:8192]
    text = title + " " + summary
    when = parse(row.get("published_at")) or parse(row.get("first_seen_at"))
    article_subject = "article:" + hashlib.sha256((url_key(row.get("url")) or str(row.get("id"))).encode()).hexdigest()
    fallback = key_for(article_subject, "article")
    c = Claim(row, fallback, article_subject, "article",
              effective=min(when, now) if when else None,
              basis="source_report" if parse(row.get("published_at")) else "first_observed")
    if not when or when > now + timedelta(hours=6) or row.get("duplicate_of"):
        c.effective = None
        return c
    observed = parse(row.get("first_seen_at"))
    if observed and observed > now:
        c.effective = None
        return c
    # Software security is the subject even when the discovering AI appears in title.
    soft = SOFTWARE.search(title) if SECURITY.search(text) else None
    if soft:
        c.spans.append(f"normalized.title:{soft.start()}:{soft.end()}:software")
        c.subject, c.action = "software:" + soft[1].lower(), "security_disclosure"
        matches = list(re.finditer(r"cve[-\s]*(\d{4})[-\s]*(\d{4,8})(?:\s*[,、]\s*(\d{4,8}))?", text))
        for m in matches:
            c.cves.add(f"CVE-{m[1]}-{m[2]}")
            if m[3]:
                c.cves.add(f"CVE-{m[1]}-{m[3]}")
        c.names = set(re.findall(r"(?<![a-z0-9])[a-z]+\d+shell(?![a-z0-9])", text))
        for actor, pattern in {"openai": r"openai", "wiz": r"(?<![a-z])wiz(?![a-z])", "calif": r"(?<![a-z])calif(?![a-z])", "aws": r"amazon web services|\baws\b"}.items():
            if re.search(pattern, text):
                c.facts.add("actor:" + actor)
        if re.search(r"兩[項个個]|两[项个]|\btwo\b", text) or len(c.cves) == 2:
            c.facts.add("count:2")
        if re.search(r"未經身分驗證|未經身份驗證|未经身份验证|unauthenticated", text):
            c.facts.add("mechanism:unauthenticated")
        if re.search(r"remote.code.execution|\brce\b|遠[端程].*執行|远程.*执行", text):
            c.facts.add("mechanism:rce")
        if re.search(r"(?:two.month|兩個月|两个月|2個月|2个月)", text):
            c.facts.add("coord_months:2")
        if re.search(r"foundation|官方維護|官方维护|\bproject\b", text):
            c.facts.add("maintainer:" + soft[1].lower())
        c.facts.update("named:" + n for n in c.names)
        c.facts.update("cve:" + n for n in c.cves)
        if re.search(r"\bunpatched\b|no patch (?:is )?available|尚無修補|尚无修补|尚未修補|尚未修补", text):
            c.facts.add("patch_status:unpatched")
        if asserted_match(r"released fixes|patch (?:is )?(?:now )?available|now patched|已釋出修補|已发布修补|已發佈修補", text):
            c.phase = "patched"
            c.phase_facts = ("patched",)
        # Explicit calendar mentions only; publication date is not a second fact.
        months = {name.lower(): i for names in (calendar.month_name, calendar.month_abbr)
                  for i, name in enumerate(names) if name}
        month_names = "|".join(sorted(months, key=len, reverse=True))
        for m in re.finditer(r"(?:(\d{1,2})月|(?<![a-z])(" + month_names + r")\.?\s+)(\d{1,2})(?:日|st|nd|rd|th)?", text):
            month = int(m[1]) if m[1] else months[m[2]]
            year = when.year - (1 if month > when.month + 2 else 0)
            try:
                day = datetime(year, month, int(m[3]), tzinfo=UTC).date()
            except ValueError:
                continue
            c.facts.add(f"announcement_day:{day.isoformat()}")
        if c.cves:
            c.key = key_for(c.subject, c.action, batch=sorted(c.cves))
            c.rule, c.strength = "R2", "strong"
        elif c.names:
            c.key = key_for(c.subject, c.action, named=sorted(c.names))
            c.rule, c.strength = "R2", "strong"
        # A circulating PoC or a hypothetical attack is not an observed attack.
        observation = asserted_match(r"logged (?:attempts|attacks)|being [\"“]?broadly exploited|actively exploited|observed (?:attacks|exploitation)|已遭(?:實際|实际)|已(?:被)?(?:大規模|大规模)利用", text)
        if observation:
            c.phase = "observed_exploitation"
            c.phase_facts = ("observed_exploitation",)
            field_name = "title" if observation.start() < len(title) else "summary"
            offset = 0 if field_name == "title" else len(title) + 1
            c.spans.append(f"normalized.{field_name}:{observation.start()-offset}:{observation.end()-offset}:observed_attack")
        return c

    models = sorted({"-".join(re.findall(r"[a-z]+|\d+(?:\.\d+)*", m.group())) for m in MODEL_RE.finditer(title)})
    if len(models) == 1:
        c.spans.extend(f"normalized.title:{m.start()}:{m.end()}:full_model" for m in MODEL_RE.finditer(title))
        model = models[0]
        c.subject, c.version = "model:" + model, model
        scopes = tuple(x for x in ("codex", "work") if x in text)
        price = re.search(r"(input|output|輸入|输入|輸出|输出).{0,60}?(?:from|從|从)\s*\$?(\d+(?:\.\d+)?)\s*(?:usd|美元)?\s*(?:to|至|到|→)\s*\$?(\d+(?:\.\d+)?)", text)
        dated = re.search(r"(?:effective|生效|自)\s*(\d{4}-\d{2}-\d{2})", text)
        if price and dated and re.search(r"million.{0,10}tokens|每百萬.{0,8}token|每百万.{0,8}token", text):
            limit = re.search(r"(?:context|上下文).{0,12}?(\d+(?:\.\d+)*)\s*(k|萬|万)", text)
            conditions = ["context:" + str(_number(limit[1], limit[2]))] if limit else []
            metric = "input_tokens" if price[1] in {"input", "輸入", "输入"} else "output_tokens"
            c.action = "pricing_change"
            c.key = key_for(c.subject, c.action, metric=metric, unit="million_tokens",
                            before=price[2], after=price[3], effective_day=dated[1], conditions=conditions)
            c.facts = {f"metric:{metric}", f"price_from:{price[2]}", f"price_to:{price[3]}", *conditions}
            c.rule, c.strength = "R4", "strong"
            return c
        if re.search(r"上下文|\bcontext\b", title) or re.search(r"擴容|扩容", title):
            nums = [_number(m[1], m[2] or "") for m in re.finditer(r"(\d+(?:\.\d+)*)\s*(k(?![a-z])|m(?![a-z])|萬|万)", text)]
            nums = sorted({n for n in nums if n >= 1000})
            if len(nums) == 2:
                c.action, c.scope = "context_change", scopes
                c.facts = {f"context_from:{nums[0]}", f"context_to:{nums[1]}"}
                c.key = key_for(c.subject, c.action, platform=list(scopes), before=nums[0], after=nums[1], unit="tokens")
                c.rule, c.strength = "R4", "strong"
                return c
        platform = "github-copilot" if re.search(r"github copilot", title) else "amazon-bedrock" if re.search(r"(?:amazon )?bedrock", title) else None
        if platform and RELEASE.search(text):
            c.action, c.scope = "platform_availability", (platform,)
            c.key = key_for(c.subject, c.action, platform=platform)
            c.rule, c.strength = "R3", "strong"
            return c
        if RELEASE.search(title) or ("ultrafast" in model and re.search(r"coming soon|即將|即将", title)):
            c.action = "speed_tier_release" if "ultrafast" in model else "model_release"
            c.key = key_for(c.subject, c.action, scope="native")
            c.rule, c.strength = "R3", "strong"
            if re.search(r"coming soon|即將|即将|\b(?:will|plans? to|set to)\b.*(?:launch|releas|available)", title):
                c.phase = "announced"
                c.phase_facts = ("announced",)
            elif re.search(r"app|subscribers|developers|開發者|开发者|全球|worldwide", title):
                c.phase = "available"
                c.phase_facts = ("available",)
                if re.search(r"部分|some|partial", text):
                    c.unknown_update = True
            elif re.search(r"limited to|select testers|cyber defenders|受信任|限制.*測試", text):
                c.phase = "announced"
                c.phase_facts = ("announced",)
            return c

    # Product capability identity requires two distinct, concrete dimensions.
    product = next((p for p in ("chatgpt", "copilot", "claude", "gemini") if p in title), None)
    if product and re.search(r"chrome|瀏覽器|浏览器|browser|擴展|扩展|extension", text):
        features = set()
        if re.search(r"標籤頁|标签页|標籤|tabs|tab context", text):
            features.add("read_open_tabs")
        if re.search(r"操作|代辦|代办|任務|任务|填表|表單|表单|automation|automate|browser.actions", text):
            features.add("browser_actions")
        if len(features) >= 2:
            c.subject, c.action, c.facts = "product:" + product, "capability_change", features
            c.scope = ("browser",)
            c.key = key_for(c.subject, c.action, platform="browser", features=sorted(features))
            c.rule, c.strength = "R4", "strong"
            c.unknown_update = bool(re.search(r"所有套餐|all plans|不再限", text))
    return c


def extract_claim(row: dict[str, Any], now: datetime) -> Claim:
    c = _extract_claim(row, now)
    title = normalized(row.get("title_original") or row.get("title"))[:2048]
    if c.action in {"model_release", "platform_availability"} and re.search(r"\bexpands?\b|擴大|擴展|扩展|拓展", title):
        regions = {region for region, pattern in {"TW": r"taiwan|台灣|臺灣|台湾", "EU": r"europe|歐盟|欧盟|歐洲|欧洲", "US": r"united states|美國|美国"}.items() if re.search(pattern, title)}
        if regions:
            c.phase = "expanded_availability"
            c.phase_facts = tuple("region:" + r for r in sorted(regions))
    if c.phase != "baseline" and not corroboration.identity(row)[0]:
        c.unknown_update = True
    # A retrospective model announcement is bounded by its stated calendar
    # date, not the date the next publisher rephrased it. Observed attacks use
    # first report time instead, so historical occurrence dates aren't confused
    # with first disclosure of a genuinely new observation.
    if c.effective is None or c.action not in {"model_release", "speed_tier_release", "context_change", "platform_availability"}:
        return c
    text = normalized(row.get("summary"))[:8192]
    clauses = re.split(r"[。;；\n]|(?<=[a-z])\.\s+", text)
    months = {name.lower(): i for i, name in enumerate(calendar.month_name) if name}
    dates = []
    for clause in clauses:
        if not re.search(r"launch|releas|open|rollout|發[佈表]|发布|推出|開放|开放|上線|上线|宣布", clause):
            continue
        for m in re.finditer(r"(?:(\d{1,2})月|(january|february|march|april|may|june|july|august|september|october|november|december)\s+)(\d{1,2})(?:日|st|nd|rd|th)?", clause):
            month = int(m[1]) if m[1] else months[m[2]]
            year = c.effective.year - (1 if month > c.effective.month + 2 else 0)
            try:
                dates.append(datetime(year, month, int(m[3]), tzinfo=UTC) + timedelta(days=1, hours=12))
            except ValueError:
                continue
    if dates and dates[-1] < c.effective:
        c.effective, c.basis = dates[-1], "reported_day_upper_bound"
    return c


@dataclass
class Group:
    key: str
    subject: str
    action: str
    claims: list[Claim] = field(default_factory=list)
    facts: set[str] = field(default_factory=set)
    cves: set[str] = field(default_factory=set)
    names: set[str] = field(default_factory=set)
    old: dict[str, Any] | None = None

    def attach(self, c: Claim, *, context: bool = False) -> None:
        self.claims.append(c)
        if not context:
            self.facts.update(c.facts)
            self.cves.update(c.cves)
            self.names.update(c.names)


def _empty(now: datetime, reason: str) -> BriefEventResult:
    diag = {"recovery_mode": "unavailable", "errors": [reason]}
    p = {"record_type": "brief_event_projection", "schema_version": 1,
         "matcher_version": VERSION, "generated_at": stamp(now), "status": "unavailable",
         "history_complete": False, "state_revision": None, "events": [],
         "selected_event_ids": [], "diagnostics": diag}
    p["generation_id"] = "bg1_" + digest(p)[:24]
    return BriefEventResult(p, None, [], diag)


def unavailable(now: datetime, reason: str) -> BriefEventResult:
    """Generator boundary can degrade a logical event failure independently."""
    return _empty(now, reason)


def _phase_key(key: str, kind: str, facts: tuple[str, ...]) -> str:
    return digest({"root": key, "kind": kind, "facts": list(facts)})


def build_brief_events(*, stories: list[dict[str, Any]], archive_records: list[dict[str, Any]],
                       archive_meta: ArchiveMeta | dict[str, Any],
                       previous_state: StateInput | dict[str, Any], now: datetime,
                       window_hours: int = 24,
                       record_builder: Callable[..., dict[str, Any]] | None = None,
                       ranker: Callable[[dict[str, Any]], Any] | None = None) -> BriefEventResult:
    """Project one card per concrete event, preserving bounded previous history.

    record_builder/ranker are pure application adapters: existing importance
    coefficients and publisher priorities remain owned by update_news.
    """
    now = now.astimezone(UTC)
    state_in = previous_state if isinstance(previous_state, StateInput) else StateInput(**previous_state)
    meta = archive_meta if isinstance(archive_meta, ArchiveMeta) else ArchiveMeta(**archive_meta)
    if state_in.status == "unsupported":
        return _empty(now, "unsupported_state_schema")
    old_payload = state_in.payload if state_in.status == "valid" and validate_state(state_in.payload) else None
    if old_payload and parse(old_payload["generated_at"]) > now + timedelta(hours=6):
        return _empty(now, "future_state")
    if not old_payload and (meta.status != "valid" or not archive_records
                            or not parse(meta.generated_at) or parse(meta.generated_at) > now + timedelta(hours=6)):
        return _empty(now, "insufficient_history")
    recovery = "none" if old_payload else "archive"
    by_id = {str(r["id"]): copy.deepcopy(r) for r in archive_records if r.get("id")}
    seed_stories: dict[str, set[str]] = defaultdict(set)
    display: dict[str, dict[str, Any]] = {}
    fallback_bases: dict[str, dict[str, Any]] = {}
    for s in sorted(stories, key=lambda s: str(s.get("story_id"))):
        refs = s.get("sources") or s.get("items") or [s.get("primary_item") or {}]
        for r in refs:
            if not r.get("id"):
                continue
            rid = str(r["id"])
            seed_stories[rid].add(str(s["story_id"]))
            fallback_bases[rid] = s
            display[rid] = {**r, **(s.get("primary_item") or {})} if r.get("id") == (s.get("primary_item") or {}).get("id") else r
            if rid not in by_id:
                by_id[rid] = copy.deepcopy(r)
    claims = [extract_claim(by_id[i], now) for i in sorted(by_id)]
    claims = [c for c in claims if c.effective is not None]
    original_claims = {str(c.row["id"]): c for c in claims}
    for rid in sorted(by_id):
        target = original_claims.get(str(by_id[rid].get("duplicate_of") or ""))
        if target:
            alias = copy.deepcopy(target)
            alias.row = by_id[rid]
            claims.append(alias)
    by_key: dict[str, Group] = {}
    old_by_hash: dict[str, dict[str, Any]] = {}
    retained: dict[str, dict[str, Any]] = {}
    for e in (old_payload or {}).get("events", []):
        if parse(e["last_mentioned_at"]) < now - timedelta(days=RETENTION_DAYS):
            continue
        retained[e["brief_event_id"]] = copy.deepcopy(e)
        for h in [hashlib.sha256(e["identity"]["key"].encode()).hexdigest(), *e["match_keys"]]:
            old_by_hash[h] = e

    security_groups: dict[str, list[Group]] = defaultdict(list)
    for old in retained.values():
        ident = old["identity"]
        g = Group(ident["key"], ident["subject"], ident["action"],
                  facts=set(ident["facts"]), old=old)
        g.cves = {f[4:] for f in g.facts if f.startswith("cve:")}
        g.names = {f[6:] for f in g.facts if f.startswith("named:")}
        by_key[g.key] = g
        if g.action == "security_disclosure" and g.cves:
            security_groups[g.subject].append(g)

    def new_group(c: Claim) -> Group:
        old = old_by_hash.get(hashlib.sha256(c.key.encode()).hexdigest())
        key = old["identity"]["key"] if old else c.key
        if key not in by_key:
            by_key[key] = Group(key, c.subject, c.action, old=old)
        return by_key[key]

    # Strong roots first. Larger explicit CVE batches absorb their subsets,
    # never join disjoint batches through a vague context attachment.
    strong = sorted((c for c in claims if c.strength == "strong" and (c.action != "security_disclosure" or c.cves)),
                    key=lambda c: (-len(c.cves), c.key, str(c.row["id"])))
    attached: set[str] = set()
    for c in strong:
        compatible = []
        if c.cves:
            compatible = [g for g in security_groups[c.subject] if c.cves <= g.cves]
        g = compatible[0] if len(compatible) == 1 else new_group(c)
        g.attach(c)
        if c.cves and g not in security_groups[c.subject]:
            security_groups[c.subject].append(g)
        attached.add(str(c.row["id"]))
    strong_by_url = defaultdict(list)
    for g in by_key.values():
        for c in g.claims:
            url = url_key(c.row.get("url"))
            if url and g not in strong_by_url[url]:
                strong_by_url[url].append(g)
    for c in claims:
        if str(c.row["id"]) in attached:
            continue
        candidates = [g for g in strong_by_url.get(url_key(c.row.get("url")), [])
                      if (c.action == "article" or c.action == g.action and c.subject == g.subject)
                      and (c.version is None or all(p.version in {None, c.version} for p in g.claims))
                      and (not c.cves or not g.cves or c.cves <= g.cves)]
        if len(candidates) == 1:
            g = candidates[0]
            anchor = min(g.claims, key=lambda p: str(p.row["id"]))
            c.rule, c.strength = "R1", "strong"
            c.subject, c.action, c.version = g.subject, g.action, anchor.version
            c.phase, c.phase_facts = anchor.phase, anchor.phase_facts
            c.unknown_update = anchor.unknown_update
            g.attach(c)
            attached.add(str(c.row["id"]))
    pending = [c for c in claims if str(c.row["id"]) not in attached and c.action == "security_disclosure"]
    # Iterate only strong context enrichment. Weak matches never grow anchors.
    for _ in range(2):
        remaining = []
        for c in pending:
            choices = []
            for g in security_groups[c.subject]:
                if c.cves and g.cves and not c.cves <= g.cves:
                    continue
                shared = c.facts & g.facts
                times = [p.effective for p in g.claims if p.cves]
                if g.old:
                    times.append(parse(g.old["initial_effective_at"]))
                named = bool(c.names & g.names)
                close = bool(times) and min(abs((c.effective - t).total_seconds()) for t in times) <= 36 * 3600
                if named or (close and len(shared - {f for f in shared if f.startswith("cve:")}) >= 2):
                    choices.append((g, shared, named))
            if len(choices) == 1:
                g, shared, named = choices[0]
                weak = not named and not any(f.startswith(("coord_months:", "announcement_day:")) for f in c.facts)
                c.rule, c.strength = "R5", "context_attachment" if weak else "strong"
                g.attach(c, context=weak)
                attached.add(str(c.row["id"]))
            else:
                remaining.append(c)
        pending = remaining
    for c in claims:
        if str(c.row["id"]) not in attached:
            # A software keyword alone is not a security-event identity.
            if c.strength != "strong":
                subject = "article:" + hashlib.sha256((url_key(c.row.get("url")) or str(c.row["id"])).encode()).hexdigest()
                c.key = key_for(subject, "article")
                c.subject, c.action = subject, "article"
            g = new_group(c)
            g.attach(c)

    events, persisted, errors = [], retained.copy(), []
    rank = ranker or (lambda r: (0 if r.get("site_id") == "official_ai" else 3,
                                not bool(r.get("summary")), str(r.get("id"))))
    for key, g in sorted(by_key.items()):
        current = [c for c in g.claims if str(c.row["id"]) in seed_stories]
        if not current:
            continue
        # An article first classified as unresolved can later acquire a strong
        # anchor without losing its event ID. Only unchanged publication
        # evidence permits this promotion; a repurposed URL is not enough.
        old_matches = {g.old["brief_event_id"]: g.old} if g.old else {}
        for c in g.claims:
            fallback_subject = "article:" + hashlib.sha256((url_key(c.row.get("url")) or str(c.row["id"])).encode()).hexdigest()
            fallback_hash = hashlib.sha256(key_for(fallback_subject, "article").encode()).hexdigest()
            prior = old_by_hash.get(fallback_hash)
            if (prior and prior["identity"]["action"] == "article"
                    and prior["last_reported_at"] == c.row.get("published_at")
                    and (prior["identity"]["version"] is None or c.version is None
                         or prior["identity"]["version"] == c.version)):
                old_matches[prior["brief_event_id"]] = prior
        merged_losers = set()
        if len(old_matches) > 1 or old_matches and not g.old:
            ordered_old = sorted(old_matches.values(), key=lambda e: (parse(e["first_observed_at"]), e["brief_event_id"]))
            survivor = copy.deepcopy(ordered_old[0])
            merged_phases = {}
            for prior in ordered_old:
                for p in prior["phases"]:
                    signature = (p["kind"], tuple(p["fact_keys"]))
                    if signature not in merged_phases or parse(p["effective_at"]) < parse(merged_phases[signature]["effective_at"]):
                        merged_phases[signature] = copy.deepcopy(p)
                if prior["brief_event_id"] != survivor["brief_event_id"]:
                    merged_losers.add(prior["brief_event_id"])
            survivor["initial_effective_at"] = min((e["initial_effective_at"] for e in ordered_old), key=parse)
            survivor["alias_event_ids"] = sorted({a for e in ordered_old for a in e["alias_event_ids"]}
                | {e["brief_event_id"] for e in ordered_old if e["brief_event_id"] != survivor["brief_event_id"]})
            survivor["match_keys"] = sorted({k for e in ordered_old for k in e["match_keys"]}
                | {hashlib.sha256(e["identity"]["key"].encode()).hexdigest() for e in ordered_old})
            for p in merged_phases.values():
                p["fingerprint"] = _phase_key(survivor["identity"]["key"], p["kind"], tuple(p["fact_keys"]))
                p["phase_id"] = "bp1_" + p["fingerprint"][:24]
            survivor["phases"] = list(merged_phases.values())
            g.old, key = survivor, survivor["identity"]["key"]
        old = g.old
        eid = old["brief_event_id"] if old else event_id(key)
        initial = min([c.effective for c in g.claims] + ([parse(old["initial_effective_at"])] if old else []))
        basis = old["initial_basis"] if old and parse(old["initial_effective_at"]) <= min(c.effective for c in g.claims) else min(g.claims, key=lambda c: c.effective).basis
        first = min([parse(c.row.get("first_seen_at")) or c.effective for c in g.claims]
                    + ([parse(old["first_observed_at"])] if old else []))
        phases = {(p["kind"], tuple(p["fact_keys"])): copy.deepcopy(p) for p in (old or {}).get("phases", [])}
        kinds = {c.phase for c in g.claims if not c.unknown_update}
        # Availability is a new phase only when the same root had a concrete
        # teaser/limited state; descriptions at launch don't invent updates.
        separate_available = "announced" in kinds or any(p["kind"] == "announced" for p in phases.values())
        announcement_times = [c.effective for c in g.claims if c.phase == "announced"]
        announcement_times.extend(parse(p["effective_at"]) for p in phases.values() if p["kind"] == "announced")
        assignment = {}
        for c in sorted(g.claims, key=lambda c: (c.effective, str(c.row["id"]))):
            kind = c.phase
            if kind == "patched" and "patch_status:unpatched" not in g.facts:
                kind = "baseline"
            if c.unknown_update:
                kind = "announced" if separate_available else "baseline"
            if kind == "available" and not separate_available:
                kind = "baseline"
            if (kind == "baseline" and not c.unknown_update and announcement_times
                    and c.action in {"model_release", "speed_tier_release"}
                    and c.strength == "strong" and corroboration.identity(c.row)[0]
                    and c.effective > min(announcement_times) + timedelta(hours=6)):
                kind = "available"
            elif kind == "baseline" and announcement_times and c.effective <= min(announcement_times) + timedelta(hours=6):
                kind = "announced"
            # Old-feature recaps explicitly dated before a rollout stay baseline.
            if c.action == "model_release" and re.search(r"(?:於|于)\s*\d+月\d+日.*(?:推出|發|发)", normalized(c.row.get("summary"))):
                kind = "announced" if separate_available else "baseline"
            fact_keys = c.phase_facts if kind == c.phase and c.phase_facts else (kind,)
            signature = (kind, tuple(fact_keys))
            fingerprint = _phase_key(key, kind, tuple(fact_keys))
            phase = phases.setdefault(signature, {"phase_id": "bp1_" + fingerprint[:24], "kind": kind,
                "fingerprint": fingerprint, "effective_at": stamp(c.effective), "time_basis": c.basis,
                "evidence_ids": [], "fact_keys": list(fact_keys)})
            # A recap of a known phase can only move its earliest evidence earlier.
            if c.effective < parse(phase["effective_at"]):
                phase["effective_at"], phase["time_basis"] = stamp(c.effective), c.basis
            if str(c.row["id"]) not in phase["evidence_ids"]:
                phase["evidence_ids"] = (phase["evidence_ids"] + [str(c.row["id"])])[:8]
            assignment[str(c.row["id"])] = signature
        phase_list = sorted(phases.values(), key=lambda p: (p["effective_at"], p["phase_id"]))
        # Baseline starts at the known initial report even when a later article
        # spells out an available-at-launch feature for the first time.
        for p in phase_list:
            if p["kind"] == "baseline":
                p["effective_at"] = stamp(initial)
                p["time_basis"] = basis
        phase_list.sort(key=lambda p: (parse(p["effective_at"]), p["phase_id"]))
        active = max(phase_list, key=lambda p: (parse(p["effective_at"]), p["kind"] != "baseline", p["phase_id"]))
        material = max((parse(p["effective_at"]) for p in phase_list if p["kind"] in {"available", "patched", "observed_exploitation", "value_changed", "expanded_availability"}
                        and parse(p["effective_at"]) > initial), default=None)
        effective = max(initial, material or initial)
        active_signature = (active["kind"], tuple(active["fact_keys"]))
        active_claims = [c for c in g.claims if assignment[str(c.row["id"])] == active_signature and not c.unknown_update and not c.row.get("duplicate_of")]
        primary_pool = [c for c in active_claims if str(c.row["id"]) in seed_stories] or active_claims or current
        primary = min(primary_pool, key=lambda c: rank({**c.row, **display.get(str(c.row["id"]), {})}))
        # The first bounded evidence ID is the same-phase primary. A new
        # same-priority publication never takes its place merely by being new.
        old_phase = next((p for p in (old or {}).get("phases", []) if p["phase_id"] == active["phase_id"]), None)
        if old_phase and old_phase["evidence_ids"]:
            prior = next((c for c in primary_pool if str(c.row["id"]) == old_phase["evidence_ids"][0]), None)
            if prior and rank({**prior.row, **display.get(str(prior.row["id"]), {})})[:-1] == rank({**primary.row, **display.get(str(primary.row["id"]), {})})[:-1]:
                primary = prior
        active["evidence_ids"] = ([str(primary.row["id"])] + [i for i in active["evidence_ids"] if i != str(primary.row["id"])])[:8]
        active_ids = {str(c.row["id"]) for c in active_claims}
        eligible_current_ids = {str(c.row["id"]) for c in current if str(c.row["id"]) in active_ids and not c.unknown_update}
        refs = []
        for c in sorted(g.claims, key=lambda c: str(c.row["id"])):
            rid = str(c.row["id"])
            r = {**c.row, **display.get(rid, {})}
            pub, status = corroboration.identity(c.row)
            refs.append({k: r.get(k) for k in ("id", "title", "title_zh", "title_en", "title_original", "url", "source", "site_id", "published_at")} | {
                "corroboration_key": pub, "corroboration_status": status,
                "role": "context_unknown" if c.unknown_update else "active_phase" if rid in eligible_current_ids else "past_phase",
                "phase_id": phases[assignment[rid]]["phase_id"]})
        count = len({r["corroboration_key"] for r in refs if r["role"] == "active_phase" and r["corroboration_key"]})
        primary_row = {**primary.row, **display.get(str(primary.row["id"]), {})}
        base = (record_builder(primary.row, effective, count) if record_builder else copy.deepcopy(fallback_bases[str(current[0].row["id"])]))
        previous_summary = fallback_bases.get(str(primary.row["id"])) or {}
        if (previous_summary.get("primary_item") or {}).get("id") == primary.row["id"]:
            for name in ("news_summary", "news_summary_provider", "news_summary_model", "news_summary_generated_at"):
                if name in previous_summary:
                    base[name] = previous_summary[name]
        primary_item = {**primary_row, "corroboration_key": corroboration.identity(primary.row)[0]}
        # v1 is a 24-hour brief even when a maintainer builds a wider ordinary
        # archive/story comparison with the generator's --window-hours option.
        expire = effective + timedelta(hours=24)
        effective_basis = active["time_basis"] if material else basis
        identity = {"key": key, "subject": g.subject, "version": primary.version, "action": g.action,
                    "scope": list(primary.scope), "batch_key": ",".join(sorted(g.cves)) or None, "facts": sorted(g.facts)}
        mentioned = max([min(parse(c.row.get("last_seen_at")) or c.effective, now) for c in g.claims]
                        + ([parse(old["last_mentioned_at"])] if old else []))
        reported = max([parse(c.row.get("published_at")) or c.effective for c in g.claims]
                       + ([parse(old["last_reported_at"])] if old and old["last_reported_at"] else []))
        keys = sorted(set((old or {}).get("match_keys", [])) | {hashlib.sha256(c.key.encode()).hexdigest() for c in g.claims if c.strength == "strong"})
        entry = {"brief_event_id": eid, "identity": identity, "initial_effective_at": stamp(initial),
                 "initial_basis": basis, "first_observed_at": stamp(first), "last_material_at": stamp(material) if material else None,
                 "last_reported_at": stamp(reported), "last_mentioned_at": stamp(mentioned),
                 "alias_event_ids": (old or {}).get("alias_event_ids", []), "match_keys": keys, "phases": phase_list}
        if len(canonical(identity)) > 1024 or len(keys) > 16 or len(phase_list) > MAX_PHASES or len(entry["alias_event_ids"]) > 16:
            errors.append("history_overflow:" + eid)
            continue
        for loser in merged_losers:
            persisted.pop(loser, None)
        persisted[eid] = entry
        base.update({"brief_event_id": eid, "story_id": eid, "identity": identity,
            "member_story_ids": sorted({sid for c in current for sid in seed_stories[str(c.row["id"])]}),
            "member_article_ids": sorted(str(c.row["id"]) for c in g.claims), "sources": refs, "items": refs,
            "primary_item": primary_item, "title": primary_row.get("title_bilingual") or primary_row.get("title") or "",
            "url": primary_row.get("url") or "", "primary_url": primary_row.get("url") or "",
            "source": primary_row.get("source") or "", "source_name": primary_row.get("site_name") or primary_row.get("source_name") or "",
            "source_names": sorted({str(c.row.get("source") or "") for c in g.claims}),
            "source_count": len(refs), "item_count": len(refs), "corroboration_count": count, "duplicate_count": max(1, count),
            "business_events": sorted({str(tag) for c in current for sid in seed_stories[str(c.row["id"])]
                                       for tag in next(s for s in stories if str(s["story_id"]) == sid).get("business_events", [])}),
            "initial_effective_at": stamp(initial), "initial_basis": basis, "first_observed_at": stamp(first),
            "last_material_at": stamp(material) if material else None, "last_reported_at": stamp(reported),
            "effective_basis": effective_basis,
            "effective_reported_day": (effective - timedelta(days=1, hours=12)).date().isoformat() if effective_basis == "reported_day_upper_bound" else None,
            "effective_at": stamp(effective), "expires_at": stamp(expire), "earliest_at": stamp(initial), "latest_at": stamp(effective),
            "active_phase_id": active["phase_id"], "eligible": effective <= now <= expire,
            "eligibility_reason": "in_window" if effective <= now <= expire else "expired",
            "match_evidence": [{"rule_id": c.rule, "strength": c.strength, "article_id": str(c.row["id"]),
                                "basis": (sorted(c.facts) if c.facts else [c.key]) + c.spans, "conflicts": []} for c in sorted(g.claims, key=lambda c: str(c.row["id"]))],
            "unknown_update_article_ids": sorted(str(c.row["id"]) for c in g.claims if c.unknown_update)})
        events.append(base)
    state = {"record_type": "brief_event_state", "schema_version": 1, "matcher_version": VERSION,
             "generated_at": stamp(now), "archive_generated_at": stamp(now),
             "history_complete": False, "events": sorted(persisted.values(), key=lambda e: e["brief_event_id"])}
    state["revision"] = digest(state)
    if len(state["events"]) > MAX_EVENTS or len(canonical(state)) > MAX_BYTES:
        return _empty(now, "state_capacity")
    if not validate_state(state):
        return _empty(now, "constructed_state_invalid")
    # Keep the original per-publisher decay, without a second title-only merger.
    available = [e for e in events if e["eligible"] and (e["corroboration_count"] >= 2 or float(e.get("score") or 0) >= .72)]
    selected, per_source = [], defaultdict(int)
    while available and len(selected) < 20:
        available.sort(key=lambda e: (-float(e.get("score") or 0) + .03 * per_source[e["source"]], e["brief_event_id"]))
        chosen = available.pop(0)
        selected.append(chosen)
        per_source[chosen["source"]] += 1
    diag = {"recovery_mode": recovery, "errors": errors, "candidate_article_count": len(seed_stories),
            "root_count": len(events), "expired_count": sum(not e["eligible"] for e in events),
            "context_attachment_count": sum(c.strength == "context_attachment" for c in claims),
            "unresolved_count": sum(c.strength == "unresolved" for c in claims),
            "state_bytes": len(canonical(state)), "capacity_warning": len(canonical(state)) >= .8 * MAX_BYTES}
    p = {"record_type": "brief_event_projection", "schema_version": 1, "matcher_version": VERSION,
         "generated_at": stamp(now), "status": "recovered" if recovery != "none" else "ready", "history_complete": False,
         "state_revision": state["revision"], "events": sorted(events, key=lambda e: e["brief_event_id"]),
         "selected_event_ids": [e["brief_event_id"] for e in selected], "diagnostics": diag}
    p["generation_id"] = "bg1_" + digest(p)[:24]
    if len(canonical(p)) > MAX_BYTES:
        return _empty(now, "projection_capacity")
    return BriefEventResult(p, state, selected, diag)


def selection_meta(projection: dict[str, Any]) -> dict[str, Any]:
    return {k: projection[k] for k in ("schema_version", "matcher_version", "generation_id", "generated_at", "status", "selected_event_ids")} | {"record_type": "brief_event_selection"}
