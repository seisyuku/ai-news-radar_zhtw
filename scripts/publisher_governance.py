"""Evidence and use qualifications layered over the unchanged event engine.

No network, LLM, source promotion or event matching rules live here. Supported
means the retained source material supports the stated event, not verified fact.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import copy
from datetime import datetime, timedelta
import math
import re
from typing import Any

try:
    from scripts import brief_events as b, publisher_policy as policy, publisher_identity as identity, publisher_material as material_cues, corroboration, evidence_policy, security_topics
except ModuleNotFoundError:
    import brief_events as b
    import publisher_policy as policy
    import publisher_identity as identity
    import publisher_material as material_cues
    import corroboration
    import evidence_policy
    import security_topics


KINDS = ("earnings", "market", "security", "pricing", "benchmark", "model_release")
MAX_BYTES, MAX_EVENTS, MAX_ARTICLES = 8 * 1024 * 1024, 10_000, 100_000
REASONS = {"identified_host", "identified_bridge", "reported_rss_source", "legacy_identity", "missing_identity", "identity_conflict", "unreviewed_publisher", "excluded_scope", "scope_mismatch", "limited_scope", "approved_scope", "legacy_metadata_missing", "outside_reader_window", "out_of_scope", "scope_unknown", "no_core_event", "insufficient_evidence", "evidence_conflict", "no_current_qualified_article", "no_counting_key", "below_qualified_gate", "official_primary", "multiple_qualified_publishers", "qualified_score", "unsupported_policy", "generation_mismatch", "invalid_projection", "projection_capacity", "summary_primary_mismatch", "not_permitted_for_radar", "not_permitted_for_featured", "control_only"}


def rx(text):
    return re.compile(text, re.I)


COMPANY = rx(r"(?<![a-z0-9])(?:OpenAI|Anthropic|Google|Alphabet|Microsoft|NVIDIA|AMD|Amazon|AWS|Meta|DeepSeek|Mistral|Tencent|Alibaba|Apple|Intel|TSMC|xAI|ByteDance|Hugging Face)(?![a-z0-9])|台積電|台积电|輝達|英偉達|英伟达|微軟|微软|騰訊|腾讯|阿里巴巴|字節跳動|字节跳动")
PRODUCT = rx(r"(?<![a-z0-9])(?:ChatGPT|Codex|Copilot|Claude|Gemini|Bedrock|Azure|OpenAI API|PHP|OpenSSL|OpenSSH|WordPress|Linux|Chrome|Firefox|Python|Redis|Apache|Nginx)(?![a-z0-9])|監控系統|监控系统|monitoring system")
PROMO = rx(r"^(?:how to\b|如何|怎麼|怎么)|教學|教程|攻略|使用技巧|入門指南|入门指南|操作心得|prompt tips|報名|报名|線上講座|线上讲座|限時優惠|限时优惠|sponsored|advertorial")
ADVICE = rx(r"(?:企業|企业|團隊|团队|你|您).{0,12}(?:如何|怎樣|怎样).{0,20}(?:成長|成长|提升|提高|效率|獲利|获利)|(?:提升|提高).{0,10}效率.{0,10}(?:建議|建议|秘訣|秘诀|技巧)|\b(?:tips for|ways to (?:use|boost|improve))\b")
RELATED = rx(r"延伸閱讀|延伸阅读|相關文章|相关文章|read more|related articles")
RELEASE = rx(r"\b(?:releases?|released|launch(?:es|ed)?|introduces?|introduced|announces?|announced)\b|now available|available (?:for|to)|發[布佈表]|发布|推出|正式(?:開放|开放|上線|上线)")
RUMOR = rx(r"rumou?r|reportedly|could launch|may launch|expected to|predicted|prediction|傳聞|传闻|據傳|据传|預測|预测|可能.{0,12}(?:發布|发布|推出)")
DENIAL = rx(r"(?:not|never|hasn't|has not|did not)\s+(?:been\s+)?(?:released|launched|changed|increased|acquired)|尚未(?:發布|发布|推出)|並未(?:發布|收購|漲價)|并未(?:发布|收购|涨价)|否認.{0,12}(?:收購|併購|漏洞|外洩)|den(?:ies|ied).{0,60}(?:breach|acquisition|acquir|merger)|no (?:confirmed )?(?:breach|vulnerability|acquisition|merger)")
MONEY = rx(r"(?:\$|US\$|USD|NT\$|美元|新臺幣|新台幣|人民币|人民幣)\s*\d|\d[\d.,]*\s*(?:%|percent|(?:萬|万|億|亿|兆)?\s*(?:美元|元|新臺幣|新台幣|人民币|人民幣)|million|billion)")
PERIOD = rx(r"(?<![a-z0-9])(?:Q[1-4](?:\s*\d{2,4})?|FY\s*\d{2,4}|20\d{2}|YoY|QoQ|MoM)(?![a-z0-9])|季度|財年|财年|第[一二三四1234]季|年度|本季|上半年|下半年|年化|季增|年增|月增|同比|環比|环比|quarter|fiscal|annualized|annualised|run.rate")
FINANCE = rx(r"revenue|earnings|net (?:income|profit)|(?:free |operating )?cash flow|capex|capital expenditures?|\bIPO\b|營收|营收|財報|财报|淨利|净利|現金流|现金流|資本支出|资本支出|首次公開募股|上市募資")
MARKET_ACTION = rx(r"\bacquir(?:e|es|ed|ing)\b|\bacquisition\b|\bmerg(?:es|ed|er)\b|antitrust (?:probe|investigation|fine)|(?:regulator|FTC|commission).{0,40}(?:orders?|fines?|investigat)|shuts? down|permanent shutdown|ceases? (?:permanently )?operations|permanently cease operations|收購|收购|併購|并购|合併|合并|反壟斷調查|反垄断调查|勒令|宣布.{0,12}(?:停運|停止營運|終止服務)")
SHARE = rx(r"market share|市場份額|市场份额|市佔|市占|流量占比|traffic share")
POPULATION = rx(r"global|worldwide|API|traffic|shipments|users|全球|流量|出貨|出货|用戶|用户|企業市場|企业市场")
PRICE_CHANGE = rx(r"(?:price|pricing|subscription|fee).{0,30}(?:cut|reduc|increas|chang|adjust)|(?:cuts?|reduces?|increases?).{0,30}(?:price|pricing|fee)|漲價|涨价|降價|降价|調整.{0,12}(?:價格|價格|收費|費率)|调整.{0,12}(?:价格|收费|费率)")
CREDIT_BENEFIT = rx(r"(?:API credits?.{0,45}(?:subscribers|subscription)|(?:subscribers|subscriptions?).{0,55}(?:can claim|receive).{0,30}(?:API )?credits?)|(?:訂閱|订阅).{0,30}(?:發放|发放|領取|领取).{0,15}(?:API|額度|额度)")
APPLICABILITY = rx(r"per .{0,30}(?:token|month|user)|million tokens|\b(?:API|plan|subscription|input|output)\b|每.{0,15}(?:token|月|用戶|用户)|方案|訂閱|订阅|輸入|输入|輸出|输出")
BENCH = rx(r"SWE[- ]bench|MMLU|GPQA|AIME|MMMU|Humanity.s Last Exam|\bHLE\b|HumanEval|LiveCodeBench|ARC[- ]AGI|Terminal[- ]Bench")
MEASURE = rx(r"scores?|scored|achieves?|achieved|evaluat|tested|benchmark result|得分|成績|成绩|達到|达到|測得|测得|評測|评测")
HISTORICAL = rx(r"last year|previously scored|historical ranking|去年|回顧.{0,15}(?:榜|評測)|回顾.{0,15}(?:榜|评测)|過去的排行|过去的排行")
RELEASE_HISTORY = rx(r"last year|previously (?:released|launched)|originally (?:released|launched)|去年|此前已(?:發布|发布|推出)|先前已(?:發布|发布|推出)")
SPECULATIVE_ACTION = rx(r"\b(?:may|might|could|would|will|plans? to|expected to)\b.{0,40}(?:launch|release|introduce|be available|acquir|merge|cut|increas)|(?:可能|預計|预计|計劃|计划).{0,20}(?:發布|发布|推出|收購|收购|降價|降价|漲價|涨价)")
ISSUE = rx(r"vulnerabilit|\bflaw|\bCVE-\d{4}-\d+|漏洞|資安事件|安全漏洞|資料外洩|数据泄露")
IMPACT = rx(r"remote.code.execution|\bRCE\b|arbitrary code|unauthorized (?:access|execution)|privilege escalation|data (?:exfiltration|leak)|bypass.{0,15}(?:auth|permission)|遠端.{0,8}執行|远程.{0,8}执行|任意.{0,8}執行|任意.{0,8}执行|未經授權|未经授权|權限提升|权限提升|資料外洩|数据泄露|繞過.{0,8}(?:認證|權限)|绕过.{0,8}(?:认证|权限)")
METHOD = rx(r"reproduc|proof.of.concept|technical (?:analysis|details)|tested|test methodology|attack chain|重現|复现|重现|攻擊鏈|攻击链|技術分析|技术分析|驗證方法|验证方法")
MECHANISM = rx(r"\bCVE-\d{4}-\d+|use.after.free|out.of.bounds|buffer overflow|heap|SQL injection|authorization bypass|unauthenticated|未經身分驗證|未经身份验证|緩衝區|缓冲区|記憶體|内存|驗證繞過|认证绕过")
SECONDHAND = rx(r"according to (?:a )?(?:Reddit|social).{0,12}post|unconfirmed demo|unverified social|社群貼文|社群帖文|網友.{0,12}示範|网友.{0,12}演示|二手轉述|二手转述")


def source_material(row):
    """Native retained fields only; never translated or generated summaries."""
    return {key: str(row.get(key) or "")[:20000] for key in ("title_original", "title", "summary")}


def evidence_text(title, summary):
    """Do not borrow another model/product/company's details from the lead."""
    return material_cues.focused_text(title, summary, b.MODEL_RE, PRODUCT, COMPANY)


