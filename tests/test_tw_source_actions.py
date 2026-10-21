"""Actions wiring contracts, all API/download/publisher requests replaced offline."""
import copy
from datetime import datetime
from datetime import timedelta
import io
import json
import subprocess
import sys
from pathlib import Path
import zipfile

import pytest

from scripts import observe_tw_sources as job
from scripts import tw_source_actions as actions
from scripts import tw_source_observation as core
from scripts import evaluate_tw_source_admission as shadow

ROOT = Path(__file__).resolve().parents[1]
CONTENT = b'name: approved fixture workflow\n'


def now(clock="06:00:00", day="2026-10-21"):
    return core.timestamp(f"{day}T{clock}+08:00")


def plan():
    draft = json.loads((ROOT / 'docs/examples/tw-source-observation.plan.json.example').read_text())
    return draft | {"enabled": True, "experiment_id": "offline-02", "start_date": "2026-10-21",
                    "code_sha": "a" * 40, "workflow_sha256": {v[0]: actions.sha(CONTENT) for v in actions.WORKFLOWS.values()}}


def run(run_id=10, clock="06:00:00", role="observe", status="in_progress", day="2026-10-21"):
    filename, name = actions.WORKFLOWS[role]
    return {"id": run_id, "name": name, "path": f".github/workflows/{filename}",
            "head_sha": "d" * 40, "head_branch": "master", "run_attempt": 1,
            "repository": {"full_name": core.REPOSITORY}, "head_repository": {"full_name": core.REPOSITORY},
            "event": "schedule", "created_at": now(clock, day).isoformat(), "updated_at": now(clock, day).isoformat(),
            "status": status, "conclusion": None if status != "completed" else "success"}


def context(run_id=10, clock="06:00:00", slot="primary", day="2026-10-21"):
    return {"repository": core.REPOSITORY, "branch": "master", "run_id": run_id,
            "created_at": now(clock, day).isoformat(), "event_name": "schedule",
            "schedule": next(k for k, v in core.CRONS.items() if v == slot)}


def zip_bytes(files):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return stream.getvalue()


class FakeGitHub:
    def __init__(self):
        self.records = {10: run()}
        self.items = {}
        self.blobs = {}
        self.job_records = {}
        self.fail = None
        self.calls = []

    def workflow_content(self, record, filename):
        self.calls.append(('workflow_content', record['id']))
        return CONTENT

    def run(self, run_id):
        if self.fail == 'run':
            raise ValueError('synthetic_api_failure')
        return copy.deepcopy(self.records[run_id])

    def runs(self, day):
        if self.fail == 'runs':
            raise ValueError('synthetic_api_failure')
        return [copy.deepcopy(r) for r in self.records.values() if r['name'] == actions.WORKFLOWS['observe'][1]
                and core.timestamp(r['created_at']).astimezone(core.TAIPEI).date().isoformat() == day]

    def artifacts(self, run_id):
        if self.fail == 'artifacts':
            raise ValueError('synthetic_api_failure')
        return copy.deepcopy(self.items.get(run_id, []))

    def archive(self, artifact):
        if self.fail == 'download':
            raise ValueError('synthetic_api_failure')
        return self.blobs[artifact['id']]

    def jobs(self, run_id):
        return copy.deepcopy(self.job_records.get(run_id, [{'steps': []}]))

    def upload(self, run_id, name, files):
        blob = zip_bytes(files)
        identity = len(self.blobs) + 1
        item = {'id': identity, 'name': name, 'expired': False, 'digest': 'sha256:' + actions.sha(blob),
                'workflow_run': {'id': run_id}}
        self.items.setdefault(run_id, []).append(item)
        self.blobs[identity] = blob
        return item


def upload_dir(api, run_id, name, path):
    return api.upload(run_id, name, {p.name: p.read_bytes() for p in path.iterdir()})


def public_source(source):
    return {**source, 'status': 'verified_native_feed', 'articles': [],
            'feed_results': [{'status': 'valid_empty'}], 'requests': []}


def baseline(path, generated='05:50:00'):
    path.write_text(json.dumps({'generated_at': now(generated).isoformat(), 'items': []}))
    return path


