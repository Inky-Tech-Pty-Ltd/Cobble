"""Read-only graph inspection and illustrative structural G0 inventory."""
import argparse
import json
from pathlib import Path
from cobble.graph import inspect_hypothesis, simple_baseline


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("centre", help="Hypothesis centre trace URI")
    parser.add_argument("--store", type=Path, default=Path.home() / "cobble-data")
    parser.add_argument("--baseline", action="store_true", help="Include G0 inventory")
    args = parser.parse_args()
    data = {"G1": inspect_hypothesis(args.store, args.centre)}
    if args.baseline:
        data["G0"] = simple_baseline(args.store, args.centre)
    print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
