from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_user
from app.prompts.personas import get_user_persona
from app.services.feedback import (
    DISLIKE_REASONS,
    is_own_assistant_message,
    set_feedback,
)


router = APIRouter(
    tags=["Feedback"]
)


class FeedbackRequest(BaseModel):
    message_id: int = Field(gt=0)
    # 1 = 👍, -1 = 👎, 0 = бағаны алып тастау
    rating: int = Field(ge=-1, le=1)
    # Тек 👎 үшін: not_understood / too_long / not_useful / tone
    reason: str | None = Field(default=None, max_length=32)


@router.post("/feedback")
def submit_feedback(
    data: FeedbackRequest,
    current_user=Depends(get_current_user),
):
    user_id = current_user["user_id"]

    if not is_own_assistant_message(user_id, data.message_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Хабарлама табылмады.",
        )

    set_feedback(
        user_id=user_id,
        message_id=data.message_id,
        rating=data.rating,
        persona=get_user_persona(current_user),
        reason=data.reason,
    )

    return {
        "message_id": data.message_id,
        "rating": data.rating,
        "reason": (
            data.reason
            if data.rating == -1 and data.reason in DISLIKE_REASONS
            else None
        ),
    }
