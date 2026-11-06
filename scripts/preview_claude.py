"""Offline Claude preview: no key is read and no network operation exists here."""
import argparse
import json
from pathlib import Path

from cobble.local_search import show
from cobble.snug_exchange import ExchangeRequest, _validate, read_event
from cobble.claude_adapter import ClaudeAdapter


def _in_git(path):
    return any((p / ".git").exists() for p in (path, *path.parents))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, default=Path.home() / "cobble-data")
    parser.add_argument("--index", type=Path)
    parser.add_argument("--question", default="Hello, Helen. What is your role?")
    parser.add_argument("--participant", default="operator")
    parser.add_argument("--memory-id", action="append", default=[])
    parser.add_argument("--allow-source", action="append", default=[],
                        choices=("chatgpt", "github", "inkytech", "villagelink"))
    parser.add_argument("--previous", action="append", default=[])
    args = parser.parse_args()
    store = args.store.expanduser().absolute()
    index = args.index.expanduser().absolute() if args.index else (
        store / "index" / "search.sqlite3")
    if _in_git(store) or _in_git(index):
        parser.error("Private memory and index must live outside Git")

    # Exactly the same source-scoping check as the exchange before retrieval.
    _validate(args.question, args.participant, "claude", args.memory_id,
              args.allow_source, args.previous)
    selected = []
    for docid in args.memory_id:
        record = show(index, docid, max_chars=1500)
        if record["source"] not in args.allow_source:
            raise PermissionError("Memory is outside explicitly authorised sources")
        selected.append({"document_id": docid, "source": record["source"],
                         "reference": record["reference"], "title": record["title"],
                         "text": record["text"]})
    previous = []
    for prior in args.previous:
        event = read_event(store, prior)
        previous.append({"event_id": prior, "provider": event["provider"],
                         "participant": event["participant"],
                         "question": event["question"], "answer": event["answer"]})
    request = ExchangeRequest(
        participant=args.participant, question=args.question,
        selected_memories=tuple(selected),
        previous_exchanges=tuple(previous))
    plan = ClaudeAdapter().preview(request)
    plan["dry_run"] = True
    plan["note"] = "No API key read; no network call; no event written."
    # Intentionally NEVER print question text, passage text, prior answer,
    # API keys, or the complete outbound JSON payload.
    print(json.dumps(plan, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
