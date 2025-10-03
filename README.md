# Email Batch Assistant

A lightweight FastAPI web application that lets NYU Gmail users create and send personalized email batches. Users upload a CSV of recipients, provide an email template (subject + body), preview each message, connect their Gmail account via OAuth, and send selected emails. Everything except the Gmail refresh token is stored in memory so it stays simple for small campaigns (dozens of recipients).

## Quickstart

1. **Create and activate a virtual environment** (Python 3.10+).
2. Install dependencies: `pip install -e .[dev]`.
3. Provide configuration (see [Setup](SETUP.md)) including Google OAuth credentials and Fernet key.
4. Run the app: `uvicorn app.main:app --reload`.
5. Open <http://localhost:8000> and follow the guided steps.

## Key Features

- Guided three-step wizard (upload recipients, provide template, preview/send).
- Landing page walks through Gmail API setup and securely stores OAuth client details per session.
- Supports pasted templates or simple `.txt` / `.docx` uploads converted to plain text.
- Preview stage lets you edit per-recipient bodies, set the final subject, and approve/suspend before sending.
- Uses Jinja placeholders (`{{ title }}`, `{{ first_name }}`, `{{ last_name }}`) for personalization.
- Gmail OAuth 2.0 integration (send via authenticated NYU Gmail account).
- Sample CSV provided for non-technical users.

## Project Structure

```
app/
  api/            # FastAPI route definitions
  models/         # Pydantic domain models
  services/       # CSV parsing, template rendering, Gmail integration, token store
  templates/      # Jinja2 templates for the UI
  static/         # Sample CSV and static assets
  main.py         # FastAPI app factory
```

## Common Tasks

- **Run the server:** `uvicorn app.main:app --reload`
- **Run tests:** `pytest`
- **Lint:** `ruff check .`
- **Format (check mode):** `black --check .`
- **Sort imports:** `isort --check-only .`
- **Type check:** `mypy .`

## Documentation

- [SETUP.md](SETUP.md) – developer environment, OAuth configuration, secrets.
- [EVAL.md](EVAL.md) – evaluation scenarios and sample inputs.
- [TODO.md](TODO.md) – backlog of planned improvements.
- [CHANGELOG.md](CHANGELOG.md) – release log.

## Deployment on Render

- Add a Render web service with the start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- Configure environment variables listed in [SETUP.md](SETUP.md).
- Ensure the Fernet key and Google credentials are stored securely via Render secrets.
- The app writes encrypted refresh tokens to `data/token_store.json`; Render's persistent disk should be attached if reuse is desired. Otherwise users will re-authenticate when the service restarts.

## Support

For issues or enhancement ideas, add them to `TODO.md` or open a ticket in your chosen tracker. When reporting issues, include steps to reproduce, any stack traces, and the CSV/template files used if possible.
