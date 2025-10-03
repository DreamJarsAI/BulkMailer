"""Ephemeral in-memory storage for user batch data."""

from __future__ import annotations

from datetime import datetime, timedelta
from threading import Lock
from typing import Dict

from app.config import get_settings
from app.models.domain import BatchState


class BatchStore:
    """In-memory, per-session storage with a simple TTL purge mechanism."""

    def __init__(self) -> None:
        self._data: Dict[str, tuple[datetime, BatchState]] = {}
        self._lock = Lock()
        self._ttl = timedelta(minutes=get_settings().session_lifetime_minutes)

    def _purge_expired(self) -> None:
        cutoff = datetime.utcnow() - self._ttl
        expired = [key for key, (ts, _) in self._data.items() if ts < cutoff]
        for key in expired:
            self._data.pop(key, None)

    def get(self, session_id: str) -> BatchState:
        """Fetch existing batch state or create a new one."""

        with self._lock:
            self._purge_expired()
            if session_id not in self._data:
                self._data[session_id] = (datetime.utcnow(), BatchState())
            state = self._data[session_id][1]
            self._data[session_id] = (datetime.utcnow(), state)
            return state

    def clear(self, session_id: str) -> None:
        """Remove batch data for the session."""

        with self._lock:
            self._data.pop(session_id, None)


_store = BatchStore()


def get_store() -> BatchStore:
    """Return shared store instance."""

    return _store


__all__ = ["BatchStore", "get_store"]
