from app.database import (
    get_connection,
    adapt_query,
)

from app.brain.summary_storage import (
    get_summary_state,
)


ARCHIVE_KEEP_RECENT = 6


# =====================================================
# ARCHIVE SUMMARIZED MESSAGES
# =====================================================

def archive_summarized_messages(
    user_id: str,
    session_id: int | None = None
) -> dict:
    """
    Summary-ге кірген ескі conversation хабарламаларын
    conversation_archive кестесіне көшіреді.

    session_id берілсе:
    - тек сол conversation session архивтеледі.

    session_id берілмесе:
    - legacy user-level режим жұмыс істейді.

    SQLite және PostgreSQL compatible.
    """

    state = get_summary_state(
        user_id=user_id,
        session_id=session_id,
    )

    last_message_id = state[
        "last_message_id"
    ]

    if last_message_id <= 0:
        return {
            "archived": 0,
            "deleted": 0,
            "reason": "summary әлі жоқ",
        }

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # =================================================
        # 1. СОҢҒЫ ACTIVE MESSAGE ID-ЛЕР
        # =================================================

        if session_id is not None:

            cursor.execute(
                adapt_query(
                    """
                    SELECT id
                    FROM conversations
                    WHERE user_id = ?
                      AND session_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                    """
                ),
                (
                    user_id,
                    session_id,
                    ARCHIVE_KEEP_RECENT,
                ),
            )

        else:

            cursor.execute(
                adapt_query(
                    """
                    SELECT id
                    FROM conversations
                    WHERE user_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                    """
                ),
                (
                    user_id,
                    ARCHIVE_KEEP_RECENT,
                ),
            )

        recent_rows = (
            cursor.fetchall()
        )

        recent_ids = [
            row["id"]
            for row in recent_rows
        ]

        # =================================================
        # 2. ARCHIVE ЖАСАЙТЫН MESSAGE-ТЕР
        # =================================================

        if recent_ids:

            placeholders = ",".join(
                "?"
                for _ in recent_ids
            )

            if session_id is not None:

                query = adapt_query(
                    f"""
                    SELECT
                        id,
                        user_id,
                        session_id,
                        role,
                        message,
                        created_at
                    FROM conversations
                    WHERE user_id = ?
                      AND session_id = ?
                      AND id <= ?
                      AND id NOT IN ({placeholders})
                    ORDER BY id ASC
                    """
                )

                params = [
                    user_id,
                    session_id,
                    last_message_id,
                    *recent_ids,
                ]

            else:

                query = adapt_query(
                    f"""
                    SELECT
                        id,
                        user_id,
                        session_id,
                        role,
                        message,
                        created_at
                    FROM conversations
                    WHERE user_id = ?
                      AND id <= ?
                      AND id NOT IN ({placeholders})
                    ORDER BY id ASC
                    """
                )

                params = [
                    user_id,
                    last_message_id,
                    *recent_ids,
                ]

            cursor.execute(
                query,
                params,
            )

        else:

            if session_id is not None:

                cursor.execute(
                    adapt_query(
                        """
                        SELECT
                            id,
                            user_id,
                            session_id,
                            role,
                            message,
                            created_at
                        FROM conversations
                        WHERE user_id = ?
                          AND session_id = ?
                          AND id <= ?
                        ORDER BY id ASC
                        """
                    ),
                    (
                        user_id,
                        session_id,
                        last_message_id,
                    ),
                )

            else:

                cursor.execute(
                    adapt_query(
                        """
                        SELECT
                            id,
                            user_id,
                            session_id,
                            role,
                            message,
                            created_at
                        FROM conversations
                        WHERE user_id = ?
                          AND id <= ?
                        ORDER BY id ASC
                        """
                    ),
                    (
                        user_id,
                        last_message_id,
                    ),
                )

        rows = cursor.fetchall()

        if not rows:
            return {
                "archived": 0,
                "deleted": 0,
                "reason": (
                    "archive жасайтын "
                    "message жоқ"
                ),
            }

        # =================================================
        # 3. ARCHIVE TABLE-ҒА КӨШІРУ
        # =================================================

        archived_count = 0

        for row in rows:

            cursor.execute(
                adapt_query(
                    """
                    INSERT INTO conversation_archive (
                        original_message_id,
                        user_id,
                        session_id,
                        role,
                        message,
                        original_created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)

                    ON CONFLICT(original_message_id)
                    DO NOTHING
                    """
                ),
                (
                    row["id"],
                    row["user_id"],
                    row["session_id"],
                    row["role"],
                    row["message"],
                    row["created_at"],
                ),
            )

            if cursor.rowcount > 0:
                archived_count += 1

        # =================================================
        # 4. ARCHIVE VERIFICATION
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
            adapt_query(
                f"""
                SELECT COUNT(*) AS total
                FROM conversation_archive
                WHERE original_message_id
                    IN ({placeholders})
                """
            ),
            ids_to_delete,
        )

        archive_check = (
            cursor.fetchone()
        )

        archived_total = (
            int(
                archive_check["total"]
                or 0
            )
            if archive_check
            else 0
        )

        if (
            archived_total
            != len(ids_to_delete)
        ):
            connection.rollback()

            return {
                "archived": 0,
                "deleted": 0,
                "reason": (
                    "archive verification "
                    "failed"
                ),
            }

        # =================================================
        # 5. ACTIVE CONVERSATIONS-ТАН ӨШІРУ
        # =================================================

        cursor.execute(
            adapt_query(
                f"""
                DELETE FROM conversations
                WHERE id IN ({placeholders})
                """
            ),
            ids_to_delete,
        )

        deleted_count = (
            cursor.rowcount
        )

        connection.commit()

        return {
            "archived": archived_count,
            "deleted": deleted_count,
            "reason": "success",
        }

    except Exception:

        connection.rollback()
        raise

    finally:
        connection.close()


