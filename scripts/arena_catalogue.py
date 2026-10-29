"""Explore saved source metadata in an Arena, without reading corpus content."""
import argparse
import json
from pathlib import Path

from cobble.arena_catalogue import CATEGORIES, catalogue, list_sources


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arena", type=Path,
                        default=Path.home() / "cobble-arenas" / "arena-a",
                        help="Populated Arena directory; independent of McKay")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("summary", help="Full census of source categories")
    listing = sub.add_parser("list", help="Bounded metadata-only source list")
    listing.add_argument("--category", default="all",
                         choices=["all", *CATEGORIES])
    listing.add_argument("--offset", type=int, default=0)
    listing.add_argument("--limit", type=int, default=25)
    listing.add_argument("--query", default="", help="Substring of source path")
    args = parser.parse_args()
    if args.command == "summary":
        result = catalogue(args.arena)
    else:
        result = list_sources(args.arena, category=args.category,
                              offset=args.offset, limit=args.limit, query=args.query)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
