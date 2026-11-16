import itertools
import random
import uuid

import pytest
from fastapi.testclient import TestClient

from app.auth.service import get_user_by_email, get_user_by_id
from app.database import adapt_query, get_connection
from app.main import app
from app.telegram import accounts, api, bot
from app.telegram.format import markdown_to_telegram_html, split_message


client = TestClient(app)

SECRET = "test-webhook-secret"
PASSWORD = "Telegram123!"

_update_ids = itertools.count(random.randint(10_000_000, 90_000_000))


@pytest.fixture(autouse=True)
def fake_telegram(monkeypatch):
    """Telegram API-ға шықпай, жіберілгенді тізімге жинайды."""

    sent = []

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:test")
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", SECRET)
    monkeypatch.setenv("TELEGRAM_BOT_USERNAME", "erkek_test_bot")

    monkeypatch.setattr(
        api, "send_message",
        lambda chat_id, text, reply_markup=None, html=True: sent.append(
            {"chat_id": chat_id, "text": text, "markup": reply_markup}
        ),
    )
    monkeypatch.setattr(api, "send_typing", lambda chat_id: None)
    monkeypatch.setattr(api, "answer_callback", lambda *a, **k: None)
    monkeypatch.setattr(api, "edit_reply_markup", lambda *a, **k: sent.append({"edit_markup": a[2]}))
    monkeypatch.setattr(api, "edit_text", lambda *a, **k: sent.append({"edit_text": a[2]}))

    monkeypatch.setattr("app.routes.chat.ask_ai", lambda *a, **k: "**Жарайсың**, брат. Келесі қадам:\n- бірінші\n- екінші")
    monkeypatch.setattr("app.brain.conversation_summary.ask_ai", lambda *a, **k: "Қысқаша.")

    return sent


def new_tg_id() -> int:
    return random.randint(10**9, 9 * 10**9)


def text_update(tg_id: int, text: str, language_code: str = "kk") -> dict:
    return {
        "update_id": next(_update_ids),
        "message": {
            "message_id": 1,
            "from": {"id": tg_id, "is_bot": False, "language_code": language_code},
            "chat": {"id": tg_id, "type": "private"},
            "text": text,
        },
    }


def callback_update(tg_id: int, data: str) -> dict:
    return {
        "update_id": next(_update_ids),
        "callback_query": {
            "id": "cb1",
            "from": {"id": tg_id, "language_code": "kk"},
            "message": {"message_id": 5, "chat": {"id": tg_id, "type": "private"}},
            "data": data,
        },
    }


def count(table: str, column: str, value) -> int:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            adapt_query(f"SELECT COUNT(*) AS n FROM {table} WHERE {column} = ?"),
            (value,),
        )
        return cursor.fetchone()["n"]
    finally:
        connection.close()


def start_and_accept(tg_id: int, sent, lang: str = "kk") -> str:
    bot.handle_update(text_update(tg_id, "/start"))
    bot.handle_update(callback_update(tg_id, f"lang:{lang}"))
    bot.handle_update(callback_update(tg_id, "accept"))
    bot.handle_update(callback_update(tg_id, "name:skip"))
    return accounts.get_by_telegram_id(tg_id)["user_id"]


# =====================================================
# FORMAT
# =====================================================

def test_markdown_to_html():
    html = markdown_to_telegram_html("## Жоспар\n**Маңызды** <тег> және `код`\n- бір\n- екі")
    assert "<b>Жоспар</b>" in html
    assert "<b>Маңызды</b>" in html
    assert "&lt;тег&gt;" in html
    assert "<code>код</code>" in html
    assert "• бір" in html


def test_split_long_message():
    text = "\n\n".join("абзац " * 200 for _ in range(10))
    chunks = split_message(text, limit=3800)
    assert len(chunks) > 1
    assert all(len(chunk) <= 3800 for chunk in chunks)


# =====================================================
# CONSENT + CHAT
# =====================================================

