"""Offline mail/finalization faults. No SMTP connection or Actions mutation."""
import copy
import csv
from datetime import datetime, timedelta
import io
import json
import os
from pathlib import Path
import smtplib
import ssl
import subprocess
import sys
from urllib.parse import unquote

import pytest

from scripts import tw_source_email as email
from scripts import tw_source_reporting as reporting
from scripts import tw_source_actions as actions
from scripts import observe_tw_sources as job
from scripts import tw_source_observation as core
from scripts import evaluate_tw_source_admission as shadow
from test_tw_source_actions import FakeGitHub, now, plan as base_plan, run, upload_dir, context as sampler_context, public_source


def plan():
    value = base_plan()
    value['notification'].update(enabled=True, provider='smtp')
    return value


class MailGitHub(FakeGitHub):
    def __init__(self):
        super().__init__()
        self.records = {}

    def report_runs(self, start, end):
        if self.fail == 'report_runs':
            raise ValueError('synthetic_ledger_api_failure')
        return [copy.deepcopy(record) for record in self.records.values()
                if record['name'] == actions.WORKFLOWS['report'][1]]


def signal(api, identity=100, day='2026-10-21', clock='07:05:00'):
    api.records[identity] = run(identity, clock, role='report', day=day)
    return {'repository': core.REPOSITORY, 'branch': 'master', 'run_id': identity,
            'event_name': 'schedule', 'schedule': '5 23 * * *', 'created_at': now(clock, day).isoformat()}


def day_row(day='2026-10-21', status='missing', *, ongoing=False):
    return {'date': day, 'status': status, 'attempts': [], 'source_summary': {},
            'collection_state': 'in_progress' if ongoing else status, 'deadline_exceeded': True,
            'candidate_articles': None, 'pending_review_articles': None, 'error': None}


def prepare(api, tmp_path, *, identity=100, day='2026-10-21', rows=None):
    context = signal(api, identity, day)
    output = tmp_path / f'report-{identity}'
    output.mkdir()
    rows = rows or [day_row(day)]
    result = reporting.prepare(api, plan(), context, output, now('07:05:00', day), rows, {})
    return context, output, result


def upload_prepared(api, identity, output, result, *, include_final=True, include_intent=True):
    if result.get('report_bundle_ready') == 'true':
        upload_dir(api, identity, result['report_artifact_name'], output / 'daily-report')
    if include_final and result.get('final_bundle_ready') == 'true':
        upload_dir(api, identity, result['final_artifact_name'], output / 'final')
    if include_intent and result.get('mail_due') == 'true':
        upload_dir(api, identity, result['mail_intent_artifact_name'], output / 'mail-intent')


def accepted(payload, config):
    return {'status': 'provider_accepted', 'retryable': False, 'phase': 'data', 'smtp_code': 250, 'error_type': None}


def rejected(payload, config):
    return {'status': 'definite_nonacceptance', 'retryable': True, 'phase': 'data', 'smtp_code': 451, 'error_type': 'SMTPDataRejected'}


def send_and_persist(api, context, output, prepared, sender=accepted, *, persist=True):
    result = reporting.notify(api, plan(), context, output, core.timestamp(context['created_at']) + timedelta(seconds=1), '', sender=sender)
    if persist:
        upload_dir(api, context['run_id'], prepared['mail_receipt_artifact_name'], output / 'mail-receipt')
    api.records[context['run_id']]['status'] = 'completed'
    return result


def smtp_settings(**changes):
    value = {'provider': 'smtp', 'tls': 'ssl', 'port': 465, 'host': 'smtp.example.test',
             'username': 'synthetic-user', 'password': 'synthetic-password',
             'from': 'radar@example.test', 'to': 'reader@example.test'}
    return json.dumps(value | changes)


class SMTP:
    def __init__(self, *, failure=None, data_code=250, rcpt_code=250, quit_failure=False):
        self.failure, self.data_code, self.rcpt_code, self.quit_failure = failure, data_code, rcpt_code, quit_failure
        self.calls, self.raw = [], None
    def ehlo(self):
        self.calls.append('ehlo')
        return 250, b'ok'
    def starttls(self, context):
        assert context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname
        self.calls.append('starttls')
    def login(self, username, password):
        self.calls.append('login')
        if self.failure == 'auth':
            raise smtplib.SMTPAuthenticationError(535, b'private auth text')
    def mail(self, address):
        self.calls.append('mail')
        return 250, b'ok'
    def rcpt(self, address):
        self.calls.append('rcpt')
        return self.rcpt_code, b'private address response'
    def data(self, content):
        self.calls.append('data')
        self.raw = content
        if self.failure == 'disconnect':
            raise smtplib.SMTPServerDisconnected('private connection detail')
        if self.failure == 'data_reject':
            raise smtplib.SMTPDataError(self.data_code, b'private rejection text')
        return self.data_code, b'private provider response'
    def quit(self):
        self.calls.append('quit')
        if self.quit_failure:
            raise smtplib.SMTPServerDisconnected('lost QUIT')
    def close(self):
        self.calls.append('close')


