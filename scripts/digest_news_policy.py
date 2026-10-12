"""Lightweight private-digest policy; public scores and brief gate stay intact."""

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
import re

if __package__:
    from . import update_news as news
    from .digest_input import Diagnostic
    from .digest_selection import DigestSelection, SelectionSettings, validate_selection_inputs
else:
    import update_news as news
    from digest_input import Diagnostic
    from digest_selection import DigestSelection, SelectionSettings, validate_selection_inputs

POLICY = "daily-news-v2"

def rx(pattern):
    return re.compile(pattern, re.I)

NOISE = {
    'promotion': rx(r'\b(?:buy tickets|save.{0,30}(?:pass|ticket)|second pass|register now|early.bird|hours to.{0,35}disrupt)\b|購票|售票|早鳥|報名優惠'),
    'crypto_prediction': rx(r'\b(?:meme ?coin|memecoin|price prediction|coin.{0,35}to hit)\b|迷因幣|幣價預測'),
    'roundup': rx(r'\b(?:daily (?:news|digest|roundup)|weekly roundup|news roundup)\b|AI\s*早報|新聞彙整|每日新聞整理|一週回顧'),
    'generic_tutorial': rx(r'\b(?:\d+ ways to|how to (?:use|build|write)|prompt tips|best prompts)\b|[一二三四五六七八九十\d]+種方法|提示詞技巧|入門教學|QCon'),
    'generic_comparison': rx(r'\b(?:alternative[s]? 20\d\d|best.{0,30}tools of 20\d\d)\b|工具推薦清單'),
}
SIGNALS = {
    'release': rx(r'\b(?:released?|releases|launch(?:es|ed|ing)?|introduce[sd]?|ship[sp]?|public research preview|announc(?:es?|ed|ing).{0,50}(?:model|agent|API|product|tool|app|system|service|platform))\b|發布|釋出|推出|上線|開源|開放權重'),
    'cost_change': rx(r'\b(?:cheaper.{0,25}(?:tokens?|AI)|token prices.{0,25}fall|price (?:cut|increase)|(?:cuts?|reduces?|lowers?|raises?)(?:\s+\w+){0,4}\s+prices?|cost(?:s)?.{0,30}(?:more|less|climb|drop)|spending more compute)\b|降價|調漲|成本.{0,12}(?:增加|下降|倍)|價格.{0,12}(?:下跌|上漲)'),
    'observed_security': rx(r'\b(?:malware|vulnerability|data breach|exposed API keys|(?:used|spent).{0,35}API keys)\b|惡意程式|資安漏洞|資料外洩|駭客|暴露.{0,10}金鑰'),
    'research_result': rx(r'\b(?:study finds|research finds|data.{0,25}shows|paper introduces|benchmark.{0,30}found|caught.{0,15}(?:errors|%))\b|研究(?:發現|指)|基準測試|揪出.{0,10}(?:錯誤|%)|(?:訪談.{0,12}AI模擬)'),
    'market_action': rx(r'\b(?:acquisition|in talks to buy|funding round|raised.{0,30}(?:million|billion)|market share|quarterly revenue)\b|收購|併購|融資|市佔|財報|營收'),
    'usage_policy': rx(r'\b(?:caps? submissions|submission.{0,25}limit|rate limit.{0,25}(?:change|cut)|restrict(?:s|ed)? access)\b|限制.{0,15}(?:投稿|用量|存取)|推進法.{0,15}上路'),
    'employment_data': rx(r'\b(?:job postings.{0,40}(?:rise|rebound|increas)|job openings.{0,30}(?:rise|data))\b|職缺.{0,15}(?:回升|突破|增加)|徵才數據'),
    'workflow_access': rx(r'\b(?:websites.{0,30}(?:access|block)|run.{0,30}models locally|hardware requirements|latency.{0,20}(?:test|reduc))\b|網站.{0,15}放行|(?:部署|延遲).{0,15}(?:測試|降低|成本)'),
}
OUTCOME = rx(r'\b(?:cost.{0,30}(?:more|less|\d)|token prices.{0,25}fall|overstate.{0,15}results|(?:up to|reached|caught|reports|priced at).{0,45}\d|\d+(?:\.\d+)?\s*(?:percent|%|x more)|(?:caps submissions|submissions at two)|exposed API keys|malware|in talks to buy.{0,40}billion)\b|\d+(?:\.\d+)?\s*(?:%|倍|億度|萬)|駭客|惡意程式')
OPINION = rx(r'\b(?:execs think|we debate|we should assume|laid out his views|language diktat|attempt to rename|plans to rebrand)\b|將重塑')
PLACEHOLDER = rx(r'^(?:點選|點擊|点击|click).{0,12}(?:原文|閱讀|阅读|read|original).{0,3}$')

