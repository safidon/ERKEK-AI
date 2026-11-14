from fastapi.testclient import TestClient

from app.main import app
from app.prompts.personas import (
    DEFAULT_PERSONA,
    build_system_prompt,
    get_user_persona,
    normalize_persona,
)
from app.prompts.system_prompt import SYSTEM_PROMPT


client = TestClient(app)


TEST_EMAIL = "persona_test@example.com"
TEST_USERNAME = "persona_test_user"
TEST_PASSWORD = "TestPassword123!"


def get_token() -> str:
    response = client.post(
        "/auth/register",
        json={
            "email": TEST_EMAIL,
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD,
        },
    )
    assert response.status_code in [201, 409]

    response = client.post(
        "/auth/login",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
        },
    )
    assert response.status_code == 200

    return response.json()["access_token"]


# =====================================================
# PROMPT BUILDING
# =====================================================

def test_default_persona_is_brother():
    assert DEFAULT_PERSONA == "brother"
    assert normalize_persona(None) == "brother"
    assert normalize_persona("unknown") == "brother"
    assert build_system_prompt(None) == SYSTEM_PROMPT


def test_hardcore_prompt_allows_profanity_with_guardrails():
    prompt = build_system_prompt("hardcore")

    assert prompt.startswith(SYSTEM_PROMPT)
    assert "HARDCORE" in prompt
    assert "нахуй" in prompt
    assert "never advise lying to kids" in prompt
    assert "drop the mat completely" in prompt


def test_strategist_prompt():
    prompt = build_system_prompt("strategist")

    assert "STRATEGIST" in prompt
    assert "no profanity" in prompt


def test_get_user_persona_handles_missing_value():
    assert get_user_persona({"user_id": "x"}) == "brother"
    assert get_user_persona({"persona": None}) == "brother"
    assert get_user_persona({"persona": "hardcore"}) == "hardcore"


# =====================================================
# API
# =====================================================

def test_persona_api_roundtrip():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    response = client.patch(
        "/profile/persona",
        headers=headers,
        json={"persona": "hardcore"},
    )
    assert response.status_code == 200
    assert response.json()["persona"] == "hardcore"

    response = client.get(
        "/profile/persona",
        headers=headers,
    )
    assert response.status_code == 200

    data = response.json()
    assert data["persona"] == "hardcore"
    assert {
        option["id"] for option in data["options"]
    } == {"brother", "hardcore", "strategist"}

    response = client.patch(
        "/profile/persona",
        headers=headers,
        json={"persona": "brother"},
    )
    assert response.json()["persona"] == "brother"


def test_persona_api_rejects_unknown_persona():
    token = get_token()

    response = client.patch(
        "/profile/persona",
        headers={"Authorization": f"Bearer {token}"},
        json={"persona": "clown"},
    )

    assert response.status_code == 422


def test_persona_api_requires_auth():
    response = client.get("/profile/persona")

    assert response.status_code in [401, 403]


def test_chat_uses_selected_persona(monkeypatch):
    from app.brain.conversation_sessions import create_session
    from app.auth.jwt import decode_access_token
    import app.routes.chat as chat_module

    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}

    client.patch(
        "/profile/persona",
        headers=headers,
        json={"persona": "hardcore"},
    )

    captured = {}

    def fake_ask_ai(*args, **kwargs):
        captured["system_prompt"] = kwargs.get(
            "system_prompt",
            args[0] if args else "",
        )
        return "Ок, бро."

    monkeypatch.setattr(chat_module, "ask_ai", fake_ask_ai)

    session = create_session(
        user_id=decode_access_token(token),
        title="Persona test",
    )

    response = client.post(
        "/chat",
        headers=headers,
        json={
            "session_id": session["id"],
            "message": "Поздравлять бывшую с днём рождения?",
        },
    )

    assert response.status_code == 200
    assert "HARDCORE" in captured["system_prompt"]

    client.patch(
        "/profile/persona",
        headers=headers,
        json={"persona": "brother"},
    )