class SMTPModule:
    def __init__(self, client=None, connect_error=None):
        self.client = client or SMTP()
        self.connect_error = connect_error
        self.calls = 0
    def SMTP_SSL(self, host, port, timeout, context):
        assert context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname
        return self.SMTP(host, port, timeout)
    def SMTP(self, host, port, timeout):
        self.calls += 1
        assert timeout == 20
        if self.connect_error:
            raise self.connect_error
        return self.client


PAYLOAD = {'subject': '[TW來源觀察][成功] 2026-10-21', 'body': '測試回報，非新增事件裁決。\n', 'payload_hash': 'a' * 64}


@pytest.mark.parametrize(('tls', 'port'), [('ssl', 465), ('starttls', 587)])
def test_smtp_tls_acceptance_is_sanitized_and_not_inbox_proof(tls, port):
    module = SMTPModule()
    result = email.send(PAYLOAD, smtp_settings(tls=tls, port=port), smtp_module=module)
    assert result['status'] == 'provider_accepted' and result['smtp_code'] == 250
    if tls == 'starttls':
        assert module.client.calls[:4] == ['ehlo', 'starttls', 'ehlo', 'login']
    assert 'delivered' not in result
    assert 'private' not in json.dumps(result) and 'example.test' not in json.dumps(result)
    assert b'Message-ID:' in module.client.raw


@pytest.mark.parametrize(('client', 'expected', 'retry'), [
    (SMTP(failure='auth'), 'definite_nonacceptance', False),
    (SMTP(rcpt_code=550), 'definite_nonacceptance', False),
    (SMTP(rcpt_code=450), 'definite_nonacceptance', True),
    (SMTP(data_code=451), 'definite_nonacceptance', True),
    (SMTP(failure='data_reject', data_code=554), 'definite_nonacceptance', False),
    (SMTP(failure='disconnect'), 'delivery_unknown', False),
    (SMTP(data_code=354), 'delivery_unknown', False),
    (SMTP(quit_failure=True), 'provider_accepted', False),
])
def test_smtp_protocol_failures_are_classified_before_retry(client, expected, retry):
    result = email.send(PAYLOAD, smtp_settings(), smtp_module=SMTPModule(client))
    assert result['status'] == expected and result['retryable'] is retry
    assert 'private' not in json.dumps(result)
    if client.rcpt_code != 250:
        assert 'data' not in client.calls


@pytest.mark.parametrize('error', [OSError('private network'), ssl.SSLCertVerificationError('private cert')])
def test_pre_data_connection_failure_is_definite_nonacceptance(error):
    result = email.send(PAYLOAD, smtp_settings(), smtp_module=SMTPModule(connect_error=error))
    assert result['status'] == 'definite_nonacceptance'
    assert result['retryable'] is not isinstance(error, ssl.SSLCertVerificationError)


@pytest.mark.parametrize('change', [
    {'tls': 'none'}, {'port': 25}, {'host': 'https://smtp.example.test'},
    {'to': 'one@example.test,two@example.test'}, {'from': 'x@example.test\r\nBcc: evil@example.test'},
    {'password': ''}, {'provider': 'other'},
])
def test_invalid_settings_never_connect_or_expose_configuration(change):
    module = SMTPModule()
    result = email.send(PAYLOAD, smtp_settings(**change), smtp_module=module)
    assert result['status'] == 'definite_nonacceptance' and result['retryable'] is False
    assert module.calls == 0 and result['error_type'] == 'EmailSettingsInvalid'


def test_missing_settings_records_failure_not_success():
    result = email.send(PAYLOAD, '', smtp_module=SMTPModule())
    assert result['status'] == 'definite_nonacceptance' and result['phase'] == 'config'


