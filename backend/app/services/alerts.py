"""
Қате мониторингі: қате болғанда әкімшінің Telegram-ына хабар жібереді.

Кімге: ADMIN_EMAILS ішіндегі, Telegram ботқа байланған аккаунттар.
Сыртқы қызмет (Sentry т.б.) қажет емес — бот арқылы жіберіледі.

Шу болмауы үшін:
- бірдей қате 15 минут ішінде бір рет қана жіберіледі;
- сағатына ең көбі 20 хабар.
Хабарламаға пайдаланушылардың хат мазмұны кірмейді — тек қате мәтіні.
"""

import html
import logging
import os
import threading
import time
import traceback
from collections import deque

from app.database import adapt_query, get_connection


REPEAT_WINDOW_SECONDS = 15 * 60
MAX_PER_HOUR = 20
MAX_DETAILS = 1500

_lock = threading.Lock()
_last_sent: dict[str, float] = {}
_sent_times: deque[float] = deque()


def _admin_chat_ids() -> list[str]:
    emails = [
        email.strip().lower()
        for email in os.getenv("ADMIN_EMAILS", "").split(",")
        if email.strip()
    ]

    if not emails:
        return []

    connection = get_connection()

    try:
        cursor = connection.cursor()
        placeholders = ", ".join("?" for _ in emails)
        cursor.execute(
            adapt_query(
                f"""
                SELECT t.chat_id
                FROM telegram_accounts t
                JOIN users u ON u.user_id = t.user_id
                WHERE LOWER(u.email) IN ({placeholders})
                """
            ),
            tuple(emails),
        )
        return [str(row["chat_id"]) for row in cursor.fetchall()]

    finally:
        connection.close()


def _should_send(key: str) -> bool:
    now = time.monotonic()

    with _lock:
        while _sent_times and now - _sent_times[0] > 3600:
            _sent_times.popleft()

        if len(_sent_times) >= MAX_PER_HOUR:
            return False

        last = _last_sent.get(key)
        if last is not None and now - last < REPEAT_WINDOW_SECONDS:
            return False

        _last_sent[key] = now
        _sent_times.append(now)

        # Ескі кілттерді тазалаймыз.
        if len(_last_sent) > 500:
            for old_key, sent_at in list(_last_sent.items()):
                if now - sent_at > REPEAT_WINDOW_SECONDS:
                    del _last_sent[old_key]

        return True


def _deliver(title: str, details: str) -> None:
    from app.telegram import api

    try:
        if not api.is_enabled():
            return

        chat_ids = _admin_chat_ids()
        if not chat_ids:
            return

        env = os.getenv("APP_ENV", "development")
        text = (
            f"🚨 <b>{html.escape(title)}</b>\n"
            f"<i>{html.escape(env)}</i>\n\n"
            f"<pre>{html.escape(details[-MAX_DETAILS:])}</pre>"
        )

        for chat_id in chat_ids:
            api.send_message(chat_id, text)

    except Exception:
        # Мониторинг ешқашан негізгі жұмысты бұзбауы керек.
        pass


def send_alert(title: str, details: str, key: str | None = None) -> bool:
    """Фонда жібереді. Жіберілсе (шектеуге түспесе) True."""

    dedup_key = key or f"{title}|{details.strip().splitlines()[-1] if details.strip() else ''}"

    if not _should_send(dedup_key):
        return False

    threading.Thread(target=_deliver, args=(title, details), daemon=True).start()
    return True


class AlertHandler(logging.Handler):
    """ERROR деңгейіндегі логтарды әкімшіге жібереді."""

    def __init__(self):
        super().__init__(level=logging.ERROR)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = record.getMessage()
            details = message

            if record.exc_info:
                details += "\n\n" + "".join(
                    traceback.format_exception(*record.exc_info)
                )

            title = "Backend қатесі"
            key = f"{record.pathname}:{record.lineno}:{message.split('|')[0].strip()}"
            send_alert(title, details, key=key)

        except Exception:
            pass


def install_alert_handler(target: logging.Logger) -> None:
    if not any(isinstance(h, AlertHandler) for h in target.handlers):
        target.addHandler(AlertHandler())
