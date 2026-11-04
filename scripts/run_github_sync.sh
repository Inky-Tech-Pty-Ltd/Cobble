#!/usr/bin/env bash
# Run the existing organisation-wide importer with a single-instance lock and a dated log.
# This is the scheduler entry point; sync_github_corpus.sh remains usable manually.
set -Eeuo pipefail
umask 077

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
log_dir="$HOME/cobble-data/logs/github-sync"
mkdir -p -- "$log_dir"
log_file="$log_dir/sync-$(date -u +%Y%m%dT%H%M%SZ)-$$.log"
printf 'GitHub corpus sync log: %s\n' "$log_file"
exec >"$log_file" 2>&1
printf 'Started: %s (pid=%s)\n' "$(date -Is)" "$$"

# Leave the lock file in place: replacing it while another process holds
# the old inode would defeat flock's single-instance guarantee.
exec 9>"$log_dir/.sync.lock"
if ! flock -n 9; then
  printf 'Another GitHub corpus sync is already running; refusing to overlap.\n'
  exit 75
fi

on_exit() {
  status=$?
  printf 'Finished: %s (exit=%s)\n' "$(date -Is)" "$status"
}
trap on_exit EXIT

bash "$script_dir/sync_github_corpus.sh" "$@"
