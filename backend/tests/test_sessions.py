from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


TEST_EMAIL = "sessions_test@example.com"
TEST_USERNAME = "sessions_test_user"
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


def auth_headers():

    token = get_token()

    return {
        "Authorization": f"Bearer {token}"
    }


# =====================================================
# CREATE SESSION
# =====================================================

def test_create_session():

    response = client.post(
        "/sessions",
        headers=auth_headers(),
        json={
            "title": "Жұмыс туралы"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert "id" in data
    assert data["title"] == "Жұмыс туралы"
    assert data["is_active"] is True


# =====================================================
# LIST SESSIONS
# =====================================================

def test_list_sessions():

    headers = auth_headers()

    create_response = client.post(
        "/sessions",
        headers=headers,
        json={
            "title": "Қаржы туралы"
        }
    )

    assert create_response.status_code == 201

    response = client.get(
        "/sessions",
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) > 0

    titles = [
        session["title"]
        for session in data
    ]

    assert "Қаржы туралы" in titles


# =====================================================
# GET ONE SESSION
# =====================================================

def test_get_session():

    headers = auth_headers()

    create_response = client.post(
        "/sessions",
        headers=headers,
        json={
            "title": "Отбасы туралы"
        }
    )

    session_id = create_response.json()["id"]

    response = client.get(
        f"/sessions/{session_id}",
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == session_id
    assert data["title"] == "Отбасы туралы"
    assert "messages" in data
    assert isinstance(
        data["messages"],
        list
    )


# =====================================================
# RENAME SESSION
# =====================================================

def test_rename_session():

    headers = auth_headers()

    create_response = client.post(
        "/sessions",
        headers=headers,
        json={
            "title": "Ескі атау"
        }
    )

    session_id = create_response.json()["id"]

    response = client.patch(
        f"/sessions/{session_id}",
        headers=headers,
        json={
            "title": "Жаңа атау"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["session_id"] == session_id
    assert data["title"] == "Жаңа атау"

    get_response = client.get(
        f"/sessions/{session_id}",
        headers=headers
    )

    assert get_response.status_code == 200

    assert (
        get_response.json()["title"]
        == "Жаңа атау"
    )


# =====================================================
# DELETE SESSION
# =====================================================

def test_delete_session():

    headers = auth_headers()

    create_response = client.post(
        "/sessions",
        headers=headers,
        json={
            "title": "Өшірілетін чат"
        }
    )

    session_id = create_response.json()["id"]

    response = client.delete(
        f"/sessions/{session_id}",
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["session_id"] == session_id

    get_response = client.get(
        f"/sessions/{session_id}",
        headers=headers
    )

    assert get_response.status_code == 404


# =====================================================
# WITHOUT TOKEN
# =====================================================

def test_sessions_without_token():

    response = client.get(
        "/sessions"
    )

    assert response.status_code == 401