"""Web routes for the email batch application."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from urllib.parse import quote_plus

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette import status

from app.config import get_settings
from app.dependencies import get_session_id
from app.models.domain import RenderedEmail, TemplateContent
from app.services.csv_loader import CSVParsingError, ParsedCSV, parse_recipients
from app.services.docx_loader import DocxProcessingError, extract_plain_text
from app.services.gmail import GmailClient, get_gmail_client
from app.services.token_store import get_token_store
from app.services.store import get_store
from app.services.template_renderer import (
    TemplateRenderingError,
    render_batch,
    render_email,
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _get_gmail_client() -> GmailClient:
    return get_gmail_client()


@router.get("/", response_class=HTMLResponse)
async def landing(request: Request, session_id: str = Depends(get_session_id)) -> HTMLResponse:
    store = get_store()
    state = store.get(session_id)
    settings = get_settings()
    redirect_uri = settings.google_redirect_uri
    alt_redirect_uri = redirect_uri.replace("localhost", "127.0.0.1")
    context = {
        "request": request,
        "client_id": state.gmail_client_id or "",
        "has_secret": bool(state.gmail_client_secret),
        "gmail_authorized": state.gmail_authorized,
        "message": request.query_params.get("message"),
        "error": request.query_params.get("error"),
        "redirect_uri": redirect_uri,
        "alt_redirect_uri": alt_redirect_uri,
    }
    return templates.TemplateResponse("landing.html", context)


@router.post("/credentials")
async def save_credentials(
    session_id: str = Depends(get_session_id),
    client_id: str = Form(""),
    client_secret: str = Form(""),
) -> RedirectResponse:
    state = get_store().get(session_id)
    errors = []
    client_id = client_id.strip()
    client_secret = client_secret.strip()

    if not client_id:
        errors.append("Client ID is required.")
    if not client_secret:
        errors.append("Client secret is required.")

    if errors:
        return RedirectResponse(
            url=f"/?error={quote_plus(' '.join(errors))}",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    state.gmail_client_id = client_id
    state.gmail_client_secret = client_secret
    state.gmail_authorized = False
    get_token_store().clear(session_id)

    return RedirectResponse(url="/auth/google/start", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/recipients", response_class=HTMLResponse)
async def recipients_form(
    request: Request,
    session_id: str = Depends(get_session_id),
    message: Optional[str] = None,
) -> HTMLResponse:
    state = get_store().get(session_id)
    context = {
        "request": request,
        "recipients": state.recipients,
        "template": state.template,
        "errors": [],
        "message": message,
        "has_credentials": bool(state.gmail_client_id and state.gmail_client_secret),
        "draft_body": state.template.body_template if state.template else "",
        "draft_subject": state.template.subject_template if state.template else "",
    }
    return templates.TemplateResponse("recipients.html", context)


@router.post("/recipients", response_class=HTMLResponse)
async def recipients_upload(
    request: Request,
    session_id: str = Depends(get_session_id),
    csv_file: UploadFile = File(...),
) -> HTMLResponse:
    store = get_store()
    state = store.get(session_id)
    try:
        result: ParsedCSV = parse_recipients(csv_file)
    except CSVParsingError as exc:
        context = {
            "request": request,
            "recipients": state.recipients,
            "errors": [str(exc)],
            "message": None,
            "template": state.template,
            "has_credentials": bool(state.gmail_client_id and state.gmail_client_secret),
            "draft_body": state.template.body_template if state.template else "",
            "draft_subject": state.template.subject_template if state.template else "",
        }
        return templates.TemplateResponse("recipients.html", context, status_code=status.HTTP_400_BAD_REQUEST)

    if result.errors:
        context = {
            "request": request,
            "recipients": result.recipients,
            "errors": result.errors,
            "message": None,
            "template": state.template,
            "has_credentials": bool(state.gmail_client_id and state.gmail_client_secret),
            "draft_body": state.template.body_template if state.template else "",
            "draft_subject": state.template.subject_template if state.template else "",
        }
        return templates.TemplateResponse("recipients.html", context, status_code=status.HTTP_400_BAD_REQUEST)

    if not result.recipients:
        context = {
            "request": request,
            "recipients": [],
            "errors": ["No valid rows found in the CSV."],
            "message": None,
            "template": state.template,
            "has_credentials": bool(state.gmail_client_id and state.gmail_client_secret),
            "draft_body": state.template.body_template if state.template else "",
            "draft_subject": state.template.subject_template if state.template else "",
        }
        return templates.TemplateResponse("recipients.html", context, status_code=status.HTTP_400_BAD_REQUEST)

    state.recipients = result.recipients
    state.template = None
    state.messages = []
    return RedirectResponse(url="/recipients", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/template", response_class=HTMLResponse)
async def template_form(
    request: Request,
    session_id: str = Depends(get_session_id),
    message: Optional[str] = None,
) -> HTMLResponse:
    return RedirectResponse(url="/recipients", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/template", response_class=HTMLResponse)
async def template_submit(
    request: Request,
    session_id: str = Depends(get_session_id),
    subject_text: str = Form(""),
    body_text: str = Form(""),
    template_file: Optional[UploadFile] = File(None),
) -> HTMLResponse:
    state = get_store().get(session_id)
    if not state.recipients:
        return RedirectResponse(url="/recipients", status_code=status.HTTP_303_SEE_OTHER)

    subject = subject_text.strip()
    body = body_text.strip()
    source_filename: Optional[str] = None

    if template_file and template_file.filename:
        data = await template_file.read()
        template_file.file.seek(0)
        source_filename = template_file.filename
        if template_file.filename.lower().endswith(".docx"):
            try:
                body = extract_plain_text(data)
            except DocxProcessingError as exc:
                context = {
                    "request": request,
                    "recipients": state.recipients,
                    "template": state.template,
                    "errors": [],
                    "message": None,
                    "template_error": str(exc),
                    "draft_body": body_text,
                    "draft_subject": subject,
                    "has_credentials": bool(state.gmail_client_id and state.gmail_client_secret),
                }
                return templates.TemplateResponse(
                    "recipients.html",
                    context,
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
        else:
            try:
                body = data.decode("utf-8")
            except UnicodeDecodeError:
                context = {
                    "request": request,
                    "recipients": state.recipients,
                    "template": state.template,
                    "errors": [],
                    "message": None,
                    "template_error": "Template text file must be UTF-8 encoded.",
                    "draft_body": body_text,
                    "draft_subject": subject,
                    "has_credentials": bool(state.gmail_client_id and state.gmail_client_secret),
                }
                return templates.TemplateResponse(
                    "recipients.html",
                    context,
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

    if not subject:
        context = {
            "request": request,
            "recipients": state.recipients,
            "template": state.template,
            "errors": [],
            "message": None,
            "template_error": "Please provide an email subject.",
            "draft_body": body_text,
            "draft_subject": subject,
            "has_credentials": bool(state.gmail_client_id and state.gmail_client_secret),
        }
        return templates.TemplateResponse(
            "recipients.html",
            context,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if not body:
        context = {
            "request": request,
            "recipients": state.recipients,
            "template": state.template,
            "errors": [],
            "message": None,
            "template_error": "Please provide the email body.",
            "draft_body": body_text,
            "draft_subject": subject,
            "has_credentials": bool(state.gmail_client_id and state.gmail_client_secret),
        }
        return templates.TemplateResponse(
            "recipients.html",
            context,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    template = TemplateContent(
        subject_template=subject,
        body_template=body,
        source_filename=source_filename,
    )
    try:
        messages = render_batch(template, state.recipients)
    except TemplateRenderingError as exc:
        context = {
            "request": request,
            "recipients": state.recipients,
            "template": state.template,
            "errors": [],
            "message": None,
            "template_error": str(exc),
            "draft_body": body,
            "draft_subject": subject,
            "has_credentials": bool(state.gmail_client_id and state.gmail_client_secret),
        }
        return templates.TemplateResponse(
            "recipients.html",
            context,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    state.template = template
    state.messages = messages

    return RedirectResponse(url="/preview", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/preview", response_class=HTMLResponse)
async def preview(
    request: Request,
    session_id: str = Depends(get_session_id),
    message: Optional[str] = None,
) -> HTMLResponse:
    state = get_store().get(session_id)
    if not state.recipients or not state.template:
        return RedirectResponse(url="/recipients", status_code=status.HTTP_303_SEE_OTHER)

    context = {
        "request": request,
        "messages": state.messages,
        "message": message or request.query_params.get("message"),
        "error": request.query_params.get("error"),
        "auth_status": request.query_params.get("auth"),
        "subject": state.template.subject_template if state.template else "",
        "gmail_authorized": state.gmail_authorized,
    }
    return templates.TemplateResponse("preview.html", context)


@router.post("/preview/{index}/toggle")
async def toggle_approval(
    index: int,
    session_id: str = Depends(get_session_id),
) -> RedirectResponse:
    state = get_store().get(session_id)
    if index < 0 or index >= len(state.messages):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    state.messages[index].approved = not state.messages[index].approved
    if not state.messages[index].approved and state.messages[index].status == "sent":
        state.messages[index].status = "pending"
        state.messages[index].error_message = None
        state.messages[index].sent_at = None
    return RedirectResponse(url="/preview", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/preview/update")
async def update_preview(
    request: Request,
    session_id: str = Depends(get_session_id),
) -> RedirectResponse:
    state = get_store().get(session_id)
    if not state.messages or not state.template:
        return RedirectResponse(url="/recipients", status_code=status.HTTP_303_SEE_OTHER)

    form = await request.form()

    for index, message in enumerate(state.messages):
        body_value = form.get(f"body_{index}")
        if body_value is not None:
            message.body = str(body_value)

    for message in state.messages:
        rendered = render_email(state.template, message.recipient)
        message.subject = rendered.subject

    return RedirectResponse(
        url=f"/preview?message={quote_plus('Changes saved.')}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/auth/google/start")
async def auth_start(session_id: str = Depends(get_session_id)) -> RedirectResponse:
    state = get_store().get(session_id)
    if not (state.gmail_client_id and state.gmail_client_secret):
        return RedirectResponse(
            url=f"/?error={quote_plus('Please add your Google OAuth client ID and secret before connecting.')}",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    auth_url = _get_gmail_client().authorization_url(
        session_id,
        client_id_override=state.gmail_client_id,
        client_secret_override=state.gmail_client_secret,
        redirect_override=get_settings().google_redirect_uri,
    )
    return RedirectResponse(auth_url)


@router.get("/auth/google/callback")
async def auth_callback(
    request: Request,
    state: str,
    code: Optional[str] = None,
    error: Optional[str] = None,
) -> RedirectResponse:
    session_id = request.session.get("session_id")
    if not session_id or state != session_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session state")

    if error:
        return RedirectResponse(url=f"/preview?auth=error&message={error}")

    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing authorization code")

    state_data = get_store().get(session_id)
    if not (state_data.gmail_client_id and state_data.gmail_client_secret):
        return RedirectResponse(
            url=f"/?error={quote_plus('Missing client credentials; please add them and try connecting again.')}",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    gmail = _get_gmail_client()
    gmail.exchange_code(
        session_id,
        code,
        client_id_override=state_data.gmail_client_id,
        client_secret_override=state_data.gmail_client_secret,
        redirect_override=get_settings().google_redirect_uri,
    )
    state_data.gmail_authorized = True
    return RedirectResponse(url="/preview?auth=success")


def _send_single_message(
    gmail: GmailClient,
    credentials,
    message: RenderedEmail,
) -> RenderedEmail:
    if not message.approved:
        message.status = "skipped"
        return message
    try:
        gmail.send_message(credentials, message.recipient.email, message.subject, message.body)
    except Exception as exc:  # pragma: no cover - network dependent
        message.status = "failed"
        message.error_message = str(exc)
    else:
        message.status = "sent"
        message.error_message = None
        message.sent_at = datetime.utcnow()
    return message


@router.post("/send")
async def send_selected(
    session_id: str = Depends(get_session_id),
) -> RedirectResponse:
    state = get_store().get(session_id)
    if not state.messages or not state.template:
        return RedirectResponse(url="/preview", status_code=status.HTTP_303_SEE_OTHER)

    if not state.template.subject_template.strip():
        return RedirectResponse(
            url=f"/preview?error={quote_plus('Please add an email subject before sending.')}",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    gmail = _get_gmail_client()
    credentials = gmail.get_credentials(session_id)
    if not credentials:
        return RedirectResponse(url="/auth/google/start", status_code=status.HTTP_302_FOUND)

    for message in state.messages:
        _send_single_message(gmail, credentials, message)

    return RedirectResponse(url="/preview?message=Send%20complete", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/recipient-template")
async def download_template() -> FileResponse:
    return FileResponse(
        "app/static/recipient-template.csv",
        media_type="text/csv",
        filename="recipient-template.csv",
    )


@router.post("/reset")
async def reset_session(session_id: str = Depends(get_session_id)) -> RedirectResponse:
    get_store().clear(session_id)
    get_token_store().clear(session_id)
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
