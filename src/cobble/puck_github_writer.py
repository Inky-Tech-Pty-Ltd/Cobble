"""Fail-closed, bounded GitHub writer for Puck's App installation token.

No gh, git subprocess, credential helpers, HOME lookup or user OAuth token.
Requires a Puck-scoped GitHub App installation token supplied by an isolated
credential broker. This module cannot mint such a token on its own.
"""
import json
import os
import re
import urllib.error
import urllib.request

REPOSITORY = "Inky-Tech-Pty-Ltd/Cobble"
BOT_NAME = "puck-gpt[bot]"
BOT_EMAIL = "320794343+puck-gpt[bot]@users.noreply.github.com"
_BRANCH = re.compile(r"puck/work/[A-Za-z0-9][A-Za-z0-9._-]{0,63}\\Z")
_PATH = re.compile(r"docs/experiments/[A-Za-z0-9][A-Za-z0-9._-]{0,75}\\.md\\Z")
_API = "https://api.github.com"


def _request(method, path, token, body=None):
    raw = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        _API + path, data=raw, method=method,
        headers={"Authorization": "Bearer " + token,
                 "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28",
                 "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            return json.loads(response.read(200000))
    except urllib.error.HTTPError as exc:
        # Don't echo request bodies, credentials or arbitrary API responses.
        raise PermissionError("GitHub rejected the Puck writer operation (HTTP %d)" %
                              exc.code) from None


def _token():
    if os.environ.get("COBBLE_MCP_ALLOW_PUCK_WRITES") != "1":
        raise PermissionError("Puck writer disabled on McKay")
    token = os.environ.get("PUCK_GITHUB_INSTALLATION_TOKEN", "")
    if not token or len(token) > 1024 or not token.startswith("ghs_"):
        raise PermissionError("Puck GitHub App installation token unavailable")
    return token


def _installation(token):
    # Personal OAuth tokens must not be accepted as the writer credential.
    result = _request("GET", "/installation/repositories?per_page=100", token)
    if not any(item.get("full_name") == REPOSITORY
               for item in result.get("repositories", [])):
        raise PermissionError("Puck installation token lacks Cobble access")


def create_branch(name):
    if not isinstance(name, str) or not _BRANCH.fullmatch(name):
        raise ValueError("Only puck/work/<name> branches may be created")
    token = _token()
    _installation(token)
    ref = _request("GET", "/repos/" + REPOSITORY + "/git/ref/heads/main", token)
    sha = ref["object"]["sha"]
    result = _request("POST", "/repos/" + REPOSITORY + "/git/refs", token,
                      {"ref": "refs/heads/" + name, "sha": sha})
    return {"repository": REPOSITORY, "branch": name,
            "created": result.get("ref") == "refs/heads/" + name}


def write_file(branch, path, content, message):
    if not isinstance(branch, str) or not _BRANCH.fullmatch(branch):
        raise ValueError("Writer requires a puck/work/<name> branch")
    if not isinstance(path, str) or not _PATH.fullmatch(path):
        raise ValueError("Writer restricted to new experiment Markdown files")
    if not isinstance(content, str) or not 0 < len(content.encode("utf-8")) <= 12000:
        raise ValueError("Invalid content length")
    if not isinstance(message, str) or not 0 < len(message) <= 120 or "\\n" in message:
        raise ValueError("Invalid commit message")
    token = _token()
    _installation(token)
    # No sha field: GitHub returns 422 if the file exists, rather than overwrite.
    import base64
    payload = {"message": message,
               "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
               "branch": branch,
               "author": {"name": BOT_NAME, "email": BOT_EMAIL},
               "committer": {"name": BOT_NAME, "email": BOT_EMAIL}}
    result = _request("PUT", "/repos/" + REPOSITORY + "/contents/" + path,
                      token, payload)
    return {"repository": REPOSITORY, "branch": branch, "path": path,
            "commit_sha": result["commit"]["sha"],
            "claimed_author": BOT_NAME,
            "note": "Verify GitHub actor separately; commit metadata alone is insufficient"}
