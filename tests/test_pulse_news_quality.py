"""Development regressions pinned to the user's 2026-10-29 snapshot.

These are known cases, not a held-out estimate of editorial precision.
"""
import copy
import json
from datetime import timedelta
from pathlib import Path

import pytest

from scripts import article_versions as v, primary_evidence as p, news_quality as q
from scripts import update_news as u, brief_events as b, signal_selection

FIXTURE = json.loads((Path(__file__).parent / 'fixtures/pulse-quality-20261029.json').read_text())
NOW = u.parse_iso(FIXTURE['generated_at'])
RECORDS = FIXTURE['records']
OLD = '8689e0ac0029c249eb843e6793ef5f8b0e74f194'
NEW = 'fc11d1facb453df169e763c2e96aabe172103e33'
JUYA = 'd77086cf4ba1de3d89cf73902356b0137fa82e78'
POLICY_URL = 'https://developers.openai.com/api/docs/guides/chatgpt-api-credits'


def row(rid): return copy.deepcopy(next(r for r in RECORDS if r['id'] == rid))


def build(rows, now=NOW, previous=None):
    items = [u.add_source_tier_fields(u.add_ai_relevance_fields(dict(r, site_name=u.apply_site_name_alias(r.get('site_name', ''))))) for r in v.current(rows)
             if u.is_within_reader_window(r, now, 24)]
    items = [r for r in items if r['ai_is_related']]
    stories = u.merge_story_items(items, now, 24)
    result = u.build_brief_event_payloads(stories, rows, previous or b.StateInput('missing'), now, 24,
        archive_meta=b.ArchiveMeta('valid', u.iso(now)))
    assert result.projection['status'] != 'unavailable', result.diagnostics
    assert signal_selection.validate(result.publisher_governance, result.projection)
    merged, daily = {}, {}
    u.apply_brief_event_result(result, daily, merged)
    return result, merged, daily


def test_cnbc_changed_publication_time_is_one_current_article_with_history_and_one_vote():
    rows = [row(OLD), row(NEW)]; before = copy.deepcopy(rows)
    result, _, _ = build(rows)
    event = result.projection['events'][0]
    assert len(event['sources']) == event['article_count'] == event['independent_publisher_count'] == 1
    assert event['raw_record_count'] == 2
    assert event['history_article_ids'] == [OLD]
    assert event['member_article_ids'] == [NEW]
    assert event['primary_item']['id'] == NEW
    assert not event['primary_item'].get('summary')
    assert event['effective_at'] == row(OLD)['published_at']
    assert rows == before


def test_cnbc_same_input_replay_does_not_invent_missing_results_or_force_selection():
    result, _, daily = build([row(OLD), row(NEW)])
    assert not daily['items']
    assert result.publisher_governance['articles'][0]['qualification']['core_evidence'][0]['status'] == 'insufficient'
    gaps = q.material_gaps(row(NEW), result.publisher_governance['articles'][0]['qualification'])
    assert {'summary_describes_pre_announcement', 'financial_metric_value_missing'} <= set(gaps)


@pytest.mark.parametrize('ids', [
    ['783e1068c48844fc88bd7b739febc6297e2b4ca9','c0a1ebcc1ab2d45fc2f13728fe2702ecae1e032d'],
    ['d719d760d7859178a7909434becf855ccd25c438','8ac43102ef8ee35dac02fb4dca2995ecdbf56295'],
])
def test_microsoft_techcrunch_and_reuters_versions_choose_latest_observation(ids):
    rows = [row(i) for i in ids]
    for ordered in (rows, rows[::-1]):
        assert [r['id'] for r in v.current(ordered)] == [ids[0]]
        result, _, _ = build(ordered)
        assert len(result.projection['events']) == 1
        assert result.projection['events'][0]['corroboration_count'] == 1


