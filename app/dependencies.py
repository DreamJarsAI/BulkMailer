"""Common FastAPI dependencies."""

from __future__ import annotations

import secrets

from fastapi import Request


SESSION_KEY = "session_id"


def get_session_id(request: Request) -> str:
    """Return a stable session identifier stored in the signed cookie."""

    session_id = request.session.get(SESSION_KEY)
    if not session_id:
        session_id = secrets.token_urlsafe(16)
        request.session[SESSION_KEY] = session_id
    return session_id


__all__ = ["get_session_id"]
