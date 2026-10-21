"""Single-recipient TLS SMTP adapter. Never logs configuration or server text.

Only a definite negative response permits retry after DATA. Disconnects during
DATA are ambiguous, even when no acceptance receipt could be saved locally.
"""
from __future__ import annotations

from email.headerregistry import Address
from email.message import EmailMessage
import json
import re
import smtplib
import ssl


def settings(raw):
    try:
        config = json.loads(raw)
        if config.get("provider") != "smtp" or config.get("tls") not in {"ssl", "starttls"}:
            raise ValueError
        if (type(config.get("port")) is not int or config["port"] != (465 if config["tls"] == "ssl" else 587)
                or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9.-]{1,251}[a-zA-Z0-9]", config.get("host", ""))):
            raise ValueError
        for key in ("username", "password", "from", "to"):
            if not isinstance(config.get(key), str) or not config[key] or any(c in config[key] for c in "\r\n\x00"):
                raise ValueError
        for key in ("from", "to"):
            mailbox = Address(addr_spec=config[key])
            if not mailbox.username or not mailbox.domain or mailbox.addr_spec != config[key] or not config[key].isascii():
                raise ValueError
        return config
    except (ValueError, TypeError, KeyError, AttributeError):
        raise ValueError("email_settings_missing_or_invalid") from None


def send(payload, raw_settings, *, smtp_module=smtplib):
    """Return sanitized acceptance evidence; never return addresses/SMTP text."""
    phase, client = "config", None
    accepted = False
    try:
        config = settings(raw_settings)
        message = EmailMessage()
        message["From"], message["To"] = config["from"], config["to"]
        message["Subject"] = payload["subject"]
        message["Message-ID"] = f"<twso-{payload['payload_hash']}@radar.invalid>"
        message.set_content(payload["body"])
        tls = ssl.create_default_context()
        phase = "connect"
        if config["tls"] == "ssl":
            client = smtp_module.SMTP_SSL(config["host"], config["port"], timeout=20, context=tls)
        else:
            client = smtp_module.SMTP(config["host"], config["port"], timeout=20)
        phase = "tls"
        client.ehlo()
        if config["tls"] == "starttls":
            client.starttls(context=tls)
            client.ehlo()
        phase = "auth"
        client.login(config["username"], config["password"])
        phase = "envelope"
        for operation, address in ((client.mail, config["from"]), (client.rcpt, config["to"])):
            code, _ = operation(address)
            if not 200 <= code < 300:
                return rejection(phase, "SMTPEnvelopeRejected", code)
        phase = "data"
        code, _ = client.data(message.as_bytes(policy=message.policy.clone(linesep="\r\n")))
        if code == 250:
            accepted = True
            return {"status": "provider_accepted", "retryable": False, "phase": phase, "smtp_code": code, "error_type": None}
        if 400 <= code < 600:
            return rejection(phase, "SMTPDataRejected", code)
        return {"status": "delivery_unknown", "retryable": False, "phase": phase, "smtp_code": None, "error_type": "UnexpectedSMTPReply"}
    except smtplib.SMTPResponseException as error:
        if 400 <= error.smtp_code < 600:
            return rejection(phase, type(error).__name__, error.smtp_code)
        return {"status": "delivery_unknown" if phase == "data" else "definite_nonacceptance",
                "retryable": False, "phase": phase, "smtp_code": None, "error_type": type(error).__name__}
    except (OSError, smtplib.SMTPException, ValueError, TypeError, KeyError) as error:
        ambiguous = phase == "data"
        retry = not ambiguous and phase != "config" and not isinstance(error, (ssl.SSLCertVerificationError, smtplib.SMTPNotSupportedError))
        return {"status": "delivery_unknown" if ambiguous else "definite_nonacceptance", "retryable": retry,
                "phase": phase, "smtp_code": None,
                "error_type": "EmailSettingsInvalid" if phase == "config" else type(error).__name__}
    finally:
        if client is not None:
            try:
                # QUIT failure after DATA acceptance must not erase acceptance.
                client.quit() if accepted else client.close()
            except (OSError, smtplib.SMTPException):
                pass


def rejection(phase, name, code):
    return {"status": "definite_nonacceptance", "retryable": 400 <= code < 500,
            "phase": phase, "smtp_code": code, "error_type": name}