def has_model_release(text):
    """Require the release verb to apply to the named model, not a nearby noun."""
    if RUMOR.search(text) or SPECULATIVE_ACTION.search(text) or RELEASE_HISTORY.search(text):
        return False
    bridge = rx(r"(?:\s|[:：\"'「」()—-]|\b(?:its|the|a|new|latest|flagship|AI|language|speech|video|frontier|multimodal|model|models)\b|了|全新|最新|新版|旗艦|旗舰|模型|語音|语音|視頻生成|视频生成|開源|开源)*")
    after = rx(r"^\s*(?:(?:AI |language |speech |video )?model\s+)?(?:(?:is|are|was|were|has been|have been)\s+)?(?:(?:now|generally|officially)\s+)?(?:available\b|released\b|launched\b)|^\s*(?:模型\s*)?(?:現已|现已|已|正式)?(?:發布|发布|推出|開放|开放|上線|上线)")
    boundaries = list(material_cues.CLAUSES.finditer(text))
    # Model identity may be established in the lead; assertion state belongs
    # only to the clause containing this particular mention and release verb.
    for mention in material_cues.models(text, b.MODEL_RE):
        start = max((m.end() for m in boundaries if m.end() <= mention.start()), default=0)
        end = min((m.start() for m in boundaries if m.start() >= mention.end()), default=len(text))
        clause = text[start:end]
        model = material_cues.Mention(mention.group(), mention.start() - start)
        if not material_cues.model_is_release_object(clause, model):
            continue
        following = after.search(clause[model.end():])
        if following:
            action = material_cues.Mention(following.group(), model.end() + following.start())
            if not material_cues.predicate_unasserted(clause, action):
                return True
        for verb in RELEASE.finditer(clause[:model.start()]):
            if (bridge.fullmatch(clause[verb.end():model.start()])
                    and not material_cues.predicate_unasserted(clause, verb)):
                return True
    return False


