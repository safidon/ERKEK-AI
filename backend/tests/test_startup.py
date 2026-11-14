import sqlite3

from fastapi.testclient import TestClient

import app.database as database
from app.main import app


def test_startup_creates_tables(tmp_path, monkeypatch):
    """
    Application іске қосылғанда бос database-те
    кестелер автоматты түрде жасалуы керек.
    """

    db_path = tmp_path / "fresh.db"

    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        db_path,
    )

    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200

    connection = sqlite3.connect(db_path)

    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }

    connection.close()

    assert {
        "users",
        "conversation_sessions",
        "conversations",
    } <= tables
