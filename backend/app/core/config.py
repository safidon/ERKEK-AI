from dotenv import load_dotenv
import os


# =====================================================
# ENVIRONMENT
# =====================================================

load_dotenv()


# =====================================================
# APPLICATION
# =====================================================

APP_NAME = os.getenv(
    "APP_NAME",
    "ERKEK AI"
)

APP_VERSION = os.getenv(
    "APP_VERSION",
    "1.0.0"
)


# =====================================================
# OPENAI
# =====================================================

OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY"
)


# =====================================================
# JWT / AUTH
# =====================================================

JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY"
)


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