def qualify(row, material):
    if reason := evidence_policy.exclusion_reason(row):
        return {"scope": "out_of_scope", "core_evidence": [], "reason_codes": [reason, "out_of_scope"]}
    title_field = "title_original" if material.get("title_original") else "title"
    title = RELATED.split(material.get(title_field, ""), maxsplit=1)[0][:1600]
    summary = RELATED.split(material.get("summary", ""), maxsplit=1)[0][:1600]
    if not title:
        return {"scope": "unknown", "core_evidence": [], "reason_codes": ["legacy_metadata_missing", "scope_unknown"]}
    if material_cues.out_of_scope(title, summary, bool(PROMO.search(title) or ADVICE.search(title))):
        return {"scope": "out_of_scope", "core_evidence": [], "reason_codes": ["out_of_scope"]}
    text = evidence_text(title, summary)
    model = material_cues.models(text, b.MODEL_RE)
    # Proper-name candidates extend known vocabulary without conferring source
    # permission. Concrete action/data/method requirements below still apply.
    named = material_cues.names(title)
    product = model or PRODUCT.search(text) or named
    company = COMPANY.search(text) or named
    benchmark = material_cues.benchmark_named(text, BENCH)
    official = row["source_policy"]["publisher_kind"] == "official"
    spans = [{"field": key, "start": 0, "end": len(value), "text": value}
             for key, value in ((title_field, title), ("summary", summary)) if value]
    urls = list(dict.fromkeys(url for value in [row.get("url"), *(row.get("publisher_links") or [])]
                             if (url := identity.public_url(value)[0]) and not evidence_policy.attachment_url(url)))[:24]
    hints = {"earnings": FINANCE.search(text) or material_cues.ipo_filing_entity(title, summary), "market": MARKET_ACTION.search(text) or SHARE.search(text),
             "security": ISSUE.search(text) and security_topics.classify({"title": title, "summary": summary}).event, "pricing": PRICE_CHANGE.search(text) or CREDIT_BENEFIT.search(text),
             "benchmark": benchmark, "model_release": RELEASE.search(text) and model}
    supported = {
        "earnings": bool(company and material_cues.financial_support(title, summary, COMPANY, FINANCE, PERIOD)),
        "market": bool(company and (material_cues.market_action_supported(title, summary) or (not material_cues.uncertain_market(text) and SHARE.search(text) and PERIOD.search(text) and POPULATION.search(text) and MONEY.search(text)))),
        "security": bool(security_topics.classify({"title": title, "summary": summary}).event and product and ISSUE.search(text) and IMPACT.search(text) and MECHANISM.search(text)
                         and (official or METHOD.search(text)) and (not SECONDHAND.search(text) or METHOD.search(text))),
        "pricing": bool(product and (PRICE_CHANGE.search(text) or CREDIT_BENEFIT.search(text)) and MONEY.search(text) and APPLICABILITY.search(text)
                        and not SPECULATIVE_ACTION.search(text)),
        "benchmark": bool(model and benchmark and MEASURE.search(text) and re.search(r"\d+(?:\.\d+)?\s*(?:%|分|points?)", text, re.I) and not HISTORICAL.search(text)),
        "model_release": bool(model and has_model_release(text)),
    }
    evidence = []
    for kind in KINDS:
        if not hints[kind]:
            continue
        conflict = bool(DENIAL.search(text))
        if kind == "market" and material_cues.transaction_denied(text):
            conflict = True
        if kind == "pricing" and rx(r"no (?:price |pricing )?change|價格未變|价格未变|並未漲價|并未涨价").search(text):
            conflict = True
        if kind == "market" and rx(r"global market share|全球市[佔占]").search(title) and rx(r"OpenRouter|single platform|單一平台|单一平台").search(summary) and not rx(r"global|全球").search(summary):
            conflict = True
        status = "conflict" if conflict else "supported" if supported[kind] else "insufficient"
        evidence.append({"kind": kind, "status": status,
            "basis": ("technical_primary" if kind == "security" and official else "official_primary" if official else "editorial_report") if status == "supported" else "insufficient",
            "spans": spans if status != "insufficient" else [], "urls": urls if status != "insufficient" else []})
    reasons = []
    if any(e["status"] == "conflict" for e in evidence): reasons.append("evidence_conflict")
    if not any(e["status"] == "supported" for e in evidence): reasons.append("insufficient_evidence" if evidence else "no_core_event")
    return {"scope": "in_scope", "core_evidence": evidence, "reason_codes": reasons}


