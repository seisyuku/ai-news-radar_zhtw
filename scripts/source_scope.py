"""Bounded platform-event policy shared by intake, relevance and event tags.

Only publisher-owned native routes participate. No network, clock, saved
acceptance flags, or inference from an article's age is used here.
"""

from dataclasses import dataclass
from datetime import datetime
import re
from urllib.parse import urlsplit


def rx(pattern):
    return re.compile(pattern, re.I)


TW_PUBLISHERS = {
    "inside": "inside.com.tw",
    "ithome": "ithome.com.tw",
    "technews 科技新報": "technews.tw",
}
KNOWN_PLATFORM = rx(r"(?<![a-z0-9])(?:zeabur|opencode|n8n|dify)(?![a-z0-9])")
SERVICE = rx(r"雲端部署|云端部署|應用(?:程式)?(?:部署|託管)|網站託管|網站代管|(?<![a-z])paas(?![a-z])")
BROAD_SERVICE = rx(r"雲端平台|雲端服務|云端平台|自動化平台|(?<![a-z])saas(?![a-z])")
SERVICE_USE = rx(r"應用|網站|程式|資料庫|工作流程|軟體|託管|代管")
CONSUMER = rx(r"個人相簿|雲端相簿|個人雲端硬碟|雲端硬碟|google photos|icloud photos")
RELATED = rx(r"延伸閱讀|相關閱讀|相關文章|read more|related articles")
CLAUSES = rx(r"[。！？!?；;\n]+|(?<!\d)\.(?!\d)")
EXIT = rx(r"停止營運|結束營運|停止运营|終止營運|全面停止服務|永久(?:停運|關閉|停止服務)|shut(?:ting)? down|wind(?:ing)? down|ceas(?:e|ing) operations")
PARTIAL = rx(r"舊(?:版|方案|叢集|集群)|部分(?:服務|功能)|單一(?:功能|區域)|停止支援|停止支持|legacy|\bfeature\b|\bregion\b")
DENIAL = rx(r"否認.{0,24}(?:停運|關閉|停止|結束)|(?:不會|並未|並非|無意|不打算|尚未決定).{0,16}(?:停運|關閉|停止|結束)|den(?:y|ies|ied).{0,30}(?:shutdown|shutting|closing)|not shutting down")
SECURITY = rx(r"遭.{0,12}(?:入侵|攻擊)|資料外洩|資料外泄|憑證外洩|金鑰外洩|金鑰遭|\b(?:breach|intrusion|hacked|compromised)\b|(?:keys?|credentials?|data).{0,25}(?:exposed|leaked|stolen)")
SECURITY_NEGATION = rx(r"(?:未|沒有|無)(?:發現|證據|遭到|遭)?[^，,。]{0,10}(?:入侵|外洩|外泄)|(?:防範|避免|預防).{0,12}(?:入侵|外洩|外泄)|no (?:evidence of |confirmed )?(?:breach|intrusion)")
PRICE = rx(r"漲價|降價|費率|價格|收費|付費|方案|\b(?:pric(?:e|es|ing)|billing|subscription)\b")
ACCESS = rx(r"權限|資料.{0,10}(?:匯出|存取)|(?:匯出|存取).{0,10}(?:資料|權限)|data (?:export|access)")
CHANGE = rx(r"調整|調漲|調降|改為|改成|取消|不再|限制|由.{0,24}(?:改|變|調)|漲價|降價|increase|decrease|remov|restrict|no longer|from .{0,30} to ")
EXISTING = rx(r"既有|現有|原有|原本|原可|老用戶|舊用戶|所有用戶|所有使用者|現行|existing|current (?:users|customers|plan)|previously")
EFFECTIVE = rx(r"即日起|已生效|正式實施|生效|起實施|起調整|日起|開始實施|effective|takes effect|starting (?:on |from )?\d")
PROMO = rx(r"業配|業配文|合作宣傳|贊助內容|sponsored|advertorial|新客|新用戶|新使用者|限時|優惠碼|推薦獎勵|免費試用|free trial|new customers|promo code")
UNCONFIRMED_CHANGE = rx(r"可能|考慮|預測|傳聞|尚未定案|rumou?r|\bmay\b|\bmight\b|considering")
OUTAGE = rx(r"中斷|停機|當機|服務故障|無法使用|\b(?:outage|downtime|unavailable)\b")
FUTURE_OR_TOTAL = rx(r"預計|預估|預告|可能|將會|將(?:中斷|停機)|累計|累積|間歇|斷斷續續|planned|scheduled|expected|intermittent|cumulative")
DURATION = rx(r"(?P<over>超過|超出|逾|more than\s*|over\s*)?\s*(?P<number>\d+(?:\.\d+)?|[一二兩三四五六七八九十百]+)\s*(?P<unit>小時|天|日|hours?|days?)")
ISO = r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2})?(?:Z|[+-]\d{2}:\d{2})"
START_TIME = rx(r"(?:自|始於|since\s*|from\s*)\s*(" + ISO + r")")
RECOVERY_TIME = rx(r"(?:於|at\s*)\s*(" + ISO + r")\s*(?:恢復|restored|recovered)")
ONGOING = rx(r"仍未恢復|仍無法|持續中斷|至今|尚未恢復|ongoing|still unavailable|remains unavailable")


