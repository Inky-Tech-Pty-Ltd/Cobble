"""Bounded Puck writer dispatcher: authorisation to request, not to commit.

McKay has no Puck GitHub App private key or installation token. A dedicated
non-Joe service principal may trigger one allow-listed Actions workflow.
That workflow alone obtains the Puck-GPT App token and authors the commit.
"""
import base64
import json
import os
import re
import urllib.error
import urllib.request

_REPO = "Inky-Tech-Pty-Ltd/InkyTech"
_WORKFLOW = "puck-writer-v1.yml"
_PATH = re.compile(r"docs/experiments/[A-Za-z0-9][A-Za-z0-9._-]{0,75}\.md\Z")
_API = "https://api.github.com"


def _api(method, path, token, payload=None):
    raw = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        _API + path, data=raw, method=method,
        headers={"Authorization": "Bearer " + token,
                 "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28",
                 "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            data = response.read(30000)
            return json.loads(data) if data else {}
    except urllib.error.HTTPError as exc:
        raise PermissionError("GitHub refused Puck dispatch (HTTP %d)" % exc.code) from None


def _dispatch_identity():
    if os.environ.get("COBBLE_MCP_ALLOW_PUCK_DISPATCH") != "1":
        raise PermissionError("Puck Actions dispatcher disabled")
    token = os.environ.get("PUCK_DISPATCH_TOKEN", "")
    if not token.startswith("ghs_") or len(token) > 2048:
        raise PermissionError("Dedicated App installation token unavailable")
    # This is an installation token, not a human OAuth token. The /user
    # endpoint does not authenticate an App installation. Verify access to
    # InkyTech; App identity is established by the trusted token issuer
    # using Puck-Dispatcher's App ID 5549836, never by this check alone.
    installation = _api("GET", "/installation/repositories?per_page=100", token)
    repositories = installation.get("repositories", [])
    if installation.get("total_count") != 1 or len(repositories) != 1 or (
        repositories[0].get("full_name") != _REPO
    ):
        raise PermissionError("Dispatcher token must be limited to InkyTech")
    return token


def submit_write(path, content, message):
    """Trigger only the fixed InkyTech Actions writer; cannot choose workflow."""
    if not isinstance(path, str) or not _PATH.fullmatch(path):
        raise ValueError("Only new docs/experiments/*.md paths are accepted")
    if not isinstance(content, str) or not 0 < len(content.encode("utf-8")) <= 12000:
        raise ValueError("Content must be 1-12000 UTF-8 bytes")
    if not isinstance(message, str) or not 0 < len(message) <= 120 or "\n" in message or "\r" in message:
        raise ValueError("Message must be a single line of up to 120 characters")
    request = {"path": path, "content": content, "message": message}
    encoded = base64.b64encode(json.dumps(request).encode("utf-8")).decode("ascii")
    token = _dispatch_identity()
    _api("POST", "/repos/" + _REPO + "/actions/workflows/" +
         _WORKFLOW + "/dispatches", token,
         {"ref": "main", "inputs": {"request_b64": encoded}})
    return {"submitted": True, "workflow": _WORKFLOW,
            "repository": _REPO, "target": path,
            "note": "Dispatch accepted; check Actions run before claiming a commit"}
