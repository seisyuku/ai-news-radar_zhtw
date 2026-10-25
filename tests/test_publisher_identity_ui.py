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


def test_unknown_public_feed_uses_configured_name_only_for_matching_article_host_and_scope():
    result = run_js(declarations() + '''
const base={site_id:'tw_media',source:'AlphaLab',url:'https://www.alphalab.site/story',
 publisher:{schema_version:1,status:'unknown',name:null,domain:'www.alphalab.site'},
 ingress:{kind:'public_feed',site_id:'tw_media',source_id:'alphalab',name:'AlphaLab',
 feed_url:'https://www.alphalab.site/feed.xml'},
 source_policy:{schema_version:1,policy_id:'publisher-governance-v1',
 registry_revision:'a'.repeat(64),scope_id:'alphalab',admission_status:'unreviewed'}};
const cyber={...base,source:'CyberQ 賽博客',url:'https://cyberq.tw/story',
 publisher:{...base.publisher,domain:'cyberq.tw'},
 ingress:{...base.ingress,source_id:'cyberq',name:'CyberQ 賽博客',feed_url:'https://cyberq.tw/feed/'},
 source_policy:{...base.source_policy,scope_id:'cyberq'}};
console.log(JSON.stringify({alpha:generalReaderSource(base),cyber:sourceDisplayName(cyber),
 otherHost:sourceDisplayName({...base,url:'https://example.com/story',
 publisher:{...base.publisher,domain:'example.com'}}),
 otherScope:sourceDisplayName({...base,source_policy:{...base.source_policy,scope_id:'other'}})}));
''')
    assert result == {'alpha': {'level': 'other', 'publisher': 'AlphaLab'},
                      'cyber': 'CyberQ 賽博客', 'otherHost': 'example.com',
                      'otherScope': 'www.alphalab.site'}


def test_unknown_private_feed_shows_article_host_without_trusting_private_label():
    result = run_js(declarations() + '''
const base={site_id:'opmlrss',source:'Private feed name',url:'https://www.infoq.cn/article/a',
 publisher:{schema_version:1,status:'unknown',name:null,domain:'www.infoq.cn'},
 ingress:{kind:'private_opml',site_id:'opmlrss',source_id:null,name:'RSS/OPML',feed_url:null}};
console.log(JSON.stringify({name:sourceDisplayName(base),group:generalReaderSource(base),
 google:sourceDisplayName({...base,url:'https://news.google.com/rss/articles/a',
 publisher:{...base.publisher,domain:'news.google.com'}}),
 conflict:sourceDisplayName({...base,publisher:{...base.publisher,status:'conflict'}})}));
''')
    assert result == {'name': 'www.infoq.cn',
                      'group': {'level': 'other', 'publisher': 'www.infoq.cn'},
                      'google': '來源待辨識', 'conflict': '來源資訊衝突'}
