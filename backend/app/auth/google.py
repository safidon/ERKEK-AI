"""
Google арқылы кіру (Google Identity Services, ID token).

Браузер Google-дан ID token (JWT) алады да, бізге жібереді.
Біз оны Google-дың ашық кілттерімен тексереміз:
- қолтаңба (RS256), aud = GOOGLE_CLIENT_ID, iss = accounts.google.com,
- мерзімі, email_verified = true.
GOOGLE_CLIENT_ID берілмесе — Google арқылы кіру өшірулі.
"""

import os
import re
import secrets
import time
import uuid

import httpx
from jose import jwt

from app.auth.service import get_user_by_email, get_user_by_username
from app.database import adapt_query, get_connection


GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUERS = ("accounts.google.com", "https://accounts.google.com")

_certs_cache: dict = {"keys": None, "expires": 0.0}


class GoogleAuthError(Exception):
    pass


def google_client_id() -> str:
    return os.getenv("GOOGLE_CLIENT_ID", "").strip()


def is_enabled() -> bool:
    return bool(google_client_id())


def _google_keys() -> dict:
    now = time.time()

    if _certs_cache["keys"] and _certs_cache["expires"] > now:
        return _certs_cache["keys"]

    response = httpx.get(GOOGLE_CERTS_URL, timeout=10)
    response.raise_for_status()

    max_age = 3600
    match = re.search(r"max-age=(\d+)", response.headers.get("cache-control", ""))
    if match:
        max_age = int(match.group(1))

    _certs_cache["keys"] = response.json()
    _certs_cache["expires"] = now + max_age

    return _certs_cache["keys"]


def verify_id_token(credential: str) -> dict:
    """Тексерілген claims қайтарады, әйтпесе GoogleAuthError."""

    client_id = google_client_id()

    if not client_id:
        raise GoogleAuthError("disabled")

    try:
        claims = jwt.decode(
            credential,
            _google_keys(),
            algorithms=["RS256"],
            audience=client_id,
            options={"verify_at_hash": False},
        )
    except Exception as error:
        raise GoogleAuthError("invalid token") from error

    if claims.get("iss") not in GOOGLE_ISSUERS:
        raise GoogleAuthError("wrong issuer")

    if not claims.get("email") or not claims.get("email_verified"):
        raise GoogleAuthError("email not verified")

    return claims


def _unique_username(email: str) -> str:
    base = re.sub(r"[^a-zA-Z0-9_]", "", email.split("@")[0])[:20] or "user"
    if len(base) < 3:
        base = f"{base}user"

    candidate = base
    while get_user_by_username(candidate):
        candidate = f"{base}{secrets.randbelow(10000)}"

    return candidate


def create_google_user(email: str, given_name: str | None) -> dict:
    """Құпиясөзсіз аккаунт ашады (кейін құпиясөзді қалпына келтіру арқылы қоюға болады)."""

    email = email.strip().lower()
    user_id = str(uuid.uuid4())
    username = _unique_username(email)
    display_name = (given_name or "").strip()[:40] or None

    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute(
            adapt_query(
                """
                INSERT INTO users (user_id, email, username, password_hash, is_active, display_name)
                VALUES (?, ?, ?, NULL, 1, ?)
                """
            ),
            (user_id, email, username, display_name),
        )
        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    return {
        "user_id": user_id,
        "email": email,
        "username": username,
    }


def find_user(email: str):
    return get_user_by_email(email.strip().lower())
