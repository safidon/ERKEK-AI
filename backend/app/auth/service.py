import uuid

from app.database import get_connection
from app.auth.security import (
    hash_password,
    verify_password
)


def get_user_by_email(email: str):
    """
    Email арқылы пайдаланушыны іздейді.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE LOWER(email) = LOWER(?)
            """,
            (email.strip(),)
        )

        return cursor.fetchone()

    finally:
        connection.close()


def get_user_by_username(username: str):
    """
    Username арқылы пайдаланушыны іздейді.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE LOWER(username) = LOWER(?)
            """,
            (username.strip(),)
        )

        return cursor.fetchone()

    finally:
        connection.close()


def create_user(
    email: str,
    username: str,
    password: str
) -> dict:
    """
    Жаңа пайдаланушы жасайды.
    """

    email = email.strip().lower()
    username = username.strip()

    # Email duplicate
    if get_user_by_email(email):
        raise ValueError(
            "Бұл email бұрын тіркелген."
        )

    # Username duplicate
    if get_user_by_username(username):
        raise ValueError(
            "Бұл username бұрын тіркелген."
        )

    # UUID
    user_id = str(uuid.uuid4())

    # Password hash
    password_hash = hash_password(password)

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO users (
                user_id,
                email,
                username,
                password_hash,
                is_active
            )
            VALUES (?, ?, ?, ?, 1)
            """,
            (
                user_id,
                email,
                username,
                password_hash
            )
        )

        connection.commit()

    finally:
        connection.close()

    return {
        "user_id": user_id,
        "email": email,
        "username": username,
        "is_active": True
    }
from app.auth.security import verify_password


def authenticate_user(
    email: str,
    password: str
):
    """
    Email және password арқылы
    пайдаланушыны тексереді.

    Дұрыс болса user row қайтарады.
    Қате болса None қайтарады.
    """

    user = get_user_by_email(
        email
    )

    if not user:
        return None

    if not user["is_active"]:
        return None

    password_hash = user["password_hash"]

    if not password_hash:
        return None

    if not verify_password(
        password,
        password_hash
    ):
        return None

    return user

def get_user_by_id(user_id: str):
    """
    user_id арқылы пайдаланушыны қайтарады.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE user_id = ?
            """,
            (user_id,)
        )

        return cursor.fetchone()

    finally:
        connection.close()