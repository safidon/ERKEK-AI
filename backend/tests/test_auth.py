from fastapi.testclient import TestClient

from app.main import app

from app.auth.jwt import decode_access_token
from app.brain.conversation_sessions import create_session


client = TestClient(app)


# =====================================================
# TEST USER
# =====================================================

TEST_EMAIL = "auth_test@example.com"
TEST_USERNAME = "auth_test_user"
TEST_PASSWORD = "TestPassword123!"


# =====================================================
# HELPERS
# =====================================================

def register_test_user():
    """
    Test user-ді тіркейді.

    Егер бұрыннан тіркелген болса,
    409-ды қалыпты жағдай деп қабылдаймыз.
    """

    response = client.post(
        "/auth/register",
        json={
            "email": TEST_EMAIL,
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD
        }
    )

    assert response.status_code in [201, 409]


def login_test_user():
    """
    Test user login жасап,
    JWT access token қайтарады.
    """

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
    assert "token_type" in data
    assert data["token_type"] == "bearer"

    return data["access_token"]


def create_test_session(token: str) -> int:
    """
    JWT ішінен user_id алып,
    сол user үшін conversation session жасайды.
    """

    user_id = decode_access_token(token)

    assert user_id is not None

    session = create_session(
        user_id=user_id,
        title="Auth test chat"
    )

    assert session["id"] is not None

    return session["id"]


# =====================================================
# REGISTER
# =====================================================

def test_register():

    response = client.post(
        "/auth/register",
        json={
            "email": "register_test@example.com",
            "username": "register_test_user",
            "password": TEST_PASSWORD
        }
    )

    # Тест бірнеше рет іске қосылғанда
    # user бұрыннан болуы мүмкін.
    assert response.status_code in [201, 409]


# =====================================================
# LOGIN SUCCESS
# =====================================================

def test_login_success():

    register_test_user()

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
    assert data["access_token"]

    assert data["token_type"] == "bearer"


# =====================================================
# WRONG PASSWORD
# =====================================================

def test_login_wrong_password():

    register_test_user()

    response = client.post(
        "/auth/login",
        json={
            "email": TEST_EMAIL,
            "password": "WrongPassword123!"
        }
    )

    assert response.status_code == 401


# =====================================================
# CHAT WITHOUT TOKEN
# =====================================================

def test_chat_without_token():

    response = client.post(
        "/chat",
        json={
            "session_id": 1,
            "message": "Сәлем"
        }
    )

    assert response.status_code == 401


# =====================================================
# CHAT WITH JWT
# =====================================================

def test_chat_with_token(monkeypatch):

    register_test_user()

    token = login_test_user()

    session_id = create_test_session(
        token
    )

    # Бұл тест кезінде нақты OpenAI API-ға
    # сұраныс жібермейміз.
    monkeypatch.setattr(
        "app.routes.chat.ask_ai",
        lambda *args, **kwargs: "Тест жауабы"
    )

    response = client.post(
        "/chat",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "session_id": session_id,
            "message": "Жұмыс туралы кеңес керек."
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "user_id" in data
    assert "session_id" in data
    assert "answer" in data

    assert data["session_id"] == session_id
    assert data["answer"]