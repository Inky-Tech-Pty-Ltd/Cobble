"""OpenAI GPT one-time hello. Default is keyless, offline, read-only preview."""
import argparse
import json
from pathlib import Path
import sys

from cobble.openai_adapter import OpenAIAdapter
from cobble.openai_first_call import (
    CONSENT, _request, first_call_status, first_live_hello
)


def _in_git(path):
    return any((p / ".git").exists() for p in (path, *path.parents))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, default=Path.home() / "cobble-data")
    parser.add_argument("--index", type=Path, help="Default: STORE/index/search.sqlite3")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--send-live", action="store_true")
    parser.add_argument("--confirm", default="")
    parser.add_argument("--project-limit-confirmed", action="store_true")
    args = parser.parse_args()
    store = args.store.expanduser().absolute()
    index = args.index.expanduser().absolute() if args.index else store / "index/search.sqlite3"
    if _in_git(store) or _in_git(index):
        parser.error("Refusing private writes inside a Git checkout")
    if args.status:
        if args.send_live:
            parser.error("Cannot combine --status with --send-live")
        print(json.dumps(first_call_status(store), indent=2))
        return
    if not args.send_live:
        plan = OpenAIAdapter().preview(_request())
        plan.update({"dry_run": True, "network_calls": 0,
                     "key_read": False, "event_written": False,
                     "first_call_status": first_call_status(store)})
        print(json.dumps(plan, indent=2))
        return
    if args.confirm != CONSENT or not args.project_limit_confirmed:
        parser.error("Exact consent and project-limit confirmation required")
    # Consumed only following explicit authorisation; never printed or persisted.
    key = sys.stdin.read(4096).strip()
    if not key or len(key) > 512:
        parser.error("Valid key required on stdin")
    result = first_live_hello(store=store, index=index, live=True,
                              confirm=args.confirm, project_limit_confirmed=True,
                              api_key=key)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
