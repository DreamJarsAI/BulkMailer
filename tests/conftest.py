import os
from typing import Generator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def _configure_env() -> None:
    os.environ.setdefault("BATCH_APP_SECRET_KEY", "test-secret-key")
    os.environ.setdefault(
        "BATCH_APP_FERNET_KEY",
        "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA=",
    )
    os.environ.setdefault("BATCH_APP_GOOGLE_CLIENT_ID", "test-client-id")
    os.environ.setdefault("BATCH_APP_GOOGLE_CLIENT_SECRET", "test-client-secret")
    os.environ.setdefault("BATCH_APP_GOOGLE_REDIRECT_URI", "http://testserver/auth/google/callback")


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    from app.main import create_app

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