@dataclass(frozen=True)
class Decision:
    eligible: bool
    priority: int
    signals: tuple
    reason: str


def classify(candidate):
    title = str(candidate.get('title_original') or candidate.get('title') or '')
    raw = str(candidate.get('summary_original') or '')
    body = '' if PLACEHOLDER.fullmatch(raw.strip()) else raw
    text = title + '\n' + body
    for reason, pattern in NOISE.items():
        # Roundup/tutorial classification is headline-led; a new release may
        # mention a tutorial in its summary without becoming a tutorial.
        target = text if reason in {'promotion', 'crypto_prediction'} else title
        if pattern.search(target):
            return Decision(False, 0, (), reason)
    signals = tuple(name for name, pattern in SIGNALS.items() if pattern.search(text))
    if OPINION.search(text) and not signals:
        return Decision(False, 0, (), 'opinion_without_concrete_change')
    if not signals:
        return Decision(False, 0, (), 'no_concrete_information')
    # A concrete outcome is a ranking signal, never a factual verification.
    priority = 2 if OUTCOME.search(text) else 1
    return Decision(True, priority, signals, 'concrete_information')


def near_duplicate(a, b):
    ta, tb = news.normalized_story_title(a), news.normalized_story_title(b)
    if not news.title_is_mergeable(ta) or not news.title_is_mergeable(tb):
        return False
    sa, sb = news.title_tokens(ta), news.title_tokens(tb)
    if not sa or not sb or len(sa & sb) / len(sa | sb) < .4:
        return False
    return news.title_similarity(ta, tb) >= .86 and news.story_titles_can_merge(ta, tb)


def select_news_candidates(stage, candidates, *, limit=10, same_source_penalty=.03):
    stories, by_id, penalty = validate_selection_inputs(stage, candidates, limit, same_source_penalty)
    limit = min(limit, 10)
    decisions = {key: classify(candidate) for key, candidate in by_id.items()}
    remaining = [stories[key] for key in sorted(stories) if decisions[key].eligible]
    eligible_count = len(remaining)
    picked, counts = [], Counter()
    while remaining and len(picked) < limit:
        remaining.sort(key=lambda s: (
            -decisions[s['story_id']].priority,
            -(float(s.get('score') or 0) - penalty * counts[str(s.get('source') or '')]),
            str(s['story_id']),
        ))
        chosen = remaining.pop(0)
        if any(near_duplicate(chosen, other) for other in picked):
            continue
        picked.append(chosen)
        counts[str(chosen.get('source') or '')] += 1
    output = []
    for row in picked:
        key = row['story_id']
        candidate = deepcopy(by_id[key])
        decision = decisions[key]
        candidate['editorial_selection'] = {'level': 'Full', 'priority': decision.priority,
                                            'signals': list(decision.signals)}
        output.append(candidate)
    rejected = Counter(d.reason for d in decisions.values() if not d.eligible)
    diagnostics = [Diagnostic(code, count, 'digest_selection') for code, count in sorted(rejected.items())]
    if eligible_count > len(output):
        diagnostics.append(Diagnostic('diversity_or_limit', eligible_count-len(output), 'digest_selection'))
    return DigestSelection(tuple(output), len(stories), eligible_count,
                           SelectionSettings(limit, penalty, None, POLICY), tuple(diagnostics))


def clean_summary(candidate):
    summary = str(candidate.get('summary') or '').strip()
    if not summary or PLACEHOLDER.fullmatch(summary):
        return ''
    # Remove publisher self-links / repeated article-title footer only. No
    # new sentence, numerical conversion, fact or impact claim is generated.
    summary = re.split(r'(?:The (?:article|post)\b|這篇(?:部落格文章|文章)|這篇「|這個(?:文章|帖子)|本文(?:「|〈)|文章〈|「[^」]+」一文|「[^」]+」文章|「[^」]+」最初)', summary, maxsplit=1, flags=re.I)[0].strip()
    compact = lambda s: re.sub(r'[^\w\u4e00-\u9fff]', '', s).casefold()
    title = str(candidate.get('title') or '')
    if compact(summary) == compact(title):
        return ''
    return summary


def nature(candidate):
    text = str(candidate.get('title_original') or '') + '\n' + str(candidate.get('summary_original') or '')
    if rx(r'\bin talks\b|\breportedly\b|\bWSJ reports\b|據悉|磋商').search(text):
        return '據報／洽談中'
    if rx(r'\bclaims?\s+(?:that|top|a|an|the|its|it|to)\b|\bit reports\b').search(text):
        return '廠商聲稱'
    if rx(r'\btests? report\b').search(text):
        return '測試報導'
    return ''
