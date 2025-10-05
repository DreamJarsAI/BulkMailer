from fastapi.testclient import TestClient


def test_oauth_start_falls_back_to_env(client: TestClient) -> None:
    # No credentials posted, but env provides test values (see conftest)
    response = client.get("/auth/google/start", follow_redirects=False)
    # Should redirect to Google Accounts with client_id present
    assert response.status_code in (302, 303, 307)
    location = response.headers.get("location", "")
    assert "accounts.google.com" in location
    assert "client_id=test-client-id" in location