def test_financial_report_cross_publisher_group_preserves_distinct_companies_periods_and_outlook():
    cnbc = row(NEW)
    verge = next(copy.deepcopy(r) for r in RECORDS if r['source'] == 'The Verge')
    result, _, _ = build([cnbc, verge])
    assert len(result.projection['events']) == 1
    assert result.projection['events'][0]['corroboration_count'] == 2
    for title in ['Microsoft Q3 2026 results: AI revenue rose 20%', 'Alphabet Q2 2026 results: AI revenue rose 20%',
                  'Alphabet Q3 2026 outlook: AI revenue may rise 20%']:
        other = dict(verge, id='other', title=title, summary='', url='https://www.theverge.com/news/different')
        result, _, _ = build([cnbc, other])
        assert len(result.projection['events']) == 2


def test_same_id_summary_update_keeps_history_and_latest_material_together():
    archive = {'x': dict(row(NEW), id='x')}
    raw = u.RawItem(site_id='curated_media', site_name='精選媒體', source='CNBC Technology',
        title=row(NEW)['title'], url=row(NEW)['url'], published_at=u.parse_iso(row(NEW)['published_at']),
        meta={'summary':'Alphabet Q3 2026 free cash flow was USD -9,065 million.'})
    rid = u.make_item_id(raw.site_id, raw.source, raw.title, raw.url)
    archive = {rid: dict(row(NEW), id=rid)}
    u.merge_raw_items_into_archive(archive, [raw], NOW)
    current = archive[rid]
    assert current['summary'] == raw.meta['summary']
    assert current['article_history'][0]['summary'] == row(NEW)['summary']
    assert current['content_observed_at'] == u.iso(NOW)
    u.merge_raw_items_into_archive(archive, [raw], NOW + timedelta(minutes=30))
    assert len(current['article_history']) == 1


def test_rolling_changelog_and_simultaneous_inputs_are_not_guessed_revisions():
    rows = [row(OLD),row(NEW)]
    for r in rows: r['url'] = 'https://developers.openai.com/codex/changelog'
    assert len(v.current(rows)) == 2
    a, c = row(OLD),row(OLD);c['id']='different';c['title']='Another simultaneous feed label'
    assert len(v.current([a,c])) == 2


def policy_page():
    return b'<main><h1>API credits for ChatGPT subscribers</h1><p>Eligible ChatGPT Pro and Business subscriptions can claim free API credits. Receive up to $500 per month as a subscription benefit.</p></main>'


def roundup_page():
    return ('<section class="news-item"><h3>OpenAI 向 ChatGPT Pro 訂閱用戶發放 API 額度</h3>'
        f'<a href="{POLICY_URL}">original</a></section>').encode()


def raw_roundup():
    r = row(JUYA)
    return u.RawItem(site_id=r['site_id'],site_name=r['site_name'],source=r['source'],title=r['title'],
        url=r['url'],published_at=u.parse_iso(r['published_at']),meta={'summary':r['summary']})


def test_roundup_recovery_uses_separate_official_material_and_never_duplicates_digest_votes():
    pages = {row(JUYA)['url']:roundup_page(), POLICY_URL:policy_page()}; calls=[]
    def fetch(url): calls.append(url); return pages[url]
    raw,status = p.recover(None,[raw_roundup()],{},NOW,fetcher=fetch)
    assert status['accepted'] == len(raw) == 1
    assert calls == list(pages)
    assert raw[0].url == POLICY_URL and raw[0].title != row(JUYA)['title']
    assert raw[0].published_at is None
    archive={};u.merge_raw_items_into_archive(archive,raw,NOW)
    result,_,daily=build(list(archive.values()))
    assert len(result.projection['events']) == 1
    assert result.projection['events'][0]['corroboration_count'] == 1
    assert result.publisher_governance['events'][0]['featured_business_events'] == ['pricing']
    assert not u.add_reader_source_policy_fields(row(JUYA))['source_policy']['allow_general']
    again,status=p.recover(None,[raw_roundup()],archive,NOW,fetcher=fetch)
    assert not again and status['already_archived'] == 1