def test_daily_email_requires_report_and_persisted_intent_then_deduplicates(tmp_path):
    api = MailGitHub()
    context, output, prepared = prepare(api, tmp_path)
    assert prepared['mail_due'] == 'true'
    called = []
    with pytest.raises(ValueError, match='persisted_notification_intent_required'):
        reporting.notify(api, plan(), context, output, now('07:05:01'), '', sender=lambda *args: called.append(args))
    assert not called
    upload_prepared(api, context['run_id'], output, prepared)
    assert send_and_persist(api, context, output, prepared)['notification_status'] == 'provider_accepted'
    _, _, subsequent = prepare(api, tmp_path, identity=101)
    assert subsequent['mail_due'] == 'false' and subsequent['notification_status'] == 'already_accepted'


def test_same_job_notify_twice_cannot_resend_without_receipt(tmp_path):
    api = MailGitHub()
    context, output, prepared = prepare(api, tmp_path)
    upload_prepared(api, 100, output, prepared)
    send_and_persist(api, context, output, prepared, persist=False)
    with pytest.raises(ValueError, match='notification_already_started'):
        reporting.notify(api, plan(), context, output, now('07:05:02'), '', sender=accepted)


@pytest.mark.parametrize('sender', [accepted, lambda *args: {'status': 'delivery_unknown', 'retryable': False,
    'phase': 'data', 'smtp_code': None, 'error_type': 'SMTPServerDisconnected'}])
def test_lost_receipt_after_send_never_automatically_resends(sender, tmp_path):
    api = MailGitHub()
    context, output, prepared = prepare(api, tmp_path)
    upload_prepared(api, 100, output, prepared)
    send_and_persist(api, context, output, prepared, sender, persist=False)
    _, _, following = prepare(api, tmp_path, identity=101)
    assert following['notification_status'] == 'delivery_unknown' and following['mail_due'] == 'false'


def test_persisted_unknown_result_never_gets_retry(tmp_path):
    api = MailGitHub()
    context, output, prepared = prepare(api, tmp_path)
    upload_prepared(api, 100, output, prepared)
    send_and_persist(api, context, output, prepared, lambda *a: {'status': 'delivery_unknown', 'retryable': False,
        'phase': 'data', 'smtp_code': None, 'error_type': 'SMTPServerDisconnected'})
    _, _, result = prepare(api, tmp_path, identity=101)
    assert result['notification_status'] == 'delivery_unknown' and result['mail_due'] == 'false'


def test_missing_configuration_still_persists_a_failed_receipt(tmp_path):
    api = MailGitHub()
    context, output, prepared = prepare(api, tmp_path)
    upload_prepared(api, 100, output, prepared)
    result = send_and_persist(api, context, output, prepared, email.send)
    assert result['notification_status'] == 'definite_nonacceptance'
    receipt = json.loads((output / 'mail-receipt/receipt.json').read_text())
    assert receipt['error_type'] == 'EmailSettingsInvalid'
    assert reporting.audit_stop(api, plan(), context, now('07:05:03'))['stop'] == 'false'


def test_mail_does_not_persist_secret_or_provider_response_fields(tmp_path):
    api = MailGitHub()
    context, output, prepared = prepare(api, tmp_path)
    upload_prepared(api, 100, output, prepared)
    def noisy(*args):
        return {**accepted(*args), 'password': 'must-not-persist', 'provider_text': 'private user@example.test'}
    send_and_persist(api, context, output, prepared, noisy)
    receipt = (output / 'mail-receipt/receipt.json').read_text()
    assert 'must-not-persist' not in receipt and 'example.test' not in receipt and 'provider_text' not in receipt


@pytest.mark.parametrize(('field', 'value', 'reason'), [
    ('payload_hash', '0' * 64, 'receipt_payload_mismatch'),
    ('final_ref', {'name': 'fake', 'hash': '0' * 64}, 'receipt_payload_mismatch'),
    ('smtp_code', 550, 'acceptance_not_proven'),
    ('phase', 'connect', 'acceptance_not_proven'),
])
def test_resealed_wrong_receipt_cannot_authorize_stop(field, value, reason, tmp_path):
    api = MailGitHub()
    context, output, prepared = prepare(api, tmp_path, day='2026-10-27', rows=[day_row(d) for d in reporting.dates(plan())])
    upload_prepared(api, 100, output, prepared)
    send_and_persist(api, context, output, prepared)
    files = {p.name: p.read_bytes() for p in (output / 'mail-receipt').iterdir()}
    manifest = json.loads(files.pop('manifest.json'))
    receipt = json.loads(files['receipt.json']) | {field: value}
    files['receipt.json'] = actions.encoded(receipt)
    files = actions.seal(files, {k: v for k, v in manifest.items() if k not in {'schema_version', 'files'}})
    api.items[100].pop()
    api.upload(100, prepared['mail_receipt_artifact_name'], files)
    with pytest.raises(ValueError, match=reason):
        reporting.audit_stop(api, plan(), context, now('07:05:03', '2026-10-27'))


