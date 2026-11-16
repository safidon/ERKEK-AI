"""
Құпиясөзді қалпына келтіру.

- Token кездейсоқ (secrets), базада тек SHA-256 hash-і сақталады.
- Token бір рет қолданылады және PASSWORD_RESET_EXPIRE_MINUTES ішінде жарамды.
- Құпиясөз ауысқанда пайдаланушының басқа token-дері де жарамсыз болады.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from app.auth.security import hash_password
from app.auth.service import get_user_by_email
from app.auth.sessions import revoke_all_sessions
from app.core.config import FRONTEND_URL, PASSWORD_RESET_EXPIRE_MINUTES
from app.core.logger import logger
from app.database import adapt_query, get_connection
from app.services.email_service import send_email
from app.services.email_templates import password_reset_email


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_reset_token(user_id: str) -> str:
    """Жаңа token жасап, hash-ін сақтайды. Ашық token-ді қайтарады."""

    token = secrets.token_urlsafe(32)
    now = _now()
    expires_at = now + timedelta(minutes=PASSWORD_RESET_EXPIRE_MINUTES)

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            adapt_query(
                """
                INSERT INTO password_reset_tokens (
                    token_hash, user_id, expires_at, used_at, created_at
                )
                VALUES (?, ?, ?, NULL, ?)
                """
            ),
            (
                _hash_token(token),
                user_id,
                expires_at.isoformat(),
                now.isoformat(),
            ),
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    return token


def build_reset_link(token: str) -> str:
    return f"{FRONTEND_URL.rstrip('/')}/reset-password?token={token}"


def request_password_reset(email: str, language: str = "kk") -> None:
    """
    Email тіркелген болса — қалпына келтіру хатын жібереді.
    Тіркелмеген болса — ештеңе істемейді (жауап бірдей болуы үшін).
    """

    user = get_user_by_email(email)

    if not user or not user["is_active"]:
        logger.info("Password reset requested for unknown or inactive email")
        return

    token = create_reset_token(user["user_id"])
    link = build_reset_link(token)
    minutes = PASSWORD_RESET_EXPIRE_MINUTES

    subject, text, html_body = password_reset_email(
        username=user["username"] or "",
        link=link,
        minutes=minutes,
        language=language,
    )

    send_email(
        to=user["email"],
        subject=subject,
        text=text,
        html=html_body,
    )


def reset_password(token: str, new_password: str) -> bool:
    """
    Token жарамды болса құпиясөзді ауыстырады.
    Сәтті болса True, token жарамсыз/мерзімі өткен/қолданылған болса False.
    """

    token_hash = _hash_token(token)
    now = _now()

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            adapt_query(
                """
                SELECT user_id, expires_at, used_at
                FROM password_reset_tokens
                WHERE token_hash = ?
                """
            ),
            (token_hash,),
        )

        row = cursor.fetchone()

        if not row or row["used_at"]:
            return False

        if datetime.fromisoformat(row["expires_at"]) <= now:
            return False

        user_id = row["user_id"]

        cursor.execute(
            adapt_query(
                """
                UPDATE users
                SET password_hash = ?,
                    -- Хаттағы сілтеме email-дің иесі екенін дәлелдейді.
                    email_verified = CASE
                        WHEN email_verified = 0 THEN 1
                        ELSE email_verified
                    END
                WHERE user_id = ?
                """
            ),
            (hash_password(new_password), user_id),
        )

        # Осы және пайдаланушының басқа барлық token-дері жарамсыз болады.
        cursor.execute(
            adapt_query(
                """
                UPDATE password_reset_tokens
                SET used_at = ?
                WHERE user_id = ? AND used_at IS NULL
                """
            ),
            (now.isoformat(), user_id),
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    # Барлық құрылғылардан шығарамыз: ескі сессиялар енді жарамсыз.
    revoke_all_sessions(user_id)

    logger.info("Password reset completed | user_id=%s", user_id)
    return True
