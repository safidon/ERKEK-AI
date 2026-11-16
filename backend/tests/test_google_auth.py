import time
import uuid

import pytest
import rsa
from fastapi.testclient import TestClient
from jose import jwk, jwt

import app.auth.google as google
import app.services.welcome as welcome
from app.auth.service import get_user_by_email
from app.main import app


client = TestClient(app)

CLIENT_ID = "test-client.apps.googleusercontent.com"

_public, _private = rsa.newkeys(1024)
PRIVATE_PEM = _private.save_pkcs1().decode()
PUBLIC_PEM = _public.save_pkcs1().decode()


@pytest.fixture(autouse=True)
def google_env(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", CLIENT_ID)

    public_jwk = jwk.construct(PUBLIC_PEM, "RS256").to_dict()
    public_jwk.update({"kid": "test-key", "use": "sig", "alg": "RS256"})
    monkeypatch.setattr(google, "_google_keys", lambda: {"keys": [public_jwk]})

    sent = []
    monkeypatch.setattr(
        welcome, "send_email",
        lambda to, subject, text, html=None: sent.append(to) or True,
    )
    return sent


def make_token(email: str, **overrides) -> str:
    now = int(time.time())
    claims = {
        "iss": "https://accounts.google.com",
        "aud": CLIENT_ID,
        "sub": uuid.uuid4().hex,
        "email": email,
        "email_verified": True,
        "given_name": "Ерлан",
        "iat": now,
        "exp": now + 600,
    }
    claims.update(overrides)
    return jwt.encode(claims, PRIVATE_PEM, algorithm="RS256", headers={"kid": "test-key"})


def new_email() -> str:
    return f"google_{uuid.uuid4().hex[:10]}@gmail.com"


def test_config():
    assert client.get("/auth/google/config").json() == {"enabled": True, "client_id": CLIENT_ID}


def test_new_user_needs_consent_then_gets_account(google_env):
    email = new_email()
    token = make_token(email)

    first = client.post("/auth/google", json={"credential": token})
    assert first.status_code == 428
    assert get_user_by_email(email) is None

    second = client.post("/auth/google", json={"credential": token, "accept_terms": True})
    assert second.status_code == 200
    tokens = second.json()
    assert tokens["access_token"] and tokens["refresh_token"]

    user = get_user_by_email(email)
    assert user["password_hash"] is None
    assert user["display_name"] == "Ерлан"
    assert google_env == [email]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}).json()
    assert me == {"email": email, "username": user["username"], "display_name": "Ерлан", "has_password": False}


def test_existing_password_user_can_use_google():
    email = new_email()
    client.post(
        "/auth/register",
        json={"accept_terms": True, "email": email, "username": f"g_{uuid.uuid4().hex[:8]}", "password": "Password123!"},
    )

    response = client.post("/auth/google", json={"credential": make_token(email.upper())})
    assert response.status_code == 200


def test_rejects_bad_tokens():
    email = new_email()

    for token in (
        make_token(email, aud="someone-else"),
        make_token(email, iss="https://evil.example.com"),
        make_token(email, email_verified=False),
        make_token(email, exp=int(time.time()) - 60),
        make_token(email)[:-4] + "abcd",
    ):
        response = client.post("/auth/google", json={"credential": token, "accept_terms": True})
        assert response.status_code == 401, token

    assert get_user_by_email(email) is None


def test_disabled_without_client_id(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "")
    assert client.get("/auth/google/config").json()["enabled"] is False
    response = client.post("/auth/google", json={"credential": make_token(new_email())})
    assert response.status_code == 404


def test_google_user_can_delete_account_without_password():
    email = new_email()
    tokens = client.post(
        "/auth/google", json={"credential": make_token(email), "accept_terms": True}
    ).json()

    response = client.post(
        "/auth/delete-account",
        json={},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert response.status_code == 200
    assert get_user_by_email(email) is None


def test_password_user_still_needs_password_to_delete():
    email = new_email()
    client.post(
        "/auth/register",
        json={"accept_terms": True, "email": email, "username": f"g_{uuid.uuid4().hex[:8]}", "password": "Password123!"},
    )
    token = client.post("/auth/login", json={"email": email, "password": "Password123!"}).json()["access_token"]

    response = client.post(
        "/auth/delete-account", json={}, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
    assert get_user_by_email(email) is not None
