"""
Күнделікті еске салу (Telegram, тек пайдаланушы өзі қосса).

- Сағатты пайдаланушы таңдайды (Астана уақыты), /remind арқылы өзгертеді.
- Күніне бір рет қана; сол күні өзі жазған болса — жіберілмейді.
- Пайдаланушы ботты бұғаттаса — еске салу өзі өшеді.
- Жіберілген еске салулар саны usage_daily-де "__reminders__" ретінде сақталады.
"""

import asyncio
import html
import os
from datetime import datetime

from app.core.logger import logger
from app.database import adapt_query, get_connection
from app.services.usage import USAGE_TZ, _add
from app.telegram import api


REMINDER_SCOPE = "__reminders__"
REMINDER_HOURS = (9, 13, 21)
CHECK_EVERY_SECONDS = 300

PROMPTS = {
    "kk": [
        "Кеш жарық, {name} 🤝 Бүгін мақсатыңа қарай қандай бір қадам жасадың?",
        "{name}, бүгінгі күнің қалай өтті? Бір жақсы нәрсе және бір қиын нәрсе айтшы.",
        "Сәлем, {name}. Бүгін өзіңе берген уәдеңді орындадың ба? Жаз — бірге талдаймыз.",
        "{name}, бүгін не үшін өзіңе «жарайсың» дей аласың?",
        "Кеш жарық, {name}. Ертеңге бір ғана маңызды іс белгілейік пе?",
        "{name}, ойыңды мазалап жүрген бір нәрсе бар ма? Жаз, тыңдаймын.",
        "Сәлем, {name} 💪 Апта қалай басталды? Ең маңызды міндетің қайсы?",
    ],
    "ru": [
        "Добрый вечер, {name} 🤝 Какой шаг к своей цели ты сделал сегодня?",
        "{name}, как прошёл день? Расскажи одну хорошую и одну трудную вещь.",
        "Привет, {name}. Сдержал сегодня обещание, данное себе? Напиши — разберём вместе.",
        "{name}, за что сегодня можешь сказать себе «молодец»?",
        "Добрый вечер, {name}. Наметим одно главное дело на завтра?",
        "{name}, что-то не даёт покоя? Напиши, я слушаю.",
        "Привет, {name} 💪 Как начинается неделя? Какая задача самая важная?",
    ],
}

DEFAULT_NAME = {"kk": "брат", "ru": "брат"}

FOOTER = {
    "kk": "\n\n<i>Еске салуды өзгерту немесе өшіру: /remind</i>",
    "ru": "\n\n<i>Изменить или выключить напоминания: /remind</i>",
}


def reminders_enabled() -> bool:
    return (
        os.getenv("REMINDERS_ENABLED", "true").lower() != "false"
        and api.is_enabled()
    )


def _fetch(query: str, params: tuple) -> list:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(adapt_query(query), params)
        return cursor.fetchall()
    finally:
        connection.close()


def _execute(query: str, params: tuple) -> None:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(adapt_query(query), params)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def set_reminder(telegram_user_id, hour: int | None) -> None:
    # Бүгінгі күн «жіберілді» деп белгіленеді: 21:30-да қосса,
    # бірден емес, ертеңнен бастап келеді.
    today = datetime.now(USAGE_TZ).date().isoformat()
    _execute(
        """
        UPDATE telegram_accounts
        SET reminder_hour = ?, last_reminded_on = ?
        WHERE telegram_user_id = ?
        """,
        (hour, today, str(telegram_user_id)),
    )


def build_text(lang: str, name: str | None, day_index: int) -> str:
    prompts = PROMPTS.get(lang, PROMPTS["kk"])

    shown = html.escape(name) if name else DEFAULT_NAME.get(lang, "брат")
    text = prompts[day_index % len(prompts)].format(name=shown)
    # Атсыз болса, сөйлем «брат» деп басталады — бас әріппен.
    text = text[:1].upper() + text[1:]
    return text + FOOTER.get(lang, FOOTER["kk"])


def send_due_reminders(now: datetime | None = None) -> int:
    """Уақыты келген еске салуларды жібереді. Жіберілген санын қайтарады."""

    now = (now or datetime.now(USAGE_TZ)).astimezone(USAGE_TZ)
    today = now.date().isoformat()

    rows = _fetch(
        """
        SELECT t.telegram_user_id, t.user_id, t.chat_id, t.lang, u.display_name
        FROM telegram_accounts t
        JOIN users u ON u.user_id = t.user_id
        WHERE t.reminder_hour = ?
          AND (t.last_reminded_on IS NULL OR t.last_reminded_on <> ?)
          AND u.is_active = 1
        """,
        (now.hour, today),
    )

    sent = 0

    for row in rows:
        tg_id = row["telegram_user_id"]

        # Белгі қоямыз — бір күнде екі рет жіберілмейді.
        _execute(
            "UPDATE telegram_accounts SET last_reminded_on = ? WHERE telegram_user_id = ?",
            (today, tg_id),
        )

        # Бүгін өзі жазған болса — мазаламаймыз.
        active = _fetch(
            "SELECT messages FROM usage_daily WHERE day = ? AND scope = ?",
            (today, row["user_id"]),
        )
        if active and int(active[0]["messages"] or 0) > 0:
            continue

        result = api.send_message_checked(
            row["chat_id"],
            build_text(row["lang"], row["display_name"], now.timetuple().tm_yday),
        )

        if result == "ok":
            sent += 1
        elif result == "blocked":
            set_reminder(tg_id, None)
            logger.info("Reminder disabled: bot blocked | user_id=%s", row["user_id"])

    if sent:
        _add(REMINDER_SCOPE, messages=sent)
        logger.info("Reminders sent | count=%s | hour=%s", sent, now.hour)

    return sent


async def reminder_loop() -> None:
    """Backend іске қосылғанда фонда жұмыс істейді."""

    while True:
        try:
            if reminders_enabled():
                await asyncio.to_thread(send_due_reminders)
        except Exception:
            logger.exception("Reminder loop failed")

        await asyncio.sleep(CHECK_EVERY_SECONDS)
