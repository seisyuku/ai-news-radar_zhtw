"""Source badges count publishers, while source records retain article history."""
from tests.js_bridge import extract_declarations, run_js


def harness():
    return extract_declarations(
        'storySourceRefs', 'storySourceCount', 'storySourceCountLabel', 'buildStoryCard', 'sourceChip',
        'sourceDisplayName', 'readerSiteName', 'readerSiteId',
    ) + r'''
class Element {
  constructor() { this.children=[]; this.dataset={}; this.textContent=''; }
  append(...nodes) { this.children.push(...nodes); }
  appendChild(node) { this.children.push(node); }
  setAttribute() {}
}
const document={createElement:()=>new Element()};
const state={briefView:'hot'};
function sourceKind(site) { return {tone:site==='official_ai'?'official':'media'}; }
function formatStoryTime() { return {latest:'2026-10-23T00:00:00Z'}; }
function fmtTime() { return '08:00'; }
function storyBusinessEvents() { return []; }
function storySortScore() { return 0; }
function storyPrimaryTitleText() { return 'Test event'; }
function storyPrimaryEnText() { return ''; }
function storyNewsSummaryText() { return ''; }
function find(node,cls) {
  return [node,...node.children.flatMap(child=>find(child,cls))]
    .filter(child=>String(child.className||'').split(' ').includes(cls));
}
function source(label,key,extra={}) {
  return {source:label,corroboration_key:key,site_id:'curated_media',...extra};
}
function cardResult(story) {
  const before=JSON.stringify(story),card=buildStoryCard(story,7);
  return {labels:find(card,'story-source-chip').map(c=>c.children[1].textContent),
    more:find(card,'story-source-more').map(c=>c.textContent),
    count:find(card,'story-count')[0].textContent,
    href:card.href,unchanged:JSON.stringify(story)===before};
}
'''


def test_article_versions_render_one_badge_without_removing_history():
    result = run_js(harness() + '''
const story={primary_item:{url:'https://example.com/original'},corroboration_count:1,
 sources:[source('CNBC Technology','publisher:cnbc',{id:'new',role:'active_phase'}),
 source('CNBC Technology','publisher:cnbc',{id:'old',role:'past_phase'})]};
console.log(JSON.stringify(cardResult(story)));
''')
    assert result == {'labels': ['CNBC Technology'], 'more': [],
                      'count': '1 個發布者', 'href': 'https://example.com/original',
                      'unchanged': True}


def test_publisher_aliases_collapse_but_distinct_publishers_remain():
    result = run_js(harness() + '''
console.log(JSON.stringify(cardResult({sources:[
 source('CNBC Technology','publisher:cnbc'),source('CNBC','publisher:cnbc'),
 source('Reuters','publisher:reuters'),
 source('Same feed label','publisher:one'),source('Same feed label','publisher:two')]})));
''')
    assert result['labels'] == ['CNBC Technology', 'Reuters', 'Same feed label', 'Same feed label']
    assert result['count'] == '4 個發布者'
    assert result['unchanged']


def test_unknown_repeated_labels_do_not_invent_publisher_votes():
    result = run_js(harness() + '''
console.log(JSON.stringify(cardResult({corroboration_count:0,sources:[
 source(' Unknown feed ',null),source('Unknown feed',null),
 {source_name:'Another feed',site_id:'curated_media'},null]})));
''')
    assert result['labels'] == ['Unknown feed', 'Another feed']
    assert result['count'] == '來源待辨識'
    assert result['unchanged']


def test_overflow_uses_unique_badges_and_duplicates_do_not_hide_other_sources():
    result = run_js(harness() + '''
const sources=[...Array.from({length:9},()=>source('CNBC','publisher:cnbc')),
 ...Array.from({length:7},(_,i)=>source(`Publisher ${i}`,`publisher:${i}`))];
console.log(JSON.stringify(cardResult({sources})));
''')
    assert result['labels'] == ['CNBC', 'Publisher 0', 'Publisher 1', 'Publisher 2', 'Publisher 3', 'Publisher 4']
    assert result['more'] == ['+2']
    assert result['count'] == '8 個發布者'
    assert result['unchanged']


def test_missing_sources_produce_no_badge_row():
    result = run_js(harness() + '''console.log(JSON.stringify(cardResult({})));''')
    assert result['labels'] == []
    assert result['more'] == []
    assert result['count'] == '來源待辨識'


def test_google_query_refs_display_distinct_reported_publishers_without_votes():
    result = run_js(harness() + '''
console.log(JSON.stringify(cardResult({corroboration_count:0,sources:[
 source('DeepSeek (Google News)',null,{publisher:{schema_version:1,status:'reported',name:'Example News'}}),
 source('DeepSeek (Google News)',null,{publisher:{schema_version:1,status:'reported',name:'Another News'}})]})));
''')
    assert result['labels'] == ['Example News', 'Another News']
    assert result['count'] == '來源資訊待核'
    assert result['unchanged']


def test_cnbc_identity_metadata_still_renders_one_badge():
    result = run_js(harness() + '''
const publisher={schema_version:1,status:'identified',name:'CNBC Technology'};
console.log(JSON.stringify(cardResult({corroboration_count:1,sources:[
 source('CNBC Technology','publisher:cnbc',{publisher,role:'active_phase'}),
 source('CNBC Technology','publisher:cnbc',{publisher,role:'past_phase'})]})));
''')
    assert result['labels'] == ['CNBC Technology']
    assert result['count'] == '1 個發布者'
