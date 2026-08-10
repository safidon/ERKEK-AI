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
    және migration орындайды.
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
        # CONVERSATION SESSIONS
        # =============================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id TEXT NOT NULL,

                title TEXT NOT NULL DEFAULT 'Жаңа әңгіме',

                is_active INTEGER NOT NULL DEFAULT 1,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(user_id)
                    ON DELETE CASCADE
            )
        """)

        # =============================================
        # CONVERSATION MESSAGES
        # =============================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id TEXT NOT NULL,

                session_id INTEGER,

                role TEXT NOT NULL,
                message TEXT NOT NULL,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(user_id)
                    ON DELETE CASCADE,

                FOREIGN KEY (session_id)
                    REFERENCES conversation_sessions(id)
                    ON DELETE CASCADE
            )
        """)

        # =============================================
        # CONVERSATION SUMMARY
        # legacy-compatible initial creation
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
        # CONVERSATION ARCHIVE
        # =============================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_archive (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                original_message_id INTEGER NOT NULL,

                user_id TEXT NOT NULL,

                session_id INTEGER,

                role TEXT NOT NULL,

                message TEXT NOT NULL,

                original_created_at TIMESTAMP,

                archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(user_id)
                    ON DELETE CASCADE,

                FOREIGN KEY (session_id)
                    REFERENCES conversation_sessions(id)
                    ON DELETE CASCADE
            )
        """)

        # =============================================
        # MIGRATION:
        # conversation_summaries.last_message_id
        # =============================================

        cursor.execute("""
            PRAGMA table_info(conversation_summaries)
        """)

        summary_columns = [
            row["name"]
            for row in cursor.fetchall()
        ]

        if "last_message_id" not in summary_columns:
            cursor.execute("""
                ALTER TABLE conversation_summaries
                ADD COLUMN last_message_id INTEGER DEFAULT 0
            """)

        # =============================================
        # AUTH MIGRATION
        # =============================================

        cursor.execute("""
            PRAGMA table_info(users)
        """)

        user_columns = [
            row["name"]
            for row in cursor.fetchall()
        ]

        auth_columns = {
            "email": "TEXT",
            "username": "TEXT",
            "password_hash": "TEXT",
            "is_active": "INTEGER DEFAULT 1"
        }

        for column_name, column_type in auth_columns.items():

            if column_name not in user_columns:

                cursor.execute(
                    f"""
                    ALTER TABLE users
                    ADD COLUMN {column_name} {column_type}
                    """
                )

        # =============================================
        # CONVERSATIONS SESSION MIGRATION
        # =============================================

        cursor.execute("""
            PRAGMA table_info(conversations)
        """)

        conversation_columns = [
            row["name"]
            for row in cursor.fetchall()
        ]

        if "session_id" not in conversation_columns:
            cursor.execute("""
                ALTER TABLE conversations
                ADD COLUMN session_id INTEGER
            """)

        # =============================================
        # CONVERSATION SUMMARIES SESSION MIGRATION
        # =============================================

        cursor.execute("""
            PRAGMA table_info(conversation_summaries)
        """)

        summary_columns = [
            row["name"]
            for row in cursor.fetchall()
        ]

        if "session_id" not in summary_columns:

            cursor.execute("""
                ALTER TABLE conversation_summaries
                RENAME TO conversation_summaries_legacy
            """)

            cursor.execute("""
                CREATE TABLE conversation_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    user_id TEXT NOT NULL,
                    session_id INTEGER,

                    summary TEXT NOT NULL,

                    last_message_id INTEGER DEFAULT 0,

                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    UNIQUE(user_id, session_id),

                    FOREIGN KEY (user_id)
                        REFERENCES users(user_id)
                        ON DELETE CASCADE,

                    FOREIGN KEY (session_id)
                        REFERENCES conversation_sessions(id)
                        ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                INSERT INTO conversation_summaries (
                    user_id,
                    session_id,
                    summary,
                    last_message_id,
                    updated_at
                )
                SELECT
                    user_id,
                    NULL,
                    summary,
                    last_message_id,
                    updated_at
                FROM conversation_summaries_legacy
            """)

            cursor.execute("""
                DROP TABLE conversation_summaries_legacy
            """)

        # =============================================
        # CONVERSATION ARCHIVE SESSION MIGRATION
        # =============================================

        cursor.execute("""
            PRAGMA table_info(conversation_archive)
        """)

        archive_columns = [
            row["name"]
            for row in cursor.fetchall()
        ]

        if "session_id" not in archive_columns:
            cursor.execute("""
                ALTER TABLE conversation_archive
                ADD COLUMN session_id INTEGER
            """)

        # =============================================
        # INDEXES
        # =============================================

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_conversation_sessions_user_id
            ON conversation_sessions(user_id)
        """)

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

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_conversations_session_id
            ON conversations(session_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_conversations_user_session_id
            ON conversations(user_id, session_id, id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_conversation_summaries_user_session
            ON conversation_summaries(user_id, session_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_conversation_archive_user_id
            ON conversation_archive(user_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_conversation_archive_user_session
            ON conversation_archive(user_id, session_id)
        """)

        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_conversation_archive_original_message_id
            ON conversation_archive(original_message_id)
        """)

        # =============================================
        # AUTH INDEXES
        # =============================================

        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_users_email
            ON users(email)
            WHERE email IS NOT NULL
        """)

        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_users_username
            ON users(username)
            WHERE username IS NOT NULL
        """)

        # =============================================
        # COMMIT
        # =============================================

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