from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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

from app.database import (
    get_connection,
    get_database_type,
    init_database,
)

from app.routes.chat import router as chat_router
from app.routes.auth import router as auth_router
from app.routes.sessions import router as sessions_router
from app.routes.profile import router as profile_router


# =====================================================
# APP
# =====================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Application іске қосылғанда database кестелері
    # жоқ болса автоматты түрде жасалады.
    init_database()
    yield


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
    chat_router
)

app.include_router(
    sessions_router
)

app.include_router(
    profile_router
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
