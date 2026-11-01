"""Global empty-only fallback must preserve qualification and primary priority."""
import json

import pytest

from scripts import brief_events, signal_selection as selection, supplement_impact as impact
from tests.js_bridge import run_js
from tests.test_publisher_governance import article
from tests.test_publisher_governance_ui import harness
from tests.test_signal_selection import bundle, schema_validator


def fallback_row(n=0):
    return article(f"fallback-{n}", title=f"Vendor{n} releases Tool{n}, an AI workflow platform",
        summary="The AI platform adds workflow automation using a new compiler and includes public documentation for customers.",
        url=f"https://the-decoder.com/fallback-{n}", source="The Decoder AI News", site_id="curated_media")


def primary_row(n=0):
    return article(f"primary-{n}", title=f"FundingFirm{n} AI raises $500 million funding",
        summary="The AI company closed the funding round and expands inference infrastructure for enterprise customers.",
        url=f"https://the-decoder.com/primary-{n}", source="The Decoder AI News", site_id="curated_media")


@pytest.mark.parametrize("main,fallback,expected,tier", [(3,2,3,"primary"), (1,3,1,"primary"), (0,3,2,"fallback"), (0,1,1,"fallback"), (0,0,0,None)])
def test_python_and_browser_select_the_same_global_tier(main, fallback, expected, tier):
    rows = [primary_row(i) for i in range(main)] + [fallback_row(i) for i in range(fallback)]
    parent, daily, _ = bundle(rows or [article()])
    schema_validator().validate(parent["publisher_governance"])
    assert len(daily["items"]) == expected
    assert all(item["selection_tier"] == tier for item in daily["items"])
    assert selection.validate(parent["publisher_governance"], parent["brief_events"])
    result = run_js(harness(parent, daily) + '''
      const resolved=G.resolve(state);
      console.log(JSON.stringify({valid:G.valid(parent),ids:G.selectIds(meta.events),
        visible:resolved.projection?.events.map(e=>e.selection_tier)}));''')
    assert result["valid"]
    assert result["ids"] == [item["brief_event_id"] for item in daily["items"]]
    assert set(result["visible"]) == ({tier} if tier else set())


@pytest.mark.parametrize("axes", [
    {"total":64,"e":20,"p":20,"passes":False},
    {"total":65,"e":10,"p":20,"passes":False},
    {"total":65,"e":20,"p":10,"passes":False},
])
def test_fallback_never_relaxes_material_or_event_requirements(axes):
    assert selection.selection_tier(axes) is None
    assert run_js("const G=require('./assets/publisher-governance.js');console.log(JSON.stringify(G.selectionTier("+json.dumps(axes)+")));") is None


def test_fallback_never_activates_from_missing_or_unavailable_data():
    parent, daily, _ = bundle([fallback_row()])
    result = run_js(harness(parent, daily) + '''
      const first=G.resolve(state);state.storiesMerged=null;
      const cached=G.resolve(state);state.storiesMerged={...parent,publisher_governance:{...meta,status:'unavailable'}};
      console.log(JSON.stringify({first:first.projection.events.length,cached:cached.projection.events.length,
        failed:G.resolve(state).projection}));''')
    assert result == {"first":1,"cached":0,"failed":None}


def test_fallback_expires_at_original_24_hour_boundary():
    parent, daily, _ = bundle([fallback_row()])
    result = run_js(harness(parent, daily) + '''
      const expires=Date.parse(parent.brief_events.events[0].expires_at);
      console.log(JSON.stringify({before:G.resolve(state,expires-1).projection.events.length,
        after:G.resolve(state,expires).projection.events.length}));''')
    assert result == {"before":1,"after":0}


@pytest.mark.parametrize("mutation", ["meta.selection_policy='impact-v2'", "meta.events[0].selection_tier='primary'", "daily.items[0].selection_tier='primary'"])
def test_old_policy_or_forged_tier_is_rejected(mutation):
    parent, daily, _ = bundle([fallback_row()])
    assert run_js(harness(parent,daily)+mutation+";console.log(JSON.stringify(G.resolve(state).projection===null));")


def test_new_primary_replaces_fallback_without_changing_event_clocks():
    first, _, result = bundle([fallback_row()])
    second, daily, _ = bundle([fallback_row(), primary_row()], previous=brief_events.StateInput("valid", result.next_state))
    assert [item["selection_tier"] for item in daily["items"]] == ["primary"]
    before=first["brief_events"]["events"][0]
    after=next(e for e in second["brief_events"]["events"] if e["brief_event_id"]==before["brief_event_id"])
    assert (after["effective_at"],after["expires_at"]) == (before["effective_at"],before["expires_at"])


@pytest.mark.parametrize("title,expected", [
    ("Meet Factory Droid 1.0: A Model-Independent Coding Agent Harness",20),
    ("Factory releases Droid 1.0 coding agent",20),
    ("A factory deploys an AI model for manufacturing",10),
    ("Factory Droid deploys an AI model in a bank",10),
])
def test_factory_brand_fix_preserves_real_industrial_deployments(title,expected):
    native={"title":title,"summary":"The AI model adds tools using a new compiler and includes documentation for enterprise customers."}
    score=impact.score(native,"supported_core")
    assert score["c"]==expected
    assert run_js("const G=require('./assets/publisher-governance.js');console.log(JSON.stringify(G.impactScore("+json.dumps(native)+",'supported_core')));")==score