def test_deleted_notification_intent_blocks_resend_even_without_receipt(tmp_path):
    api = MailGitHub()
    context, output, prepared = prepare(api, tmp_path)
    upload_prepared(api, 100, output, prepared)
    api.items[100].pop()
    api.records[100]['status'] = 'completed'
    api.job_records[100] = [{'steps': [{'name': 'Persist notification intent', 'conclusion': 'success'}]}]
    with pytest.raises(ValueError, match='notification_intent_missing'):
        prepare(api, tmp_path, identity=101)


def test_only_three_definite_negative_delivery_attempts_with_same_payload(tmp_path):
    api = MailGitHub()
    hashes = []
    for identity in range(100, 103):
        context, output, prepared = prepare(api, tmp_path, identity=identity)
        upload_prepared(api, identity, output, prepared)
        hashes.append(json.loads((output / 'notification-state.json').read_text())['intent']['payload_hash'])
        send_and_persist(api, context, output, prepared, rejected)
    _, _, fourth = prepare(api, tmp_path, identity=103)
    assert len(set(hashes)) == 1
    assert fourth['mail_due'] == 'false' and fourth['notification_status'] == 'notification_failed'


def test_nonretryable_rejection_never_gets_second_attempt(tmp_path):
    api = MailGitHub()
    context, output, prepared = prepare(api, tmp_path)
    upload_prepared(api, 100, output, prepared)
    send_and_persist(api, context, output, prepared, lambda *a: {**rejected(*a), 'retryable': False, 'smtp_code': 550})
    _, _, second = prepare(api, tmp_path, identity=101)
    assert second['notification_status'] == 'notification_failed'


def test_notification_ledger_failure_does_not_mean_unsent(tmp_path):
    api = MailGitHub()
    api.fail = 'report_runs'
    with pytest.raises(ValueError, match='synthetic_ledger_api_failure'):
        prepare(api, tmp_path)


def test_d7_missing_produces_35_rows_and_only_final_receipt_allows_stop(tmp_path):
    api = MailGitHub()
    rows = [day_row(day) for day in reporting.dates(plan())]
    context, output, prepared = prepare(api, tmp_path, day='2026-10-27', rows=rows)
    assert prepared['final_bundle_ready'] == 'true'
    daily = list(csv.DictReader(io.StringIO((output / 'final/SOURCE_DAILY.csv').read_text(encoding='utf-8-sig'))))
    assert len(daily) == 35 and all(row['status'] == 'missing' for row in daily)
    observations = json.loads((output / 'final/observations.json').read_text())
    assert observations['novel_events_confirmed'] is None and len(observations['days']) == 7
    upload_prepared(api, 100, output, prepared)
    audit = reporting.audit_stop(api, plan(), context, now('07:05:01', '2026-10-27'))
    assert audit['stop'] == 'false'
    send_and_persist(api, context, output, prepared)
    assert reporting.audit_stop(api, plan(), context, now('07:05:02', '2026-10-27'))['stop'] == 'true'


def test_final_email_cannot_send_when_final_package_not_uploaded(tmp_path):
    api = MailGitHub()
    context, output, prepared = prepare(api, tmp_path, day='2026-10-27', rows=[day_row(d) for d in reporting.dates(plan())])
    upload_prepared(api, 100, output, prepared, include_final=False)
    with pytest.raises(ValueError, match='final_mail_binding_mismatch'):
        reporting.notify(api, plan(), context, output, now('07:05:01', '2026-10-27'), '', sender=accepted)


def test_daily_acceptance_does_not_authorize_final_stop(tmp_path):
    api = MailGitHub()
    context, output, prepared = prepare(api, tmp_path)
    upload_prepared(api, 100, output, prepared)
    send_and_persist(api, context, output, prepared)
    late = signal(api, 101, day='2026-10-27')
    final = reporting.final_files(plan(), [day_row(d) for d in reporting.dates(plan())], {})
    api.upload(101, reporting.name(plan(), 'final'), actions.seal(final, reporting.metadata(plan(), 101, 'final')))
    assert reporting.audit_stop(api, plan(), late, now('07:05:02', '2026-10-27'))['stop'] == 'false'


