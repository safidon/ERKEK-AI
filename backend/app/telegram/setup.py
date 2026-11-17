"""
Telegram ботты бір рет баптау (серверде):

    docker compose exec backend python -m app.telegram.setup

Webhook-ты https://<DOMAIN>/api/telegram/webhook мекенжайына қояды,
мәзірдегі командаларды (қазақша/орысша) және бот сипаттамасын орнатады.
"""

import os
import sys

from app.telegram import api


COMMANDS = {
    "kk": [
        ("new", "Жаңа әңгіме"),
        ("mode", "ERKEK AI мінезін таңдау"),
        ("lang", "Тілді ауыстыру"),
        ("remind", "Күнделікті еске салу"),
        ("name", "Атыңды өзгерту"),
        ("help", "Көмек"),
        ("delete", "Аккаунтты жою"),
    ],
    "ru": [
        ("new", "Новый разговор"),
        ("mode", "Выбрать характер ERKEK AI"),
        ("lang", "Сменить язык"),
        ("remind", "Ежедневные напоминания"),
        ("name", "Изменить имя"),
        ("help", "Помощь"),
        ("delete", "Удалить аккаунт"),
    ],
}

DESCRIPTIONS = {
    "kk": (
        "ERKEK AI — ер адамдарға арналған цифрлық ментор. Жұмыс, ақша, отбасы, "
        "мақсат туралы жаз — бірге талдаймыз. 18+."
    ),
    "ru": (
        "ERKEK AI — цифровой наставник для мужчин. Пиши о работе, деньгах, семье, "
        "целях — разберём вместе. 18+."
    ),
}

SHORT = {
    "kk": "Ер адамдарға арналған AI ментор. erkekai.kz",
    "ru": "ИИ-наставник для мужчин. erkekai.kz",
}


def main() -> int:
    if not api.is_enabled():
        print("TELEGRAM_BOT_TOKEN және TELEGRAM_WEBHOOK_SECRET берілмеген.")
        return 1

    base = os.getenv("BACKEND_URL", "").rstrip("/")
    if not base.startswith("https://"):
        print("BACKEND_URL https:// болуы керек (мысалы https://erkekai.kz/api).")
        return 1

    me = api.call("getMe")
    if not me:
        print("Token жарамсыз сияқты: getMe жауап бермеді.")
        return 1

    print(f"Бот: @{me.get('username')}")
    if api.bot_username() and api.bot_username().lower() != str(me.get("username", "")).lower():
        print("Ескерту: TELEGRAM_BOT_USERNAME бот атымен сәйкес келмейді.")

    ok = api.call("setWebhook", {
        "url": f"{base}/telegram/webhook",
        "secret_token": api.webhook_secret(),
        "allowed_updates": ["message", "callback_query"],
        "drop_pending_updates": True,
    })
    print("Webhook:", "OK" if ok else "ҚАТЕ")

    # Әдепкі (тілі белгісіз) — қазақша, Telegram тілі орысша болса — орысша.
    for lang_code, lang in ((None, "kk"), ("kk", "kk"), ("ru", "ru")):
        extra = {"language_code": lang_code} if lang_code else {}
        api.call("setMyCommands", {
            "commands": [{"command": c, "description": d} for c, d in COMMANDS[lang]],
            **extra,
        })
        api.call("setMyDescription", {"description": DESCRIPTIONS[lang], **extra})
        api.call("setMyShortDescription", {"short_description": SHORT[lang], **extra})

    info = api.call("getWebhookInfo") or {}
    print("Webhook URL:", info.get("url"))
    if info.get("last_error_message"):
        print("Соңғы қате:", info["last_error_message"])

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
