"""Bounded official-text recovery from control roundups.

Roundup paragraphs are search leads, never syndicated articles or votes. Only
linked, separately fetched official policy material can become a record.
"""
import hashlib
import re
from urllib.parse import urlsplit, urljoin

from bs4 import BeautifulSoup

try:
    from scripts import news_quality, evidence_policy
except ModuleNotFoundError:
    import news_quality
    import evidence_policy


def policy_document(url):
    try:
        p = urlsplit(url)
        return (p.scheme == 'https' and p.netloc == 'developers.openai.com'
            and p.path.startswith('/api/docs/guides/') and len(p.path.split('/')) == 5
            and not evidence_policy.attachment_url(url)
            and not p.query and not p.fragment and not re.search(r'%|\s|\\|\.\.', p.path))
    except ValueError:
        return False


def fetch_page(session, url, *, slash_redirect=False):
    if evidence_policy.attachment_url(url):
        raise ValueError('unsupported_evidence_format')
    # Permit only a single trailing-slash canonicalization on this exact URL.
    with session.get(url, timeout=(4, 8), stream=True, allow_redirects=False,
                     headers={'User-Agent': 'AI-News-Radar/1.0 (primary evidence)'}) as response:
        target = urljoin(url, response.headers.get('Location', ''))
        if (not slash_redirect and response.status_code in {301, 302, 307, 308}
                and target == url.rstrip('/') + '/' and target != url):
            return fetch_page(session, target, slash_redirect=True)
        if response.status_code != 200: raise ValueError('primary_http_' + str(response.status_code))
        evidence_policy.validate_text_mime(response.headers.get('Content-Type', ''))
        chunks, size = [], 0
        for chunk in response.iter_content(32768):
            size += len(chunk)
            if size > 2 * 1024 * 1024: raise ValueError('primary_page_too_large')
            chunks.append(chunk)
        return evidence_policy.validate_text_bytes(b''.join(chunks), response.headers.get('Content-Type', ''))


def linked_policy_documents(page):
    soup = BeautifulSoup(page, 'html.parser')
    result = []
    for section in soup.select('section.news-item'):
        heading = section.find(['h2', 'h3'])
        if not heading or not news_quality.signals(heading.get_text(' ', strip=True)): continue
        for a in section.select('a[href]'):
            url = a['href'].rstrip('/')
            if policy_document(url) and url not in result: result.append(url)
    return result[:2]


def policy_material(page):
    evidence_policy.validate_text_bytes(page)
    soup = BeautifulSoup(page, 'html.parser')
    main = soup.find('main') or soup.find('article')
    if not main or not main.find('h1'): raise ValueError('primary_body_missing')
    title = main.find('h1').get_text(' ', strip=True)[:500]
    for node in main.select(evidence_policy.NON_TEXT_NODES): node.decompose()
    text = main.get_text(' ', strip=True)
    text = re.sub(r'^Copy Page\s*', '', text[text.find(title) + len(title):].strip())
    text = text[:1600]
    if len(text) == 1600 and '. ' in text:
        text = text.rsplit('. ', 1)[0] + '.'
    # Reject instructions, ordinary API docs and undated evergreen tutorials.
    if (not news_quality.signals(title + '\n' + text)
            or not re.search(r'\b(?:eligible|subscription|subscribers|plan)\b', title + ' ' + text, re.I)
            or not re.search(r'\$\s*\d|\d+\s*(?:USD|dollars)', text, re.I)
            or not re.search(r'can claim|included|receive|benefit', text, re.I)):
        raise ValueError('not_concrete_subscription_policy')
    return title, text


def recover(session, raw_items, archive, now, *, fetcher=None):
    """At most one current roundup and two primary pages per existing refresh."""
    try:
        from scripts import update_news as u
    except ModuleNotFoundError:
        import update_news as u
    fetcher = fetcher or (lambda url: fetch_page(session, url))
    status = {'roundups_checked': 0, 'primary_attempted': 0, 'accepted': 0, 'already_archived': 0,
              'failed': 0, 'reason_counts': {}, 'generated_at': u.iso(now)}
    records = []
    known = {r['url'] for r in archive.values()}
    candidates = sorted((r for r in raw_items if r.site_id == 'juya_daily'
        and r.published_at and now - u.timedelta(hours=24) <= r.published_at <= now
        and news_quality.signals(str(r.meta.get('summary') or ''))), key=lambda r: r.published_at, reverse=True)[:1]
    for roundup in candidates:
        # Only this existing control's issue pages, never a URL supplied in prose.
        if not re.fullmatch(r'https://daily\.juya\.uk/issues/\d{4}-\d{2}-\d{2}/?', roundup.url): continue
        try:
            status['roundups_checked'] += 1
            links = linked_policy_documents(fetcher(roundup.url))
        except Exception as exc:
            status['failed'] += 1
            status['reason_counts'][str(exc) if isinstance(exc, ValueError) else type(exc).__name__] = 1
            continue
        for url in links:
            if url in known:
                status['already_archived'] += 1
                continue
            status['primary_attempted'] += 1
            try:
                page = fetcher(url)
                title, summary = policy_material(page)
                records.append(u.RawItem(site_id='official_ai', site_name='Official AI Updates',
                    source='OpenAI Developer Policy', title=title, url=url, published_at=None,
                    meta={'summary': summary, 'publisher_links': [url],
                        'primary_provenance': {'discovered_via': roundup.url, 'evidence_url': url,
                            'retrieved_at': u.iso(now), 'sha256': hashlib.sha256(page).hexdigest(),
                            'evidence_format': 'html', 'policy_version': evidence_policy.VERSION,
                            'time_basis': 'first_observed', 'publication_time_known': False}}))
                status['accepted'] += 1; known.add(url)
            except Exception as exc:
                status['failed'] += 1
                name = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
                status['reason_counts'][name] = status['reason_counts'].get(name, 0) + 1
    return records, status
