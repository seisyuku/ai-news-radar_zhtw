"""One-time phone authorization for a headless, Drive-file-only client.

No Drive writes, GitHub updates or browser callback server. Live authorization
requires an explicit CLI flag and a user-provided Google device-client file.
"""

import argparse
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import re
import time
from urllib.parse import urlsplit

import requests


SCOPE = "https://www.googleapis.com/auth/drive.file"
DEVICE_ENDPOINT = "https://oauth2.googleapis.com/device/code"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
CLIENT_ID = re.compile(r"[A-Za-z0-9_.-]+\.apps\.googleusercontent\.com\Z")


class DriveAuthorizationError(ValueError):
    """Fixed codes only; provider descriptions and credentials never escape."""

    def __init__(self, code):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class DeviceClient:
    client_id: str = field(repr=False)
    client_secret: str = field(repr=False)


def _secret(value):
    if not isinstance(value, str) or not value or len(value) > 16384 or not value.isprintable():
        raise DriveAuthorizationError("invalid_response")
    return value


def load_client(path):
    try:
        path = Path(path)
        if path.stat().st_size > 65536:
            raise ValueError()
        raw = json.loads(path.read_text(encoding="utf-8"))
        data = raw["installed"]
        if not CLIENT_ID.fullmatch(data["client_id"]):
            raise ValueError()
        return DeviceClient(data["client_id"], _secret(data["client_secret"]))
    except Exception:
        raise DriveAuthorizationError("invalid_client_file") from None


def google_post(url, data):
    if url not in {DEVICE_ENDPOINT, TOKEN_ENDPOINT}:
        raise DriveAuthorizationError("invalid_endpoint")
    try:
        response = requests.post(url, data=data, timeout=(10, 30), allow_redirects=False)
        if len(response.content) > 65536:
            raise ValueError()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError()
        return response.status_code, payload
    except Exception:
        raise DriveAuthorizationError("authorization_unavailable") from None


def _post(post, url, data):
    try:
        status, payload = post(url, data)
        if type(status) is not int or not isinstance(payload, dict):
            raise ValueError()
        return status, payload
    except DriveAuthorizationError:
        raise
    except Exception:
        raise DriveAuthorizationError("authorization_unavailable") from None


def _verification_url(value):
    try:
        parts = urlsplit(value)
        if (not isinstance(value, str) or not value.isascii() or not value.isprintable()
                or len(value) > 2048 or any(c in value for c in '[]<>"`')
                or parts.scheme != "https" or parts.hostname not in
                {"google.com", "www.google.com", "accounts.google.com"}
                or parts.username or parts.password or parts.port not in {None, 443}):
            raise ValueError()
    except Exception:
        raise DriveAuthorizationError("invalid_response") from None
    return value  # Preserve Google's returned URL; do not manufacture a login link.


def authorize(client, show_code, *, post=google_post, clock=time.monotonic, sleep=time.sleep):
    if (not isinstance(client, DeviceClient) or not isinstance(client.client_id, str)
            or not CLIENT_ID.fullmatch(client.client_id)):
        raise DriveAuthorizationError("invalid_client_file")
    _secret(client.client_secret)
    start = clock()
    status, data = _post(post, DEVICE_ENDPOINT, {"client_id": client.client_id, "scope": SCOPE})
    if status != 200:
        raise DriveAuthorizationError("device_request_failed")
    device_code = _secret(data.get("device_code"))
    user_code = _secret(data.get("user_code"))
    if not user_code.isascii() or len(user_code) > 64:
        raise DriveAuthorizationError("invalid_response")
    url = _verification_url(data.get("verification_url", data.get("verification_uri")))
    expires, interval = data.get("expires_in"), data.get("interval")
    if type(expires) is not int or expires <= 0 or type(interval) is not int or interval <= 0:
        raise DriveAuthorizationError("invalid_response")
    deadline = start + min(expires, 1800)
    interval = max(interval, 5)
    show_code({"verification_url": url, "user_code": user_code})
    while True:
        remaining = deadline - clock()
        if remaining <= interval:
            raise DriveAuthorizationError("authorization_expired")
        sleep(interval)
        if clock() >= deadline:
            raise DriveAuthorizationError("authorization_expired")
        status, result = _post(post, TOKEN_ENDPOINT, {
            "client_id": client.client_id, "client_secret": client.client_secret,
            "device_code": device_code, "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        })
        if clock() >= deadline:
            raise DriveAuthorizationError("authorization_expired")
        if status == 200:
            scope = result.get("scope")
            if (not isinstance(scope, str) or set(scope.split()) != {SCOPE}
                    or result.get("token_type") != "Bearer"):
                raise DriveAuthorizationError("unexpected_grant")
            _secret(result.get("access_token"))
            token = _secret(result.get("refresh_token"))
            return {"client_id": client.client_id, "client_secret": client.client_secret,
                    "refresh_token": token, "scope": SCOPE, "token_type": "Bearer"}
        error = result.get("error")
        if not isinstance(error, str):
            raise DriveAuthorizationError("authorization_failed")
        if error == "authorization_pending" and status in {400, 428}:
            continue
        if error == "slow_down" and status in {400, 403, 429}:
            interval += 5
            continue
        if error in {"access_denied", "expired_token", "invalid_client", "invalid_scope"}:
            raise DriveAuthorizationError({"expired_token": "authorization_expired"}.get(error, error))
        raise DriveAuthorizationError("authorization_failed")


def credential_path(path):
    path = Path(path).resolve()
    if (Path.home() / "Downloads").resolve() not in path.parents or path.exists():
        raise DriveAuthorizationError("invalid_credential_destination")
    return path


def save_credentials(path, credentials):
    path = credential_path(path)
    raw = (json.dumps(credentials, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError:
        raise DriveAuthorizationError("credential_save_failed") from None
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        path.unlink(missing_ok=True)  # Only this newly created credential file.
        raise DriveAuthorizationError("credential_save_failed") from None


def main(argv=None):
    parser = argparse.ArgumentParser(description="Authorize the private Drive project using an iPhone browser.")
    parser.add_argument("--authorize", action="store_true", required=True)
    parser.add_argument("--client-file", type=Path, required=True)
    parser.add_argument("--output-file", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        destination = credential_path(args.output_file)
        client = load_client(args.client_file)
        # Only the intended user code and Google's verification URL are displayed.
        credentials = authorize(client, lambda code: print(json.dumps(code), flush=True))
        save_credentials(destination, credentials)
    except DriveAuthorizationError as exc:
        print(json.dumps({"status": "failed", "reason": exc.code}))
        return 1
    except KeyboardInterrupt:
        print(json.dumps({"status": "cancelled"}))
        return 1
    print(json.dumps({"status": "authorized", "credentials_saved": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
