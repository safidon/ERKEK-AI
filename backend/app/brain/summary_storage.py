from app.database import get_connection
from app.brain.memory import get_user_profile


def get_summary_state(user_id: str) -> dict:
    """
    Пайдаланушының summary күйін қайтарады.

    Нәтиже:
    {
        "summary": str | None,
        "last_message_id": int
    }
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                summary,
                last_message_id
            FROM conversation_summaries
            WHERE user_id = ?
            """,
            (user_id,)
        )

        row = cursor.fetchone()

        if row is None:
            return {
                "summary": None,
                "last_message_id": 0
            }

        return {
            "summary": row["summary"],
            "last_message_id": row["last_message_id"] or 0
        }

    finally:
        connection.close()


def get_summary(user_id: str) -> str | None:
    """
    Тек summary мәтінін қайтарады.
    """

    state = get_summary_state(user_id)

    return state["summary"]


def save_summary(
    user_id: str,
    summary: str,
    last_message_id: int
) -> None:
    """
    Summary және summary жасалған соңғы message ID-ні сақтайды.
    """

    # User users кестесінде бар екеніне кепілдік
    get_user_profile(user_id)

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO conversation_summaries (
                user_id,
                summary,
                last_message_id,
                updated_at
            )
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)

            ON CONFLICT(user_id) DO UPDATE SET
                summary = excluded.summary,
                last_message_id = excluded.last_message_id,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                user_id,
                summary,
                last_message_id
            )
        )

        connection.commit()

    finally:
        connection.close()

def delete_summary(user_id: str) -> None:
    """
    Пайдаланушы summary-сін өшіреді.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM conversation_summaries
            WHERE user_id = ?
            """,
            (user_id,)
        )

        connection.commit()

    finally:
        connection.close()