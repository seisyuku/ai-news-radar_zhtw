"""D+ reader contract: complete candidates, source evidence and bounded fill."""
import json

import pytest

from tests.js_bridge import extract_declarations, run_js
from tests.test_signal_selection import bundle, USER_CASES
from tests.test_publisher_governance_ui import harness


def test_primary_score_tie_uses_python_id_order_instead_of_browser_locale():
    from tests.test_publisher_governance import article
    parent, daily, _ = bundle([article("B", url="https://openai.com/B"), article("a", url="https://openai.com/a")])
    assert parent["publisher_governance"]["events"][0]["featured_primary_article_id"] == "B"
    assert run_js(harness(parent, daily) + "console.log(JSON.stringify({valid:G.valid(parent)}));") == {"valid": True}


@pytest.mark.parametrize("case", USER_CASES["cases"], ids=lambda c: c["case_id"])
def test_user_cases_survive_browser_guard_with_exact_class_and_flags(case):
    from scripts.brief_events import parse
    parent, daily, _ = bundle([case["record"]], now=parse(USER_CASES["asof"]))
    expected = daily["items"][0]
    result = run_js(harness(parent, daily) + """
const r=G.resolve(state), e=r.projection?.events[0];
console.log(JSON.stringify({valid:G.valid(parent),cls:e?.selection_class,
 flags:e?.disclosure_flags,badges:e?.business_events}));
""")
    assert result == {"valid": True, "cls": expected["selection_class"],
        "flags": expected["disclosure_flags"], "badges": expected["business_events"]}


@pytest.mark.parametrize("change", [
    "d.selection_class='supplement'", "d.eligibility_basis='qualified_score'",
    "d.disclosure_flags=['provider_claim']", "d.support_scores[0].score='0.8'",
    "d.support_scores[0].score=-1", "d.support_scores[0].score=2",
    "d.support_scores=[]", "d.featured_business_events=[]",
    "d.featured_score=0", "d.support_article_ids.pop()",
    "d.featured_primary_item.corroboration_key='publisher:invented'",
    "d.featured_primary_item.source='borrowed-source'",
    "d.featured_primary_item.source_links=['https://unrelated.example/a']",
    "g.selection_policy='other'", "g.default_visible_limit=6",
    "g.articles[0].supplement_evidence.kind='industry_news'",
    "g.articles[0].qualification.core_evidence[0].urls=['https://unrelated.example/a']",
    "g.articles[0].source_policy.source_tier_rank='1'",
    "parent.brief_events.events[0].sources.forEach(r=>r.corroboration_key='publisher:invented')",
])
def test_v2_relationship_failures_reject_even_with_matching_version(change):
    result = run_js(harness() + f"""
const g=parent.publisher_governance,d=g.events[0]; {change};
console.log(JSON.stringify({{valid:G.valid(parent),empty:G.resolve(state).projection===null}}));
""")
    assert result == {"valid": False, "empty": True}


@pytest.mark.parametrize("change", [
    "d.disclosure_flags=[]", "d.disclosure_flags=['provider_claim']",
    "d.featured_business_events=['model_release']", "d.selection_class='core'",
    "a.supplement_evidence.spans[0].text='invented'",
    "a.supplement_evidence.qualifiers=[]", "a.supplement_evidence.qualifiers=['unreleased']",
    "a.supplement_evidence.urls=['https://unrelated.example/a']",
    "a.supplement_evidence.kind='industry_news'",
    "parent.brief_events.events[0].identity.action='model_release'",
])
def test_disclosure_cannot_lose_qualifiers_borrow_material_or_become_core(change):
    from scripts.brief_events import parse
    case = next(c for c in USER_CASES["cases"] if c["case_id"] == "unreleased_disclosure")
    parent, daily, _ = bundle([case["record"]], now=parse(USER_CASES["asof"]))
    result = run_js(harness(parent, daily) + f"""
const g=parent.publisher_governance,d=g.events[0],a=g.articles[0]; {change};
console.log(JSON.stringify({{valid:G.valid(parent)}}));
""")
    assert result == {"valid": False}


@pytest.mark.parametrize("change", [
    "state.latestGovernanceMeta={...state.latestGovernanceMeta,selection_policy:'other'}",
    "state.dailyBrief.items[0].selection_class='supplement'",
    "state.dailyBrief.items[0].disclosure_flags=['provider_claim']",
    "state.dailyBrief.selection_diagnostics.core_count=0",
    "state.dailyBrief.selection_diagnostics.supplement_candidate_count=1",
    "state.dailyBrief.selection_diagnostics.score_gate=.72",
    "state.dailyBrief.selection_diagnostics.default_visible_limit=6",
])
def test_new_daily_and_metadata_fields_are_bound_to_same_projection(change):
    result = run_js(harness() + change + ";console.log(JSON.stringify({empty:G.resolve(state).projection===null}));")
    assert result == {"empty": True}


