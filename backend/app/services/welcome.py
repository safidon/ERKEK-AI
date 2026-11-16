"""Тіркелгеннен кейінгі қош келдіңіз хаты (фонда жіберіледі)."""

from app.core.logger import logger
from app.services.email_service import send_email
from app.services.email_templates import welcome_email


def send_welcome_email(email: str, username: str, language: str = "kk") -> None:
    try:
        from app.telegram import api as telegram_api

        telegram_url = None
        if telegram_api.is_enabled() and telegram_api.bot_username():
            telegram_url = f"https://t.me/{telegram_api.bot_username()}"

        subject, text, html_body = welcome_email(
            username=username,
            language=language,
            telegram_url=telegram_url,
        )

        send_email(to=email, subject=subject, text=text, html=html_body)

    except Exception:
        logger.exception("Welcome email failed")
