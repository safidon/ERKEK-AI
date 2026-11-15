from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.services.usage import get_user_usage, next_reset_at


router = APIRouter(
    prefix="/usage",
    tags=["Usage"]
)


@router.get("/me")
def my_usage(current_user=Depends(get_current_user)):
    """Бүгін қанша хабарлама жіберілді және қаншасы қалды."""

    usage = get_user_usage(current_user["user_id"])

    return {
        "used": usage.used,
        "limit": usage.limit,
        "remaining": usage.remaining,
        "resets_at": next_reset_at().isoformat(),
    }
