# Developer Setup

## Prerequisites

- Python 3.10 or newer
- Pip + virtual environment tooling (`venv`, `virtualenv`, or `pyenv`)
- Google Cloud project with OAuth 2.0 credentials (Web application)
- Optional: Render account for deployment testing

## Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .[dev]
```

## Environment Variables

Create a `.env` file (never commit it) with at least the following values:

```
BATCH_APP_SECRET_KEY=your-session-secret
BATCH_APP_FERNET_KEY=urlsafe-base64-32-byte-key
BATCH_APP_GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
BATCH_APP_TOKEN_STORAGE_PATH=./data/token_store.json
BATCH_APP_SESSION_LIFETIME_MINUTES=120
```

Google OAuth credentials can be provided in one of two ways:

1) Paste via the app UI (recommended for demos): no additional env needed.

2) Preconfigure via environment variables (headless deployments):

```
BATCH_APP_GOOGLE_CLIENT_ID=your-google-client-id
BATCH_APP_GOOGLE_CLIENT_SECRET=your-google-client-secret
```

Generate the Fernet key with:

```bash
python - <<'PY'
import base64, os
print(base64.urlsafe_b64encode(os.urandom(32)).decode())
PY
```

## Google OAuth Configuration

1. In Google Cloud Console, create an OAuth 2.0 Client ID (Web application).
2. Add authorized redirect URI: `http://localhost:8000/auth/google/callback` (and your Render URL when deployed).
3. Enable the Gmail API.
4. Download the client credentials, then copy the Client ID and Client Secret into the `.env` file.
5. When running locally, the app guides you through the Google consent screen and stores the encrypted refresh token at `data/token_store.json`.

## Running the App

```bash
uvicorn app.main:app --reload
```

Open <http://localhost:8000>. Complete the steps: upload CSV, provide template, preview, connect Google, and send. The sample CSV lives at `/static/recipient-template.csv` and can be downloaded from the UI.

## Tests & Quality Checks

```bash
pytest
ruff check .
black --check .
isort --check-only .
mypy .
```

## Render Deployment Notes

- Configure the required environment variables above in Render's dashboard.
- Mount a persistent disk if you want refresh tokens to survive restarts (`/opt/render/project/src/data`).
- Set the start command to `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- Add your Render domain to the Google OAuth credential redirect URIs.

## Troubleshooting

- **Invalid session state after OAuth**: ensure cookies are enabled and the redirect URI matches exactly.
- **CSV upload errors**: verify the header row is `title,first_name,last_name,email` and saved as UTF-8.
- **Template errors**: only the placeholders `{{ title }}`, `{{ first_name }}`, `{{ last_name }}` are supported.
