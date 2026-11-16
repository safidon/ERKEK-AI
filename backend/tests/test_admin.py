import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)

PASSWORD = "AdminTest123!"


@pytest.fixture(autouse=True)
def fake_openai(monkeypatch):
    monkeypatch.setattr(
        "app.routes.chat.ask_ai",
        lambda *args, **kwargs: "Тест жауабы.",
    )
    monkeypatch.setattr(
        "app.brain.conversation_summary.ask_ai",
        lambda *args, **kwargs: "Қысқаша мазмұн.",
    )


def make_user() -> tuple[str, dict]:
    suffix = uuid.uuid4().hex[:10]
    email = f"admin_{suffix}@example.com"

    client.post(
        "/auth/register",
        json={
            "accept_terms": True,
            "email": email,
            "username": f"adm_{suffix}",
            "password": PASSWORD,
        },
    )
    token = client.post(
        "/auth/login",
        json={"email": email, "password": PASSWORD},
    ).json()["access_token"]

    return email, {"Authorization": f"Bearer {token}"}


def send_message(headers: dict) -> None:
    session_id = client.post(
        "/sessions",
        json={"title": "Admin test"},
        headers=headers,
    ).json()["id"]

    assert client.post(
        "/chat",
        json={"session_id": session_id, "message": "Сәлем"},
        headers=headers,
    ).status_code == 200


def test_regular_user_cannot_open_admin(monkeypatch):
    monkeypatch.setenv("ADMIN_EMAILS", "boss@example.com")
    _, headers = make_user()

    assert client.get("/admin/stats", headers=headers).status_code == 403
    assert client.get("/admin/me", headers=headers).json() == {"is_admin": False}


def test_admin_requires_login():
    assert client.get("/admin/stats").status_code in (401, 403)


def test_admin_sees_stats(monkeypatch):
    admin_email, admin_headers = make_user()
    monkeypatch.setenv("ADMIN_EMAILS", f" other@example.com , {admin_email.upper()} ")

    before = client.get("/admin/stats", headers=admin_headers).json()

    user_email, user_headers = make_user()
    send_message(user_headers)
    send_message(user_headers)

    response = client.get("/admin/stats", headers=admin_headers)
    assert response.status_code == 200
    stats = response.json()

    assert client.get("/admin/me", headers=admin_headers).json() == {"is_admin": True}

    assert stats["users"]["total"] == before["users"]["total"] + 1
    assert stats["users"]["new_today"] >= 2
    assert stats["messages"]["today"] == before["messages"]["today"] + 2
    assert stats["users"]["active_today"] >= 1

    assert len(stats["daily"]) == 14
    assert stats["daily"][-1]["day"] == stats["today"]
    assert stats["daily"][-1]["messages"] == stats["messages"]["today"]

    ours = next(
        u for u in stats["recent_users"] if u["email"] == user_email
    )
    assert ours["messages_30d"] == 2
    assert ours["last_active"] == stats["today"]
    assert len(stats["recent_users"]) <= 20


def test_cost_is_estimated_only_when_prices_are_set(monkeypatch):
    admin_email, headers = make_user()
    monkeypatch.setenv("ADMIN_EMAILS", admin_email)

    monkeypatch.delenv("OPENAI_PRICE_INPUT_PER_1M", raising=False)
    stats = client.get("/admin/stats", headers=headers).json()
    assert stats["tokens"]["last_30d"]["cost_usd"] is None

    monkeypatch.setenv("OPENAI_PRICE_INPUT_PER_1M", "1")
    monkeypatch.setenv("OPENAI_PRICE_OUTPUT_PER_1M", "2")
    stats = client.get("/admin/stats", headers=headers).json()
    assert stats["tokens"]["last_30d"]["cost_usd"] is not None
