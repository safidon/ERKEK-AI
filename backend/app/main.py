import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core.config import (
    APP_NAME,
    APP_VERSION,
    APP_ENV,
    CORS_ORIGINS,
    IS_PRODUCTION,
    RATE_LIMIT_ENABLED,
)

from app.core.logger import logger
from app.core.rate_limit import RateLimiter, RateLimitMiddleware
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.i18n import TranslateDetailMiddleware
from app.services.alerts import install_alert_handler, send_alert
from app.telegram.reminders import reminder_loop

from app.database import (
    get_connection,
    get_database_type,
    init_database,
)

from app.routes.chat import router as chat_router
from app.routes.auth import router as auth_router
from app.routes.sessions import router as sessions_router
from app.routes.profile import router as profile_router
from app.routes.usage import router as usage_router
from app.routes.admin import router as admin_router
from app.routes.feedback import router as feedback_router
from app.routes.telegram import router as telegram_router


# =====================================================
# APP
# =====================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Application іске қосылғанда database кестелері
    # жоқ болса автоматты түрде жасалады.
    init_database()

    # Telegram еске салулары (бот қосулы болса ғана жібереді).
    reminder_task = asyncio.create_task(reminder_loop())

    yield

    reminder_task.cancel()


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    lifespan=lifespan,
    # Production-да API құжаттамасы жабық.
    docs_url=None if IS_PRODUCTION else "/docs",
    redoc_url=None if IS_PRODUCTION else "/redoc",
    openapi_url=None if IS_PRODUCTION else "/openapi.json",
)


# =====================================================
# MIDDLEWARE
# =====================================================
# Соңғы қосылған middleware ең сыртқы болады:
# Security headers -> CORS -> Rate limit -> routes.

rate_limiter = RateLimiter()

app.add_middleware(
    RateLimitMiddleware,
    limiter=rate_limiter,
    enabled=RATE_LIMIT_ENABLED,
)

# Орысша интерфейсте қате хабарламаларын аударады
# (rate limit жауабын да қамтуы үшін одан сыртта тұр).
app.add_middleware(
    TranslateDetailMiddleware,
)

app.add_middleware(
    CORSMiddleware,

    allow_origins=CORS_ORIGINS,

    allow_credentials=True,

    allow_methods=[
        "GET",
        "POST",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],

    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Lang",
    ],
)

app.add_middleware(
    SecurityHeadersMiddleware,
    hsts=IS_PRODUCTION,
)


# =====================================================
# ROUTES
# =====================================================

app.include_router(
    auth_router
)

app.include_router(
    feedback_router
)

app.include_router(
    telegram_router
)

app.include_router(
    chat_router
)

app.include_router(
    sessions_router
)

app.include_router(
    profile_router
)

app.include_router(
    usage_router
)

app.include_router(
    admin_router
)


# =====================================================
# HEALTH CHECK
# =====================================================

@app.get("/health")
def health_check():
    """Liveness: процесс жұмыс істеп тұр ма."""
    return {
        "status": "ok",
        "app": APP_NAME,
        "version": APP_VERSION,
        "environment": APP_ENV,
    }


@app.get("/health/ready")
def readiness_check():
    """Readiness: database қолжетімді ме (мониторинг үшін)."""
    try:
        connection = get_connection()

        try:
            connection.cursor().execute("SELECT 1")
        finally:
            connection.close()

    except Exception:
        logger.exception("Readiness check failed: database unavailable")

        return JSONResponse(
            status_code=503,
            content={
                "status": "unavailable",
                "database": get_database_type(),
            },
        )

    return {
        "status": "ok",
        "database": get_database_type(),
    }


# =====================================================
# HOME
# =====================================================

@app.get("/")
def home():
    return {
        "name": APP_NAME,
        "status": "online",
        "version": APP_VERSION,
    }


# =====================================================
# ҚАТЕ МОНИТОРИНГІ
# =====================================================
# ERROR логтары және күтпеген қателер әкімшінің Telegram-ына барады.

if os.getenv("ALERTS_ENABLED", "true").lower() != "false":
    install_alert_handler(logger)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled error | %s %s",
        request.method,
        request.url.path,
        exc_info=(type(exc), exc, exc.__traceback__),
    )

    return JSONResponse(
        status_code=500,
        content={"detail": "Сервер қатесі. Біраз уақыттан кейін қайталап көр."},
    )


class ClientError(BaseModel):
    message: str = Field(max_length=1000)
    stack: str | None = Field(default=None, max_length=4000)
    url: str | None = Field(default=None, max_length=500)
    user_agent: str | None = Field(default=None, max_length=300)


@app.post("/client-errors", status_code=204)
def report_client_error(data: ClientError):
    """Браузердегі (frontend) қателер. Тек әкімшіге хабар жібереді."""

    details = "\n".join(
        part
        for part in (
            data.message,
            f"URL: {data.url}" if data.url else "",
            f"Browser: {data.user_agent}" if data.user_agent else "",
            "",
            data.stack or "",
        )
        if part is not None
    ).strip()

    logger.warning("Client error | %s | %s", data.url, data.message[:200])

    if os.getenv("ALERTS_ENABLED", "true").lower() != "false":
        send_alert(
            "Frontend қатесі",
            details,
            key=f"client|{data.message[:200]}",
        )

    return Response(status_code=204)