def admitted(annotation, use):
    p = annotation["source_policy"]
    return annotation["publisher"]["status"] == "identified" and p["admission_status"] in {"approved", "limited"} and p["allow_" + use]


def radar_allowed(row, now, model_org_ids=()):
    when = b.parse(row.get("published_at")) or b.parse(row.get("first_seen_at"))
    if evidence_policy.exclusion_reason(row) or not admitted(row, "radar") or not when or not now - timedelta(hours=24) < when <= now:
        return False
    if row["source_policy"]["scope_id"] == "llm_stats":
        return bool(row.get("model_vendor_id") in model_org_ids and row.get("discovery_source") == "llm_stats_latest_models"
                    and row.get("model_name") and re.fullmatch(r"[a-z0-9._-]{2,120}", str(row.get("model_id") or "")))
    return any(e["kind"] == "model_release" and e["status"] == "supported"
               for e in qualify(row, source_material(row))["core_evidence"])


def qualified_kinds(event, annotation, row, now):
    if not admitted(annotation, "featured") or annotation["qualification"]["scope"] != "in_scope":
        return []
    subject = event["identity"].get("subject", "")
    if subject.startswith(("model:", "software:", "product:")) and b.extract_claim(row, now).subject != subject:
        return []
    kinds = [e["kind"] for e in annotation["qualification"]["core_evidence"] if e["status"] == "supported"]
    action = event["identity"].get("action")
    required = {"security_disclosure": "security", "pricing_change": "pricing", "model_release": "model_release", "speed_tier_release": "model_release", "platform_availability": "model_release"}.get(action)
    return [k for k in kinds if required is None or k == required]


