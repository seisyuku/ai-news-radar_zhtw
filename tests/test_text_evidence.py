"""Contract regressions for the explicitly reduced text-only evidence scope."""
import json
from unittest.mock import Mock, MagicMock

import pytest

from scripts import evidence_policy as e, primary_evidence as p, update_news as u
from tests.test_pulse_news_quality import policy_page, POLICY_URL
from tests.test_publisher_governance import NOW


@pytest.mark.parametrize('suffix',['pdf','PDF','docx','xlsx','pptx','zip','mp4','mp3','png','svg','webp'])
def test_attachment_links_are_not_text_sources(suffix):
    url='https://abc.xyz/investor/results.'+suffix
    assert e.attachment_url(url)
    assert e.exclusion_reason({'url':url})
    session=Mock()
    with pytest.raises(ValueError,match='unsupported_evidence_format'):
        p.fetch_page(session,url)
    session.get.assert_not_called()


@pytest.mark.parametrize('url',[
    'https://abc.xyz/report.%70%64%66','https://abc.xyz/report%252epdf',
    'https://abc.xyz/download?file=results.pdf','https://abc.xyz/download?format=pdf',
    'https://abc.xyz/report.pdf/','https://abc.xyz/report.pdf;download=1',
])
def test_encoded_and_download_attachment_urls_hold(url):
    assert e.attachment_url(url)


@pytest.mark.parametrize('data',[b'%PDF-1.7',b' \n%PDF-1.7',b'\xef\xbb\xbf%PDF-1.7',b'PK\x03\x04document',
    b'\x89PNGfile',b'GIF89afile',b'RIFFaudio',b'\x00\x00\x00\x20ftypmp42',b'\xd0\xcf\x11\xe0legacy'])
@pytest.mark.parametrize('mime',['','text/html'])
def test_binary_bytes_cannot_masquerade_as_html(data,mime):
    with pytest.raises(ValueError,match='unsupported_evidence_format'):
        e.validate_text_bytes(data,mime)


@pytest.mark.parametrize('mime',['application/pdf','application/octet-stream','image/png','video/mp4',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'])
def test_nontext_response_is_rejected_before_reading_body(mime):
    response=MagicMock(status_code=200,headers={'Content-Type':mime})
    response.__enter__.return_value=response
    session=Mock();session.get.return_value=response
    with pytest.raises(ValueError,match='unsupported_evidence_format'):
        p.fetch_page(session,POLICY_URL)
    response.iter_content.assert_not_called()


def test_text_page_with_embedded_media_uses_only_visible_prose():
    original=policy_page()
    extra=b'<video>FAKE_VIDEO $999</video><audio>FAKE_AUDIO</audio><table><tr><td>FAKE_TABLE $777</td></tr></table><figure>FAKE_FIGURE</figure><p hidden>FAKE_HIDDEN</p>'
    page=original.replace(b'</main>',extra+b'</main>')
    assert p.policy_material(page)==p.policy_material(original)
    evidence=u.feed_entry_evidence({'link':POLICY_URL,'summary':'<p>Official AI announcement.</p>'+extra.decode()+'<a href="report.pdf">attachment</a><a href="/api/docs/guides/credits">source</a>'})
    assert 'FAKE_' not in evidence['summary']
    assert evidence['publisher_links']==['https://developers.openai.com/api/docs/guides/credits']


def test_raw_metadata_cannot_disguise_the_actual_attachment_url():
    raw=u.RawItem('official_ai','Official AI Updates','OpenAI News','OpenAI releases GPT-6 model',
        'https://openai.com/result.pdf',NOW,{'url':'https://openai.com/index/result','summary':'OpenAI releases GPT-6 model for developers.'})
    archive={}
    assert not u.merge_raw_items_into_archive(archive,[raw],NOW)
    assert not archive


def test_rss_nontext_mime_is_rejected_before_reading_feed_content():
    response=Mock(headers={'Content-Type':'application/pdf'})
    session=Mock();session.get.return_value=response
    with pytest.raises(ValueError,match='unsupported_evidence_format'):
        u.fetch_feed_as_source_items(session,{'xml_url':'https://openai.com/news/rss.xml','title':'OpenAI News'},NOW)
    assert not any(c[0]=='content' for c in response.mock_calls)


def test_native_official_rss_prose_is_collected_without_attachment_enclosures():
    xml=f"""<rss><channel><title>OpenAI News</title><item><title>OpenAI releases GPT-6 model</title>
    <link>https://openai.com/index/synthetic</link><pubDate>{u.iso(NOW)}</pubDate>
    <description><![CDATA[<p>OpenAI releases GPT-6 model for developers.</p><video>FAKE_VIDEO</video>]]></description>
    <enclosure url='https://openai.com/results.pdf' type='application/pdf'/></item></channel></rss>""".encode()
    response=Mock(headers={'Content-Type':'application/rss+xml'},content=xml)
    session=Mock();session.get.return_value=response
    rows=u.fetch_feed_as_source_items(session,{'xml_url':'https://openai.com/news/rss.xml','title':'OpenAI News'},NOW)
    assert len(rows)==1 and rows[0].meta['summary']=='OpenAI releases GPT-6 model for developers.'
    assert session.get.call_count==1
    assert 'results.pdf' not in json.dumps(rows[0].meta)


@pytest.mark.parametrize('marker',[[],{},123])
def test_malformed_format_metadata_is_held_without_crashing(marker):
    assert e.exclusion_reason({'url':POLICY_URL,'primary_provenance':{'evidence_format':marker}})=='unsupported_evidence_format'
