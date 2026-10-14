"""Read a local star and verify that every ray is a Village Link."""
import argparse
import hashlib
import json
from pathlib import Path

from cobble.stars import trace_id
from villagelink.codec import make, parse


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("centre", help="URI of the star's centre")
    parser.add_argument("--store", type=Path, default=Path.home() / "cobble-data")
    args = parser.parse_args()
    store = args.store.expanduser().resolve()
    ident = trace_id(args.centre)
    star = json.loads((store / "stars" / f"{ident}.json").read_text())
    if star.get("type") != "StarCredential" or star.get("A") != args.centre:
        raise ValueError("Not a matching StarCredential")
    centre = json.loads((store / "traces" / f"{ident}.json").read_text())
    print("Hypothesis:", centre["selector"]["exact"])
    print("Centre:", star["A"])
    for index, member in enumerate(star["B"], 1):
        ray = make(star["A"], member)
        filename = hashlib.sha256(ray.encode("utf-8")).hexdigest() + ".json"
        saved = json.loads((store / "links" / filename).read_text())
        if saved.get("uri") != ray or parse(ray) != (star["A"], member):
            raise ValueError(f"Ray {index} failed verification")
        print(f"Ray {index}: {member} [verified locally]")
    print(f"Verified {len(star['B'])} rays.")


if __name__ == "__main__":
    main()
