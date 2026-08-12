from app.database import (
    get_connection,
    adapt_query,
    is_postgresql,
)


# =====================================================
# CREATE SESSION
# =====================================================

def create_session(
    user_id: str,
    title: str = "Жаңа әңгіме",
) -> dict:
    """
    Жаңа conversation session жасайды.

    SQLite және PostgreSQL compatible.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        clean_title = (
            title.strip()
            or "Жаңа әңгіме"
        )

        # =================================================
        # POSTGRESQL
        # =================================================
        #
        # is_active schema-да INTEGER (0/1) ретінде тұр.
        # Сондықтан PostgreSQL-де TRUE емес, 1 жазамыз.
        #

        if is_postgresql():
            cursor.execute(
                """
                INSERT INTO conversation_sessions (
                    user_id,
                    title,
                    is_active
                )
                VALUES (%s, %s, 1)
                RETURNING id
                """,
                (
                    user_id,
                    clean_title,
                ),
            )

            row = cursor.fetchone()

            if row is None:
                raise RuntimeError(
                    "Жаңа session ID алынбады."
                )

            session_id = int(
                row["id"]
            )

        # =================================================
        # SQLITE
        # =================================================

        else:
            cursor.execute(
                """
                INSERT INTO conversation_sessions (
                    user_id,
                    title,
                    is_active
                )
                VALUES (?, ?, 1)
                """,
                (
                    user_id,
                    clean_title,
                ),
            )

            session_id = (
                cursor.lastrowid
            )

            if session_id is None:
                raise RuntimeError(
                    "Жаңа session ID алынбады."
                )

            session_id = int(
                session_id
            )

        connection.commit()

        return {
            "id": session_id,
            "user_id": user_id,
            "title": clean_title,
            "is_active": True,
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# =====================================================
# GET SESSION
# =====================================================

def get_session(
    user_id: str,
    session_id: int,
):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            adapt_query(
                """
                SELECT *
                FROM conversation_sessions
                WHERE id = ?
                  AND user_id = ?
                """
            ),
            (
                session_id,
                user_id,
            ),
        )

        return cursor.fetchone()

    finally:
        connection.close()


# =====================================================
# LIST SESSIONS
# =====================================================

def list_sessions(
    user_id: str,
    limit: int = 50,
) -> list[dict]:
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            adapt_query(
                """
                SELECT
                    id,
                    title,
                    is_active,
                    created_at,
                    updated_at
                FROM conversation_sessions
                WHERE user_id = ?
                ORDER BY updated_at DESC, id DESC
                LIMIT ?
                """
            ),
            (
                user_id,
                limit,
            ),
        )

        rows = cursor.fetchall()

        return [
            {
                "id": row["id"],
                "title": row["title"],
                "is_active": bool(
                    row["is_active"]
                ),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]

    finally:
        connection.close()


# =====================================================
# RENAME SESSION
# =====================================================

def rename_session(
    user_id: str,
    session_id: int,
    title: str,
) -> bool:
    clean_title = (
        title.strip()
    )

    if not clean_title:
        return False

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            adapt_query(
                """
                UPDATE conversation_sessions
                SET
                    title = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                  AND user_id = ?
                """
            ),
            (
                clean_title,
                session_id,
                user_id,
            ),
        )

        updated = (
            cursor.rowcount > 0
        )

        connection.commit()

        return updated

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# =====================================================
# TOUCH SESSION
# =====================================================

def touch_session(
    user_id: str,
    session_id: int,
) -> bool:
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            adapt_query(
                """
                UPDATE conversation_sessions
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                  AND user_id = ?
                """
            ),
            (
                session_id,
                user_id,
            ),
        )

        updated = (
            cursor.rowcount > 0
        )

        connection.commit()

        return updated

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# =====================================================
# DELETE SESSION
# =====================================================

def delete_session(
    user_id: str,
    session_id: int,
) -> bool:
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            adapt_query(
                """
                DELETE FROM conversation_sessions
                WHERE id = ?
                  AND user_id = ?
                """
            ),
            (
                session_id,
                user_id,
            ),
        )

        deleted = (
            cursor.rowcount > 0
        )

        connection.commit()

        return deleted

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# =====================================================
# GET FULL SESSION HISTORY
# =====================================================

def get_session_messages(
    user_id: str,
    session_id: int,
    limit: int = 100,
) -> list[dict]:
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            adapt_query(
                """
                SELECT
                    original_message_id AS id,
                    role,
                    message,
                    original_created_at AS created_at
                FROM conversation_archive
                WHERE user_id = ?
                  AND session_id = ?
                ORDER BY original_message_id ASC
                """
            ),
            (
                user_id,
                session_id,
            ),
        )

        archived_rows = (
            cursor.fetchall()
        )

        archived_messages = [
            {
                "id": row["id"],
                "role": row["role"],
                "content": row["message"],
                "created_at": row["created_at"],
                "archived": True,
            }
            for row in archived_rows
        ]

        cursor.execute(
            adapt_query(
                """
                SELECT
                    id,
                    role,
                    message,
                    created_at
                FROM conversations
                WHERE user_id = ?
                  AND session_id = ?
                ORDER BY id ASC
                """
            ),
            (
                user_id,
                session_id,
            ),
        )

        active_rows = (
            cursor.fetchall()
        )

        active_messages = [
            {
                "id": row["id"],
                "role": row["role"],
                "content": row["message"],
                "created_at": row["created_at"],
                "archived": False,
            }
            for row in active_rows
        ]

        messages = (
            archived_messages
            + active_messages
        )

        messages.sort(
            key=lambda item:
                item["id"]
        )

        if limit > 0:
            messages = (
                messages[-limit:]
            )

        return messages

    finally:
        connection.close()


# =====================================================
# AUTO SESSION TITLE
# =====================================================

def generate_session_title(
    user_id: str,
    session_id: int,
    message: str,
) -> str:
    session = get_session(
        user_id,
        session_id,
    )

    if session is None:
        return "Жаңа әңгіме"

    current_title = (
        session["title"]
    )

    if (
        current_title
        != "Жаңа әңгіме"
    ):
        return current_title

    clean_message = " ".join(
        message
        .strip()
        .split()
    )

    if not clean_message:
        return current_title

    max_length = 45

    if (
        len(clean_message)
        > max_length
    ):
        clean_message = (
            clean_message[
                :max_length
            ]
            .rstrip(
                " ,.!?:;-"
            )
            + "..."
        )

    rename_session(
        user_id=user_id,
        session_id=session_id,
        title=clean_message,
    )

    return clean_message