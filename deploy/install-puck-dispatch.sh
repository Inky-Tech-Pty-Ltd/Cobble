#!/usr/bin/env bash
# Operator-run after reviewing the exact code and provenance on main.
# Does NOT retrieve, install or print any private key.
set -euo pipefail
[[ "${EUID}" == 0 ]] || { echo "Run as root" >&2; exit 1; }
ROOT="${1:-}"
[[ -n "$ROOT" && -f "$ROOT/src/cobble/puck_dispatch_broker.py" &&
   -f "$ROOT/src/cobble/puck_github_writer.py" &&
   -f "$ROOT/deploy/puck-dispatch.service" ]] || {
  echo "Pass the reviewed Cobble checkout directory" >&2; exit 1;
}
id -u puck-dispatch >/dev/null 2>&1 || useradd --system --no-create-home --home-dir /nonexistent --shell /usr/sbin/nologin puck-dispatch
getent group puck-dispatch-clients >/dev/null || groupadd --system puck-dispatch-clients
# Cobble's interactive user gets socket access, not key or code write access.
usermod -aG puck-dispatch-clients cobbler
install -d -o root -g root -m 0755 /opt/puck-dispatch /opt/puck-dispatch/cobble
install -m 0644 -o root -g root "$ROOT/src/cobble/puck_dispatch_broker.py" /opt/puck-dispatch/cobble/puck_dispatch_broker.py
install -m 0644 -o root -g root "$ROOT/src/cobble/puck_github_writer.py" /opt/puck-dispatch/cobble/puck_github_writer.py
install -d -o puck-dispatch -g puck-dispatch -m 0700 /etc/puck-dispatch
install -m 0644 -o root -g root "$ROOT/deploy/puck-dispatch.service" /etc/systemd/system/puck-dispatch.service
systemctl daemon-reload
echo "Installed root-owned broker code and service definition."
echo "NO PRIVATE KEY INSTALLED; service intentionally not enabled or started."
echo "Log out and back in before using the new socket-access group."