def test_outage_catchup_combines_original_dates_without_extra_sampling(tmp_path):
    api = MailGitHub()
    rows = [day_row('2026-10-21'), day_row('2026-10-22')]
    context, output, prepared = prepare(api, tmp_path, day='2026-10-22', rows=rows)
    intent = json.loads((output / 'notification-state.json').read_text())['intent']
    assert intent['covered_dates'] == ['2026-10-21', '2026-10-22']
    assert '2026-10-21：missing' in intent['message']['body']
    upload_prepared(api, 100, output, prepared)
    send_and_persist(api, context, output, prepared)
    assert len(api.items[100]) == 3


def test_final_deduplicates_source_urls_and_keeps_daily_vs_retrospective_evidence():
    value = plan()
    rows = [day_row(d) for d in reporting.dates(value)]
    article = {'title': 'OpenAI 發布 AI 模型', 'canonical_url': 'https://cyberq.tw/test-launch',
               'published_at': now('05:00:00').isoformat(), 'summary_if_provided': '公開發布模型',
               'retrieval_status': 'ok', 'filter_reason': None}
    source = {**shadow.SOURCES[1], 'status': 'verified_native_feed', 'articles': [article],
              'feed_results': [{'status': 'valid_feed'}], 'requests': []}
    evidence = {}
    for index, day in enumerate(reporting.dates(value)[:2]):
        capture = {'generated_at': now('06:00:00', day).isoformat(), 'sources': [source]}
        comparison = {'generated_at': now('05:50:00', day).isoformat(), 'items':
                      [{'url': article['canonical_url'], 'title': article['title']}] if index else []}
        report = shadow.evaluate(capture, comparison)
        evidence[day] = {'primary': {'capture.json': actions.encoded(capture), 'baseline.json': actions.encoded(comparison),
                                    'report.json': actions.encoded(report)}}
    files = reporting.final_files(value, rows, evidence)
    reporting.verify_final(value, files)
    events = list(csv.DictReader(io.StringIO(files['EVENT_REVIEW.csv'].decode('utf-8-sig'))))
    assert len(events) == 1 and events[0]['days_seen'] == '2'
    assert events[0]['retrospective_url_seen'] == 'True' and events[0]['manual_decision'] == ''
    comparisons = json.loads(events[0]['daily_comparisons'])
    assert comparisons['2026-10-21'] == 'baseline_window_unverified'
    assert comparisons['2026-10-22'] == 'duplicate_url'
    assert json.loads(files['observations.json'])['novel_events_confirmed'] is None


def test_unknown_previous_day_is_not_blindly_retried_with_today_payload(tmp_path):
    api = MailGitHub()
    context, output, prepared = prepare(api, tmp_path)
    upload_prepared(api, 100, output, prepared)
    send_and_persist(api, context, output, prepared, persist=False)
    _, later_output, _ = prepare(api, tmp_path, identity=101, day='2026-10-22', rows=[day_row('2026-10-21'), day_row('2026-10-22')])
    intent = json.loads((later_output / 'notification-state.json').read_text())['intent']
    assert intent['covered_dates'] == ['2026-10-22']


def test_observation_history_failure_can_be_reported_if_notification_ledger_works(tmp_path):
    api = MailGitHub()
    api.fail = 'runs'
    context = signal(api)
    result = job.reconcile(api, plan(), context, tmp_path, now('07:05:00'))
    row = json.loads((tmp_path / 'reconciliation.json').read_text())['days'][0]
    assert row['status'] == 'unavailable' and result['mail_due'] == 'true'
    assert '證據無法驗證' in json.loads((tmp_path / 'daily-report/message.json').read_text())['subject']


def test_unavailable_notification_ledger_preserves_diagnostic_and_blocks_delivery(tmp_path):
    api = MailGitHub()
    context = signal(api)
    api.fail = 'report_runs'
    result = job.reconcile(api, plan(), context, tmp_path, now('07:05:00'))
    assert result['mode'] == 'blocked' and result['mail_due'] == 'false'
    assert result['reconciliation_ready'] == 'true'
    assert json.loads((tmp_path / 'reconciliation.json').read_text())['notification']['status'] == 'notification_ledger_unavailable_or_unverified'
    assert not (tmp_path / 'mail-intent').exists()