def primary_attempt(api, tmp_path, collector=public_source, generated='05:50:00'):
    output = tmp_path / 'primary'
    output.mkdir()
    prepared = job.prepare(api, plan(), context(), output, now())
    upload_dir(api, 10, prepared['intent_artifact_name'], output / 'intent')
    state = json.loads((output / 'state.json').read_text())
    result = job.collect(api, state, output, baseline(tmp_path / 'baseline.json', generated),
                         lambda: now('06:04:00'), collector)
    upload_dir(api, 10, prepared['daily_artifact_name'], output / 'bundle')
    api.records[10]['status'] = 'completed'
    return result, output


def test_end_to_end_prepare_persist_collect_restore_and_skip_recovery(tmp_path):
    api = FakeGitHub()
    result, _ = primary_attempt(api, tmp_path)
    assert result['observation_status'] == 'complete'
    api.records[20] = run(20, '06:30:00')
    history, evidence = actions.restore(api, plan(), '2026-10-21', now('06:30:00'), 20)
    assert history['attempts'][0]['verified'] is True
    assert set(evidence['primary']) == {'attempt.json', 'capture.json', 'baseline.json', 'report.json', 'REPORT.md'}
    result = job.prepare(api, plan(), context(20, '06:30:00', 'recovery'), tmp_path / 'not-written', now('06:30:00'))
    assert result['reason'] == 'primary_complete'
    assert not (tmp_path / 'not-written').exists()


def test_partial_source_recovery_only_fetches_failed_source(tmp_path):
    api = FakeGitHub()
    def mixed(source):
        if source['source_id'] == 'cyberq':
            raise TimeoutError('sensitive exception text must not be saved')
        return public_source(source)
    first, main_output = primary_attempt(api, tmp_path, mixed)
    assert first['observation_status'] == 'partial'
    assert b'sensitive exception' not in (main_output / 'bundle/capture.json').read_bytes()
    api.records[20] = run(20, '06:30:00')
    output = tmp_path / 'recovery'
    output.mkdir()
    prepared = job.prepare(api, plan(), context(20, '06:30:00', 'recovery'), output, now('06:30:00'))
    assert prepared['fetch_source_ids'] == ['cyberq']
    upload_dir(api, 20, prepared['intent_artifact_name'], output / 'intent')
    called = []
    def collect(source):
        called.append(source['source_id'])
        return public_source(source)
    state = json.loads((output / 'state.json').read_text())
    result = job.collect(api, state, output, tmp_path / 'absent-baseline.json', lambda: now('06:34:00'), collect)
    assert called == ['cyberq']
    assert result['observation_status'] == 'complete'
    upload_dir(api, 20, prepared['daily_artifact_name'], output / 'bundle')
    api.records[20]['status'] = 'completed'
    history, _ = actions.restore(api, plan(), '2026-10-21', now('06:35:00'))
    assessed = core.assess(history['attempts'])
    assert assessed['observation_status'] == 'complete'
    assert assessed['sources']['netadmin']['retrieved_at'] == now('06:04:00').isoformat()
    assert assessed['sources']['cyberq']['retrieved_at'] == now('06:34:00').isoformat()


def test_no_publisher_request_without_confirmed_persisted_intent(tmp_path):
    api = FakeGitHub()
    job.prepare(api, plan(), context(), tmp_path, now())
    state = json.loads((tmp_path / 'state.json').read_text())
    called = []
    with pytest.raises(ValueError, match='persisted_intent_required'):
        job.collect(api, state, tmp_path, tmp_path / 'baseline', lambda: now('06:01:00'), called.append)
    assert not called


def test_same_collect_command_cannot_refetch_in_same_job(tmp_path):
    api = FakeGitHub()
    _, output = primary_attempt(api, tmp_path)
    api.records[10]['status'] = 'in_progress'
    state = json.loads((output / 'state.json').read_text())
    called = []
    with pytest.raises(ValueError, match='collection_already_started'):
        job.collect(api, state, output, tmp_path / 'baseline.json', lambda: now('06:04:00'), called.append)
    assert called == []


def test_api_time_cannot_push_actual_collection_past_start_window(tmp_path):
    api = FakeGitHub()
    job.prepare(api, plan(), context(), tmp_path, now())
    upload_dir(api, 10, actions.artifact_name(plan(), '2026-10-21', 'primary', 'intent'), tmp_path / 'intent')
    state = json.loads((tmp_path / 'state.json').read_text())
    ticks = iter([now('06:29:59'), now('06:30:00')])
    called = []
    with pytest.raises(ValueError, match='outside_trigger_window'):
        job.collect(api, state, tmp_path, tmp_path / 'baseline', lambda: next(ticks), called.append)
    assert not called


