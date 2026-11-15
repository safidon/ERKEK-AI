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


# =====================================================
# EMAIL (SMTP)
# =====================================================
# Құпиясөзді қалпына келтіру хаттары үшін.
# SMTP_HOST бос болса, dev режимінде хаттың сілтемесі
# логқа жазылады (хат жіберілмейді).

SMTP_HOST = os.getenv("SMTP_HOST", "").strip()

try:
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
except ValueError:
    SMTP_PORT = 587

SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER).strip()

# "starttls" (587 порт), "ssl" (465 порт) немесе "none"
SMTP_SECURITY = os.getenv("SMTP_SECURITY", "starttls").strip().lower()

try:
    PASSWORD_RESET_EXPIRE_MINUTES = int(
        os.getenv("PASSWORD_RESET_EXPIRE_MINUTES", "30")
    )
except ValueError:
    PASSWORD_RESET_EXPIRE_MINUTES = 30


# =====================================================
# RATE LIMITING
# =====================================================

RATE_LIMIT_ENABLED = os.getenv(
    "RATE_LIMIT_ENABLED",
    "true",
).strip().lower() not in ("0", "false", "no", "off")


if IS_PRODUCTION:
    if len(JWT_SECRET_KEY) < 32:
        raise RuntimeError(
            "Production режимінде JWT_SECRET_KEY кемінде 32 таңба болуы керек."
        )

    if JWT_SECRET_KEY.startswith("your_"):
        raise RuntimeError(
            "Production режимінде JWT_SECRET_KEY мысал мәні болмауы керек."
        )

    if any(
        "localhost" in origin or "127.0.0.1" in origin
        for origin in CORS_ORIGINS
    ):
        raise RuntimeError(
            "Production режимінде CORS_ORIGINS ішінде localhost болмауы керек."
        )

    if not FRONTEND_URL.startswith("https://"):
        raise RuntimeError(
            "Production режимінде FRONTEND_URL HTTPS болуы керек."
        )

    if not BACKEND_URL.startswith("https://"):
        raise RuntimeError(
            "Production режимінде BACKEND_URL HTTPS болуы керек."
        )