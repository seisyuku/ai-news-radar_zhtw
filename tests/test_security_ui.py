"""Exercise the shipped topic filter and tag row against event membership."""
import pytest

from tests.js_bridge import extract_declarations, run_js


@pytest.mark.parametrize("mode", ["selected", "ai", "all"])
def test_topic_combines_with_mode_search_source_and_event_filters(mode):
    code = extract_declarations("getFilteredItems", "sectionItems", "itemMatchesBusinessEvent")
    result = run_js(code + r'''
const AiRadarSelection=require('./assets/selection.js');
const {itemMatchesSection}=AiRadarSelection;
const state={activeSection:'security',mode:MODE,query:'',siteFilter:'',sourceTypeFilter:'',signalLevelFilter:'',businessEventFilter:''};
const incident={id:'incident',title:'Codex vulnerability',security_topic:true,business_events:['security'],kind:'media'};
const research={id:'research',title:'AI security agent comparison',security_topic:true,business_events:[],kind:'official'};
const old={id:'old',title:'Codex vulnerability',business_events:['security'],kind:'media'};
const pools={selected:[incident,research],ai:[incident,research,old],all:[incident,research,old,{id:'other',title:'Chinese company funding'}]};
function modeItems(_section,mode){return pools[mode||state.mode];}
function generalReaderSource(i){return {level:i.kind};}
function multiSourceEventKeys(){return new Set();}
function itemMatchesSignalLevel(){return true;}
function sourceDisplayName(){return '';}
const initial=getFilteredItems().map(i=>i.id);
state.query='comparison'; const search=getFilteredItems().map(i=>i.id);
state.query='';state.siteFilter='official';const source=getFilteredItems().map(i=>i.id);
state.siteFilter='';state.businessEventFilter='security';const event=getFilteredItems().map(i=>i.id);
console.log(JSON.stringify({initial,search,source,event}));
'''.replace("MODE", repr(mode)))
    assert result == {"initial": ["incident", "research"], "search": ["research"], "source": ["research"], "event": ["incident"]}


def test_featured_filter_uses_member_topics_without_granting_event_eligibility():
    code = extract_declarations("briefEventMatchesFilters")
    result = run_js(code + r'''
const AiRadarSelection=require('./assets/selection.js');
const {itemMatchesSection}=AiRadarSelection;
const state={activeSection:'security',query:'',siteFilter:'',sourceTypeFilter:'',signalLevelFilter:'',businessEventFilter:''};
function generalReaderSource(){return {level:'media'};}
function sourceDisplayName(){return '';}
const ordinary={primary_item:{title:'Chinese company funding'},sources:[],business_events:[]};
const security={...ordinary,sources:[{title:'Codex vulnerability',security_topic:true}]};
const initial=[briefEventMatchesFilters(ordinary),briefEventMatchesFilters(security)];
state.businessEventFilter='security';
console.log(JSON.stringify({initial,event:briefEventMatchesFilters(security)}));
''')
    assert result == {"initial": [False, True], "event": False}


def test_security_label_shows_once_with_or_without_event_badge():
    code = extract_declarations("buildIntelTagRow", "TAG_SYNONYM_SUPPRESS", "BUSINESS_EVENT_LABELS")
    result = run_js(code + r'''
const document={createElement:()=>({children:[],appendChild(x){this.children.push(x);}})};
function rowBusinessEvents(row){return row.badged?[BUSINESS_EVENT_LABELS.security]:[];}
function itemTagLabels(){return ['資安','研究'];}
function businessEventChip(b){return b.label;}
function itemTagChip(s){return s;}
console.log(JSON.stringify([false,true].map(badged=>buildIntelTagRow({}, {badged}).children)));
''')
    assert result == [["資安", "研究"], ["資安", "研究"]]


def test_security_topic_remains_visible_when_other_content_tags_fill_the_card():
    code = extract_declarations("itemTagLabels")
    result = run_js(code + r'''
const {itemSections}=require('./assets/selection.js');
const state={activeSection:'hot'};
function rowSourceCount(){return 2;}
const item={title:'Codex model security research',site_id:'official_ai',security_topic:true};
console.log(JSON.stringify(itemTagLabels(item,{})));
''')
    assert result.count("資安") == 1
    assert len(result) <= 3
