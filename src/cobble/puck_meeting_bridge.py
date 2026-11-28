"""Private local bridge from a Puck MCP seat to the restricted guest HTTP surface.

A convenor issues the grant through the local operator console. The secret
never enters a chat/tool argument. The guest server remains the authority
for scope, expiry, attribution, and revocation.
"""
import http.client
import json
import os
from pathlib import Path
import stat
import tempfile

from cobble.meeting_door import MeetingDoor, TOKEN


def _binding(store, room_id, *, create=False):
    door = MeetingDoor(store)
    room_id = door._room(room_id)
    door._safe(create=create)
    folder = door.folder / "puck-seats"
    if folder.is_symlink():
        raise PermissionError("Unsafe Puck seat directory")
    if create:
        folder.mkdir(mode=0o700, exist_ok=True)
    if folder.exists() and (not folder.is_dir() or folder.stat().st_mode & 0o077):
        raise PermissionError("Unsafe Puck seat directory permissions")
    path = folder / (room_id + ".json")
    if path.is_symlink():
        raise PermissionError("Unsafe Puck seat binding")
    return path


def bind_invitation(store, room_id, port, token):
    path = _binding(store, room_id, create=True)
    if not isinstance(port, int) or not 1 <= port <= 65535 or not TOKEN.fullmatch(token):
        raise ValueError("Invalid Puck seat binding")
    fd, tmp = tempfile.mkstemp(prefix=".seat-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            os.fchmod(stream.fileno(), 0o600)
            json.dump({"room_id": room_id, "port": port, "token": token}, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        Path(tmp).unlink(missing_ok=True)


def unbind_invitation(store, room_id):
    _binding(store, room_id).unlink(missing_ok=True)


def _grant(store, room_id):
    if os.environ.get("COBBLE_MCP_ALLOW_PUCK_MEETINGS") != "1":
        raise PermissionError("Puck meeting participation is disabled locally")
    path = _binding(store, room_id)
    try:
        with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "r", encoding="utf-8") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077 or info.st_size > 1024:
                raise PermissionError("Unsafe Puck seat binding")
            grant = json.load(stream)
    except FileNotFoundError:
        raise PermissionError("No Puck invitation for this meeting") from None
    if (not isinstance(grant, dict) or grant.get("room_id") != room_id
            or type(grant.get("port")) is not int or not 1 <= grant["port"] <= 65535
            or not isinstance(grant.get("token"), str) or not TOKEN.fullmatch(grant["token"])):
        raise PermissionError("Invalid Puck seat binding")
    # Check local registry before contacting the port, including expiry and seat.
    if MeetingDoor(store).require(grant["token"]) != {"room_id": room_id, "speaker": "Puck"}:
        raise PermissionError("Puck seat identity or room mismatch")
    return grant


def _request(grant, method, route, body=None):
    port = grant["port"]
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=15)
    try:
        conn.request(method, route, body=json.dumps(body) if body is not None else None,
                     headers={"X-Cobble-Room-Token": grant["token"],
                              "Origin": f"http://127.0.0.1:{port}",
                              "Content-Type": "application/json"})
        response = conn.getresponse()
        if response.status != 200:
            raise PermissionError("Puck meeting invitation refused or unavailable")
        raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError("Meeting exceeds local bridge response budget")
        return json.loads(raw)
    finally:
        conn.close()


def _read(grant):
    result = _request(grant, "GET", "/api/guest/session")
    if result.get("speaker") != "Puck" or result.get("meeting", {}).get("id") != grant["room_id"]:
        raise PermissionError("Puck seat identity or room mismatch")
    return result


def meeting_read(store, room_id):
    return _read(_grant(store, room_id))


def meeting_post(store, room_id, text):
    if not isinstance(text, str) or not 0 < len(text.strip()) <= 2000:
        raise ValueError("Contribution must contain 1–2000 characters")
    grant = _grant(store, room_id)
    _read(grant)
    result = _request(grant, "POST", "/api/guest/post", {"text": text})
    if result.get("speaker") != "Puck":
        raise PermissionError("Unexpected contributor identity; do not retry automatically")
    return result
