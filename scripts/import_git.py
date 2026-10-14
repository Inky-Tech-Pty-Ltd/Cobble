"""Archive a local Git checkout, incrementally, into Cobble memory."""
import argparse
from pathlib import Path
from cobble.git_archive import archive_repository


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", help="GitHub owner/repository")
    parser.add_argument("checkout", type=Path, help="Local checkout root")
    parser.add_argument("--store", type=Path, default=Path.home() / "cobble-data")
    args = parser.parse_args()
    record = archive_repository(args.store, args.repository, args.checkout)
    print("Archived:", record["repository"])
    print("HEAD:", record["head"])
    print("Git objects:", record["archive_path"])


if __name__ == "__main__":
    main()
