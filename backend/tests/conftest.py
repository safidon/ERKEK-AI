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
os.environ["DATABASE_URL"] = ""
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-jwt-secret-key-for-pytest-only",
)


from app.database import init_database  # noqa: E402


init_database()
