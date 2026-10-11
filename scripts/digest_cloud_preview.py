"""C06 loopback-only, synthetic private-digest preview over the C05 service.

This is a local UI adapter, not an authentication or durable cloud service.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
from html import escape
import json
from pathlib import Path
import secrets
from urllib.parse import parse_qs
from uuid import uuid4
from wsgiref.simple_server import make_server

from .digest_cloud_editorial import EditorialError, MockEditorialService, SimulatedPrincipal
from .digest_cloud_mock import (DeliveryRequest, MemoryControl, MemoryObjectStore,
                                MockDeliveryService, MockDeliveryError)
from .digest_cloud_prepare import PinnedInputs, PreparationError, prepare_generation
from .digest_input import INPUT_NAMES
from .digest_window import TAIPEI, window_for_date


ASSETS = Path(__file__).resolve().parents[1] / "private_preview"
MAX_BODY = 1024 * 1024


def _json_bytes(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


class PreviewApp:
    """WSGI boundary with a per-process token and a simulated owner only."""

    def __init__(self, delivery: MockDeliveryService, editorial: MockEditorialService,
                 issue_date: str, *, origin: str, token: str | None = None):
        self.delivery = delivery
        self.editorial = editorial
        self.issue_date = window_for_date(issue_date).date
        self.origin = origin
        self.token = token or secrets.token_urlsafe(32)
        self.principal = SimulatedPrincipal(editorial.owner_id, True)

    @staticmethod
    def _respond(start_response, status, body, content_type, extra=()):
        headers = [("Content-Type", content_type), ("Content-Length", str(len(body))),
                   ("Cache-Control", "no-store"), ("X-Content-Type-Options", "nosniff"),
                   ("Referrer-Policy", "no-referrer"),
                   ("Content-Security-Policy", "default-src 'self'; script-src 'self'; "
                    "style-src 'self'; connect-src 'self'; img-src 'self' data:; "
                    "object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"),
                   *extra]
        start_response(status, headers)
        return [body]

    def _error(self, start_response, status, code, *, current_revision=None):
        value = {"error": code}
        if current_revision is not None:
            value["current_revision"] = current_revision
        return self._respond(start_response, status, _json_bytes(value), "application/json; charset=utf-8")

    @staticmethod
    def _params(query, allowed):
        values = parse_qs(query, keep_blank_values=True, strict_parsing=True)
        if set(values) != allowed or any(len(value) != 1 for value in values.values()):
            raise ValueError("invalid_request")
        return {key: value[0] for key, value in values.items()}

    def _status(self):
        summary = self.delivery.get_issue(self.issue_date)
        state = self.delivery.control.get_issue(self.issue_date)
        bases = []
        seen = set()
        for delivery_id in state["delivery_ids"]:
            row = state["deliveries"][delivery_id]
            identity = row["base_identity"]
            if identity not in seen:
                seen.add(identity)
                bases.append({"base_identity": identity, "quality": row["quality"],
                              "timeliness": row["timeliness"],
                              "revision": state["review_heads"][identity]})
        return {"issue_date": self.issue_date, "selected_base": summary["selected_base"],
                "delivery_count": summary["delivery_count"],
                "meets_daily_target": summary["meets_daily_target"],
                "integrity": summary["integrity"],
                "control_version": summary["control_version"], "bases": bases,
                "synthetic": True, "durable": False}

    def __call__(self, environ, start_response):
        method = environ.get("REQUEST_METHOD", "")
        path = environ.get("PATH_INFO", "")
        expected_host = self.origin.removeprefix("http://")
        if environ.get("HTTP_HOST") != expected_host:
            return self._error(start_response, "403 Forbidden", "forbidden")
        if method == "GET" and path in {"/", "/preview.css", "/preview.js"}:
            name = {"/": "index.html", "/preview.css": "preview.css",
                    "/preview.js": "preview.js"}[path]
            raw = (ASSETS / name).read_bytes()
            if name == "index.html":
                raw = raw.replace(b"{{TOKEN}}", escape(self.token).encode("ascii"))
            kind = "text/html" if name.endswith(".html") else "text/css" if name.endswith(".css") else "text/javascript"
            return self._respond(start_response, "200 OK", raw, f"{kind}; charset=utf-8")
        if not path.startswith("/api/"):
            return self._error(start_response, "404 Not Found", "not_found")
        if environ.get("HTTP_X_PREVIEW_TOKEN") != self.token:
            return self._error(start_response, "403 Forbidden", "forbidden")
        if method == "POST" and environ.get("HTTP_ORIGIN") != self.origin:
            return self._error(start_response, "403 Forbidden", "forbidden")
        try:
            if method == "GET":
                if path == "/api/status" and not environ.get("QUERY_STRING"):
                    result = self._status()
                elif path == "/api/review":
                    params = self._params(environ.get("QUERY_STRING", ""), {"base"})
                    result = self.editorial.read_review(self.principal, self.issue_date, params["base"])
                elif path == "/api/revision":
                    params = self._params(environ.get("QUERY_STRING", ""), {"base", "revision"})
                    result = self.editorial.read_review(self.principal, self.issue_date, params["base"],
                                                        int(params["revision"]))
                elif path == "/api/export":
                    params = self._params(environ.get("QUERY_STRING", ""), {"base", "revision"})
                    exported = self.editorial.export_review(self.principal, self.issue_date,
                                                            params["base"], int(params["revision"]))
                    return self._respond(start_response, "200 OK", exported["bytes"], exported["content_type"],
                                         (("Content-Disposition", f'attachment; filename="{exported["filename"]}"'),
                                          ("X-Content-SHA256", exported["sha256"])))
                else:
                    return self._error(start_response, "404 Not Found", "not_found")
            elif method == "POST" and path in {"/api/edit", "/api/select"}:
                if environ.get("CONTENT_TYPE", "").split(";", 1)[0].lower() != "application/json":
                    raise ValueError("invalid_request")
                size = int(environ.get("CONTENT_LENGTH", "-1"))
                if size < 0 or size > MAX_BODY:
                    return self._error(start_response, "413 Content Too Large", "payload_limit")
                raw = environ["wsgi.input"].read(size)
                if len(raw) != size:
                    raise ValueError("invalid_request")
                if path == "/api/edit":
                    result = self.editorial.apply_edit(self.principal, raw)
                else:
                    result = self.editorial.select_base(self.principal, raw)
            else:
                return self._error(start_response, "404 Not Found", "not_found")
            return self._respond(start_response, "200 OK", _json_bytes(result), "application/json; charset=utf-8")
        except EditorialError as exc:
            status = "409 Conflict" if exc.code in {"revision_conflict", "idempotency_conflict",
                                                      "integrity_error", "base_mismatch"} else (
                "403 Forbidden" if exc.code == "unauthorized" else "400 Bad Request")
            return self._error(start_response, status, exc.code, current_revision=exc.current_revision)
        except (ValueError, TypeError, json.JSONDecodeError):
            return self._error(start_response, "400 Bad Request", "invalid_request")
        except MockDeliveryError as exc:
            return self._error(start_response, "409 Conflict", exc.code)
        except Exception:
            return self._error(start_response, "503 Service Unavailable", "service_unavailable")


def build_synthetic_preview(workspace: Path, issue_date: str, *, origin: str,
                            token: str | None = None) -> PreviewApp:
    """Create two fake corroborated stories. No fetch, private input, or provider call."""
    window = window_for_date(issue_date)
    slot = datetime.combine(window.end_utc.astimezone(TAIPEI).date(),
                            datetime.min.time(), TAIPEI).replace(hour=7, minute=15).astimezone(timezone.utc)
    now = slot + timedelta(minutes=45)
    as_of = slot + timedelta(minutes=30)
    published = window.start_utc + timedelta(hours=12)
    originals = [
        {"id": "synthetic-one", "site_id": "official_ai", "source": "OpenAI News",
         "title": "OpenAI releases new Codex model for developers", "url": "https://example.invalid/synthetic-one",
         "published_at": published.isoformat().replace("+00:00", "Z"),
         "summary": "OpenAI released a new Codex model for developers."},
        {"id": "synthetic-two", "site_id": "curated_media", "source": "Other Publisher",
         "title": "Anthropic releases new Claude model for business", "url": "https://example.invalid/synthetic-two",
         "published_at": (published + timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
         "summary": "Anthropic released a new Claude model for business."},
    ]
    items = originals + [{**row, "id": row["id"] + "-confirm",
                          "source": "Independent Publisher", "site_id": "curated_media" if row["site_id"] == "official_ai" else "official_ai",
                          "url": row["url"] + "/confirm"} for row in originals]
    generated_at = as_of.isoformat().replace("+00:00", "Z")
    content = {"archive.json": _json_bytes({"items": items, "generated_at": generated_at}),
               "title-zh-cache.json": b"{}",
               "source-status.json": _json_bytes({"generated_at": generated_at, "sites": []})}
    commit = "a" * 40
    pinned = PinnedInputs(commit, content,
                          {name: hashlib.sha256(value).hexdigest() for name, value in content.items()},
                          {name: commit for name in INPUT_NAMES})
    intent = {"schema_version": 1, "request_id": str(uuid4()), "issue_date": window.date,
              "mode": "scheduled", "scheduled_for": slot.isoformat().replace("+00:00", "Z"),
              "issued_at": (slot + timedelta(seconds=1)).isoformat().replace("+00:00", "Z"),
              "issuer_id": "synthetic-scheduler", "owner_authorized": False}
    pair = prepare_generation(intent, pinned, lambda: now, workspace,
                              trusted_issuer_ids=frozenset({"synthetic-scheduler"}))
    delivery = MockDeliveryService(MemoryObjectStore(), MemoryControl(lambda: now), workspace)
    delivery.commit_delivery(pair, DeliveryRequest(1, pair.request_id, str(uuid4()), pair.issue_date, 1))
    editorial = MockEditorialService(delivery, owner_id="synthetic-owner")
    return PreviewApp(delivery, editorial, window.date, origin=origin, token=token)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Loopback synthetic digest editorial preview")
    parser.add_argument("--issue-date", default=datetime.now(TAIPEI).date().isoformat())
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--workspace", type=Path,
                        default=Path.home() / "Downloads" / "ai-news-radar-cloud-preview")
    args = parser.parse_args(argv)
    if not 0 <= args.port <= 65535:
        parser.error("port must be 0..65535")
    try:
        with make_server("127.0.0.1", args.port, lambda _e, _s: []) as server:
            origin = f"http://127.0.0.1:{server.server_port}"
            server.set_app(build_synthetic_preview(args.workspace, args.issue_date, origin=origin))
            print(f"Synthetic local preview: {origin}/", flush=True)
            server.serve_forever()
    except KeyboardInterrupt:
        return
    except (PreparationError, MockDeliveryError, ValueError) as exc:
        parser.error(getattr(exc, "code", "invalid_request"))


if __name__ == "__main__":
    main()
