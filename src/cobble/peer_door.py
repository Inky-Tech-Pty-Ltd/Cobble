"""Deliberate local Cobble-to-Cobble participation over the existing guest Door.

No remote HTTP, ambient proxy, automatic posting, retries or supplier calls.
An invitation is a bearer capability, not proof of the holder's identity.
"""
import http.client
import json
from urllib.parse import urlsplit, parse_qs

from cobble.instance_identity import ID_PATTERN, load
from cobble.meeting_door import ROOM_ID, TOKEN

MAX_RESPONSE = 2 * 1024 * 1024


class PeerDoor:
    def __init__(self, store, invitation):
        local = load(store)
        if not local:
            raise PermissionError("Provision a named local instance first")
        if (not isinstance(invitation, dict)
                or invitation.get("speaker") != local["name"]
                or not isinstance(invitation.get("host_instance_id"), str)
                or not ID_PATTERN.fullmatch(invitation["host_instance_id"])
                or invitation["host_instance_id"] == local["instance_id"]
                or not isinstance(invitation.get("room_id"), str)
                or not ROOM_ID.fullmatch(invitation["room_id"])):
            raise PermissionError("Invitation does not address this pilot instance")
        url = urlsplit(invitation.get("guest_url", ""))
        tokens = parse_qs(url.fragment, strict_parsing=True)
        if (url.scheme != "http" or url.hostname != "127.0.0.1"
                or not url.port or url.username is not None or url.password is not None
                or url.path != "/" or url.query or set(tokens) != {"invite"}
                or len(tokens["invite"]) != 1 or not TOKEN.fullmatch(tokens["invite"][0])):
            raise PermissionError("Only explicit loopback guest invitations are supported")
        self.port = url.port
        self._token = tokens["invite"][0]
        self._host_id = invitation["host_instance_id"]
        self._room_id = invitation["room_id"]
        self._speaker = local["name"]

    def _request(self, path, text=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        headers = {"X-Cobble-Room-Token": self._token}
        try:
            if text is None:
                conn.request("GET", path, headers=headers)
            else:
                headers.update({"Origin": f"http://127.0.0.1:{self.port}",
                                "Content-Type": "application/json"})
                conn.request("POST", path, json.dumps({"text": text}), headers)
            response = conn.getresponse()
            if response.status != 200:
                raise PermissionError("Peer Door refused the request")
            raw = response.read(MAX_RESPONSE + 1)
            if len(raw) > MAX_RESPONSE:
                raise ValueError("Peer response exceeds pilot limit")
            return json.loads(raw)
        finally:
            conn.close()

    def read(self):
        data = self._request("/api/guest/session")
        if (data.get("host_instance_id") != self._host_id
                or data.get("meeting", {}).get("id") != self._room_id
                or data.get("speaker") != self._speaker):
            raise PermissionError("Unexpected peer, room or seat")
        return data

    def post(self, text):
        if not isinstance(text, str) or not 0 < len(text.strip()) <= 2000:
            raise ValueError("Contribution must be 1–2000 characters")
        self.read()  # Verify the invited seat before a deliberate write.
        result = self._request("/api/guest/post", text)
        if result.get("speaker") != self._speaker:
            raise RuntimeError("Unverified post outcome; do not retry automatically")
        return result
