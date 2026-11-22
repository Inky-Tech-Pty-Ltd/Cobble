"""Narrow GitHub Discussion comment writer for the dedicated Puck account.

Independent of `gh` and `GH_TOKEN` on McKay: those may be logged in as Joe.
A separately provisioned, fine-grained Puck token is required. This interface
never accepts arbitrary API paths, GraphQL, or token values.
"""
import json
import os
from pathlib import Path
import stat
import urllib.error
import urllib.request

API = "https://api.github.com/graphql"
ALLOWED_REPOSITORY = "Inky-Tech-Pty-Ltd/VillageLink"
EXPECTED_LOGIN = "puck-inky"
MAX_BODY_BYTES = 12000
MAX_RESPONSE_BYTES = 20000

_LOOKUP = """query($owner: String!, $name: String!, $number: Int!) {
  viewer { login }
  repository(owner: $owner, name: $name) {
    discussion(number: $number) { id title url }
  }
}"""
_POST = """mutation($discussionId: ID!, $body: String!) {
  addDiscussionComment(input: {discussionId: $discussionId, body: $body}) {
    comment { id url author { login } }
  }
}"""


def validate_request(repository, number, body):
    if repository != ALLOWED_REPOSITORY:
        raise ValueError("Only VillageLink Discussions are permitted")
    if type(number) is not int or not (1 <= number <= 1000000):
        raise ValueError("Invalid Discussion number")
    if not isinstance(body, str) or not body.strip():
        raise ValueError("Comment body is required")
    if len(body.encode("utf-8")) > MAX_BODY_BYTES:
        raise ValueError("Comment exceeds 12000 UTF-8 bytes")
    return repository, number, body


def _read_puck_token():
    filename = os.environ.get("COBBLE_PUCK_GITHUB_TOKEN_FILE", "")
    path = Path(filename)
    if not filename or not path.is_absolute() or path.is_symlink():
        raise PermissionError("Puck token file must be a regular absolute path")
    try:
        info = path.stat()
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or info.st_mode & 0o077:
            raise PermissionError("Puck token file must be owned by the service account and mode 0600")
        token = path.read_text(encoding="utf-8").strip()
    except OSError:
        raise PermissionError("Puck token file unavailable") from None
    if not token or len(token) > 1024 or any(c.isspace() for c in token):
        raise PermissionError("Invalid Puck token file")
    return token


def _graphql(query, variables, token):
    request = urllib.request.Request(
        API,
        method="POST",
        data=json.dumps({"query": query, "variables": variables}).encode("utf-8"),
        headers={"Authorization": "Bearer " + token,
                 "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json",
                 "User-Agent": "Cobble-Puck-Discussion-Writer"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as exc:
        # Do not pass back the remote response body or request headers.
        raise PermissionError("GitHub API rejected request (HTTP %s)" % exc.code) from None
    except urllib.error.URLError:
        raise ConnectionError("GitHub API unavailable") from None
    if len(raw) > MAX_RESPONSE_BYTES:
        raise RuntimeError("Unexpectedly large GitHub response")
    try:
        result = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        raise RuntimeError("Invalid GitHub response") from None
    if not isinstance(result, dict):
        raise PermissionError("GitHub GraphQL response malformed")
    errors = result.get("errors")
    if errors:
        # Report an actionable *category*, never GitHub's free-form error text.
        # Error messages could echo query parameters or credentials.
        messages = " ".join(str(e.get("message", "")) for e in errors if isinstance(e, dict)).lower()
        if "resource not accessible by personal access token" in messages:
            category = "token lacks the required repository permission"
        elif "forbidden" in messages or "insufficient" in messages or "permission" in messages:
            category = "permission denied"
        elif "locked" in messages:
            category = "discussion locked"
        elif "rate limit" in messages or "rate_limit" in messages:
            category = "rate limited"
        elif "could not resolve" in messages or "not found" in messages:
            category = "resource not found"
        elif "something went wrong" in messages:
            category = "GitHub internal error"
        else:
            category = "unclassified GraphQL error"
        operation = "comment mutation" if query == _POST else "discussion lookup"
        raise PermissionError(f"GitHub {operation} rejected: {category}")
    if not isinstance(result.get("data"), dict):
        raise PermissionError("GitHub GraphQL response missing data")
    return result["data"]


def post_discussion_comment(repository, number, body):
    """Post once as Puck. Only an explicitly enabled McKay service may call it."""
    validate_request(repository, number, body)
    if os.environ.get("COBBLE_MCP_ALLOW_PUCK_DISCUSSIONS") != "1":
        raise PermissionError("Puck Discussion comments are disabled")
    token = _read_puck_token()
    owner, name = repository.split("/", 1)
    lookup = _graphql(_LOOKUP, {"owner": owner, "name": name, "number": number}, token)
    if str((lookup.get("viewer") or {}).get("login", "")).lower() != EXPECTED_LOGIN:
        raise PermissionError("The configured GitHub token does not belong to puck-inky")
    discussion = (lookup.get("repository") or {}).get("discussion")
    if not isinstance(discussion, dict) or not isinstance(discussion.get("id"), str):
        raise ValueError("Discussion not found or inaccessible to Puck")
    response = _graphql(_POST, {"discussionId": discussion["id"], "body": body}, token)
    comment = (response.get("addDiscussionComment") or {}).get("comment")
    if not isinstance(comment, dict) or not isinstance(comment.get("url"), str):
        raise RuntimeError("GitHub did not confirm a discussion comment; verify before retrying")
    author = (comment.get("author") or {}).get("login", "")
    if str(author).lower() != EXPECTED_LOGIN:
        raise RuntimeError("GitHub returned an unexpected comment author")
    return {"posted": True, "author": author, "repository": repository,
            "discussion": number, "url": comment["url"]}
