import sqlite3
from pathlib import Path
from typing import Literal

import psycopg
from psycopg.rows import dict_row

from app.core.config import (
    APP_ENV,
    DATABASE_URL,
)


# =====================================================
# DATABASE TYPE
# =====================================================

DatabaseType = Literal[
    "sqlite",
    "postgresql",
]


# =====================================================
# SQLITE PATH
# =====================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

DATABASE_DIR = (
    BASE_DIR /
    "database"
)

DATABASE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

DATABASE_PATH = (
    DATABASE_DIR /
    "erkek_ai.db"
)


# =====================================================
# DATABASE TYPE DETECTION
# =====================================================

def get_database_type() -> DatabaseType:
    """
    Қай database қолданылатынын анықтайды.

    DATABASE_URL PostgreSQL URL болса -> PostgreSQL.
    Әйтпесе -> SQLite.
    """

    if DATABASE_URL:
        normalized_url = (
            DATABASE_URL
            .strip()
            .lower()
        )

        if (
            normalized_url.startswith(
                "postgresql://"
            )
            or
            normalized_url.startswith(
                "postgres://"
            )
        ):
            return "postgresql"

    return "sqlite"


# =====================================================
# HELPERS
# =====================================================

def is_postgresql() -> bool:
    return (
        get_database_type()
        == "postgresql"
    )


def is_sqlite() -> bool:
    return (
        get_database_type()
        == "sqlite"
    )


# =====================================================
# SQL ADAPTER
# =====================================================

def adapt_query(
    query: str
) -> str:
    """
    SQLite-style parameter placeholder-ларды
    PostgreSQL форматына бейімдейді.

    SQLite:
        ?

    PostgreSQL / Psycopg:
        %s
    """

    if is_postgresql():
        return query.replace(
            "?",
            "%s"
        )

    return query


# =====================================================
# SQLITE CONNECTION
# =====================================================

def get_sqlite_connection():
    """
    SQLite connection.
    """

    connection = sqlite3.connect(
        DATABASE_PATH,
        check_same_thread=False,
    )

    connection.row_factory = (
        sqlite3.Row
    )

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


# =====================================================
# POSTGRESQL CONNECTION
# =====================================================

def get_postgresql_connection():
    """
    PostgreSQL connection.

    dict_row қолданамыз,
    сондықтан row["column_name"]
    синтаксисі сақталады.
    """

    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL PostgreSQL үшін "
            "көрсетілмеген."
        )

    connection = psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row,
    )

    return connection


# =====================================================
# CONNECTION
# =====================================================

def get_connection():
    """
    Environment/config бойынша
    сәйкес database connection қайтарады.
    """

    database_type = (
        get_database_type()
    )

    if (
        database_type
        == "postgresql"
    ):
        return (
            get_postgresql_connection()
        )

    return (
        get_sqlite_connection()
    )


# =====================================================
# SQLITE INITIALIZATION
# =====================================================

def init_sqlite_database():
    """
    Қазіргі SQLite schema мен migration-дарды
    орындайды.
    """

    connection = (
        get_sqlite_connection()
    )

    try:
        cursor = (
            connection.cursor()
        )

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
            for row
            in cursor.fetchall()
        ]

        if (
            "last_message_id"
            not in summary_columns
        ):
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
            for row
            in cursor.fetchall()
        ]

        auth_columns = {
            "email":
                "TEXT",

            "username":
                "TEXT",

            "password_hash":
                "TEXT",

            "is_active":
                "INTEGER DEFAULT 1",
        }

        for (
            column_name,
            column_type,
        ) in auth_columns.items():

            if (
                column_name
                not in user_columns
            ):
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
            for row
            in cursor.fetchall()
        ]

        if (
            "session_id"
            not in conversation_columns
        ):
            cursor.execute("""
                ALTER TABLE conversations
                ADD COLUMN session_id INTEGER
            """)

        # =============================================
        # SUMMARY SESSION MIGRATION
        # =============================================

        cursor.execute("""
            PRAGMA table_info(conversation_summaries)
        """)

        summary_columns = [
            row["name"]
            for row
            in cursor.fetchall()
        ]

        if (
            "session_id"
            not in summary_columns
        ):

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
        # ARCHIVE SESSION MIGRATION
        # =============================================

        cursor.execute("""
            PRAGMA table_info(conversation_archive)
        """)

        archive_columns = [
            row["name"]
            for row
            in cursor.fetchall()
        ]

        if (
            "session_id"
            not in archive_columns
        ):
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

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# =====================================================
# POSTGRESQL INITIALIZATION
# =====================================================

