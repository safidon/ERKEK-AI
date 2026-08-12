from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import (
    APP_NAME,
    APP_VERSION,
    APP_ENV,
    CORS_ORIGINS,
)

from app.routes.chat import router as chat_router
from app.routes.auth import router as auth_router
from app.routes.sessions import router as sessions_router
from app.routes.profile import router as profile_router


# =====================================================
# APP
# =====================================================

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
)


# =====================================================
# CORS
# =====================================================

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
    return {
        "status": "ok",
        "app": APP_NAME,
        "version": APP_VERSION,
        "environment": APP_ENV,
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
        "environment": APP_ENV,
    }