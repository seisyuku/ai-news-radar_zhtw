"""Reader-facing six-event filter and ordinary news-card behavior."""

import re
from pathlib import Path

from tests.js_bridge import extract_declarations, run_js


def test_advanced_select_matches_the_existing_six_event_codes():
    html = Path("index.html").read_text(encoding="utf-8")
    match = re.search(r'<select id="businessEventSelect"[^>]*>(.*?)</select>', html, re.S)
    assert match is not None
    assert re.findall(r'<option value="([^"]*)"', match.group(1)) == [
        "", "earnings", "market", "security", "pricing", "benchmark", "model_release",
    ]
    labels = run_js(extract_declarations("BUSINESS_EVENT_LABELS", "businessEventBadges") + """
console.log(JSON.stringify(businessEventBadges(['earnings','market','security','pricing','benchmark','model_release'])
  .map(x=>x.label)));
""")
    assert labels == ["財報", "市佔", "資安", "價格", "評測", "模型發布"]
    assert html.index('id="businessEventSelect"') > html.index('<details class="advanced-panel">')


def test_event_filter_intersects_existing_list_filters_and_unknowns_do_not_match():
    code = extract_declarations("itemMatchesBusinessEvent", "getFilteredItems")
    result = run_js(code + """
const state={mode:'ai',activeSection:'hot',query:'',siteFilter:'',authorFilter:'',
 sourceTypeFilter:'',signalLevelFilter:'',businessEventFilter:'security'};
const items=[
 {id:'a',title:'Alpha',business_events:['security','pricing'],source:'One'},
 {id:'b',title:'Beta',business_events:['pricing'],source:'Two'},
 {id:'c',title:'Gamma',source:'Three'},
];
const modeItems=()=>items,sectionItems=x=>x,multiSourceEventKeys=()=>new Set();
const itemMatchesSignalLevel=()=>true,sourceDisplayName=x=>x.source;
const generalReaderSource=x=>({level:x.source==='One'?'official':'media'});
const security=getFilteredItems().map(x=>x.id);
state.query='alpha';const search=getFilteredItems().map(x=>x.id);
state.query='';state.siteFilter='media';const source=getFilteredItems().map(x=>x.id);
state.siteFilter='';state.businessEventFilter='pricing';const pricing=getFilteredItems().map(x=>x.id);
state.businessEventFilter='';const all=getFilteredItems().map(x=>x.id);
console.log(JSON.stringify({security,search,source,pricing,all}));
""")
    assert result == {"security": ["a"], "search": ["a"], "source": [],
                      "pricing": ["a", "b"], "all": ["a", "b", "c"]}


def test_event_filter_keeps_featured_cards_consistent_with_list():
    result = run_js(extract_declarations("briefEventMatchesFilters") + """
const state={signalLevelFilter:'',businessEventFilter:'benchmark',query:'',
 activeSection:'hot',siteFilter:'',authorFilter:'',sourceTypeFilter:''};
const generalReaderSource=()=>({level:'media'}),sourceDisplayName=()=>'';
const itemMatchesSection=()=>true,isCuratedItem=()=>true,storySourceCount=()=>1;
const isHighPriorityItem=()=>true;
const base={primary_item:{title:'Alpha',business_events:[]},sources:[]};
console.log(JSON.stringify({story:briefEventMatchesFilters({...base,business_events:['benchmark']}),
 primary:briefEventMatchesFilters({...base,primary_item:{title:'Alpha',business_events:['benchmark']}}),
 absent:briefEventMatchesFilters(base)}));
""")
    assert result == {"story": True, "primary": True, "absent": False}


def test_ordinary_card_shows_event_badge_without_repeated_model_tag_and_keeps_link():
    code = extract_declarations("BUSINESS_EVENT_LABELS", "TAG_SYNONYM_SUPPRESS",
                                "businessEventBadges", "businessEventChip")
    source = Path("assets/app.js").read_text(encoding="utf-8")
    start = source.index("function renderItemNode(")
    code += "\n" + source[start:source.index("\nconst SOURCE_ITEM_INITIAL_LIMIT", start)]
    result = run_js(code + """
class Element {
  constructor(cls='') {this.className=cls;this.children=[];this.textContent='';this.hidden=false;this.classList={add:()=>{}};}
  appendChild(el) {this.children.push(el);el.parent=this;return el;}
  insertBefore(el,ref) {const i=this.children.indexOf(ref);this.children.splice(i<0?this.children.length:i,0,el);el.parent=this;return el;}
  insertAdjacentElement(where,el) {const p=this.parent;const i=p.children.indexOf(this);p.children.splice(i+1,0,el);el.parent=p;}
  querySelector(selector) {return this.parts[selector];}
}
function card() {
 const root=new Element('news-card');root.parts={};
 for (const name of ['meta-row','site','category','source','time','card-actions','title','news-summary']) root.parts['.'+name]=new Element(name);
 const meta=root.parts['.meta-row'];
 for (const name of ['site','category','source']) meta.appendChild(root.parts['.'+name]);
 return root;
}
const document={createElement:()=>new Element()};
const itemTpl={content:{firstElementChild:{cloneNode:()=>card()}}};
const READER_SOURCE_LEVELS={media:{label:'媒體',tone:'media'}};
const generalReaderSource=()=>({publisher:'Example',level:'media'});
const sourceKind=()=>({label:'媒體',tone:'media'}),readerSiteId=()=>'';
const scorePercent=()=>80,itemLabelTone=()=>'',labelText=()=> 'AI';
const sourceSignal=()=> 'Example',sourceSignalTone=()=>'',setSourceBadge=(el,label)=>{el.textContent=label};
const itemTagLabels=()=>['模型','開發者'];
const itemTagChip=label=>{const el=new Element('signal-tag');el.textContent=label;return el};
const fmtTime=()=> '10:00',buildCopyNewsUrlButton=()=>null;
const itemTitleText=x=>x.title,itemOriginalTitleText=()=>'',feedSummaryText=()=> '摘要';
const node=renderItemNode({title:'測試消息',url:'https://example.com/story',
 published_at:'2026-10-25T02:00:00Z',business_events:['model_release','benchmark']});
const meta=node.querySelector('.meta-row').children;
console.log(JSON.stringify({tags:meta.filter(x=>x.className.startsWith('signal-tag')).map(x=>x.textContent),
 source:node.querySelector('.source').textContent,time:node.querySelector('.time').textContent,
 link:node.querySelector('.card-actions').children[0].href,
 linkText:node.querySelector('.card-actions').children[0].textContent}));
""")
    assert result == {"tags": ["模型發布", "評測", "開發者"], "source": "Example",
                      "time": "發布 10:00", "link": "https://example.com/story", "linkText": "檢視原文 ↗"}
