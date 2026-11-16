from app.services.email_templates import password_reset_email


LINK = "https://erkekai.kz/reset-password?token=abc123&x=1"


def test_reset_email_has_link_in_both_versions():
    subject, text, html = password_reset_email(
        username="Мейрамбек",
        link=LINK,
        minutes=30,
    )

    assert "құпиясөз" in subject.lower()
    assert LINK in text
    # HTML ішінде & белгісі қорғалған түрде болуы керек
    assert "token=abc123&amp;x=1" in html
    assert "Сәлем, Мейрамбек!" in text
    assert "30 минут" in html
    assert "info@erkekai.kz" in html
    assert html.lstrip().startswith("<!DOCTYPE html>")


def test_username_is_escaped():
    _, _, html = password_reset_email(
        username="<script>alert(1)</script>",
        link=LINK,
        minutes=30,
    )

    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_greeting_without_username():
    _, text, _ = password_reset_email(username="", link=LINK, minutes=30)

    assert text.startswith("Сәлем!")


# =====================================================
# WELCOME
# =====================================================

import uuid  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402

import app.services.welcome as welcome  # noqa: E402
from app.main import app  # noqa: E402
from app.services.email_templates import welcome_email  # noqa: E402


def test_welcome_email_kk_and_ru():
    subject, text, html = welcome_email(username="Ерлан", language="kk")
    assert subject == "ERKEK AI-ға қош келдің"
    assert text.startswith("Қош келдің, Ерлан!")
    assert "/chat" in html and "112" in html and "111" in html

    subject, text, html = welcome_email(
        username="<b>x</b>", language="ru", telegram_url="https://t.me/erkek_bot"
    )
    assert subject == "Добро пожаловать в ERKEK AI"
    assert "<b>x</b>" not in html
    assert "https://t.me/erkek_bot" in html and "https://t.me/erkek_bot" in text


def test_register_sends_welcome_in_users_language(monkeypatch):
    sent = []
    monkeypatch.setattr(
        welcome, "send_email",
        lambda to, subject, text, html=None: sent.append((to, subject)) or True,
    )

    client = TestClient(app)
    suffix = uuid.uuid4().hex[:10]
    email = f"welcome_{suffix}@example.com"

    response = client.post(
        "/auth/register",
        json={
            "accept_terms": True,
            "email": email,
            "username": f"welcome_{suffix}",
            "password": "Welcome123!",
        },
        headers={"X-Lang": "ru"},
    )

    assert response.status_code == 201
    assert sent == [(email, "Добро пожаловать в ERKEK AI")]
