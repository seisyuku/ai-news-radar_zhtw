from tests.js_bridge import extract_declarations, run_js


def test_reader_group_consumes_policy_instead_of_query_or_parent_edition():
    code = extract_declarations('generalReaderSource', 'sourceDisplayName', 'readerSiteName',
                                'readerSiteId', 'READER_PUBLISHERS')
    result = run_js(code + '''
const base={site_id:'curated_media',source:'DeepSeek (Google News)',url:'https://news.google.com/a',
 publisher:{schema_version:1,status:'identified',name:'Bloomberg',domain:'bloomberg.com'},
 source_policy:{schema_version:1,policy_id:'publisher-governance-v1',registry_revision:'a'.repeat(64),
 admission_status:'unreviewed',publisher_kind:'media'}};
const approved={...base,source_policy:{...base.source_policy,admission_status:'limited'}};
console.log(JSON.stringify({unreviewed:generalReaderSource(base),limited:generalReaderSource(approved)}));
''')
    assert result == {'unreviewed': {'level': 'other', 'publisher': 'Bloomberg'},
                      'limited': {'level': 'media', 'publisher': 'Bloomberg'}}


def test_count_does_not_turn_identified_unreviewed_sources_into_quality_acceptance():
    code = extract_declarations('storySourceCountLabel', 'storySourceCount')
    result = run_js(code + '''
const r={corroboration_key:'publisher:bloomberg',publisher:{schema_version:1,status:'identified',name:'Bloomberg'},
 source_policy:{schema_version:1,policy_id:'publisher-governance-v1',admission_status:'unreviewed'}};
console.log(JSON.stringify({label:storySourceCountLabel({sources:[r,r]}),
 count:storySourceCount({sources:[r,r]})}));
''')
    assert result == {'label': '1 個發布者 · 含未審來源', 'count': 1}


def test_policy_metadata_does_not_change_legacy_event_priority_or_diversity_keys():
    code = extract_declarations('sourceSignal', 'storyCandidateSiteId', 'readerSiteId', 'readerSiteName')
    result = run_js(code + '''
const a={site_id:'curated_media',source:'Meta AI (Google News)'},b={...a,
 source_policy:{admission_status:'unreviewed',source_tier_rank:6}};
console.log(JSON.stringify([sourceSignal(a)===sourceSignal(b),storyCandidateSiteId(a)===storyCandidateSiteId(b)]));
''')
    assert result == [True, True]
