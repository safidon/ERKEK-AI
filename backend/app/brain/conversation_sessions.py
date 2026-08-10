from app.database import get_connection


# =====================================================
# CREATE SESSION
# =====================================================

def create_session(
    user_id: str,
    title: str = "Жаңа әңгіме"
) -> dict:
    """
    Жаңа conversation session жасайды.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        clean_title = (
            title.strip()
            or "Жаңа әңгіме"
        )

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
                clean_title
            )
        )

        session_id = cursor.lastrowid

        connection.commit()

        return {
            "id": session_id,
            "user_id": user_id,
            "title": clean_title,
            "is_active": True
        }

    finally:
        connection.close()


# =====================================================
# GET SESSION
# =====================================================

def get_session(
    user_id: str,
    session_id: int
):
    """
    Белгілі бір session-ді қайтарады.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM conversation_sessions
            WHERE id = ?
              AND user_id = ?
            """,
            (
                session_id,
                user_id
            )
        )

        return cursor.fetchone()

    finally:
        connection.close()


# =====================================================
# LIST SESSIONS
# =====================================================

def list_sessions(
    user_id: str,
    limit: int = 50
) -> list[dict]:
    """
    Пайдаланушының conversation session тізімін қайтарады.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
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
            """,
            (
                user_id,
                limit
            )
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
                "updated_at": row["updated_at"]
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
    title: str
) -> bool:
    """
    Session title өзгертеді.
    """

    clean_title = title.strip()

    if not clean_title:
        return False

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE conversation_sessions
            SET
                title = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
              AND user_id = ?
            """,
            (
                clean_title,
                session_id,
                user_id
            )
        )

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()


# =====================================================
# TOUCH SESSION
# =====================================================

def touch_session(
    user_id: str,
    session_id: int
) -> bool:
    """
    Session updated_at уақытын жаңартады.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE conversation_sessions
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
              AND user_id = ?
            """,
            (
                session_id,
                user_id
            )
        )

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()


# =====================================================
# DELETE SESSION
# =====================================================

def delete_session(
    user_id: str,
    session_id: int
) -> bool:
    """
    Session-ді өшіреді.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM conversation_sessions
            WHERE id = ?
              AND user_id = ?
            """,
            (
                session_id,
                user_id
            )
        )

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()


# =====================================================
# GET FULL SESSION HISTORY
# =====================================================

def get_session_messages(
    user_id: str,
    session_id: int,
    limit: int = 100
) -> list[dict]:
    """
    Нақты conversation session-ның толық history-сін қайтарады.

    Бұл функция:
    - archive-тегі ескі message-терді;
    - active conversations message-терін;

    біріктіріп қайтарады.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # =================================================
        # 1. ARCHIVED MESSAGES
        # =================================================

        cursor.execute(
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
            """,
            (
                user_id,
                session_id
            )
        )

        archived_rows = cursor.fetchall()

        archived_messages = [
            {
                "id": row["id"],
                "role": row["role"],
                "content": row["message"],
                "created_at": row["created_at"],
                "archived": True
            }
            for row in archived_rows
        ]

        # =================================================
        # 2. ACTIVE MESSAGES
        # =================================================

        cursor.execute(
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
            """,
            (
                user_id,
                session_id
            )
        )

        active_rows = cursor.fetchall()

        active_messages = [
            {
                "id": row["id"],
                "role": row["role"],
                "content": row["message"],
                "created_at": row["created_at"],
                "archived": False
            }
            for row in active_rows
        ]

        # =================================================
        # 3. MERGE HISTORY
        # =================================================

        messages = (
            archived_messages
            + active_messages
        )

        messages.sort(
            key=lambda item: item["id"]
        )

        # =================================================
        # 4. LIMIT
        # =================================================

        if limit > 0:
            messages = messages[-limit:]

        return messages

    finally:
        connection.close()


# =====================================================
# AUTO SESSION TITLE
# =====================================================

def generate_session_title(
    user_id: str,
    session_id: int,
    message: str
) -> str:
    """
    Session әлі "Жаңа әңгіме" болса,
    бірінші user хабарламасынан автоматты title жасайды.
    """

    session = get_session(
        user_id,
        session_id
    )

    if session is None:
        return "Жаңа әңгіме"

    current_title = session["title"]

    # Қолмен немесе бұрын автоматты өзгертілген
    # title-ды қайта өзгертпейміз.
    if current_title != "Жаңа әңгіме":
        return current_title

    clean_message = " ".join(
        message.strip().split()
    )

    if not clean_message:
        return current_title

    max_length = 45

    if len(clean_message) > max_length:
        clean_message = (
            clean_message[:max_length]
            .rstrip(" ,.!?:;-")
            + "..."
        )

    rename_session(
        user_id=user_id,
        session_id=session_id,
        title=clean_message
    )

    return clean_message