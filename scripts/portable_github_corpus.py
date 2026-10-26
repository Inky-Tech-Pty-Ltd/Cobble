"""Export or restore a selected GitHub conversation archive offline."""
import argparse
import json
from cobble.portability import export_corpus, restore_corpus


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    export = sub.add_parser("export")
    export.add_argument("--store", required=True)
    export.add_argument("--output", required=True)
    export.add_argument("--repo", action="append", required=True)
    restore = sub.add_parser("restore")
    restore.add_argument("--input", required=True)
    restore.add_argument("--store", required=True)
    args = parser.parse_args()
    result = (export_corpus(args.store, args.output, args.repo)
              if args.operation == "export"
              else restore_corpus(args.input, args.store))
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
