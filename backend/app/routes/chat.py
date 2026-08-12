from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from fastapi.responses import StreamingResponse
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

from app.brain.conversation_sessions import (
    get_session,
    touch_session,
    generate_session_title,
)

from app.brain.conversation import (
    add_message,
    format_conversation,
    get_regenerate_target,
    format_conversation_before_message,
    replace_assistant_message,
)

from app.core.logger import logger

from app.brain.memory import get_user_profile
from app.brain.memory_extractor import extract_memory
from app.brain.memory_conflict import resolve_memory_update

from app.brain.summary_storage import get_summary

from app.brain.summary_manager import (
    update_conversation_summary,
)

from app.brain.response_style import (
    detect_response_style,
    detect_tone,
    build_response_style_prompt,
)

from app.prompts.system_prompt import SYSTEM_PROMPT

from app.services.openai_service import (
    ask_ai,
    stream_ai,
)


router = APIRouter()


# =====================================================
# REQUEST SCHEMAS
# =====================================================

class ChatRequest(BaseModel):
    session_id: int
    message: str


class RegenerateRequest(BaseModel):
    session_id: int


# =====================================================
# CHAT
# =====================================================

@router.post("/chat")
def chat(
    data: ChatRequest,
    current_user=Depends(get_current_user),
):

    # =====================================================
    # 1. AUTHENTICATED USER
    # =====================================================

    user_id = current_user["user_id"]

    logger.info(
        "Chat request started | user_id=%s | session_id=%s",
        user_id,
        data.session_id,
    )

    # =====================================================
    # 2. SESSION VALIDATION
    # =====================================================

    session = get_session(
        user_id=user_id,
        session_id=data.session_id,
    )

    if not session:

        logger.warning(
            (
                "Chat session not found | "
                "user_id=%s | session_id=%s"
            ),
            user_id,
            data.session_id,
        )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Әңгіме табылмады.",
        )

    # =====================================================
    # 3. AUTO SESSION TITLE
    # =====================================================

    generate_session_title(
        user_id=user_id,
        session_id=data.session_id,
        message=data.message,
    )

    # =====================================================
    # 4. USER PROFILE
    # =====================================================

    profile = get_user_profile(
        user_id,
    )

    # =====================================================
    # 5. LANGUAGE
    # =====================================================

    language = detect_language(
        data.message,
    )

    profile.update(
        language=language,
    )

    # =====================================================
    # 6. MEMORY EXTRACTOR
    # =====================================================

    memory_data = extract_memory(
        data.message,
    )

    # =====================================================
    # 7. MEMORY CONFLICT / UPDATE
    # =====================================================

    resolved_memory = resolve_memory_update(
        profile,
        memory_data,
    )

    if resolved_memory:
        profile.update(
            **resolved_memory,
        )

    # =====================================================
    # 8. CATEGORY
    # =====================================================

    category_result = detect_categories(
        data.message,
    )

    category = category_result["primary"]

    secondary_categories = (
        category_result["secondary"]
    )

    # =====================================================
    # 9. EMOTION
    # =====================================================

    emotion = detect_emotion(
        data.message,
    )

    # =====================================================
    # 10. RISK
    # =====================================================

    risk = detect_risk(
        data.message,
    )

    logger.info(
        (
            "Chat analysis | user_id=%s | session_id=%s | "
            "category=%s | secondary=%s | "
            "emotion=%s | risk=%s"
        ),
        user_id,
        data.session_id,
        category,
        secondary_categories,
        emotion,
        risk,
    )

    # =====================================================
    # 11. LONG-TERM MEMORY
    # =====================================================

    memory_context = profile.get_context()

    # =====================================================
    # 12. SPECIAL RISK RESPONSE
    # =====================================================

    risk_answer = build_risk_response(
        risk=risk,
        language=language,
    )

    if risk_answer is not None:

        logger.warning(
            (
                "Safety response triggered | "
                "user_id=%s | session_id=%s | risk=%s"
            ),
            user_id,
            data.session_id,
            risk,
        )

        add_message(
            user_id=user_id,
            role="user",
            content=data.message,
            session_id=data.session_id,
        )

        add_message(
            user_id=user_id,
            role="assistant",
            content=risk_answer,
            session_id=data.session_id,
        )

        touch_session(
            user_id=user_id,
            session_id=data.session_id,
        )

        conversation_summary = get_summary(
            user_id=user_id,
            session_id=data.session_id,
        )

        if not conversation_summary:
            conversation_summary = (
                "Әңгіме summary жоқ."
            )

        updated_recent_history = (
            format_conversation(
                user_id=user_id,
                limit=4,
                session_id=data.session_id,
            )
        )

        logger.info(
            (
                "Safety response completed | "
                "user_id=%s | session_id=%s"
            ),
            user_id,
            data.session_id,
        )

        return {
            "user_id": user_id,
            "session_id": data.session_id,
            "language": language,
            "category": category,
            "secondary_categories": secondary_categories,
            "emotion": emotion,
            "risk": risk,
            "response_style": "safety",
            "tone": "calm",
            "memory": memory_context,
            "conversation_summary": conversation_summary,
            "recent_history": updated_recent_history,
            "answer": risk_answer,
        }

    # =====================================================
    # 13. RESPONSE STYLE / TONE
    # =====================================================

    response_style = detect_response_style(
        data.message,
        category,
        risk,
        emotion,
    )

    tone = detect_tone(
        data.message,
        category,
        risk,
        emotion,
    )

    logger.info(
        (
            "ERKEK response mode | "
            "user_id=%s | session_id=%s | "
            "style=%s | tone=%s"
        ),
        user_id,
        data.session_id,
        response_style,
        tone,
    )

    # =====================================================
    # 14. RESPONSE STYLE PROMPT
    # =====================================================

    response_style_prompt = (
        build_response_style_prompt(
            response_style,
            language,
            tone=tone,
        )
    )

    # =====================================================
    # 15. BRAIN / PLANNER
    # =====================================================

    brain_prompt = build_prompt(
        category=category,
        language=language,
        secondary_categories=secondary_categories,
    )

    # =====================================================
    # 16. SAVED CONVERSATION SUMMARY
    # =====================================================

    conversation_summary = get_summary(
        user_id=user_id,
        session_id=data.session_id,
    )

    if not conversation_summary:
        conversation_summary = (
            "Әңгіме summary жоқ."
        )

    # =====================================================
    # 17. RECENT HISTORY
    # =====================================================

    recent_history = format_conversation(
        user_id=user_id,
        limit=4,
        session_id=data.session_id,
    )

    # =====================================================
    # 18. FULL AI PROMPT
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
        response_style=response_style,
    )

    # =====================================================
    # 19. OPENAI
    # =====================================================

    answer = ask_ai(
        full_prompt,
        data.message,
        language=language,
    )

    # =====================================================
    # 20. FORMAT
    # =====================================================

    answer = format_answer(
        answer,
    )

    # =====================================================
    # 21. SAVE USER MESSAGE
    # =====================================================

    add_message(
        user_id=user_id,
        role="user",
        content=data.message,
        session_id=data.session_id,
    )

    # =====================================================
    # 22. SAVE AI ANSWER
    # =====================================================

    add_message(
        user_id=user_id,
        role="assistant",
        content=answer,
        session_id=data.session_id,
    )

    # =====================================================
    # 23. SESSION UPDATED_AT
    # =====================================================

    touch_session(
        user_id=user_id,
        session_id=data.session_id,
    )

    # =====================================================
    # 24. INCREMENTAL SUMMARY UPDATE
    # =====================================================

    conversation_summary = (
        update_conversation_summary(
            user_id=user_id,
            session_id=data.session_id,
        )
    )

    # =====================================================
    # 25. UPDATED RECENT HISTORY
    # =====================================================

    updated_recent_history = (
        format_conversation(
            user_id=user_id,
            limit=4,
            session_id=data.session_id,
        )
    )

    # =====================================================
    # 26. RESPONSE
    # =====================================================

    logger.info(
        (
            "Chat completed | user_id=%s | "
            "session_id=%s | response_style=%s | tone=%s"
        ),
        user_id,
        data.session_id,
        response_style,
        tone,
    )

    return {
        "user_id": user_id,
        "session_id": data.session_id,
        "language": language,
        "category": category,
        "secondary_categories": secondary_categories,
        "emotion": emotion,
        "risk": risk,
        "response_style": response_style,
        "tone": tone,
        "memory": memory_context,
        "conversation_summary": conversation_summary,
        "recent_history": updated_recent_history,
        "answer": answer,
    }


