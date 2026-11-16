"""
Telegram аккаунттары.

Екі жол:
1. Ботқа бірден жазу: шарттарға келіскеннен кейін email/құпиясөзсіз
   жеке ERKEK AI аккаунты ашылады.
2. Сайт аккаунтын байланыстыру: сайттағы Баптауларда бір реттік сілтеме
   жасалады (t.me/<bot>?start=link_<code>). Telegram-да бұрын ашылған
   жеке аккаунт болса, оның әңгімелері сайт аккаунтына көшіріледі,
   ал Telegram аккаунтының өзі жойылады.
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from app.auth.account import delete_account
from app.auth.consents import record_consents
from app.core.logger import logger
from app.database import adapt_query, get_connection


LINK_CODE_MINUTES = 15


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _fetch_one(query: str, params: tuple):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(adapt_query(query), params)
        return cursor.fetchone()
    finally:
        connection.close()


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


# =====================================================
# READ
# =====================================================

def get_by_telegram_id(telegram_user_id: int | str):
    return _fetch_one(
        "SELECT * FROM telegram_accounts WHERE telegram_user_id = ?",
        (str(telegram_user_id),),
    )


def get_by_user_id(user_id: str):
    return _fetch_one(
        "SELECT * FROM telegram_accounts WHERE user_id = ?",
        (user_id,),
    )


def is_telegram_only(user) -> bool:
    """Аккаунт тек Telegram арқылы ашылған ба (email жоқ)."""
    return not (user["email"] or "").strip()


# =====================================================
# CREATE (ботқа бірден жазғандар)
# =====================================================

def create_telegram_user(
    telegram_user_id: int | str,
    chat_id: int | str,
    lang: str,
) -> str:
    """Шарттарға келіскен Telegram пайдаланушысына аккаунт ашады."""

    existing = get_by_telegram_id(telegram_user_id)
    if existing:
        return existing["user_id"]

    user_id = str(uuid.uuid4())

    _execute([
        (
            """
            INSERT INTO users (user_id, email, username, password_hash, is_active)
            VALUES (?, NULL, ?, NULL, 1)
            """,
            (user_id, f"tg{telegram_user_id}"),
        ),
        (
            """
            INSERT INTO telegram_accounts
                (telegram_user_id, user_id, chat_id, lang, active_session_id, created_at)
            VALUES (?, ?, ?, ?, NULL, ?)
            """,
            (str(telegram_user_id), user_id, str(chat_id), lang, _now().isoformat()),
        ),
    ])

    record_consents(user_id)

    logger.info("Telegram user created | user_id=%s", user_id)

    return user_id


def set_active_session(telegram_user_id: int | str, session_id: int | None) -> None:
    _execute([(
        "UPDATE telegram_accounts SET active_session_id = ? WHERE telegram_user_id = ?",
        (session_id, str(telegram_user_id)),
    )])


def set_lang(telegram_user_id: int | str, lang: str) -> None:
    _execute([(
        "UPDATE telegram_accounts SET lang = ? WHERE telegram_user_id = ?",
        (lang, str(telegram_user_id)),
    )])


# =====================================================
# LINK CODES (сайт -> Telegram)
# =====================================================

def create_link_code(user_id: str) -> str:
    code = secrets.token_urlsafe(24)
    now = _now()

    _execute([
        # Ескі қолданылмаған кодтар жарамсыз болады.
        ("DELETE FROM telegram_link_codes WHERE user_id = ?", (user_id,)),
        (
            """
            INSERT INTO telegram_link_codes (code_hash, user_id, expires_at, used_at, created_at)
            VALUES (?, ?, ?, NULL, ?)
            """,
            (
                _hash(code),
                user_id,
                (now + timedelta(minutes=LINK_CODE_MINUTES)).isoformat(),
                now.isoformat(),
            ),
        ),
    ])

    return code


def consume_link_code(code: str) -> str | None:
    """Код жарамды болса — сайт пайдаланушысының user_id-ін қайтарады."""

    row = _fetch_one(
        "SELECT * FROM telegram_link_codes WHERE code_hash = ?",
        (_hash(code),),
    )

    if not row or row["used_at"]:
        return None

    if datetime.fromisoformat(row["expires_at"]) < _now():
        return None

    _execute([(
        "UPDATE telegram_link_codes SET used_at = ? WHERE code_hash = ?",
        (_now().isoformat(), _hash(code)),
    )])

    return row["user_id"]


# =====================================================
# LINK / UNLINK
# =====================================================

# Telegram-дағы жеке аккаунттан сайт аккаунтына көшірілетін деректер.
_MOVE_TABLES = (
    "conversation_sessions",
    "conversations",
    "conversation_summaries",
    "conversation_archive",
    "message_feedback",
)


def link_to_site_account(
    telegram_user_id: int | str,
    chat_id: int | str,
    lang: str,
    site_user_id: str,
) -> bool:
    """
    Telegram-ды сайт аккаунтына байланыстырады.
    Telegram-да бұрын жеке аккаунт болса, әңгімелерін көшіріп, өзін жояды.
    Қайтарады: әңгімелер көшірілді ме.
    """

    tg_id = str(telegram_user_id)
    current = get_by_telegram_id(tg_id)

    # Сайт аккаунты басқа Telegram-ға байланған болса — ажыратамыз.
    queries: list[tuple[str, tuple]] = [
        ("DELETE FROM telegram_accounts WHERE user_id = ? AND telegram_user_id <> ?",
         (site_user_id, tg_id)),
    ]

    moved = False
    old_user_id = None

    if current and current["user_id"] != site_user_id:
        old_user = _fetch_one(
            "SELECT email FROM users WHERE user_id = ?",
            (current["user_id"],),
        )

        # Деректер тек Telegram-да ашылған (email-сіз) аккаунттан көшеді.
        # Басқа сайт аккаунтына байланған болса — тек байланыс ауысады.
        if old_user is not None and not (old_user["email"] or "").strip():
            old_user_id = current["user_id"]
            moved = True

            for table in _MOVE_TABLES:
                queries.append((
                    f"UPDATE {table} SET user_id = ? WHERE user_id = ?",
                    (site_user_id, old_user_id),
                ))

        queries.append((
            "DELETE FROM telegram_accounts WHERE telegram_user_id = ?",
            (tg_id,),
        ))

    elif current:
        # Бұрыннан осы аккаунтқа байланған.
        return False

    queries.append((
        """
        INSERT INTO telegram_accounts
            (telegram_user_id, user_id, chat_id, lang, active_session_id, created_at)
        VALUES (?, ?, ?, ?, NULL, ?)
        """,
        (tg_id, site_user_id, str(chat_id), lang, _now().isoformat()),
    ))

    _execute(queries)

    # Бұрынғы Telegram аккаунтының қалған деректерін (профиль, лимит
    # санауыштары, келісімдер) толық жоямыз.
    if old_user_id:
        delete_account(old_user_id)

    logger.info("Telegram linked to site account | user_id=%s", site_user_id)

    return moved


def unlink_user(user_id: str) -> bool:
    """Сайт аккаунтынан Telegram байланысын алып тастайды."""

    if not get_by_user_id(user_id):
        return False

    _execute([("DELETE FROM telegram_accounts WHERE user_id = ?", (user_id,))])
    return True
