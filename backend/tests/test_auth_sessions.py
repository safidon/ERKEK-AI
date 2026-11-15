import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

import app.auth.password_reset as password_reset
from app.auth.jwt import create_access_token
from app.auth.service import get_user_by_email
from app.database import adapt_query, get_connection
from app.main import app


client = TestClient(app)

PASSWORD = "SessionTest123!"


@pytest.fixture
def account():
    suffix = uuid.uuid4().hex[:10]
    email = f"sess_{suffix}@example.com"

    response = client.post(
        "/auth/register",
        json={
            "accept_terms": True,
            "email": email,
            "username": f"sess_{suffix}",
            "password": PASSWORD,
        },
    )
    assert response.status_code == 201

    return email


def login(email: str) -> dict:
    response = client.post(
        "/auth/login",
        json={"email": email, "password": PASSWORD},
    )
    assert response.status_code == 200
    return response.json()


def refresh(refresh_token: str):
    return client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )


def can_access(access_token: str) -> bool:
    response = client.get(
        "/sessions",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code in (200, 401)
    return response.status_code == 200


def _age_rotation(seconds: int) -> None:
    """Барлық сессиялардың соңғы rotation уақытын өткенге жылжытады."""

    past = (
        datetime.now(timezone.utc) - timedelta(seconds=seconds)
    ).isoformat()

    connection = get_connection()
    try:
        connection.cursor().execute(
            adapt_query(
                "UPDATE auth_sessions SET rotated_at = ? "
                "WHERE rotated_at IS NOT NULL"
            ),
            (past,),
        )
        connection.commit()
    finally:
        connection.close()


def test_login_returns_refresh_token(account):
    tokens = login(account)

    assert tokens["token_type"] == "bearer"
    assert tokens["refresh_token"]
    assert tokens["expires_in"] > 0
    assert can_access(tokens["access_token"])


def test_refresh_rotates_tokens(account):
    tokens = login(account)

    response = refresh(tokens["refresh_token"])
    assert response.status_code == 200

    new_tokens = response.json()
    assert new_tokens["refresh_token"] != tokens["refresh_token"]
    assert can_access(new_tokens["access_token"])

    # Ескі refresh token енді жарамсыз, бірақ сессия жабылмайды
    # (бірнеше қойынды бір мезетте жаңартуы мүмкін).
    assert refresh(tokens["refresh_token"]).status_code == 401
    assert refresh(new_tokens["refresh_token"]).status_code == 200


def test_reused_old_refresh_token_revokes_session(account):
    tokens = login(account)
    new_tokens = refresh(tokens["refresh_token"]).json()

    _age_rotation(seconds=120)

    # Ескі token grace уақытынан кейін қайта келді — ұрлық белгісі.
    assert refresh(tokens["refresh_token"]).status_code == 401

    assert refresh(new_tokens["refresh_token"]).status_code == 401
    assert not can_access(new_tokens["access_token"])


def test_logout_ends_session_immediately(account):
    tokens = login(account)
    assert can_access(tokens["access_token"])

    response = client.post(
        "/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert response.status_code == 200

    assert not can_access(tokens["access_token"])
    assert refresh(tokens["refresh_token"]).status_code == 401


def test_logout_affects_only_this_device(account):
    phone = login(account)
    laptop = login(account)

    client.post(
        "/auth/logout",
        json={"refresh_token": phone["refresh_token"]},
    )

    assert not can_access(phone["access_token"])
    assert can_access(laptop["access_token"])


def test_password_reset_ends_all_sessions(account, monkeypatch):
    emails = []
    monkeypatch.setattr(
        password_reset,
        "send_email",
        lambda to, subject, text, html=None: emails.append(text) or True,
    )

    phone = login(account)
    laptop = login(account)

    client.post("/auth/forgot-password", json={"email": account})
    token = emails[0].split("token=")[1].split()[0]

    response = client.post(
        "/auth/reset-password",
        json={"token": token, "password": "BrandNewPass456!"},
    )
    assert response.status_code == 200

    for device in (phone, laptop):
        assert not can_access(device["access_token"])
        assert refresh(device["refresh_token"]).status_code == 401


def test_expired_refresh_token_rejected(account):
    tokens = login(account)

    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    user_id = get_user_by_email(account)["user_id"]

    connection = get_connection()
    try:
        connection.cursor().execute(
            adapt_query(
                "UPDATE auth_sessions SET expires_at = ? WHERE user_id = ?"
            ),
            (past, user_id),
        )
        connection.commit()
    finally:
        connection.close()

    assert refresh(tokens["refresh_token"]).status_code == 401
    assert not can_access(tokens["access_token"])


def test_unknown_refresh_token_rejected():
    assert refresh("x" * 64).status_code == 401


def test_old_tokens_without_session_still_work(account):
    # Жаңарту алдында берілген token-дерде sid жоқ:
    # олар мерзімі біткенше жұмыс істей береді.
    user_id = get_user_by_email(account)["user_id"]

    assert can_access(create_access_token(user_id))
