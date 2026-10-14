"""Add a ray to an existing star without changing its centre URI."""
import argparse
from pathlib import Path
from cobble.stars import add_ray


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("centre", help="Existing star centre URI")
    parser.add_argument("member", help="Existing evidence trace URI")
    parser.add_argument("--store", type=Path, default=Path.home() / "cobble-data")
    args = parser.parse_args()
    star = add_ray(args.store, args.centre, args.member)
    print("Centre:", star["A"])
    print("Rays:", len(star["B"]))


if __name__ == "__main__":
    main()
