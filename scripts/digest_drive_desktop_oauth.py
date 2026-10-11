"""One-time desktop OAuth: PKCE, loopback only, no automatic browser launch.

Only drive.file is requested. Codes and tokens never appear in console output.
No Drive writes, GitHub secrets or schedules are changed by this helper.
"""

import argparse
import base64
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import secrets
import time
from urllib.parse import parse_qs, urlencode, urlsplit

try:
    from .digest_drive_oauth import (
        DriveAuthorizationError, SCOPE, TOKEN_ENDPOINT, _post, _secret,
        credential_path, google_post, load_client, save_credentials,
    )
except ImportError:
    from digest_drive_oauth import (
        DriveAuthorizationError, SCOPE, TOKEN_ENDPOINT, _post, _secret,
        credential_path, google_post, load_client, save_credentials,
    )


AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"


def authorization_url(client, redirect_uri, state, verifier):
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode("ascii")).digest()
    ).rstrip(b"=").decode("ascii")
    return AUTH_ENDPOINT + "?" + urlencode({
        "client_id": client.client_id, "redirect_uri": redirect_uri,
        "response_type": "code", "scope": SCOPE, "state": state,
        "code_challenge": challenge, "code_challenge_method": "S256",
        "access_type": "offline", "prompt": "consent select_account",
        "include_granted_scopes": "false",
    })


def callback_result(path, state):
    """Ignore unsolicited callbacks; accept only one state-bound code or denial."""
    try:
        parts = urlsplit(path)
        if len(path) > 8192 or parts.path != "/" or parts.scheme or parts.netloc or parts.fragment:
            raise ValueError()
        query = parse_qs(parts.query, keep_blank_values=True, max_num_fields=20)
        received = query.get("state", [])
        if len(received) != 1 or not secrets.compare_digest(received[0], state):
            raise ValueError()
        code, error = query.get("code", []), query.get("error", [])
        if error == ["access_denied"] and not code:
            return {"error": "access_denied"}
        if len(code) != 1 or error:
            raise ValueError()
        return {"code": _secret(code[0])}
    except Exception:
        raise DriveAuthorizationError("invalid_callback") from None


def exchange_code(client, code, redirect_uri, verifier, *, post=google_post):
    status, result = _post(post, TOKEN_ENDPOINT, {
        "client_id": client.client_id, "client_secret": client.client_secret,
        "code": code, "redirect_uri": redirect_uri, "code_verifier": verifier,
        "grant_type": "authorization_code",
    })
    if status != 200:
        raise DriveAuthorizationError("authorization_failed")
    scope = result.get("scope")
    if (not isinstance(scope, str) or set(scope.split()) != {SCOPE}
            or result.get("token_type") != "Bearer"):
        raise DriveAuthorizationError("unexpected_grant")
    _secret(result.get("access_token"))
    return {"client_id": client.client_id, "client_secret": client.client_secret,
            "refresh_token": _secret(result.get("refresh_token")),
            "scope": SCOPE, "token_type": "Bearer"}


def authorize_desktop(client, show_url, *, post=google_post,
                      clock=time.monotonic, server_factory=HTTPServer):
    state, verifier = secrets.token_urlsafe(32), secrets.token_urlsafe(64)
    result = []
    host = []

    class CallbackHandler(BaseHTTPRequestHandler):
        def setup(self):
            self.request.settimeout(2)
            super().setup()

        def log_message(self, *args):
            pass  # Default HTTP logging would expose the authorization code.

        def do_GET(self):
            try:
                if self.headers.get("Host") != host[0]:
                    raise DriveAuthorizationError("invalid_callback")
                value = callback_result(self.path, state)
            except DriveAuthorizationError:
                self.send_response(400)
                body = b"Invalid authorization response. Return to the Google login page."
            else:
                result.append(value)
                self.send_response(200)
                body = b"Response received. Return to Codex to check the final authorization result."
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Connection", "close")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    try:
        server = server_factory(("127.0.0.1", 0), CallbackHandler)
    except OSError:
        raise DriveAuthorizationError("loopback_unavailable") from None
    try:
        host.append("127.0.0.1:" + str(server.server_port))
        redirect_uri = "http://" + host[0] + "/"
        server.timeout = 1
        deadline = clock() + 900
        show_url(authorization_url(client, redirect_uri, state, verifier))
        while not result:
            if clock() >= deadline:
                raise DriveAuthorizationError("authorization_expired")
            server.handle_request()
        if clock() >= deadline:
            raise DriveAuthorizationError("authorization_expired")
    finally:
        server.server_close()
    if "error" in result[0]:
        raise DriveAuthorizationError("access_denied")
    return exchange_code(client, result[0]["code"], redirect_uri, verifier, post=post)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Authorize Drive using a browser on this Mac.")
    parser.add_argument("--authorize", action="store_true", required=True)
    parser.add_argument("--client-file", type=Path, required=True)
    parser.add_argument("--output-file", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        destination = credential_path(args.output_file)
        client = load_client(args.client_file)
        credentials = authorize_desktop(client, lambda url: print(
            json.dumps({"status": "awaiting_user", "authorization_url": url,
                        "open_on_same_mac": True, "expires_in_seconds": 900}), flush=True))
        save_credentials(destination, credentials)
    except DriveAuthorizationError as exc:
        print(json.dumps({"status": "failed", "reason": exc.code}), flush=True)
        return 1
    except KeyboardInterrupt:
        print(json.dumps({"status": "cancelled"}), flush=True)
        return 1
    except Exception:
        print(json.dumps({"status": "failed", "reason": "authorization_unavailable"}), flush=True)
        return 1
    print(json.dumps({"status": "authorized", "credentials_saved": True}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
