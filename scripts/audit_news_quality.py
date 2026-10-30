"""Read a saved generation and print a complete funnel or selected ID/URL."""
import argparse
import json
from pathlib import Path

try:
    from scripts import news_quality, update_news as u
except ModuleNotFoundError:
    import news_quality
    import update_news as u


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=Path('data'))
    parser.add_argument('--query', help='Exact article ID, event ID or URL')
    args = parser.parse_args()
    def read(name): return json.loads((args.data_dir / name).read_text())
    archive, latest, all_items, merged, status = [read(n) for n in ('archive.json','latest-24h.json','latest-24h-all.json','stories-merged.json','source-status.json')]
    result = status.get('news_quality') or news_quality.build(archive['items'], all_items['items_all'], latest['items'], merged, status,
        now=u.parse_iso(archive['generated_at']), project_versions=False)
    if args.query:
        rows = [r for r in result['articles'] if args.query in (r['article_id'],r['url']) or args.query in r['event_ids']]
        ids = {eid for r in rows for eid in r['event_ids']}
        result = {'generated_at': result['generated_at'], 'articles': rows,
            'events': [e for e in result['events'] if e['event_id'] in ids],
            'review_leads': [r for r in result['review_leads'] if r['article_id'] in {x['article_id'] for x in rows}]}
        if not rows:
            found = [r for r in archive['items'] if args.query in (r['id'], r.get('url'))]
            result['archive_matches'] = [{'article_id': r['id'], 'archived': True, 'in_window': False, 'reason_codes': ['outside_reader_window']} for r in found]
            result['reason'] = 'outside_reader_window' if found else 'not_in_retained_archive_fetch_history_unknown'
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