@dataclass(frozen=True)
class PlatformDecision:
    applies: bool = False
    admitted: bool = False
    events: tuple[str, ...] = ()
    reason: str = ""


def runtimewire_article_allowed(record):
    """Also rejects retained catalog records before the all-items/MT path."""
    if str(record.get("site_id") or "") != "runtimewire":
        return True
    try:
        u = urlsplit(str(record.get("url") or ""))
        return (u.scheme in {"http", "https"} and u.hostname in {"runtimewire.com", "www.runtimewire.com"}
                and u.path.startswith("/article/") and bool(u.path[len("/article/"):]))
    except ValueError:
        return False


def _publisher(record):
    try:
        u = urlsplit(str(record.get("url") or ""))
        host = u.hostname or ""
    except ValueError:
        return ""
    if u.scheme not in {"http", "https"}:
        return ""
    source = str(record.get("source") or "").casefold().strip()
    if record.get("site_id") == "tw_media":
        domain = TW_PUBLISHERS.get(source)
        if domain and host in {domain, "www." + domain}:
            return "tw"
    if record.get("site_id") == "runtimewire" and source == "runtimewire" and runtimewire_article_allowed(record):
        return "runtimewire"
    return ""


def _subject(text, native_tw):
    if KNOWN_PLATFORM.search(text):
        return "known_platform_event"
    if native_tw and (SERVICE.search(text) or (BROAD_SERVICE.search(text) and SERVICE_USE.search(text))):
        return "cloud_application_service_event"
    return ""


def _number(value):
    try:
        return float(value)
    except ValueError:
        digits = dict(zip("一二兩三四五六七八九", [1, 2, 2, 3, 4, 5, 6, 7, 8, 9]))
        total = current = 0
        for ch in value:
            if ch in "十百":
                total += (current or 1) * (10 if ch == "十" else 100)
                current = 0
            else:
                current = digits[ch]
        return total + current


def _time(value):
    try:
        t = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return t if t.utcoffset() is not None else None
    except (ValueError, TypeError):
        return None


def _long_outage(text, published_at):
    if not OUTAGE.search(text) or FUTURE_OR_TOTAL.search(text):
        return False
    for match in DURATION.finditer(text):
        hours = _number(match["number"]) * (24 if match["unit"].lower() in {"天", "日", "day", "days"} else 1)
        if hours > 72 or (hours == 72 and match["over"]):
            return True
    start = START_TIME.search(text)
    recovery = RECOVERY_TIME.search(text)
    # The article's publish timestamp is usable only if it explicitly says
    # the same outage is ongoing, never merely because the article is old.
    end = _time(recovery[1]) if recovery else (_time(published_at) if ONGOING.search(text) else None)
    beginning = _time(start[1]) if start else None
    return bool(beginning and end and (end - beginning).total_seconds() > 72 * 3600)


