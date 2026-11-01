import json

from tests.js_bridge import extract_declarations, run_js
from tests.test_empty_fallback import fallback_row, primary_row
from tests.test_signal_selection import bundle
from tests.test_publisher_governance_ui import harness


def test_filtered_empty_primary_pool_cannot_reveal_fallback():
    parent,daily,_=bundle([primary_row(),fallback_row()])
    code=extract_declarations("dplusStories")+harness(parent,daily)+'''
      const AiRadarGovernance=G;
      const resolved=G.resolve(state).projection.events;
      const filtered=resolved.filter(e=>e.primary_item.id.startsWith('fallback-'));
      console.log(JSON.stringify({global:resolved.map(e=>e.selection_tier),filtered:dplusStories(filtered,'hot',20)}));'''
    assert run_js(code)=={"global":["primary"],"filtered":[]}


def test_actual_reader_selector_caps_fallback_in_both_sort_modes():
    parent,daily,_=bundle([fallback_row(i) for i in range(4)])
    code=extract_declarations("dplusStories")+harness(parent,daily)+'''
      const AiRadarGovernance=G;
      const storyTimeMs=s=>Date.parse(s.effective_at);
      const pool=G.resolve(state).projection.events;
      console.log(JSON.stringify({hot:dplusStories(pool,'hot',20).map(e=>e.brief_event_id),
        timeline:dplusStories(pool,'timeline',20).map(e=>e.brief_event_id)}));'''
    expected=[item["brief_event_id"] for item in daily["items"]]
    assert run_js(code)=={"hot":expected,"timeline":expected}


def test_actual_reader_renders_an_explicit_fallback_badge():
    code=extract_declarations("appendSignalLabels")+'''
      const document={createElement:()=>({})}, labels=[];
      appendSignalLabels({appendChild:chip=>labels.push(chip.textContent)},
        {selection_class:'supplement',selection_tier:'fallback',disclosure_flags:[]});
      console.log(JSON.stringify(labels));'''
    assert run_js(code)==["候補","產業動態"]
