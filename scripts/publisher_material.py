"""Bounded native-text cues for use qualification, separate from event matching.

Names are grammatical candidates, never publisher grants or fact verification.
Unknown prose remains insufficient; these helpers never fetch missing material.
"""
from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Mention:
    text: str
    offset: int

    def group(self):
        return self.text

    def start(self):
        return self.offset

    def end(self):
        return self.offset + len(self.text)


# Case matters for grammatical proper names; matching is intentionally bounded.
NAME = re.compile(r"(?<![A-Za-z0-9])(?:[A-Z][A-Za-z0-9]*(?:[._/-][A-Za-z0-9]+)*)(?:[ \t]+(?:[A-Z][A-Za-z0-9]*(?:[._/-][A-Za-z0-9]+)*|v?\d+(?:\.\d+)*(?:[A-Za-z]+)?)){0,4}")
CJK_NAME = re.compile(r"[\u3400-\u9fff]{2,14}(?:公司|集團|集团|科技|平台|銀行|银行)")
STOP_NAMES = {"AI", "API", "The", "This", "A", "An", "New", "Original", "General", "Generic", "Critical", "Security", "Researchers", "Research", "Report", "Revenue", "Earnings", "Quarter", "Q1", "Q2", "Q3", "Q4", "FY", "SUMMARY", "TITLE", "Market", "Global", "Worldwide", "Study", "Survey", "Company", "Companies", "Benchmark", "Findings", "Results", "Quarterly", "Fiscal", "Warning", "Vulnerability", "Vulnerabilities", "Unconfirmed", "Rumor", "Industry"}
TITLE_VERB = re.compile(r"\b(?:Releases?|Released|Launch(?:es|ed)?|Introduces?|Introduced|Announces?|Announced|Reports?|Acquires?|Acquired|Scores?)\b")
MODEL_WORD = r"(?:(?:AI|language|speech|video|foundation|generative|frontier|multimodal|vision|reasoning|open|voice|audio)[ -]+)*models?"
MODEL_BEFORE = re.compile(r"(?:\b" + MODEL_WORD + r"|模型)\s*[:：\"「『“]?\s*$", re.I)
MODEL_AFTER = re.compile(r"^\s*(?:" + MODEL_WORD + r"(?![A-Za-z0-9])|模型)", re.I)
CLAUSES = re.compile(r"[。;；\n]|(?<=[a-z])\.\s+")


def names(text):
    result = []
    candidates=[]
    for match in NAME.finditer(text):
        last=match.start()
        for verb in TITLE_VERB.finditer(match.group()):
            candidates.extend(Mention(m.group(),last+m.start()) for m in NAME.finditer(text[last:match.start()+verb.start()]))
            last=match.start()+verb.end()
        candidates.extend(Mention(m.group(),last+m.start()) for m in NAME.finditer(text[last:match.end()]))
    candidates.extend(Mention(m.group(),m.start()) for m in CJK_NAME.finditer(text))
    for match in candidates:
        value = match.group().rstrip()
        leading=re.match(r"(?:The|A|An)\s+",value)
        offset=match.start()+(leading.end() if leading else 0)
        if leading:value=value[leading.end():]
        # AI/model describes the adjacent name, rather than being its suffix.
        value = re.sub(r"(?:\s+(?:AI|Model|Models))+$", "", value)
        if value and not all(w in STOP_NAMES for w in value.split()) and not re.fullmatch(r"(?:Q[1-4]|FY|[Vv])\s*\d*", value):
            result.append(Mention(value, offset))
    return result


