"""Puck MCP request client. Never handles credentials, only a Unix socket."""
import json
import os
import re
import socket

_PATH = re.compile(r"docs/experiments/[A-Za-z0-9][A-Za-z0-9._-]{0,75}\.md\Z")


def validate_request(request):
    if not isinstance(request, dict) or set(request) != {"path", "content", "message"}:
        raise ValueError("Unexpected Puck request fields")
    path, content, message = request["path"], request["content"], request["message"]
    if not isinstance(path, str) or not _PATH.fullmatch(path):
        raise ValueError("Only new experiment Markdown paths are accepted")
    if not isinstance(content, str) or not 0 < len(content.encode("utf-8")) <= 12000:
        raise ValueError("Content must be 1-12000 UTF-8 bytes")
    if not isinstance(message, str) or not 0 < len(message) <= 120 or "\n" in message or "\r" in message:
        raise ValueError("Invalid commit message")
    return request


def submit_write(path, content, message):
    request = validate_request({"path": path, "content": content, "message": message})
    if os.environ.get("COBBLE_MCP_ALLOW_PUCK_DISPATCH") != "1":
        raise PermissionError("Puck dispatch disabled")
    sock_path = os.environ.get("PUCK_BROKER_SOCKET", "")
    if not sock_path.startswith("/run/puck-dispatch/") or len(sock_path) > 200:
        raise PermissionError("Dedicated Puck broker socket unavailable")
    data = (json.dumps(request) + "\n").encode()
    if len(data) > 20000:
        raise ValueError("Dispatch request too large")
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(20)
        client.connect(sock_path)
        client.sendall(data)
        response = bytearray()
        while not response.endswith(b"\n"):
            part = client.recv(4096)
            if not part or len(response) + len(part) > 10000:
                raise RuntimeError("Invalid broker response")
            response.extend(part)
    result = json.loads(response)
    if not result.get("submitted"):
        raise PermissionError("Broker denied or failed the writing request")
    return result
