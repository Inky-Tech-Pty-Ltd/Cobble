"""Private read-only McKay connectivity monitor (Python standard library only).

A sample separates physical-router reachability, wider HTTPS reachability,
OpenAI HTTPS reachability, and Cobble tunnel control-plane health.
The router's *Windows* default gateway is used, not WSL's virtual NAT gateway.
No API keys, prompts, or response bodies are recorded.
"""
import argparse
from contextlib import closing
from datetime import datetime, timedelta, timezone
import ipaddress
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_DB = Path.home() / "cobble-data" / "monitoring" / "network.sqlite3"
WINDOWS_GATEWAY_COMMAND = (
    '$n = Get-NetIPConfiguration | Where-Object { '
    '$_.IPv4DefaultGateway -and $_.NetAdapter.Status -eq "Up" } | '
    'Sort-Object { if ($_.InterfaceAlias -match "Ethernet") { 0 } else { 1 } } | '
    'Select-Object -First 1; '
    'if ($n) { $n.IPv4DefaultGateway[0].NextHop }'
)


def windows_router_gateway():
    """Find the actual LAN gateway, avoiding WSL's virtual gateway."""
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
             WINDOWS_GATEWAY_COMMAND], capture_output=True, text=True, timeout=12,
            check=False,
        )
        candidate = result.stdout.strip().splitlines()[0].strip()
        addr = ipaddress.ip_address(candidate)
        return str(addr) if addr.version == 4 and addr.is_private else None
    except (OSError, ValueError, IndexError, subprocess.TimeoutExpired):
        return None


def router_probe(gateway):
    if not gateway or not shutil.which("ping"):
        return None, None
    started = time.monotonic()
    try:
        result = subprocess.run(
            ["ping", "-n", "-c", "1", "-W", "2", gateway],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=3, check=False,
        )
        return result.returncode == 0, round((time.monotonic() - started) * 1000)
    except (OSError, subprocess.TimeoutExpired):
        return False, round((time.monotonic() - started) * 1000)


def http_probe(url, accepted_codes):
    started = time.monotonic()
    try:
        with urlopen(Request(url, headers={"User-Agent": "CobbleNetworkMonitor/1"}), timeout=6) as response:
            return response.status in accepted_codes, round((time.monotonic() - started) * 1000), response.status
    except HTTPError as exc:
        code = exc.code
        exc.close()
        return code in accepted_codes, round((time.monotonic() - started) * 1000), code
    except (URLError, TimeoutError, OSError, ValueError):
        return False, round((time.monotonic() - started) * 1000), None


def tunnel_probe():
    try:
        with urlopen("http://127.0.0.1:8080/health/control-plane", timeout=3) as response:
            data = json.load(response)
        return data.get("status"), data.get("state"), data.get("details", {}).get("consecutive_failures")
    except (URLError, TimeoutError, OSError, ValueError, KeyError):
        return "unreachable", None, None


def sample(gateway):
    router_ok, router_ms = router_probe(gateway)
    internet_ok, internet_ms, _ = http_probe("https://www.google.com/generate_204", {204})
    openai_ok, openai_ms, openai_code = http_probe("https://api.openai.com/v1/models", {401})
    tunnel_status, tunnel_state, tunnel_failures = tunnel_probe()
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "gateway_ip": gateway, "router_ok": router_ok, "router_ms": router_ms,
        "internet_ok": internet_ok, "internet_ms": internet_ms,
        "openai_ok": openai_ok, "openai_ms": openai_ms,
        "openai_http": openai_code, "tunnel_status": tunnel_status,
        "tunnel_state": tunnel_state, "tunnel_failures": tunnel_failures,
    }


def connect_db(path):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if not path.exists():
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
    db = sqlite3.connect(path, timeout=10)
    db.execute("""CREATE TABLE IF NOT EXISTS samples (
        timestamp_utc TEXT NOT NULL, gateway_ip TEXT,
        router_ok INTEGER, router_ms INTEGER,
        internet_ok INTEGER NOT NULL, internet_ms INTEGER,
        openai_ok INTEGER NOT NULL, openai_ms INTEGER, openai_http INTEGER,
        tunnel_status TEXT, tunnel_state TEXT, tunnel_failures INTEGER
    )""")
    db.execute("CREATE INDEX IF NOT EXISTS samples_at ON samples(timestamp_utc)")
    db.commit()
    return db


def save(db, observation):
    fields = list(observation)
    db.execute(f"INSERT INTO samples ({', '.join(fields)}) VALUES ({', '.join('?' for _ in fields)})",
               [None if observation[k] is None else int(observation[k])
                if isinstance(observation[k], bool) else observation[k] for k in fields])
    cutoff = (datetime.now(timezone.utc) - timedelta(days=31)).isoformat(timespec="seconds")
    db.execute("DELETE FROM samples WHERE timestamp_utc < ?", (cutoff,))
    db.commit()


def report(db):
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat(timespec="seconds")
    row = db.execute("""SELECT COUNT(*), SUM(CASE WHEN router_ok=0 THEN 1 ELSE 0 END),
        SUM(CASE WHEN internet_ok=0 THEN 1 ELSE 0 END),
        SUM(CASE WHEN openai_ok=0 THEN 1 ELSE 0 END),
        SUM(CASE WHEN tunnel_status!='ok' THEN 1 ELSE 0 END),
        MAX(timestamp_utc) FROM samples WHERE timestamp_utc >= ?""", (cutoff,)).fetchone()
    return dict(zip(("samples_24h", "router_no_reply", "internet_failures", "openai_failures",
                     "tunnel_non_ok", "last_sample_utc"), row))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--once", action="store_true", help="Take and store one sample")
    group.add_argument("--report", action="store_true", help="Summarise last 24h; no network calls")
    parser.add_argument("--interval", type=int, default=60, help="Sampling interval, seconds (default 60)")
    parser.add_argument("--gateway", help="Override Windows-detected physical router IPv4 address")
    args = parser.parse_args()
    if not 15 <= args.interval <= 3600:
        parser.error("Interval must be between 15 and 3600 seconds")
    gateway = args.gateway or (None if args.report else windows_router_gateway())
    if gateway:
        try:
            if not ipaddress.IPv4Address(gateway).is_private:
                raise ValueError()
        except ValueError:
            parser.error("Gateway must be a private IPv4 address")
    with closing(connect_db(args.db)) as db:
        if args.report:
            print(json.dumps(report(db), indent=2))
            return
        if args.once:
            observation = sample(gateway)
            save(db, observation)
            print(json.dumps(observation, indent=2))
            return
        while True:
            started = time.monotonic()
            save(db, sample(gateway))
            time.sleep(max(0, args.interval - (time.monotonic() - started)))


if __name__ == "__main__":
    main()
