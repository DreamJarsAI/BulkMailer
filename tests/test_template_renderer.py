from app.models.domain import Recipient, TemplateContent
from app.services.template_renderer import TemplateRenderingError, render_email


def test_render_email_renders_placeholders() -> None:
    recipient = Recipient(title="Dr.", first_name="Ada", last_name="Lovelace", email="ada@example.com")
    template = TemplateContent(
        subject_template="Hello {{ first_name }}",
        body_template="Dear {{ title }} {{ last_name }},\nWelcome!",
    )
    rendered = render_email(template, recipient)
    assert rendered.subject == "Hello Ada"
    assert "Dear Dr. Lovelace" in rendered.body


def test_render_email_raises_for_unknown_variable() -> None:
    recipient = Recipient(title="Dr.", first_name="Ada", last_name="Lovelace", email="ada@example.com")
    template = TemplateContent(
        subject_template="Hello {{ missing }}",
        body_template="Body",
    )
    try:
        render_email(template, recipient)
    except TemplateRenderingError:
        pass
    else:
        raise AssertionError("Expected TemplateRenderingError")