def init_postgresql_database():
    """
    ERKEK AI PostgreSQL schema-сын жасайды.

    Қазіргі application layer-мен compatible:
    - users
    - conversation_sessions
    - conversations
    - conversation_summaries
    - conversation_archive
    """

    connection = (
        get_postgresql_connection()
    )

    try:
        cursor = (
            connection.cursor()
        )

        # =============================================
        # USERS
        # =============================================

        cursor.execute(
            """
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

                email TEXT,
                username TEXT,
                password_hash TEXT,

                is_active INTEGER NOT NULL DEFAULT 1,

                created_at TIMESTAMPTZ
                    NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMPTZ
                    NOT NULL
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # =============================================
        # CONVERSATION SESSIONS
        # =============================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation_sessions (
                id BIGINT
                    GENERATED BY DEFAULT AS IDENTITY
                    PRIMARY KEY,

                user_id TEXT NOT NULL,

                title TEXT
                    NOT NULL
                    DEFAULT 'Жаңа әңгіме',

                is_active INTEGER
                    NOT NULL
                    DEFAULT 1,

                created_at TIMESTAMPTZ
                    NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMPTZ
                    NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                CONSTRAINT fk_sessions_user
                    FOREIGN KEY (user_id)
                    REFERENCES users(user_id)
                    ON DELETE CASCADE
            )
            """
        )

        # =============================================
        # CONVERSATIONS
        # =============================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id BIGINT
                    GENERATED BY DEFAULT AS IDENTITY
                    PRIMARY KEY,

                user_id TEXT NOT NULL,

                session_id BIGINT,

                role TEXT NOT NULL,
                message TEXT NOT NULL,

                created_at TIMESTAMPTZ
                    NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                CONSTRAINT fk_conversations_user
                    FOREIGN KEY (user_id)
                    REFERENCES users(user_id)
                    ON DELETE CASCADE,

                CONSTRAINT fk_conversations_session
                    FOREIGN KEY (session_id)
                    REFERENCES conversation_sessions(id)
                    ON DELETE CASCADE
            )
            """
        )

        # =============================================
        # CONVERSATION SUMMARIES
        # =============================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation_summaries (
                id BIGINT
                    GENERATED BY DEFAULT AS IDENTITY
                    PRIMARY KEY,

                user_id TEXT NOT NULL,

                session_id BIGINT,

                summary TEXT NOT NULL,

                last_message_id BIGINT
                    NOT NULL
                    DEFAULT 0,

                updated_at TIMESTAMPTZ
                    NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                CONSTRAINT uq_summary_user_session
                    UNIQUE (
                        user_id,
                        session_id
                    ),

                CONSTRAINT fk_summaries_user
                    FOREIGN KEY (user_id)
                    REFERENCES users(user_id)
                    ON DELETE CASCADE,

                CONSTRAINT fk_summaries_session
                    FOREIGN KEY (session_id)
                    REFERENCES conversation_sessions(id)
                    ON DELETE CASCADE
            )
            """
        )

        # =============================================
        # CONVERSATION ARCHIVE
        # =============================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation_archive (
                id BIGINT
                    GENERATED BY DEFAULT AS IDENTITY
                    PRIMARY KEY,

                original_message_id BIGINT
                    NOT NULL,

                user_id TEXT NOT NULL,

                session_id BIGINT,

                role TEXT NOT NULL,

                message TEXT NOT NULL,

                original_created_at TIMESTAMPTZ,

                archived_at TIMESTAMPTZ
                    NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                CONSTRAINT fk_archive_user
                    FOREIGN KEY (user_id)
                    REFERENCES users(user_id)
                    ON DELETE CASCADE,

                CONSTRAINT fk_archive_session
                    FOREIGN KEY (session_id)
                    REFERENCES conversation_sessions(id)
                    ON DELETE CASCADE
            )
            """
        )

        # =============================================
        # USERS INDEXES
        # =============================================

        cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_users_email
            ON users (
                LOWER(email)
            )
            WHERE email IS NOT NULL
            """
        )

        cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_users_username
            ON users (
                LOWER(username)
            )
            WHERE username IS NOT NULL
            """
        )

        # =============================================
        # SESSION INDEXES
        # =============================================

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_conversation_sessions_user_id
            ON conversation_sessions(user_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_conversation_sessions_user_updated
            ON conversation_sessions(
                user_id,
                updated_at DESC
            )
            """
        )

        # =============================================
        # CONVERSATION INDEXES
        # =============================================

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_conversations_user_id
            ON conversations(user_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_conversations_user_id_id
            ON conversations(
                user_id,
                id
            )
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_conversations_session_id
            ON conversations(session_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_conversations_user_session_id
            ON conversations(
                user_id,
                session_id,
                id
            )
            """
        )

        # =============================================
        # SUMMARY INDEXES
        # =============================================

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_conversation_summaries_user_session
            ON conversation_summaries(
                user_id,
                session_id
            )
            """
        )

        cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_conversation_summaries_legacy_user
            ON conversation_summaries(user_id)
            WHERE session_id IS NULL
            """
        )

        # =============================================
        # ARCHIVE INDEXES
        # =============================================

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_conversation_archive_user_id
            ON conversation_archive(user_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_conversation_archive_user_session
            ON conversation_archive(
                user_id,
                session_id
            )
            """
        )

        cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_conversation_archive_original_message_id
            ON conversation_archive(
                original_message_id
            )
            """
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# =====================================================
# INITIALIZE DATABASE
# =====================================================

def init_database():
    """
    Database type бойынша
    сәйкес initializer іске қосылады.
    """

    if is_postgresql():
        init_postgresql_database()
        return

    init_sqlite_database()


# =====================================================
# SIMPLE TEST
# =====================================================

if __name__ == "__main__":

    init_database()

    print(
        "ERKEK AI database дайын."
    )

    print(
        "Database type:",
        get_database_type(),
    )

    if is_sqlite():
        print(
            f"Database: {DATABASE_PATH}"
        )

    else:
        print(
            "Database: PostgreSQL"
        )