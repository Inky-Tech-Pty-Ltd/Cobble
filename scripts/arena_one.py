"""Arena One CLI: copy the entire preserved corpus into an isolated arena."""
import argparse
import json
from pathlib import Path

from cobble.arena import FIELDS, init_arena, overview, populate_corpus


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    start = sub.add_parser("init", help="Create an isolated derived arena")
    start.add_argument("--archive", type=Path, default=Path.home() / "cobble-data")
    start.add_argument("--arena", type=Path, default=Path.home() / "cobble-arenas" / "arena-a")
    start.add_argument("--memory-bytes", type=int, default=268435456,
                       help="Raw copied source bytes budget (default: 256 MiB)")
    start.add_argument("--model-tokens", type=int, default=0)
    start.add_argument("--attention-steps", type=int, default=10)
    start.add_argument("--archive-reads", type=int, default=100000)
    start.add_argument("--external-ops", type=int, default=0)
    populate = sub.add_parser("populate", help="Copy ALL archived files, never excerpts")
    populate.add_argument("--arena", type=Path,
                          default=Path.home() / "cobble-arenas" / "arena-a")
    status = sub.add_parser("status", help="Show corpus totals and budgets, not content")
    status.add_argument("--arena", type=Path,
                        default=Path.home() / "cobble-arenas" / "arena-a")
    args = parser.parse_args()
    if args.command == "init":
        limits = {"memory_bytes": args.memory_bytes,
                  "model_tokens": args.model_tokens,
                  "attention_steps": args.attention_steps,
                  "archive_reads": args.archive_reads,
                  "external_ops": args.external_ops}
        assert set(limits) == set(FIELDS)
        result = init_arena(args.archive, args.arena, limits)
    elif args.command == "populate":
        result = populate_corpus(args.arena)
    else:
        result = overview(args.arena)
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
