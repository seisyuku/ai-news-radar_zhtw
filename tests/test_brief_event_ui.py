"""Exercise the shipped event-only UI boundary, cache, expiry and filters."""
import json
import pytest
from tests.js_bridge import extract_declarations, run_js


def harness():
    return extract_declarations('validBriefProjection', 'resolveBriefProjection',
        'currentStoryPools', 'briefEventMatchesFilters', 'storySourceCount',
        'formatStoryTime', 'storyDurationLabel', 'scheduleBriefExpiry',
        'sourceDisplayName', 'readerSiteName', 'readerSiteId') + r'''
const epoch=Date.parse('2026-10-22T12:00:00Z'); let now=epoch;
Date.now=()=>now;
const state={activeSection:'hot',query:'',siteFilter:'',sourceTypeFilter:'',authorFilter:'',signalLevelFilter:''};
function isUnsafeStory(){return false;}
function generalReaderSource(i){return {level:i.site_id};}
function isHighPriorityItem(i){return i.score>=.75;}
function isCuratedItem(i){return i.site_id==='official_ai';}
function itemMatchesSection(i,s){return i.section===s;}
let rendered=0, timer=null, statRenders=0;
function setStats(){statRenders+=1;}
function setTimeout(fn,delay){timer={fn,delay};return 1;}
function clearTimeout(){timer=null;}
function renderBriefPicks(){rendered++;}
function renderLlmRadar(){}
const id='be1_'+'1'.repeat(24), phase='bp1_'+'2'.repeat(24);
function event(){return {brief_event_id:id,story_id:id,identity:{key:'model-release'},
 member_article_ids:['a','b'],member_story_ids:['raw-a','raw-b'],
 primary_item:{id:'a',title:'Release',url:'https://example.com/a',site_id:'media'},
 sources:[{id:'a',url:'https://example.com/a',title:'Release',site_id:'media',role:'active_phase'},
 {id:'b',url:'https://example.com/b',title:'historic localized headline',site_id:'official_ai',role:'past_phase',section:'models'}],
 corroboration_count:1,eligible:true,effective_at:'2026-10-22T11:00:00Z',initial_effective_at:'2026-10-22T11:00:00Z',expires_at:'2026-10-23T11:00:00Z',
 title:'Release',url:'https://example.com/a',source:'Media',business_events:[],source_count:2,item_count:2,duplicate_count:1,score:.8,category:'model_release',importance_breakdown:{},initial_basis:'source_report',first_observed_at:'2026-10-22T11:00:00Z',last_material_at:null,last_reported_at:'2026-10-22T11:30:00Z',active_phase_id:phase,eligibility_reason:'in_window',match_evidence:[],unknown_update_article_ids:[],primary_url:'https://example.com/a',source_name:'Media',source_names:['Media'],items:[],importance:.8,importance_score:.8,importance_label:'high',reasons:[],earliest_at:'2026-10-22T11:00:00Z',latest_at:'2026-10-22T11:00:00Z'};}
function projection(){return {record_type:'brief_event_projection',schema_version:1,matcher_version:'brief-event-v1',generation_id:'bg1_'+'a'.repeat(24),generated_at:'2026-10-22T12:00:00Z',status:'ready',history_complete:false,state_revision:'b'.repeat(64),events:[event()],selected_event_ids:[id],diagnostics:{recovery_mode:'none',errors:[]}};}
'''


@pytest.mark.parametrize('mutation', [
    "p.schema_version=2", "p.status='unavailable'", "delete p.generation_id",
    "p.events.push(p.events[0])", "p.events[0].expires_at='2026-10-24T11:00:00Z'",
    "delete p.events[0].identity", "delete p.events[0].sources", "p.events[0].score=NaN",
    "p.events[0].corroboration_count=-1", "p.selected_event_ids=[id,id]",
    "p.selected_event_ids=['be1_'+'9'.repeat(24)]", "p.events[0].story_id='raw'",
    "p.events[0].effective_basis='reported_day_upper_bound'",
    "p.generated_at='2027-01-01T00:00:00Z'", "p.events[0].sources[0].role='legacy'",
    "delete p.diagnostics",
])
def test_invalid_projection_never_falls_back_to_raw(mutation):
    result=run_js(harness()+f'''const p=projection();{mutation};
state.storiesMerged={{brief_events:p,stories:[event(),event()]}};
state.dailyBrief={{items:[event()]}};
console.log(JSON.stringify({{valid:validBriefProjection(p),pool:currentStoryPools([]).merged.length}}));''')
    assert result == {'valid': False, 'pool': 0}


def test_legacy_projection_and_daily_cannot_restore_featured_cache_without_governance():
    result=run_js(harness()+'''
state.storiesMerged={brief_events:projection()};state.dailyBrief={items:[event(),event()]};
const first=currentStoryPools([]);state.storiesMerged={stories:[event()]};
const cached=currentStoryPools([]);now=Date.parse('2026-10-23T11:00:00Z');
const expired=currentStoryPools([]);console.log(JSON.stringify({first:first.merged.length,cached:cached.cached,count:cached.merged.length,expired:expired.merged.length,unavailable:expired.projection===null}));''')
    assert result == {'first':0,'cached':False,'count':0,'expired':0,'unavailable':True}


def test_legacy_past_reference_cannot_supply_a_homepage_search_match():
    result=run_js(harness()+'''
state.storiesMerged={brief_events:projection()};state.query='localized';state.siteFilter='official_ai';state.activeSection='models';
const full=currentStoryPools([]);state.signalLevelFilter='multi';const multi=currentStoryPools([]);
state.signalLevelFilter='';state.query='no-match';const absent=currentStoryPools([]);
console.log(JSON.stringify({full:full.merged.length,unique:full.brief.length+full.followup.length,multi:multi.merged.length,absent:absent.merged.length}));''')
    assert result == {'full':0,'unique':0,'multi':0,'absent':0}


def test_expiry_schedules_only_local_render_and_replaces_old_timer():
    result=run_js(harness()+'''
scheduleBriefExpiry(projection());const delay=timer.delay;timer.fn();
now=Date.parse('2026-10-23T11:00:00Z');scheduleBriefExpiry(projection());
console.log(JSON.stringify({delay,rendered,noTimer:timer===null,statRenders}));''')
    assert result == {'delay':23*3600000,'rendered':1,'noTimer':True,'statRenders':1}


@pytest.mark.parametrize(('basis','expected'), [('source_report','首次報導'),('first_observed','本系統初見'),('reported_day_upper_bound','報導日期 2026-10-21（時刻不明）')])
def test_event_time_does_not_use_repost_date_or_fermentation(basis, expected):
    result=run_js(harness()+f'''const e=event();e.effective_basis={json.dumps(basis)};e.effective_reported_day='2026-10-21';e.latest_at='2026-10-22T11:59:00Z';console.log(JSON.stringify(formatStoryTime(e)));''')
    assert result['latest']=='2026-10-22T11:00:00Z'
    assert result['rangeLabel']==expected
