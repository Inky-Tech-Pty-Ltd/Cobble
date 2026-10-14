"""Snapshot GitHub conversations into local, versioned JSON records.

The REST API handles issues and pull requests. GraphQL handles Discussions.
No text interpretation, trace equivalence or public publication occurs here.
"""
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from cobble.git_archive import _slug


class GitHubAPI:
    def __init__(self, token=None):
        self.token = token or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not self.token:
            try:
                self.token = subprocess.run(
                    ["gh", "auth", "token"], capture_output=True, text=True,
                    timeout=10, check=True
                ).stdout.strip() or None
            except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
                pass

    def request(self, path, payload=None):
        base = "https://api.github.com"
        url = base + ("/graphql" if payload is not None else path)
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "Cobble-memory-importer",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        data = json.dumps(payload).encode() if payload is not None else None
        if data is not None:
            headers["Content-Type"] = "application/json"
        req = Request(url, data=data, headers=headers)
        try:
            with urlopen(req, timeout=45) as response:
                body = json.load(response)
                link = response.headers.get("Link", "")
        except HTTPError as exc:
            raise RuntimeError(f"GitHub API HTTP {exc.code} for {path}") from exc
        if isinstance(body, dict) and body.get("errors"):
            raise RuntimeError("GitHub GraphQL errors: " + str(body["errors"]))
        return body, link

    def pages(self, path):
        """Exhaust REST pagination using GitHub's next Link only."""
        url = path + ("&" if "?" in path else "?") + "per_page=100"
        while url:
            body, link = self.request(url)
            if not isinstance(body, list):
                raise ValueError(f"Expected paged list from {path}")
            yield from body
            next_url = None
            for part in link.split(","):
                if 'rel="next"' in part:
                    next_url = part.strip().split(";")[0].strip("<> ")
            if next_url and not next_url.startswith("https://api.github.com/"):
                raise ValueError("Unexpected GitHub pagination URL")
            url = next_url.removeprefix("https://api.github.com") if next_url else None

    def graphql(self, query, **variables):
        if not self.token:
            raise RuntimeError("Discussions require GH_TOKEN, GITHUB_TOKEN, or 'gh auth login'")
        body, _ = self.request("/graphql", {"query": query, "variables": variables})
        return body["data"]


DISCUSSIONS = """query($owner:String!, $repo:String!, $after:String) {
  repository(owner:$owner, name:$repo) {
    discussions(first:100, after:$after) {
      pageInfo { hasNextPage endCursor }
      nodes { id number title body url createdAt updatedAt closedAt
        author { login } category { name }
        answer { id }
      }
    }
  }
}"""
COMMENTS = """query($id:ID!, $after:String) {
  node(id:$id) { ... on Discussion {
    comments(first:100, after:$after) {
      pageInfo { hasNextPage endCursor }
      nodes { id body url createdAt updatedAt isAnswer
        author { login }
      }
    }
  } }
}"""
REPLIES = """query($id:ID!, $after:String) {
  node(id:$id) { ... on DiscussionComment {
    replies(first:100, after:$after) {
      pageInfo { hasNextPage endCursor }
      nodes { id body url createdAt updatedAt author { login } }
    }
  } }
}"""


def graphql_nodes(api, query, node_path, **vars):
    after = None
    while True:
        root = api.graphql(query, after=after, **vars)
        for part in node_path:
            root = root[part]
        if root is None:
            raise ValueError("Missing GraphQL conversation node")
        yield from root["nodes"]
        page = root["pageInfo"]
        if not page["hasNextPage"]:
            return
        after = page["endCursor"]
        if not after:
            raise ValueError("Missing pagination cursor")


def _atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    try:
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(value, f, indent=2, ensure_ascii=False, sort_keys=True)
            f.write("\n")
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def preserve(store, slug, kind, number, record):
    """Immutable content-addressed revisions plus a stable latest pointer."""
    root = Path(store).expanduser().resolve() / "github" / "conversations"
    owner, name = _slug(slug).split("/")
    base = root / owner / name / kind / str(number)
    encoded = json.dumps(record, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    snapshot = base / "versions" / (digest + ".json")
    if not snapshot.exists():
        _atomic_json(snapshot, record)
    _atomic_json(base / "latest.json", {"sha256": digest, "version": f"versions/{digest}.json"})
    return digest


def ingest_rest(api, store, slug):
    root = "/repos/" + _slug(slug)
    counts = {"issues": 0, "pulls": 0}
    for issue in api.pages(root + "/issues?state=all"):
        number = issue["number"]
        is_pr = "pull_request" in issue
        if is_pr:
            pull, _ = api.request(root + f"/pulls/{number}")
            record = {
                "kind": "pull_request", "issue": issue, "pull": pull,
                "conversation_comments": list(api.pages(root + f"/issues/{number}/comments")),
                "reviews": list(api.pages(root + f"/pulls/{number}/reviews")),
                "review_comments": list(api.pages(root + f"/pulls/{number}/comments")),
            }
            kind, key = "pulls", "pulls"
        else:
            record = {
                "kind": "issue", "issue": issue,
                "conversation_comments": list(api.pages(root + f"/issues/{number}/comments")),
            }
            kind, key = "issues", "issues"
        record["timeline"] = list(api.pages(root + f"/issues/{number}/timeline"))
        preserve(store, slug, kind, number, record)
        counts[key] += 1
    return counts


def ingest_discussions(api, store, slug):
    owner, repo = _slug(slug).split("/")
    count = 0
    for discussion in graphql_nodes(api, DISCUSSIONS,
                                    ("repository", "discussions"), owner=owner, repo=repo):
        comments = []
        for comment in graphql_nodes(api, COMMENTS, ("node", "comments"), id=discussion["id"]):
            replies = list(graphql_nodes(api, REPLIES, ("node", "replies"), id=comment["id"]))
            comments.append({"comment": comment, "replies": replies})
        record = {"kind": "discussion", "discussion": discussion, "comments": comments}
        preserve(store, slug, "discussions", discussion["number"], record)
        count += 1
    return count


def ingest_conversations(store, slug, api=None, include_discussions=True):
    """Complete per-conversation snapshots; failures propagate visibly."""
    api = api or GitHubAPI()
    counts = ingest_rest(api, store, slug)
    if include_discussions:
        counts["discussions"] = ingest_discussions(api, store, slug)
    else:
        counts["discussions"] = "SKIPPED"
    return counts
