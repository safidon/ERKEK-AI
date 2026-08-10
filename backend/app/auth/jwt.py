from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import JWT_SECRET_KEY


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def create_access_token(user_id: str) -> str:
    """
    User үшін JWT access token жасайды.
    """

    now = datetime.now(timezone.utc)

    expire = now + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": user_id,
        "iat": now,
        "exp": expire
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=ALGORITHM
    )


def decode_access_token(token: str) -> str | None:
    """
    JWT token-ді тексеріп,
    ішіндегі user_id қайтарады.
    """

    try:

        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if not user_id:
            return None

        return str(user_id)

    except JWTError:
        return None