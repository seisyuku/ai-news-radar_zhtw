from tests.js_bridge import extract_declarations, run_js


def declarations():
    return extract_declarations('sourceDisplayName', 'readerSiteName', 'readerSiteId',
                                'generalReaderSource', 'READER_PUBLISHERS',
                                'storyCandidateSiteId', 'sourceSignal')


def test_reported_names_are_visible_without_claiming_official_identity():
    result = run_js(declarations() + '''
const r={site_id:'curated_media',source:'Meta AI (Google News)',url:'https://news.google.com/a',
 publisher:{schema_version:1,status:'reported',name:'Example News',domain:'example.org'}};
console.log(JSON.stringify({name:sourceDisplayName(r),group:generalReaderSource(r)}));
''')
    assert result == {'name': 'Example News', 'group': {'level': 'other', 'publisher': 'Example News'}}


def test_identity_does_not_change_legacy_diversity_or_priority_signals():
    result = run_js(declarations() + '''
const before={site_id:'curated_media',source:'DeepSeek (Google News)'},
 after={...before,publisher:{schema_version:1,status:'reported',name:'Example News'}};
console.log(JSON.stringify({sameCap:storyCandidateSiteId(before)===storyCandidateSiteId(after),
 samePriority:sourceSignal(before)===sourceSignal(after),display:sourceDisplayName(after)}));
''')
    assert result == {'sameCap': True, 'samePriority': True, 'display': 'Example News'}


def test_conflicts_do_not_fall_back_to_query_subject_as_publisher():
    result = run_js(declarations() + '''
const r={site_id:'curated_media',source:'Reuters AI (Google News)',url:'https://news.google.com/a',
 publisher:{schema_version:1,status:'conflict',name:null}};
console.log(JSON.stringify({name:sourceDisplayName(r),group:generalReaderSource(r)}));
''')
    assert result['name'] == '來源資訊衝突'
    assert result['group']['level'] == 'other'


def test_older_snapshots_keep_existing_display_fallback():
    result = run_js(declarations() + '''
console.log(JSON.stringify({name:sourceDisplayName({site_id:'curated_media',source:'aibase'}),
 group:generalReaderSource({site_id:'curated_media',source:'Reuters AI (Google News)',
 url:'https://news.google.com/a',title:'Example news - Reuters'})}));
''')
    assert result == {'name': 'AIBASE', 'group': {'level': 'media', 'publisher': 'Reuters'}}
