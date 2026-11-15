import uuid

import pytest
from fastapi.testclient import TestClient

import app.auth.password_reset as password_reset
from app.auth.service import get_user_by_email
from app.database import adapt_query, get_connection
from app.main import app


client = TestClient(app)

PASSWORD = "DeleteMe123!"

USER_TABLES = (
    ("users", "user_id"),
    ("conversation_sessions", "user_id"),
    ("conversations", "user_id"),
    ("conversation_summaries", "user_id"),
    ("conversation_archive", "user_id"),
    ("password_reset_tokens", "user_id"),
    ("auth_sessions", "user_id"),
    ("user_consents", "user_id"),
    ("usage_daily", "scope"),
)


@pytest.fixture(autouse=True)
def fake_external(monkeypatch):
    monkeypatch.setattr(
        "app.routes.chat.ask_ai",
        lambda *args, **kwargs: "Тест жауабы.",
    )
    monkeypatch.setattr(
        "app.brain.conversation_summary.ask_ai",
        lambda *args, **kwargs: "Қысқаша мазмұн.",
    )
    monkeypatch.setattr(
        password_reset,
        "send_email",
        lambda *args, **kwargs: True,
    )


def make_active_user() -> dict:
    """Чаты, сессиясы, лимит санауышы бар толық пайдаланушы."""

    suffix = uuid.uuid4().hex[:10]
    email = f"del_{suffix}@example.com"

    client.post(
        "/auth/register",
        json={
            "accept_terms": True,
            "email": email,
            "username": f"del_{suffix}",
            "password": PASSWORD,
        },
    )
    tokens = client.post(
        "/auth/login",
        json={"email": email, "password": PASSWORD},
    ).json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    session_id = client.post(
        "/sessions",
        json={"title": "Жойылатын чат"},
        headers=headers,
    ).json()["id"]

    assert client.post(
        "/chat",
        json={"session_id": session_id, "message": "Менің жасым 30, екі балам бар."},
        headers=headers,
    ).status_code == 200

    client.post("/auth/forgot-password", json={"email": email})

    return {
        "email": email,
        "user_id": get_user_by_email(email)["user_id"],
        "headers": headers,
        "refresh_token": tokens["refresh_token"],
    }


def count_rows(user_id: str) -> dict:
    connection = get_connection()
    counts = {}

    try:
        cursor = connection.cursor()
        for table, column in USER_TABLES:
            cursor.execute(
                adapt_query(
                    f"SELECT COUNT(*) AS n FROM {table} WHERE {column} = ?"
                ),
                (user_id,),
            )
            counts[table] = cursor.fetchone()["n"]
    finally:
        connection.close()

    return counts


def test_wrong_password_keeps_everything():
    user = make_active_user()
    before = count_rows(user["user_id"])

    response = client.post(
        "/auth/delete-account",
        json={"password": "WrongPassword!"},
        headers=user["headers"],
    )

    assert response.status_code == 403
    assert count_rows(user["user_id"]) == before


def test_delete_account_removes_all_data():
    user = make_active_user()
    other = make_active_user()

    before = count_rows(user["user_id"])
    assert before["users"] == 1
    assert before["conversations"] > 0
    assert before["auth_sessions"] > 0
    assert before["user_consents"] > 0

    response = client.post(
        "/auth/delete-account",
        json={"password": PASSWORD},
        headers=user["headers"],
    )

    assert response.status_code == 200
    assert all(n == 0 for n in count_rows(user["user_id"]).values())

    # Кіру, ескі token, refresh — бәрі жабық.
    assert client.post(
        "/auth/login",
        json={"email": user["email"], "password": PASSWORD},
    ).status_code == 401
    assert client.get(
        "/sessions",
        headers=user["headers"],
    ).status_code == 401
    assert client.post(
        "/auth/refresh",
        json={"refresh_token": user["refresh_token"]},
    ).status_code == 401

    # Басқа пайдаланушыға тиіспейді.
    assert count_rows(other["user_id"])["users"] == 1
    assert client.get("/sessions", headers=other["headers"]).status_code == 200


def test_email_can_register_again_after_deletion():
    user = make_active_user()

    client.post(
        "/auth/delete-account",
        json={"password": PASSWORD},
        headers=user["headers"],
    )

    response = client.post(
        "/auth/register",
        json={
            "accept_terms": True,
            "email": user["email"],
            "username": "again_" + uuid.uuid4().hex[:8],
            "password": PASSWORD,
        },
    )

    assert response.status_code == 201


def test_delete_requires_login():
    response = client.post(
        "/auth/delete-account",
        json={"password": PASSWORD},
    )

    assert response.status_code in (401, 403)
