"""
AI жауаптарына пайдаланушы бағасы (👍 / 👎).

Тек баға сақталады; хабарлама мәтіні көшірілмейді.
Әкімші панелі тек санын көреді, мазмұнын көрмейді.
"""

from datetime import datetime, timezone

from app.database import adapt_query, get_connection


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_own_assistant_message(user_id: str, message_id: int) -> bool:
    """Хабарлама осы пайдаланушыныкі және AI жауабы ма."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            adapt_query(
                """
                SELECT 1 FROM conversations
                WHERE id = ? AND user_id = ? AND role = 'assistant'
                """
            ),
            (message_id, user_id),
        )

        if cursor.fetchone():
            return True

        cursor.execute(
            adapt_query(
                """
                SELECT 1 FROM conversation_archive
                WHERE original_message_id = ? AND user_id = ?
                  AND role = 'assistant'
                """
            ),
            (message_id, user_id),
        )

        return cursor.fetchone() is not None

    finally:
        connection.close()


def set_feedback(
    user_id: str,
    message_id: int,
    rating: int,
    persona: str | None,
) -> None:
    """rating: 1, -1 немесе 0 (бағаны алып тастау)."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            adapt_query(
                "DELETE FROM message_feedback WHERE user_id = ? AND message_id = ?"
            ),
            (user_id, message_id),
        )

        if rating != 0:
            now = _now()
            cursor.execute(
                adapt_query(
                    """
                    INSERT INTO message_feedback
                        (user_id, message_id, rating, persona, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """
                ),
                (user_id, message_id, rating, persona, now, now),
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_feedback_map(user_id: str, message_ids: list[int]) -> dict[int, int]:
    """{message_id: rating} — тек баға қойылған хабарламалар."""

    if not message_ids:
        return {}

    connection = get_connection()

    try:
        cursor = connection.cursor()
        placeholders = ", ".join("?" for _ in message_ids)

        cursor.execute(
            adapt_query(
                f"""
                SELECT message_id, rating FROM message_feedback
                WHERE user_id = ? AND message_id IN ({placeholders})
                """
            ),
            (user_id, *message_ids),
        )

        return {
            int(row["message_id"]): int(row["rating"])
            for row in cursor.fetchall()
        }

    finally:
        connection.close()


def feedback_stats(since_iso: str) -> dict:
    """Әкімші панелі үшін: since_iso-дан бергі бағалар саны."""

    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute(
            adapt_query(
                """
                SELECT rating, persona FROM message_feedback
                WHERE updated_at >= ?
                """
            ),
            (since_iso,),
        )
        rows = cursor.fetchall()

    finally:
        connection.close()

    likes = sum(1 for row in rows if int(row["rating"]) > 0)
    dislikes = sum(1 for row in rows if int(row["rating"]) < 0)

    by_persona: dict[str, dict[str, int]] = {}
    for row in rows:
        key = row["persona"] or "brother"
        entry = by_persona.setdefault(key, {"likes": 0, "dislikes": 0})
        if int(row["rating"]) > 0:
            entry["likes"] += 1
        else:
            entry["dislikes"] += 1

    total = likes + dislikes

    return {
        "likes": likes,
        "dislikes": dislikes,
        "satisfaction": round(likes / total * 100) if total else None,
        "by_persona": by_persona,
    }
