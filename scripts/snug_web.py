"""Start Snug's first browser interface on local loopback only."""
import argparse
from pathlib import Path

from cobble.snug_console import create_server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arena", type=Path,
                        default=Path.home() / "cobble-arenas" / "arena-a",
                        help="Populated local Arena; never a public web root")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    with create_server(args.arena, args.port) as server:
        print(f"Snug local console: http://127.0.0.1:{server.server_port}/", flush=True)
        print("Offline mode. Private corpus never served. Ctrl+C to stop.", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()


if __name__ == "__main__":
    main()
