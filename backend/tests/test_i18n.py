import uuid

from fastapi.testclient import TestClient

import app.auth.password_reset as password_reset
from app.core.i18n import (
    RU_MESSAGES,
    language_from_headers,
    translate,
)
from app.main import app
from app.services.email_templates import password_reset_email


client = TestClient(app)


def test_language_detection():
    assert language_from_headers({}) == "kk"
    assert language_from_headers({"x-lang": "ru"}) == "ru"
    assert language_from_headers({"x-lang": "en"}) == "kk"
    assert language_from_headers({"cookie": "a=1; erkek_lang=ru"}) == "ru"
    assert language_from_headers({"cookie": "erkek_lang=kk"}) == "kk"
    # Header cookie-ден басым
    assert language_from_headers({"x-lang": "kk", "cookie": "erkek_lang=ru"}) == "kk"


def test_translate_exact_and_patterns():
    assert translate("Әңгіме табылмады.", "ru") == "Разговор не найден."
    assert translate("Әңгіме табылмады.", "kk") == "Әңгіме табылмады."
    assert translate(
        "Бүгінгі 50 хабарлама лимиті бітті. Ертең қайта жалғастырамыз.", "ru"
    ) == "Дневной лимит в 50 сообщений исчерпан. Продолжим завтра."
    # Белгісіз мәтін өзгермейді
    assert translate("Басқа мәтін", "ru") == "Басқа мәтін"


def test_all_translations_are_russian():
    for kazakh, russian in RU_MESSAGES.items():
        assert russian and russian != kazakh


def test_error_detail_translated_by_cookie():
    response = client.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": "WrongPassword1!"},
        cookies={"erkek_lang": "ru"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Неверный email или пароль."


def test_error_detail_stays_kazakh_by_default():
    response = client.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": "WrongPassword1!"},
    )

    assert response.json()["detail"] == "Email немесе пароль қате."


def test_duplicate_email_translated():
    suffix = uuid.uuid4().hex[:10]
    payload = {
        "accept_terms": True,
        "email": f"i18n_{suffix}@example.com",
        "username": f"i18n_{suffix}",
        "password": "I18nPassword123!",
    }
    assert client.post("/auth/register", json=payload).status_code == 201

    payload["username"] = f"i18n2_{suffix}"
    response = client.post("/auth/register", json=payload, headers={"X-Lang": "ru"})

    assert response.status_code == 409
    assert response.json()["detail"] == "Этот email уже зарегистрирован."


def test_russian_reset_email(monkeypatch):
    suffix = uuid.uuid4().hex[:10]
    email = f"i18n_reset_{suffix}@example.com"
    client.post(
        "/auth/register",
        json={
            "accept_terms": True,
            "email": email,
            "username": f"i18n_reset_{suffix}",
            "password": "I18nPassword123!",
        },
    )

    sent = []
    monkeypatch.setattr(
        password_reset,
        "send_email",
        lambda to, subject, text, html=None: sent.append(subject) or True,
    )

    response = client.post(
        "/auth/forgot-password",
        json={"email": email},
        cookies={"erkek_lang": "ru"},
    )

    assert response.status_code == 200
    assert response.json()["detail"].startswith("Если этот email")
    assert sent == ["Восстановление пароля — ERKEK AI"]


def test_reset_email_template_ru():
    subject, text, html = password_reset_email(
        username="Рустам", link="https://erkekai.kz/r?t=1", minutes=30, language="ru"
    )

    assert subject == "Восстановление пароля — ERKEK AI"
    assert text.startswith("Привет, Рустам!")
    assert '<html lang="ru">' in html
    assert "Конфиденциальность" in html
    assert "құпиясөз" not in html.lower()
