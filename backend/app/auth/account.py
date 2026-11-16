"""
Аккаунтты толық жою.

Пайдаланушының барлық деректері бір транзакцияда өшіріледі.
Кестелер foreign key арқылы да байланысқан (ON DELETE CASCADE),
бірақ ешнәрсе қалып қоймауы үшін әрқайсысы анық өшіріледі.
Резервтік көшірмелерден деректер BACKUP_KEEP_DAYS ішінде өзі кетеді.
"""

from app.core.logger import logger
from app.database import adapt_query, get_connection


# Ретімен: алдымен тәуелді кестелер, соңында users.
_DELETE_QUERIES = (
    "DELETE FROM conversation_archive WHERE user_id = ?",
    "DELETE FROM conversations WHERE user_id = ?",
    "DELETE FROM conversation_summaries WHERE user_id = ?",
    "DELETE FROM conversation_sessions WHERE user_id = ?",
    "DELETE FROM password_reset_tokens WHERE user_id = ?",
    "DELETE FROM auth_sessions WHERE user_id = ?",
    "DELETE FROM user_consents WHERE user_id = ?",
    "DELETE FROM usage_daily WHERE scope = ?",
    "DELETE FROM message_feedback WHERE user_id = ?",
    "DELETE FROM users WHERE user_id = ?",
)


def delete_account(user_id: str) -> None:
    connection = get_connection()

    try:
        cursor = connection.cursor()

        for query in _DELETE_QUERIES:
            cursor.execute(adapt_query(query), (user_id,))

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    logger.info("Account deleted | user_id=%s", user_id)
