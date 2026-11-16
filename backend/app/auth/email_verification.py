"""
Email-ді растау (белсендіру сілтемесі).

users.email_verified:
- NULL — бұрын тіркелген аккаунттар (растау талап етілмейді);
- 0    — email арқылы жаңа тіркелген, әлі расталмаған;
- 1    — расталған (сілтеме, Google немесе құпиясөзді қалпына келтіру арқылы).

Token кездейсоқ, базада тек SHA-256 hash-і сақталады, 24 сағат жарамды,
бір рет қолданылады. REQUIRE_EMAIL_VERIFICATION=false болса — талап өшеді.
"""

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

from app.auth.service import get_user_by_email
from app.core.config import FRONTEND_URL
from app.core.logger import logger
from app.database import adapt_query, get_connection
from app.services.email_service import send_email
from app.services.email_templates import verification_email


VERIFY_EXPIRE_HOURS = 24


def verification_required() -> bool:
    return os.getenv("REQUIRE_EMAIL_VERIFICATION", "true").lower() != "false"


def is_unverified(user) -> bool:
    """Аккаунт растауды күтіп тұр ма (тек жаңа email тіркелулері)."""

    if not verification_required():
        return False

    try:
        value = user["email_verified"]
    except (KeyError, IndexError):
        return False

    return value is not None and int(value) == 0


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _execute(queries: list[tuple[str, tuple]]) -> None:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        for query, params in queries:
            cursor.execute(adapt_query(query), params)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def mark_unverified(user_id: str) -> None:
    _execute([("UPDATE users SET email_verified = 0 WHERE user_id = ?", (user_id,))])


def mark_verified(user_id: str) -> None:
    _execute([("UPDATE users SET email_verified = 1 WHERE user_id = ?", (user_id,))])


def create_verification_token(user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    now = _now()

    _execute([
        # Бұрынғы қолданылмаған сілтемелер жарамсыз болады.
        ("DELETE FROM email_verification_tokens WHERE user_id = ?", (user_id,)),
        (
            """
            INSERT INTO email_verification_tokens
                (token_hash, user_id, expires_at, used_at, created_at)
            VALUES (?, ?, ?, NULL, ?)
            """,
            (
                _hash(token),
                user_id,
                (now + timedelta(hours=VERIFY_EXPIRE_HOURS)).isoformat(),
                now.isoformat(),
            ),
        ),
    ])

    return token


def build_verify_link(token: str) -> str:
    return f"{FRONTEND_URL.rstrip('/')}/verify-email?token={token}"


def send_verification(user_id: str, email: str, username: str, language: str = "kk") -> None:
    """Белсендіру хатын жібереді (фонда шақырылады, қате шығармайды)."""

    try:
        token = create_verification_token(user_id)
        subject, text, html_body = verification_email(
            username=username,
            link=build_verify_link(token),
            hours=VERIFY_EXPIRE_HOURS,
            language=language,
        )
        send_email(to=email, subject=subject, text=text, html=html_body)
    except Exception:
        logger.exception("Verification email failed | user_id=%s", user_id)


def resend_verification(email: str, language: str = "kk") -> None:
    """Email расталмаған аккаунт болса ғана хатты қайта жібереді."""

    user = get_user_by_email(email)

    if not user or not user["is_active"] or not is_unverified(user):
        return

    send_verification(user["user_id"], user["email"], user["username"] or "", language)


def verify_token(token: str) -> str | None:
    """Token жарамды болса email-ді растап, user_id қайтарады."""

    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute(
            adapt_query(
                """
                SELECT user_id, expires_at, used_at
                FROM email_verification_tokens
                WHERE token_hash = ?
                """
            ),
            (_hash(token),),
        )
        row = cursor.fetchone()

    finally:
        connection.close()

    if not row or row["used_at"]:
        return None

    if datetime.fromisoformat(row["expires_at"]) <= _now():
        return None

    user_id = row["user_id"]

    _execute([
        ("UPDATE users SET email_verified = 1 WHERE user_id = ?", (user_id,)),
        (
            "UPDATE email_verification_tokens SET used_at = ? WHERE token_hash = ?",
            (_now().isoformat(), _hash(token)),
        ),
    ])

    logger.info("Email verified | user_id=%s", user_id)

    return user_id
