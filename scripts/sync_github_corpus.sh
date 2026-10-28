#!/usr/bin/env bash
# Incrementally archive every GitHub repository visible in an organisation.
# Conventional source files only: this does not mint traces or memory links.
set -Eeuo pipefail

usage() {
  cat <<'HELP'
Usage: bash scripts/sync_github_corpus.sh [--dry-run] [--org OWNER] [--store DIR] [--checkouts DIR]

Synchronise all GitHub repositories visible to the authenticated gh account.
Keep disposable source checkouts separate from working repositories, then run
Cobble's existing Git history and conversation importers.

Defaults:
  --org       Inky-Tech-Pty-Ltd
  --store     ~/cobble-data
  --checkouts ~/cobble-source-checkouts

--dry-run lists repositories and planned operations, changing nothing locally.
Requires gh auth (including private-repository and Discussions read access),
git, and python3. This script does not write to GitHub.
HELP
}

org=Inky-Tech-Pty-Ltd
store="$HOME/cobble-data"
checkouts="$HOME/cobble-source-checkouts"
dry_run=false

while (($#)); do
  case "$1" in
    --dry-run) dry_run=true; shift ;;
    --org|--store|--checkouts)
      option="$1"
      if (($# < 2)) || [[ -z "$2" ]]; then
        printf 'Missing value for %s\n' "$option" >&2; exit 2
      fi
      case "$option" in
        --org) org="$2" ;;
        --store) store="$2" ;;
        --checkouts) checkouts="$2" ;;
      esac
      shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done

# gh output becomes a directory component. Treat it as untrusted input.
if [[ ! "$org" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]*$ ]]; then
  printf 'Invalid GitHub organisation: %s\n' "$org" >&2; exit 2
fi
for tool in gh git python3; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    printf 'Missing required command: %s\n' "$tool" >&2; exit 1
  fi
done

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
project_root="$(cd -- "$script_dir/.." && pwd -P)"
if [[ ! -f "$script_dir/import_git.py" || ! -f "$script_dir/import_github_conversations.py" ]]; then
  printf 'Run the version-controlled script from its Cobble checkout.\n' >&2
  exit 1
fi

# A failed gh command must not look like an empty or complete repository list.
repo_output="$(gh repo list "$org" --limit 1000 --json name --jq '.[].name')"
if [[ -z "$repo_output" ]]; then
  printf 'GitHub returned no accessible repositories for %s; refusing an empty sync.\n' "$org" >&2
  exit 1
fi
mapfile -t repo_names <<< "$repo_output"
for name in "${repo_names[@]}"; do
  if [[ ! "$name" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]*$ ]]; then
    printf 'Unexpected repository name: %s\n' "$name" >&2; exit 1
  fi
done

if "$dry_run"; then
  printf 'DRY RUN: %s accessible repositories for %s (no files will be changed)\n' "${#repo_names[@]}" "$org"
  for name in "${repo_names[@]}"; do
    source="$checkouts/$name"
    if [[ -d "$source/.git" ]]; then action='fetch and fast-forward'; else action='clone'; fi
    printf '  %s/%s: %s; archive Git history and conversations\n' "$org" "$name" "$action"
  done
  exit 0
fi

current=setup
trap 'code=$?; printf "Sync stopped during %s (exit %s, line %s). Earlier archived records remain.\n" "$current" "$code" "$LINENO" >&2' ERR
mkdir -p -- "$checkouts" "$store"

# Python imports must resolve Cobble even when called from another directory.
export PYTHONPATH="$project_root/src${PYTHONPATH:+:$PYTHONPATH}"
new_versions_total=0
for name in "${repo_names[@]}"; do
  current="$org/$name"
  slug="$org/$name"
  source="$checkouts/$name"
  printf '\n===== %s =====\n' "$slug"
  if [[ -d "$source/.git" ]]; then
    if [[ -n "$(git -C "$source" status --porcelain)" ]]; then
      printf "Checkout has uncommitted changes; refusing to update: %s\n" "$source" >&2
      exit 1
    fi
    git -C "$source" fetch origin --tags
    git -C "$source" pull --ff-only
  elif [[ -e "$source" || -L "$source" ]]; then
    printf 'Checkout path exists but is not a Git checkout: %s\n' "$source" >&2
    exit 1
  else
    gh repo clone "$slug" "$source"
  fi

  # Count immutable snapshots, not conversation threads or messages.
  versions_dir="$store/github/conversations/$org/$name"
  before=0
  if [[ -d "$versions_dir" ]]; then
    before="$(find "$versions_dir" -type f -path '*/versions/*.json' | wc -l)"
  fi

  python3 "$script_dir/import_git.py" "$slug" "$source" --store "$store"
  python3 "$script_dir/import_github_conversations.py" "$slug" --store "$store"

  after=0
  if [[ -d "$versions_dir" ]]; then
    after="$(find "$versions_dir" -type f -path '*/versions/*.json' | wc -l)"
  fi
  added=$((after - before))
  if ((added < 0)); then
    printf 'Unexpected snapshot loss in %s: before=%s after=%s\n' "$slug" "$before" "$after" >&2
    exit 1
  fi
  new_versions_total=$((new_versions_total + added))
  printf 'New archived conversation versions: %s\n' "$added"
done
current=complete
printf '\nSync complete: %s repositories; %s new conversation versions.\n' "${#repo_names[@]}" "$new_versions_total"
printf 'Source store: %s\n' "$store"
