"""
Пайдалану шарттары мен құпиялылық саясатына келісім.

Құжат өзгерсе, LEGAL_VERSION жаңартылады (frontend/lib/legal.ts-тегі
нұсқамен бірдей болуы керек).
"""

from datetime import datetime, timezone

from app.database import adapt_query, get_connection


LEGAL_VERSION = "2026-11-15"

DOCUMENTS = ("terms", "privacy", "cross_border_transfer", "age_18_plus")


def record_consents(user_id: str, version: str = LEGAL_VERSION) -> None:
    now = datetime.now(timezone.utc).isoformat()

    connection = get_connection()

    try:
        cursor = connection.cursor()

        for document in DOCUMENTS:
            cursor.execute(
                adapt_query(
                    """
                    INSERT INTO user_consents (
                        user_id, document, version, accepted_at
                    )
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT (user_id, document, version) DO NOTHING
                    """
                ),
                (user_id, document, version, now),
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_consents(user_id: str) -> list[dict]:
    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute(
            adapt_query(
                """
                SELECT document, version, accepted_at
                FROM user_consents
                WHERE user_id = ?
                ORDER BY document
                """
            ),
            (user_id,),
        )
        rows = cursor.fetchall()

    finally:
        connection.close()

    return [
        {
            "document": row["document"],
            "version": row["version"],
            "accepted_at": row["accepted_at"],
        }
        for row in rows
    ]
