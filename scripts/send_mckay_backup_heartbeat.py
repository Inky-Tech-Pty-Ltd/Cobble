#!/usr/bin/env python3
"""Daily Cobble backup heartbeat over an existing authenticated SMTP account.

No external calls unless --send or --test-mail is explicitly selected.
Credentials are provisioned interactively to a mode-0600 local file
outside Git and outside the five-directory encrypted backup set.
"""
import argparse
from datetime import datetime
from email.message import EmailMessage
import getpass
import json
import os
from pathlib import Path
import re
import smtplib
import ssl
import stat
import sys
import tempfile


DEFAULT_CONFIG = Path.home() / ".config" / "cobble" / "backup-heartbeat.json"
EMAIL_RE = re.compile(r"^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+$")


def _require_email(value):
    if not isinstance(value, str) or not EMAIL_RE.fullmatch(value):
        raise ValueError("Invalid email address")
    return value


def _write_private(path, value):
    path = Path(path)
    if path.exists() or path.is_symlink():
        raise FileExistsError("Credential configuration already exists; do not overwrite")
    parent = path.parent
    parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    # The directory contains email credentials; reduce accidental exposure.
    parent.chmod(0o700)
    fd, temp = tempfile.mkstemp(prefix=".backup-heartbeat-", dir=parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            os.fchmod(f.fileno(), 0o600)
            f.write(value)
            f.flush()
            os.fsync(f.fileno())
        os.link(temp, path)  # Do not overwrite an existing secret.
    finally:
        Path(temp).unlink(missing_ok=True)


def configure(args):
    if args.config.exists() or args.config.is_symlink():
        raise FileExistsError("Existing heartbeat configuration; refusing to overwrite")
    username = _require_email(args.username)
    sender = _require_email(args.sender)
    recipient = _require_email(args.recipient)
    if not args.smtp_host or not re.fullmatch(r"[a-zA-Z0-9.-]+", args.smtp_host):
        raise ValueError("Invalid SMTP hostname")
    if not 1 <= args.smtp_port <= 65535:
        raise ValueError("Invalid SMTP port")
    password = getpass.getpass("SMTP password (hidden; paste from 1Password): ")
    if not password:
        raise ValueError("Empty SMTP password")
    secret_path = args.config.with_suffix(".password")
    _write_private(secret_path, password)
    # Restrict this file even though its contents are not secret.
    _write_private(args.config, json.dumps({
        "smtp_host": args.smtp_host,
        "smtp_port": args.smtp_port,
        "username": username,
        "sender": sender,
        "recipient": recipient,
        "password_file": str(secret_path),
    }, indent=2) + "\n")
    print("Configured: credentials stored privately on McKay; no email sent")


def _read_private(path):
    path = Path(path)
    if path.is_symlink():
        raise PermissionError("Heartbeat credentials must not be symlinks")
    metadata = path.stat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_mode & 0o077:
        raise PermissionError("Heartbeat credential file must be regular and mode 0600")
    return path.read_text(encoding="utf-8")


def load_config(path):
    cfg = json.loads(_read_private(path))
    if not isinstance(cfg, dict) or set(cfg) != {
        "smtp_host", "smtp_port", "username", "sender", "recipient", "password_file"
    }:
        raise ValueError("Unexpected heartbeat configuration")
    for k in ("username", "sender", "recipient"):
        _require_email(cfg[k])
    if not isinstance(cfg["smtp_host"], str) or not re.fullmatch(r"[a-zA-Z0-9.-]+", cfg["smtp_host"]):
        raise ValueError("Invalid SMTP hostname")
    if not isinstance(cfg["smtp_port"], int) or not 1 <= cfg["smtp_port"] <= 65535:
        raise ValueError("Invalid SMTP port")
    secret = Path(cfg["password_file"])
    if not secret.is_absolute() or secret.parent != path.parent:
        raise ValueError("Password file must be next to the private configuration")
    cfg["password"] = _read_private(secret)
    return cfg


def report_summary(report_path, today, forced_warning=None):
    """Never include private corpus contents or SMTP credentials in email."""
    alerts = []
    state = "UNKNOWN"
    checked = "not available"
    total = 0
    try:
        report = json.loads(Path(report_path).read_text(encoding="utf-8-sig"))
        if not isinstance(report, dict):
            raise ValueError("Unexpected report format")
        state = report.get("status", "UNKNOWN")
        checked = report.get("checked_at_local", "not available")
        if not isinstance(checked, str) or checked[:10] != today:
            alerts.append("Watchdog report is missing or stale for today's check")
        original = report.get("alerts", [])
        if not isinstance(original, list) or any(not isinstance(a, str) for a in original):
            raise ValueError("Invalid watchdog alerts")
        # Keep email compact and prevent unexpected long/private contents.
        alerts.extend(a[:150] for a in original[:40])
        archives = report.get("archives", [])
        if not isinstance(archives, list):
            raise ValueError("Invalid archive list")
        total = len(archives)
        if state != "OK_LOCAL_AND_PROVIDER_SYNC":
            if not alerts:
                alerts.append("Watchdog reported non-healthy status")
        if state == "OK_LOCAL_AND_PROVIDER_SYNC" and original:
            alerts.append("Watchdog status contradicts its alert list")
    except (OSError, ValueError, TypeError, UnicodeError):
        alerts.append("Watchdog report missing, unreadable or malformed")
    if forced_warning:
        alerts.append("Watchdog process error or unexpected exit")
    health = "WARNING" if alerts else "OK"
    subject = f"Cobble backup: {health} | {today}"
    lines = [
        "Cobble nightly backup heartbeat",
        f"Date: {today}",
        f"Health: {health}",
        f"Windows watchdog status: {state}",
        f"Watchdog checked: {checked}",
        f"Archive records inspected: {total}",
        "",
        "Windows sync-provider status is NOT independent verification",
        "that a backup can be downloaded or decrypted off McKay.",
    ]
    if alerts:
        lines += ["", "Warnings:", *(f"- {a}" for a in alerts)]
    else:
        lines += ["", "No warnings from the local backup and iCloud provider checks."]
    lines += [
        "",
        "Missing a daily heartbeat is itself a reason to investigate.",
        "This message contains no corpus contents or credentials.",
    ]
    return health, subject, "\n".join(lines) + "\n"


def send_mail(config, subject, body):
    message = EmailMessage()
    message["From"] = config["sender"]
    message["To"] = config["recipient"]
    message["Subject"] = subject
    message.set_content(body)
    with smtplib.SMTP_SSL(
        config["smtp_host"], config["smtp_port"],
        context=ssl.create_default_context(), timeout=25,
    ) as server:
        server.login(config["username"], config["password"])
        refused = server.send_message(message)
        if refused:
            raise RuntimeError("SMTP recipient refused")
    # Accepted for delivery by SMTP is not proof of arrival in the inbox.
    print("Heartbeat accepted by SMTP server; inbox delivery unverified")


def self_test():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        report = Path(d) / "latest.json"
        today = "2026-11-27"
        report.write_text(json.dumps({
            "status": "OK_LOCAL_AND_PROVIDER_SYNC",
            "checked_at_local": today + "T09:00:00+11:00",
            "alerts": [], "archives": [{}, {}],
        }), encoding="utf-8")
        assert report_summary(report, today)[0] == "OK"
        report.write_text(json.dumps({
            "status": "WARNING",
            "checked_at_local": today + "T09:00:00+11:00",
            "alerts": ["Cloud delivery unconfirmed"], "archives": [],
        }), encoding="utf-8")
        assert report_summary(report, today)[0] == "WARNING"
        assert report_summary(report, "2026-11-28")[0] == "WARNING"
        assert report_summary(report, today, forced_warning=True)[0] == "WARNING"
        report.unlink()
        assert report_summary(report, today)[0] == "WARNING"
    print("BACKUP EMAIL SELF-TEST PASS: healthy, warning, stale, forced error, missing")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--setup", action="store_true")
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--test-mail", action="store_true")
    mode.add_argument("--send", action="store_true")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--smtp-host")
    parser.add_argument("--smtp-port", type=int, default=465)
    parser.add_argument("--username")
    parser.add_argument("--sender")
    parser.add_argument("--recipient")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--watchdog-error", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if args.setup:
        if not all((args.smtp_host, args.username, args.sender, args.recipient)):
            parser.error("--setup requires --smtp-host, --username, --sender and --recipient")
        configure(args)
        return
    cfg = load_config(args.config)
    if args.test_mail:
        subject = "Cobble backup: TEST heartbeat"
        body = "This is a one-off email delivery test. No backup archives were accessed.\n"
    else:
        if args.report is None:
            parser.error("--send requires --report")
        _, subject, body = report_summary(
            args.report, datetime.now().astimezone().date().isoformat(),
            forced_warning=args.watchdog_error,
        )
    send_mail(cfg, subject, body)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Never echo a credential, mail body or provider exception message.
        print(f"BACKUP HEARTBEAT ERROR: {type(exc).__name__}", file=sys.stderr)
        sys.exit(3)