def models(text, known):
    result = [Mention(m.group(), m.start()) for m in known.finditer(text)]
    for m in names(text):
        before, after = text[max(0, m.start()-60):m.start()], text[m.end():m.end()+60]
        # A complete previously unknown name needs an explicit model noun, or
        # a versioned name directly performing a named evaluation.
        versioned_result = bool(re.search(r"\d", m.text) and re.match(r"\s+(?:scores?|achieves?|得分|測得|测得)\b", after, re.I))
        if MODEL_BEFORE.search(before) or MODEL_AFTER.search(after) or versioned_result:
            result.append(m)
    # The headline can omit the noun supplied by the lead, but the exact name
    # must recur. This does not infer a model from an unrelated publisher name.
    established = [m.text for m in result]
    result.extend(m for m in names(text) if any(same_name(m.text, value) for value in established))
    return sorted({(m.start(), m.end()): m for m in result}.values(), key=lambda m: (m.start(), -len(m.text)))


def benchmark_named(text, known):
    if known.search(text):
        return True
    for m in names(text):
        before, after = text[max(0,m.start()-35):m.start()], text[m.end():m.end()+35]
        if re.search(r"(?:on|在|於|于)\s*$", before, re.I) and re.search(r"bench|eval|基準|基准|評測|评测", m.text+after, re.I):
            return True
        if re.match(r"\s+(?:benchmark|evaluation|test)\b|\s*(?:基準|基准|評測|评测)", after, re.I):
            return True
    return False


def same_name(a, b):
    compact = lambda s: re.sub(r"[^a-z0-9\u3400-\u9fff]", "", s.casefold())
    return compact(a) == compact(b)


def model_is_release_object(text, mention):
    """Require a complete model noun phrase, rather than an unknown head noun.

    A model can end the object or be followed by a separate qualifier/clause.
    An unfinished nominal tail cannot inherit the
    release verb. This also rejects unseen artifact names/modifiers, without
    treating publications in later clauses as a veto on a real model release.
    """
    tail = CLAUSES.split(text[mention.end():], maxsplit=1)[0].lstrip()
    possessive = re.compile(r"^(?:['’]s\b|的)\s*", re.I)
    tail = re.sub(r'^["”」』]\s*', '', tail)
    # Type/edition words can finish the model noun phrase. They cannot hide a
    # later artifact head: 'speech model series documentation' is unfinished.
    cjk_model = r"(?:(?:語音|语音|語言|语言|音頻|音频|視頻|视频|決策|决策|推理|多模態|多模态|生成|視覺|视觉))*模型"
    tail = re.sub(r"^(?:" + MODEL_WORD + r"(?![A-Za-z0-9])|" + cjk_model + r")\s*", "", tail, count=1, flags=re.I)
    tail = re.sub(r"^(?:預覽版|预览版|系列|preview(?: version)?\b|series\b)\s*", "", tail, count=1, flags=re.I)
    if possessive.match(tail):
        tail = possessive.sub('', tail, count=1)
        if not re.match(r"weights\b|權重|权重", tail, re.I):
            return False
    # Public weights are the model distribution, provided 'weights' itself
    # completes the object (not 'weights documentation', for example).
    tail = re.sub(r"^(?:weights\b|權重|权重)\s*", "", tail, count=1, flags=re.I)
    return bool(re.match(
        r"^(?:$|[,.:;!?，。：；！？\n]|[\"”」』](?:\s|$)|"
        r"\b(?:and|with|alongside|including|for|to|which|that|is|are|was|were|has|have|now|generally|officially|available|released|launched)\b|"
        r"及|與|与|並|并|附|用於|用于|可供|(?:(?:現已|现已|已|正式)\s*)?(?:發布|发布|推出|開放|开放|上線|上线)|"
        r"(?:準確率|准确率|效能|性能|速度)(?:達到|达到|超過|超过|超越|提升)|(?:支持|支援)\s*(?=\d))",
        tail, re.I))


def financial_entities(text, companies):
    """Native name candidates, excluding period/currency and prose labels."""
    known = [Mention(m.group(), m.start()) for m in companies.finditer(text)]
    result = list(known)
    labels = STOP_NAMES | {"Discussion", "Outlook", "Update", "Forecast", "Review", "Financial", "IPO",
                          "USD", "US", "Its", "It", "Our", "We", "They", "Their", "In", "By", "As"}
    labels = {s.casefold() for s in labels}
    for mention in names(text):
        if any(mention.start() < m.end() and m.start() < mention.end() for m in known):
            continue
        words = mention.text.split()
        while words and (words[-1].casefold() in labels
                         or re.fullmatch(r"(?:Q[1-4]|FY|20\d{2}|\d+)", words[-1], re.I)):
            words.pop()
        if words:
            result.append(Mention(" ".join(words), mention.start()))
    return result


