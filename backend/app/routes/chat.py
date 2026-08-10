from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.dependencies import get_current_user

from app.brain.emotion import detect_emotion
from app.brain.language import detect_language
from app.brain.analyzer import detect_categories
from app.brain.planner import build_prompt
from app.brain.formatter import format_answer
from app.brain.risk import detect_risk
from app.brain.risk_response import build_risk_response
from app.brain.prompt_builder import build_full_prompt

from app.core.logger import logger

from app.brain.memory import get_user_profile
from app.brain.memory_extractor import extract_memory
from app.brain.memory_conflict import resolve_memory_update

from app.brain.conversation import (
    add_message,
    format_conversation
)

from app.brain.summary_storage import get_summary

from app.brain.summary_manager import (
    update_conversation_summary
)

from app.brain.response_style import (
    detect_response_style,
    build_response_style_prompt
)

from app.prompts.system_prompt import SYSTEM_PROMPT
from app.services.openai_service import ask_ai


router = APIRouter()


# =====================================================
# REQUEST SCHEMA
# =====================================================

class ChatRequest(BaseModel):
    message: str


# =====================================================
# CHAT
# =====================================================

@router.post("/chat")
def chat(
    data: ChatRequest,
    current_user=Depends(get_current_user)
):

    # =====================================================
    # 1. AUTHENTICATED USER
    # =====================================================

    user_id = current_user["user_id"]

    logger.info(
        "Chat request started | user_id=%s",
        user_id
    )

    # =====================================================
    # 2. USER PROFILE
    # =====================================================

    profile = get_user_profile(
        user_id
    )

    # =====================================================
    # 3. LANGUAGE
    # =====================================================

    language = detect_language(
        data.message
    )

    profile.update(
        language=language
    )

    # =====================================================
    # 4. MEMORY EXTRACTOR
    # =====================================================

    memory_data = extract_memory(
        data.message
    )

    # =====================================================
    # 5. MEMORY CONFLICT / UPDATE
    # =====================================================

    resolved_memory = resolve_memory_update(
        profile,
        memory_data
    )

    if resolved_memory:
        profile.update(
            **resolved_memory
        )

    # =====================================================
    # 6. CATEGORY V2
    # =====================================================

    category_result = detect_categories(
        data.message
    )

    category = category_result["primary"]
    secondary_categories = category_result["secondary"]

    # =====================================================
    # 7. EMOTION
    # =====================================================

    emotion = detect_emotion(
        data.message
    )

    # =====================================================
    # 8. RISK
    # =====================================================

    risk = detect_risk(
        data.message
    )

    logger.info(
        (
            "Chat analysis | user_id=%s | category=%s | "
            "secondary=%s | emotion=%s | risk=%s"
        ),
        user_id,
        category,
        secondary_categories,
        emotion,
        risk
    )

    # =====================================================
    # 9. LONG-TERM MEMORY
    # =====================================================

    memory_context = profile.get_context()

    # =====================================================
    # 10. SPECIAL RISK RESPONSE
    # =====================================================

    risk_answer = build_risk_response(
        risk=risk,
        language=language
    )

    if risk_answer is not None:

        logger.warning(
            "Safety response triggered | user_id=%s | risk=%s",
            user_id,
            risk
        )

        add_message(
            user_id,
            "user",
            data.message
        )

        add_message(
            user_id,
            "assistant",
            risk_answer
        )

        conversation_summary = get_summary(
            user_id
        )

        if not conversation_summary:
            conversation_summary = "Әңгіме summary жоқ."

        updated_recent_history = format_conversation(
            user_id,
            limit=4
        )

        logger.info(
            "Safety response completed | user_id=%s",
            user_id
        )

        return {
            "user_id": user_id,
            "language": language,
            "category": category,
            "secondary_categories": secondary_categories,
            "emotion": emotion,
            "risk": risk,
            "response_style": "safety",
            "memory": memory_context,
            "conversation_summary": conversation_summary,
            "recent_history": updated_recent_history,
            "answer": risk_answer
        }

    # =====================================================
    # 11. RESPONSE STYLE
    # =====================================================

    response_style = detect_response_style(
        data.message,
        category,
        risk,
        emotion
    )

    # =====================================================
    # 12. RESPONSE STYLE PROMPT
    # =====================================================

    response_style_prompt = build_response_style_prompt(
        response_style,
        language
    )

    # =====================================================
    # 13. BRAIN / PLANNER
    # =====================================================

    brain_prompt = build_prompt(
        category=category,
        language=language,
        secondary_categories=secondary_categories
    )

    # =====================================================
    # 14. SAVED CONVERSATION SUMMARY
    # =====================================================

    conversation_summary = get_summary(
        user_id
    )

    if not conversation_summary:
        conversation_summary = "Әңгіме summary жоқ."

    # =====================================================
    # 15. RECENT HISTORY
    # =====================================================

    recent_history = format_conversation(
        user_id,
        limit=4
    )

    # =====================================================
    # 16. FULL AI PROMPT
    # =====================================================

    full_prompt = build_full_prompt(
        system_prompt=SYSTEM_PROMPT,
        brain_prompt=brain_prompt,
        response_style_prompt=response_style_prompt,
        memory_context=memory_context,
        conversation_summary=conversation_summary,
        recent_history=recent_history,
        current_message=data.message,
        language=language,
        category=category,
        secondary_categories=secondary_categories,
        emotion=emotion,
        risk=risk,
        response_style=response_style
    )

    # =====================================================
    # 17. OPENAI
    # =====================================================

    answer = ask_ai(
        full_prompt,
        data.message,
        language=language
    )

    # =====================================================
    # 18. FORMAT
    # =====================================================

    answer = format_answer(
        answer
    )

    # =====================================================
    # 19. SAVE USER MESSAGE
    # =====================================================

    add_message(
        user_id,
        "user",
        data.message
    )

    # =====================================================
    # 20. SAVE AI ANSWER
    # =====================================================

    add_message(
        user_id,
        "assistant",
        answer
    )

    # =====================================================
    # 21. INCREMENTAL SUMMARY UPDATE
    # =====================================================

    conversation_summary = update_conversation_summary(
        user_id
    )

    # =====================================================
    # 22. UPDATED RECENT HISTORY
    # =====================================================

    updated_recent_history = format_conversation(
        user_id,
        limit=4
    )

    # =====================================================
    # 23. RESPONSE
    # =====================================================

    logger.info(
        "Chat completed | user_id=%s | response_style=%s",
        user_id,
        response_style
    )

    return {
        "user_id": user_id,
        "language": language,
        "category": category,
        "secondary_categories": secondary_categories,
        "emotion": emotion,
        "risk": risk,
        "response_style": response_style,
        "memory": memory_context,
        "conversation_summary": conversation_summary,
        "recent_history": updated_recent_history,
        "answer": answer
    }