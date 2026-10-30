"""D+ impact-v2: one bounded impact-ranked pool for every featured event.

The v1 event engine and general article classifier remain authoritative for
identity/history and the ordinary reader. v2 is deliberately rejected by the
old browser guard until the matching I02 frontend is installed.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import copy
import math
import re

try:
    from scripts import publisher_governance as legacy, signal_material as material, supplement_impact
except ModuleNotFoundError:
    import publisher_governance as legacy
    import signal_material as material
    import supplement_impact

b, policy, corroboration = legacy.b, legacy.policy, legacy.corroboration
SCHEMA_VERSION, SELECTION_POLICY, DEFAULT_VISIBLE_LIMIT = 2, "impact-v2", 5
MAX_BYTES, MAX_EVENTS, MAX_ARTICLES = legacy.MAX_BYTES, legacy.MAX_EVENTS, legacy.MAX_ARTICLES
BASES = {"supported_core", "industry_news", "capability_disclosure"}
REASONS = legacy.REASONS | BASES


def qualified_kinds(event, annotation, row, now):
    if any(e["status"] == "conflict" for e in annotation["qualification"]["core_evidence"]):
        return []
    return legacy.qualified_kinds(event, annotation, row, now)


def decide(event, annotations, rows, now, scorer):
    result = {"brief_event_id": event["brief_event_id"], "active_phase_id": event["active_phase_id"],
        "featured_eligible": False, "selection_class": None, "reason_codes": [],
        "qualified_source_count": 0, "qualified_corroboration_keys": [], "support_article_ids": [],
        "support_scores": [], "eligibility_basis": None, "featured_primary_article_id": None,
        "featured_primary_item": None, "featured_score": None, "featured_business_events": [],
        "featured_news_summary": None, "summary_article_id": None, "disclosure_flags": [],
        "supplement_impact": None}
    if not event["eligible"] or not b.parse(event["effective_at"]) <= now < b.parse(event["expires_at"]):
        result["reason_codes"] = ["outside_reader_window"]
        return result
    core, supplement = [], []
    for ref in event["sources"]:
        rid = ref["id"]
        if ref["role"] != "active_phase" or ref["phase_id"] != event["active_phase_id"]:
            continue
        # Absence/withdrawal of an engine key can never be repaired by a new
        # headline, a newly recognized model name, or a supplement label.
        if not ref.get("corroboration_key") or ref["corroboration_key"] != corroboration.identity(rows[rid])[0]:
            continue
        annotation = annotations[rid]
        kinds = qualified_kinds(event, annotation, rows[rid], now)
        if kinds:
            core.append((ref, kinds))
        elif (event["identity"].get("action") == "article"
                and legacy.admitted(annotation, "featured")
                and annotation["supplement_evidence"]["kind"]):
            supplement.append((ref, []))
    candidates = core or supplement
    if not candidates:
        result["reason_codes"] = ["no_current_qualified_article"]
        return result
    keys = sorted({ref["corroboration_key"] for ref, _ in candidates})
    selection_class = "core" if core else "supplement"
    def impact_for(ref):
        basis = "supported_core" if core else annotations[ref["id"]]["supplement_evidence"]["kind"]
        return supplement_impact.score(ref["source_material"], basis)
    scored = [(supplement_impact.rank(impact_for(ref), selection_class, b.parse(event["effective_at"]), now), ref, kinds)
              for ref, kinds in candidates]
    if any(type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 1
           for score, _, _ in scored):
        raise ValueError("invalid_importance")
    score, primary, kinds = min(scored, key=lambda x:
        (-x[0], annotations[x[1]["id"]]["source_policy"]["source_tier_rank"], x[1]["id"]))
    supplement_evidence = annotations[primary["id"]]["supplement_evidence"]
    basis = "supported_core" if core else supplement_evidence["kind"]
    result.update(featured_eligible=True, selection_class="core" if core else "supplement",
        reason_codes=[basis], qualified_source_count=len(keys), qualified_corroboration_keys=keys,
        support_article_ids=sorted(ref["id"] for ref, _ in candidates),
        support_scores=sorted([{"article_id": ref["id"], "score": value} for value, ref, _ in scored],
                              key=lambda x: x["article_id"]),
        eligibility_basis=basis, featured_primary_article_id=primary["id"],
        featured_primary_item=copy.deepcopy(primary), featured_score=score,
        featured_business_events=kinds, disclosure_flags=[] if core else supplement_evidence["qualifiers"])
    result["featured_primary_item"]["business_events"] = kinds
    result["supplement_impact"] = impact_for(primary)
    summary = event.get("news_summary")
    if isinstance(summary, str) and summary:
        if primary["id"] == event["primary_item"]["id"] and len(summary) <= 2000:
            result.update(featured_news_summary=summary, summary_article_id=primary["id"])
        else:
            result["reason_codes"].append("summary_primary_mismatch")
    return result


def select(decisions, *, limit=20, target=DEFAULT_VISIBLE_LIMIT):
    """Select after caller filtering using one impact gate and five shared slots."""
    if not 0 <= target <= limit <= 20:
        raise ValueError("invalid_selection_bounds")
    eligible = [d for d in decisions if d["featured_eligible"]]
    if len({d["brief_event_id"] for d in eligible}) != len(eligible):
        raise ValueError("duplicate_event")
    selected, counts = [], defaultdict(int)
    remaining = [d for d in eligible if d["supplement_impact"]["passes"]]
    while remaining and len(selected) < min(limit, target):
        def key(d):
            primary = d["featured_primary_item"]
            return primary.get("corroboration_key") or "publisher:" + primary["publisher"]["publisher_id"]
        remaining.sort(key=lambda d: (-d["featured_score"] + .03 * counts[key(d)], d["brief_event_id"]))
        chosen = remaining.pop(0)
        selected.append(chosen["brief_event_id"])
        counts[key(chosen)] += 1
    return selected


def featured_view(event, decision):
    out = legacy.featured_view(event, decision)
    out.update(selection_class=decision["selection_class"],
        signal_label="核心事件" if decision["selection_class"] == "core" else "產業動態",
        disclosure_flags=copy.deepcopy(decision["disclosure_flags"]),
        supplement_impact=copy.deepcopy(decision["supplement_impact"]))
    impact = decision["supplement_impact"]
    bonus = 3 if decision["selection_class"] == "core" else 0
    out["importance_breakdown"] = {"impact": impact["total"], "core_bonus": bonus,
        "freshness": round(decision["featured_score"] * 103 / (impact["total"] + bonus), 4) if impact["total"] + bonus else 0}
    return out


def _hashes(projection, overlay):
    projection["generation_id"] = "bg1_" + b.digest({k: v for k, v in projection.items() if k != "generation_id"})[:24]
    overlay["brief_generation_id"] = projection["generation_id"]
    overlay["generation_id"] = "pg2_" + b.digest({k: v for k, v in overlay.items() if k != "generation_id"})[:24]


def unavailable(projection, revision, error):
    projection["selected_event_ids"] = []
    overlay = {"record_type": "publisher_governance_projection", "schema_version": SCHEMA_VERSION,
        "policy_id": policy.POLICY_ID, "selection_policy": SELECTION_POLICY,
        "default_visible_limit": DEFAULT_VISIBLE_LIMIT, "registry_revision": revision,
        "generated_at": projection["generated_at"], "brief_generation_id": None,
        "brief_state_revision": projection.get("state_revision"), "status": "unavailable",
        "articles": [], "events": [], "featured_event_ids": [], "daily_selected_event_ids": [],
        "diagnostics": {"errors": [error], "reason_counts": {}}, "generation_id": ""}
    _hashes(projection, overlay)
    return overlay


def build(projection, records, *, now, annotate, scorer, sanitize):
    revision = policy.current_registry().revision
    if projection.get("status") not in {"ready", "recovered"}:
        return unavailable(projection, revision, "invalid_projection")
    if len(projection["events"]) > MAX_EVENTS:
        return unavailable(projection, revision, "projection_capacity")
    raw_rows = {row["id"]: row for row in records}
    if len(raw_rows) != len(records):
        return unavailable(projection, revision, "invalid_projection")
    annotations, rows = {}, {}
    try:
        for event in projection["events"]:
            if len({r["id"] for r in event["sources"]}) != len(event["sources"]):
                raise ValueError("duplicate_reference")
            for ref in [*event["sources"], *event["items"], event["primary_item"]]:
                rid = ref["id"]
                if rid not in annotations:
                    raw = raw_rows.get(rid)
                    row = annotate(sanitize(raw or ref))
                    row["site_name"] = str(row.get("site_name") or "")
                    native = sanitize(legacy.source_material(raw)) if raw else {"title_original": "", "title": "", "summary": ""}
                    qualification = material.qualify_core(row, native)
                    rows[rid] = row
                    annotations[rid] = {"id": rid, **{k: row[k] for k in ("ingress", "publisher", "source_policy")},
                        "qualification": qualification,
                        "supplement_evidence": material.supplement(row, native, qualification)}
                    if len(annotations) > MAX_ARTICLES:
                        return unavailable(projection, revision, "projection_capacity")
                raw = raw_rows.get(rid)
                native = sanitize(legacy.source_material(raw)) if raw else {"title_original": "", "title": "", "summary": ""}
                # Retain public links so the runtime guard can recompute exact
                # native evidence without fetching, guessing, or borrowing URLs.
                links = [url for value in rows[rid].get("publisher_links") or []
                         if (url := legacy.identity.public_url(value)[0])][:24]
                ref.update({k: annotations[rid][k] for k in ("ingress", "publisher", "source_policy")},
                    source_material=native, source_links=links, source_site_name=rows[rid]["site_name"])
        decisions = [decide(e, annotations, rows, now, scorer) for e in projection["events"]]
        selected = select(decisions)
        projection["selected_event_ids"] = selected
        overlay = {"record_type": "publisher_governance_projection", "schema_version": SCHEMA_VERSION,
            "policy_id": policy.POLICY_ID, "selection_policy": SELECTION_POLICY,
            "default_visible_limit": DEFAULT_VISIBLE_LIMIT, "registry_revision": revision,
            "generated_at": projection["generated_at"], "brief_generation_id": "",
            "brief_state_revision": projection["state_revision"], "status": "ready",
            "articles": [annotations[k] for k in sorted(annotations)], "events": decisions,
            "featured_event_ids": sorted(d["brief_event_id"] for d in decisions if d["featured_eligible"]),
            "daily_selected_event_ids": selected,
            "diagnostics": {"errors": [], "reason_counts": dict(Counter(c for d in decisions for c in d["reason_codes"]))},
            "generation_id": ""}
        _hashes(projection, overlay)
        if len(b.canonical(overlay)) > MAX_BYTES or len(b.canonical(projection)) > MAX_BYTES:
            return unavailable(projection, revision, "projection_capacity")
        if not validate(overlay, projection):
            return unavailable(projection, revision, "invalid_projection")
        return overlay
    except (KeyError, TypeError, ValueError, OverflowError, AttributeError):
        return unavailable(projection, revision, "invalid_projection")


def metadata(overlay):
    return {**legacy.metadata(overlay), "selection_policy": overlay["selection_policy"],
            "default_visible_limit": overlay["default_visible_limit"]}


def _native_row(ref):
    return {**ref, **ref["source_material"], "publisher_links": ref["source_links"],
            "site_name": ref["source_site_name"]}


def validate(g, projection):
    """Recompute native qualifications and relationship guards, without I/O."""
    try:
        if (g["record_type"] != "publisher_governance_projection" or type(g["schema_version"]) is not int
                or g["schema_version"] != SCHEMA_VERSION or g["policy_id"] != policy.POLICY_ID
                or g["selection_policy"] != SELECTION_POLICY or type(g["default_visible_limit"]) is not int
                or g["default_visible_limit"] != DEFAULT_VISIBLE_LIMIT
                or not re.fullmatch(r"[0-9a-f]{64}", g["registry_revision"])):
            return False
        if (len(b.canonical(g)) > MAX_BYTES or len(b.canonical(projection)) > MAX_BYTES
                or len(g["events"]) > MAX_EVENTS or len(g["articles"]) > MAX_ARTICLES):
            return False
        if g["generation_id"] != "pg2_" + b.digest({k: v for k, v in g.items() if k != "generation_id"})[:24]:
            return False
        if projection["generation_id"] != "bg1_" + b.digest({k: v for k, v in projection.items() if k != "generation_id"})[:24]:
            return False
        if (g["generated_at"] != projection["generated_at"] or g["brief_generation_id"] != projection["generation_id"]
                or g["brief_state_revision"] != projection["state_revision"]):
            return False
        if g["status"] == "unavailable":
            return (not any(g[k] for k in ("events", "articles", "featured_event_ids", "daily_selected_event_ids"))
                    and not projection["selected_event_ids"] and bool(g["diagnostics"]["errors"]))
        if g["status"] != "ready" or projection["status"] not in {"ready", "recovered"} or g["diagnostics"]["errors"]:
            return False
        articles = {a["id"]: a for a in g["articles"]}
        events = {e["brief_event_id"]: e for e in projection["events"]}
        decisions = {d["brief_event_id"]: d for d in g["events"]}
        if (len(articles) != len(g["articles"]) or len(events) != len(projection["events"])
                or len(decisions) != len(g["events"]) or set(events) != set(decisions)):
            return False
        asof, ref_ids = b.parse(g["generated_at"]), set()
        for eid, event in events.items():
            refs = {r["id"]: r for r in event["sources"]}
            if (len(refs) != len(event["sources"]) or len(event["member_article_ids"]) != len(refs)
                    or set(refs) != set(event["member_article_ids"]) or event["primary_item"]["id"] not in refs):
                return False
            rows = {}
            for rid, ref in refs.items():
                a = articles[rid]
                ref_ids.add(rid)
                sp = a["source_policy"]
                if (sp["schema_version"] != 1 or sp["policy_id"] != policy.POLICY_ID
                        or type(sp["schema_version"]) is not int
                        or sp["registry_revision"] != g["registry_revision"]
                        or sp["admission_status"] not in {"approved", "limited", "unreviewed", "excluded"}
                        or sp["source_tier"] not in policy.TIERS or sp["publisher_kind"] not in policy.KINDS
                        or type(sp["source_tier_rank"]) is not int or not 0 <= sp["source_tier_rank"] <= 9
                        or any(type(sp[k]) is not bool for k in policy.PERMISSIONS)
                        or type(a["publisher"]["schema_version"]) is not int or a["publisher"]["schema_version"] != 1
                        or a["publisher"]["status"] not in {"identified", "reported", "unknown", "conflict"}
                        or any(ref[k] != a[k] for k in ("ingress", "publisher", "source_policy"))):
                    return False
                if sp["admission_status"] == "unreviewed" and (sp["source_tier"] != "watchlist"
                        or sp["source_tier_rank"] != 6 or sp["allow_featured"] or sp["allow_radar"]):
                    return False
                if (not isinstance(ref["source_links"], list) or len(ref["source_links"]) > 24
                        or not isinstance(ref["source_site_name"], str)
                        or any(legacy.identity.public_url(url)[0] != url for url in ref["source_links"])):
                    return False
                row = _native_row(ref)
                rows[rid] = row
                expected = material.qualify_core(row, ref["source_material"])
                if a["qualification"] != expected or a["supplement_evidence"] != material.supplement(row, ref["source_material"], expected):
                    return False
                for evidence in [*a["qualification"]["core_evidence"], a["supplement_evidence"]]:
                    for span in evidence["spans"]:
                        if type(span["start"]) is not int or type(span["end"]) is not int:
                            return False
            decision = decisions[eid]
            if (type(decision["featured_eligible"]) is not bool
                    or type(decision["qualified_source_count"]) is not int):
                return False
            scores = decision["support_scores"]
            score_map = {s["article_id"]: s["score"] for s in scores}
            if (len(score_map) != len(scores) or any(type(v) not in (int, float)
                    or not math.isfinite(v) or not 0 <= v <= 1 for v in score_map.values())):
                return False
            expected = decide(event, articles, rows, asof, lambda row, *_: score_map[row["id"]])
            if decision != expected or set(score_map) != set(decision["support_article_ids"]):
                return False
        if ref_ids != set(articles):
            return False
        featured = sorted(eid for eid, d in decisions.items() if d["featured_eligible"])
        selected = select(g["events"])
        return (g["featured_event_ids"] == featured and g["daily_selected_event_ids"] == selected
                and projection["selected_event_ids"] == selected
                and g["diagnostics"]["reason_counts"] == dict(Counter(c for d in g["events"] for c in d["reason_codes"])))
    except (KeyError, TypeError, ValueError, OverflowError, AttributeError):
        return False
