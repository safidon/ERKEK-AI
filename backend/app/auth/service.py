import uuid

from app.database import (
    get_connection,
    adapt_query,
)

from app.auth.security import (
    hash_password,
    verify_password,
)


# =====================================================
# GET USER BY EMAIL
# =====================================================

def get_user_by_email(
    email: str
):
    """
    Email арқылы пайдаланушыны іздейді.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            adapt_query(
                """
                SELECT *
                FROM users
                WHERE LOWER(email) = LOWER(?)
                """
            ),
            (
                email.strip(),
            ),
        )

        return cursor.fetchone()

    finally:
        connection.close()


# =====================================================
# GET USER BY USERNAME
# =====================================================

def get_user_by_username(
    username: str
):
    """
    Username арқылы пайдаланушыны іздейді.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            adapt_query(
                """
                SELECT *
                FROM users
                WHERE LOWER(username) = LOWER(?)
                """
            ),
            (
                username.strip(),
            ),
        )

        return cursor.fetchone()

    finally:
        connection.close()


# =====================================================
# CREATE USER
# =====================================================

def create_user(
    email: str,
    username: str,
    password: str,
) -> dict:
    """
    Жаңа пайдаланушы жасайды.
    """

    # =================================================
    # NORMALIZE
    # =================================================

    email = (
        email
        .strip()
        .lower()
    )

    username = (
        username
        .strip()
    )

    # =================================================
    # EMAIL DUPLICATE
    # =================================================

    if get_user_by_email(
        email
    ):
        raise ValueError(
            "Бұл email бұрын тіркелген."
        )

    # =================================================
    # USERNAME DUPLICATE
    # =================================================

    if get_user_by_username(
        username
    ):
        raise ValueError(
            "Бұл username бұрын тіркелген."
        )

    # =================================================
    # UUID
    # =================================================

    user_id = str(
        uuid.uuid4()
    )

    # =================================================
    # PASSWORD HASH
    # =================================================

    password_hash = (
        hash_password(
            password
        )
    )

    # =================================================
    # DATABASE
    # =================================================

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            adapt_query(
                """
                INSERT INTO users (
                    user_id,
                    email,
                    username,
                    password_hash,
                    is_active
                )
                VALUES (?, ?, ?, ?, 1)
                """
            ),
            (
                user_id,
                email,
                username,
                password_hash,
            ),
        )

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:
        connection.close()

    # =================================================
    # RESULT
    # =================================================

    return {
        "user_id": user_id,
        "email": email,
        "username": username,
        "is_active": True,
    }


# =====================================================
# AUTHENTICATE USER
# =====================================================

def authenticate_user(
    email: str,
    password: str,
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

    # =================================================
    # ACTIVE CHECK
    # =================================================

    if not user[
        "is_active"
    ]:
        return None

    # =================================================
    # PASSWORD HASH
    # =================================================

    password_hash = user[
        "password_hash"
    ]

    if not password_hash:
        return None

    # =================================================
    # PASSWORD VERIFY
    # =================================================

    if not verify_password(
        password,
        password_hash,
    ):
        return None

    return user


# =====================================================
# GET USER BY ID
# =====================================================

def get_user_by_id(
    user_id: str
):
    """
    user_id арқылы пайдаланушыны қайтарады.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            adapt_query(
                """
                SELECT *
                FROM users
                WHERE user_id = ?
                """
            ),
            (
                user_id,
            ),
        )

        return cursor.fetchone()

    finally:
        connection.close()