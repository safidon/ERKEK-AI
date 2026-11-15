import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import JWT_SECRET_KEY


ALGORITHM = "HS256"


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


# Қысқа өмір сүреді: frontend оны refresh token арқылы
# мерзімі бітпей тұрып автоматты түрде жаңартады.
ACCESS_TOKEN_EXPIRE_MINUTES = _env_int("ACCESS_TOKEN_EXPIRE_MINUTES", 15)


def create_access_token(
    user_id: str,
    session_id: str | None = None,
) -> str:
    """
    User үшін JWT access token жасайды.
    session_id (sid) берілсе, әр сұраныста сессияның
    белсенді екені тексеріледі (logout / құпиясөз ауысуы бірден әсер етеді).
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

    if session_id:
        payload["sid"] = session_id

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=ALGORITHM
    )


def decode_access_payload(token: str) -> dict | None:
    """
    JWT token-ді тексереді. Жарамды болса payload қайтарады.
    """

    try:

        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[ALGORITHM]
        )

    except JWTError:
        return None

    if not payload.get("sub"):
        return None

    return payload


def decode_access_token(token: str) -> str | None:
    """
    JWT token-ді тексеріп,
    ішіндегі user_id қайтарады.
    """

    payload = decode_access_payload(token)

    if not payload:
        return None

    return str(payload["sub"])
