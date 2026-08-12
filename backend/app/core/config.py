from dotenv import load_dotenv
import os


# =====================================================
# ENVIRONMENT
# =====================================================

load_dotenv()


APP_ENV = os.getenv(
    "APP_ENV",
    "development",
).lower()


IS_PRODUCTION = (
    APP_ENV == "production"
)


# =====================================================
# APPLICATION
# =====================================================

APP_NAME = os.getenv(
    "APP_NAME",
    "ERKEK AI",
)

APP_VERSION = os.getenv(
    "APP_VERSION",
    "1.0.0",
)


# =====================================================
# URLS
# =====================================================

FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost:3000",
)

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://127.0.0.1:8000",
)


# =====================================================
# DATABASE
# =====================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "",
)


# =====================================================
# OPENAI
# =====================================================

OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY",
)


# =====================================================
# JWT / AUTH
# =====================================================

JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
)


# =====================================================
# CORS
# =====================================================

CORS_ORIGINS_RAW = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000",
)

CORS_ORIGINS = [
    origin.strip()
    for origin in CORS_ORIGINS_RAW.split(",")
    if origin.strip()
]


# =====================================================
# VALIDATION
# =====================================================

if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY .env файлынан табылмады."
    )


if not JWT_SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY .env файлынан табылмады."
    )


if IS_PRODUCTION:
    if not FRONTEND_URL.startswith("https://"):
        raise RuntimeError(
            "Production режимінде FRONTEND_URL HTTPS болуы керек."
        )

    if not BACKEND_URL.startswith("https://"):
        raise RuntimeError(
            "Production режимінде BACKEND_URL HTTPS болуы керек."
        )