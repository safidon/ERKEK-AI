from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from app.core.logger import logger

from app.auth.jwt import create_access_token

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

    try:

        user = create_user(
            email=str(data.email),
            username=data.username,
            password=data.password
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

        access_token = create_access_token(
            user_id=user["user_id"]
        )

        logger.info(
            "Login successful | user_id=%s",
            user["user_id"]
        )

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

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