@pytest.mark.parametrize('event', ['workflow_run', 'schedule'])
def test_before_experiment_report_does_not_read_ledger_or_prepare_mail(tmp_path, monkeypatch, event):
    api = MailGitHub()
    day = '2026-10-20'  # The fixture experiment starts on October 21.
    clock = '06:36:00' if event == 'workflow_run' else '07:05:00'
    context = signal(api, day=day, clock=clock)
    if event == 'workflow_run':
        context.update(event_name=event, action='completed', workflow_run={
            'name': actions.WORKFLOWS['observe'][1], 'repository': core.REPOSITORY,
            'branch': 'master', 'event': 'workflow_run', 'id': 99,
            'created_at': now('06:35:00', day).isoformat(),
            'completed_at': now('06:35:30', day).isoformat(),
        })

    def forbidden_ledger(*_):
        raise AssertionError('Pre-start reporting must not query a future ledger range')

    monkeypatch.setattr(api, 'report_runs', forbidden_ledger)
    result = job.reconcile(api, plan(), context, tmp_path, now(clock, day))
    assert result['mode'] == 'reconciled' and result['days_checked'] == 0
    assert result['notification_status'] == 'before_experiment'
    assert result['mail_due'] == result['stop'] == 'false'
    assert json.loads((tmp_path / 'reconciliation.json').read_text())['days'] == []
    assert not (tmp_path / 'mail-intent').exists()
    assert not (tmp_path / 'daily-report').exists()
    assert reporting.audit_stop(api, plan(), context, now(clock, day))['stop'] == 'false'


def test_before_experiment_cannot_accept_fabricated_observation_rows(tmp_path):
    with pytest.raises(ValueError, match='pre_experiment_rows_unexpected'):
        reporting.prepare(MailGitHub(), plan(), {}, tmp_path,
                          now('07:05:00', '2026-10-20'), [day_row()], {})


def test_empty_rows_during_experiment_cannot_bypass_the_notification_ledger(tmp_path):
    with pytest.raises(ValueError, match='in_experiment_rows_missing'):
        reporting.prepare(MailGitHub(), plan(), {}, tmp_path, now('07:05:00'), [], {})


def test_stop_api_failure_stays_failed_and_targets_only_two_experiments(tmp_path):
    import yaml
    root = Path(__file__).resolve().parents[1]
    doc = yaml.safe_load((root / 'docs/examples/tw-source-report.workflow.yml.example').read_text())
    code = doc['jobs']['stop-observation']['steps'][0]['run']
    executable = tmp_path / 'gh'
    log = tmp_path / 'calls'
    executable.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$STOP_TEST_LOG"\ncase "$*" in *tw-source-report.yml/disable*) exit 42;; esac\n')
    executable.chmod(0o700)
    process = subprocess.run(['/bin/bash', '-e', '-o', 'pipefail', '-c', code], capture_output=True, text=True,
        env={**os.environ, 'PATH': str(tmp_path) + os.pathsep + os.environ['PATH'],
             'STOP_TEST_LOG': str(log), 'GITHUB_REPOSITORY': core.REPOSITORY, 'GH_TOKEN': 'synthetic-token'})
    assert process.returncode == 42
    calls = log.read_text().splitlines()
    assert len(calls) == 2 and all('/disable' in call for call in calls)
    assert not any('update-news' in call or 'digest' in call for call in calls)


def test_final_checksum_and_matrix_errors_are_not_silently_accepted():
    value = plan()
    files = reporting.final_files(value, [day_row(d) for d in reporting.dates(value)], {})
    files['SOURCE_DAILY.csv'] = b'changed'
    with pytest.raises(ValueError, match='final_checksum_mismatch'):
        reporting.verify_final(value, files)


@pytest.mark.parametrize('change', [{'provider': None}, {'resend_on_unknown_delivery': True},
                                   {'max_delivery_attempts': 4}, {'send_failure': False}])
def test_notification_policy_cannot_remove_failure_or_unknown_guards(change):
    value = plan()
    value['notification'].update(change)
    with pytest.raises(ValueError):
        reporting.validate_notification(value)


