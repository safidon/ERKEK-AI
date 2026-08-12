from app.database import (
    get_connection,
    adapt_query,
)

from app.brain.memory import (
    get_user_profile,
)


# =====================================================
# GET SUMMARY STATE
# =====================================================

def get_summary_state(
    user_id: str,
    session_id: int | None = None
) -> dict:
    """
    Пайдаланушының summary күйін қайтарады.

    session_id берілсе:
    - нақты conversation session summary алынады.

    session_id берілмесе:
    - legacy summary алынады.

    Нәтиже:
    {
        "summary": str | None,
        "last_message_id": int
    }

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
                        summary,
                        last_message_id
                    FROM conversation_summaries
                    WHERE user_id = ?
                      AND session_id = ?
                    LIMIT 1
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
                    SELECT
                        summary,
                        last_message_id
                    FROM conversation_summaries
                    WHERE user_id = ?
                      AND session_id IS NULL
                    LIMIT 1
                    """
                ),
                (
                    user_id,
                ),
            )

        row = cursor.fetchone()

        if row is None:
            return {
                "summary": None,
                "last_message_id": 0,
            }

        return {
            "summary": row["summary"],
            "last_message_id": int(
                row["last_message_id"] or 0
            ),
        }

    finally:
        connection.close()


# =====================================================
# GET SUMMARY
# =====================================================

def get_summary(
    user_id: str,
    session_id: int | None = None
) -> str | None:
    """
    Тек summary мәтінін қайтарады.
    """

    state = get_summary_state(
        user_id=user_id,
        session_id=session_id,
    )

    return state["summary"]


# =====================================================
# SAVE SUMMARY
# =====================================================

def save_summary(
    user_id: str,
    summary: str,
    last_message_id: int,
    session_id: int | None = None
) -> None:
    """
    Summary және summary жасалған соңғы
    message ID-ні сақтайды.

    SQLite және PostgreSQL compatible.
    """

    # User users кестесінде бар екеніне кепілдік.
    get_user_profile(
        user_id
    )

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # =============================================
        # SESSION SUMMARY
        # =============================================

        if session_id is not None:

            cursor.execute(
                adapt_query(
                    """
                    INSERT INTO conversation_summaries (
                        user_id,
                        session_id,
                        summary,
                        last_message_id,
                        updated_at
                    )
                    VALUES (
                        ?, ?, ?, ?,
                        CURRENT_TIMESTAMP
                    )

                    ON CONFLICT(user_id, session_id)
                    DO UPDATE SET
                        summary = excluded.summary,
                        last_message_id = excluded.last_message_id,
                        updated_at = CURRENT_TIMESTAMP
                    """
                ),
                (
                    user_id,
                    session_id,
                    summary,
                    last_message_id,
                ),
            )

        # =============================================
        # LEGACY SUMMARY
        # =============================================

        else:

            # SQLite және PostgreSQL-де әдеттегі UNIQUE
            # constraint NULL session_id мәндерін бірдей
            # conflict ретінде ұстамайды.
            #
            # Сондықтан legacy NULL-session summary үшін
            # алдымен UPDATE, row табылмаса INSERT жасаймыз.

            cursor.execute(
                adapt_query(
                    """
                    UPDATE conversation_summaries
                    SET
                        summary = ?,
                        last_message_id = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                      AND session_id IS NULL
                    """
                ),
                (
                    summary,
                    last_message_id,
                    user_id,
                ),
            )

            if cursor.rowcount == 0:

                cursor.execute(
                    adapt_query(
                        """
                        INSERT INTO conversation_summaries (
                            user_id,
                            session_id,
                            summary,
                            last_message_id,
                            updated_at
                        )
                        VALUES (
                            ?, NULL, ?, ?,
                            CURRENT_TIMESTAMP
                        )
                        """
                    ),
                    (
                        user_id,
                        summary,
                        last_message_id,
                    ),
                )

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:
        connection.close()


# =====================================================
# DELETE SUMMARY
# =====================================================

def delete_summary(
    user_id: str,
    session_id: int | None = None
) -> None:
    """
    Summary өшіреді.

    session_id берілсе:
    - тек сол conversation session summary өшеді.

    session_id берілмесе:
    - legacy summary өшеді.

    SQLite және PostgreSQL compatible.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        if session_id is not None:

            cursor.execute(
                adapt_query(
                    """
                    DELETE FROM conversation_summaries
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
                    DELETE FROM conversation_summaries
                    WHERE user_id = ?
                      AND session_id IS NULL
                    """
                ),
                (
                    user_id,
                ),
            )

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:
        connection.close()