def financial_actors(text, companies, finance):
    """Names governing finance predicates, excluding later attribution/segments."""
    entities = sorted(financial_entities(text, companies), key=lambda m: m.start())
    actors = []
    for index, entity in enumerate(entities):
        end = entities[index + 1].start() if index + 1 < len(entities) else len(text)
        follows = text[entity.end():end][:160]
        precedes = text[max(0, entity.start() - 60):entity.start()]
        # 'Acme reports revenue ... CNBC confirmed' and 'revenue from Acme'
        # have different roles. The next named entity bounds the predicate, so
        # 'OpenAI says Cedar reports revenue' belongs to Cedar, not OpenAI.
        if finance.search(follows) or re.search(r"(?:revenue|earnings|income|profit)\s+(?:from|of|at|for)\s*$", precedes, re.I):
            actors.append(entity)
            previous = index - 1
            while previous >= 0 and re.fullmatch(r"\s*(?:,|and|&|及|與|与|和|、)\s*", text[entities[previous].end():entities[previous + 1].start()], re.I):
                actors.append(entities[previous])
                previous -= 1
    return actors


def financial_clauses(title, summary, companies, finance):
    """Tie each financial clause to a headline actor, carrying only clear ellipsis."""
    targets = financial_actors(title, companies, finance) or financial_entities(title, companies)[:1]
    if not targets:
        return []
    clauses = [title]
    # A single headline actor licenses 'Revenue rose ...'; a foreign named
    # actor resets that context, so its following pronouns cannot borrow it.
    inherited = len({m.text.casefold() for m in targets}) == 1
    for sentence in CLAUSES.split(summary):
        for clause in re.split(r"\b(?:while|whereas)\b|而(?=[\u3400-\u9fffA-Z])", sentence):
            actors = financial_actors(clause, companies, finance)
            if actors:
                inherited = all(any(same_name(m.text, t.text) for t in targets) for m in actors)
            elif not finance.search(clause):
                # A named new subject can reset an omitted subject in the next
                # sentence. Names after a financial statement (attribution or
                # segment names) do not themselves own that statement.
                entities = financial_entities(clause, companies)
                if entities:
                    inherited = all(any(same_name(m.text, t.text) for t in targets) for m in entities)
            if inherited:
                clauses.append(clause)
    return clauses


def focused_text(title, summary, known_models, products, companies):
    """Keep native clauses about one headline subject; never borrow a rival's data."""
    combined = title + "\n" + summary
    model_titles = [m for m in models(combined, known_models) if m.end() <= len(title)]
    groups = [(model_titles, lambda s: models(s, known_models)),
              ([Mention(m.group(),m.start()) for m in products.finditer(title)], lambda s: list(products.finditer(s))),
              ([Mention(m.group(),m.start()) for m in companies.finditer(title)], lambda s: list(companies.finditer(s)))]
    for targets, find in groups:
        distinct = {re.sub(r"\W", "", m.group().casefold()) for m in targets}
        if len(distinct) != 1:
            if distinct:
                break
            continue
        target = targets[0].group()
        kept=[]
        for clause in CLAUSES.split(summary):
            mentions=find(clause)
            if mentions and any(not same_name(m.group(), target) for m in mentions):
                continue
            kept.append(clause)
        summary="\n".join(kept)
        break
    return title + "\n" + summary


