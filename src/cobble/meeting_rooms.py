"""Durable, local meeting identity and title registry.

The legacy 'default' meeting retains its original event directory unchanged.
New meetings have independent bounded-id directories, all outside Git.
A mutable display title is not an authority, credential or pathname.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import secrets
import tempfile
import threading


ROOM_ID = re.compile(r"[0-9a-f]{16}\Z")
MAX_ROOMS = 128
DEFAULT_ORDERS = (
    "Welcome to this Cobble meeting. The convenor sets the agenda, invites participants "
    "and controls who may speak for the room. Everyone at the table shares the tabled "
    "material. The top-precedence AI at the table may be asked to summarise, propose or "
    "record a decision for the room. Cobble itself marks that authority; participants "
    "cannot claim it. The room's output is the convenor's opening agenda, together with "
    "contributions explicitly attributed as speaking for the room, and their attachments. "
    "Estimated AI costs are visible to the convenor. Rooms operate within finite "
    "resources and may cooperate in larger networks. The convenor can adjourn, close, "
    "reopen, or redact outward-facing contributions without erasing historical evidence."
)



class MeetingCatalog:
    def __init__(self, store):
        self.store = Path(store).expanduser().resolve()
        if any((p / ".git").exists() for p in (self.store, *self.store.parents)):
            raise ValueError("Private meetings must stay outside Git")
        self.base = self.store / "snug" / "live"
        self.rooms = self.base / "rooms"
        self._lock = threading.Lock()

    @staticmethod
    def _title(value):
        if (not isinstance(value, str) or not value.strip() or
            len(value.strip()) > 100 or
            any(ord(ch) < 32 or ord(ch) == 127 for ch in value)):
            raise ValueError("Meeting title must be 1–100 printable characters")
        return value.strip()

    def _folder(self, meeting_id):
        if meeting_id == "default":
            return self.base / "default"
        if not isinstance(meeting_id, str) or not ROOM_ID.fullmatch(meeting_id):
            raise ValueError("Invalid meeting ID")
        return self.rooms / meeting_id

    def _safe_dirs(self, folder, create=False):
        levels = [self.store / "snug", self.base]
        if folder != self.base / "default":
            levels.append(self.rooms)
        levels.append(folder)
        for directory in levels:
            if directory.is_symlink():
                raise PermissionError("Private meeting path cannot be a symlink")
            if create:
                directory.mkdir(mode=0o700, parents=True, exist_ok=True)
                directory.chmod(0o700)
            elif directory.exists() and not directory.is_dir():
                raise PermissionError("Unsafe meeting directory")

    def _read(self, meeting_id):
        folder = self._folder(meeting_id)
        self._safe_dirs(folder)
        path = folder / "room.json"
        if path.is_symlink():
            raise PermissionError("Unsafe meeting metadata")
        if not path.exists():
            return None
        result = json.loads(path.read_text(encoding="utf-8"))
        if (result.get("id") != meeting_id or not isinstance(result.get("title"), str)
            or not isinstance(result.get("created_utc"), str)):
            raise ValueError("Meeting metadata mismatch")
        self._title(result["title"])
        return result

    def _write(self, meeting_id, info, *, new=False):
        folder = self._folder(meeting_id)
        self._safe_dirs(folder, create=True)
        target = folder / "room.json"
        if target.is_symlink() or (new and target.exists()):
            raise PermissionError("Unsafe or existing meeting metadata")
        raw = (json.dumps(info, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
        fd, temp = tempfile.mkstemp(prefix=".room-", dir=folder)
        try:
            with os.fdopen(fd, "wb") as stream:
                os.fchmod(stream.fileno(), 0o600)
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            if new:
                os.link(temp, target)  # Atomic create, never overwrite.
            else:
                os.replace(temp, target)  # Atomic title change.
            dirfd = os.open(folder, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(dirfd)
            finally:
                os.close(dirfd)
        finally:
            Path(temp).unlink(missing_ok=True)

    def _list(self):
        default = self._read("default") or {
            "id": "default", "title": "Current meeting", "created_utc": ""}
        result = [default]
        if self.rooms.is_symlink():
            raise PermissionError("Unsafe meeting registry directory")
        if self.rooms.exists():
            for folder in self.rooms.iterdir():
                if folder.is_symlink():
                    raise PermissionError("Unsafe meeting in registry")
                if folder.is_dir() and ROOM_ID.fullmatch(folder.name):
                    item = self._read(folder.name)
                    if item is not None:
                        result.append(item)
        return [result[0], *sorted(result[1:], key=lambda item: item["created_utc"], reverse=True)]

    def list(self):
        with self._lock:
            return self._list()

    def require(self, meeting_id):
        with self._lock:
            if meeting_id == "default":
                self._read("default")
                return meeting_id
            if self._read(meeting_id) is None:
                raise ValueError("Unknown meeting")
            return meeting_id

    def create(self, *, title="New meeting"):
        title = self._title(title)
        with self._lock:
            if len(self._list()) >= MAX_ROOMS:
                raise PermissionError("Local meeting limit reached")
            meeting_id = secrets.token_hex(8)
            while (self.rooms / meeting_id).exists():
                meeting_id = secrets.token_hex(8)
            item = {"id": meeting_id, "title": title,
                    "created_utc": datetime.now(timezone.utc).isoformat(),
                    "standing_orders": DEFAULT_ORDERS, "state": "open",
                    "precedence": ["openai", "claude", "mistral"],
                    "room_voice": [], "redacted": []}
            self._write(meeting_id, item, new=True)
            return item

    def rename(self, *, meeting_id, title):
        title = self._title(title)
        with self._lock:
            current = self._read(meeting_id)
            if current is None:
                if meeting_id != "default":
                    raise ValueError("Unknown meeting")
                current = {"id": "default", "title": "Current meeting",
                           "created_utc": datetime.now(timezone.utc).isoformat()}
            updated = {**current, "title": title}
            self._write(meeting_id, updated)
            return updated

    def configure(self, *, meeting_id, standing_orders=None, state=None,
                  precedence=None, voice_event=None, redact_event=None):
        """Redaction withdraws publication, never deletes the conversation."""
        with self._lock:
            current = self._read(meeting_id)
            if current is None:
                if meeting_id != "default":
                    raise ValueError("Unknown meeting")
                current = {"id": "default", "title": "Current meeting",
                           "created_utc": datetime.now(timezone.utc).isoformat()}
            updated = dict(current)
            if standing_orders is not None:
                if (not isinstance(standing_orders, str) or
                    not 1 <= len(standing_orders.strip()) <= 8000):
                    raise ValueError("Standing orders must contain 1–8000 characters")
                updated["standing_orders"] = standing_orders.strip()
            if state is not None:
                if state not in ("open", "adjourned", "closed"):
                    raise ValueError("Invalid meeting state")
                updated["state"] = state
            if precedence is not None:
                if (not isinstance(precedence, list) or
                    len(precedence) != 3 or
                    set(precedence) != {"openai", "claude", "mistral"}):
                    raise ValueError("Invalid precedence")
                updated["precedence"] = precedence
            if voice_event is not None:
                if (not isinstance(voice_event, str) or
                    not re.fullmatch(r"[0-9]{20}-[0-9a-f]{12}", voice_event)):
                    raise ValueError("Invalid contribution ID")
                voice = list(updated.get("room_voice", []))
                if voice_event not in voice:
                    voice.append(voice_event)
                updated["room_voice"] = voice
                updated["redacted"] = [x for x in updated.get("redacted", [])
                                       if x != voice_event]
            if redact_event is not None:
                if redact_event not in updated.get("room_voice", []):
                    raise ValueError("Only room-voice contributions can be redacted")
                updated["redacted"] = list(dict.fromkeys(
                    [*updated.get("redacted", []), redact_event]))
            self._write(meeting_id, updated)
            return updated
