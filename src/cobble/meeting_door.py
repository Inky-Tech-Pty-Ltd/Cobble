"""One-room admission Door for the first trusted human collaborator.

Only a digest of each high-entropy invitation is persisted. An invitation
admits its bearer to one meeting, never to the operator's Cobble console.
The actual person behind a bearer link must be verified out of band.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import tempfile
import threading


ROOM_ID = re.compile(r"(?:default|[0-9a-f]{16})\Z")
TOKEN = re.compile(r"[A-Za-z0-9_-]{32,128}\Z")
VALID_DAYS = 7
MAX_INVITES = 128


class MeetingDoor:
    def __init__(self, store):
        self.store = Path(store).expanduser().resolve()
        if any((p / ".git").exists() for p in (self.store, *self.store.parents)):
            raise ValueError("Private invitations must stay outside Git")
        self.folder = self.store / "snug" / "doors"
        self.file = self.folder / "invitations.json"
        self.lock = threading.Lock()

    def _safe(self, create=False):
        for directory in (self.store / "snug", self.folder):
            if directory.is_symlink():
                raise PermissionError("Invitation path cannot be a symlink")
            if create:
                directory.mkdir(parents=True, exist_ok=True, mode=0o700)
                directory.chmod(0o700)
            elif directory.exists() and not directory.is_dir():
                raise PermissionError("Invalid invitation directory")
        if self.file.is_symlink():
            raise PermissionError("Invitation registry cannot be a symlink")

    def _read(self):
        self._safe()
        if not self.file.exists():
            return {}
        records = json.loads(self.file.read_text(encoding="utf-8"))
        if (not isinstance(records, dict) or len(records) > MAX_INVITES
                or any(not re.fullmatch(r"[0-9a-f]{64}", k) or
                       not isinstance(v, dict) or
                       not ROOM_ID.fullmatch(v.get("room_id", "")) or
                       v.get("speaker") != "Sankarshan" or
                       not isinstance(v.get("expires_utc"), str) or
                       not isinstance(v.get("revoked"), bool) or
                       ("first_seen_utc" in v and
                        not isinstance(v["first_seen_utc"], str))
                       for k, v in records.items())):
            raise ValueError("Corrupt invitation registry")
        return records

    def _write(self, records):
        self._safe(create=True)
        raw = (json.dumps(records, indent=2, sort_keys=True) + "\n").encode("utf-8")
        fd, tmp = tempfile.mkstemp(prefix=".doors-", dir=self.folder)
        try:
            with os.fdopen(fd, "wb") as stream:
                os.fchmod(stream.fileno(), 0o600)
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            if self.file.is_symlink():
                raise PermissionError("Invitation registry cannot be a symlink")
            os.replace(tmp, self.file)
            folder_fd = os.open(self.folder, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(folder_fd)
            finally:
                os.close(folder_fd)
        finally:
            Path(tmp).unlink(missing_ok=True)

    @staticmethod
    def _room(room_id):
        if not isinstance(room_id, str) or not ROOM_ID.fullmatch(room_id):
            raise ValueError("Invalid invited room")
        return room_id

    def issue(self, *, room_id):
        """Return a secret exactly once; an older invitation to this room expires."""
        room_id = self._room(room_id)
        with self.lock:
            records = self._read()
            now = datetime.now(timezone.utc)
            records = {
                k: v for k, v in records.items()
                if datetime.fromisoformat(v["expires_utc"]) > now
            }
            for item in records.values():
                if item["room_id"] == room_id:
                    item["revoked"] = True
            if len(records) >= MAX_INVITES:
                raise PermissionError("Invitation registry is full")
            token = secrets.token_urlsafe(32)
            digest = hashlib.sha256(token.encode("ascii")).hexdigest()
            records[digest] = {
                "room_id": room_id, "speaker": "Sankarshan",
                "created_utc": now.isoformat(),
                "expires_utc": (now + timedelta(days=VALID_DAYS)).isoformat(),
                "revoked": False,
            }
            self._write(records)
            return {"token": token, "room_id": room_id,
                    "expires_utc": records[digest]["expires_utc"]}

    def require(self, token, *, mark_arrival=False):
        """Check this bearer, optionally remembering their first room visit.

        Arrival proves a link was used, *not* that the real Sankarshan was
        holding it. Polling a room does not continually rewrite the ledger.
        """
        if not isinstance(token, str) or not TOKEN.fullmatch(token):
            raise PermissionError("Invitation not recognised")
        digest = hashlib.sha256(token.encode("ascii")).hexdigest()
        with self.lock:
            records = self._read()
            record = records.get(digest)
            now = datetime.now(timezone.utc)
            if (not record or record["revoked"] or
                    datetime.fromisoformat(record["expires_utc"]) <= now):
                raise PermissionError("Invitation not recognised")
            if mark_arrival and not record.get("first_seen_utc"):
                record["first_seen_utc"] = now.isoformat()
                self._write(records)
            return {"room_id": record["room_id"], "speaker": record["speaker"]}

    def status(self, *, room_id):
        """Operator-only view. No bearer secret or unrelated room is returned."""
        room_id = self._room(room_id)
        with self.lock:
            now = datetime.now(timezone.utc)
            active = next((item for item in self._read().values()
                           if item["room_id"] == room_id and not item["revoked"]
                           and datetime.fromisoformat(item["expires_utc"]) > now), None)
        return {"room_id": room_id, "open": active is not None,
                "arrived": bool(active and active.get("first_seen_utc")),
                "expires_utc": active["expires_utc"] if active else None}

    def revoke(self, *, room_id):
        room_id = self._room(room_id)
        with self.lock:
            records = self._read()
            changed = 0
            for item in records.values():
                if item["room_id"] == room_id and not item["revoked"]:
                    item["revoked"] = True
                    changed += 1
            if changed:
                self._write(records)
            return {"revoked_count": changed}
