"""
Әкімші панелі.

Кіру: ADMIN_EMAILS (үтірмен бөлінген email тізімі) ішіндегі пайдаланушылар.
Мән әр сұраныста env-тен оқылады, сондықтан сервер .env-ін өзгертіп,
backend-ті қайта іске қосу жеткілікті.

Статистика шағын көлемге арналған (мыңдаған пайдаланушыға дейін):
есептер Python-да жасалады, SQLite пен PostgreSQL-да бірдей жұмыс істейді.
"""

import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.database import adapt_query, get_connection
from app.services.feedback import feedback_stats
from app.services.usage import (
    DAILY_SITE_TOKEN_BUDGET,
    SITE_SCOPE,
    TELEGRAM_SCOPE,
    USAGE_TZ,
)
from app.telegram.reminders import REMINDER_SCOPE


router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

CHART_DAYS = 14
RECENT_USERS = 20


# =====================================================
# ACCESS
# =====================================================

def _admin_emails() -> set[str]:
    raw = os.getenv("ADMIN_EMAILS", "")
    return {
        email.strip().lower()
        for email in raw.split(",")
        if email.strip()
    }


def is_admin(user) -> bool:
    email = (user["email"] or "").strip().lower()
    return bool(email) and email in _admin_emails()


def require_admin(current_user=Depends(get_current_user)):
    if not is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Бұл бетке кіруге рұқсат жоқ."
        )

    return current_user


@router.get("/me")
def admin_me(current_user=Depends(get_current_user)):
    """Frontend мәзірде «Әкімші панелі» сілтемесін көрсету үшін."""

    return {
        "is_admin": is_admin(current_user)
    }


# =====================================================
# HELPERS
# =====================================================

