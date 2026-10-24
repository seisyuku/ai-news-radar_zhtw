"""Native-material qualifications for D+, separate from the legacy matcher.

These bounded cues nominate reading material, not independently verified facts.
They never change general AI classification, source admission or event identity.
"""
from __future__ import annotations

import copy
import re

try:
    from scripts import publisher_governance as legacy, publisher_material as cues, ai_relevance
except ModuleNotFoundError:  # direct generator invocation
    import publisher_governance as legacy
    import publisher_material as cues
    import ai_relevance


INDUSTRY_LABELS = frozenset({"model_release", "ai_product_update", "industry_business",
    "infra_compute", "infrastructure", "developer_tool", "developer_tooling",
    "ai_tech", "agent_workflow"})
GENRE = legacy.rx(r"^(?:how\b|using\b|building\b|scaling\b|see\b|meet\b|turning\b)|"
    r"\b(?:tutorial|walkthrough|tips|showcase|builders? (?:are|using)|"
    r"what .{0,30} (?:building|making)|part (?:one|two|three|\d+))\b|"
    r"教學|教程|技巧|攻略|看看|如何|操作指南|心得|使用分享|案例分享|第[一二三123]部分")
OPINION = legacy.rx(r"\b(?:says?|believes?|thinks?|predicts?|warns?|opinion|commentary|interview)\b|"
    r"表示|認為|认为|預言|预言|預測|预测|專訪|专访|觀點|观点")
NEWS_ACTION = legacy.rx(r"\b(?:announc(?:e|es|ed)|launch(?:es|ed)?|introduc(?:e|es|ed)|"
    r"releas(?:e|es|ed)|unveil(?:s|ed)?|roll(?:s|ed)? out|open.sources?|"
    r"acquir(?:e|es|ed)|acquisition|funding|raises?|raised|invest(?:s|ed|ment)?|"
    r"partner(?:s|ed|ship)?|deploy(?:s|ed|ment)?|audit|investigation|breach|vulnerability|shutdown)\b|"
    r"發布|发布|發表|发表|推出|開放|开放|上線|上线|更新|新增|收購|收购|融資|融资|"
    r"募資|募资|投資|投资|合作|簽約|签约|部署|停運|停运|漏洞|稽核|調查|调查|揭露")
ATTRIBUTION = legacy.rx(r"\b(?:says?|said|reports?|reveals?|publishes?|discloses?)\b|"
    r"表示|指出|公布|披露|揭露|發表|发表")
MODEL_CONTEXT = legacy.rx(r"\b(?:model|models)\b|模型")
ASSESSMENT = legacy.rx(r"\b(?:align(?:ed|ment)?|capab(?:le|ility|ilities)|outperforms?|"
    r"safety|cybersecurity)\b|對齊|对齐|能力|效能|性能|安全評估|安全评估")
TEST_METHOD = legacy.rx(r"\b(?:test(?:s|ed|ing)?|evalua\w*|experiment\w*|benchmark\w*)\b|"
    r"測試|测试|評估|评估|評測|评测|實驗|实验")
QUANTIFIED = legacy.rx(r"\d+(?:\.\d+)?\s*(?:%|percent|out of|of\s+\d+|分)|"
    r"\d+\s*/\s*\d+|百分之\d+")
EVALUATOR = re.compile(r"\b[A-Z][A-Z0-9-]{2,15}\b")
UNRELEASED = legacy.rx(r"\bunreleased\b|\bunpublished\b|not (?:yet )?(?:released|available)|"
    r"未(?:發[布佈表]|发布|公開|公开)|尚未(?:發[布佈表]|发布|公開|公开)")

# The extension requires a versioned proper name as the release object and a
# model noun in its apposition. It is not a growing vendor/model allowlist.
_TOKEN = r"(?:[A-Z][A-Za-z0-9]*(?:[._/-][A-Za-z0-9]+)*|[vV]?\d+(?:\.\d+)*(?:[A-Za-z0-9]+)?)"
_NAME = r"[A-Z][A-Za-z0-9]*(?:[._/-][A-Za-z0-9]+)*(?:[ \t]+" + _TOKEN + r"){0,8}"
RELEASE_OBJECT = re.compile(r"(?:\b(?i:releases?|released|launch(?:es|ed)?|introduces?|introduced|"
    r"announces?|announced)\s+(?:(?i:its|the|a|new|latest|flagship|open-weight)\s+)*|"
    r"(?:發布|发布|發表|发表|推出)\s*(?:全新|新版|模型)?\s*)(?P<name>" + _NAME + r")")
APPOSITIVE_MODEL = legacy.rx(r"^\s*[,，:：—-]?\s*(?:an?\s+)?"
    r"(?:(?:open|small|large|language|AI|vision|speech|audio|video|multimodal|foundation|"
    r"reasoning|generative|local|on-device|端側|端侧|開源|开源|小型|語言|语言)[ -]*)*"
    r"(?:models?\b|模型)")


def native(material):
    field = "title_original" if material.get("title_original") else "title"
    title = legacy.RELATED.split(material.get(field, ""), maxsplit=1)[0][:1600]
    summary = legacy.RELATED.split(material.get("summary", ""), maxsplit=1)[0][:1600]
    return field, title, summary