# =====================================================
# GET ARCHIVE COUNT
# =====================================================

def get_archive_count(
    user_id: str,
    session_id: int | None = None
) -> int:
    """
    Archive-тегі message санын қайтарады.

    SQLite және PostgreSQL compatible.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        if session_id is not None:

            cursor.execute(
                adapt_query(
                    """
                    SELECT COUNT(*) AS total
                    FROM conversation_archive
                    WHERE user_id = ?
                      AND session_id = ?
                    """
                ),
                (
                    user_id,
                    session_id,
                ),
            )

        else:

            cursor.execute(
                adapt_query(
                    """
                    SELECT COUNT(*) AS total
                    FROM conversation_archive
                    WHERE user_id = ?
                    """
                ),
                (
                    user_id,
                ),
            )

        row = cursor.fetchone()

        if row is None:
            return 0

        return int(
            row["total"] or 0
        )

    finally:
        connection.close()


# =====================================================
# GET ARCHIVED MESSAGES
# =====================================================

def get_archived_messages(
    user_id: str,
    limit: int = 20,
    session_id: int | None = None
) -> list[dict]:
    """
    Archive-тегі соңғы message-терді алады.

    SQLite және PostgreSQL compatible.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        if session_id is not None:

            cursor.execute(
                adapt_query(
                    """
                    SELECT
                        original_message_id,
                        session_id,
                        role,
                        message,
                        original_created_at,
                        archived_at
                    FROM conversation_archive
                    WHERE user_id = ?
                      AND session_id = ?
                    ORDER BY original_message_id DESC
                    LIMIT ?
                    """
                ),
                (
                    user_id,
                    session_id,
                    limit,
                ),
            )

        else:

            cursor.execute(
                adapt_query(
                    """
                    SELECT
                        original_message_id,
                        session_id,
                        role,
                        message,
                        original_created_at,
                        archived_at
                    FROM conversation_archive
                    WHERE user_id = ?
                    ORDER BY original_message_id DESC
                    LIMIT ?
                    """
                ),
                (
                    user_id,
                    limit,
                ),
            )

        rows = list(
            reversed(
                cursor.fetchall()
            )
        )

        return [
            {
                "id":
                    row[
                        "original_message_id"
                    ],

                "session_id":
                    row["session_id"],

                "role":
                    row["role"],

                "content":
                    row["message"],

                "created_at":
                    row[
                        "original_created_at"
                    ],

                "archived_at":
                    row["archived_at"],
            }
            for row in rows
        ]

    finally:
        connection.close()