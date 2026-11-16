import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)

PASSWORD = "Feedback123!"


@pytest.fixture(autouse=True)
def fake_ai(monkeypatch):
    monkeypatch.setattr(
        "app.routes.chat.ask_ai",
        lambda *args, **kwargs: "Тест жауабы.",
    )
    monkeypatch.setattr(
        "app.brain.conversation_summary.ask_ai",
        lambda *args, **kwargs: "Қысқаша мазмұн.",
    )


def make_user_with_answer(email: str | None = None) -> dict:
    suffix = uuid.uuid4().hex[:10]
    email = email or f"fb_{suffix}@example.com"

    client.post(
        "/auth/register",
        json={
            "accept_terms": True,
            "email": email,
            "username": f"fb_{suffix}",
            "password": PASSWORD,
        },
    )
    token = client.post(
        "/auth/login",
        json={"email": email, "password": PASSWORD},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    session_id = client.post(
        "/sessions", json={"title": "Баға"}, headers=headers
    ).json()["id"]

    assert client.post(
        "/chat",
        json={"session_id": session_id, "message": "Жұмыс туралы кеңес керек."},
        headers=headers,
    ).status_code == 200

    messages = client.get(f"/sessions/{session_id}", headers=headers).json()["messages"]

    return {
        "email": email,
        "headers": headers,
        "session_id": session_id,
        "answer_id": next(m["id"] for m in messages if m["role"] == "assistant"),
        "question_id": next(m["id"] for m in messages if m["role"] == "user"),
    }


def session_feedback(user) -> int:
    messages = client.get(
        f"/sessions/{user['session_id']}", headers=user["headers"]
    ).json()["messages"]
    return next(m["feedback"] for m in messages if m["id"] == user["answer_id"])


def rate(user, message_id, rating):
    return client.post(
        "/feedback",
        json={"message_id": message_id, "rating": rating},
        headers=user["headers"],
    )


def test_like_dislike_and_remove():
    user = make_user_with_answer()

    assert session_feedback(user) == 0

    assert rate(user, user["answer_id"], 1).status_code == 200
    assert session_feedback(user) == 1

    assert rate(user, user["answer_id"], -1).status_code == 200
    assert session_feedback(user) == -1

    assert rate(user, user["answer_id"], 0).status_code == 200
    assert session_feedback(user) == 0


def test_cannot_rate_own_question_or_foreign_answer():
    user = make_user_with_answer()
    stranger = make_user_with_answer()

    assert rate(user, user["question_id"], 1).status_code == 404
    assert rate(user, stranger["answer_id"], 1).status_code == 404
    assert rate(user, 999_999_999, 1).status_code == 404


def test_rating_must_be_valid():
    user = make_user_with_answer()

    assert rate(user, user["answer_id"], 5).status_code == 422


def test_feedback_requires_login():
    assert client.post(
        "/feedback", json={"message_id": 1, "rating": 1}
    ).status_code == 401


def test_regenerate_clears_old_rating():
    user = make_user_with_answer()
    rate(user, user["answer_id"], -1)

    response = client.post(
        "/chat/regenerate",
        json={"session_id": user["session_id"]},
        headers=user["headers"],
    )

    assert response.status_code == 200
    assert session_feedback(user) == 0


def test_admin_sees_feedback_counts(monkeypatch):
    admin_email = f"fb_admin_{uuid.uuid4().hex[:8]}@example.com"
    admin = make_user_with_answer(admin_email)
    monkeypatch.setenv("ADMIN_EMAILS", admin_email)

    before = client.get("/admin/stats", headers=admin["headers"]).json()["feedback"]["last_30d"]

    rate(admin, admin["answer_id"], 1)

    after = client.get("/admin/stats", headers=admin["headers"]).json()["feedback"]["last_30d"]

    assert after["likes"] == before["likes"] + 1
    assert after["satisfaction"] is not None


def test_dislike_reason_saved_and_returned():
    user = make_user_with_answer()

    response = client.post(
        "/feedback",
        json={"message_id": user["answer_id"], "rating": -1, "reason": "too_long"},
        headers=user["headers"],
    )
    assert response.status_code == 200
    assert response.json()["reason"] == "too_long"

    messages = client.get(f"/sessions/{user['session_id']}", headers=user["headers"]).json()["messages"]
    answer = next(m for m in messages if m["id"] == user["answer_id"])
    assert answer["feedback"] == -1
    assert answer["feedback_reason"] == "too_long"


def test_reason_ignored_for_likes_and_unknown_values():
    user = make_user_with_answer()

    like = client.post(
        "/feedback",
        json={"message_id": user["answer_id"], "rating": 1, "reason": "too_long"},
        headers=user["headers"],
    )
    assert like.json()["reason"] is None

    unknown = client.post(
        "/feedback",
        json={"message_id": user["answer_id"], "rating": -1, "reason": "hack"},
        headers=user["headers"],
    )
    assert unknown.json()["reason"] is None


def test_admin_sees_dislike_reasons(monkeypatch):
    admin_email = f"fb_reason_{uuid.uuid4().hex[:8]}@example.com"
    admin = make_user_with_answer(admin_email)
    monkeypatch.setenv("ADMIN_EMAILS", admin_email)

    before = client.get("/admin/stats", headers=admin["headers"]).json()["feedback"]["last_30d"]["by_reason"]

    client.post(
        "/feedback",
        json={"message_id": admin["answer_id"], "rating": -1, "reason": "not_useful"},
        headers=admin["headers"],
    )

    after = client.get("/admin/stats", headers=admin["headers"]).json()["feedback"]["last_30d"]["by_reason"]
    assert after.get("not_useful", 0) == before.get("not_useful", 0) + 1