def evidence(row, material):
    field, title, summary = native(material)
    spans = [{"field": k, "start": 0, "end": len(v), "text": v}
             for k, v in ((field, title), ("summary", summary)) if v]
    urls = list(dict.fromkeys(url for value in [row.get("url"), *(row.get("publisher_links") or [])]
        if (url := legacy.identity.public_url(value)[0])))[:24]
    return spans, urls


def versioned_release(material):
    """Return an asserted full model object; never infer it from a brand alone."""
    _, title, summary = native(material)
    text = title + "\n" + summary
    if (legacy.RUMOR.search(text) or legacy.SPECULATIVE_ACTION.search(text)
            or legacy.RELEASE_HISTORY.search(text) or legacy.DENIAL.search(text)):
        return None
    headline_objects = [re.sub(r"\s+(?:AI|Language|Model|Models)$", "", x.group("name").rstrip())
                        for x in RELEASE_OBJECT.finditer(title) if re.search(r"\d", x.group("name"))]
    for source in (title, summary):
        for clause in cues.CLAUSES.split(source):
            if re.search(r"^\s*(?:did|does|has|have|is|are|will|can|could)\b", clause, re.I):
                continue
            for match in RELEASE_OBJECT.finditer(clause):
                name = match.group("name").rstrip()
                # A trailing descriptor belongs to the model noun, not its ID.
                name = re.sub(r"\s+(?:AI|Language|Model|Models)$", "", name)
                if not re.search(r"\d", name) or len(name) > 120:
                    continue
                if headline_objects and not any(cues.same_name(name, target) for target in headline_objects):
                    continue
                mention = cues.Mention(name, match.start("name"))
                tail = clause[mention.end():]
                apposition = APPOSITIVE_MODEL.search(tail[:160])
                if not apposition:
                    continue
                object_end = mention.end() + apposition.end()
                complete = cues.Mention(clause[mention.start():object_end], mention.start())
                if (cues.model_is_release_object(clause, complete)
                        and not cues.predicate_unasserted(clause,
                            cues.Mention(match.group(), match.start()))):
                    return name
    return None


def qualify_core(row, material):
    """Keep six core kinds; extend only complete native release-object parsing."""
    result = copy.deepcopy(legacy.qualify(row, material))
    if result["scope"] != "in_scope" or "evidence_conflict" in result["reason_codes"]:
        return result
    released = versioned_release(material)
    _, title, _ = native(material)
    unseen_object = any(re.search(r"\d", match.group("name"))
        and not legacy.b.MODEL_RE.search(match.group("name")) for match in RELEASE_OBJECT.finditer(title))
    if unseen_object and not released:
        for item in result["core_evidence"]:
            if item["kind"] == "model_release" and item["status"] == "supported":
                item.update(status="insufficient", basis="insufficient", spans=[], urls=[])
        if not any(item["status"] == "supported" for item in result["core_evidence"]):
            result["reason_codes"] = ["insufficient_evidence"] if result["core_evidence"] else ["no_core_event"]
    if not released:
        return result
    spans, urls = evidence(row, material)
    supported = {"kind": "model_release", "status": "supported",
        "basis": "official_primary" if row["source_policy"]["publisher_kind"] == "official" else "editorial_report",
        "spans": spans, "urls": urls}
    result["core_evidence"] = [e for e in result["core_evidence"] if e["kind"] != "model_release"] + [supported]
    result["reason_codes"] = [c for c in result["reason_codes"] if c not in {"no_core_event", "insufficient_evidence"}]
    return result


def supplement(row, material, qualification):
    """Specific news or attributed measured disclosure, not a seventh core kind."""
    result = {"kind": None, "spans": [], "urls": [], "qualifiers": []}
    _, title, summary = native(material)
    text = title + "\n" + summary
    if (qualification["scope"] != "in_scope" or not title
            or any(e["status"] == "conflict" for e in qualification["core_evidence"])
            or legacy.PROMO.search(title) or legacy.ADVICE.search(title) or GENRE.search(title)
            or legacy.RUMOR.search(text) or legacy.SPECULATIVE_ACTION.search(text)):
        return result
    relevance = ai_relevance.score_ai_relevance({**row, **material})
    if not relevance["is_ai_related"] or relevance["score"] < ai_relevance.AI_RELEVANCE_THRESHOLD:
        return result
    # A "says" headline is not automatically opinion. Retained test/method,
    # evaluator and measured results must accompany the attributed model claim.
    measured_test = any(TEST_METHOD.search(clause) and QUANTIFIED.search(clause)
        and (EVALUATOR.search(clause) or legacy.BENCH.search(clause))
        for clause in cues.CLAUSES.split(summary))
    disclosure = (legacy.COMPANY.search(title) and ATTRIBUTION.search(title)
        and MODEL_CONTEXT.search(title) and ASSESSMENT.search(title)
        and measured_test)
    if disclosure:
        result.update(kind="capability_disclosure", qualifiers=["provider_claim"])
        if UNRELEASED.search(text):
            result["qualifiers"].append("unreleased")
    elif (relevance["label"] in INDUSTRY_LABELS and NEWS_ACTION.search(title)
            and not OPINION.search(title) and not legacy.DENIAL.search(text)
            # Failed core evidence cannot be relabelled as generic news.
            and not qualification["core_evidence"]):
        result["kind"] = "industry_news"
    else:
        return result
    result["spans"], result["urls"] = evidence(row, material)
    return result