def _to_datetime(value) -> datetime | None:
    """SQLite мәтінін де, PostgreSQL datetime-ын да UTC datetime-ға келтіреді."""

    if value is None:
        return None

    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip().replace("T", " ")
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def _local_day(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.astimezone(USAGE_TZ).date().isoformat()


def _fetch_all(query: str, params: tuple = ()) -> list:
    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute(adapt_query(query), params)
        return cursor.fetchall()

    finally:
        connection.close()


def _token_cost_usd(input_tokens: int, output_tokens: int) -> float | None:
    """
    Шамамен шығын. OPENAI_PRICE_INPUT_PER_1M / OPENAI_PRICE_OUTPUT_PER_1M
    (USD, 1 млн токенге) .env-те берілсе ғана есептеледі.
    """

    try:
        price_in = float(os.getenv("OPENAI_PRICE_INPUT_PER_1M", ""))
        price_out = float(os.getenv("OPENAI_PRICE_OUTPUT_PER_1M", ""))
    except ValueError:
        return None

    return round(
        input_tokens / 1_000_000 * price_in
        + output_tokens / 1_000_000 * price_out,
        4,
    )


# =====================================================
# RETENTION (қайта оралу)
# =====================================================

COHORT_DAYS = 30


def _retention(user_rows: list, today) -> dict:
    """
    Соңғы 30 күнде тіркелгендер бойынша:
    - d1: ертеңіне қайта жазғандар (тіркелгеніне кемі 1 күн болғандар ішінен);
    - d7: 7 күннен кейін де жазғандар (кемі 7 күн болғандар ішінен);
    - returned: тіркелген күннен кейін кез келген күні оралғандар.
    Белсенділік = usage_daily ішінде хабарлама жазған күн (сайт + Telegram).
    """

    since = (today - timedelta(days=COHORT_DAYS + 14)).isoformat()
    rows = _fetch_all(
        "SELECT day, scope, messages FROM usage_daily WHERE day >= ? AND messages > 0",
        (since,),
    )

    active_days: dict[str, set] = {}
    for row in rows:
        if str(row["scope"]).startswith("__"):
            continue
        active_days.setdefault(row["scope"], set()).add(row["day"])

    cohort_start = today - timedelta(days=COHORT_DAYS)

    def rate(returned: int, eligible: int):
        return {
            "eligible": eligible,
            "returned": returned,
            "percent": round(returned / eligible * 100) if eligible else None,
        }

    d1 = [0, 0]
    d7 = [0, 0]
    any_return = [0, 0]

    for row, created, created_day in user_rows:
        if not created_day:
            continue

        signup = datetime.fromisoformat(created_day).date()
        if signup < cohort_start:
            continue

        days = active_days.get(row["user_id"], set())
        age = (today - signup).days

        if age >= 1:
            next_day = (signup + timedelta(days=1)).isoformat()
            d1[1] += 1
            d1[0] += next_day in days
            any_return[1] += 1
            any_return[0] += any(day > created_day for day in days)

        if age >= 7:
            week = (signup + timedelta(days=7)).isoformat()
            d7[1] += 1
            d7[0] += any(day >= week for day in days)

    return {
        "cohort_days": COHORT_DAYS,
        "d1": rate(*d1),
        "d7": rate(*d7),
        "returned": rate(*any_return),
    }


def _count_reminders_enabled() -> int:
    rows = _fetch_all(
        "SELECT COUNT(*) AS n FROM telegram_accounts WHERE reminder_hour IS NOT NULL"
    )
    return int(rows[0]["n"]) if rows else 0


# =====================================================
# STATS
# =====================================================

@router.get("/stats")
def admin_stats(_admin=Depends(require_admin)):

    today = datetime.now(USAGE_TZ).date()
    days = [
        (today - timedelta(days=offset)).isoformat()
        for offset in range(CHART_DAYS - 1, -1, -1)
    ]
    since_30 = (today - timedelta(days=29)).isoformat()
    since_7 = (today - timedelta(days=6)).isoformat()

    # ---------- users ----------
    users = _fetch_all(
        "SELECT user_id, email, username, is_active, created_at FROM users"
    )

    user_rows = []
    new_by_day: dict[str, int] = {}

    for row in users:
        created = _to_datetime(row["created_at"])
        created_day = _local_day(created)
        if created_day:
            new_by_day[created_day] = new_by_day.get(created_day, 0) + 1
        user_rows.append((row, created, created_day))

    total_users = len(user_rows)
    new_today = new_by_day.get(today.isoformat(), 0)
    new_7 = sum(n for d, n in new_by_day.items() if d >= since_7)
    new_30 = sum(n for d, n in new_by_day.items() if d >= since_30)

    # ---------- usage ----------
    usage = _fetch_all(
        """
        SELECT day, scope, messages, input_tokens, output_tokens
        FROM usage_daily
        WHERE day >= ?
        """,
        (since_30,),
    )

    messages_by_day: dict[str, int] = {}
    telegram_by_day: dict[str, int] = {}
    reminders_by_day: dict[str, int] = {}
    active_by_day: dict[str, int] = {}
    tokens_by_day: dict[str, dict] = {}
    messages_by_user_30: dict[str, int] = {}
    last_active: dict[str, str] = {}
    active_users_7: set[str] = set()
    active_users_30: set[str] = set()

    for row in usage:
        day = row["day"]

        if row["scope"] == TELEGRAM_SCOPE:
            telegram_by_day[day] = int(row["messages"] or 0)
            continue

        if row["scope"] == REMINDER_SCOPE:
            reminders_by_day[day] = int(row["messages"] or 0)
            continue

        if row["scope"] == SITE_SCOPE:
            tokens_by_day[day] = {
                "input": int(row["input_tokens"] or 0),
                "output": int(row["output_tokens"] or 0),
            }
            continue

        count = int(row["messages"] or 0)
        if count <= 0:
            continue

        user_id = row["scope"]
        messages_by_day[day] = messages_by_day.get(day, 0) + count
        active_by_day[day] = active_by_day.get(day, 0) + 1
        messages_by_user_30[user_id] = messages_by_user_30.get(user_id, 0) + count
        active_users_30.add(user_id)
        if day >= since_7:
            active_users_7.add(user_id)
        if day > last_active.get(user_id, ""):
            last_active[user_id] = day

    def tokens_sum(predicate) -> dict:
        inp = sum(v["input"] for d, v in tokens_by_day.items() if predicate(d))
        out = sum(v["output"] for d, v in tokens_by_day.items() if predicate(d))
        return {
            "input": inp,
            "output": out,
            "total": inp + out,
            "cost_usd": _token_cost_usd(inp, out),
        }

    tokens_today = tokens_sum(lambda d: d == today.isoformat())
    tokens_30 = tokens_sum(lambda d: d >= since_30)

    # ---------- telegram ----------
    telegram_rows = _fetch_all(
        """
        SELECT u.email
        FROM telegram_accounts t
        JOIN users u ON u.user_id = t.user_id
        """
    )
    telegram_users = len(telegram_rows)
    telegram_linked = sum(1 for row in telegram_rows if (row["email"] or "").strip())

    # ---------- recent users ----------
    recent = sorted(
        user_rows,
        key=lambda item: item[1] or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )[:RECENT_USERS]

    recent_users = [
        {
            "username": row["username"],
            "email": row["email"],
            "is_active": bool(row["is_active"]),
            "created_at": created.isoformat() if created else None,
            "messages_30d": messages_by_user_30.get(row["user_id"], 0),
            "last_active": last_active.get(row["user_id"]),
        }
        for row, created, _ in recent
    ]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "today": today.isoformat(),
        "users": {
            "total": total_users,
            "new_today": new_today,
            "new_7d": new_7,
            "new_30d": new_30,
            "active_today": active_by_day.get(today.isoformat(), 0),
            "active_7d": len(active_users_7),
            "active_30d": len(active_users_30),
        },
        "messages": {
            "today": messages_by_day.get(today.isoformat(), 0),
            "last_7d": sum(n for d, n in messages_by_day.items() if d >= since_7),
            "last_30d": sum(messages_by_day.values()),
        },
        "tokens": {
            "today": tokens_today,
            "last_30d": tokens_30,
            "daily_budget": DAILY_SITE_TOKEN_BUDGET,
        },
        "daily": [
            {
                "day": day,
                "messages": messages_by_day.get(day, 0),
                "active_users": active_by_day.get(day, 0),
                "new_users": new_by_day.get(day, 0),
                "telegram_messages": telegram_by_day.get(day, 0),
                "tokens": (
                    tokens_by_day.get(day, {}).get("input", 0)
                    + tokens_by_day.get(day, {}).get("output", 0)
                ),
            }
            for day in days
        ],
        "retention": _retention(user_rows, today),
        "reminders": {
            "enabled": _count_reminders_enabled(),
            "sent_today": reminders_by_day.get(today.isoformat(), 0),
            "sent_7d": sum(n for d, n in reminders_by_day.items() if d >= since_7),
        },
        "telegram": {
            "users": telegram_users,
            "linked_to_site": telegram_linked,
            "messages_today": telegram_by_day.get(today.isoformat(), 0),
            "messages_7d": sum(n for d, n in telegram_by_day.items() if d >= since_7),
            "messages_30d": sum(telegram_by_day.values()),
        },
        "feedback": {
            "last_30d": feedback_stats(
                (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
            ),
        },
        "recent_users": recent_users,
    }