@pytest.mark.parametrize('url', ['http://developers.openai.com/api/docs/guides/credits',
    'https://evil.example/api/docs/guides/credits','https://developers.openai.com@127.0.0.1/api/docs/guides/credits',
    'https://developers.openai.com/api/docs/guides/../keys','https://developers.openai.com/api/docs/guides/%2e%2e/keys',
    'https://developers.openai.com/api/docs/guides/credits?token=secret'])
def test_recovery_never_fetches_arbitrary_or_credential_urls(url):
    assert not p.policy_document(url)


def test_unlinked_roundup_and_generic_documentation_cannot_create_articles():
    assert not p.linked_policy_documents(b'<section class="news-item"><h3>API credits</h3><p>$500</p></section>')
    with pytest.raises(ValueError): p.policy_material(b'<main><h1>API tutorial</h1><p>Use $500 of credits to run an example.</p></main>')
    raw,status=p.recover(None,[raw_roundup()],{},NOW,fetcher=lambda url: roundup_page() if 'juya.uk' in url else b'no official body')
    assert not raw and status['failed'] == 1


@pytest.mark.parametrize('title,summary,supported', [
    ('Alphabet Q3 2026 free cash flow sinks','Alphabet Q3 2026 free cash flow was USD -9,065 million.',True),
    ('Alphabet Q3 2026 capital expenditures','Alphabet Q3 2026 capital expenditures were $51.355 billion.',True),
    ('Alphabet Q3 2026 free cash flow sinks','Alphabet prepares to report results.',False),
    ('Alphabet Q3 2026 forecast','Alphabet expects free cash flow of $9 billion.',False),
    ('Alphabet Q3 2026 results','Microsoft Q3 2026 free cash flow was $9 billion.',False),
    ('A supermarket offers API credits','A shopping subscription offers coupons worth $500.',False),
])
def test_financial_and_credit_material_requires_actual_linked_evidence(title,summary,supported):
    r=u.add_reader_source_policy_fields(dict(row(NEW),title=title,summary=summary))
    qual=u.publisher_governance.qualify(r,u.publisher_governance.source_material(r))
    assert any(e['status']=='supported' for e in qual['core_evidence']) is supported


def test_monitor_traces_control_exclusion_versions_material_gap_and_selected_state():
    rows=[row(OLD),row(NEW),row(JUYA)]
    result,merged,_=build(rows)
    report=q.build(rows,[row(NEW)],[row(NEW)],merged,{'generated_at':u.iso(NOW)},now=NOW)
    records={r['article_id']:r for r in report['articles']}
    assert 'control_only' in records[JUYA]['reason_codes']
    assert not records[JUYA]['in_raw_pool'] and records[JUYA]['archived']
    assert records[OLD]['superseded_by']==NEW
    assert 'financial_metric_value_missing' in records[NEW]['reason_codes']
    assert report['counts']['summary_stale_preview']==1
    assert report['counts']['superseded_records']==1
    assert any(r['article_id']==JUYA for r in report['review_leads'])


def official_results():
    return dict(id='official-result', site_id='official_ai', site_name='官方更新', source='Official Text Fixture',
        title='Alphabet Announces Third Quarter 2026 Results',
        url='https://abc.xyz/investor/news/news-details/2026/alphabet-q3-results/default.aspx',
        published_at=None, first_seen_at=u.iso(NOW), last_seen_at=u.iso(NOW),
        summary='Alphabet Q3 2026 revenue: USD 127,577 million. Google Cloud revenue: USD 30,709 million (+103% YoY), including enterprise AI infrastructure and TPU systems sales. Alphabet Q3 2026 free cash flow: USD -9,065 million. Capital expenditures: USD 51,355 million.')