def test_future_baseline_preserves_sources_as_partial_evidence(tmp_path):
    api = FakeGitHub()
    result, output = primary_attempt(api, tmp_path, generated='06:10:00')
    assert result['observation_status'] == 'partial'
    assert result['baseline_error'] == 'baseline_unavailable_or_invalid'
    assert len(json.loads((output / 'bundle/capture.json').read_text())['sources']) == 5
    history, _ = actions.restore(api, plan(), '2026-10-21', now('06:30:00'))
    decision = core.decide(plan(), context(20, '06:30:00', 'recovery'), history, now('06:30:00'))
    assert decision['fetch_source_ids'] == [] and decision['refresh_baseline'] is True


def test_comparison_failure_preserves_capture_and_requires_baseline_repair(tmp_path, monkeypatch):
    api = FakeGitHub()
    def fail(*args, **kwargs):
        raise ValueError('synthetic baseline schema failure')
    monkeypatch.setattr(shadow, 'evaluate', fail)
    result, output = primary_attempt(api, tmp_path)
    assert result['observation_status'] == 'partial'
    assert result['baseline_error'] == 'baseline_comparison_failed'
    assert (output / 'bundle/capture.json').exists()
    history, _ = actions.restore(api, plan(), '2026-10-21', now('06:30:00'))
    assert history['attempts'][0]['baseline_at'] is None


@pytest.mark.parametrize(('field', 'value', 'reason'), [
    ('experiment_id', 'another', 'manifest_scope_mismatch'),
    ('code_sha', 'f' * 40, 'manifest_scope_mismatch'),
    ('plan_hash', 'e' * 64, 'manifest_scope_mismatch'),
    ('run_id', 999, 'manifest_scope_mismatch'),
])
def test_resealed_wrong_scope_never_becomes_verified(field, value, reason, tmp_path):
    api = FakeGitHub()
    _, output = primary_attempt(api, tmp_path)
    files = {p.name: p.read_bytes() for p in (output / 'bundle').iterdir()}
    manifest = json.loads(files['manifest.json']) | {field: value}
    files['manifest.json'] = actions.encoded(manifest)
    api.items[10].pop()
    api.upload(10, actions.artifact_name(plan(), '2026-10-21', 'primary', 'bundle'), files)
    with pytest.raises(ValueError, match=reason):
        actions.restore(api, plan(), '2026-10-21', now('06:30:00'))


def test_resealed_false_success_is_rederived_from_capture_not_verified_flag(tmp_path):
    api = FakeGitHub()
    _, output = primary_attempt(api, tmp_path)
    files = {p.name: p.read_bytes() for p in (output / 'bundle').iterdir()}
    manifest = json.loads(files.pop('manifest.json'))
    attempt = json.loads(files['attempt.json'])
    attempt['verified'] = True
    attempt['sources']['cyberq']['status'] = 'valid_feed'
    attempt['sources']['cyberq']['item_count'] = 25
    files['attempt.json'] = actions.encoded(attempt)
    files = actions.seal(files, {k: v for k, v in manifest.items() if k not in {'files', 'schema_version'}})
    api.items[10].pop()
    api.upload(10, actions.artifact_name(plan(), '2026-10-21', 'primary', 'bundle'), files)
    with pytest.raises(ValueError, match='source_evidence_mismatch'):
        actions.restore(api, plan(), '2026-10-21', now('06:30:00'))


def test_orphan_bundle_is_not_treated_as_a_free_slot(tmp_path):
    api = FakeGitHub()
    primary_attempt(api, tmp_path)
    api.items[10].pop(0)
    with pytest.raises(ValueError, match='orphan_bundle'):
        actions.restore(api, plan(), '2026-10-21', now('06:30:00'))


def test_signed_download_never_receives_github_authorization():
    class Response:
        def __init__(self, status, headers=None):
            self.status_code, self.headers = status, headers or {}
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def iter_content(self, size):
            yield b'archive'
    class Session:
        def __init__(self):
            self.calls = []
        def get(self, url, **kwargs):
            self.calls.append((url, kwargs))
            if len(self.calls) == 1:
                return Response(302, {'Location': 'https://production.blob.core.windows.net/a?signature=private'})
            return Response(200)
    session = Session()
    api = actions.GitHub('synthetic-token', session)
    assert api.archive({'id': 1}) == b'archive'
    assert session.trust_env is False
    assert session.calls[0][1]['headers']['Authorization'] == 'Bearer synthetic-token'
    assert session.calls[1][1]['headers'] == {}
    assert session.calls[1][1]['allow_redirects'] is False


