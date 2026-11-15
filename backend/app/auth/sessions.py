"""
Кіру сессиялары және refresh token.

- Әр кіру (құрылғы/браузер) — auth_sessions кестесіндегі бір жол.
- Access token қысқа (ACCESS_TOKEN_EXPIRE_MINUTES), ішінде session id (sid) бар.
- Refresh token ұзақ: соңғы қолданылғаннан бастап REFRESH_TOKEN_EXPIRE_DAYS
  жарамды (адам сайтқа кіріп жүрсе — сессия ұзара береді).
- Әр жаңартуда refresh token ауысады (rotation). Ескі token біраз уақыттан
  кейін қайта ұсынылса — ол ұрланған деп саналып, сессия жабылады.
- Logout немесе құпиясөз ауысқанда сессиялар бірден жабылады: access token
  әр сұраныста сессияның белсенді екенін тексереді.
"""

import hashlib
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from app.core.logger import logger
from app.database import adapt_query, get_connection


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


REFRESH_TOKEN_EXPIRE_DAYS = _env_int("REFRESH_TOKEN_EXPIRE_DAYS", 30)

# Бір браузердің бірнеше қойындысы бір мезетте жаңартса,
# ескі token осы уақыт ішінде "ұрлық" деп саналмайды.
ROTATION_GRACE_SECONDS = 60


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _new_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def create_session(user_id: str) -> tuple[str, str]:
    """Жаңа сессия ашады. (session_id, refresh_token) қайтарады."""

    session_id = str(uuid.uuid4())
    refresh_token = _new_refresh_token()
    now = _now()
    expires_at = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    connection = get_connection()

    try:
        connection.cursor().execute(
            adapt_query(
                """
                INSERT INTO auth_sessions (
                    session_id, user_id, refresh_hash, previous_hash,
                    rotated_at, created_at, last_used_at, expires_at,
                    revoked_at
                )
                VALUES (?, ?, ?, NULL, NULL, ?, ?, ?, NULL)
                """
            ),
            (
                session_id,
                user_id,
                _hash(refresh_token),
                now.isoformat(),
                now.isoformat(),
                expires_at.isoformat(),
            ),
        )
        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    return session_id, refresh_token


def rotate_refresh_token(
    refresh_token: str,
) -> tuple[str, str, str] | None:
    """
    Refresh token-ді тексеріп, жаңасын береді.
    Сәтті болса (user_id, session_id, new_refresh_token), әйтпесе None.
    """

    token_hash = _hash(refresh_token)
    now = _now()

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            adapt_query(
                """
                SELECT session_id, user_id, expires_at, revoked_at
                FROM auth_sessions
                WHERE refresh_hash = ?
                """
            ),
            (token_hash,),
        )

        row = cursor.fetchone()

        if row is None:
            _handle_unknown_token(cursor, token_hash, now)
            connection.commit()
            return None

        if row["revoked_at"]:
            return None

        if datetime.fromisoformat(row["expires_at"]) <= now:
            return None

        new_token = _new_refresh_token()
        new_expires = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        cursor.execute(
            adapt_query(
                """
                UPDATE auth_sessions
                SET refresh_hash = ?,
                    previous_hash = ?,
                    rotated_at = ?,
                    last_used_at = ?,
                    expires_at = ?
                WHERE session_id = ? AND refresh_hash = ?
                """
            ),
            (
                _hash(new_token),
                token_hash,
                now.isoformat(),
                now.isoformat(),
                new_expires.isoformat(),
                row["session_id"],
                token_hash,
            ),
        )

        # Басқа сұраныс осы token-ді бізден бұрын ауыстырып үлгерген.
        if cursor.rowcount != 1:
            connection.rollback()
            return None

        connection.commit()

        return row["user_id"], row["session_id"], new_token

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def _handle_unknown_token(cursor, token_hash: str, now: datetime) -> None:
    """
    Token ағымдағы емес. Егер ол бұрын ауыстырылған token болса және
    grace уақыты өтіп кетсе — ұрлық белгісі: сессияны жабамыз.
    """

    cursor.execute(
        adapt_query(
            """
            SELECT session_id, rotated_at, revoked_at
            FROM auth_sessions
            WHERE previous_hash = ?
            """
        ),
        (token_hash,),
    )

    row = cursor.fetchone()

    if row is None or row["revoked_at"] or not row["rotated_at"]:
        return

    rotated_at = datetime.fromisoformat(row["rotated_at"])

    if now - rotated_at <= timedelta(seconds=ROTATION_GRACE_SECONDS):
        return

    cursor.execute(
        adapt_query(
            "UPDATE auth_sessions SET revoked_at = ? WHERE session_id = ?"
        ),
        (now.isoformat(), row["session_id"]),
    )

    logger.warning(
        "Refresh token reuse detected, session revoked | session_id=%s",
        row["session_id"],
    )


def is_session_active(session_id: str, user_id: str) -> bool:
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            adapt_query(
                """
                SELECT expires_at, revoked_at
                FROM auth_sessions
                WHERE session_id = ? AND user_id = ?
                """
            ),
            (session_id, user_id),
        )

        row = cursor.fetchone()

    finally:
        connection.close()

    if row is None or row["revoked_at"]:
        return False

    return datetime.fromisoformat(row["expires_at"]) > _now()


def revoke_session_by_refresh_token(refresh_token: str) -> None:
    """Logout: осы refresh token-нің сессиясын жабады."""

    _revoke(
        "UPDATE auth_sessions SET revoked_at = ? "
        "WHERE refresh_hash = ? AND revoked_at IS NULL",
        _hash(refresh_token),
    )


def revoke_session(session_id: str) -> None:
    _revoke(
        "UPDATE auth_sessions SET revoked_at = ? "
        "WHERE session_id = ? AND revoked_at IS NULL",
        session_id,
    )


def revoke_all_sessions(user_id: str) -> None:
    """Құпиясөз ауысқанда: пайдаланушының барлық құрылғыларынан шығару."""

    _revoke(
        "UPDATE auth_sessions SET revoked_at = ? "
        "WHERE user_id = ? AND revoked_at IS NULL",
        user_id,
    )


def _revoke(query: str, value: str) -> None:
    connection = get_connection()

    try:
        connection.cursor().execute(
            adapt_query(query),
            (_now().isoformat(), value),
        )
        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
