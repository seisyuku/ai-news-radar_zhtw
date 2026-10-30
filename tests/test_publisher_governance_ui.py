"""The shipped browser guard rejects missing/mixed/expired qualification data."""
import copy
import json

import pytest

from tests.js_bridge import run_js, extract_declarations
from tests.test_publisher_governance import article, mutate as mutate_legacy, CROSS_CASES, NOW
from scripts import update_news as u, brief_events as b

def ready_bundle():
    rows = [article(summary="The AI model adds tool calling and supports enterprise customers using longer context windows."), article("b", url="https://cnbc.com/synthetic", source="CNBC Technology", site_id="curated_media")]
    story = u.build_story_record("synthetic-story", rows, NOW, 24)
    story["news_summary"] = "Synthetic summary bound to the original primary."
    result = u.build_brief_event_payloads([story], rows, b.StateInput("missing"), NOW, 24,
        archive_meta=b.ArchiveMeta("valid", u.iso(NOW)))
    parent, daily = {"generated_at": u.iso(NOW)}, {"generated_at": u.iso(NOW)}
    u.apply_brief_event_result(result, daily, parent)
    return parent, daily, result, rows


def mutate(parent, name):
    mutate_legacy(parent, name)
    # Keep pg2 so these cases exercise actual relationships, not version rejection.
    parent["publisher_governance"]["generation_id"] = "pg2_" + "a" * 24


def harness(parent=None, daily=None):
    if parent is None: parent, daily, *_ = ready_bundle()
    return f'''
const G=require('./assets/publisher-governance.js');
let now=Date.parse({json.dumps(parent["generated_at"])}); Date.now=()=>now;
const parent={json.dumps(parent, ensure_ascii=False)},daily={json.dumps(daily, ensure_ascii=False)};
const meta=parent.publisher_governance;
const state={{storiesMerged:parent,dailyBrief:daily,generatedAt:parent.generated_at,latestGovernanceMeta:daily?.publisher_governance_meta}};
'''


def test_real_backend_overlay_is_accepted_and_only_qualified_views_are_exposed():
    result = run_js(harness() + '''
const r=G.resolve(state);console.log(JSON.stringify({valid:G.valid(parent),count:r.projection?.events.length,
 current:r.projection?.events.every(e=>e.publisher_qualified),summary:r.projection?.events[0].news_summary}));
''')
    assert result == {'valid': True, 'count': 1, 'current': True, 'summary': 'Synthetic summary bound to the original primary.'}


@pytest.mark.parametrize('name', CROSS_CASES)
def test_browser_rejects_all_frozen_cross_field_relationship_failures(name):
    parent, daily, *_ = ready_bundle()
    if name != 'projection_over_8mib': mutate(parent, name)
    extra = "parent.publisher_governance.diagnostics.errors=['x'.repeat(8388608)];" if name == 'projection_over_8mib' else ''
    result = run_js(harness(parent, daily) + extra + '''
console.log(JSON.stringify({valid:G.valid(parent),empty:G.resolve(state).projection===null}));
''')
    assert result == {'valid': False, 'empty': True}


def test_old_data_never_falls_back_to_raw_events_or_daily_badges():
    result = run_js(harness() + '''
delete parent.publisher_governance;state.latestGovernanceMeta=null;
console.log(JSON.stringify({empty:G.resolve(state).projection===null}));
''')
    assert result == {'empty': True}


def test_same_page_cache_is_same_revision_and_excludes_expired_events():
    result = run_js(harness() + '''
const first=G.resolve(state);state.storiesMerged=null;
const cached=G.resolve(state);now=Date.parse(parent.brief_events.events[0].expires_at);
const expired=G.resolve(state);
console.log(JSON.stringify({first:first.projection.events.length,cached:cached.cached,count:cached.projection.events.length,
 expired:expired.projection?.events.length||0}));
''')
    assert result == {'first': 1, 'cached': True, 'count': 1, 'expired': 0}


