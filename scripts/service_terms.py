"""Bounded original-text service changes; no inference from display summaries."""
from __future__ import annotations

import re


def rx(pattern):
    return re.compile(pattern, re.I)


QUOTA = rx(r"\b(?:quotas?|usage limits?|rate limits?|credits?|allowances?|token-based|billing|metering)\b|配[額额]|[額额]度|用量|使用上限|計費|计费|計量|计量")
PLAN = rx(r"\b(?:plans?|subscriptions?|subscribers?|paid|Plus|Pro|Business|Enterprise|Team|Max)\b|方案|訂閱|订阅|會員|会员|付費|付费")
CHANGE = rx(r"\b(?:doubl\w*|halv\w*|rais\w*|increas\w*|reduc\w*|cuts?|chang\w*|adjust\w*|revers\w*|reset\w*|compensat\w*|remov\w*|shar\w*|pool\w*|unif\w*|grant\w*)\b|翻倍|加倍|提高|上調|上调|降低|下調|下调|調整|调整|更新.{0,8}(?:規則|规则)|取消|撤回|共用|共享|重置|補償|补偿|發放|发放")
MECHANISM = rx(r"\b(?:doubl\w*|halv\w*|common|shar\w*|pool\w*|token-based|per (?:token|request|task|month)|unlimited)\b|\d|翻倍|加倍|共用|共享|重置|補償|补偿|計費|计费|每(?:月|次|週|周|日)")
ACCOUNT_LIMIT = rx(r"\b(?:capp?ing|caps?|limits?|restrict\w*)\b.{0,65}\b(?:paid|accounts?|subscriptions?)\b|限制.{0,20}(?:付費|付费|帳戶|账户|訂閱|订阅)")
ACCOUNT_UNIT = rx(r"\b(?:per device|payment card|per card)\b|每.{0,5}(?:裝置|设备|設備|付款卡|支付卡)")
DATA = rx(r"\b(?:data|sessions?|conversations?)\b|資料|数据|對話|对话")
TRAIN = rx(r"\b(?:use|uses|using)\b.{0,100}\btrain\w*\b|使用.{0,50}(?:訓練|训练)")
CONSENT = rx(r"\b(?:opt-out|opt out|turned off training|consent)\b|退出|拒絕|拒绝|同意|關閉.{0,8}訓練|关闭.{0,8}训练")
WATERMARK = rx(r"\bwatermarks?\b|浮水印|水印")
ROLLOUT = rx(r"\b(?:expand\w*|roll\w* out|extend\w*)\b|擴大|扩大|擴展|扩展")
UNCERTAIN = rx(r"\b(?:rumou?r|reportedly|might|could|may|expected to|plans? to|considering|if)\b|據傳|据传|傳聞|传闻|可能|考慮|考虑|如果|擬議|拟议")
DENIED = rx(r"\b(?:not|never|no longer)\s+(?:sharing|share|changing|change|capping|using|use|expanding)|\b(?:quota|usage limits?)\b.{0,15}\bunchanged\b|沒有調整|没有调整|並未調整|并未调整|額度不變|额度不变")
NEGATED_CHANGE = rx(r"\b(?:not|never|denies|denied)\b.{0,25}\b(?:doubl\w*|increas\w*|reduc\w*|shar\w*|chang\w*|capp?ing)\b|(?:並未|并未|否認|否认).{0,8}(?:翻倍|共享|限制|調整|调整)")
MONTH = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
START = rx(r"\b(?:starting|effective|from|on)\s+(?:(?:in|on)\s+)?(?:" + MONTH
           + r"\b(?:\s+\d{1,2})?|\d{1,2}\s+" + MONTH
           + r"\b|\d{4}[-/]\d{1,2}(?:[-/]\d{1,2})?|\d{1,2}[-/]\d{1,2})"
           + r"|(?:自|從|从)\s*(?:\d{4}年)?\d{1,2}月(?:\d{1,2}日)?(?:起|生效)?")
MODEL_OBJECT = rx(r"\b(?:models?|AI|ChatGPT|Codex|Claude|Copilot|Gemini)\b|模型|人工智慧|人工智能")


def classify(title, summary, *, product):
    """Return a pricing/policy cue only with a concrete, asserted native clause.

    product is established by the caller's existing product/model parser.
    A scheduled change is admissible only with a specific start in its clause;
    the mere existence of a plan, quota or a future prediction is insufficient.
    """
    if not product or DENIED.search(title) or NEGATED_CHANGE.search(title):
        return None
    # Sentence boundaries exclude decimal/version dots and publication footers.
    summary = re.split(r"\bThe article\b|\bThe post\b", summary, flags=re.I)[0]
    clauses = re.split(r"(?<=[!?。！？])\s*|\.(?=\s+[A-Z])|\n|[;；]", title + "\n" + summary)
    title_uncertain = UNCERTAIN.search(START.sub("", title))
    if title_uncertain and not re.search(r"\bplans? to\b", title, re.I):
        return None
    for clause in clauses:
        if (not clause.strip() or UNCERTAIN.search(START.sub("", clause)) or DENIED.search(clause)
                or NEGATED_CHANGE.search(clause)):
            continue
        if re.search(r"\bwill\b", clause, re.I) and not START.search(clause):
            continue
        if title_uncertain and not START.search(clause):
            continue
        if (QUOTA.search(clause) and PLAN.search(clause) and CHANGE.search(clause)
                and MECHANISM.search(clause)):
            return "pricing"
        if ACCOUNT_LIMIT.search(clause) and ACCOUNT_UNIT.search(clause) and PLAN.search(clause):
            return "pricing"
        if (DATA.search(clause) and TRAIN.search(clause) and MODEL_OBJECT.search(clause)
                and START.search(clause) and CONSENT.search(summary)):
            return "policy"
        if WATERMARK.search(clause) and ROLLOUT.search(clause) and MODEL_OBJECT.search(clause):
            return "policy"
    return None
