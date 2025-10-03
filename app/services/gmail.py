"""Wrapper around the Gmail API."""

from __future__ import annotations

import base64
from email.mime.text import MIMEText
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from app.config import get_settings
from app.services.token_store import get_token_store

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


class GmailClient:
    """Handle OAuth flows and message sending via Gmail."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._token_store = get_token_store()

    def _client_config(
        self,
        client_id_override: Optional[str] = None,
        client_secret_override: Optional[str] = None,
        redirect_override: Optional[str] = None,
    ) -> dict:
        client_id = client_id_override or self._settings.google_client_id
        client_secret = client_secret_override or self._settings.google_client_secret
        redirect_uri = redirect_override or self._settings.google_redirect_uri
        return {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uris": [redirect_uri],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }

    def _build_flow(
        self,
        state: str,
        client_id_override: Optional[str] = None,
        client_secret_override: Optional[str] = None,
        redirect_override: Optional[str] = None,
    ) -> Flow:
        return Flow.from_client_config(
            self._client_config(
                client_id_override=client_id_override,
                client_secret_override=client_secret_override,
                redirect_override=redirect_override,
            ),
            scopes=SCOPES,
            redirect_uri=redirect_override or self._settings.google_redirect_uri,
            state=state,
        )

    def authorization_url(
        self,
        state: str,
        client_id_override: Optional[str] = None,
        client_secret_override: Optional[str] = None,
        redirect_override: Optional[str] = None,
    ) -> str:
        flow = self._build_flow(
            state,
            client_id_override=client_id_override,
            client_secret_override=client_secret_override,
            redirect_override=redirect_override,
        )
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            prompt="consent",
        )
        return auth_url

    def exchange_code(
        self,
        state: str,
        code: str,
        client_id_override: Optional[str] = None,
        client_secret_override: Optional[str] = None,
        redirect_override: Optional[str] = None,
    ) -> Credentials:
        flow = self._build_flow(
            state,
            client_id_override=client_id_override,
            client_secret_override=client_secret_override,
            redirect_override=redirect_override,
        )
        flow.fetch_token(code=code)
        credentials = flow.credentials
        self._token_store.save_credentials(state, credentials)
        return credentials

    def get_credentials(self, user_id: str) -> Optional[Credentials]:
        credentials = self._token_store.load_credentials(user_id)
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            self._token_store.save_credentials(user_id, credentials)
        return credentials

    def send_message(self, credentials: Credentials, to_email: str, subject: str, body: str) -> dict:
        message = MIMEText(body, "plain", "utf-8")
        message["to"] = to_email
        message["subject"] = subject
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        service = build("gmail", "v1", credentials=credentials)
        return service.users().messages().send(userId="me", body={"raw": raw_message}).execute()


_client = GmailClient()


def get_gmail_client() -> GmailClient:
    """Return shared Gmail client."""

    return _client


__all__ = ["GmailClient", "get_gmail_client", "SCOPES"]
