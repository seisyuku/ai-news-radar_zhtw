"""Shared impact gate and time-aware ranking, independent of event labels."""
from datetime import timedelta
import json

import pytest

from scripts import supplement_impact as impact
from tests.js_bridge import run_js
from tests.test_publisher_governance import NOW, article
from tests.test_signal_selection import bundle


@pytest.mark.parametrize('hours', [0, 1, 6, 12, 24, 48])
def test_freshness_and_rank_match_browser(hours):
    effective = NOW - timedelta(hours=hours)
    for cls in ['core', 'supplement']:
        expected = impact.rank({'total':80}, cls, effective, NOW)
        code = "const G=require('./assets/publisher-governance.js'); console.log(JSON.stringify(G.rank({total:80}," + json.dumps(cls) + ',' + json.dumps(effective.isoformat()) + ',Date.parse(' + json.dumps(NOW.isoformat()) + '))));'
        assert run_js(code) == expected
    if hours not in (0,48):
        assert impact.freshness(hours) < 2 ** (-hours/48)
    if hours == 48:
        assert impact.freshness(hours) == .5


def test_core_only_gets_three_points_and_old_leader_can_be_overtaken():
    assert impact.rank({'total':80}, 'core', NOW, NOW) == round(83/103,4)
    assert impact.rank({'total':80}, 'supplement', NOW, NOW) == round(80/103,4)
    old = impact.rank({'total':90}, 'core', NOW-timedelta(hours=24), NOW)
    fresh = impact.rank({'total':80}, 'supplement', NOW-timedelta(hours=1), NOW)
    assert fresh > old


@pytest.mark.parametrize('title,summary,basis', [
    ('OpenAI-backed Holdings acquires HomeSecurityCo', 'The $15.3 billion deal plans to bring AI to the home security business.', 'supported_core'),
    ('OpenAI launches GPT-6.1 Sol', 'GPT-6.1 Sol is now available.', 'supported_core'),
    ('Cedar AI secures $800 million funding', 'The company closed the round and expands inference capacity for its enterprise customers.', 'industry_news'),
    ('Anthropic reports revenue concentration', 'One customer accounts for 34.5% of revenue.', 'supported_core'),
])
def test_material_axes_match_browser(title, summary, basis):
    native={'title':title,'summary':summary}
    result=impact.score(native,basis)
    js="const G=require('./assets/publisher-governance.js');console.log(JSON.stringify(G.impactScore("+json.dumps(native)+','+json.dumps(basis)+')));'
    assert run_js(js)==result
    if 'backed' in title:
        assert result['i']==15 and result['c']==10 and not result['passes']


def test_core_material_qualification_does_not_bypass_shared_impact_gate():
    parent,daily,_=bundle([article(summary='GPT-6.1 Sol is now available to developers.')])
    d=parent['publisher_governance']['events'][0]
    assert d['featured_eligible'] and d['selection_class']=='core'
    assert d['supplement_impact']['total']==65 and not d['supplement_impact']['passes']
    assert not daily['items']


def test_browser_view_does_not_reuse_old_importance_breakdown():
    parent,daily,_=bundle()
    event=parent['brief_events']['events'][0]
    decision=parent['publisher_governance']['events'][0]
    code="const G=require('./assets/publisher-governance.js');console.log(JSON.stringify(G.view("+json.dumps(event)+','+json.dumps(decision)+').importance_breakdown));'
    assert run_js(code)==daily['items'][0]['importance_breakdown']
    assert set(daily['items'][0]['importance_breakdown'])=={'impact','core_bonus','freshness'}


def test_real_browser_selector_and_producer_mix_high_impact_news_before_core():
    from tests.js_bridge import extract_declarations
    rows=[article(summary='The AI model adds tool calling and supports enterprise customers using longer context windows.'),
          article('funded',title='Cedar AI secures $800 million funding',
                  summary='Cedar AI closed the round and expands inference infrastructure for its enterprise customers.',
                  url='https://the-decoder.com/round',source='The Decoder AI News',site_id='curated_media')]
    parent,daily,_=bundle(rows)
    code=extract_declarations('dplusStories')+"const AiRadarGovernance=require('./assets/publisher-governance.js');const parent="+json.dumps(parent)+"; Date.now=()=>Date.parse(parent.generated_at); const state={storiesMerged:parent,generatedAt:parent.generated_at,latestGovernanceMeta:parent.publisher_governance}; const pool=AiRadarGovernance.resolve(state).projection.events;console.log(JSON.stringify(dplusStories(pool,'hot',10).map(x=>x.brief_event_id)));"
    assert [x['selection_class'] for x in daily['items']]==['supplement','core']
    assert run_js(code)==[x['brief_event_id'] for x in daily['items']]