def test_onboarding_language_consent_name_then_first_question(fake_telegram):
    tg_id = new_tg_id()

    bot.handle_update(text_update(tg_id, "Жұмыс таппай жүрмін"))

    # 1. Тіл таңдау (жалаушалар)
    assert accounts.get_by_telegram_id(tg_id) is None
    flags = [b["callback_data"] for b in fake_telegram[-1]["markup"]["inline_keyboard"][0]]
    assert flags == ["lang:kk", "lang:ru"]

    # 2. Келісім (таңдалған тілде)
    bot.handle_update(callback_update(tg_id, "lang:ru"))
    assert "Согласен" in fake_telegram[-1]["markup"]["inline_keyboard"][0][0]["text"]
    assert accounts.get_by_telegram_id(tg_id) is None

    # 3. Есім
    bot.handle_update(callback_update(tg_id, "accept"))
    account = accounts.get_by_telegram_id(tg_id)
    assert account is not None
    assert account["lang"] == "ru"
    assert account["awaiting"] == "name"
    assert "Как тебя зовут" in fake_telegram[-1]["text"]

    user = get_user_by_id(account["user_id"])
    assert user["email"] is None
    assert count("user_consents", "user_id", account["user_id"]) > 0

    bot.handle_update(text_update(tg_id, "ерлан"))
    assert get_user_by_id(account["user_id"])["display_name"] == "Ерлан"
    assert accounts.get_by_telegram_id(tg_id)["awaiting"] is None

    # 4. Алғашқы сұраққа бірден жауап келеді (батырмалары бар).
    answer = fake_telegram[-1]
    assert "<b>Жарайсың</b>" in answer["text"]
    buttons = answer["markup"]["inline_keyboard"][0]
    assert buttons[0]["callback_data"].startswith("fb:")
    assert count("conversations", "user_id", account["user_id"]) == 2


def test_chat_and_new_session(fake_telegram):
    tg_id = new_tg_id()
    user_id = start_and_accept(tg_id, fake_telegram)

    bot.handle_update(text_update(tg_id, "Сәлем"))
    first_session = accounts.get_by_telegram_id(tg_id)["active_session_id"]
    assert first_session

    bot.handle_update(text_update(tg_id, "/new"))
    bot.handle_update(text_update(tg_id, "Тағы сұрақ"))

    assert accounts.get_by_telegram_id(tg_id)["active_session_id"] != first_session
    assert count("conversation_sessions", "user_id", user_id) == 2


def test_duplicate_update_is_ignored(fake_telegram):
    tg_id = new_tg_id()
    user_id = start_and_accept(tg_id, fake_telegram)

    update = text_update(tg_id, "Бір рет қана")
    bot.handle_update(update)
    bot.handle_update(update)

    assert count("conversations", "user_id", user_id) == 2


def test_group_chats_are_ignored(fake_telegram):
    tg_id = new_tg_id()
    update = text_update(tg_id, "/start")
    update["message"]["chat"]["type"] = "group"

    before = len(fake_telegram)
    bot.handle_update(update)
    assert len(fake_telegram) == before


# =====================================================
# MODE + FEEDBACK
# =====================================================

def test_mode_switch(fake_telegram):
    tg_id = new_tg_id()
    user_id = start_and_accept(tg_id, fake_telegram)

    bot.handle_update(text_update(tg_id, "/mode"))
    options = [row[0]["callback_data"] for row in fake_telegram[-1]["markup"]["inline_keyboard"]]
    assert "mode:strategist" in options

    bot.handle_update(callback_update(tg_id, "mode:strategist"))
    assert get_user_by_id(user_id)["persona"] == "strategist"


def test_feedback_toggle(fake_telegram):
    tg_id = new_tg_id()
    user_id = start_and_accept(tg_id, fake_telegram)

    bot.handle_update(text_update(tg_id, "Кеңес бер"))
    data = fake_telegram[-1]["markup"]["inline_keyboard"][0][0]["callback_data"]

    bot.handle_update(callback_update(tg_id, data))
    assert count("message_feedback", "user_id", user_id) == 1
    assert fake_telegram[-1]["edit_markup"]["inline_keyboard"][0][0]["text"] == "👍 ✓"

    bot.handle_update(callback_update(tg_id, data))
    assert count("message_feedback", "user_id", user_id) == 0


def test_cannot_rate_someone_elses_answer(fake_telegram):
    owner = new_tg_id()
    start_and_accept(owner, fake_telegram)
    bot.handle_update(text_update(owner, "Менің сұрағым"))
    data = fake_telegram[-1]["markup"]["inline_keyboard"][0][0]["callback_data"]

    stranger = new_tg_id()
    stranger_id = start_and_accept(stranger, fake_telegram)
    bot.handle_update(callback_update(stranger, data))

    assert count("message_feedback", "user_id", stranger_id) == 0


# =====================================================
# DELETE
# =====================================================

def test_delete_telegram_only_account(fake_telegram):
    tg_id = new_tg_id()
    user_id = start_and_accept(tg_id, fake_telegram)
    bot.handle_update(text_update(tg_id, "Сәлем"))

    bot.handle_update(text_update(tg_id, "/delete"))
    bot.handle_update(callback_update(tg_id, "del:yes"))

    assert get_user_by_id(user_id) is None
    assert accounts.get_by_telegram_id(tg_id) is None
    assert count("conversations", "user_id", user_id) == 0


