import hmac

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status

from app.auth.dependencies import get_current_user
from app.telegram import accounts, api
from app.telegram.bot import handle_update


router = APIRouter(
    prefix="/telegram",
    tags=["Telegram"]
)


def _bot_url(start: str | None = None) -> str | None:
    username = api.bot_username()
    if not username:
        return None
    return f"https://t.me/{username}" + (f"?start={start}" if start else "")


# =====================================================
# WEBHOOK (Telegram серверлерінен)
# =====================================================

@router.post("/webhook")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    if not api.is_enabled():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    received = request.headers.get("x-telegram-bot-api-secret-token", "")

    if not hmac.compare_digest(received, api.webhook_secret()):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    try:
        update = await request.json()
    except ValueError:
        return {"ok": True}

    # Telegram-ға бірден жауап береміз, AI жауабы фонда дайындалады.
    if isinstance(update, dict):
        background_tasks.add_task(handle_update, update)

    return {"ok": True}


# =====================================================
# PUBLIC INFO (басты беттегі сілтеме үшін)
# =====================================================

@router.get("/info")
def telegram_info():
    url = _bot_url() if api.is_enabled() else None
    return {"enabled": url is not None, "url": url}


# =====================================================
# САЙТ АККАУНТЫН БАЙЛАНЫСТЫРУ
# =====================================================

@router.get("/status")
def telegram_status(current_user=Depends(get_current_user)):
    return {
        "enabled": api.is_enabled() and bool(api.bot_username()),
        "linked": accounts.get_by_user_id(current_user["user_id"]) is not None,
        "bot_url": _bot_url(),
    }


@router.post("/link")
def telegram_link(current_user=Depends(get_current_user)):
    if not (api.is_enabled() and api.bot_username()):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram бот әзірге қосылмаған.",
        )

    code = accounts.create_link_code(current_user["user_id"])

    return {
        "url": _bot_url(f"link_{code}"),
        "expires_in_minutes": accounts.LINK_CODE_MINUTES,
    }


@router.delete("/link")
def telegram_unlink(current_user=Depends(get_current_user)):
    accounts.unlink_user(current_user["user_id"])
    return {"linked": False}
