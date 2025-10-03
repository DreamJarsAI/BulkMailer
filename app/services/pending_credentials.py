"""Ephemeral holder for user-supplied OAuth credentials."""

from __future__ import annotations

from threading import Lock
from typing import Optional, Tuple


class PendingCredentialStore:
    """In-memory map keyed by session id."""

    def __init__(self) -> None:
        self._data: dict[str, Tuple[str, str]] = {}
        self._lock = Lock()

    def set(self, session_id: str, client_id: str, client_secret: str) -> None:
        with self._lock:
            self._data[session_id] = (client_id, client_secret)

    def pop(self, session_id: str) -> Optional[Tuple[str, str]]:
        with self._lock:
            return self._data.pop(session_id, None)

    def peek(self, session_id: str) -> Optional[Tuple[str, str]]:
        with self._lock:
            return self._data.get(session_id)


_store = PendingCredentialStore()


def get_pending_store() -> PendingCredentialStore:
    return _store


__all__ = ["get_pending_store", "PendingCredentialStore"]
