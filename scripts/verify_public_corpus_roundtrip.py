"""Bounded live-public importer/export/restore check for GitHub Actions.

Output counts and integrity identifiers, not the underlying conversations.
"""
import hashlib
import json
import tempfile
from pathlib import Path

from cobble.github_conversations import GitHubAPI, ingest_conversations
from cobble.portability import export_corpus, restore_corpus


def main():
    repositories = ["Inky-Tech-Pty-Ltd/Cobble", "Inky-Tech-Pty-Ltd/VillageLink"]
    with tempfile.TemporaryDirectory(prefix="cobble-public-corpus-") as temp:
        root = Path(temp)
        src, dst, package = root / "original", root / "restored", root / "package.json"
        api = GitHubAPI()
        if not api.token:
            raise RuntimeError("Authenticated GitHub API token required; do not skip Discussions")
        result = {}
        for repo in repositories:
            result[repo] = ingest_conversations(src, repo, api, include_discussions=True)
        stats = export_corpus(src, package, repositories)
        restored = restore_corpus(package, dst)
        if stats != restored:
            raise AssertionError("Export/restore counts differ")
        archive = Path("github/conversations")
        original_root, restored_root = src / archive, dst / archive
        original = {p.relative_to(original_root): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in original_root.rglob("*") if p.is_file()}
        reconstructed = {p.relative_to(restored_root): hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in restored_root.rglob("*") if p.is_file()}
        if original != reconstructed:
            raise AssertionError("Offline restored archive bytes differ")
        if not all(isinstance(v["discussions"], int) for v in result.values()):
            raise AssertionError("Authenticated Discussion ingestion was skipped")
        print(json.dumps({"scope": "public GitHub API view, not an atomic source snapshot",
                          "source_counts": result, "roundtrip": stats,
                          "package_sha256": hashlib.sha256(package.read_bytes()).hexdigest(),
                          "distinct_file_sha256": len(set(original.values())),
                          "byte_identical": True}, sort_keys=True))


if __name__ == "__main__":
    main()
