"""General-list levels must not depend on news score, count, or feed transport."""
import pytest
from tests.js_bridge import extract_declarations, run_js

DECLARATIONS = extract_declarations(
    "READER_SOURCE_LEVELS", "READER_PUBLISHERS", "generalReaderSource",
    "readerSiteId", "readerSiteName", "sourceDisplayName", "computeSiteStats",
    "sourceGroupEntries", "groupedSites", "subgroupSortValue", "sortItemsForList",
    "dedupeSubgroupItems", "getFilteredItems",
)
HELPERS = '''
const state = {listSort: "priority", activeSection: "hot", query: "", siteFilter: "", authorFilter: "", sourceTypeFilter: ""};
const itemPriorityScore = i => i.score || 0;
const scorePercent = itemPriorityScore;
const timelineMs = i => i.time || 0;
const displayDedupeKey = i => i.id;
const itemSourceSortKey = i => i.source;
const multiSourceEventKeys = () => new Set();
const itemMatchesSignalLevel = () => true;
let pool = [];
const sectionItems = () => pool;
'''


@pytest.mark.parametrize("sort", ["priority", "latest", "ai", "source"])
def test_levels_win_over_aibase_score_recency_and_count(sort):
    result = run_js(DECLARATIONS + HELPERS + f'state.listSort = "{sort}";' + '''
const items = [
  {id:"official", source:"OpenAI News", site_id:"official_ai", url:"https://openai.com/news/a", score:1, time:1},
  {id:"media", source:"Reuters", site_id:"curated_media", url:"https://reuters.com/a", score:2, time:2},
  {id:"unknown", source:"Personal feed", site_id:"opmlrss", url:"https://example.com/a", score:99999, time:99999},
  ...Array.from({length: 20}, (_, n) => ({id:`ai${n}`, source:"AIBASE", site_id:"curated_media", score:9999, time:9999})),
];
console.log(JSON.stringify({groups:groupedSites(items).map(([id]) => id), filters:computeSiteStats(items).map(i => i.site_id)}));
''')
    assert result["groups"] == ["original", "media", "aggregate", "other"]
    assert result["filters"] == result["groups"]


def test_publisher_identity_uses_actual_publisher_and_preserves_watchlists():
    result = run_js(DECLARATIONS + HELPERS + '''
const cases = [
 {site_id:"aibase",source:"AIbase"},
 {site_id:"opmlrss",source:"Custom feed",url:"https://blog.lmarena.ai/post"},
 {site_id:"curated_media",source:"Epoch AI (Google News)",url:"https://news.google.com/rss/articles/a",title:"Research results - Epoch AI"},
 {site_id:"opmlrss",source:"Personal name",url:"https://www.reuters.com/a"},
 {site_id:"curated_media",source:"Meta AI (Google News)",url:"https://news.google.com/rss/articles/a",title:"Meta publishes a model - Reuters"},
 {site_id:"curated_media",source:"DeepSeek (Google News)",url:"https://news.google.com/rss/articles/a",title:"New model - Unknown outlet"},
 {site_id:"tw_media",source:"iThome",url:"https://www.ithome.com.tw/news/1"},
 {site_id:"runtimewire",source:"RuntimeWire",source_tier:"watchlist",url:"https://runtimewire.com/a"},
 {site_id:"opmlrss",source:"OpenAI announcement review",url:"https://example.com/a"},
];
console.log(JSON.stringify(cases.map(generalReaderSource)));
''')
    assert [r["level"] for r in result] == ["aggregate", "original", "original", "media", "media", "other", "media", "other", "other"]
    assert result[0]["publisher"] == "AIBASE"
    assert result[4]["publisher"] == "Reuters"
    assert result[5]["publisher"] == "Unknown outlet"


def test_legacy_and_current_aibase_share_filter_and_publisher_group():
    result = run_js(DECLARATIONS + HELPERS + '''
pool = [
 {id:"old",site_id:"aibase",source:"AIbase"},
 {id:"new",site_id:"curated_media",source:"AIBASE"},
 {id:"news",site_id:"curated_media",source:"Reuters",url:"https://reuters.com/a"},
];
state.siteFilter = "aggregate";
const selected = getFilteredItems();
state.siteFilter = "";
state.sourceTypeFilter = "aggregate";
console.log(JSON.stringify({ids:selected.map(i => i.id), typeIds:getFilteredItems().map(i => i.id), groups:groupedSites(selected)[0][1].sourceGroups.map(g => g.source), legacy:readerSiteId(pool[0])}));
''')
    assert result["ids"] == result["typeIds"] == ["old", "new"]
    assert result["groups"] == ["AIBASE"]
    assert result["legacy"] == "curated_media"  # Shared featured identity stays unchanged.
