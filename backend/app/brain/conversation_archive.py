from app.database import get_connection
from app.brain.summary_storage import get_summary_state


ARCHIVE_KEEP_RECENT = 6


def archive_summarized_messages(
    user_id: str
) -> dict:
    """
    Summary-ге кірген ескі conversation хабарламаларын
    conversation_archive кестесіне көшіреді.

    Қауіпсіздік үшін соңғы бірнеше active message сақталады.
    """

    state = get_summary_state(user_id)

    last_message_id = state["last_message_id"]

    if last_message_id <= 0:
        return {
            "archived": 0,
            "deleted": 0,
            "reason": "summary әлі жоқ"
        }

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # =================================================
        # 1. Соңғы active message ID-лерін анықтау
        # =================================================

        cursor.execute(
            """
            SELECT id
            FROM conversations
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (
                user_id,
                ARCHIVE_KEEP_RECENT
            )
        )

        recent_rows = cursor.fetchall()

        recent_ids = [
            row["id"]
            for row in recent_rows
        ]

        # =================================================
        # 2. Archive жасауға болатын message-тер
        # =================================================

        if recent_ids:

            placeholders = ",".join(
                "?"
                for _ in recent_ids
            )

            query = f"""
                SELECT
                    id,
                    user_id,
                    role,
                    message,
                    created_at
                FROM conversations
                WHERE user_id = ?
                  AND id <= ?
                  AND id NOT IN ({placeholders})
                ORDER BY id ASC
            """

            params = [
                user_id,
                last_message_id,
                *recent_ids
            ]

            cursor.execute(
                query,
                params
            )

        else:

            cursor.execute(
                """
                SELECT
                    id,
                    user_id,
                    role,
                    message,
                    created_at
                FROM conversations
                WHERE user_id = ?
                  AND id <= ?
                ORDER BY id ASC
                """,
                (
                    user_id,
                    last_message_id
                )
            )

        rows = cursor.fetchall()

        if not rows:
            return {
                "archived": 0,
                "deleted": 0,
                "reason": "archive жасайтын message жоқ"
            }

        # =================================================
        # 3. Archive table-ға көшіру
        # =================================================

        archived_count = 0

        for row in rows:

            cursor.execute(
                """
                INSERT OR IGNORE INTO conversation_archive (
                    original_message_id,
                    user_id,
                    role,
                    message,
                    original_created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    row["id"],
                    row["user_id"],
                    row["role"],
                    row["message"],
                    row["created_at"]
                )
            )

            if cursor.rowcount > 0:
                archived_count += 1

        # =================================================
        # 4. Archive бар екенін тексеру
        # =================================================

        ids_to_delete = [
            row["id"]
            for row in rows
        ]

        placeholders = ",".join(
            "?"
            for _ in ids_to_delete
        )

        cursor.execute(
            f"""
            SELECT COUNT(*) AS total
            FROM conversation_archive
            WHERE original_message_id IN ({placeholders})
            """,
            ids_to_delete
        )

        archive_check = cursor.fetchone()

        archived_total = (
            archive_check["total"]
            if archive_check
            else 0
        )

        # Бір message те жоғалмауы керек
        if archived_total != len(ids_to_delete):

            connection.rollback()

            return {
                "archived": 0,
                "deleted": 0,
                "reason": "archive verification failed"
            }

        # =================================================
        # 5. Active conversations-тан өшіру
        # =================================================

        cursor.execute(
            f"""
            DELETE FROM conversations
            WHERE id IN ({placeholders})
            """,
            ids_to_delete
        )

        deleted_count = cursor.rowcount

        connection.commit()

        return {
            "archived": archived_count,
            "deleted": deleted_count,
            "reason": "success"
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_archive_count(
    user_id: str
) -> int:
    """
    User archive-індегі message санын қайтарады.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM conversation_archive
            WHERE user_id = ?
            """,
            (user_id,)
        )

        row = cursor.fetchone()

        if row is None:
            return 0

        return int(row["total"] or 0)

    finally:
        connection.close()


def get_archived_messages(
    user_id: str,
    limit: int = 20
) -> list[dict]:
    """
    Archive-тегі соңғы message-терді алады.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                original_message_id,
                role,
                message,
                original_created_at,
                archived_at
            FROM conversation_archive
            WHERE user_id = ?
            ORDER BY original_message_id DESC
            LIMIT ?
            """,
            (
                user_id,
                limit
            )
        )

        rows = cursor.fetchall()

        rows = list(reversed(rows))

        return [
            {
                "id": row["original_message_id"],
                "role": row["role"],
                "content": row["message"],
                "created_at": row["original_created_at"],
                "archived_at": row["archived_at"]
            }
            for row in rows
        ]

    finally:
        connection.close()