"""Offline full-generator replay of a pinned snapshot; never fetches providers."""
import argparse
from contextlib import ExitStack
import json
import os
import random
from pathlib import Path
import shutil
import sys
from datetime import datetime, timezone
from unittest.mock import patch

try:
    from scripts import update_news as u, primary_evidence
except ModuleNotFoundError:
    import update_news as u
    import primary_evidence


def replay(baseline, output, *, evidence_pages=None, evidence_saved_at=None):
    baseline, output = Path(baseline).resolve(), Path(output).resolve()
    if baseline == output or output.exists(): raise ValueError('replay_requires_new_output_directory')
    output.mkdir(parents=True)
    for p in baseline.glob('*.json'): shutil.copy2(p, output / p.name)
    archive = json.loads((baseline / 'archive.json').read_text())
    status = json.loads((baseline / 'source-status.json').read_text())
    now = u.parse_iso(archive['generated_at'])
    raw = []
    if evidence_pages:
        candidates = [r for r in archive['items'] if r.get('site_id') == 'juya_daily' and u.is_within_reader_window(r, now, 24)]
        for r in candidates:
            raw.append(u.RawItem(site_id=r['site_id'], site_name=r['site_name'], source=r['source'],
                title=r['title'], url=r['url'], published_at=u.parse_iso(r['published_at']), meta={'summary': r.get('summary','')}))
        recovered, _ = primary_evidence.recover(
            None, raw, {row['id']: row for row in archive['items']}, now,
            fetcher=evidence_pages.__getitem__,
        )
        for record in recovered:
            provenance = record.meta['primary_provenance']
            provenance['retrieved_at'] = (evidence_saved_at or {}).get(record.url)
            provenance['replay_time_basis'] = 'counterfactual_at_snapshot_cutoff'
        raw.extend(recovered)
    argv = ['update_news.py', '--output-dir', str(output), '--translate-max-new', '0']
    with ExitStack() as stack:
        stack.callback(random.setstate, random.getstate())
        random.seed(0)
        stack.enter_context(patch.object(sys, 'argv', argv))
        stack.enter_context(patch.object(u, 'utc_now', lambda: now))
        stack.enter_context(patch.object(u, 'collect_all', lambda *_: (raw, status['sites'])))
        stack.enter_context(patch.object(u, 'run_market_sensors', lambda *_: ({'generated_at':u.iso(now),'signals':[]}, {}, [])))
        stack.enter_context(patch.dict(os.environ, {k:'' for k in ('GEMINI_API_KEY','GROQ_API_KEY','GITHUB_STEP_SUMMARY','GOOGLE_TRANSLATE_API_KEY')}))
        stack.enter_context(patch('requests.sessions.Session.request', side_effect=AssertionError('offline_replay_network_forbidden')))
        if u.main() != 0:
            raise RuntimeError('offline_replay_failed')
    meta = {'snapshot_time': u.iso(now), 'mode': 'counterfactual_primary_recovery' if evidence_pages else 'same_input_repair',
            'live_fetch_performed': False, 'random_seed': 0, 'baseline': str(baseline),
            'limitation': 'Supplementary primary material was retrieved after the cutoff; this is a counterfactual ingestion test, not historical evidence of presence.'}
    (output / 'replay-meta.json').write_text(json.dumps(meta, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--page-manifest', type=Path, help='JSON mapping exact public URL to saved HTML path')
    args = parser.parse_args()
    paths = json.loads(args.page_manifest.read_text()) if args.page_manifest else {}
    pages = {url: Path(path).read_bytes() for url,path in paths.items()}
    saved = {url: datetime.fromtimestamp(Path(path).stat().st_mtime, timezone.utc).isoformat() for url,path in paths.items()}
    replay(args.baseline, args.output_dir, evidence_pages=pages, evidence_saved_at=saved)


if __name__ == '__main__':
    main()
