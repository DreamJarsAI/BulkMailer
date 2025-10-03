from fastapi.testclient import TestClient


def test_full_preview_flow(client: TestClient) -> None:
    csv_payload = "title,first_name,last_name,email\nDr.,Ada,Lovelace,ada@example.com\n"
    response = client.post(
        "/recipients",
        files={"csv_file": ("recipients.csv", csv_payload, "text/csv")},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/recipients"

    response = client.post(
        "/template",
        data={
            "subject_text": "Hello {{ first_name }}",
            "body_text": "Dear {{ title }} {{ last_name }}, welcome!",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/preview"

    response = client.post(
        "/preview/update",
        data={
            "body_0": "Dear Dr. Lovelace, welcome!",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].startswith("/preview")

    response = client.get("/preview")
    assert response.status_code == 200
    assert "Dear Dr. Lovelace" in response.text
    assert "Subject template:" in response.text
    assert "Subject preview: <strong>Hello Ada" in response.text
    assert "Send approved emails" in response.text
