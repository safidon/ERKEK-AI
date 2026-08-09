from fastapi import APIRouter
from pydantic import BaseModel

from app.brain.emotion import detect_emotion
from app.brain.language import detect_language
from app.brain.analyzer import detect_category
from app.brain.planner import build_prompt
from app.brain.formatter import format_answer
from app.brain.risk import detect_risk
from app.brain.risk_response import build_risk_response

from app.brain.memory import get_user_profile
from app.brain.memory_extractor import extract_memory

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


class ChatRequest(BaseModel):
    user_id: str
    message: str


@router.post("/chat")
def chat(data: ChatRequest):

    # =====================================================
    # 1. USER PROFILE
    # =====================================================

    profile = get_user_profile(
        data.user_id
    )

    # =====================================================
    # 2. LANGUAGE
    # =====================================================

    language = detect_language(
        data.message
    )

    profile.update(
        language=language
    )

    # =====================================================
    # 3. MEMORY EXTRACTOR
    # =====================================================

    memory_data = extract_memory(
        data.message
    )

    if memory_data:
        profile.update(
            **memory_data
        )

    # =====================================================
    # 4. CATEGORY
    # =====================================================

    category = detect_category(
        data.message
    )

    # =====================================================
    # 5. EMOTION
    # =====================================================

    emotion = detect_emotion(
        data.message
    )

    # =====================================================
    # 6. RISK
    # =====================================================

    risk = detect_risk(
        data.message
    )

    # =====================================================
    # 7. LONG-TERM MEMORY
    # =====================================================

    memory_context = profile.get_context()

    # =====================================================
    # 8. SPECIAL RISK RESPONSE
    # =====================================================

    risk_answer = build_risk_response(
        risk=risk,
        language=language
    )

    # HIGH немесе CRITICAL болса,
    # кәдімгі OpenAI pipeline іске қосылмайды.
    if risk_answer is not None:

        # User message сақтау
        add_message(
            data.user_id,
            "user",
            data.message
        )

        # Safety response сақтау
        add_message(
            data.user_id,
            "assistant",
            risk_answer
        )

        # Safety режимінде summary жасау үшін
        # қосымша OpenAI request жібермейміз.
        conversation_summary = get_summary(
            data.user_id
        )

        if not conversation_summary:
            conversation_summary = "Әңгіме summary жоқ."

        updated_recent_history = format_conversation(
            data.user_id,
            limit=4
        )

        return {
            "user_id": data.user_id,
            "language": language,
            "category": category,
            "emotion": emotion,
            "risk": risk,
            "response_style": "safety",
            "memory": memory_context,
            "conversation_summary": conversation_summary,
            "recent_history": updated_recent_history,
            "answer": risk_answer
        }

    # =====================================================
    # 9. RESPONSE STYLE
    # =====================================================

    response_style = detect_response_style(
        data.message,
        category,
        risk,
        emotion
    )

    # =====================================================
    # 10. RESPONSE STYLE PROMPT
    # =====================================================

    response_style_prompt = build_response_style_prompt(
        response_style,
        language
    )

    # =====================================================
    # 11. BRAIN / PLANNER
    # =====================================================

    brain_prompt = build_prompt(
        category,
        language
    )

    # =====================================================
    # 12. SAVED CONVERSATION SUMMARY
    # =====================================================

    conversation_summary = get_summary(
        data.user_id
    )

    if not conversation_summary:
        conversation_summary = "Әңгіме summary жоқ."

    # =====================================================
    # 13. RECENT HISTORY
    # =====================================================

    recent_history = format_conversation(
        data.user_id,
        limit=4
    )

    # =====================================================
    # 14. FULL AI PROMPT
    # =====================================================

    full_prompt = (
        SYSTEM_PROMPT
        + "\n\n"

        + brain_prompt
        + "\n\n"

        + response_style_prompt
        + "\n\n"

        + "ПАЙДАЛАНУШЫНЫҢ ҰЗАҚ МЕРЗІМДІ MEMORY-СІ:\n"
        + memory_context
        + "\n\n"

        + "БҰРЫНҒЫ ӘҢГІМЕНІҢ ҚЫСҚА SUMMARY-СІ:\n"
        + conversation_summary
        + "\n\n"

        + "СОҢҒЫ 4 ХАБАРЛАМА:\n"
        + recent_history
        + "\n\n"

        + "ҚАЗІРГІ ХАБАРЛАМА:\n"
        + data.message
        + "\n\n"

        + f"ТІЛІ: {language}\n"
        + f"КАТЕГОРИЯСЫ: {category}\n"
        + f"ЭМОЦИЯ ДЕҢГЕЙІ: {emotion}\n"
        + f"ҚАУІП ДЕҢГЕЙІ: {risk}\n"
        + f"ЖАУАП СТИЛІ: {response_style}"
    )

    # =====================================================
    # 15. OPENAI
    # =====================================================

    answer = ask_ai(
        full_prompt,
        data.message
    )

    # =====================================================
    # 16. FORMAT
    # =====================================================

    answer = format_answer(
        answer
    )

    # =====================================================
    # 17. SAVE USER MESSAGE
    # =====================================================

    add_message(
        data.user_id,
        "user",
        data.message
    )

    # =====================================================
    # 18. SAVE AI ANSWER
    # =====================================================

    add_message(
        data.user_id,
        "assistant",
        answer
    )

    # =====================================================
    # 19. INCREMENTAL SUMMARY UPDATE
    # =====================================================

    # summary_manager өзі:
    #
    # - бұрынғы summary-ді алады
    # - last_message_id қарайды
    # - тек жаңа messages алады
    # - threshold жетсе жаңартады
    # - SQLite-ке жаңа last_message_id сақтайды

    conversation_summary = update_conversation_summary(
        data.user_id
    )

    # =====================================================
    # 20. UPDATED RECENT HISTORY
    # =====================================================

    updated_recent_history = format_conversation(
        data.user_id,
        limit=4
    )

    # =====================================================
    # 21. RESPONSE
    # =====================================================

    return {
        "user_id": data.user_id,
        "language": language,
        "category": category,
        "emotion": emotion,
        "risk": risk,
        "response_style": response_style,
        "memory": memory_context,
        "conversation_summary": conversation_summary,
        "recent_history": updated_recent_history,
        "answer": answer
    }