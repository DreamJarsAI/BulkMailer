"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
import logging

from app.api.routes import router as web_router
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        max_age=settings.session_lifetime_minutes * 60,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://*", "http://localhost", "http://127.0.0.1"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Respect X-Forwarded-* headers on platforms like Render to ensure
    # correct scheme/host when constructing absolute callback URLs.
    app.add_middleware(ProxyHeadersMiddleware)
    # Ensure our OAuth diagnostics are visible at INFO level
    oauth_logger = logging.getLogger("app.oauth")
    oauth_logger.setLevel(logging.INFO)
    if not oauth_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(levelname)s:%(name)s:%(message)s")
        handler.setFormatter(formatter)
        oauth_logger.addHandler(handler)
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"],
    )

    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    app.include_router(web_router)

    @app.get("/health")
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()


__all__ = ["app", "create_app"]