@pytest.mark.parametrize('target', ['http://production.blob.core.windows.net/a', 'https://attacker.example/a',
                                   'https://user:password@production.blob.core.windows.net/a'])
def test_untrusted_artifact_redirect_never_requested(target):
    class Session:
        calls = 0
        def get(self, *args, **kwargs):
            self.calls += 1
            return type('Response', (), {'status_code': 302, 'headers': {'Location': target}})()
    session = Session()
    with pytest.raises(ValueError, match='untrusted_artifact_redirect'):
        actions.GitHub('synthetic-token', session).archive({'id': 1})
    assert session.calls == 1


@pytest.mark.parametrize('clock', ['07:04:59', '07:20:00'])
def test_deadline_schedule_does_not_bypass_window(clock):
    signal = context(30, clock) | {'schedule': '5 23 * * *'}
    with pytest.raises(ValueError, match='outside_reconcile_window'):
        actions.reconciliation(signal, plan(), now(clock))


@pytest.mark.parametrize('failure', ['runs', 'run', 'artifacts', 'download'])
def test_api_failure_is_never_empty_history(failure, tmp_path):
    api = FakeGitHub()
    primary_attempt(api, tmp_path)
    api.fail = failure
    with pytest.raises(ValueError, match='synthetic_api_failure'):
        actions.restore(api, plan(), '2026-10-21', now('06:30:00'))


@pytest.mark.parametrize(('field', 'value', 'reason'), [
    ('digest', 'sha256:' + '0' * 64, 'artifact_digest_mismatch'),
    ('expired', True, 'artifact_expired'),
    ('workflow_run', {'id': 999}, 'artifact_run_mismatch'),
])
def test_artifact_metadata_tamper_blocks_restore(field, value, reason, tmp_path):
    api = FakeGitHub()
    primary_attempt(api, tmp_path)
    api.items[10][0][field] = value
    with pytest.raises(ValueError, match=reason):
        actions.restore(api, plan(), '2026-10-21', now('06:30:00'))


@pytest.mark.parametrize(('field', 'value'), [
    ('repository', {'full_name': 'attacker/fork'}), ('head_branch', 'feature'),
    ('path', '.github/workflows/update-news.yml'), ('run_attempt', 2), ('event', 'pull_request'),
    ('head_repository', {'full_name': 'attacker/fork'}), ('head_sha', 'master'),
])
def test_wrong_run_identity_or_rerun_rejected(field, value):
    api = FakeGitHub()
    record = run() | {field: value}
    with pytest.raises(ValueError):
        actions.verify_run(api, record, plan())


def test_workflow_content_pin_is_independent_of_head_commit_sha():
    api = FakeGitHub()
    actions.verify_run(api, run() | {'head_sha': 'f' * 40}, plan())
    bad = plan()
    bad['workflow_sha256']['tw-source-observation.yml'] = '0' * 64
    with pytest.raises(ValueError, match='workflow_pin_mismatch'):
        actions.verify_run(api, run(), bad)


@pytest.mark.parametrize('member', ['../escape', '/absolute', 'directory/file', 'nested/', 'a\\b'])
def test_archive_never_extracts_paths(member):
    content = zip_bytes({member: b'data'})
    with pytest.raises(ValueError, match='unsafe_archive_member'):
        actions.unpack(content, {'expired': False, 'digest': 'sha256:' + actions.sha(content)})


def test_manifest_hash_tamper_rejected_even_with_correct_archive_digest():
    files = actions.seal({'intent.json': b'original'}, {})
    files['intent.json'] = b'modified'
    content = zip_bytes(files)
    with pytest.raises(ValueError, match='manifest_hash_mismatch'):
        actions.unpack(content, {'expired': False, 'digest': 'sha256:' + actions.sha(content)})


def test_manifest_scope_and_claim_deletion_are_detected(tmp_path):
    api = FakeGitHub()
    primary_attempt(api, tmp_path)
    api.items[10] = []
    api.job_records[10] = [{'steps': [{'name': 'Persist sampling intent', 'conclusion': 'success'}]}]
    with pytest.raises(ValueError, match='intent_missing_after_upload_attempt'):
        actions.restore(api, plan(), '2026-10-21', now('06:30:00'))


