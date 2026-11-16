import os
import tempfile
from pathlib import Path


# =====================================================
# TEST ENVIRONMENT
# =====================================================
# app модульдері import болмай тұрып орнатылуы керек:
# тесттер нағыз database-ке жазбайды және
# OpenAI кілтінсіз де іске қосылады (OpenAI mock жасалады).

_TEST_DB_DIR = tempfile.mkdtemp(
    prefix="erkek_ai_tests_"
)

os.environ["SQLITE_PATH"] = str(
    Path(_TEST_DB_DIR) / "test.db"
)
# CI-де PostgreSQL-мен тексеру үшін TEST_DATABASE_URL беріледі.
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", "")
# Тесттер бір IP-ден көп сұраныс жібереді; лимит өз тестінде тексеріледі.
os.environ["RATE_LIMIT_ENABLED"] = "false"
# Күндік хабарлама лимиті өз тестінде тексеріледі.
os.environ["DAILY_MESSAGES_PER_USER"] = "100000"
# Қате хабарлары тесттерде жіберілмейді (өз тестінде тексеріледі).
os.environ["ALERTS_ENABLED"] = "false"
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-jwt-secret-key-for-pytest-only",
)


from app.database import init_database  # noqa: E402


init_database()
