"""Bounded recognition of named AI personnel changes in native news text."""
from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata


ORGANIZATIONS = re.compile(
    r"(?<![A-Za-z0-9])(?:OpenAI|Anthropic|Google(?: DeepMind)?|DeepMind|Meta(?: AI)?|NVIDIA|"
    r"Microsoft(?: AI)?|Thinking Machines(?: Lab)?|DeepSeek|Hugging Face|Mistral AI|xAI|AMD)(?![A-Za-z0-9])"
    r"|微軟|微软|輝達|英伟达|騰訊(?:\s*AI Lab)?|腾讯(?:\s*AI Lab)?|字節(?:跳動)?(?:\s*Seed)?|"
    r"字节(?:跳动)?(?:\s*Seed)?|(?<![A-Za-z])(?:ByteDance|Tencent)(?![A-Za-z])", re.I)
AI_DUTY = re.compile(
    r"\b(?:AI|LLM|machine learning|reinforcement learning|foundation models?|Claude Code|"
    r"ChatGPT|Codex|Gemini|Copilot|DeepMind|Seed)\b|人工智慧|人工智能|機器學習|机器学习|"
    r"模型(?:研究|訓練|训练|團隊|团队)|大模型", re.I)
AI_LABS = {"openai", "anthropic", "deepmind", "thinking machines", "deepseek", "hugging face", "mistral ai", "xai"}
TOP = re.compile(r"\b(?:CEO|CTO|chief executive officer|chief technology officer)\b|"
    r"執行長|执行长|首席執行官|首席执行官|技術長|技术长|首席技術官|首席技术官|"
    r"(?:entire|all) (?:AI |model )?research (?:division|organization)|整(?:條|条|個|个).{0,8}研究(?:線|线|部門|部门)", re.I)
LEAD = re.compile(
    r"\b(?:heads?|leads?|led|leading|runs?|ran|oversees?|oversaw|in charge of|responsible for)\b"
    r".{0,28}\b(?:flagship (?:AI )?products?|core (?:AI )?products?|(?:AI|model|"
    r"research|AI research) (?:teams?|divisions?)|Claude Code|ChatGPT|Codex|Gemini|Copilot)\b|"
    r"\b(?:head|lead|director|VP)\b.{0,24}\b(?:AI|research|machine learning|"
    r"Claude Code|ChatGPT|Codex|Gemini|Copilot)\b|"
    r"\b(?:AI|research|machine learning|Claude Code|ChatGPT|Codex|Gemini|Copilot)\b.{0,22}"
    r"\b(?:head|lead|director)\b|"
    r"(?:主導|主导|掌管|帶領|带领|領導|领导|負責|负责).{0,14}"
    r"(?:旗艦|旗舰|核心|研究|模型|AI|Claude Code|ChatGPT|Codex|Gemini|Copilot)|"
    r"(?:旗艦|旗舰|核心|研究|模型|AI|Claude Code|ChatGPT|Codex|Gemini|Copilot).{0,18}"
    r"(?:[產产]品[負负][責责]人|[技研][術术發发]?[負负][責责]人|[負负][責责]人|主管|總監|总监)", re.I)
SENIOR = re.compile(
    r"\b(?:chief [a-z]+(?: [a-z]+){0,3} officer|[A-Z]PO|CFO|COO|president|VP|vice president|"
    r"director|head|senior counsel(?:or|lor)?|senior advis(?:er|or))\b|"
    r"主管|總監|总监|[負负][責责]人|總裁|总裁|副總|副总|首席|資深顧問|资深顾问", re.I)

_JOIN_EN = r"joins?|joined|moves? to|moved to|defects? to"
_JOIN_ZH = r"加入|轉戰|转战|加盟|跳槽(?:至|到)?"
_LEAVE_EN = r"leaves?|left|departs?(?: from)?|departed(?: from)?|is departing|resigns?(?: from)?|resigned(?: from)?|steps? down(?: from)?|stepping down(?: from)?|exits?"
_LEAVE_ZH = r"離職|离职|離開|离开|請辭|请辞|辭職|辞职|辭[去任]|辞[去任]|卸任"
_APPOINT_EN = r"appoints?|appointed|hires?|hired|names?|named|taps?|tapped|promotes?|promoted"
_APPOINT_ZH = r"任命|聘任|聘請|聘请|延攬|延揽|升任|出任|接任"
_JOIN = rf"(?:{_JOIN_EN}|{_JOIN_ZH})"
_LEAVE = rf"(?:{_LEAVE_EN}|{_LEAVE_ZH})"
_APPOINT = rf"(?:{_APPOINT_EN}|{_APPOINT_ZH})"
ACTION = re.compile(rf"(?<![A-Za-z])(?:{_JOIN_EN}|{_LEAVE_EN}|{_APPOINT_EN})(?![A-Za-z])|"
                    rf"{_JOIN_ZH}|{_LEAVE_ZH}|{_APPOINT_ZH}", re.I)
