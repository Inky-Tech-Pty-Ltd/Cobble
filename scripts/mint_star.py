"""Mint a local star with a newly authored hypothesis as its centre."""
import argparse
from pathlib import Path
from cobble.stars import mint_star


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("hypothesis", help="Hypothesis text")
    parser.add_argument("members", nargs="+", help="Existing Cobble evidence trace URIs")
    parser.add_argument("--store", type=Path, default=Path.home() / "cobble-data")
    args = parser.parse_args()
    star = mint_star(args.store, args.hypothesis, args.members)
    ident = star["A"].rsplit("/", 1)[-1]
    print("STAR CREDENTIAL MINTED (local only)")
    print("Hypothesis:", args.hypothesis.strip())
    print("Centre:", star["A"])
    print("Rays:", len(star["B"]))
    print("Credential:", args.store.expanduser().resolve() / "stars" / f"{ident}.json")


if __name__ == "__main__":
    main()
