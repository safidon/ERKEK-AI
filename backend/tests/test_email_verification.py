import uuid
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

import app.auth.email_verification as verification
import app.services.welcome as welcome
from app.auth.service import get_user_by_email
from app.main import app


client = TestClient(app)
PASSWORD = "Verify123!"


@pytest.fixture
def mailbox(monkeypatch):
    """Растау талабын қосып, хаттарды жинайды."""

    monkeypatch.setenv("REQUIRE_EMAIL_VERIFICATION", "true")

    letters = []
    monkeypatch.setattr(
        verification, "send_email",
        lambda to, subject, text, html=None: letters.append({"to": to, "subject": subject, "text": text}) or True,
    )
    monkeypatch.setattr(
        welcome, "send_email",
        lambda to, subject, text, html=None: letters.append({"to": to, "subject": subject, "text": text}) or True,
    )
    return letters


def register(email: str):
    return client.post(
        "/auth/register",
        json={"accept_terms": True, "email": email, "username": f"v_{uuid.uuid4().hex[:8]}", "password": PASSWORD},
    )


def token_from(letter) -> str:
    link = next(line for line in letter["text"].splitlines() if "/verify-email?token=" in line)
    return parse_qs(urlparse(link.strip()).query)["token"][0]


def login(email: str):
    return client.post("/auth/login", json={"email": email, "password": PASSWORD})


def test_register_sends_link_and_blocks_login_until_verified(mailbox):
    email = f"verify_{uuid.uuid4().hex[:8]}@example.com"

    response = register(email)
    assert response.status_code == 201
    assert response.json()["email_verification_required"] is True

    assert len(mailbox) == 1
    assert mailbox[0]["to"] == email
    assert "растау" in mailbox[0]["subject"].lower()

    assert login(email).status_code == 403

    verified = client.post("/auth/verify-email", json={"token": token_from(mailbox[0])})
    assert verified.status_code == 200
    assert verified.json()["access_token"]

    # Растағаннан кейін қош келдің хаты кетеді және кіру ашылады.
    assert any("қош келдің" in letter["subject"].lower() for letter in mailbox[1:])
    assert login(email).status_code == 200


def test_link_works_once(mailbox):
    email = f"verify_{uuid.uuid4().hex[:8]}@example.com"
    register(email)
    token = token_from(mailbox[0])

    assert client.post("/auth/verify-email", json={"token": token}).status_code == 200
    assert client.post("/auth/verify-email", json={"token": token}).status_code == 400


def test_resend_invalidates_old_link(mailbox):
    email = f"verify_{uuid.uuid4().hex[:8]}@example.com"
    register(email)
    old_token = token_from(mailbox[0])

    response = client.post("/auth/resend-verification", json={"email": email})
    assert response.status_code == 200
    assert len(mailbox) == 2

    assert client.post("/auth/verify-email", json={"token": old_token}).status_code == 400
    assert client.post("/auth/verify-email", json={"token": token_from(mailbox[1])}).status_code == 200


def test_resend_does_not_reveal_accounts(mailbox):
    unknown = client.post("/auth/resend-verification", json={"email": "nobody-here@example.com"})
    assert unknown.status_code == 200
    assert mailbox == []


def test_expired_link_rejected(mailbox, monkeypatch):
    monkeypatch.setattr(verification, "VERIFY_EXPIRE_HOURS", -1)
    email = f"verify_{uuid.uuid4().hex[:8]}@example.com"
    register(email)

    assert client.post("/auth/verify-email", json={"token": token_from(mailbox[0])}).status_code == 400


def test_password_reset_also_verifies_email(mailbox, monkeypatch):
    import app.auth.password_reset as password_reset

    reset_letters = []
    monkeypatch.setattr(
        password_reset, "send_email",
        lambda to, subject, text, html=None: reset_letters.append(text) or True,
    )

    email = f"verify_{uuid.uuid4().hex[:8]}@example.com"
    register(email)
    client.post("/auth/forgot-password", json={"email": email})

    link = next(line for line in reset_letters[0].splitlines() if "/reset-password?token=" in line)
    reset_token = parse_qs(urlparse(link.strip()).query)["token"][0]
    assert client.post("/auth/reset-password", json={"token": reset_token, "password": PASSWORD}).status_code == 200

    assert login(email).status_code == 200


def test_old_accounts_are_not_blocked(mailbox, monkeypatch):
    # Растау талабы қосылмай тұрып тіркелгендер (email_verified = NULL).
    monkeypatch.setenv("REQUIRE_EMAIL_VERIFICATION", "false")
    email = f"verify_old_{uuid.uuid4().hex[:8]}@example.com"
    register(email)
    assert get_user_by_email(email)["email_verified"] is None

    monkeypatch.setenv("REQUIRE_EMAIL_VERIFICATION", "true")
    assert login(email).status_code == 200


def test_russian_activation_email(mailbox):
    email = f"verify_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/auth/register",
        json={"accept_terms": True, "email": email, "username": f"v_{uuid.uuid4().hex[:8]}", "password": PASSWORD},
        headers={"X-Lang": "ru"},
    )
    assert mailbox[0]["subject"] == "Подтверди email — ERKEK AI"

    response = client.post("/auth/login", json={"email": email, "password": PASSWORD}, headers={"X-Lang": "ru"})
    assert response.json()["detail"].startswith("Email ещё не подтверждён")