def test_revision_order_uses_real_instants_and_does_not_refresh_old_headlines():
    old,new=row(OLD),row(NEW)
    old['first_seen_at']='2026-10-28T20:35:30Z'
    new['first_seen_at']='2026-10-29T04:35:30.001+08:00'
    old['last_seen_at']=u.iso(NOW)
    assert v.current([new,old])[0]['id']==NEW
    old['published_at']='2026-10-20T12:00:00Z'
    assert len(v.current([new,old]))==2


def test_same_url_different_quarters_are_not_revisions():
    old,new=row(NEW),row(NEW)
    old.update(id='q2',title='Alphabet Q2 2026 results: revenue grew 20%',url='https://example.test/results')
    new.update(url=old['url'],first_seen_at=u.iso(NOW))
    assert len(v.current([old,new]))==2


def test_feed_update_time_survives_empty_summary():
    assert u.feed_entry_evidence({'updated':'2026-10-29T02:00:00Z'})['source_updated_at']=='2026-10-29T02:00:00Z'


def test_quality_counts_urls_and_explains_noncurrent_evidence():
    r=official_results();r['summary']='Alphabet Q3 2026 revenue was $10 billion.'
    result,merged,_=build([row(NEW),r])
    report=q.build([row(NEW),r],[r],[row(NEW)],merged,{'sites':[{'site_id':'official_ai','ok':True}]},now=NOW)
    trace=next(x for x in report['articles'] if x['article_id']==r['id'])
    assert 'missing_meaningful_ai_signal' in trace['reason_codes']
    assert 'not_current_active_phase' in report['events'][0]['article_reasons'][r['id']]
    assert report['source_health']['success_rate']==1


def test_roundup_recovery_has_fixed_budget_and_separate_votes():
    links = [POLICY_URL + str(i) for i in range(10)]
    page = ('<section class="news-item"><h3>ChatGPT subscription API credits</h3>' + ''.join(f'<a href="{url}">source</a>' for url in links) + '</section>').encode()
    raw,status=p.recover(None,[raw_roundup()]*5,{},NOW,fetcher=lambda url: page if 'juya.uk' in url else policy_page())
    assert status['roundups_checked']==1 and status['primary_attempted']==2
    assert len(raw)==2
    assert all(r.url in links and r.site_id!='juya_daily' for r in raw)


def test_same_id_publication_update_retains_previous_content_and_time():
    r=row(NEW)
    raw=u.RawItem(site_id=r['site_id'],site_name=r['site_name'],source=r['source'],title=r['title'],url=r['url'],
                  published_at=NOW,meta={'summary':'Updated actual financial results.'})
    rid=u.make_item_id(raw.site_id,raw.source,raw.title,raw.url)
    archive={rid:dict(r,id=rid)}
    u.merge_raw_items_into_archive(archive,[raw],NOW)
    assert archive[rid]['published_at']==u.iso(NOW)
    assert archive[rid]['article_history'][0]['published_at']==r['published_at']


def test_earnings_identity_does_not_borrow_finance_context_for_a_different_event():
    assert v.earnings_signature(dict(row(NEW),title='Alphabet reports AI layoffs',
        summary='Previously, Alphabet reported Q3 2026 revenue of $100 billion.',url='https://example.test/layoffs')) is None


def test_primary_fetch_allows_only_one_exact_slash_redirect():
    from unittest.mock import Mock, MagicMock
    def response(status,location=''):
        r=MagicMock(status_code=status,headers={'Location':location})
        r.__enter__.return_value=r;r.iter_content.return_value=[b'body']
        return r
    session=Mock();session.get.side_effect=[response(308,'/issues/2026-10-29/'),response(200)]
    assert p.fetch_page(session,'https://daily.juya.uk/issues/2026-10-29')==b'body'
    assert session.get.call_count==2
    for target in ['http://daily.juya.uk/issues/2026-10-29/','https://evil.test/','/other']:
        session=Mock();session.get.return_value=response(308,target)
        with pytest.raises(ValueError,match='primary_http_308'):
            p.fetch_page(session,'https://daily.juya.uk/issues/2026-10-29')
        assert session.get.call_count==1