def decide(event, annotations, rows, now, scorer):
    result = {"brief_event_id": event["brief_event_id"], "active_phase_id": event["active_phase_id"],
        "featured_eligible": False, "reason_codes": [], "qualified_source_count": 0,
        "qualified_corroboration_keys": [], "support_article_ids": [], "eligibility_basis": None,
        "featured_primary_article_id": None, "featured_primary_item": None, "featured_score": None,
        "featured_business_events": [], "featured_news_summary": None, "summary_article_id": None}
    if not event["eligible"] or not b.parse(event["effective_at"]) <= now < b.parse(event["expires_at"]):
        result["reason_codes"] = ["outside_reader_window"]
        return result
    candidates = []
    for ref in event["sources"]:
        rid = ref["id"]
        if ref["role"] != "active_phase" or ref.get("phase_id") != event["active_phase_id"]:
            continue
        kinds = qualified_kinds(event, annotations[rid], rows[rid], now)
        if not kinds:
            continue
        # Only the engine's existing active keys may contribute. A metadata
        # inconsistency cannot resurrect a withdrawn or previously absent key.
        if ref.get("corroboration_key") != corroboration.identity(rows[rid])[0]:
            continue
        candidates.append((ref, kinds))
    result["support_article_ids"] = sorted(ref["id"] for ref, _ in candidates)
    keys = sorted({ref["corroboration_key"] for ref, _ in candidates if ref.get("corroboration_key")})
    result.update(qualified_corroboration_keys=keys, qualified_source_count=len(keys))
    if not candidates:
        result["reason_codes"] = ["no_current_qualified_article"]
        return result
    ranked = [(scorer(rows[ref["id"]], b.parse(event["effective_at"]), len(keys)), ref, kinds) for ref, kinds in candidates]
    score, primary, kinds = min(ranked, key=lambda x: (-x[0], annotations[x[1]["id"]]["source_policy"]["source_tier_rank"], x[1]["id"]))
    official = annotations[primary["id"]]["source_policy"]["publisher_kind"] == "official"
    basis = "official_primary" if official else "multiple_qualified_publishers" if len(keys) >= 2 else "qualified_score" if score >= .72 else None
    if not basis:
        result["reason_codes"] = ["below_qualified_gate"] + ([] if keys else ["no_counting_key"])
        return result
    result.update(featured_eligible=True, eligibility_basis=basis, reason_codes=[basis],
        featured_primary_article_id=primary["id"], featured_primary_item=copy.deepcopy(primary),
        featured_score=score, featured_business_events=kinds)
    result["featured_primary_item"]["business_events"] = kinds
    summary = event.get("news_summary")
    if isinstance(summary, str) and summary:
        if primary["id"] == event["primary_item"]["id"] and len(summary) <= 2000:
            result.update(featured_news_summary=summary, summary_article_id=primary["id"])
        else:
            result["reason_codes"].append("summary_primary_mismatch")
    return result


