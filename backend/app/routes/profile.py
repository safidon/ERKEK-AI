from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_user
from app.brain.memory import (
    UserProfile,
    get_user_profile,
)


router = APIRouter()


# =====================================================
# SCHEMAS
# =====================================================

class ProfileResponse(BaseModel):
    user_id: str

    language: Optional[str] = None
    age: Optional[int] = None
    marital_status: Optional[str] = None
    children: Optional[int] = None

    career: Optional[str] = None
    financial_status: Optional[str] = None
    main_goal: Optional[str] = None

    goals: list[str] = Field(
        default_factory=list
    )

    habits: list[str] = Field(
        default_factory=list
    )

    important_events: list[str] = Field(
        default_factory=list
    )


class ProfileUpdateRequest(BaseModel):
    language: Optional[str] = None
    age: Optional[int] = None
    marital_status: Optional[str] = None
    children: Optional[int] = None

    career: Optional[str] = None
    financial_status: Optional[str] = None
    main_goal: Optional[str] = None

    goals: Optional[list[str]] = None
    habits: Optional[list[str]] = None
    important_events: Optional[list[str]] = None


class ProfileMemoryDeleteRequest(BaseModel):
    fields: list[str] = Field(
        min_length=1
    )


# =====================================================
# PROFILE RESPONSE HELPER
# =====================================================

def build_profile_response(
    profile: UserProfile
) -> ProfileResponse:

    return ProfileResponse(
        user_id=profile.user_id,

        language=profile.language,
        age=profile.age,
        marital_status=profile.marital_status,
        children=profile.children,

        career=profile.career,
        financial_status=profile.financial_status,
        main_goal=profile.main_goal,

        goals=profile.goals,
        habits=profile.habits,
        important_events=profile.important_events,
    )


# =====================================================
# GET PROFILE
# =====================================================

@router.get(
    "/profile",
    response_model=ProfileResponse,
)
def get_profile(
    current_user=Depends(
        get_current_user
    )
):

    user_id = current_user[
        "user_id"
    ]

    profile = get_user_profile(
        user_id
    )

    return build_profile_response(
        profile
    )


# =====================================================
# UPDATE PROFILE
# =====================================================

@router.patch(
    "/profile",
    response_model=ProfileResponse,
)
def update_profile(
    data: ProfileUpdateRequest,
    current_user=Depends(
        get_current_user
    )
):

    user_id = current_user[
        "user_id"
    ]

    profile = get_user_profile(
        user_id
    )

    update_data = data.model_dump(
        exclude_unset=True
    )

    if update_data:
        profile.update(
            **update_data
        )

    return build_profile_response(
        profile
    )


# =====================================================
# DELETE SELECTED MEMORY FIELDS
# =====================================================

@router.delete(
    "/profile/memory",
    response_model=ProfileResponse,
)
def delete_profile_memory(
    data: ProfileMemoryDeleteRequest,
    current_user=Depends(
        get_current_user
    )
):

    user_id = current_user[
        "user_id"
    ]

    profile = get_user_profile(
        user_id
    )

    invalid_fields = [
        field
        for field in data.fields
        if field not in profile.MEMORY_FIELDS
    ]

    if invalid_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message":
                    "Белгісіз memory field табылды.",
                "invalid_fields":
                    invalid_fields,
            },
        )

    for field in data.fields:
        profile.clear_memory_field(
            field
        )

    return build_profile_response(
        profile
    )


# =====================================================
# DELETE ONE MEMORY FIELD
# =====================================================

@router.delete(
    "/profile/memory/{field_name}",
    response_model=ProfileResponse,
)
def delete_profile_memory_field(
    field_name: str,
    current_user=Depends(
        get_current_user
    )
):

    user_id = current_user[
        "user_id"
    ]

    profile = get_user_profile(
        user_id
    )

    success = profile.clear_memory_field(
        field_name
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"'{field_name}' memory field "
                "ретінде қолдау көрсетілмейді."
            ),
        )

    return build_profile_response(
        profile
    )


# =====================================================
# CLEAR ALL MEMORY
# =====================================================

@router.delete(
    "/profile/memory/all",
    response_model=ProfileResponse,
)
def clear_all_profile_memory(
    current_user=Depends(
        get_current_user
    )
):

    user_id = current_user[
        "user_id"
    ]

    profile = get_user_profile(
        user_id
    )

    profile.clear_memory()

    return build_profile_response(
        profile
    )