def test_duplicate_slot_claim_in_different_run_is_not_last_writer_wins(tmp_path):
    api = FakeGitHub()
    _, output = primary_attempt(api, tmp_path)
    api.records[11] = run(11, '06:01:00', status='completed')
    files = {p.name: p.read_bytes() for p in (output / 'intent').iterdir()}
    manifest = json.loads(files['manifest.json']) | {'run_id': 11}
    files['manifest.json'] = actions.encoded(manifest)
    api.upload(11, actions.artifact_name(plan(), '2026-10-21', 'primary', 'intent'), files)
    with pytest.raises(ValueError, match='duplicate_slot_claim'):
        actions.restore(api, plan(), '2026-10-21', now('06:30:00'))


def test_future_queued_runs_do_not_block_current_serialized_job(tmp_path):
    api = FakeGitHub()
    api.records[11] = run(11, '06:01:00', status='queued')
    result = job.prepare(api, plan(), context(), tmp_path, now())
    assert result['mode'] == 'collect'


def test_prior_active_run_without_intent_blocks_recovery():
    api = FakeGitHub()
    api.records[20] = run(20, '06:30:00')
    with pytest.raises(ValueError, match='prior_run_active_without_intent'):
        actions.restore(api, plan(), '2026-10-21', now('06:30:00'), 20)


def test_supervisor_detects_missing_day_without_source_or_email_requests(tmp_path):
    api = FakeGitHub()
    api.records = {}
    signal = context(30, '07:05:00') | {'schedule': '5 23 * * *'}
    result = job.reconcile(api, plan(), signal, tmp_path, now('07:05:00'))
    rows = json.loads((tmp_path / 'reconciliation.json').read_text())['days']
    assert rows[0]['status'] == 'missing'
    assert result['mail_due'] == 'false' and result['stop'] == 'false'


def test_overdue_running_sampler_is_unmet_and_not_cancelled(tmp_path):
    api = FakeGitHub()
    work = tmp_path / 'sampler'
    work.mkdir()
    prepared = job.prepare(api, plan(), context(), work, now())
    upload_dir(api, 10, prepared['intent_artifact_name'], work / 'intent')
    report = tmp_path / 'report'
    report.mkdir()
    signal = context(30, '07:05:00') | {'schedule': '5 23 * * *'}
    job.reconcile(api, plan(), signal, report, now('07:05:00'))
    row = json.loads((report / 'reconciliation.json').read_text())['days'][0]
    assert row['status'] == 'unmet'
    assert row['collection_state'] == 'in_progress'
    assert row['deadline_exceeded'] is True
    assert api.records[10]['status'] == 'in_progress'


def test_delayed_manual_reconciliation_stops_at_d7():
    signal = context(30, '10:00:00', day='2026-10-30') | {'event_name': 'workflow_dispatch'}
    dates = actions.reconciliation(signal, plan(), now('10:00:00', '2026-10-30'))
    assert dates == [f'2026-10-{day}' for day in range(21, 28)]


def test_normalize_real_pulse_uses_checked_updated_at_not_invented_completed_at():
    api = FakeGitHub()
    api.records[10] = run(10, '06:35:00') | {'event': 'workflow_run'}
    upstream = run(5, '06:31:00', status='completed') | {'name': 'Update AI News Snapshot',
                'updated_at': now('06:34:00').isoformat(), 'conclusion': 'failure', 'event': 'workflow_dispatch'}
    api.records[5] = upstream
    event = {'repository': {'full_name': core.REPOSITORY}, 'action': 'completed', 'workflow_run': upstream}
    normalized = actions.normalize_context(api, plan(), event, 10, 'workflow_run')
    assert core.trigger(normalized, now('06:35:00'))['slot'] == 'recovery'
    assert normalized['workflow_run']['completed_at'] == upstream['updated_at']
    assert normalized['workflow_run']['conclusion'] == 'failure'
    event['workflow_run'] = upstream | {'updated_at': now('06:32:00').isoformat()}
    with pytest.raises(ValueError, match='stale_or_changed_pulse'):
        actions.normalize_context(api, plan(), event, 10, 'workflow_run')


