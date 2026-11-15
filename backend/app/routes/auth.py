from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from app.core.logger import logger

from app.auth.account import delete_account
from app.auth.consents import record_consents
from app.auth.dependencies import get_current_user
from app.auth.security import verify_password

from app.auth.jwt import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
)

from app.auth.sessions import (
    create_session,
    revoke_session_by_refresh_token,
    rotate_refresh_token,
)

from app.auth.password_reset import (
    request_password_reset,
    reset_password,
)

from app.auth.service import (
    create_user,
    authenticate_user
)


router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


# =====================================================
# SCHEMAS
# =====================================================

class RegisterRequest(BaseModel):
    email: EmailStr

    username: str = Field(
        min_length=3,
        max_length=30
    )

    password: str = Field(
        min_length=8,
        max_length=128
    )

    # Пайдалану шарттары, құпиялылық саясаты, деректерді шетелге
    # (OpenAI) беру және 18 жастан асқаны туралы келісім.
    accept_terms: bool = False


class RegisterResponse(BaseModel):
    user_id: str
    email: str
    username: str
    is_active: bool


class LoginRequest(BaseModel):
    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128
    )


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str
    # Access token қанша секунд жарамды
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str = Field(
        min_length=20,
        max_length=200
    )


def _issue_tokens(user_id: str, session_id: str, refresh_token: str) -> dict:
    return {
        "access_token": create_access_token(
            user_id=user_id,
            session_id=session_id,
        ),
        "token_type": "bearer",
        "refresh_token": refresh_token,
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


# =====================================================
# REGISTER
# =====================================================

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED
)
def register(data: RegisterRequest):

    logger.info(
        "Register request | email=%s | username=%s",
        data.email,
        data.username
    )

    if not data.accept_terms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Тіркелу үшін пайдалану шарттары мен "
                "құпиялылық саясатына келісу керек."
            )
        )

    try:

        user = create_user(
            email=str(data.email),
            username=data.username,
            password=data.password
        )

        record_consents(
            user["user_id"]
        )

        logger.info(
            "User registered | user_id=%s | username=%s",
            user["user_id"],
            user["username"]
        )

        return user

    except ValueError as error:

        logger.warning(
            "Register rejected | username=%s | reason=%s",
            data.username,
            str(error)
        )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )

    except Exception:

        logger.exception(
            "Register unexpected error | username=%s",
            data.username
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Тіркелу кезінде сервер қатесі пайда болды."
        )


# =====================================================
# LOGIN
# =====================================================

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK
)
def login(data: LoginRequest):

    logger.info(
        "Login request | email=%s",
        data.email
    )

    try:

        user = authenticate_user(
            email=str(data.email),
            password=data.password
        )

        if not user:

            logger.warning(
                "Login failed | email=%s",
                data.email
            )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email немесе пароль қате.",
                headers={
                    "WWW-Authenticate": "Bearer"
                }
            )

        session_id, refresh_token = create_session(
            user["user_id"]
        )

        logger.info(
            "Login successful | user_id=%s",
            user["user_id"]
        )

        return _issue_tokens(
            user["user_id"],
            session_id,
            refresh_token,
        )

    except HTTPException:
        raise

    except Exception:

        logger.exception(
            "Login unexpected error | email=%s",
            data.email
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Кіру кезінде сервер қатесі пайда болды."
        )

# =====================================================
# FORGOT PASSWORD
# =====================================================

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(
        min_length=20,
        max_length=200
    )

    password: str = Field(
        min_length=8,
        max_length=128
    )


FORGOT_PASSWORD_MESSAGE = (
    "Егер бұл email тіркелген болса, "
    "құпиясөзді қалпына келтіру сілтемесі жіберілді."
)


@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK
)
def forgot_password(
    data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
):
    # Email тіркелген-тіркелмегеніне қарамастан жауап бірдей:
    # бөгде адам кімнің аккаунты бар екенін біле алмайды.
    # Хат фонда жіберіледі, сондықтан жауап уақыты да бірдей.
    background_tasks.add_task(
        _safe_request_password_reset,
        str(data.email),
    )

    return {
        "detail": FORGOT_PASSWORD_MESSAGE
    }


def _safe_request_password_reset(email: str) -> None:
    try:
        request_password_reset(email)
    except Exception:
        logger.exception("Password reset request failed")


# =====================================================
# RESET PASSWORD
# =====================================================

@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK
)
def reset_password_endpoint(data: ResetPasswordRequest):

    try:
        changed = reset_password(
            token=data.token,
            new_password=data.password
        )

    except Exception:
        logger.exception("Password reset unexpected error")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Құпиясөзді ауыстыру кезінде сервер қатесі пайда болды."
        )

    if not changed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Сілтеме жарамсыз немесе мерзімі өтіп кеткен. "
                "Қалпына келтіруді қайта сұра."
            )
        )

    return {
        "detail": "Құпиясөз ауыстырылды. Енді жаңа құпиясөзбен кір."
    }


# =====================================================
# REFRESH
# =====================================================

@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK
)
def refresh(data: RefreshRequest):
    """
    Refresh token арқылы жаңа access token береді.
    Refresh token-нің өзі де ауысады (ескісі енді жарамсыз).
    """

    try:
        result = rotate_refresh_token(
            data.refresh_token
        )

    except Exception:
        logger.exception("Token refresh unexpected error")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Сессияны жаңарту кезінде сервер қатесі пайда болды."
        )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Сессия аяқталды. Қайта кір.",
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )

    user_id, session_id, new_refresh_token = result

    return _issue_tokens(
        user_id,
        session_id,
        new_refresh_token,
    )


# =====================================================
# LOGOUT
# =====================================================

@router.post(
    "/logout",
    status_code=status.HTTP_200_OK
)
def logout(data: RefreshRequest):
    """Осы құрылғыдағы сессияны жабады."""

    try:
        revoke_session_by_refresh_token(
            data.refresh_token
        )

    except Exception:
        logger.exception("Logout unexpected error")

    return {
        "detail": "Шықтың."
    }


# =====================================================
# DELETE ACCOUNT
# =====================================================

class DeleteAccountRequest(BaseModel):
    password: str = Field(
        min_length=1,
        max_length=128
    )


@router.post(
    "/delete-account",
    status_code=status.HTTP_200_OK
)
def delete_account_endpoint(
    data: DeleteAccountRequest,
    current_user=Depends(get_current_user),
):
    """
    Аккаунтты және барлық деректерді біржола өшіреді.
    Қауіпсіздік үшін құпиясөз қайта сұралады.
    """

    if not verify_password(
        data.password,
        current_user["password_hash"]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Құпиясөз қате."
        )

    try:
        delete_account(
            current_user["user_id"]
        )

    except Exception:
        logger.exception(
            "Account deletion failed | user_id=%s",
            current_user["user_id"]
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Аккаунтты жою кезінде сервер қатесі пайда болды."
        )

    return {
        "detail": "Аккаунтың және барлық деректерің жойылды."
    }
