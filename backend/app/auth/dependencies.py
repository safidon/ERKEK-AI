from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.jwt import decode_access_payload
from app.auth.sessions import is_session_active
from app.auth.service import get_user_by_id


security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Authorization: Bearer <token>
    арқылы ағымдағы user-ді анықтайды.
    """

    token = credentials.credentials

    payload = decode_access_payload(
        token
    )

    user_id = (
        str(payload["sub"])
        if payload
        else None
    )

    # Сессия жабылған болса (logout, құпиясөз ауысты) —
    # token мерзімі бітпесе де қабылданбайды.
    if (
        user_id
        and payload.get("sid")
        and not is_session_active(
            str(payload["sid"]),
            user_id,
        )
    ):
        user_id = None

    if not user_id:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Жарамсыз немесе мерзімі өткен token.",
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )

    user = get_user_by_id(
        user_id
    )

    if not user:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пайдаланушы табылмады.",
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )

    if not user["is_active"]:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Аккаунт белсенді емес."
        )

    return user