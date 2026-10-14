"""Create a locally addressable trace, optionally retaining supplied text."""
import argparse
from pathlib import Path
from cobble.traces import mint_trace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_uri", help="Original resource's URI")
    parser.add_argument("exact", help="Selected passage")
    parser.add_argument("--copy-file", type=Path, help="Existing UTF-8 text file to preserve")
    parser.add_argument("--store", type=Path, default=Path.home() / "cobble-data")
    args = parser.parse_args()
    copy_text = args.copy_file.read_text(encoding="utf-8") if args.copy_file else None
    record = mint_trace(args.store, args.source_uri, args.exact, copy_text)
    print("Trace:", record["uri"])
    print("Local copy:", record.get("local_copy_uri", "(none)"))


if __name__ == "__main__":
    main()
