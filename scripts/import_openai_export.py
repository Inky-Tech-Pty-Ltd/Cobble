"""Import local ChatGPT conversation snapshots into Cobble's private source store."""
import argparse
import json
from pathlib import Path

from cobble.openai_export import import_export


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exports", nargs="+", type=Path,
                        help="Conversation ZIP or full Privacy Portal ZIP, oldest first")
    parser.add_argument("--store", type=Path,
                        default=Path.home() / "cobble-data",
                        help="Private archive root, default: ~/cobble-data")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate and report changes without writing")
    args = parser.parse_args()

    store = args.store.expanduser().resolve()
    if any((p / ".git").exists() for p in (store, *store.parents)):
        parser.error("Refusing to store private conversations inside a Git checkout")

    for export in args.exports:
        result = import_export(export, store, dry_run=args.dry_run)
        # Private message bodies, titles and IDs are never printed.
        print(json.dumps({"archive": export.name, **result}, sort_keys=True))


if __name__ == "__main__":
    main()
