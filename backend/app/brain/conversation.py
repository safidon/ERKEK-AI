from app.database import get_connection


MAX_HISTORY = 20


def get_conversation(user_id: str) -> list[dict[str, str]]:
    """
    SQLite базасынан пайдаланушының соңғы хабарламаларын алады.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

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

        # DESC келгендіктен қайта аударамыз
        rows = list(reversed(rows))

        conversation = []

        for row in rows:
            conversation.append({
                "role": row["role"],
                "content": row["message"]
            })

        return conversation

    finally:
        connection.close()


def add_message(
    user_id: str,
    role: str,
    content: str
) -> None:
    """
    Жаңа хабарламаны SQLite conversation history-ге сақтайды.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO conversations (
                user_id,
                role,
                message
            )
            VALUES (?, ?, ?)
            """,
            (
                user_id,
                role,
                content
            )
        )

        connection.commit()

        # Бір user үшін өте көп history жиналмасын
        cursor.execute(
            """
            DELETE FROM conversations
            WHERE user_id = ?
            AND id NOT IN (
                SELECT id
                FROM conversations
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
            )
            """,
            (
                user_id,
                user_id,
                MAX_HISTORY
            )
        )

        connection.commit()

    finally:
        connection.close()


def get_recent_messages(
    user_id: str,
    limit: int = 10
) -> list[dict[str, str]]:
    """
    Пайдаланушының соңғы бірнеше хабарламасын алады.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

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

        messages = []

        for row in rows:
            messages.append({
                "role": row["role"],
                "content": row["message"]
            })

        return messages

    finally:
        connection.close()


def format_conversation(
    user_id: str,
    limit: int = 10
) -> str:
    """
    Conversation history-ді AI prompt үшін мәтінге айналдырады.
    """

    messages = get_recent_messages(
        user_id,
        limit
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


def get_latest_message_id(user_id: str) -> int:
    """
    Пайдаланушының ең соңғы conversation message ID-сін қайтарады.

    Егер хабарлама болмаса — 0.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

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


def get_messages_after(
    user_id: str,
    last_message_id: int,
    limit: int = 20
) -> list[dict]:
    """
    Белгілі бір message ID-ден кейінгі
    жаңа conversation хабарламаларын қайтарады.

    Бұл функция incremental summary үшін қажет.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
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

        messages = []

        for row in rows:
            messages.append({
                "id": row["id"],
                "role": row["role"],
                "content": row["message"],
                "created_at": row["created_at"]
            })

        return messages

    finally:
        connection.close()