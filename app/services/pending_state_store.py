"""File-backed store for ephemeral OAuth client credentials keyed by state.

This avoids relying on cookies during the OAuth redirect by persisting the
client_id and client_secret associated with the generated `state` token.
Values are encrypted at rest using the app's Fernet key.
"""

from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Optional, Tuple

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings


class StateCredentialStore:
    """Persist minimal credentials keyed by OAuth `state`."""

    def __init__(self) -> None:
        settings = get_settings()
        # Reuse the data directory; keep a separate file from token storage
        self._path: Path = Path("data/pending_credentials.json")
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._fernet = Fernet(settings.fernet_key.encode("utf-8"))
        self._lock = Lock()

    def _load(self) -> dict[str, dict[str, str]]:
        if not self._path.exists():
            return {}
        try:
            raw = self._path.read_bytes()
            if not raw:
                return {}
            decrypted = self._fernet.decrypt(raw)
            return json.loads(decrypted.decode("utf-8"))
        except (InvalidToken, ValueError):
            return {}

    def _save(self, data: dict[str, dict[str, str]]) -> None:
        payload = json.dumps(data).encode("utf-8")
        encrypted = self._fernet.encrypt(payload)
        self._path.write_bytes(encrypted)

    def set(self, state: str, client_id: str, client_secret: str) -> None:
        with self._lock:
            data = self._load()
            data[state] = {"client_id": client_id, "client_secret": client_secret}
            self._save(data)

    def pop(self, state: str) -> Optional[Tuple[str, str]]:
        with self._lock:
            data = self._load()
            record = data.pop(state, None)
            self._save(data)
            if not record:
                return None
            return record["client_id"], record["client_secret"]

    def peek(self, state: str) -> Optional[Tuple[str, str]]:
        with self._lock:
            data = self._load()
            record = data.get(state)
            if not record:
                return None
            return record["client_id"], record["client_secret"]


_state_store = StateCredentialStore()


def get_state_store() -> StateCredentialStore:
    return _state_store


__all__ = ["StateCredentialStore", "get_state_store"]

