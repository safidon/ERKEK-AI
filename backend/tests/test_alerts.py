import logging
import random
import uuid

import pytest
from fastapi.testclient import TestClient

import app.services.alerts as alerts
from app.main import app
from app.telegram import accounts, api


class _ImmediateThread:
    """Тестте фондық thread-ті бірден орындайды."""

    def __init__(self, target, args=(), daemon=None):
        self.target = target
        self.args = args

    def start(self):
        self.target(*self.args)


@pytest.fixture
def delivered(monkeypatch):
    sent = []

    monkeypatch.setattr(alerts.threading, "Thread", _ImmediateThread)
    monkeypatch.setattr(alerts, "_last_sent", {})
    monkeypatch.setattr(alerts, "_sent_times", alerts.deque())

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:test")
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "secret")
    monkeypatch.setattr(
        api, "send_message",
        lambda chat_id, text, reply_markup=None, html=True: sent.append((str(chat_id), text)),
    )

    return sent


def admin_with_telegram(monkeypatch) -> str:
    """ADMIN_EMAILS ішіндегі, Telegram-ға байланған аккаунт жасайды."""

    client = TestClient(app)
    suffix = uuid.uuid4().hex[:10]
    email = f"alerts_{suffix}@example.com"
    client.post(
        "/auth/register",
        json={"accept_terms": True, "email": email, "username": f"al_{suffix}", "password": "Alerts123!"},
    )

    from app.auth.service import get_user_by_email

    user_id = get_user_by_email(email)["user_id"]
    chat_id = str(random.randint(10**9, 9 * 10**9))
    accounts.link_to_site_account(chat_id, chat_id, "kk", user_id)

    monkeypatch.setenv("ADMIN_EMAILS", email)
    return chat_id


def test_alert_goes_to_admin_telegram(delivered, monkeypatch):
    chat_id = admin_with_telegram(monkeypatch)

    assert alerts.send_alert("Backend қатесі", "Traceback ...\nValueError: <boom>")

    assert len(delivered) == 1
    assert delivered[0][0] == chat_id
    assert "&lt;boom&gt;" in delivered[0][1]


def test_same_error_is_sent_once(delivered, monkeypatch):
    admin_with_telegram(monkeypatch)

    assert alerts.send_alert("X", "same error")
    assert not alerts.send_alert("X", "same error")
    assert alerts.send_alert("X", "other error")
    assert len(delivered) == 2


def test_hourly_cap(delivered, monkeypatch):
    admin_with_telegram(monkeypatch)

    results = [alerts.send_alert("X", f"error {i}") for i in range(alerts.MAX_PER_HOUR + 5)]
    assert results.count(True) == alerts.MAX_PER_HOUR


def test_logger_error_triggers_alert(delivered, monkeypatch):
    admin_with_telegram(monkeypatch)

    test_logger = logging.getLogger(f"alerts-test-{uuid.uuid4().hex}")
    test_logger.propagate = False
    alerts.install_alert_handler(test_logger)

    test_logger.info("just info")
    try:
        raise RuntimeError("database exploded")
    except RuntimeError:
        test_logger.exception("Chat failed | user_id=1")

    assert len(delivered) == 1
    assert "database exploded" in delivered[0][1]


def test_no_admin_telegram_means_no_message(delivered, monkeypatch):
    monkeypatch.setenv("ADMIN_EMAILS", "nobody-linked@example.com")
    alerts.send_alert("X", "lonely error")
    assert delivered == []


def test_client_error_endpoint(delivered, monkeypatch):
    chat_id = admin_with_telegram(monkeypatch)
    monkeypatch.setenv("ALERTS_ENABLED", "true")

    client = TestClient(app)
    response = client.post(
        "/client-errors",
        json={"message": "TypeError: x is undefined", "url": "https://erkekai.kz/chat", "stack": "at foo"},
    )

    assert response.status_code == 204
    assert delivered and delivered[0][0] == chat_id
    assert "Frontend" in delivered[0][1]


def test_client_error_payload_is_limited():
    client = TestClient(app)
    response = client.post("/client-errors", json={"message": "x" * 5000})
    assert response.status_code == 422