def out_of_scope(title, summary, legacy):
    # Reporting a new teaching product, guide publication, or conference result
    # is distinct from asking the reader to follow instructions or buy tickets.
    reporting = bool(re.search(r"\b(?:announces?|publishes?|releases?|introduces?)\b.{0,55}(?:tutorial|guide|course)|(?:發布|发布|推出|公布).{0,30}(?:教學|教程|課程|课程)", title, re.I))
    # A release-led news headline may include a later 'how to' section. The
    # reverse (a tutorial with a product name in its prefix) stays instructional.
    prefix=title.split(":",1)[0].split("：",1)[0]
    reporting = reporting or bool(re.search(r"\b(?:launches|released|releases|introduces|introduced)\b",prefix,re.I) and not re.search(r"how to|for beginners|tutorial",prefix,re.I))
    tutorial = re.search(r"\b(?:how to|for beginners|beginner.s guide|step.by.step|tutorial|tips for|ways to (?:use|boost|improve))\b|(?:開發者|开发者|使用者|用户).{0,6}(?:指南|手冊|手册)", title, re.I)
    imperative_sale = re.search(r"^(?:save\s+\d|buy\b|register\b|book your\b)|立即(?:報名|报名|購票|购票)|票券.{0,12}(?:優惠|优惠|折扣)", title, re.I)
    summary_sale = re.search(r"^(?:register now|buy (?:your |a )?ticket|save \d+\s*%).{0,150}(?:ticket|conference|event|pass)", summary, re.I)
    advice = re.search(r"(?:企業|企业|團隊|团队|政府).{0,10}如何.{0,30}(?:防止|避免|治理|管理|成長|成长|提升|提高).{0,25}(?:建議|建议|方向|方法|秘訣|秘诀)", title)
    return bool(imperative_sale or summary_sale or (not reporting and (tutorial or legacy or advice)))


def uncertain_market(text):
    """A proposed/talked-about transaction is not an announced commitment."""
    return bool(re.search(r"\b(?:rumou?r|reportedly|may acquire|might acquire|could acquire|plans? to acquire|in talks|negotiat\w*|consider(?:s|ed|ing)? (?:an? )?acquisition|unconfirmed)\b|據傳|据传|傳聞|传闻|(?:擬|拟|有意|欲|傳被|传被|傳將|传将).{0,8}(?:收購|收购|併購|并购)|(?:收購|收购|併購|并购).{0,30}(?:談判|谈判|洽談|洽谈|磋商|未定案|未敲定)|(?:談判|谈判|洽談|洽谈|磋商).{0,30}(?:收購|收购|併購|并购)|未經證實|未经证实|拒絕證實|拒绝证实", text, re.I))


TRANSACTION = re.compile(r"\bacquir(?:e|es|ed|ing)\b|\bmerg(?:e|es|ed|ing|er)\b|\bacquisition\b|收購|收购|併購|并购|合併|合并", re.I)


def predicate_parts(clause, action):
    """Scope questions to this predicate, excluding a colon-led next clause."""
    start = max(clause.rfind(':', 0, action.start()), clause.rfind('：', 0, action.start())) + 1
    following = re.search(r"[:：]", clause[action.end():])
    end = action.end() + following.start() if following else len(clause)
    return clause[start:action.start()], clause[action.end():end]


def predicate_prefix(prefix):
    """Remove neutral parenthetical adjuncts without discarding their negation."""
    governing = re.compile(r"\b(?:not|never|no|if|unless|whether|may|might|could|would|will|\w+n['’]t)\b|不|未|無|无|否|如果|假如|可能", re.I)
    def adjunct(match):
        inside = match.group()[1:-1]
        return ' ' + inside + ' ' if governing.search(inside) else ' '
    prefix = re.sub(r"\([^()\n]{1,100}\)|（[^（）\n]{1,100}）|—[^—\n]{1,100}—|,[^,\n]{1,100},|，[^，\n]{1,100}，", adjunct, prefix)
    return re.split(r"\bbut\b|但|卻|却", prefix, flags=re.I)[-1][-200:]