def featured_view(event, decision):
    out = copy.deepcopy(event)
    primary = copy.deepcopy(decision["featured_primary_item"])
    support = set(decision["support_article_ids"])
    refs = [r for r in out["sources"] if r["id"] in support]
    out.update(primary_item=primary, title=primary["title"], url=primary["url"], primary_url=primary["url"],
        source=primary.get("source", ""), source_name=primary.get("source_name", ""),
        sources=refs, items=refs, all_sources=event["sources"], source_count=len(refs),
        corroboration_count=decision["qualified_source_count"], duplicate_count=max(1, decision["qualified_source_count"]),
        score=decision["featured_score"], importance=decision["featured_score"], importance_score=decision["featured_score"],
        business_events=decision["featured_business_events"], publisher_qualified=True,
        governance_publisher_key=primary.get("corroboration_key") or "publisher:" + str(primary["publisher"]["publisher_id"]))
    for key in list(out):
        if key.startswith("news_summary"):
            out.pop(key)
    if decision["featured_news_summary"]:
        out["news_summary"] = decision["featured_news_summary"]
    return out


def _hashes(projection, overlay):
    projection["generation_id"] = "bg1_" + b.digest({k: v for k, v in projection.items() if k != "generation_id"})[:24]
    overlay["brief_generation_id"] = projection["generation_id"]
    overlay["generation_id"] = "pg1_" + b.digest({k: v for k, v in overlay.items() if k != "generation_id"})[:24]


def unavailable(projection, revision, error):
    projection["selected_event_ids"] = []
    overlay = {"record_type": "publisher_governance_projection", "schema_version": 1, "policy_id": policy.POLICY_ID,
        "registry_revision": revision, "generated_at": projection["generated_at"],
        "brief_generation_id": None, "brief_state_revision": projection.get("state_revision"),
        "status": "unavailable", "articles": [], "events": [], "featured_event_ids": [], "daily_selected_event_ids": [],
        "diagnostics": {"errors": [error], "reason_counts": {}}, "generation_id": ""}
    _hashes(projection, overlay)
    return overlay