# =====================================================
# LINK SITE ACCOUNT
# =====================================================

def site_user():
    suffix = uuid.uuid4().hex[:10]
    email = f"tg_site_{suffix}@example.com"
    client.post(
        "/auth/register",
        json={"accept_terms": True, "email": email, "username": f"tgs_{suffix}", "password": PASSWORD},
    )
    token = client.post("/auth/login", json={"email": email, "password": PASSWORD}).json()["access_token"]
    return {
        "user_id": get_user_by_email(email)["user_id"],
        "headers": {"Authorization": f"Bearer {token}"},
    }


def link_code(site) -> str:
    response = client.post("/telegram/link", headers=site["headers"])
    assert response.status_code == 200
    url = response.json()["url"]
    assert url.startswith("https://t.me/erkek_test_bot?start=link_")
    return url.split("start=")[1]


def test_link_moves_telegram_chats_to_site_account(fake_telegram):
    tg_id = new_tg_id()
    old_user_id = start_and_accept(tg_id, fake_telegram)
    bot.handle_update(text_update(tg_id, "Telegram-дағы сұрақ"))

    site = site_user()
    assert client.get("/telegram/status", headers=site["headers"]).json()["linked"] is False

    bot.handle_update(text_update(tg_id, f"/start {link_code(site)}"))

    assert accounts.get_by_telegram_id(tg_id)["user_id"] == site["user_id"]
    assert count("conversations", "user_id", site["user_id"]) == 2
    assert get_user_by_id(old_user_id) is None
    assert client.get("/telegram/status", headers=site["headers"]).json()["linked"] is True

    # Енді Telegram-дағы хабарлама сайт аккаунтына жазылады.
    bot.handle_update(text_update(tg_id, "Тағы бір сұрақ"))
    assert count("conversations", "user_id", site["user_id"]) == 4


def test_link_code_is_single_use(fake_telegram):
    site = site_user()
    code = link_code(site)

    bot.handle_update(text_update(new_tg_id(), f"/start {code}"))
    other = new_tg_id()
    bot.handle_update(text_update(other, f"/start {code}"))

    assert accounts.get_by_telegram_id(other) is None


def test_relinking_does_not_move_another_site_accounts_data(fake_telegram):
    tg_id = new_tg_id()
    first = site_user()
    bot.handle_update(text_update(tg_id, f"/start {link_code(first)}"))
    bot.handle_update(text_update(tg_id, "Бірінші аккаунттағы сұрақ"))

    second = site_user()
    bot.handle_update(text_update(tg_id, f"/start {link_code(second)}"))

    assert accounts.get_by_telegram_id(tg_id)["user_id"] == second["user_id"]
    assert count("conversations", "user_id", first["user_id"]) == 2
    assert count("conversations", "user_id", second["user_id"]) == 0
    assert get_user_by_id(first["user_id"]) is not None


def test_unlink_from_site(fake_telegram):
    site = site_user()
    tg_id = new_tg_id()
    bot.handle_update(text_update(tg_id, f"/start {link_code(site)}"))

    assert client.delete("/telegram/link", headers=site["headers"]).status_code == 200
    assert accounts.get_by_telegram_id(tg_id) is None
    assert get_user_by_id(site["user_id"]) is not None


# =====================================================
# WEBHOOK
# =====================================================

def test_webhook_requires_secret(fake_telegram):
    update = text_update(new_tg_id(), "/start")

    assert client.post("/telegram/webhook", json=update).status_code == 403
    assert client.post(
        "/telegram/webhook", json=update,
        headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"},
    ).status_code == 403

    before = len(fake_telegram)
    response = client.post(
        "/telegram/webhook", json=update,
        headers={"X-Telegram-Bot-Api-Secret-Token": SECRET},
    )
    assert response.status_code == 200
    assert len(fake_telegram) == before + 1


def test_webhook_disabled_without_token(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "")
    response = client.post(
        "/telegram/webhook", json={},
        headers={"X-Telegram-Bot-Api-Secret-Token": SECRET},
    )
    assert response.status_code == 404
    assert client.get("/telegram/info").json()["enabled"] is False


# =====================================================
# ADMIN STATS
# =====================================================

