import uuid
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import app.services.usage as usage
from app.main import app


client = TestClient(app)

PASSWORD = "UsageTest123!"


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


def new_user() -> tuple[str, int]:
    """Жаңа пайдаланушы: (access_token, session_id)."""

    suffix = uuid.uuid4().hex[:10]
    email = f"usage_{suffix}@example.com"

    client.post(
        "/auth/register",
        json={
            "accept_terms": True,
            "email": email,
            "username": f"usage_{suffix}",
            "password": PASSWORD,
        },
    )
    token = client.post(
        "/auth/login",
        json={"email": email, "password": PASSWORD},
    ).json()["access_token"]

    session = client.post(
        "/sessions",
        json={"title": "Usage"},
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    return token, session["id"]


def send(token: str, session_id: int):
    return client.post(
        "/chat",
        json={"session_id": session_id, "message": "Сәлем"},
        headers={"Authorization": f"Bearer {token}"},
    )


def my_usage(token: str) -> dict:
    return client.get(
        "/usage/me",
        headers={"Authorization": f"Bearer {token}"},
    ).json()


def test_daily_user_limit(monkeypatch):
    monkeypatch.setattr(usage, "DAILY_MESSAGES_PER_USER", 2)
    token, session_id = new_user()

    assert my_usage(token)["remaining"] == 2

    assert send(token, session_id).status_code == 200
    assert send(token, session_id).status_code == 200

    blocked = send(token, session_id)
    assert blocked.status_code == 429
    assert "лимиті бітті" in blocked.json()["detail"]

    info = my_usage(token)
    assert info["used"] == 2
    assert info["remaining"] == 0
    assert info["limit"] == 2
    assert info["resets_at"]


def test_limit_is_per_user(monkeypatch):
    monkeypatch.setattr(usage, "DAILY_MESSAGES_PER_USER", 1)

    first_token, first_session = new_user()
    second_token, second_session = new_user()

    assert send(first_token, first_session).status_code == 200
    assert send(first_token, first_session).status_code == 429

    assert send(second_token, second_session).status_code == 200


def test_site_budget_blocks_everyone(monkeypatch):
    token, session_id = new_user()

    used = usage.site_tokens_used_today()
    monkeypatch.setattr(usage, "DAILY_SITE_TOKEN_BUDGET", used + 50)

    assert send(token, session_id).status_code == 200

    usage.record_tokens(input_tokens=40, output_tokens=20)

    blocked = send(token, session_id)
    assert blocked.status_code == 429
    assert "Ертең" in blocked.json()["detail"]


def test_record_usage_from_openai_response():
    before = usage.site_tokens_used_today()

    usage.record_usage_from(
        SimpleNamespace(
            usage=SimpleNamespace(input_tokens=120, output_tokens=30)
        )
    )
    usage.record_usage_from(SimpleNamespace(usage=None))
    usage.record_usage_from(None)

    assert usage.site_tokens_used_today() == before + 150


def test_usage_requires_login():
    assert client.get("/usage/me").status_code in (401, 403)
