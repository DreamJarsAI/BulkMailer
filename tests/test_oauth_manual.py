from fastapi.testclient import TestClient


def test_oauth_start_uses_manually_posted_credentials(client: TestClient) -> None:
    # Post user-supplied credentials
    manual_client_id = "999999999999-abcdefabcdefabcdefabcdefabcdef.apps.googleusercontent.com"
    manual_secret = "GOCSPX-TESTSECRET"
    r = client.post(
        "/credentials",
        data={"client_id": manual_client_id, "client_secret": manual_secret},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert r.headers["location"] == "/auth/google/start"

    # Start OAuth; should use manual client_id
    r = client.get("/auth/google/start", follow_redirects=False)
    assert r.status_code in (302, 303, 307)
    location = r.headers.get("location", "")
    assert "accounts.google.com" in location
    assert f"client_id={manual_client_id}" in location