JOIN = re.compile(_JOIN, re.I)
LEAVE = re.compile(_LEAVE, re.I)
APPOINT = re.compile(_APPOINT, re.I)
HOLD = re.compile(
    r"\?|？|\b(?:denies|denied|denial|rumou?rs?|reportedly|might|may|could|expected to|"
    r"in talks|considering|set to|plans? to|not|never|false)\b|"
    r"否認|否认|傳聞|传闻|傳出|传出|據傳|据传|澄清|未離職|未离职|可能|有望|擬任|拟任|傳將|传将|尚未", re.I)
CLAUSE = re.compile(r"[。！？；;\n]|(?<=[a-z])\.\s+")
RELATED = re.compile(r"延伸閱讀|延伸阅读|相關文章|相关文章|read more|related articles", re.I)
_LATIN_NAME = r"[A-Z][a-z]+(?:[-'’][A-Z]?[a-z]+)?(?:[ \t]+(?:[A-Z]\.\s+)?[A-Z][a-z]+(?:[-'’][A-Z]?[a-z]+)?){1,2}"
LATIN_NAMES = re.compile(r"(?<![A-Za-z])(?=(" + _LATIN_NAME + r")(?![A-Za-z]))")
LATIN_FULL_NAME = re.compile(_LATIN_NAME)
_CJK_NAME = r"[王李張张劉刘陳陈楊杨趙赵黃黄周吳吴徐孫孙馬马朱胡郭林何高羅罗鄭郑梁謝谢宋唐許许韓韩鄧邓曹彭曾蕭萧葉叶方沈鍾钟杜蘇苏盧卢姜崔潘于袁蔡余蔣蒋賴赖魏任程田董丁][\u4e00-\u9fff]{1,2}"
CJK_NAMES = re.compile(r"(?:(?:[負负][責责]人|主管|總監|总监|總裁|总裁|創辦人|创办人|執行長|执行长|"
    r"執行官|执行官|工程師|工程师|任命|聘任|宣布)\s*|"
    r"(?<![\u4e00-\u9fff]))(" + _CJK_NAME + r")(?=\s*(?:現已|现已|正式|已|宣布|確定|确定|官宣|兼職|兼职)*\s*(?:"
    + _JOIN + "|" + _LEAVE + "|" + _APPOINT + r"|[，,、:]|$))")
_BRIDGE = r"(?:[\s,，:：—-]|\b(?:has|had|is|officially|will|to|now|then)\b|宣布|正式|現已|现已|已|剛|刚|閃電|闪电|確定|确定|官宣|兼職|兼职)*"
BRIDGE = re.compile(_BRIDGE, re.I)
FROM_EMPLOYER = re.compile(r"^\s*(?:從|从|自)\s*(?:" + ORGANIZATIONS.pattern + r")\s*$", re.I)
ANNOUNCED = re.compile(r"\b(?:announces?|announced|appoints?|appointed|hires?|hired)\b|宣布|任命|證實|证实", re.I)
ROLE_BRIDGE = re.compile(r"^\s*(?:,\s*|，\s*|\b(?:as|to|leads?|led|heads?|headed|oversees?|oversaw)\b|"
    r"[:：]|擔任|担任|出任|任職|任职|是|曾|原|現|现|負責|负责|主導|主导)", re.I)
ASSIGNED_ROLE = re.compile(r"^.{0,52}?(?P<role>\b(?:as|to lead|to head|to run)\b|擔任|担任|出任|負責|负责|主導|主导)", re.I)
NON_PERSON = re.compile(r"\b(?:AI|Lab|Code|Research|Team|Group|Systems|Department|Security|"
    r"Product|Officer|Counselor|United|States|New|Office|Workspace|Deputy|Vice|President|Director|"
    r"Chief|The|Army|Secretary|Senate|Head|Lead|Senior|Update|Industry|Works)\b", re.I)