@pytest.mark.parametrize(('row', 'expected'), [
    ({'status': 'Timeout'}, 'timeout'), ({'status': 'http_error', 'http_status': 503}, 'http_5xx'),
    ({'status': 'http_error', 'http_status': 401}, 'http_401'),
    ({'status': 'http_error', 'http_status': 403}, 'http_403'),
    ({'status': 'http_error', 'http_status': 429}, 'http_429'),
    ({'status': 'robots_blocked_or_unavailable'}, 'robots_unavailable'),
    ({'status': 'outside_publisher_hosts'}, 'host_redirect_blocked'),
    ({'status': 'crawl_delay_requires_manual_run'}, 'manual_required'),
])
def test_source_diagnostics_not_falsified_as_missing_feed(row, expected):
    assert actions.source_status({'requests': [row], 'feed_results': []}) == expected


def test_repo_output_is_forbidden():
    with pytest.raises(ValueError, match='output_must_be_outside_repository'):
        job.external_root(ROOT / 'data/experimental')


def test_read_only_api_pagination_cannot_silently_truncate():
    api = actions.GitHub('synthetic-token')
    api.get = lambda path: {'total_count': 101, 'artifacts': [{'id': 1}]}
    with pytest.raises(ValueError, match='incomplete_api_history'):
        api.pages('actions/runs/10/artifacts', 'artifacts')


def test_cli_disabled_plan_needs_no_token_api_or_output_directory(tmp_path):
    output = tmp_path / 'must-not-exist'
    process = subprocess.run([sys.executable, str(ROOT / 'scripts/observe_tw_sources.py'), 'prepare',
                              '--plan', str(ROOT / 'docs/examples/tw-source-observation.plan.json.example'),
                              '--event-file', str(tmp_path / 'absent-event'), '--output-root', str(output)],
                             capture_output=True, text=True)
    assert process.returncode == 0
    assert json.loads(process.stdout)['reason'] == 'disabled'
    assert not output.exists()


def test_cli_prepare_normalizes_api_metadata_and_sets_action_outputs(tmp_path, monkeypatch):
    api = FakeGitHub()
    config = tmp_path / 'plan.json'
    event = tmp_path / 'event.json'
    configuration = plan()
    configuration['notification'].update(enabled=True, provider='smtp')
    config.write_text(json.dumps(configuration))
    event.write_text(json.dumps({'repository': {'full_name': core.REPOSITORY}, 'schedule': '0 22 * * *'}))
    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return now()
    monkeypatch.setattr(job, 'datetime', FixedDatetime)
    monkeypatch.setattr(actions, 'GitHub', lambda token: api)
    monkeypatch.setattr(job.subprocess, 'run', lambda *a, **kw: type('Result', (), {'stdout': 'a' * 40})())
    monkeypatch.setenv('GITHUB_RUN_ID', '10')
    monkeypatch.setenv('GITHUB_EVENT_NAME', 'schedule')
    monkeypatch.setenv('GITHUB_OUTPUT', str(tmp_path / 'action-output'))
    monkeypatch.setattr(sys, 'argv', ['observe_tw_sources.py', 'prepare', '--plan', str(config),
                                     '--event-file', str(event), '--output-root', str(tmp_path / 'work')])
    assert job.main() == 0
    assert 'mode=collect\n' in (tmp_path / 'action-output').read_text()
    assert (tmp_path / 'work/intent/manifest.json').exists()


def test_workflow_drafts_stay_disabled_and_use_only_experimental_groups():
    import yaml
    for role, (filename, _) in actions.WORKFLOWS.items():
        path = ROOT / 'docs/examples' / filename.replace('.yml', '.workflow.yml.example')
        doc = yaml.safe_load(path.read_text())
        assert all(str(job['if']).startswith('${{ false') for job in doc['jobs'].values())
        assert doc['concurrency']['group'].startswith('tw-source-shadow-')
        assert doc['concurrency']['cancel-in-progress'] is False
        for item in doc['jobs'].values():
            assert 'contents: write' not in json.dumps(item)
        primary_job = doc['jobs']['observe' if role == 'observe' else 'report']
        run_commands = '\n'.join(step.get('run', '') for step in primary_job['steps'])
        assert '--plan "observation-code/' not in run_commands
        assert '--plan "radar-baseline/' in run_commands if role == 'observe' else '--plan "observation-plan/' in run_commands
    draft = json.loads((ROOT / 'docs/examples/tw-source-observation.plan.json.example').read_text())
    assert draft['enabled'] is False and all(value is None for value in draft['workflow_sha256'].values())