@pytest.mark.parametrize('signal', ['revision', 'unavailable', 'missing_annotation', 'mixed_daily', 'mixed_radar', 'mixed_all', 'older_generation'])
def test_new_or_invalid_policy_signal_invalidates_previous_cache(signal):
    changes = {
        'revision': "state.latestGovernanceMeta={...state.latestGovernanceMeta,registry_revision:'f'.repeat(64)};state.storiesMerged=null;",
        'unavailable': "parent.publisher_governance.status='unavailable';",
        'missing_annotation': "parent.publisher_governance.articles=[];",
        'mixed_daily': "state.dailyBrief={...daily,publisher_governance_meta:{...daily.publisher_governance_meta,brief_generation_id:'bg1_'+'0'.repeat(24)}};",
        'mixed_radar': "state.llmRadarGovernanceMeta={...state.latestGovernanceMeta,registry_revision:'f'.repeat(64)};",
        'mixed_all': "state.allGovernanceMeta={...state.latestGovernanceMeta,registry_revision:'f'.repeat(64)};",
        'older_generation': "state.latestGovernanceMeta={...state.latestGovernanceMeta,generated_at:'2026-10-23T04:35:27Z'};",
    }
    result = run_js(harness() + f'''G.resolve(state);{changes[signal]}
console.log(JSON.stringify({{empty:G.resolve(state).projection===null,cacheCleared:state.publisherGovernanceCache===null}}));''')
    assert result == {'empty': True, 'cacheCleared': True}


def test_same_timestamp_conflicting_revision_cannot_be_overwritten_on_the_same_page():
    result = run_js(harness() + '''
G.resolve(state);state.llmRadarGovernanceMeta={...state.latestGovernanceMeta,registry_revision:'f'.repeat(64)};
G.resolve(state);delete state.llmRadarGovernanceMeta;
console.log(JSON.stringify({stillBlocked:G.resolve(state).projection===null}));
''')
    assert result == {'stillBlocked': True}


@pytest.mark.parametrize('mutation', ["state.dailyBrief.items[0].title='wrong article';", "state.dailyBrief.selection_diagnostics.selected_count=99;", "state.dailyBrief.items[0].news_summary='wrong summary';"])
def test_daily_body_and_diagnostics_must_match_its_qualification_metadata(mutation):
    result = run_js(harness() + mutation + '''console.log(JSON.stringify({empty:G.resolve(state).projection===null}));''')
    assert result == {'empty': True}


def test_unqualified_reference_cannot_supply_search_filter_or_source_diversity_seat():
    # A validated view only carries qualified support into the shipped filters.
    code = extract_declarations('briefEventMatchesFilters','storyCandidateSiteId','storySourceCount','sourceDisplayName','readerSiteName','readerSiteId')
    result = run_js(harness() + code + '''
function generalReaderSource(i){return {level:i.site_id};}
function isHighPriorityItem(){return true;}function isCuratedItem(){return true;}function itemMatchesSection(){return true;}
state.activeSection='hot';state.query='only-unreviewed-text';state.siteFilter='';state.authorFilter='';state.sourceTypeFilter='';state.signalLevelFilter='';
const e=G.resolve(state).projection.events[0];e.all_sources.push({id:'unreviewed',title:'only-unreviewed-text'});
console.log(JSON.stringify({matches:briefEventMatchesFilters(e),key:storyCandidateSiteId(e),qualifiedSources:e.sources.length}));
''')
    assert result['matches'] is False
    assert result['key'].startswith('publisher:') and result['qualifiedSources'] == 2


def test_radar_requires_matching_policy_generation_and_local_expiry():
    result = run_js(harness() + '''
const e={...parent.brief_events.events[0].primary_item,effective_at:'2026-10-23T03:00:00Z',
 qualification:parent.publisher_governance.articles[0].qualification};
const good=G.radarEvents([e],daily.publisher_governance_meta,state).length;
const bad=G.radarEvents([e],{...daily.publisher_governance_meta,registry_revision:'f'.repeat(64)},state).length;
now=Date.parse(e.effective_at)+86400000;
console.log(JSON.stringify({good,bad,expired:G.radarEvents([e],daily.publisher_governance_meta,state).length}));
''')
    assert result == {'good': 1, 'bad': 0, 'expired': 0}


def test_all_mode_loader_carries_policy_revision_without_adding_a_request():
    result = run_js('''
(async()=>{const loader=require('./assets/loader.js');let calls=0;const state={allDataUrl:'data/latest-24h-all.json',itemsAi:[]};
 const api=loader.createLoader({state,fetchImpl:async()=>{calls++;return {ok:true,json:async()=>({items_all:[],publisher_governance_meta:{registry_revision:'new-revision'}})};}});
 await api.loadAllModeData();await api.loadAllModeData();console.log(JSON.stringify({calls,revision:state.allGovernanceMeta.registry_revision}));})();
''')
    assert result == {'calls': 1, 'revision': 'new-revision'}