def platform_event_decision(record):
    publisher = _publisher(record)
    if not publisher:
        return PlatformDecision()
    title = RELATED.split(str(record.get("title_original") or record.get("title") or ""), maxsplit=1)[0]
    summary = RELATED.split(str(record.get("summary") or ""), maxsplit=1)[0]
    # Consumer storage claims cannot gain admission by adding AI to the
    # headline, even when no deployment-platform subject was recognized.
    if CONSUMER.search(title) and any(pattern.search(title) for pattern in (PRICE, ACCESS, EXIT, OUTAGE, SECURITY)):
        return PlatformDecision(True, False, (), "personal_cloud_service_excluded")
    native_tw = publisher == "tw"
    title_subject = _subject(title, native_tw)
    if not title_subject and native_tw and BROAD_SERVICE.search(title) and SERVICE_USE.search(summary):
        title_subject = "cloud_application_service_event"
    clauses = [c.strip() for c in CLAUSES.split(summary) if c.strip()]
    # A named title is not permission to borrow a different company's event
    # from the description. Accept explicit subjects or short continuations.
    context = [title] if title_subject else []
    title_name = KNOWN_PLATFORM.search(title)
    for clause in clauses:
        name = KNOWN_PLATFORM.search(clause)
        if title_name and name and name[0].casefold() != title_name[0].casefold():
            continue
        if _subject(clause, native_tw) or (title_subject and re.match(
            r"(?:該平台|該公司|這家|這個|客戶|用戶|使用者|既有|現有|原有|原可|自\d|已|服務|帳戶|從\d|於\d|\d{1,2}月|its |the (?:platform|company)|existing )", clause, re.I
        )):
            context.append(clause)
    reason = title_subject or next((_subject(c, native_tw) for c in context if _subject(c, native_tw)), "")
    if not reason:
        return PlatformDecision()
    text = "\n".join(context)
    if CONSUMER.search(title) or (not title_subject and CONSUMER.search(text)):
        return PlatformDecision(True, False, (), "personal_cloud_service_excluded")

    security = any(SECURITY.search(c) and not SECURITY_NEGATION.search(c) for c in context)
    exits = any(EXIT.search(c) and not DENIAL.search(c)
                and (not PARTIAL.search(c) or re.search(r"全面|整個平台|entire platform", c, re.I)) for c in context)
    if DENIAL.search(title):
        exits = False
    # A title saying the platform stops service plus an explicit customer
    # migration in the description is a shutdown, not an ordinary outage.
    if title_subject and "停止服務" in title and re.search(r"遷移(?:網站|資料庫|服務)|遷移網站及資料庫|migrate", text, re.I):
        exits = exits or not (DENIAL.search(title) or PARTIAL.search(title) or OUTAGE.search(title))
    price_or_access = bool(PRICE.search(text) or ACCESS.search(text))
    strict_change = bool(price_or_access and CHANGE.search(text) and EXISTING.search(text) and EFFECTIVE.search(text))
    if (PROMO.search(title) or UNCONFIRMED_CHANGE.search(text)
            or re.search(r"業配|贊助內容|合作宣傳|sponsored|advertorial", summary, re.I)):
        strict_change = False
    outage_context = context + ([title + " " + context[1]] if OUTAGE.search(title) and len(context) > 1 else [])
    outage = any(_long_outage(c, record.get("published_at")) for c in outage_context)
    events = tuple(event for event, yes in (("market", exits), ("security", security),
                                           ("pricing", strict_change and bool(PRICE.search(text)))) if yes)
    admitted = exits or security or strict_change or outage
    # Failed concrete-event claims must not bypass the bounded policy simply
    # by adding AI to a promotion, short outage, or shutdown denial headline.
    intent = bool(price_or_access or OUTAGE.search(text) or EXIT.search(text) or DENIAL.search(text))
    return PlatformDecision(bool(admitted or intent), bool(admitted), events,
                            reason if admitted else "platform_event_evidence_insufficient")