def build(projection, records, *, now, annotate, scorer, sanitize):
    """Add use decisions after the engine has finalized its immutable state."""
    revision = policy.current_registry().revision
    if projection.get("status") not in {"ready", "recovered"}:
        return unavailable(projection, revision, "invalid_projection")
    if len(projection["events"]) > MAX_EVENTS:
        return unavailable(projection, revision, "projection_capacity")
    raw_rows = {}
    for row in records:
        if row.get("id") in raw_rows:
            return unavailable(projection, revision, "invalid_projection")
        raw_rows[row.get("id")] = row
    annotations, rows = {}, {}
    try:
        for event in projection["events"]:
            refs = event["sources"]
            if len({r["id"] for r in refs}) != len(refs) or event["primary_item"]["id"] not in {r["id"] for r in refs}:
                raise ValueError("invalid_projection")
            for ref in [*refs, *event["items"], event["primary_item"]]:
                rid = ref["id"]
                if rid not in annotations:
                    raw = raw_rows.get(rid)
                    row = annotate(sanitize(raw or ref))
                    material = sanitize(source_material(raw)) if raw else {"title_original": "", "title": "", "summary": ""}
                    rows[rid] = row
                    annotations[rid] = {"id": rid, **{key: row[key] for key in ("ingress", "publisher", "source_policy")},
                                        "qualification": qualify(row, material)}
                    if len(annotations) > MAX_ARTICLES:
                        raise ValueError("projection_capacity")
                else:
                    raw = raw_rows.get(rid)
                    material = sanitize(source_material(raw)) if raw else {"title_original": "", "title": "", "summary": ""}
                ref.update({key: annotations[rid][key] for key in ("ingress", "publisher", "source_policy")}, source_material=material)
        decisions = [decide(e, annotations, rows, now, scorer) for e in projection["events"]]
        featured = {d["brief_event_id"]: d for d in decisions if d["featured_eligible"]}
        views = [featured_view(e, featured[e["brief_event_id"]]) for e in projection["events"] if e["brief_event_id"] in featured]
        # Keep the engine's existing publisher-decay selector, using actual
        # qualified publisher keys instead of query/transport labels.
        selected, per_publisher = [], defaultdict(int)
        while views and len(selected) < 20:
            views.sort(key=lambda e: (-e["score"] + .03 * per_publisher[e["governance_publisher_key"]], e["brief_event_id"]))
            chosen = views.pop(0)
            selected.append(chosen["brief_event_id"])
            per_publisher[chosen["governance_publisher_key"]] += 1
        projection["selected_event_ids"] = selected
        overlay = {"record_type": "publisher_governance_projection", "schema_version": 1, "policy_id": policy.POLICY_ID,
            "registry_revision": revision, "generated_at": projection["generated_at"],
            "brief_generation_id": "", "brief_state_revision": projection["state_revision"], "status": "ready",
            "articles": [annotations[k] for k in sorted(annotations)], "events": decisions,
            "featured_event_ids": sorted(featured), "daily_selected_event_ids": selected,
            "diagnostics": {"errors": [], "reason_counts": dict(Counter(r for d in decisions for r in d["reason_codes"]))}, "generation_id": ""}
        _hashes(projection, overlay)
        if len(b.canonical(overlay)) > MAX_BYTES or len(b.canonical(projection)) > MAX_BYTES:
            return unavailable(projection, revision, "projection_capacity")
        if not validate(overlay, projection):
            return unavailable(projection, revision, "invalid_projection")
        return overlay
    except (KeyError, TypeError, ValueError, OverflowError):
        return unavailable(projection, revision, "invalid_projection")


def metadata(overlay):
    return {key: overlay[key] for key in ("schema_version", "policy_id", "registry_revision", "generated_at", "brief_generation_id", "brief_state_revision", "generation_id", "status")}


