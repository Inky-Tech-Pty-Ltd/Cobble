"""Explicitly provision an empty, independently identified local Cobble store.

Run using the repository's virtual environment and PYTHONPATH=src.
No supplier credentials, imports of existing memories or network activity.
"""
import argparse
import json
from pathlib import Path

from cobble.instance_identity import PILOT_NAMES, provision
from cobble.local_search import build
from cobble.peer_door import PeerDoor


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    init = actions.add_parser("init")
    init.add_argument("--store", required=True, type=Path)
    init.add_argument("--name", choices=PILOT_NAMES, required=True)
    for action in ("read", "post"):
        peer = actions.add_parser(action)
        peer.add_argument("--store", required=True, type=Path)
    args = parser.parse_args()
    if args.action == "init":
        identity = provision(args.store, args.name)
        build(args.store, args.store / "index" / "search.sqlite3")
        print(json.dumps(identity))
        return

    # Invitation credentials must not be included in shell command arguments.
    import sys
    raw = sys.stdin.read(32769)
    if len(raw) > 32768:
        parser.error("Peer input too large")
    data = json.loads(raw)
    expected = {"invitation"} if args.action == "read" else {"invitation", "text"}
    if not isinstance(data, dict) or set(data) != expected:
        parser.error("Expected a private JSON object on stdin")
    client = PeerDoor(args.store, data["invitation"])
    result = client.read() if args.action == "read" else client.post(data["text"])
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
