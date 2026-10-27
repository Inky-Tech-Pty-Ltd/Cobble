"""Append a local source-retrieval observation without fetching any content."""
import argparse
import json
from pathlib import Path
from cobble.observations import record_observation, STATUSES


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace_uri")
    parser.add_argument("status", choices=sorted(STATUSES))
    parser.add_argument("--store", type=Path, default=Path.home() / "cobble-data")
    parser.add_argument("--method", choices=["manual", "local-file", "other"], default="manual")
    args = parser.parse_args()
    print(json.dumps(record_observation(args.store, args.trace_uri, args.status,
                                        method=args.method), indent=2))


if __name__ == "__main__":
    main()