# =====================================================
# STREAM CHAT
# =====================================================

@router.post("/chat/stream")
def stream_chat(
    data: ChatRequest,
    current_user=Depends(get_current_user),
):
    """
    ERKEK AI жауабын chunk-by-chunk streaming режимде қайтарады.
    """

    # =====================================================
    # 1. AUTHENTICATED USER
    # =====================================================

    user_id = current_user["user_id"]

    logger.info(
        (
            "Streaming chat started | "
            "user_id=%s | session_id=%s"
        ),
        user_id,
        data.session_id,
    )

    # =====================================================
    # 2. SESSION VALIDATION
    # =====================================================

    session = get_session(
        user_id=user_id,
        session_id=data.session_id,
    )

    if not session:

        logger.warning(
            (
                "Streaming chat session not found | "
                "user_id=%s | session_id=%s"
            ),
            user_id,
            data.session_id,
        )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Әңгіме табылмады.",
        )

    # =====================================================
    # 3. AUTO SESSION TITLE
    # =====================================================

    generate_session_title(
        user_id=user_id,
        session_id=data.session_id,
        message=data.message,
    )

    # =====================================================
    # 4. USER PROFILE
    # =====================================================

    profile = get_user_profile(
        user_id,
    )

    # =====================================================
    # 5. LANGUAGE
    # =====================================================

    language = detect_language(
        data.message,
    )

    profile.update(
        language=language,
    )

    # =====================================================
    # 6. MEMORY EXTRACTOR
    # =====================================================

    memory_data = extract_memory(
        data.message,
    )

    # =====================================================
    # 7. MEMORY CONFLICT / UPDATE
    # =====================================================

    resolved_memory = resolve_memory_update(
        profile,
        memory_data,
    )

    if resolved_memory:
        profile.update(
            **resolved_memory,
        )

    # =====================================================
    # 8. CATEGORY
    # =====================================================

    category_result = detect_categories(
        data.message,
    )

    category = category_result["primary"]

    secondary_categories = (
        category_result["secondary"]
    )

    # =====================================================
    # 9. EMOTION
    # =====================================================

    emotion = detect_emotion(
        data.message,
    )

    # =====================================================
    # 10. RISK
    # =====================================================

    risk = detect_risk(
        data.message,
    )

    logger.info(
        (
            "Streaming chat analysis | "
            "user_id=%s | session_id=%s | "
            "category=%s | secondary=%s | "
            "emotion=%s | risk=%s"
        ),
        user_id,
        data.session_id,
        category,
        secondary_categories,
        emotion,
        risk,
    )

    # =====================================================
    # 11. LONG-TERM MEMORY
    # =====================================================

    memory_context = profile.get_context()

    # =====================================================
    # 12. SPECIAL RISK RESPONSE
    # =====================================================

    risk_answer = build_risk_response(
        risk=risk,
        language=language,
    )

    if risk_answer is not None:

        logger.warning(
            (
                "Streaming safety response triggered | "
                "user_id=%s | session_id=%s | risk=%s"
            ),
            user_id,
            data.session_id,
            risk,
        )

        add_message(
            user_id=user_id,
            role="user",
            content=data.message,
            session_id=data.session_id,
        )

        add_message(
            user_id=user_id,
            role="assistant",
            content=risk_answer,
            session_id=data.session_id,
        )

        touch_session(
            user_id=user_id,
            session_id=data.session_id,
        )

        try:
            update_conversation_summary(
                user_id=user_id,
                session_id=data.session_id,
            )

        except Exception:
            logger.exception(
                (
                    "Streaming safety summary update failed | "
                    "user_id=%s | session_id=%s"
                ),
                user_id,
                data.session_id,
            )

        def stream_risk_answer():
            yield risk_answer

        return StreamingResponse(
            stream_risk_answer(),
            media_type="text/plain; charset=utf-8",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    # =====================================================
    # 13. RESPONSE STYLE / TONE
    # =====================================================

    response_style = detect_response_style(
        data.message,
        category,
        risk,
        emotion,
    )

    tone = detect_tone(
        data.message,
        category,
        risk,
        emotion,
    )

    logger.info(
        (
            "ERKEK streaming response mode | "
            "user_id=%s | session_id=%s | "
            "style=%s | tone=%s"
        ),
        user_id,
        data.session_id,
        response_style,
        tone,
    )

    # =====================================================
    # 14. RESPONSE STYLE PROMPT
    # =====================================================

    response_style_prompt = (
        build_response_style_prompt(
            response_style,
            language,
            tone=tone,
        )
    )

    # =====================================================
    # 15. BRAIN / PLANNER
    # =====================================================

    brain_prompt = build_prompt(
        category=category,
        language=language,
        secondary_categories=secondary_categories,
    )

    # =====================================================
    # 16. SAVED CONVERSATION SUMMARY
    # =====================================================

    conversation_summary = get_summary(
        user_id=user_id,
        session_id=data.session_id,
    )

    if not conversation_summary:
        conversation_summary = (
            "Әңгіме summary жоқ."
        )

    # =====================================================
    # 17. RECENT HISTORY
    # =====================================================

    recent_history = format_conversation(
        user_id=user_id,
        limit=4,
        session_id=data.session_id,
    )

    # =====================================================
    # 18. FULL AI PROMPT
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
        response_style=response_style,
    )

    # =====================================================
    # 19. SAVE USER MESSAGE BEFORE STREAM
    # =====================================================

    add_message(
        user_id=user_id,
        role="user",
        content=data.message,
        session_id=data.session_id,
    )

    touch_session(
        user_id=user_id,
        session_id=data.session_id,
    )

    # =====================================================
    # 20. STREAM GENERATOR
    # =====================================================

    def generate_response():
        answer_parts: list[str] = []
        stream_completed = False

        try:

            for chunk in stream_ai(
                full_prompt,
                data.message,
                language=language,
            ):
                if not chunk:
                    continue

                answer_parts.append(
                    chunk
                )

                yield chunk

            stream_completed = True

        except GeneratorExit:

            logger.info(
                (
                    "Streaming client disconnected | "
                    "user_id=%s | session_id=%s"
                ),
                user_id,
                data.session_id,
            )

            raise

        except Exception:

            logger.exception(
                (
                    "Streaming generator failed | "
                    "user_id=%s | session_id=%s"
                ),
                user_id,
                data.session_id,
            )

        finally:

            # If the client disconnects or streaming fails unexpectedly,
            # do not save an incomplete assistant response.

            if not stream_completed:
                return

            raw_answer = "".join(
                answer_parts
            )

            if not raw_answer.strip():

                logger.warning(
                    (
                        "Streaming answer empty | "
                        "user_id=%s | session_id=%s"
                    ),
                    user_id,
                    data.session_id,
                )

                return

            final_answer = format_answer(
                raw_answer,
            )

            if not final_answer:
                final_answer = raw_answer

            try:
                add_message(
                    user_id=user_id,
                    role="assistant",
                    content=final_answer,
                    session_id=data.session_id,
                )

                touch_session(
                    user_id=user_id,
                    session_id=data.session_id,
                )

            except Exception:

                logger.exception(
                    (
                        "Streaming answer save failed | "
                        "user_id=%s | session_id=%s"
                    ),
                    user_id,
                    data.session_id,
                )

                return

            try:
                update_conversation_summary(
                    user_id=user_id,
                    session_id=data.session_id,
                )

            except Exception:

                logger.exception(
                    (
                        "Streaming summary update failed | "
                        "user_id=%s | session_id=%s"
                    ),
                    user_id,
                    data.session_id,
                )

            logger.info(
                (
                    "Streaming chat completed | "
                    "user_id=%s | session_id=%s | "
                    "response_style=%s | tone=%s"
                ),
                user_id,
                data.session_id,
                response_style,
                tone,
            )

    # =====================================================
    # 21. STREAMING RESPONSE
    # =====================================================

    return StreamingResponse(
        generate_response(),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# =====================================================
# REGENERATE LAST ANSWER
# =====================================================

@router.post("/chat/regenerate")
def regenerate_chat_answer(
    data: RegenerateRequest,
    current_user=Depends(get_current_user),
):

    # =====================================================
    # 1. AUTHENTICATED USER
    # =====================================================

    user_id = current_user["user_id"]

    logger.info(
        (
            "Regenerate request started | "
            "user_id=%s | session_id=%s"
        ),
        user_id,
        data.session_id,
    )

    # =====================================================
    # 2. SESSION VALIDATION
    # =====================================================

    session = get_session(
        user_id=user_id,
        session_id=data.session_id,
    )

    if not session:

        logger.warning(
            (
                "Regenerate session not found | "
                "user_id=%s | session_id=%s"
            ),
            user_id,
            data.session_id,
        )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Әңгіме табылмады.",
        )

    # =====================================================
    # 3. FIND REGENERATE TARGET
    # =====================================================

    target = get_regenerate_target(
        user_id=user_id,
        session_id=data.session_id,
    )

    if target is None:

        logger.warning(
            (
                "Regenerate target not found | "
                "user_id=%s | session_id=%s"
            ),
            user_id,
            data.session_id,
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Қайта жауап беруге жарамды "
                "соңғы сұрақ табылмады."
            ),
        )

    user_message = target[
        "user_message"
    ]

    user_message_id = target[
        "user_message_id"
    ]

    assistant_message_id = target[
        "assistant_message_id"
    ]

    # =====================================================
    # 4. USER PROFILE
    # =====================================================

    profile = get_user_profile(
        user_id,
    )

    memory_context = profile.get_context()

    # =====================================================
    # 5. LANGUAGE
    # =====================================================

    language = detect_language(
        user_message,
    )

    # =====================================================
    # 6. CATEGORY
    # =====================================================

    category_result = detect_categories(
        user_message,
    )

    category = category_result[
        "primary"
    ]

    secondary_categories = (
        category_result["secondary"]
    )

    # =====================================================
    # 7. EMOTION
    # =====================================================

    emotion = detect_emotion(
        user_message,
    )

    # =====================================================
    # 8. RISK
    # =====================================================

    risk = detect_risk(
        user_message,
    )

    logger.info(
        (
            "Regenerate analysis | "
            "user_id=%s | session_id=%s | "
            "category=%s | secondary=%s | "
            "emotion=%s | risk=%s"
        ),
        user_id,
        data.session_id,
        category,
        secondary_categories,
        emotion,
        risk,
    )

    # =====================================================
    # 9. SAFETY RESPONSE
    # =====================================================

    risk_answer = build_risk_response(
        risk=risk,
        language=language,
    )

    if risk_answer is not None:

        replaced = replace_assistant_message(
            user_id=user_id,
            session_id=data.session_id,
            message_id=assistant_message_id,
            content=risk_answer,
        )

        if not replaced:

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Алдыңғы жауапты "
                    "ауыстыру мүмкін болмады."
                ),
            )

        touch_session(
            user_id=user_id,
            session_id=data.session_id,
        )

        logger.info(
            (
                "Safety regenerate completed | "
                "user_id=%s | session_id=%s"
            ),
            user_id,
            data.session_id,
        )

        return {
            "user_id": user_id,
            "session_id": data.session_id,
            "language": language,
            "category": category,
            "secondary_categories": secondary_categories,
            "emotion": emotion,
            "risk": risk,
            "response_style": "safety",
            "tone": "calm",
            "answer": risk_answer,
            "regenerated": True,
        }

    # =====================================================
    # 10. RESPONSE STYLE / TONE
    # =====================================================

    response_style = detect_response_style(
        user_message,
        category,
        risk,
        emotion,
    )

    tone = detect_tone(
        user_message,
        category,
        risk,
        emotion,
    )

    logger.info(
        (
            "ERKEK regenerate response mode | "
            "user_id=%s | session_id=%s | "
            "style=%s | tone=%s"
        ),
        user_id,
        data.session_id,
        response_style,
        tone,
    )

    response_style_prompt = (
        build_response_style_prompt(
            response_style,
            language,
            tone=tone,
        )
    )

    # =====================================================
    # 11. BRAIN / PLANNER
    # =====================================================

    brain_prompt = build_prompt(
        category=category,
        language=language,
        secondary_categories=secondary_categories,
    )

    # =====================================================
    # 12. SAVED SUMMARY
    # =====================================================

    conversation_summary = get_summary(
        user_id=user_id,
        session_id=data.session_id,
    )

    if not conversation_summary:
        conversation_summary = (
            "Әңгіме summary жоқ."
        )

    # =====================================================
    # 13. HISTORY BEFORE CURRENT USER MESSAGE
    # =====================================================

    recent_history = (
        format_conversation_before_message(
            user_id=user_id,
            session_id=data.session_id,
            message_id=user_message_id,
            limit=4,
        )
    )

    # =====================================================
    # 14. FULL PROMPT
    # =====================================================

    full_prompt = build_full_prompt(
        system_prompt=SYSTEM_PROMPT,
        brain_prompt=brain_prompt,
        response_style_prompt=response_style_prompt,
        memory_context=memory_context,
        conversation_summary=conversation_summary,
        recent_history=recent_history,
        current_message=user_message,
        language=language,
        category=category,
        secondary_categories=secondary_categories,
        emotion=emotion,
        risk=risk,
        response_style=response_style,
    )

    # =====================================================
    # 15. REGENERATE INSTRUCTION
    # =====================================================

    full_prompt += (
        "\n\n"
        "ADDITIONAL INSTRUCTION:\n"
        "Regenerate the answer to the user's latest message.\n"
        "Do not repeat the previous assistant response verbatim.\n"
        "Give a fresh, useful, and preferably improved answer.\n"
        "The user has not asked a new question."
    )

    # =====================================================
    # 16. OPENAI
    # =====================================================

    answer = ask_ai(
        full_prompt,
        user_message,
        language=language,
    )

    # =====================================================
    # 17. FORMAT
    # =====================================================

    answer = format_answer(
        answer,
    )

    if not answer:

        logger.error(
            (
                "Regenerate empty answer | "
                "user_id=%s | session_id=%s"
            ),
            user_id,
            data.session_id,
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Жаңа жауап алынбады.",
        )

    # =====================================================
    # 18. REPLACE OLD ASSISTANT MESSAGE
    # =====================================================

    replaced = replace_assistant_message(
        user_id=user_id,
        session_id=data.session_id,
        message_id=assistant_message_id,
        content=answer,
    )

    if not replaced:

        logger.error(
            (
                "Regenerate replace failed | "
                "user_id=%s | session_id=%s | "
                "assistant_message_id=%s"
            ),
            user_id,
            data.session_id,
            assistant_message_id,
        )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Алдыңғы жауапты "
                "ауыстыру мүмкін болмады."
            ),
        )

    # =====================================================
    # 19. SESSION UPDATED_AT
    # =====================================================

    touch_session(
        user_id=user_id,
        session_id=data.session_id,
    )

    # =====================================================
    # 20. UPDATED HISTORY
    # =====================================================

    updated_recent_history = (
        format_conversation(
            user_id=user_id,
            limit=4,
            session_id=data.session_id,
        )
    )

    # =====================================================
    # 21. RESULT
    # =====================================================

    logger.info(
        (
            "Regenerate completed | "
            "user_id=%s | session_id=%s | "
            "assistant_message_id=%s | "
            "response_style=%s | tone=%s"
        ),
        user_id,
        data.session_id,
        assistant_message_id,
        response_style,
        tone,
    )

    return {
        "user_id": user_id,
        "session_id": data.session_id,
        "language": language,
        "category": category,
        "secondary_categories": secondary_categories,
        "emotion": emotion,
        "risk": risk,
        "response_style": response_style,
        "tone": tone,
        "recent_history": updated_recent_history,
        "answer": answer,
        "regenerated": True,
    }