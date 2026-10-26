"""Bounded, native-material impact score for already qualified D+ supplements."""
from __future__ import annotations

import re

try:
    from scripts import signal_material
except ModuleNotFoundError:
    import signal_material


MONEY = re.compile(r"(?:US\s*)?\$\s*(\d+(?:\.\d+)?)\s*(billion|bn|million|m)\b", re.I)
CHINESE_MONEY = re.compile(r"(\d+(?:\.\d+)?)\s*(億|万|萬)\s*(?:美[元金]|USD)", re.I)
FINANCE = re.compile(r"\b(?:funding|financing|investment|invests?|offering|stock sale|raises?|raised|secures?|secured)\b|融資|募資|投資|股票發行", re.I)
SUPPLY_ATTACK = re.compile(r"supply.chain|發布鏈|供應鏈|official release|官方發布", re.I)
RELEASE_CHANNEL = re.compile(r"\b(?:PyPI|container|registry|published package|malicious version)\b|惡意版本|發布渠道", re.I)
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


def _dollars(text):
    amounts = []
    for value, unit in MONEY.findall(text):
        amounts.append(float(value) * (1_000_000_000 if unit.lower() in {"billion", "bn"} else 1_000_000))
    for value, unit in CHINESE_MONEY.findall(text):
        amounts.append(float(value) * (100_000_000 if unit == "億" else 10_000))
    return max(amounts, default=0)


def score(native, basis):
    """Return I/P/E/C; conservative when native material lacks commercial scale."""
    _, title, summary = signal_material.native(native)
    text = title + "\n" + summary
    if not title:
        return {"i": 0, "p": 0, "e": 0, "c": 0, "total": 0, "passes": False}

    finance = bool(FINANCE.search(title))
    amount = _dollars(title) if finance else 0
    realized_savings = _dollars(text) if REALIZED_SAVINGS.search(text) and DEPLOYMENT.search(text) else 0
    supply_harm = bool(SUPPLY_ATTACK.search(text) and RELEASE_CHANNEL.search(text) and HARM.search(text))
    monitored_gap = bool(MONITORING.search(text) and re.search(r"\d+(?:\.\d+)?\s*%", summary))
    unit_cost = bool(len(DOLLAR_VALUE.findall(summary)) + len(CENT_VALUE.findall(summary)) >= 2
                     and UNIT_COMPARE.search(summary)
                     and WORK_UNIT.search(text) and QUALITY.search(text))
    deployment = bool(DEPLOYMENT.search(title))
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

    if supply_harm or (finance and amount > 0):
        proximity = 20
    elif product or deployment:
        proximity = 10
    else:
        proximity = 0

    # A repeated headline supplies an actor and action, but not a second
    # checkable mechanism, affected party, or outcome.
    title_words = set(re.findall(r"[a-z0-9]+", title.lower()))
    new_words = {w for w in re.findall(r"[a-z0-9]+", summary.lower()) if len(w) > 3} - title_words
    cjk_detail = bool(re.search(r"[\u3400-\u9fff]", summary) and len(summary) >= len(title) + 20
                      and title not in summary)
    detailed = (len(new_words) >= 5 or cjk_detail) and E_DETAIL.search(summary) and not CONTENT_ONLY.search(title)
    evidence = 20 if detailed else 10 if title else 0

    if CONTENT_ONLY.search(title):
        centrality = 0
    elif OTHER_INDUSTRY.search(title) and deployment:
        centrality = 10
    elif basis == "capability_disclosure" or AI_DIRECT.search(text):
        centrality = 20
    else:
        centrality = 0
    total = impact + proximity + evidence + centrality
    return {"i": impact, "p": proximity, "e": evidence, "c": centrality,
            "total": total, "passes": total >= 70 and (impact >= 30 or proximity == 20)}