CEO = re.compile(r"(?<![\w-])CEO\b|\bchief executive(?: officer)?\b|執行長|执行长|首席執行官|首席执行官", re.I)
BACKGROUND = re.compile(r"\b(?:after|since|amid|following)\b\s*$|(?:回應|回应|談|谈|因|解讀|解读)\s*$", re.I)
ATTRIBUTED_PREFIX = re.compile(r"\b(?:said|says|confirmed)\b|表示|指出", re.I)
TRANSITION_HEADLINE = re.compile(r"\b(?:announces?|announced)\s+(?:a\s+)?(?:CEO|leadership) transition\b|"
    r"(?:宣布|公告).{0,12}(?:人事異動|人事变动|執行長交接|执行长交接)", re.I)


@dataclass(frozen=True)
class Change:
    person: str
    impact: int
    transitions: frozenset[tuple[str, str]]
    ceo_departure: str | None = None


def _organizations(text):
    aliases = {"微軟": "microsoft", "微软": "microsoft", "microsoft ai": "microsoft",
               "輝達": "nvidia", "英伟达": "nvidia", "google deepmind": "deepmind",
               "meta ai": "meta", "thinking machines lab": "thinking machines"}
    for match in ORGANIZATIONS.finditer(text):
        name = re.sub(r"\s+", " ", match[0].lower())
        if name.startswith(("字節", "字节")):
            name = "bytedance"
        elif name.startswith(("騰訊", "腾讯")):
            name = "tencent"
        yield aliases.get(name, name)


def _names(clause):
    for match in LATIN_NAMES.finditer(clause):
        # In title case a capitalized action can look like the last name token.
        tokens = match[1].split()
        for length in range(min(3, len(tokens)), 1, -1):
            name = " ".join(tokens[:length])
            if (LATIN_FULL_NAME.fullmatch(name) and not NON_PERSON.search(name)
                    and not ORGANIZATIONS.search(name) and not name.endswith(("'s", "’s"))):
                end = match.start(1) + re.match(r"\S+(?:\s+\S+){" + str(length - 1) + "}", match[1]).end()
                yield name, match.start(1), end
    for match in CJK_NAMES.finditer(clause):
        yield match[1], match.start(1), match.end(1)


def _role_segment(text):
    """Stop a role description at a clause break or another named actor."""
    text = re.split(r"[,，;；]|\b(?:where|whose|while|according to)\b", text, maxsplit=1, flags=re.I)[0]
    first_other = next((start for _, start, end in _names(text) if
        re.match(r"\s*(?:said\b|says\b|confirmed\b|表示|指出)", text[end:], re.I)
        or list(_actions(text, start, end))), len(text))
    return text[:first_other]


def _actions(clause, start, end):
    for action in ACTION.finditer(clause):
        verb = action[0]
        before = clause[:action.start()]
        after = clause[action.end():]
        gap = clause[end:action.start()]
        from_employer = FROM_EMPLOYER.fullmatch(gap)
        if action.start() >= end and (BRIDGE.fullmatch(gap) or from_employer):
            direction = "leave" if LEAVE.fullmatch(verb) else "join"
            # A company that hired someone is the object, never the role of
            # the person whose name happened to precede the hiring verb.
            if direction == "join" and not (JOIN.fullmatch(verb) or verb in {"出任", "升任", "接任"}):
                continue
            if from_employer and direction != "leave":
                continue
            group = list(_organizations(gap if from_employer else re.split(
                r"[,，、]|\b(?:as|after|to take|to start|to join)\b", after, 1, flags=re.I)[0][:52]))
            if direction == "leave" and not group:
                role_after = re.match(r"^\s*as\s+([^,，;]{1,60})", after, re.I)
                earlier = re.split(r"[,，;；]", clause[max(0, start - 75):start])[-1]
                group = list(_organizations(role_after[1])) if role_after else []
                if not group and not ATTRIBUTED_PREFIX.search(earlier):
                    group = list(_organizations(earlier))
            if direction == "leave" and re.match(r"^\s*(?:後|后|calls?\b|petition\b)", after, re.I):
                continue
            yield direction, group[0] if group else "", action.end()
            if direction == "leave":
                moved = re.match(r"^(?:.*?)(?:即|隨即|随即|並|并|and)\s*(?:閃電|闪电|then)?\s*"
                                 r"(?:" + _JOIN + r")", after[:65], re.I)
                if moved and (destinations := list(_organizations(after[moved.end():moved.end() + 36]))):
                    yield "join", destinations[0], action.end() + moved.end()
        elif action.end() <= start and APPOINT.fullmatch(verb):
            gap = clause[action.end():start]
            # Permit an appointee's descriptive prefix, with no other actor/action.
            descriptive = re.fullmatch(r"\s*(?:(?:the )?(?:former|ex-)\s*[A-Za-z. -]{1,42}|"
                                       r"(?:前|原)[\u4e00-\u9fff]{1,12})?\s*", gap, re.I)
            employer = re.search(r"(?:" + ORGANIZATIONS.pattern + r")\s*(?:has\s+|宣布\s*)?$", before, re.I)
            if descriptive and employer:
                yield "join", next(_organizations(employer[0])), end


