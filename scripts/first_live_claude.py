"""Operator CLI for Claude's one-time memory-free first call.

No flags: private, keyless, offline preview.
The live command is intentionally not advertised until workspace spend controls
and a local expiring key have been independently configured.
"""
import argparse
import json
from pathlib import Path

from cobble.claude_adapter import ClaudeAdapter
from cobble.claude_first_call import (
    CONSENT, HELLO, first_call_status, first_live_hello,
)
from cobble.snug_exchange import ExchangeRequest


def _in_git(path):
    return any((p / ".git").exists() for p in (path, *path.parents))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, default=Path.home() / "cobble-data")
    parser.add_argument("--index", type=Path, help="Default: STORE/index/search.sqlite3")
    parser.add_argument("--status", action="store_true",
                        help="Read previous attempt status without network or secrets")
    parser.add_argument("--send-live", action="store_true",
                        help="Enable an actual, one-time, memory-free API call")
    parser.add_argument("--confirm", default="",
                        help="Exact authorisation phrase, no secrets here")
    parser.add_argument("--workspace-limit-confirmed", action="store_true",
                        help="Affirm the vendor workspace has a suitable spending limit")
    args = parser.parse_args()

    store = args.store.expanduser().absolute()
    index = args.index.expanduser().absolute() if args.index else (
        store / "index" / "search.sqlite3")
    if _in_git(store) or _in_git(index):
        parser.error("Refusing to write private data inside a Git checkout")
    if args.status:
        if args.send_live:
            parser.error("--status and --send-live are mutually exclusive")
        print(json.dumps(first_call_status(store), indent=2))
        return

    if not args.send_live:
        request = ExchangeRequest(
            participant="operator", question=HELLO,
            selected_memories=(), previous_exchanges=())
        preview = ClaudeAdapter().preview(request)
        preview.update({
            "dry_run": True,
            "network_enabled": False,
            "key_read": False,
            "event_written": False,
            "explicit_context": "No archived memory or earlier exchange",
            "first_call_status": first_call_status(store),
        })
        print(json.dumps(preview, indent=2))
        return

    if args.confirm != CONSENT:
        parser.error("Live calls require --confirm with the exact authorisation phrase")
    result = first_live_hello(
        store=store, index=index, live=True, confirm=args.confirm,
        workspace_limit_confirmed=args.workspace_limit_confirmed)
    # Print only operational metadata and the answer-free usage estimate.
    # Answer itself is retained in Snug's protected event store.
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
