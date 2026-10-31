"""Isolated Unix-socket GitHub Actions dispatcher.

Run as a *separate OS account*, not the Cobble/McKay user. Its private key
must only be readable by that account. The MCP client has socket access,
never key or token access. Not an OS sandbox on its own.
"""
import base64
import json
import os
from pathlib import Path
import socketserver
import subprocess
import time
import urllib.request

APP_ID = 5549836
INSTALLATION_ID = 177074425
REPO = "Inky-Tech-Pty-Ltd/InkyTech"
WORKFLOW = "puck-writer-v1.yml"
API = "https://api.github.com"
MAX_REQUEST = 20000


def b64url(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def jwt_for_app(key_path, now=None):
    now = int(time.time() if now is None else now)
    header = b64url(b'{"alg":"RS256","typ":"JWT"}')
    payload = b64url(json.dumps({"iat": now - 60, "exp": now + 540,
                                 "iss": APP_ID}, separators=(",", ":")).encode())
    unsigned = (header + "." + payload).encode("ascii")
    signed = subprocess.run(["/usr/bin/openssl", "dgst", "-sha256", "-sign",
                             str(key_path)], input=unsigned, capture_output=True,
                            check=True, timeout=5).stdout
    return unsigned.decode() + "." + b64url(signed)


def api(method, route, token, body=None):
    req = urllib.request.Request(API + route, method=method,
        data=None if body is None else json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + token,
                 "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as response:
        data = response.read(25000)
        return json.loads(data) if data else {}


def dispatch(request, key_path):
    # Check the *operation*, not just the eventual Actions workflow.
    from cobble.puck_github_writer import validate_request
    validated = validate_request(request)
    app_jwt = jwt_for_app(key_path)
    token = api("POST", "/app/installations/%d/access_tokens" % INSTALLATION_ID,
                app_jwt, {"repositories": ["InkyTech"],
                          "permissions": {"actions": "write"}})["token"]
    encoded = base64.b64encode(json.dumps(validated).encode()).decode("ascii")
    api("POST", "/repos/" + REPO + "/actions/workflows/" + WORKFLOW + "/dispatches",
        token, {"ref": "main", "inputs": {"request_b64": encoded}})
    return {"submitted": True, "workflow": WORKFLOW, "target": validated["path"]}


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        line = self.rfile.readline(MAX_REQUEST + 1)
        if len(line) > MAX_REQUEST or not line.endswith(b"\n"):
            return
        try:
            request = json.loads(line)
            result = dispatch(request, self.server.private_key)
        except Exception:
            # Never return token, private key, raw GitHub response, or traceback.
            result = {"submitted": False, "error": "dispatch denied or failed"}
        self.wfile.write((json.dumps(result) + "\n").encode())


class Server(socketserver.UnixStreamServer):
    allow_reuse_address = True


def main():
    # Invoked by a dedicated system account with its own HOME and key.
    socket_path = Path(os.environ["PUCK_BROKER_SOCKET"])
    key_path = Path(os.environ["PUCK_DISPATCH_PRIVATE_KEY_FILE"])
    if not key_path.is_file() or key_path.is_symlink():
        raise RuntimeError("Missing protected Puck-Dispatcher key")
    key_stat = key_path.stat()
    if key_stat.st_mode & 0o077 or key_stat.st_uid != os.geteuid():
        raise RuntimeError("Private key must be service-owned and mode 0600")
    if socket_path.exists():
        raise RuntimeError("Socket already exists; investigate before restarting")
    oldmask = os.umask(0o117)  # Unix socket 0660, directory must be restricted too
    try:
        with Server(str(socket_path), Handler) as server:
            server.private_key = key_path
            server.serve_forever()
    finally:
        os.umask(oldmask)


if __name__ == "__main__":
    main()