def test_seven_logical_days_end_to_end_produce_seven_emails_and_one_final_stop(tmp_path):
    api = MailGitHub()
    value = plan()
    sent, fetched = [], []
    for index, day in enumerate(reporting.dates(value)):
        identity = index + 10
        api.records[identity] = run(identity, '06:00:00', day=day)
        sample_context = sampler_context(identity, day=day)
        output = tmp_path / f'sample-{day}'
        output.mkdir()
        sampling = job.prepare(api, value, sample_context, output, now('06:00:00', day))
        upload_dir(api, identity, sampling['intent_artifact_name'], output / 'intent')
        baseline_path = tmp_path / 'latest-public-baseline.json'
        baseline_path.write_text(json.dumps({'generated_at': now('05:50:00', day).isoformat(), 'items': []}))
        def collector(source):
            fetched.append((day, source['source_id']))
            return public_source(source)
        job.collect(api, json.loads((output / 'state.json').read_text()), output, baseline_path,
                    lambda: now('06:04:00', day), collector)
        upload_dir(api, identity, sampling['daily_artifact_name'], output / 'bundle')
        api.records[identity]['status'] = 'completed'
        report_context = signal(api, index + 100, day)
        report_output = tmp_path / f'report-{day}'
        report_output.mkdir()
        report = job.reconcile(api, value, report_context, report_output, now('07:05:00', day))
        assert report['mail_due'] == 'true'
        upload_prepared(api, index + 100, report_output, report)
        def sender(payload, config):
            module = SMTPModule()
            result = email.send(payload, smtp_settings(), smtp_module=module)
            sent.append(module.client.raw)
            return result
        result = send_and_persist(api, report_context, report_output, report, sender)
        assert result['notification_status'] == 'provider_accepted'
        audit = reporting.audit_stop(api, value, report_context, now('07:05:03', day))
        assert (audit['stop'] == 'true') is (index == 6)
    assert len(sent) == 7 and len(fetched) == 35
    matrix = list(csv.DictReader(io.StringIO((report_output / 'final/SOURCE_DAILY.csv').read_text(encoding='utf-8-sig'))))
    assert len(matrix) == 35 and all(row['status'] == 'valid_empty' for row in matrix)
    assert all(row['origin_run_id'] and row['origin_artifact_id'] and row['comparison_baseline_at'] for row in matrix)
    assert json.loads((report_output / 'final/observations.json').read_text())['novel_events_confirmed'] is None


def test_notify_cli_missing_settings_exits_failed_but_writes_receipt(tmp_path, monkeypatch):
    api = MailGitHub()
    context, output, prepared = prepare(api, tmp_path)
    upload_prepared(api, 100, output, prepared)
    config = tmp_path / 'plan.json'
    event = tmp_path / 'event.json'
    config.write_text(json.dumps(plan()))
    event.write_text(json.dumps({'repository': {'full_name': core.REPOSITORY}, 'schedule': '5 23 * * *'}))
    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return now('07:05:01')
    monkeypatch.setattr(job, 'datetime', FixedDatetime)
    monkeypatch.setattr(actions, 'GitHub', lambda token: api)
    monkeypatch.setattr(job.subprocess, 'run', lambda *args, **kwargs: type('Result', (), {'stdout': 'a' * 40})())
    monkeypatch.setenv('GITHUB_RUN_ID', '100')
    monkeypatch.setenv('GITHUB_EVENT_NAME', 'schedule')
    monkeypatch.setenv('TW_SOURCE_EMAIL_SETTINGS', '')
    monkeypatch.setenv('GITHUB_OUTPUT', str(tmp_path / 'action-output'))
    monkeypatch.setattr(sys, 'argv', ['observe_tw_sources.py', 'notify', '--plan', str(config),
        '--event-file', str(event), '--output-root', str(output)])
    assert job.main() == 2
    assert (output / 'mail-receipt/receipt.json').exists()
    assert 'notification_status=definite_nonacceptance' in (tmp_path / 'action-output').read_text()


def test_live_cli_rejects_silent_observation_without_email_enabled(tmp_path, monkeypatch):
    config = tmp_path / 'plan.json'
    config.write_text(json.dumps(base_plan()))
    monkeypatch.setattr(sys, 'argv', ['observe_tw_sources.py', 'prepare', '--plan', str(config),
        '--event-file', str(tmp_path / 'not-read'), '--output-root', str(tmp_path / 'not-created')])
    assert job.main() == 2
    assert not (tmp_path / 'not-created').exists()


def test_history_queries_bound_heartbeat_volume_and_keep_manual_catchup():
    api = actions.GitHub('synthetic-token')
    calls = []
    def pages(path, field):
        calls.append(unquote(path))
        return [{'id': 100}] if 'event=workflow_dispatch' not in path else [{'id': 100}, {'id': 101}]
    api.pages = pages
    api.runs('2026-10-21')
    assert '22:00:00' in calls[0] and '22:49:59' in calls[0]
    calls.clear()
    rows = api.report_runs('2026-10-21', '2026-10-27')
    assert len(calls) == 8 and len(rows) == 2
    assert all('22:00:00' in call and '23:19:59' in call for call in calls[:-1])
    assert 'event=workflow_dispatch' in calls[-1]


