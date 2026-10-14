"""Retrieve a trace's selected local copy without network access."""
import argparse
from pathlib import Path
from cobble.traces import resolve_local


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", help="Cobble trace URI")
    parser.add_argument("--store", type=Path, default=Path.home() / "cobble-data")
    args = parser.parse_args()
    print(resolve_local(args.store, args.trace), end="")


if __name__ == "__main__":
    main()
