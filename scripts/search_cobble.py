"""Private, offline Cobble source search. Never send results to a provider."""
import argparse
import json
from pathlib import Path

from cobble.local_search import build, search, show


def _inside_git(path):
    path = Path(path).expanduser().absolute()
    return any((ancestor / ".git").exists() for ancestor in (path, *path.parents))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path,
                        default=Path.home() / "cobble-data",
                        help="Protected source root, not a Git checkout")
    parser.add_argument("--index", type=Path,
                        help="Private SQLite index (default: STORE/index/search.sqlite3)")
    commands = parser.add_subparsers(dest="action", required=True)
    commands.add_parser("build", help="Locally rebuild search from preserved sources")
    query = commands.add_parser("search", help="Search all indexed sources")
    query.add_argument("terms")
    query.add_argument("--limit", type=int, default=8)
    page = commands.add_parser("show", help="Read one bounded indexed text excerpt")
    page.add_argument("document_id")
    page.add_argument("--max-chars", type=int, default=1800)
    args = parser.parse_args()

    store = args.store.expanduser().absolute()
    index = args.index.expanduser().absolute() if args.index else store / "index" / "search.sqlite3"
    if _inside_git(store) or _inside_git(index):
        parser.error("Refusing to use a Git checkout for private source storage/indexes")

    if args.action == "build":
        outcome = build(store, index)
        print(json.dumps(outcome, indent=2, sort_keys=True))
    elif args.action == "search":
        print(json.dumps(search(index, args.terms, args.limit), indent=2,
                         ensure_ascii=False))
    else:
        print(json.dumps(show(index, args.document_id, args.max_chars),
                         indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
