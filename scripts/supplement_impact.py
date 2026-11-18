"""Bounded, native-material impact score for all already qualified featured events."""
from __future__ import annotations

import re
import math

try:
    from scripts import signal_material
except ModuleNotFoundError:
    import signal_material


MONEY = re.compile(r"(?:US\s*)?\$\s*(\d+(?:\.\d+)?)\s*(billion|bn|million|m)\b", re.I)
CHINESE_MONEY = re.compile(r"(\d+(?:\.\d+)?)\s*(億|万|萬)\s*(?:美[元金]|USD)", re.I)
FINANCE = re.compile(r"\b(?:funding|financing|investment|invests?|offering|stock sale|raises?|raised|secures?|secured)\b|融資|募資|投資|股票發行", re.I)
SUPPLY_ATTACK = re.compile(r"supply.chain|發布鏈|供應鏈|official release|官方發布", re.I)
RELEASE_CHANNEL = re.compile(r"(?<![A-Za-z0-9])(?:PyPI|container|registry|published package|malicious version)(?![A-Za-z0-9])|惡意版本|發布渠道", re.I)
HARM = re.compile(r"\b(?:attack|compromis\w*|malicious|stolen|breach|hacked|exfiltrat\w*)\b|入侵|惡意|竊取|外洩", re.I)
MONITORING = re.compile(r"\b(?:unmonitored|monitoring gap|unobserved traffic)\b|監控缺口|未受監控", re.I)
REALIZED_SAVINGS = re.compile(r"\b(?:annual cost savings|realized savings|saved in operating costs)\b|年度節省成本|已節省成本", re.I)
DEPLOYMENT = re.compile(r"\b(?:deploy\w*|contract|refinery|factory|enterprise rollout)\b|部署|合約|煉油廠", re.I)
PRODUCT = re.compile(r"\b(?:launch\w*|releas\w*|introduc\w*|unveil\w*|open.sourc\w*|redesign|update|integration|platform|tool)\b|推出|發布|開源|改版|更新|平台|工具", re.I)
UNIT_COMPARE = re.compile(r"\b(?:instead of|versus|vs\.?|compared (?:with|to))\b|對比|相較於", re.I)
DOLLAR_VALUE = re.compile(r"\$\s*\d+(?:\.\d+)?")
CENT_VALUE = re.compile(r"\b\d+(?:\.\d+)?\s+cents?\b", re.I)
WORK_UNIT = re.compile(r"\b(?:per|an?|one)\s+(?:hour|video|token|request|image|task)\b|每(?:小時|次|張|百萬)|一小時", re.I)
QUALITY = re.compile(r"\b(?:quality|accuracy|performance|scor\w*|error|benchmark)\b|品質|準確|效能|評測", re.I)
AI_DIRECT = re.compile(r"(?<![A-Za-z])(?:AI|LLM|GPT|Claude|Copilot|LiteLLM|OpenAI|Anthropic|Nvidia|Meta|Qwen)(?![A-Za-z])|\bmodel\b|人工智慧|模型|機器學習", re.I)
OTHER_INDUSTRY = re.compile(r"\b(?:refinery|oil|bank|hospital|factory|manufacturer)\b|煉油廠|銀行|醫院|製造", re.I)
CONTENT_ONLY = re.compile(r"\b(?:clip|trailer|video generated|film|Odyssey)\b|影片片段|電影預告", re.I)
E_DETAIL = re.compile(r"\b(?:because|after|using|uses?|found|affect\w*|caus\w*|result\w*|includ\w*|add\w*|built?|deplo\w*|test\w*|quality|sav\w*|customer\w*|closed|expand\w*|leaked|entered|scor\w*)\b|引入|功能|發現|发现|影響|影响|造成|結果|结果|採用|采用|測試|测试|節省|节省|外洩|外泄|憑證|凭证|渠道", re.I)
FUNDRAISE = re.compile(r"\b(?:fundrais\w*|funding round|financing round|stock offering|stock sale)\b|"
    r"\b(?:announc\w*|clos\w*|secur\w*|rais\w*|receiv\w*|obtain\w*)\b.{0,36}"
    r"\b(?:funding|financing|bank loans?|credit facilit(?:y|ies))\b|\b(?:raises?|raised|secures?|secured)\s+"
    r"(?:(?:an?|another|additional|fresh)\s+)*(?:US\s*)?\$\s*\d|"
    r"融資|融资|募資|募资|募得|股票發行|股票发行|銀行授信|银行授信", re.I)
