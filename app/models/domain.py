"""Domain models used by the application."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


class Recipient(BaseModel):
    """A single email recipient parsed from the uploaded CSV."""

    title: str = Field(..., min_length=1, max_length=40)
    first_name: str = Field(..., min_length=1, max_length=120)
    last_name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr

    def display_name(self) -> str:
        """Return a formatted full name."""

        return f"{self.title.strip()} {self.first_name.strip()} {self.last_name.strip()}".strip()


class TemplateContent(BaseModel):
    """Subject and body template provided by the user."""

    subject_template: str = ""
    body_template: str
    source_filename: Optional[str] = None


class RenderedEmail(BaseModel):
    """Preview of the personalized email."""

    recipient: Recipient
    subject: str
    body: str
    approved: bool = True
    status: str = Field("pending", description="pending|sent|failed|skipped")
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None


class BatchState(BaseModel):
    """Holds all in-memory data for a user's workflow."""

    recipients: List[Recipient] = Field(default_factory=list)
    template: Optional[TemplateContent] = None
    messages: List[RenderedEmail] = Field(default_factory=list)
    gmail_client_id: Optional[str] = None
    gmail_client_secret: Optional[str] = None
    gmail_authorized: bool = False

    def approvals(self) -> Dict[str, bool]:
        """Return approval flags keyed by recipient email."""

        return {message.recipient.email: message.approved for message in self.messages}


__all__ = [
    "Recipient",
    "TemplateContent",
    "RenderedEmail",
    "BatchState",
]
