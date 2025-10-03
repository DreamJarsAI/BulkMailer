"""Jinja-based templating helpers."""

from __future__ import annotations

from typing import Iterable, List

from jinja2 import Environment, StrictUndefined, TemplateError

from app.models.domain import Recipient, RenderedEmail, TemplateContent

_ALLOWED_FIELDS = {"title", "first_name", "last_name", "email"}

_env = Environment(autoescape=True, undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True)


class TemplateRenderingError(Exception):
    """Raised when the user-supplied template cannot be rendered."""


def _recipient_context(recipient: Recipient) -> dict[str, str]:
    return {
        "title": recipient.title,
        "first_name": recipient.first_name,
        "last_name": recipient.last_name,
        "email": recipient.email,
    }


def render_email(template: TemplateContent, recipient: Recipient) -> RenderedEmail:
    """Render personalized subject and body for a recipient."""

    try:
        subject = _env.from_string(template.subject_template).render(
            **_recipient_context(recipient)
        )
        body = _env.from_string(template.body_template).render(
            **_recipient_context(recipient)
        )
    except TemplateError as exc:
        raise TemplateRenderingError(str(exc)) from exc

    return RenderedEmail(recipient=recipient, subject=subject.strip(), body=body.strip())


def render_batch(template: TemplateContent, recipients: Iterable[Recipient]) -> List[RenderedEmail]:
    """Render all emails and return preview objects."""

    return [render_email(template, recipient) for recipient in recipients]


__all__ = [
    "TemplateRenderingError",
    "render_email",
    "render_batch",
]
