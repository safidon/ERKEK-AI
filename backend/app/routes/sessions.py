from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_user

from app.brain.conversation_sessions import (
    create_session,
    get_session,
    list_sessions,
    rename_session,
    delete_session,
    get_session_messages
)

from app.core.logger import logger


router = APIRouter(
    prefix="/sessions",
    tags=["Sessions"]
)


# =====================================================
# SCHEMAS
# =====================================================

class CreateSessionRequest(BaseModel):
    title: str = Field(
        default="Жаңа әңгіме",
        min_length=1,
        max_length=100
    )


class RenameSessionRequest(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=100
    )


# =====================================================
# CREATE SESSION
# =====================================================

@router.post(
    "",
    status_code=status.HTTP_201_CREATED
)
def create_conversation_session(
    data: CreateSessionRequest,
    current_user=Depends(get_current_user)
):

    user_id = current_user["user_id"]

    session = create_session(
        user_id=user_id,
        title=data.title
    )

    logger.info(
        "Conversation session created | user_id=%s | session_id=%s",
        user_id,
        session["id"]
    )

    return session


# =====================================================
# LIST SESSIONS
# =====================================================

@router.get("")
def get_conversation_sessions(
    current_user=Depends(get_current_user)
):

    user_id = current_user["user_id"]

    return list_sessions(
        user_id=user_id
    )


# =====================================================
# GET ONE SESSION
# =====================================================

@router.get("/{session_id}")
def get_conversation_session(
    session_id: int,
    current_user=Depends(get_current_user)
):

    user_id = current_user["user_id"]

    session = get_session(
        user_id=user_id,
        session_id=session_id
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Әңгіме табылмады."
        )

    messages = get_session_messages(
        user_id=user_id,
        session_id=session_id
    )

    return {
        "id": session["id"],
        "title": session["title"],
        "is_active": bool(
            session["is_active"]
        ),
        "created_at": session["created_at"],
        "updated_at": session["updated_at"],
        "messages": messages
    }


# =====================================================
# RENAME SESSION
# =====================================================

@router.patch("/{session_id}")
def update_conversation_session(
    session_id: int,
    data: RenameSessionRequest,
    current_user=Depends(get_current_user)
):

    user_id = current_user["user_id"]

    success = rename_session(
        user_id=user_id,
        session_id=session_id,
        title=data.title
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Әңгіме табылмады."
        )

    return {
        "success": True,
        "session_id": session_id,
        "title": data.title.strip()
    }


# =====================================================
# DELETE SESSION
# =====================================================

@router.delete(
    "/{session_id}",
    status_code=status.HTTP_200_OK
)
def remove_conversation_session(
    session_id: int,
    current_user=Depends(get_current_user)
):

    user_id = current_user["user_id"]

    success = delete_session(
        user_id=user_id,
        session_id=session_id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Әңгіме табылмады."
        )

    logger.info(
        "Conversation session deleted | user_id=%s | session_id=%s",
        user_id,
        session_id
    )

    return {
        "success": True,
        "session_id": session_id
    }