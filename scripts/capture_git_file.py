"""Mint a Cobble trace from a selected passage of an archived Git file."""
import argparse
from pathlib import Path
from cobble.git_archive import capture_file_trace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", help="GitHub owner/repository")
    parser.add_argument("commit", help="Full commit SHA of archived file")
    parser.add_argument("path", help="Repository-relative file path")
    parser.add_argument("exact", help="Exact selected text present in the file")
    parser.add_argument("--store", type=Path, default=Path.home() / "cobble-data")
    args = parser.parse_args()
    trace = capture_file_trace(
        args.store, args.repository, args.commit, args.path, args.exact
    )
    print("Trace:", trace["uri"])
    print("Source:", trace["source_uri"])
    print("Local copy:", trace["local_copy_uri"])


if __name__ == "__main__":
    main()