def test_admin_sees_telegram_split(fake_telegram, monkeypatch):
    admin = site_user()
    admin_email = get_user_by_id(admin["user_id"])["email"]
    monkeypatch.setenv("ADMIN_EMAILS", admin_email)

    before = client.get("/admin/stats", headers=admin["headers"]).json()

    tg_only = new_tg_id()
    start_and_accept(tg_only, fake_telegram)
    bot.handle_update(text_update(tg_only, "Telegram-нан сұрақ"))

    linked = new_tg_id()
    bot.handle_update(text_update(linked, f"/start {link_code(site_user())}"))
    bot.handle_update(text_update(linked, "Байланысқан аккаунттан сұрақ"))

    after = client.get("/admin/stats", headers=admin["headers"]).json()

    assert after["telegram"]["users"] == before["telegram"]["users"] + 2
    assert after["telegram"]["linked_to_site"] == before["telegram"]["linked_to_site"] + 1
    assert after["telegram"]["messages_today"] == before["telegram"]["messages_today"] + 2
    assert after["daily"][-1]["telegram_messages"] == after["telegram"]["messages_today"]
    # Telegram санауышы пайдаланушы ретінде есептелмейді.
    assert after["users"]["active_today"] == before["users"]["active_today"] + 2


# =====================================================
# NAME + LANGUAGE
# =====================================================

def test_name_goes_into_ai_memory(fake_telegram):
    from app.brain.memory import get_user_profile

    tg_id = new_tg_id()
    bot.handle_update(text_update(tg_id, "/start"))
    bot.handle_update(callback_update(tg_id, "lang:kk"))
    bot.handle_update(callback_update(tg_id, "accept"))
    bot.handle_update(text_update(tg_id, "Мейрамбек"))

    user_id = accounts.get_by_telegram_id(tg_id)["user_id"]
    assert "Аты: Мейрамбек" in get_user_profile(user_id).get_context()
    assert "Мейрамбек" in fake_telegram[-1]["text"]


def test_question_instead_of_name_is_answered(fake_telegram):
    tg_id = new_tg_id()
    bot.handle_update(text_update(tg_id, "/start"))
    bot.handle_update(callback_update(tg_id, "lang:kk"))
    bot.handle_update(callback_update(tg_id, "accept"))

    bot.handle_update(text_update(tg_id, "Жұмысымды қалай ауыстырсам болады?"))

    user_id = accounts.get_by_telegram_id(tg_id)["user_id"]
    assert get_user_by_id(user_id)["display_name"] is None
    assert count("conversations", "user_id", user_id) == 2


def test_change_language_and_name_later(fake_telegram):
    tg_id = new_tg_id()
    user_id = start_and_accept(tg_id, fake_telegram)

    bot.handle_update(text_update(tg_id, "/lang"))
    bot.handle_update(callback_update(tg_id, "lang:ru"))
    assert accounts.get_by_telegram_id(tg_id)["lang"] == "ru"

    bot.handle_update(text_update(tg_id, "/name"))
    assert "Как тебя зовут" in fake_telegram[-1]["text"]
    bot.handle_update(text_update(tg_id, "Арман"))
    assert get_user_by_id(user_id)["display_name"] == "Арман"


def test_name_is_html_escaped(fake_telegram):
    tg_id = new_tg_id()
    bot.handle_update(text_update(tg_id, "/start"))
    bot.handle_update(callback_update(tg_id, "lang:kk"))
    bot.handle_update(callback_update(tg_id, "accept"))
    bot.handle_update(text_update(tg_id, "Али & Co"))

    assert "Али &amp; Co" in fake_telegram[-1]["text"]


def test_dislike_asks_for_reason_in_bot(fake_telegram):
    tg_id = new_tg_id()
    user_id = start_and_accept(tg_id, fake_telegram)
    bot.handle_update(text_update(tg_id, "Кеңес бер"))

    dislike = fake_telegram[-1]["markup"]["inline_keyboard"][0][1]["callback_data"]
    bot.handle_update(callback_update(tg_id, dislike))

    keyboard = fake_telegram[-1]["edit_markup"]["inline_keyboard"]
    reasons = [b["callback_data"] for row in keyboard[1:] for b in row]
    assert any(r.endswith(":too_long") for r in reasons)

    reason = next(r for r in reasons if r.endswith(":too_long"))
    bot.handle_update(callback_update(tg_id, reason))

    from app.services.feedback import get_feedback_details

    message_id = int(reason.split(":")[1])
    assert get_feedback_details(user_id, [message_id])[message_id] == {"rating": -1, "reason": "too_long"}
    # Себеп таңдалғаннан кейін тек 👍 / 👎✓ қалады.
    assert len(fake_telegram[-1]["edit_markup"]["inline_keyboard"]) == 1