ACQUISITION_ACTION = re.compile(r"\b(?:acquires|acquired|merges|merged)\b|(?:正式|已)?(?:收購|收购|併購|并购)", re.I)
LIVE_CHANGE = re.compile(
    r"\b(?:now generally available|now available|went live|entered general availability|"
    r"has deployed|has opened|has shipped|began serving|started serving|now operates|"
    r"now serves|now runs)\b|已(?:上[線线]|投入運作|投入运作|正式開放|正式开放|部署|開始提供|开始提供)", re.I)
LIVE_OBJECT = re.compile(r"\b(?:API|GPUs?|capacity|inference|clusters?|platform|models?|customers?|users?)\b|算力|叢集|集群|推理|使用者|用戶|用户|客戶|客户|模型", re.I)
LIVE_HEDGE = re.compile(r"\b(?:plans?|intends?|aims?|hopes?|would|could|might|not|if|expects?|projected|will)\b|計劃|计划|擬|拟|可能|預計|预计|尚未|並未|并未", re.I)
EXPLICIT_SUBJECT = re.compile(r"^\s*(?:(?:the|its)\s+(?:company|startup|developer|team)|it)\s+", re.I)
MODEL_ID = re.compile(r"\b(?:GPT|Claude|Gemini|Grok|Qwen|DeepSeek|Llama|Mistral|Voxtral|GLM|Kimi)"
    r"[\s\-‐‑–]*(?:(?:Opus|Sonnet|Haiku)\s+)?[vVkK]?\d+(?:\.\d+)*"
    r"(?:[\s\-‐‑–]+(?:Astra|Sol|Luna|Pro|Max|Mini|Nano|Flash|Lite|Preview)\b)*", re.I)
MODEL_ACCESS = re.compile(r"\b(?:now (?:generally )?available|generally available|available now)\b"
    r".{0,90}\b(?:API|Copilot|ChatGPT|Codex|Bedrock|Vertex AI|AI Studio|Azure)\b|"
    r"(?:正式|現已|现已).{0,14}(?:開放|开放|上[線线]).{0,50}(?:API|Copilot|ChatGPT|Codex|Bedrock|Vertex AI)", re.I)
MODEL_RANK = re.compile(r"\b(?:benchmark|index|leaderboard)\b.{0,90}\b(?:ranks?|placed|ranked)\s+"
    r"(?:first|second|third|fourth|fifth|#?\d+)(?![A-Za-z0-9])", re.I)


FACTORY_BRAND = re.compile(r"\bFactory(?:['’]s)?(?=\s+(?:Droid\b|(?:releases?|released|launches?|launched|introduces?|introduced)\s+Droid\b))", re.ASCII)


def _dollars(text):
    amounts = []
    for value, unit in MONEY.findall(text):
        amounts.append(float(value) * (1_000_000_000 if unit.lower() in {"billion", "bn"} else 1_000_000))
    for value, unit in CHINESE_MONEY.findall(text):
        amounts.append(float(value) * (100_000_000 if unit == "億" else 10_000))
    return max(amounts, default=0)


def _model_ids(text):
    return {re.sub(r"[^a-z0-9.]", "", match[0].lower()) for match in MODEL_ID.finditer(text)}


