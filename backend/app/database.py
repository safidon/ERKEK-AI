import sqlite3
from pathlib import Path


# =====================================================
# DATABASE PATH
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_DIR = BASE_DIR / "database"
DATABASE_DIR.mkdir(
    parents=True,
    exist_ok=True
)

DATABASE_PATH = DATABASE_DIR / "erkek_ai.db"


# =====================================================
# CONNECTION
# =====================================================

def get_connection():
    """
    SQLite базасына connection қайтарады.
    """

    connection = sqlite3.connect(
        DATABASE_PATH,
        check_same_thread=False
    )

    connection.row_factory = sqlite3.Row

    # SQLite foreign key support
    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


# =====================================================
# INITIALIZE DATABASE
# =====================================================

def init_database():
    """
    ERKEK AI үшін қажетті кестелерді жасайды
    және қарапайым migration орындайды.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # =============================================
        # USERS / LONG-TERM MEMORY
        # =============================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,

                language TEXT,
                age INTEGER,
                marital_status TEXT,
                children INTEGER,

                career TEXT,
                financial_status TEXT,
                main_goal TEXT,

                goals TEXT,
                habits TEXT,
                important_events TEXT,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # =============================================
        # CONVERSATION MESSAGES
        # =============================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                message TEXT NOT NULL,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(user_id)
                    ON DELETE CASCADE
            )
        """)

        # =============================================
        # CONVERSATION SUMMARY
        # =============================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_summaries (
                user_id TEXT PRIMARY KEY,

                summary TEXT NOT NULL,

                last_message_id INTEGER DEFAULT 0,

                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(user_id)
                    ON DELETE CASCADE
            )
        """)

        # =============================================
        # MIGRATION
        # old database:
        # conversation_summaries.last_message_id
        # =============================================

        cursor.execute("""
            PRAGMA table_info(conversation_summaries)
        """)

        columns = [
            row["name"]
            for row in cursor.fetchall()
        ]

        if "last_message_id" not in columns:

            cursor.execute("""
                ALTER TABLE conversation_summaries
                ADD COLUMN last_message_id INTEGER DEFAULT 0
            """)

        # =============================================
        # INDEXES
        # =============================================

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_conversations_user_id
            ON conversations(user_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_conversations_user_id_id
            ON conversations(user_id, id)
        """)

        connection.commit()

    finally:
        connection.close()


# =====================================================
# SIMPLE TEST
# =====================================================

if __name__ == "__main__":

    init_database()

    print("ERKEK AI database дайын.")
    print(f"Database: {DATABASE_PATH}")