def selector_harness():
    return extract_declarations("dplusStories", "storyRowsForPool", "storyCandidateCounts") + """
const state={briefView:'hot'}, BRIEF_HOT_LIMIT=10, BRIEF_TIMELINE_LIMIT=20;
const applyFeaturedSourceDiversityCap=x=>x;
const briefStorySortCompare=(a,b)=>b.score-a.score;
const storyTimeMs=s=>s.time;
const storyToBriefRow=story=>({story});
function rows(nCore,nSupplement){return [...Array.from({length:nCore},(_,i)=>
 ({brief_event_id:'c'+i,selection_class:'core',score:i/100,time:i})),
 ...Array.from({length:nSupplement},(_,i)=>({brief_event_id:'s'+i,
 selection_class:'supplement',score:1-i/100,time:100-i}))];}
"""


@pytest.mark.parametrize("core,sup,expected", [(0,0,0),(0,8,5),(1,8,5),(4,8,5),(5,8,5),(12,8,12),(22,8,20)])
def test_view_eligibility_core_precedence_and_bounded_supplement(core, sup, expected):
    result = run_js(selector_harness() + f"""
const input=rows({core},{sup});
const hot=dplusStories(input,'hot',10),timeline=dplusStories(input,'timeline',20);
console.log(JSON.stringify({{hot:hot.length,timeline:timeline.length,
 hotCore:hot.filter(s=>s.selection_class==='core').length,
 timelineCore:timeline.filter(s=>s.selection_class==='core').length,
 coreFirst:[hot,timeline].every(xs=>!xs.some((s,i)=>s.selection_class==='core'&&xs.slice(0,i).some(x=>x.selection_class==='supplement')))}}));
""")
    assert result == {"hot": min(10, expected), "timeline": expected,
        "hotCore": min(core,10), "timelineCore": min(core,20), "coreFirst": True}


def test_filtering_reselects_from_full_pool_not_default_five_and_modes_do_not_gate_upper():
    code = extract_declarations("currentStoryPools", "briefEventMatchesFilters")
    result = run_js(selector_harness() + code + """
Object.assign(state,{activeSection:'hot',mode:'selected',signalLevelFilter:'',query:'needle',siteFilter:'',authorFilter:'',sourceTypeFilter:''});
const pool=rows(2,9).map((s,i)=>({...s,eligible:true,effective_at:'2026-10-23T00:00:00Z',expires_at:'2026-10-24T00:00:00Z',
 primary_item:{title:i>=7?'needle':'other'},sources:[]}));
Date.now=()=>Date.parse('2026-10-23T12:00:00Z');
const resolveBriefProjection=()=>({projection:{events:pool,selected_event_ids:pool.slice(0,5).map(s=>s.brief_event_id)}});
const isUnsafeStory=()=>false, generalReaderSource=()=>({level:'media'}),sourceDisplayName=()=>'';
const selected=storyRowsForPool(currentStoryPools().merged).map(r=>r.story.brief_event_id);
state.mode='ai';const ai=storyRowsForPool(currentStoryPools().merged).map(r=>r.story.brief_event_id);
console.log(JSON.stringify({selected,ai}));
""")
    assert result["selected"] == result["ai"] == ["s5","s6","s7","s8"]


@pytest.mark.parametrize("mode", ["selected", "ai", "all"])
def test_clear_resets_filters_without_changing_mode_or_raw_dedupe(mode):
    result = run_js(extract_declarations("clearAllFilters", "activeAdjustmentCount") + f"""
const state={{mode:{json.dumps(mode)},allDedup:false,query:'x',activeSection:'models',siteFilter:'media',authorFilter:'x',sourceTypeFilter:'media',signalLevelFilter:'multi'}};
const searchInputEl={{}},siteSelectEl={{}},sourceTypeSelectEl={{}},signalLevelSelectEl={{}};
function rerenderCurrentView(){{}}
clearAllFilters();console.log(JSON.stringify({{mode:state.mode,dedup:state.allDedup,filters:activeAdjustmentCount()}}));
""")
    assert result == {"mode": mode,"dedup":False,"filters":0}


def test_signal_labels_are_explicit_and_do_not_invent_a_release_badge():
    from tests.test_story_source_badges_ui import harness as cards
    result = run_js(cards() + """
const card=buildStoryCard({selection_class:'supplement',disclosure_flags:['provider_claim','unreleased']},1);
console.log(JSON.stringify({labels:find(card,'signal-qualifier').map(x=>x.textContent),badges:find(card,'signal-tag').length}));
""")
    assert result == {"labels":["產業動態","廠商宣稱","未發布"],"badges":0}