@pytest.mark.parametrize('end', ['2026-10-20', '2026-11-20', '2027-10-21'])
def test_unverifiable_history_horizon_blocks_without_api_requests(end):
    api = actions.GitHub('synthetic-token')
    def unexpected_api(*args):
        pytest.fail('Out-of-retention history must not issue API requests')
    api.pages = unexpected_api
    with pytest.raises(ValueError, match='history_outside_retention_window'):
        api.report_runs('2026-10-21', end)


def test_last_retained_day_still_queries_full_history_including_manual_runs():
    api = actions.GitHub('synthetic-token')
    calls = []
    api.pages = lambda path, field: calls.append(path) or []
    assert api.report_runs('2026-10-21', '2026-11-19') == []
    assert len(calls) == 31 and 'event=workflow_dispatch' in calls[-1]


def test_primary_failure_before_recovery_waits_instead_of_mailing_twice(tmp_path):
    api = MailGitHub()
    row = day_row(status='partial')
    row['deadline_exceeded'] = False
    _, _, result = prepare(api, tmp_path, rows=[row])
    assert result['mail_due'] == 'false' and result['notification_status'] == 'pending_recovery'


def test_overdue_in_progress_d7_then_explicit_final_correction(tmp_path):
    api = MailGitHub()
    rows = [day_row(d) for d in reporting.dates(plan())]
    rows[-1] = day_row('2026-10-27', status='unmet', ongoing=True)
    context, output, interim = prepare(api, tmp_path, day='2026-10-27', rows=rows)
    assert interim['final_bundle_ready'] == 'false'
    upload_prepared(api, 100, output, interim)
    send_and_persist(api, context, output, interim)
    rows[-1]['collection_state'] = 'partial'
    later_context, later_output, final = prepare(api, tmp_path, identity=101, day='2026-10-27', rows=rows)
    state = json.loads((later_output / 'notification-state.json').read_text())
    assert state['intent']['purpose'] == 'final-correction-1'
    assert '結案更正1' in state['intent']['message']['subject']
    upload_prepared(api, 101, later_output, final)
    send_and_persist(api, later_context, later_output, final)
    assert reporting.audit_stop(api, plan(), later_context, now('07:05:03', '2026-10-27'))['stop'] == 'true'


@pytest.mark.parametrize('targets', [['update-news.yml'], ['tw-source-observation.yml', 'digest-generation.yml']])
def test_stop_gate_never_accepts_production_targets(targets):
    value = plan() | {'self_disable_workflows': targets}
    with pytest.raises(ValueError, match='invalid_stop_targets'):
        reporting.audit_stop(MailGitHub(), value, {}, now('07:05:00', '2026-10-27'))


def test_unsafe_csv_titles_do_not_become_spreadsheet_formulas():
    content = reporting.csv_bytes([{'title': '=HYPERLINK("https://example.test")'}], ['title'])
    row = next(csv.DictReader(io.StringIO(content.decode('utf-8-sig'))))
    assert row['title'].startswith("'=")


def test_workflow_self_stop_has_only_fixed_targets_and_no_checkout():
    import yaml
    root = Path(__file__).resolve().parents[1]
    doc = yaml.safe_load((root / 'docs/examples/tw-source-report.workflow.yml.example').read_text())
    stop = doc['jobs']['stop-observation']
    assert stop['permissions'] == {'actions': 'write'}
    assert all('uses' not in step for step in stop['steps'])
    code = stop['steps'][0]['run']
    assert code.count('gh api --method PUT') == 2
    assert 'tw-source-observation.yml/disable' in code and 'tw-source-report.yml/disable' in code
    assert doc['jobs']['report']['outputs']['stop'] == '${{ steps.audit.outputs.stop }}'


def test_email_secret_is_exposed_only_to_notification_step():
    import yaml
    root = Path(__file__).resolve().parents[1]
    for filename in ('tw-source-observation.workflow.yml.example', 'tw-source-report.workflow.yml.example'):
        document = yaml.safe_load((root / 'docs/examples' / filename).read_text())
        assert document['permissions'] == {}
        for label, task in document['jobs'].items():
            if label != 'stop-observation':
                assert task['permissions'] == {'contents': 'read', 'actions': 'read'}
            for step in task['steps']:
                if 'TW_SOURCE_EMAIL_SETTINGS' in json.dumps(step):
                    assert step['name'] == 'Send daily report'
