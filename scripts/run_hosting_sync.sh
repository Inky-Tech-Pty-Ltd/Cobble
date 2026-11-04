#!/usr/bin/env bash
# Scheduler entry point for the versioned hosting filesystem synchroniser.
# The Python script owns the single-instance lock and source configurations.
set -Eeuo pipefail
umask 077

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
log_dir="$HOME/cobble-data/logs/hosting-sync"
mkdir -p -- "$log_dir"
chmod 700 -- "$log_dir"
log_file="$log_dir/sync-$(date -u +%Y%m%dT%H%M%SZ)-$$.log"
printf 'Hosting filesystem sync log: %s\n' "$log_file"
exec >"$log_file" 2>&1

printf 'Started: %s (pid=%s)\n' "$(date -Is)" "$$"
on_exit() {
    status=$?
    printf 'Finished: %s (exit=%s)\n' "$(date -Is)" "$status"
}
trap on_exit EXIT

python3 "$script_dir/sync_hosting_filesystems.py" "$@"
