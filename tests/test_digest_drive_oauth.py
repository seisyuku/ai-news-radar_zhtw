"""No live credentials: bounded device flow, least privilege and private saves."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import digest_drive_oauth as oauth


CLIENT = oauth.DeviceClient("synthetic.apps.googleusercontent.com", "SYNTHETIC-SECRET")
START = {"device_code": "SYNTHETIC-PRIVATE-DEVICE", "user_code": "SAMPLE-CODE",
         "verification_url": "https://www.google.com/device", "expires_in": 1800, "interval": 5}
SUCCESS = {"access_token": "SYNTHETIC-ACCESS", "refresh_token": "SYNTHETIC-REFRESH",
           "scope": oauth.SCOPE, "token_type": "Bearer"}


def flow(responses, start=None):
    now, waits, requests, shown = [0], [], [], []
    responses = iter([(200, dict(START if start is None else start)), *responses])
    def post(url, data):
        requests.append((now[0], url, data))
        return next(responses)
    def sleep(seconds):
        waits.append(seconds)
        now[0] += seconds
    return lambda: oauth.authorize(CLIENT, shown.append, post=post, clock=lambda: now[0], sleep=sleep), waits, requests, shown


def test_phone_code_is_only_displayed_data_and_polling_backs_off():
    run, waits, calls, shown = flow([(428, {"error": "authorization_pending"}),
                                   (403, {"error": "slow_down"}), (200, SUCCESS)])
    credentials = run()
    assert waits == [5, 5, 10] and [r[0] for r in calls] == [0, 5, 10, 20]
    assert calls[0][2] == {"client_id": CLIENT.client_id, "scope": oauth.SCOPE}
    assert all(r[1] == oauth.TOKEN_ENDPOINT and r[2]["client_secret"] == CLIENT.client_secret for r in calls[1:])
    assert shown == [{"verification_url": START["verification_url"], "user_code": START["user_code"]}]
    assert "PRIVATE" not in json.dumps(shown) and "SECRET" not in repr(CLIENT)
    assert credentials["refresh_token"] == SUCCESS["refresh_token"] and "access_token" not in credentials


@pytest.mark.parametrize("error,code", [("access_denied", "access_denied"),
                                     ("expired_token", "authorization_expired"),
                                     ("invalid_client", "invalid_client"),
                                     ("invalid_scope", "invalid_scope"),
                                     ("PRIVATE-payload", "authorization_failed")])
def test_denial_and_errors_never_echo_descriptions(error, code):
    run, *_ = flow([(400, {"error": error, "error_description": "PRIVATE token and draft"})])
    with pytest.raises(oauth.DriveAuthorizationError, match="^" + code + "$"):
        run()


@pytest.mark.parametrize("error", [None, {"PRIVATE": "token"}, ["PRIVATE"]])
def test_malformed_provider_error_has_fixed_failure(error):
    run, *_ = flow([(400, {"error": error})])
    with pytest.raises(oauth.DriveAuthorizationError, match="^authorization_failed$"):
        run()


def test_expiry_and_provider_interval_bound_polling():
    run, waits, calls, shown = flow([(428, {"error": "authorization_pending"})], {**START, "expires_in": 11, "interval": 6})
    with pytest.raises(oauth.DriveAuthorizationError, match="authorization_expired"):
        run()
    assert waits == [6] and len(calls) == 2
    run, waits, *_ = flow([(200, SUCCESS)], {**START, "interval": 1})
    run()
    assert waits == [5]


@pytest.mark.parametrize("patch", [{"expires_in": True}, {"interval": 0}, {"device_code": None},
                                   {"verification_url": "http://www.google.com/device"},
                                   {"verification_url": "https://google.com.evil.invalid/device"},
                                   {"verification_url": "https://user:secret@www.google.com/device"}])
def test_invalid_device_response_rejected_before_any_poll(patch):
    run, waits, calls, shown = flow([], {**START, **patch})
    with pytest.raises(oauth.DriveAuthorizationError, match="invalid_response"):
        run()
    assert len(calls) == 1 and not waits and not shown


@pytest.mark.parametrize("patch", [{"scope": "https://www.googleapis.com/auth/drive"},
                                   {"scope": oauth.SCOPE + " openid"}, {"scope": None},
                                   {"refresh_token": None}, {"token_type": "Other"}])
def test_broad_or_incomplete_grant_is_not_saved(patch):
    run, *_ = flow([(200, {**SUCCESS, **patch})])
    with pytest.raises(oauth.DriveAuthorizationError):
        run()


def test_credentials_remain_private_and_do_not_replace_previous(tmp_path):
    target = tmp_path / "private" / "credentials.json"
    oauth.save_credentials(target, {"refresh_token": "SYNTHETIC-REFRESH"})
    assert target.stat().st_mode & 0o077 == 0 and target.parent.stat().st_mode & 0o077 == 0
    with pytest.raises(oauth.DriveAuthorizationError, match="invalid_credential_destination"):
        oauth.save_credentials(target, {"refresh_token": "changed"})
    assert json.loads(target.read_text())["refresh_token"] == "SYNTHETIC-REFRESH"
    with pytest.raises(oauth.DriveAuthorizationError, match="invalid_credential_destination"):
        oauth.credential_path(Path.cwd() / "credentials.json")


def test_client_file_uses_only_id_secret_not_supplied_endpoints(tmp_path):
    target = tmp_path / "client.json"
    target.write_text(json.dumps({"installed": {"client_id": CLIENT.client_id,
                       "client_secret": CLIENT.client_secret, "token_uri": "https://evil.invalid"}}))
    assert oauth.load_client(target) == CLIENT
    target.write_text('{"web":{"client_id":"PRIVATE"}}')
    with pytest.raises(oauth.DriveAuthorizationError, match="^invalid_client_file$"):
        oauth.load_client(target)


def test_http_has_fixed_google_targets_no_redirects_or_error_echo(monkeypatch):
    def post(url, **kwargs):
        assert url == oauth.DEVICE_ENDPOINT
        assert kwargs["allow_redirects"] is False and kwargs["timeout"] == (10, 30)
        return SimpleNamespace(status_code=403, content=b"{}", json=lambda: {"error": "access_denied"})
    monkeypatch.setattr(oauth.requests, "post", post)
    assert oauth.google_post(oauth.DEVICE_ENDPOINT, {}) == (403, {"error": "access_denied"})
    with pytest.raises(oauth.DriveAuthorizationError, match="invalid_endpoint"):
        oauth.google_post("https://evil.invalid", {})
    monkeypatch.setattr(oauth.requests, "post", lambda *a, **k: (_ for _ in ()).throw(OSError("PRIVATE secret")))
    with pytest.raises(oauth.DriveAuthorizationError, match="^authorization_unavailable$"):
        oauth.google_post(oauth.DEVICE_ENDPOINT, {})


def test_cli_requires_explicit_live_flag_and_never_logs_credentials(tmp_path, monkeypatch, capsys):
    args = ["--client-file", str(tmp_path / "client.json"), "--output-file", str(tmp_path / "credentials.json")]
    with pytest.raises(SystemExit):
        oauth.main(args)
    capsys.readouterr()
    monkeypatch.setattr(oauth, "load_client", lambda _: CLIENT)
    def authorized(client, show):
        show({"verification_url": START["verification_url"], "user_code": START["user_code"]})
        return {"refresh_token": SUCCESS["refresh_token"]}
    monkeypatch.setattr(oauth, "authorize", authorized)
    assert oauth.main(["--authorize", *args]) == 0
    printed = capsys.readouterr().out
    assert "SYNTHETIC-REFRESH" not in printed and "SYNTHETIC-SECRET" not in printed
    assert "authorized" in printed
