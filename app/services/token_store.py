"""Encrypted storage for Google refresh tokens."""

from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from google.oauth2.credentials import Credentials

from app.config import get_settings


class TokenStore:
    """Persist Google OAuth credentials using Fernet encryption."""

    def __init__(self) -> None:
        settings = get_settings()
        self._path: Path = settings.token_storage_path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._fernet = Fernet(settings.fernet_key.encode("utf-8"))
        self._lock = Lock()

    def _load_data(self) -> dict[str, str]:
        if not self._path.exists():
            return {}
        try:
            encrypted = self._path.read_bytes()
            if not encrypted:
                return {}
            decrypted = self._fernet.decrypt(encrypted)
        except (InvalidToken, ValueError):  # pragma: no cover - corrupted file
            return {}
        return json.loads(decrypted.decode("utf-8"))

    def _save_data(self, data: dict[str, str]) -> None:
        payload = json.dumps(data).encode("utf-8")
        encrypted = self._fernet.encrypt(payload)
        self._path.write_bytes(encrypted)

    def save_credentials(self, user_id: str, credentials: Credentials) -> None:
        with self._lock:
            data = self._load_data()
            data[user_id] = credentials.to_json()
            self._save_data(data)

    def load_credentials(self, user_id: str) -> Optional[Credentials]:
        with self._lock:
            data = self._load_data()
            if user_id not in data:
                return None
            info = json.loads(data[user_id]) if isinstance(data[user_id], str) else data[user_id]
            return Credentials.from_authorized_user_info(info)

    def clear(self, user_id: str) -> None:
        with self._lock:
            data = self._load_data()
            data.pop(user_id, None)
            self._save_data(data)


_store = TokenStore()


def get_token_store() -> TokenStore:
    """Return singleton token store."""

    return _store


__all__ = ["TokenStore", "get_token_store"]
