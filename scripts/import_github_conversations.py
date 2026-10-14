"""Archive GitHub Issues, PR conversations and Discussions as local JSON."""
import argparse
from pathlib import Path
from cobble.github_conversations import GitHubAPI, ingest_conversations


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", help="GitHub owner/repository")
    parser.add_argument("--store", type=Path, default=Path.home() / "cobble-data")
    parser.add_argument("--skip-discussions", action="store_true",
                        help="Capture REST conversations only; explicitly skip GraphQL Discussions")
    args = parser.parse_args()
    api = GitHubAPI()
    if not args.skip_discussions and not api.token:
        parser.error("Discussions require GH_TOKEN, GITHUB_TOKEN or 'gh auth login'; "
                     "use --skip-discussions for an explicitly partial import")
    counts = ingest_conversations(args.store, args.repository, api,
                                  include_discussions=not args.skip_discussions)
    print("Archived:", args.repository)
    for kind, count in counts.items():
        print(f"  {kind}: {count}")
    print("Local memory:", args.store.expanduser() / "github" / "conversations")


if __name__ == "__main__":
    main()
