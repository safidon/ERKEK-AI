from fastapi.testclient import TestClient

from app.main import app
from app.auth.jwt import decode_access_token
from app.brain.conversation_sessions import create_session


client = TestClient(app)


TEST_EMAIL = "chat_test@example.com"
TEST_USERNAME = "chat_test_user"
TEST_PASSWORD = "TestPassword123!"


# =====================================================
# HELPERS
# =====================================================

def ensure_user():

    response = client.post(
        "/auth/register",
        json={
            "email": TEST_EMAIL,
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD
        }
    )

    assert response.status_code in [201, 409]


def get_token():

    ensure_user()

    response = client.post(
        "/auth/login",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data

    return data["access_token"]


def create_test_session(
    token: str,
    title: str = "Pytest chat"
) -> int:

    user_id = decode_access_token(
        token
    )

    assert user_id is not None

    session = create_session(
        user_id=user_id,
        title=title
    )

    assert session["id"] is not None

    return session["id"]


# =====================================================
# CHAT SUCCESS
# =====================================================

def test_chat_endpoint_success(monkeypatch):

    token = get_token()

    session_id = create_test_session(
        token,
        "Career test"
    )

    monkeypatch.setattr(
        "app.routes.chat.ask_ai",
        lambda *args, **kwargs: "Тест AI жауабы."
    )

    response = client.post(
        "/chat",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "session_id": session_id,
            "message": "Менің жұмысым тұрақсыз."
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "user_id" in data
    assert "session_id" in data

    assert data["session_id"] == session_id
    assert data["language"] == "kk"
    assert data["category"] == "career"
    assert data["risk"] == "low"

    assert "answer" in data
    assert "memory" in data
    assert "recent_history" in data
    assert "conversation_summary" in data


# =====================================================
# MULTI CATEGORY
# =====================================================

def test_chat_multi_category(monkeypatch):

    token = get_token()

    session_id = create_test_session(
        token,
        "Multi category test"
    )

    monkeypatch.setattr(
        "app.routes.chat.ask_ai",
        lambda *args, **kwargs: "Тест жауап."
    )

    response = client.post(
        "/chat",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "session_id": session_id,
            "message": (
                "Ажырастым, екі балам бар, "
                "қарызым бар және жұмысым тұрақсыз."
            )
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["session_id"] == session_id

    assert "secondary_categories" in data

    all_categories = [
        data["category"],
        *data["secondary_categories"]
    ]

    assert "fatherhood" in all_categories
    assert "relationship" in all_categories
    assert "finance" in all_categories
    assert "career" in all_categories


# =====================================================
# MEMORY UPDATE
# =====================================================

def test_chat_memory_update(monkeypatch):

    token = get_token()

    session_id = create_test_session(
        token,
        "Memory update test"
    )

    monkeypatch.setattr(
        "app.routes.chat.ask_ai",
        lambda *args, **kwargs: "Тест жауап."
    )

    first_response = client.post(
        "/chat",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "session_id": session_id,
            "message": "Менің жұмысым тұрақсыз."
        }
    )

    assert first_response.status_code == 200

    second_response = client.post(
        "/chat",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "session_id": session_id,
            "message": "Жаңа тұрақты жұмыс таптым."
        }
    )

    assert second_response.status_code == 200

    data = second_response.json()

    assert data["session_id"] == session_id

    assert "тұрақты жұмысы бар" in data["memory"]