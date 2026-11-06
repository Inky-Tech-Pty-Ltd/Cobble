"""Local-only Snug exchange: two *simulated* intelligences, no external calls."""
import argparse
import json
from pathlib import Path

from cobble.snug_exchange import exchange, read_event


def _in_git(path):
    return any((p / ".git").exists() for p in (path, *path.parents))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, default=Path.home() / "cobble-data")
    parser.add_argument("--index", type=Path,
                        help="Default: STORE/index/search.sqlite3")
    actions = parser.add_subparsers(dest="action", required=True)

    ask = actions.add_parser("ask", help="Run one authorised offline fixture exchange")
    ask.add_argument("--question", required=True)
    ask.add_argument("--participant", default="operator")
    ask.add_argument("--provider", choices=("fixture-amber", "fixture-indigo"),
                     default="fixture-amber")
    ask.add_argument("--memory-id", action="append", default=[],
                     help="Explicitly selected index document ID, at most three")
    ask.add_argument("--allow-source", action="append", default=[],
                     choices=("chatgpt", "github", "inkytech", "villagelink"),
                     help="Sources operator explicitly permits in this request")
    ask.add_argument("--previous", action="append", default=[],
                     help="Explicitly include a previously recorded exchange ID")

    inspect = actions.add_parser("inspect", help="Read one saved exchange summary")
    inspect.add_argument("event_id")

    args = parser.parse_args()
    store = args.store.expanduser().absolute()
    index = args.index.expanduser().absolute() if args.index else (
        store / "index" / "search.sqlite3")
    if _in_git(store) or _in_git(index):
        parser.error("Private exchange store/index cannot live inside Git")

    if args.action == "ask":
        event = exchange(
            store=store, index=index, question=args.question,
            participant=args.participant, provider=args.provider,
            memory_ids=args.memory_id, allowed_sources=args.allow_source,
            prior_ids=args.previous)
    else:
        event = read_event(store, args.event_id)

    # Intentionally omit original question and sourced passages from output.
    # The retained event file contains the complete authorised exchange.
    print(json.dumps({
        "event_id": event["event_id"],
        "provider": event["provider"],
        "participant": event["participant"],
        "selected_memories": len(event["selected_memories"]),
        "prior_exchanges": len(event["previous_exchange_ids"]),
        "answer": event["answer"],
        "mode": event["usage"]["kind"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