def predicate_unasserted(clause, action):
    """Question/antecedent/negative state belonging to one release predicate."""
    prefix, following = predicate_parts(clause, action)
    before = predicate_prefix(prefix)
    return bool(re.search(r"[?？]", following) or re.search(
        r"\b(?:if|unless|whether|suppose|supposing)\b|是否|會否|会否|能否|會不會|会不会|如果|假如|假設|假设|倘若", prefix, re.I)
        or re.search(r"\b(?:not(?!\s+(?:only|just)\b)|never|no longer|\w+n['’]t)\b(?:[ -]+[\w'’]+){0,5}\s*$"
                     r"|(?:並未|并未|尚未|沒有|没有|不會|不会|未|不)(?:曾|已|正式|真正|真的|將|将|會|会)*\s*$", before, re.I))


def transaction_state(clause, action):
    """Recognize an asserted predicate; an unknown governing phrase is uncertain."""
    prefix, following = predicate_parts(clause, action)
    before = predicate_prefix(prefix)
    # Questions and antecedent conditions do not assert the transaction. A
    # condition *after* an announced agreement (regulatory approval) is allowed.
    if re.search(r"[?？]", following) or re.search(
        r"\b(?:if|unless|whether|suppose|supposing)\b|是否|會否|会否|能否|會不會|会不会|如果|假如|假設|假设|倘若", prefix, re.I):
        return "uncertain"
    # Auxiliary chains permit inflection/composition: 'is not acquiring',
    # 'does not plan to acquire', 'has never intended to acquire', etc.
    if re.search(r"\b(?:not(?!\s+(?:only|just)\b)|never|no longer|\w+n['’]t|rul(?:e|es|ed) out|declin(?:e|es|ed|ing)|refus(?:e|es|ed|ing)|decid(?:e|es|ed) against)\b(?:[ -]+[\w'’]+){0,5}\s*$"
                 r"|\bno\s+(?:current\s+)?(?:intentions?|plans?|agreement|decision|commitment)\s+(?:of|to)\s*$"
                 r"|(?:不會|不会|並未|并未|尚未|沒有|没有|無意|无意|否認|否认|拒絕|拒绝|放棄|放弃|取消|不|未)(?:(?:打算|計劃|计划|考慮|考虑|有|曾|將|将|進行|进行|完成|正式|真正|真的|決定|决定|會|会|再|已經|已经))*\s*$", before, re.I):
        return "negated"
    if re.search(r"\b(?:consider(?:s|ed|ing)?|explor(?:e|es|ed|ing)|hop(?:e|es|ed|ing)|wish(?:es|ed|ing)?|want(?:s|ed|ing)?|intend(?:s|ed|ing)?|aim(?:s|ed|ing)?|seek(?:s|ing)?|plan(?:s|ned|ning)?|propos(?:e|es|ed|ing)|expect(?:s|ed|ing)?|anticipat(?:e|es|ed|ing)|unlikely|may|might|could|would)\b(?:[ -]+[\w'’]+){0,5}\s*$"
                 r"|(?:擬|拟|考慮|考虑|計劃|计划|打算|希望|有意|欲|可能|或將|或将|預期|预期|預計|预计).{0,14}$", before, re.I):
        return "uncertain"
    # Affirmative finite forms and progressive/future auxiliaries state an
    # action; bare infinitives/gerunds need a specific commitment governor.
    verb = action.group().casefold()
    subjects = sorted(names(before), key=lambda m: m.end())
    bridge = before[subjects[-1].end():] if subjects else before
    asserted_auxiliaries = re.fullmatch(
        r"\s*(?:(?:announces?|announced|confirms?|confirmed)\s+(?:that\s+)?(?:it\s+)?)?"
        r"(?:(?:has|have|had|is|are|was|were|will|be|being|been|just|also|already|officially|successfully|now|recently|currently|actively|not only)\s+)*",
        bridge, re.I)
    if verb in {"acquires", "acquired", "merges", "merged"} and asserted_auxiliaries:
        return "affirmed"
    if verb in {"acquire", "merge", "acquiring", "merging"} and asserted_auxiliaries and re.search(
        r"\b(?:will(?: be)?|is|are|was|were|has been|have been|had been)\s+(?:(?:now|currently|officially|actively)\s+)*$", before, re.I):
        return "affirmed"
    if re.fullmatch(
        r"\s*(?:(?:has|have|had)\s+)?(?:"
        r"(?:agrees?|agreed)\s+to\s*|"
        r"(?:signs?|signed|enters?|entered)\s+(?:(?:a|an|the|definitive|binding|final|merger|acquisition)\s+)*(?:agreement|deal|contract)\s+(?:to|for)\s*|"
        r"(?:announces?|announced|confirms?|confirmed|completes?|completed|approves?|approved)\s+(?:(?:its|the|a|an)\s+)*(?:(?:agreement|deal)\s+to\s+)?)",
        bridge, re.I):
        return "affirmed"
    if verb in {"acquisition", "merger"} and re.fullmatch(r"\s*(?:(?:has|have|had)\s+)?(?:signs?|signed|enters?|entered)\s+(?:(?:a|an|the|definitive|binding)\s+)*", bridge, re.I) and re.match(r"\s+(?:agreement|deal|contract)\b", clause[action.end():], re.I):
        return "affirmed"
    if re.search(r"[\u3400-\u9fff]", verb):
        # Monetary adjuncts and passive/commitment frames remain assertions.
        # The price is a modifier of this action, not a separate business cue.
        price = r"(?:約|约)?\s*(?:US\$|USD|\$)?\s*\d[\d.,]*\s*(?:億|亿|萬|万|兆|million|billion)?\s*(?:美元|元|USD|dollars)"
        if re.fullmatch(r"(?:\s|宣布|宣佈|已|已經|已经|正式|完成|將|将|決定|决定|同意|簽署|签署|達成|达成|[\"“「『]|反向|獲|获|被|大幅溢價|大幅溢价|全現金|全现金|未獲監管核准便|以\s*" + price + r")*", bridge, re.I):
            return "affirmed"
    return "uncertain"


