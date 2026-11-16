"""
OpenAI шығынын бақылау.

- Әр пайдаланушыға күніне DAILY_MESSAGES_PER_USER хабарлама
  (чат, stream, қайта жауап — барлығы есептеледі).
- Бүкіл сайтқа күніне DAILY_SITE_TOKEN_BUDGET токен
  (OpenAI-дың барлық шақыруы: жауаптар да, summary да).
  0 — шектеусіз.
- Күн USAGE_TZ_OFFSET_HOURS уақыт белдеуі бойынша ауысады
  (әдепкі +5, Қазақстан).

Санауыштар usage_daily кестесінде: scope = user_id немесе "__site__".
"""

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.core.logger import logger
from app.database import adapt_query, get_connection


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


DAILY_MESSAGES_PER_USER = _env_int("DAILY_MESSAGES_PER_USER", 50)
DAILY_SITE_TOKEN_BUDGET = _env_int("DAILY_SITE_TOKEN_BUDGET", 2_000_000)
USAGE_TZ = timezone(timedelta(hours=_env_int("USAGE_TZ_OFFSET_HOURS", 5)))

SITE_SCOPE = "__site__"
# Telegram бот арқылы келген хабарламалар (әкімші панеліндегі бөлініс үшін).
TELEGRAM_SCOPE = "__telegram__"


def _today() -> str:
    return datetime.now(USAGE_TZ).date().isoformat()


def next_reset_at() -> datetime:
    """Келесі күннің басы (лимиттер қайта ашылатын уақыт)."""

    now = datetime.now(USAGE_TZ)
    tomorrow = (now + timedelta(days=1)).date()
    return datetime(
        tomorrow.year, tomorrow.month, tomorrow.day, tzinfo=USAGE_TZ
    )


def record_telegram_message() -> None:
    _add(TELEGRAM_SCOPE, messages=1)


def _add(scope: str, messages: int = 0, input_tokens: int = 0,
         output_tokens: int = 0) -> None:
    connection = get_connection()

    try:
        connection.cursor().execute(
            adapt_query(
                """
                INSERT INTO usage_daily (
                    day, scope, messages, input_tokens, output_tokens
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (day, scope) DO UPDATE SET
                    messages = usage_daily.messages + excluded.messages,
                    input_tokens = usage_daily.input_tokens + excluded.input_tokens,
                    output_tokens = usage_daily.output_tokens + excluded.output_tokens
                """
            ),
            (_today(), scope, messages, input_tokens, output_tokens),
        )
        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def _get(scope: str) -> dict:
    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute(
            adapt_query(
                """
                SELECT messages, input_tokens, output_tokens
                FROM usage_daily
                WHERE day = ? AND scope = ?
                """
            ),
            (_today(), scope),
        )
        row = cursor.fetchone()

    finally:
        connection.close()

    if not row:
        return {"messages": 0, "input_tokens": 0, "output_tokens": 0}

    return {
        "messages": row["messages"],
        "input_tokens": row["input_tokens"],
        "output_tokens": row["output_tokens"],
    }


def record_tokens(input_tokens: int, output_tokens: int) -> None:
    """OpenAI шақыруынан кейін сайттың жалпы токен санауышына қосады."""

    try:
        _add(
            SITE_SCOPE,
            input_tokens=max(int(input_tokens or 0), 0),
            output_tokens=max(int(output_tokens or 0), 0),
        )
    except Exception:
        # Санау қатесі пайдаланушының жауабын бұзбауы керек.
        logger.exception("Failed to record OpenAI token usage")


def record_usage_from(response) -> None:
    """OpenAI Responses API жауабынан usage-ді оқып, тіркейді."""

    usage = getattr(response, "usage", None)

    if usage is None:
        return

    record_tokens(
        getattr(usage, "input_tokens", 0),
        getattr(usage, "output_tokens", 0),
    )


@dataclass
class UserUsage:
    used: int
    limit: int

    @property
    def remaining(self) -> int:
        return max(self.limit - self.used, 0)


def get_user_usage(user_id: str) -> UserUsage:
    return UserUsage(
        used=_get(user_id)["messages"],
        limit=DAILY_MESSAGES_PER_USER,
    )


def site_tokens_used_today() -> int:
    site = _get(SITE_SCOPE)
    return site["input_tokens"] + site["output_tokens"]


def enforce_chat_quota(current_user=Depends(get_current_user)) -> None:
    """
    Чат endpoint-тері үшін dependency.
    Лимит асса — 429, әйтпесе хабарламаны санап жібереді.
    """

    user_id = current_user["user_id"]

    if (
        DAILY_SITE_TOKEN_BUDGET > 0
        and site_tokens_used_today() >= DAILY_SITE_TOKEN_BUDGET
    ):
        logger.error("Daily site token budget reached")

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "ERKEK AI бүгін тым көп сұраныс алды. "
                "Ертең қайта келіп жаз — кешірім сұраймыз."
            ),
        )

    usage = get_user_usage(user_id)

    if usage.remaining <= 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Бүгінгі {usage.limit} хабарлама лимиті бітті. "
                "Ертең қайта жалғастырамыз."
            ),
        )

    _add(user_id, messages=1)