def detect(title: str, summary: str = "") -> Change | None:
    title = unicodedata.normalize("NFKC", RELATED.split(title, maxsplit=1)[0][:1600])
    index_headline = TRANSITION_HEADLINE.search(title)
    if (not ACTION.search(title) and not index_headline) or HOLD.search(title) or re.search(
            r"連署.{0,14}回任|联署.{0,14}回任|\b(?:petition|calls?)\b.{0,40}\breturn\b", title, re.I):
        return None
    summary = unicodedata.normalize("NFKC", RELATED.split(summary, maxsplit=1)[0][:1600])
    if re.search(r"\b(?:will|to)\s+(?:" + _JOIN + "|" + _LEAVE + r")\b|即將|即将|將加入|将加入",
                 title, re.I) and not ANNOUNCED.search(title):
        return None
    lead = CLAUSE.split(summary, maxsplit=1)[0] if index_headline else title
    headlines = [(clause, name, start, end) for clause in CLAUSE.split(lead)
                 for name, start, end in _names(clause)
                 if not BACKGROUND.search(clause[:start]) and list(_actions(clause, start, end))]
    headlines = [mention for mention in headlines if not any(
        other[0] == mention[0] and other[2] < mention[2] and other[3] == mention[3] for other in headlines)]
    if headlines and re.search(r"接任|繼任|继任|(?:出任|擔任|担任)臨時|\breplaces?\b|\bsucceeds?\b", title, re.I):
        # The incoming successor is context for the outgoing CEO's same
        # transition when the headline leads with the announced departure.
        first_clause, _, start, end = min(headlines, key=lambda m: (lead.index(m[0]), m[2]))
        if any(direction == "leave" and org for direction, org, _ in _actions(first_clause, start, end)):
            headlines = [(clause, name, a, b) for clause, name, a, b in headlines
                         if clause == first_clause and a == start and b == end]
    people = {name.casefold() for _, name, _, _ in headlines}
    if len(people) != 1:
        return None
    person = next(iter(people))
    clauses = headlines + [(clause, name, start, end) for clause in CLAUSE.split(summary)
                           for name, start, end in _names(clause) if name.casefold() == person]
    transitions, roles, organizations = set(), [], set()
    for clause, _, start, end in clauses:
        if HOLD.search(clause) and ACTION.search(clause):
            return None
        for direction, org, stop in _actions(clause, start, end):
            if org:
                transitions.add((direction, org))
                organizations.add(org)
            after = clause[stop:stop + 100].lstrip(" ,，")
            assignment = ASSIGNED_ROLE.search(_role_segment(after))
            if assignment:
                assigned = _role_segment(after[assignment.start("role"):])
                additional_ceo_role = re.match(r".{1,58}?[,，、]\s*(?:and\s+)?(" + CEO.pattern + r")",
                                               after[assignment.start("role"):], re.I)
                roles.append(assigned + (" " + additional_ceo_role[1] if additional_ceo_role else ""))
            elif direction == "leave":
                roles.append(_role_segment(re.split(r"、", after, maxsplit=1)[0]))
        prefix, suffix = clause[max(0, start - 72):start], clause[end:end + 100]
        # A role in another named person's clause cannot qualify this person.
        prefix = re.split(r"[,，;；]", prefix)[-1]
        if not ATTRIBUTED_PREFIX.search(prefix):
            roles.append(prefix)
            organizations.update(_organizations(prefix))
        if ROLE_BRIDGE.search(suffix):
            roles.append(_role_segment(suffix.lstrip(" ,，:：")))
    role = "\n".join(roles)
    if not (AI_DUTY.search(role) or organizations & AI_LABS
            or organizations & {"amd", "nvidia"} and TOP.search(role)):
        return None
    if TOP.search(role):
        impact = 30
    elif LEAD.search(role):
        impact = 20
    elif SENIOR.search(role):
        impact = 15
    else:
        return None
    departures = {org for direction, org in transitions if direction == "leave"}
    ceo_departure = next(iter(departures)) if (len(departures) == 1 and CEO.search(role)
        and not re.search(r"\bco[- ]CEO\b|聯席|联席|代理|臨時|临时|interim", role, re.I)) else None
    return Change(person, impact, frozenset(transitions), ceo_departure)
