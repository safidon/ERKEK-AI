"""
Telegram Bot API-ға қарапайым синхронды сұраныстар.

Баптау (env):
- TELEGRAM_BOT_TOKEN       — @BotFather берген token;
- TELEGRAM_WEBHOOK_SECRET  — webhook сұраныстарын тексеретін құпия мән;
- TELEGRAM_BOT_USERNAME    — бот аты (@-сыз), сілтемелер үшін.
Token берілмесе, бот өшірулі деп саналады.
"""

import os

import httpx

from app.core.logger import logger


API_BASE = "https://api.telegram.org"


def bot_token() -> str:
    return os.getenv("TELEGRAM_BOT_TOKEN", "").strip()


def webhook_secret() -> str:
    return os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()


def bot_username() -> str:
    return os.getenv("TELEGRAM_BOT_USERNAME", "").strip().lstrip("@")


def is_enabled() -> bool:
    return bool(bot_token() and webhook_secret())


def call(method: str, payload: dict | None = None, timeout: float = 15) -> dict | None:
    """Bot API әдісін шақырады. Қате болса None (лог жазылады, token жазылмайды)."""

    token = bot_token()

    if not token:
        return None

    try:
        response = httpx.post(
            f"{API_BASE}/bot{token}/{method}",
            json=payload or {},
            timeout=timeout,
        )
        data = response.json()

    except Exception as error:
        logger.warning("Telegram API %s failed | %s", method, type(error).__name__)
        return None

    if not data.get("ok"):
        logger.warning(
            "Telegram API %s error | %s",
            method,
            data.get("description", "unknown"),
        )
        return None

    return data.get("result")


def send_message(
    chat_id: str | int,
    text: str,
    reply_markup: dict | None = None,
    html: bool = True,
) -> dict | None:
    payload = {
        "chat_id": chat_id,
        "text": text,
        "link_preview_options": {"is_disabled": True},
    }

    if html:
        payload["parse_mode"] = "HTML"

    if reply_markup:
        payload["reply_markup"] = reply_markup

    result = call("sendMessage", payload)

    # HTML белгілеуі қате болса — қарапайым мәтінмен қайталаймыз.
    if result is None and html:
        payload.pop("parse_mode", None)
        result = call("sendMessage", payload)

    return result


def send_typing(chat_id: str | int) -> None:
    call("sendChatAction", {"chat_id": chat_id, "action": "typing"}, timeout=5)


def answer_callback(callback_id: str, text: str | None = None) -> None:
    payload = {"callback_query_id": callback_id}
    if text:
        payload["text"] = text
    call("answerCallbackQuery", payload, timeout=5)


def edit_reply_markup(chat_id: str | int, message_id: int, reply_markup: dict | None) -> None:
    call(
        "editMessageReplyMarkup",
        {
            "chat_id": chat_id,
            "message_id": message_id,
            "reply_markup": reply_markup or {"inline_keyboard": []},
        },
        timeout=5,
    )


def edit_text(
    chat_id: str | int,
    message_id: int,
    text: str,
    reply_markup: dict | None = None,
) -> None:
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML",
        "link_preview_options": {"is_disabled": True},
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    call("editMessageText", payload, timeout=10)