def score(native, basis, personnel_impact=None, *, model_release=False):
    """Return I/P/E/C; conservative when native material lacks commercial scale."""
    _, title, summary = signal_material.native(native)
    text = title + "\n" + summary
    if not title:
        return {"i": 0, "p": 0, "e": 0, "c": 0, "total": 0, "passes": False}

    capital = bool(re.search(r"acquir|acquisition|merger|收購|收购|併購|并购", title, re.I))
    finance = bool(FINANCE.search(title)) or capital
    amount = _dollars(text) if finance else 0
    realized_savings = _dollars(text) if REALIZED_SAVINGS.search(text) and DEPLOYMENT.search(text) else 0
    supply_harm = bool(SUPPLY_ATTACK.search(text) and RELEASE_CHANNEL.search(text) and HARM.search(text))
    monitored_gap = bool(MONITORING.search(text) and re.search(r"\d+(?:\.\d+)?\s*%", summary))
    unit_cost = bool(len(DOLLAR_VALUE.findall(summary)) + len(CENT_VALUE.findall(summary)) >= 2
                     and UNIT_COMPARE.search(summary)
                     and WORK_UNIT.search(text) and QUALITY.search(text))
    industry_title = FACTORY_BRAND.sub("", title)
    deployment = bool(DEPLOYMENT.search(industry_title))
    product = bool(PRODUCT.search(title) and not CONTENT_ONLY.search(title))

    if supply_harm or amount >= 1_000_000_000:
        impact = 40
    elif amount >= 100_000_000 or realized_savings >= 100_000_000 or monitored_gap:
        impact = 30
    elif deployment or unit_cost or (finance and amount > 0):
        impact = 15
    elif product and not CONTENT_ONLY.search(title):
        impact = 5
    else:
        impact = 0

    quantified_business = bool(re.search(r"revenue|earnings|operating costs?|market share|營收|营收|營運成本|市佔|市占", text, re.I)
                               and (re.search(r"\d+(?:\.\d+)?\s*%", text) or _dollars(text) > 0))
    if quantified_business:
        impact = max(30, impact)
    if basis == "supported_core":
        impact = max(15, impact)

    if basis == "supported_core" or supply_harm or (finance and amount > 0) or product or deployment:
        proximity = 20
    elif unit_cost:
        proximity = 10
    else:
        proximity = 0

    # A repeated headline supplies an actor and action, but not a second
    # checkable mechanism, affected party, or outcome.
    title_words = set(re.findall(r"[a-z0-9]+", title.lower()))
    new_words = {w for w in re.findall(r"[a-z0-9]+", summary.lower()) if len(w) > 3} - title_words
    cjk_detail = bool(re.search(r"[\u3400-\u9fff]", summary) and len(summary) >= len(title) + 20
                      and title not in summary)
    financing = FUNDRAISE.search(title)
    funding = bool(financing and not ACQUISITION_ACTION.search(title, 0, financing.start())
                   and not re.search(r"\b(?:IPO|initial public offering)\b|首次公開募股|首次公开募股", title, re.I))
    actual_change = False
    if funding:
        actor = re.split(r"\b(?:has |just )?(?:raises?|raised|secures?|secured|closes?|closed|launches?)\b|"
                         r"(?:完成|獲得|获得|募資|募资|融資|融资)", title, maxsplit=1, flags=re.I)[0].strip()
        actual_change = any(LIVE_CHANGE.search(clause) and LIVE_OBJECT.search(clause)
            and not LIVE_HEDGE.search(clause)
            and (index == 0 and EXPLICIT_SUBJECT.search(clause)
                 or actor and clause.lstrip().lower().startswith(actor.lower() + " "))
            for index, clause in enumerate(signal_material.cues.CLAUSES.split(summary)))
        impact = 15 if actual_change else min(impact, 15)
        proximity = 20 if actual_change else min(proximity, 10)
    model_ids = _model_ids(title) if model_release else set()
    release_detail = bool(model_ids and not LIVE_HEDGE.search(summary)
        and (any(model_ids & _model_ids(clause) and MODEL_ACCESS.search(clause)
                 for clause in signal_material.cues.CLAUSES.split(summary))
             or model_ids & _model_ids(summary) and MODEL_RANK.search(summary)))
    detailed = ((len(new_words) >= 5 or cjk_detail) and E_DETAIL.search(summary) or release_detail or actual_change
                ) and not CONTENT_ONLY.search(title)
    evidence = 20 if detailed else 10 if title else 0

    if basis == "industry_news" and personnel_impact in (15, 20, 30):
        total = personnel_impact + 20 + evidence + 20
        return {"i": personnel_impact, "p": 20, "e": evidence, "c": 20,
                "total": total, "passes": total >= 70}

    if CONTENT_ONLY.search(title):
        centrality = 0
    elif (OTHER_INDUSTRY.search(industry_title) and deployment) or (capital and re.search(r"(?:AI|OpenAI|Anthropic)[ -]backed|(?:AI|人工智慧).{0,6}(?:支持|支援|投資)", title, re.I) and not re.search(r"\b(?:model|LLM|inference)\b|模型|推理", title, re.I)):
        centrality = 10
    elif basis == "capability_disclosure" or AI_DIRECT.search(text):
        centrality = 20
    else:
        centrality = 0
    if centrality < 20:
        impact = min(15, impact)
    total = impact + proximity + evidence + centrality
    return {"i": impact, "p": proximity, "e": evidence, "c": centrality,
            "total": total, "passes": total >= 70 and (impact >= 30 or proximity == 20)}


def freshness(age_hours):
    """Faster early decay, with the same 48-hour half-value point."""
    return 2 ** -math.sqrt(max(0.0, age_hours) / 48.0)


def rank(impact, selection_class, effective, now):
    value = (impact["total"] + (3 if selection_class == "core" else 0)) * freshness((now - effective).total_seconds() / 3600) / 103
    return round(value, 4)
