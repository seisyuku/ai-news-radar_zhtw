"""Synthetic desktop authorization; no real Google login or credentials."""

from io import BytesIO
from urllib.parse import parse_qs, urlencode, urlsplit

import pytest

from scripts import digest_drive_desktop_oauth as desktop
from scripts import digest_drive_oauth as oauth


CLIENT = oauth.DeviceClient("synthetic.apps.googleusercontent.com", "SYNTHETIC-SECRET")
SUCCESS = {"access_token": "SYNTHETIC-ACCESS", "refresh_token": "SYNTHETIC-REFRESH",
           "scope": oauth.SCOPE, "token_type": "Bearer"}


def test_login_url_uses_pkce_offline_and_account_selection_without_secret():
    # RFC 7636 example verifies the transformation, not merely its presence.
    verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
    url = desktop.authorization_url(CLIENT, "http://127.0.0.1:1234/", "state", verifier)
    query = parse_qs(urlsplit(url).query)
    assert query["code_challenge"] == ["E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"]
    assert query["code_challenge_method"] == ["S256"]
    assert query["scope"] == [oauth.SCOPE]
    assert query["access_type"] == ["offline"]
    assert query["prompt"] == ["consent select_account"]
    assert query["include_granted_scopes"] == ["false"]
    assert CLIENT.client_secret not in url and verifier not in url


@pytest.mark.parametrize("path", [
    "/?code=PRIVATE", "/?state=wrong&code=PRIVATE", "/other?state=expected&code=PRIVATE",
    "/?state=expected&state=expected&code=PRIVATE", "/?state=expected&code=a&code=b",
    "/?state=expected&code=a&error=access_denied", "/?state=expected&error=PRIVATE",
    "/?state=expected&code=", "https://evil.invalid/?state=expected&code=PRIVATE",
])
def test_unsolicited_malformed_callbacks_do_not_echo_code(path):
    with pytest.raises(oauth.DriveAuthorizationError, match="^invalid_callback$"):
        desktop.callback_result(path, "expected")


def test_callback_accepts_only_state_bound_code_or_denial():
    assert desktop.callback_result("/?state=expected&code=SYNTHETIC", "expected") == {"code": "SYNTHETIC"}
    assert desktop.callback_result("/?state=expected&error=access_denied", "expected") == {"error": "access_denied"}


@pytest.mark.parametrize("patch", [{"scope": oauth.SCOPE + " openid"},
                                   {"scope": "https://www.googleapis.com/auth/drive"},
                                   {"scope": None}, {"refresh_token": None},
                                   {"access_token": None}, {"token_type": "Other"}])
def test_incomplete_or_broad_grants_are_rejected(patch):
    with pytest.raises(oauth.DriveAuthorizationError):
        desktop.exchange_code(CLIENT, "code", "http://127.0.0.1:1234/", "verifier",
                              post=lambda *_: (200, {**SUCCESS, **patch}))


def test_exchange_matches_redirect_pkce_and_saves_no_access_token():
    def post(url, data):
        assert url == oauth.TOKEN_ENDPOINT
        assert data == {"client_id": CLIENT.client_id, "client_secret": CLIENT.client_secret,
                        "code": "code", "redirect_uri": "http://127.0.0.1:1234/",
                        "code_verifier": "verifier", "grant_type": "authorization_code"}
        return 200, SUCCESS
    result = desktop.exchange_code(CLIENT, "code", "http://127.0.0.1:1234/", "verifier", post=post)
    assert result["refresh_token"] == SUCCESS["refresh_token"] and "access_token" not in result
    with pytest.raises(oauth.DriveAuthorizationError, match="^authorization_failed$"):
        desktop.exchange_code(CLIENT, "code", "redirect", "verifier",
                              post=lambda *_: (400, {"error_description": "PRIVATE"}))


def test_loopback_listener_expires_and_closes_without_exchange():
    now, closed, shown = [0], [], []
    class FakeServer:
        server_port = 1234
        def __init__(self, address, handler):
            assert address == ("127.0.0.1", 0)
            assert handler.log_message(None, "PRIVATE") is None
        def handle_request(self):
            now[0] += 901
        def server_close(self):
            closed.append(True)
    with pytest.raises(oauth.DriveAuthorizationError, match="^authorization_expired$"):
        desktop.authorize_desktop(CLIENT, shown.append, clock=lambda: now[0], server_factory=FakeServer,
                                  post=lambda *_: pytest.fail("must not exchange after timeout"))
    assert closed == [True] and len(shown) == 1


def test_cli_requires_live_flag_and_output_is_secret_free(tmp_path, monkeypatch, capsys):
    args = ["--client-file", str(tmp_path / "client.json"), "--output-file", str(tmp_path / "credentials.json")]
    with pytest.raises(SystemExit):
        desktop.main(args)
    capsys.readouterr()
    monkeypatch.setattr(desktop, "load_client", lambda _: CLIENT)
    def authorized(client, show):
        show(desktop.authorization_url(client, "http://127.0.0.1:1234/", "state", "verifier"))
        return {"refresh_token": "SYNTHETIC-REFRESH"}
    monkeypatch.setattr(desktop, "authorize_desktop", authorized)
    assert desktop.main(["--authorize", *args]) == 0
    output = capsys.readouterr().out
    assert "SYNTHETIC-REFRESH" not in output and "SYNTHETIC-SECRET" not in output
    assert "authorized" in output


def test_listener_binding_failure_is_fixed_code():
    def unavailable(*_):
        raise OSError("PRIVATE")
    with pytest.raises(oauth.DriveAuthorizationError, match="^loopback_unavailable$"):
        desktop.authorize_desktop(CLIENT, lambda _: None, server_factory=unavailable)


@pytest.mark.parametrize("denied", [False, True])
def test_callback_handler_ignores_wrong_host_and_state_then_closes(denied):
    shown, responses, closed, calls = [], [], [], []
    class FakeServer:
        server_port = 1234
        def __init__(self, address, handler):
            self.handler, self.step = handler, 0
        def handle_request(self):
            state = parse_qs(urlsplit(shown[0]).query)["state"][0]
            instance = object.__new__(self.handler)
            instance.headers = {"Host": "evil.invalid" if self.step == 0 else "127.0.0.1:1234"}
            query = {"state": "wrong" if self.step == 1 else state}
            query.update({"error": "access_denied"} if denied else {"code": "SYNTHETIC-CODE"})
            instance.path = "/?" + urlencode(query)
            instance.wfile = BytesIO()
            instance.send_response = responses.append
            instance.send_header = lambda *_: None
            instance.end_headers = lambda: None
            instance.do_GET()
            assert b"SYNTHETIC-CODE" not in instance.wfile.getvalue()
            self.step += 1
        def server_close(self):
            closed.append(True)
    def post(url, data):
        calls.append(data)
        assert data["code"] == "SYNTHETIC-CODE"
        return 200, SUCCESS
    if denied:
        with pytest.raises(oauth.DriveAuthorizationError, match="^access_denied$"):
            desktop.authorize_desktop(CLIENT, shown.append, post=post, server_factory=FakeServer)
        assert not calls
    else:
        result = desktop.authorize_desktop(CLIENT, shown.append, post=post, server_factory=FakeServer)
        assert result["refresh_token"] == SUCCESS["refresh_token"] and len(calls) == 1
    assert responses == [400, 400, 200] and closed == [True]