def transaction_denied(text):
    return any(transaction_state(clause, action) == "negated"
               for clause in CLAUSES.split(text) for action in TRANSACTION.finditer(clause))


def market_action_supported(text):
    if uncertain_market(text):
        return False
    for clause in CLAUSES.split(text):
        if re.search(r"antitrust (?:probe|investigation|fine)|(?:regulator|FTC|commission).{0,40}(?:orders?|fines?|investigat)|反壟斷調查|反垄断调查|勒令|shuts? down|permanent shutdown|ceases? (?:permanently )?operations|permanently cease operations|宣布.{0,12}(?:停運|停止營運|終止服務)", clause, re.I):
            return True
        for action in re.finditer(r"\bacquir(?:e|es|ed|ing)\b|\bmerg(?:es|ed)\b|收購|收购|併購|并购|合併|合并",clause,re.I):
            if transaction_state(clause, action) != "affirmed":
                continue
            before,after=clause[:action.start()],re.split(r"[,，]",clause[action.end():],maxsplit=1)[0][:100]
            # A real named object or passive named target is required. A budget
            # for acquisitions, acquisition interest, or 'merged revenue' is not
            # a transaction between companies.
            if re.match(r"\s*(?:營收|营收|收入)",after):
                continue
            objects=names(after)
            if objects and names(before):
                return True
            if re.search(r"被|獲|获",before[-40:]) and names(before):
                return True
            if re.search(r"(?:簽署|签署)\s*$", before) and re.match(r"\s*(?:協議|协议|合約|合约)", after) and len(names(before)) >= 2:
                return True
            if re.search(r"(?:達成|达成)[\s\"“「『]*(?:反向)?$", before) and re.match(r"(?:僱傭|雇佣)?[\"”」』]?\s*交易", after) and len(names(before)) >= 2:
                return True
        if any(transaction_state(clause, m) == "affirmed" for m in re.finditer(r"\bacquisition\b|\bmerger\b", clause, re.I)) and re.search(r"\b(?:signs?|signed|enters?|entered|announces?|announced|confirms?|confirmed|completes?|completed|approves?|approved|agrees?|agreed)\b",clause,re.I) and len(names(clause))>=2:
            return True
    return False