def validate(g, projection):
    """Cross-field runtime guard; schema shape is additionally tested offline."""
    try:
        if g["record_type"] != "publisher_governance_projection" or type(g["schema_version"]) is not int or g["schema_version"] != 1 or g["policy_id"] != policy.POLICY_ID or not re.fullmatch(r"[0-9a-f]{64}", g["registry_revision"]): return False
        if len(b.canonical(g)) > MAX_BYTES or len(g["events"]) > MAX_EVENTS or len(g["articles"]) > MAX_ARTICLES: return False
        if g["generation_id"] != "pg1_" + b.digest({k:v for k,v in g.items() if k != "generation_id"})[:24]: return False
        if projection["generation_id"] != "bg1_" + b.digest({k:v for k,v in projection.items() if k != "generation_id"})[:24]: return False
        if g["generated_at"] != projection["generated_at"] or g["brief_generation_id"] != projection["generation_id"] or g["brief_state_revision"] != projection["state_revision"]: return False
        if g["status"] not in {"ready", "unavailable"}: return False
        if g["status"] != "ready": return not any(g[k] for k in ["events", "articles", "featured_event_ids", "daily_selected_event_ids"]) and bool(g["diagnostics"]["errors"])
        if projection["status"] not in {"ready", "recovered"} or g["diagnostics"]["errors"]: return False
        articles = {a["id"]:a for a in g["articles"]}; events = {e["brief_event_id"]:e for e in projection["events"]}
        if len(articles) != len(g["articles"]) or len(events) != len(projection["events"]): return False
        decisions = {d["brief_event_id"]:d for d in g["events"]}
        if len(decisions) != len(g["events"]) or set(decisions) != set(events): return False
        ref_ids = set()
        asof = b.parse(g["generated_at"])
        for eid, event in events.items():
            decision = decisions[eid]; refs = {r["id"]:r for r in event["sources"]}
            if len(refs) != len(event["sources"]) or set(refs) != set(event["member_article_ids"]) or decision["active_phase_id"] != event["active_phase_id"]: return False
            for rid, ref in refs.items():
                ref_ids.add(rid); a=articles[rid]
                sp = a["source_policy"]
                if sp["schema_version"] != 1 or sp["policy_id"] != policy.POLICY_ID or sp["registry_revision"] != g["registry_revision"]: return False
                if sp["admission_status"] not in {"approved", "limited", "unreviewed", "excluded"}: return False
                if sp["admission_status"] == "unreviewed" and (sp["source_tier"] != "watchlist" or sp["source_tier_rank"] != 6 or sp["allow_featured"] or sp["allow_radar"]): return False
                if any(ref[k] != a[k] for k in ("ingress", "publisher", "source_policy")): return False
                for evidence in a["qualification"]["core_evidence"]:
                    if evidence["kind"] not in KINDS or evidence["status"] not in {"supported","insufficient","conflict"}: return False
                    if evidence["status"] == "supported" and not evidence["spans"]: return False
                    for span in evidence["spans"]:
                        text=ref["source_material"][span["field"]]
                        if type(span["start"]) is not int or type(span["end"]) is not int or not 0 <= span["start"] < span["end"] <= len(text) or text[span["start"]:span["end"]] != span["text"]: return False
            support = decision["support_article_ids"]
            if len(support) != len(set(support)): return False
            keys=set()
            for rid in support:
                ref=refs[rid]; a=articles[rid]
                if rid not in event["member_article_ids"] or ref["role"] != "active_phase" or ref["phase_id"] != event["active_phase_id"] or not admitted(a,"featured") or a["qualification"]["scope"] != "in_scope": return False
                if not qualified_kinds(event, a, {**ref, **ref["source_material"]}, asof): return False
                if ref.get("corroboration_key"): keys.add(ref["corroboration_key"])
            if len(decision["qualified_corroboration_keys"]) != len(set(decision["qualified_corroboration_keys"])) or keys != set(decision["qualified_corroboration_keys"]) or len(keys) != decision["qualified_source_count"]: return False
            if decision["featured_eligible"]:
                primary=decision["featured_primary_item"];rid=decision["featured_primary_article_id"]
                if not event["eligible"] or not b.parse(event["effective_at"]) <= asof < b.parse(event["expires_at"]) or rid not in support or primary["id"] != rid: return False
                if any(primary[k] != refs[rid][k] for k in ("id","title","url","publisher","source_policy","source_material")): return False
                if not math.isfinite(decision["featured_score"]) or not 0 <= decision["featured_score"] <= 1 or not decision["featured_business_events"]: return False
                kinds=set(qualified_kinds(event, articles[rid], {**refs[rid], **refs[rid]["source_material"]}, asof))
                if not set(decision["featured_business_events"]) <= kinds: return False
                basis=decision["eligibility_basis"]
                if basis == "official_primary":
                    if articles[rid]["source_policy"]["publisher_kind"] != "official": return False
                elif basis == "multiple_qualified_publishers":
                    if len(keys) < 2: return False
                elif basis != "qualified_score" or decision["featured_score"] < .72: return False
                if decision["featured_news_summary"] is not None:
                    if decision["summary_article_id"] != rid or event["primary_item"]["id"] != rid or decision["featured_news_summary"] != event.get("news_summary"): return False
                elif decision["summary_article_id"] is not None: return False
            elif any(decision[k] is not None for k in ("featured_primary_article_id","featured_primary_item","featured_score","eligibility_basis","featured_news_summary","summary_article_id")) or decision["featured_business_events"]: return False
        if ref_ids != set(articles): return False
        featured=[eid for eid,d in decisions.items() if d["featured_eligible"]]
        if len(g["featured_event_ids"]) != len(set(g["featured_event_ids"])) or set(featured) != set(g["featured_event_ids"]): return False
        return g["daily_selected_event_ids"] == projection["selected_event_ids"] and len(g["daily_selected_event_ids"]) <= 20 and len(g["daily_selected_event_ids"]) == len(set(g["daily_selected_event_ids"])) and set(g["daily_selected_event_ids"]) <= set(featured)
    except (KeyError, TypeError, ValueError, OverflowError):
        return False
