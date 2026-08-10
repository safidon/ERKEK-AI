from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.jwt import decode_access_token
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

    user_id = decode_access_token(
        token
    )

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