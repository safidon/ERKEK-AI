import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

import app.auth.password_reset as password_reset
from app.database import adapt_query, get_connection
from app.main import app


client = TestClient(app)

OLD_PASSWORD = "OldPassword123!"
NEW_PASSWORD = "NewPassword456!"


@pytest.fixture
def sent_emails(monkeypatch):
    """Хаттарды жібермей, тізімге жинайды."""

    emails = []

    def fake_send_email(to, subject, text, html=None):
        emails.append({"to": to, "subject": subject, "text": text})
        return True

    monkeypatch.setattr(password_reset, "send_email", fake_send_email)
    return emails


@pytest.fixture
def user():
    suffix = uuid.uuid4().hex[:10]
    email = f"reset_{suffix}@example.com"

    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "username": f"reset_{suffix}",
            "password": OLD_PASSWORD,
        },
    )
    assert response.status_code == 201

    return email


def _token_from(email_text: str) -> str:
    link = next(
        line.strip()
        for line in email_text.splitlines()
        if "/reset-password?token=" in line
    )
    return parse_qs(urlparse(link).query)["token"][0]


def _login(email: str, password: str) -> int:
    return client.post(
        "/auth/login",
        json={"email": email, "password": password},
    ).status_code


def test_full_reset_flow(user, sent_emails):
    response = client.post("/auth/forgot-password", json={"email": user})

    assert response.status_code == 200
    assert len(sent_emails) == 1
    assert sent_emails[0]["to"] == user

    token = _token_from(sent_emails[0]["text"])

    response = client.post(
        "/auth/reset-password",
        json={"token": token, "password": NEW_PASSWORD},
    )

    assert response.status_code == 200
    assert _login(user, NEW_PASSWORD) == 200
    assert _login(user, OLD_PASSWORD) == 401


def test_unknown_email_gets_same_answer_and_no_email(sent_emails, user):
    known = client.post("/auth/forgot-password", json={"email": user})
    unknown = client.post(
        "/auth/forgot-password",
        json={"email": "nobody_here@example.com"},
    )

    assert known.status_code == unknown.status_code == 200
    assert known.json() == unknown.json()
    assert [mail["to"] for mail in sent_emails] == [user]


def test_token_works_only_once(user, sent_emails):
    client.post("/auth/forgot-password", json={"email": user})
    token = _token_from(sent_emails[0]["text"])

    first = client.post(
        "/auth/reset-password",
        json={"token": token, "password": NEW_PASSWORD},
    )
    second = client.post(
        "/auth/reset-password",
        json={"token": token, "password": "AnotherPass789!"},
    )

    assert first.status_code == 200
    assert second.status_code == 400
    assert _login(user, NEW_PASSWORD) == 200


def test_reset_invalidates_older_tokens(user, sent_emails):
    client.post("/auth/forgot-password", json={"email": user})
    client.post("/auth/forgot-password", json={"email": user})

    older = _token_from(sent_emails[0]["text"])
    newer = _token_from(sent_emails[1]["text"])

    assert client.post(
        "/auth/reset-password",
        json={"token": newer, "password": NEW_PASSWORD},
    ).status_code == 200

    assert client.post(
        "/auth/reset-password",
        json={"token": older, "password": "AnotherPass789!"},
    ).status_code == 400


def test_expired_token_rejected(user, sent_emails):
    client.post("/auth/forgot-password", json={"email": user})
    token = _token_from(sent_emails[0]["text"])

    past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    connection = get_connection()
    try:
        connection.cursor().execute(
            adapt_query(
                "UPDATE password_reset_tokens SET expires_at = ? "
                "WHERE token_hash = ?"
            ),
            (past, password_reset._hash_token(token)),
        )
        connection.commit()
    finally:
        connection.close()

    response = client.post(
        "/auth/reset-password",
        json={"token": token, "password": NEW_PASSWORD},
    )

    assert response.status_code == 400
    assert _login(user, OLD_PASSWORD) == 200


def test_invalid_token_and_short_password():
    bad_token = client.post(
        "/auth/reset-password",
        json={"token": "x" * 43, "password": NEW_PASSWORD},
    )
    short_password = client.post(
        "/auth/reset-password",
        json={"token": "x" * 43, "password": "short"},
    )

    assert bad_token.status_code == 400
    assert short_password.status_code == 422


def test_token_is_stored_hashed(user, sent_emails):
    client.post("/auth/forgot-password", json={"email": user})
    token = _token_from(sent_emails[0]["text"])

    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            adapt_query(
                "SELECT COUNT(*) AS n FROM password_reset_tokens "
                "WHERE token_hash = ?"
            ),
            (token,),
        )
        assert cursor.fetchone()["n"] == 0
    finally:
        connection.close()
