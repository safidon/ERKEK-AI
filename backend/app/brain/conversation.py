from app.database import get_connection


MAX_HISTORY = 20


# =====================================================
# GET CONVERSATION
# =====================================================

def get_conversation(
    user_id: str,
    session_id: int | None = None
) -> list[dict[str, str]]:
    """
    SQLite базасынан пайдаланушының соңғы хабарламаларын алады.

    session_id берілсе:
    - тек сол conversation session хабарламалары алынады.

    session_id берілмесе:
    - бұрынғы legacy логика сақталады.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        if session_id is not None:

            cursor.execute(
                """
                SELECT role, message
                FROM conversations
                WHERE user_id = ?
                  AND session_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (
                    user_id,
                    session_id,
                    MAX_HISTORY
                )
            )

        else:

            cursor.execute(
                """
                SELECT role, message
                FROM conversations
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (
                    user_id,
                    MAX_HISTORY
                )
            )

        rows = cursor.fetchall()

        rows = list(reversed(rows))

        return [
            {
                "role": row["role"],
                "content": row["message"]
            }
            for row in rows
        ]

    finally:
        connection.close()


# =====================================================
# ADD MESSAGE
# =====================================================

def add_message(
    user_id: str,
    role: str,
    content: str,
    session_id: int | None = None
) -> None:
    """
    Жаңа хабарламаны SQLite conversation history-ге сақтайды.

    Егер session_id берілсе,
    хабарлама нақты conversation session-ге байланысады.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO conversations (
                user_id,
                session_id,
                role,
                message
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                session_id,
                role,
                content
            )
        )

        connection.commit()

    finally:
        connection.close()


# =====================================================
# GET RECENT MESSAGES
# =====================================================

def get_recent_messages(
    user_id: str,
    limit: int = 10,
    session_id: int | None = None
) -> list[dict[str, str]]:
    """
    Пайдаланушының соңғы бірнеше хабарламасын алады.

    session_id берілсе,
    тек сол session history алынады.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        if session_id is not None:

            cursor.execute(
                """
                SELECT role, message
                FROM conversations
                WHERE user_id = ?
                  AND session_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (
                    user_id,
                    session_id,
                    limit
                )
            )

        else:

            cursor.execute(
                """
                SELECT role, message
                FROM conversations
                WHERE user_id = ?
                ORDER BY id DESC
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
                "role": row["role"],
                "content": row["message"]
            }
            for row in rows
        ]

    finally:
        connection.close()


# =====================================================
# FORMAT CONVERSATION
# =====================================================

def format_conversation(
    user_id: str,
    limit: int = 10,
    session_id: int | None = None
) -> str:
    """
    Conversation history-ді AI prompt үшін мәтінге айналдырады.
    """

    messages = get_recent_messages(
        user_id=user_id,
        limit=limit,
        session_id=session_id
    )

    if not messages:
        return "Бұрынғы әңгіме жоқ."

    history = []

    for message in messages:

        role = message["role"]
        content = message["content"]

        if role == "user":
            history.append(
                f"Пайдаланушы: {content}"
            )

        elif role == "assistant":
            history.append(
                f"ERKEK AI: {content}"
            )

    return "\n".join(history)


# =====================================================
# LATEST MESSAGE ID
# =====================================================

def get_latest_message_id(
    user_id: str,
    session_id: int | None = None
) -> int:
    """
    Ең соңғы conversation message ID қайтарады.

    session_id болса:
    - сол session бойынша.

    Болмаса:
    - user бойынша.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        if session_id is not None:

            cursor.execute(
                """
                SELECT MAX(id) AS latest_id
                FROM conversations
                WHERE user_id = ?
                  AND session_id = ?
                """,
                (
                    user_id,
                    session_id
                )
            )

        else:

            cursor.execute(
                """
                SELECT MAX(id) AS latest_id
                FROM conversations
                WHERE user_id = ?
                """,
                (user_id,)
            )

        row = cursor.fetchone()

        if row is None:
            return 0

        latest_id = row["latest_id"]

        if latest_id is None:
            return 0

        return int(latest_id)

    finally:
        connection.close()


# =====================================================
# GET MESSAGES AFTER ID
# =====================================================

def get_messages_after(
    user_id: str,
    last_message_id: int,
    limit: int = 20,
    session_id: int | None = None
) -> list[dict]:
    """
    Белгілі message ID-ден кейінгі жаңа хабарламаларды қайтарады.

    Incremental summary үшін қолданылады.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        if session_id is not None:

            cursor.execute(
                """
                SELECT
                    id,
                    session_id,
                    role,
                    message,
                    created_at
                FROM conversations
                WHERE user_id = ?
                  AND session_id = ?
                  AND id > ?
                ORDER BY id ASC
                LIMIT ?
                """,
                (
                    user_id,
                    session_id,
                    last_message_id,
                    limit
                )
            )

        else:

            cursor.execute(
                """
                SELECT
                    id,
                    session_id,
                    role,
                    message,
                    created_at
                FROM conversations
                WHERE user_id = ?
                  AND id > ?
                ORDER BY id ASC
                LIMIT ?
                """,
                (
                    user_id,
                    last_message_id,
                    limit
                )
            )

        rows = cursor.fetchall()

        return [
            {
                "id": row["id"],
                "session_id": row["session_id"],
                "role": row["role"],
                "content": row["message"],
                "created_at": row["created_at"]
            }
            for row in rows
        ]

    finally:
        connection.close()


# =====================================================
# GET MESSAGES BEFORE OR EQUAL
# =====================================================

def get_messages_before_or_equal(
    user_id: str,
    message_id: int,
    limit: int = 100,
    session_id: int | None = None
) -> list[dict]:
    """
    Белгілі бір ID-ге дейінгі хабарламаларды алады.

    Cleanup/archive кезінде қолданылады.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        if session_id is not None:

            cursor.execute(
                """
                SELECT
                    id,
                    session_id,
                    role,
                    message,
                    created_at
                FROM conversations
                WHERE user_id = ?
                  AND session_id = ?
                  AND id <= ?
                ORDER BY id ASC
                LIMIT ?
                """,
                (
                    user_id,
                    session_id,
                    message_id,
                    limit
                )
            )

        else:

            cursor.execute(
                """
                SELECT
                    id,
                    session_id,
                    role,
                    message,
                    created_at
                FROM conversations
                WHERE user_id = ?
                  AND id <= ?
                ORDER BY id ASC
                LIMIT ?
                """,
                (
                    user_id,
                    message_id,
                    limit
                )
            )

        rows = cursor.fetchall()

        return [
            {
                "id": row["id"],
                "session_id": row["session_id"],
                "role": row["role"],
                "content": row["message"],
                "created_at": row["created_at"]
            }
            for row in rows
        ]

    finally:
        connection.close()


# =====================================================
# MESSAGE COUNT
# =====================================================

def get_message_count(
    user_id: str,
    session_id: int | None = None
) -> int:
    """
    Conversation message санын қайтарады.

    session_id берілсе,
    тек сол session ішіндегі message саны есептеледі.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        if session_id is not None:

            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM conversations
                WHERE user_id = ?
                  AND session_id = ?
                """,
                (
                    user_id,
                    session_id
                )
            )

        else:

            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM conversations
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