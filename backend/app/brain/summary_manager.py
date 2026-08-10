from app.brain.summary_storage import (
    get_summary_state,
    save_summary
)

from app.brain.conversation import (
    get_messages_after,
    get_latest_message_id
)

from app.brain.conversation_summary import (
    summarize_conversation
)

from app.brain.conversation_archive import (
    archive_summarized_messages
)


SUMMARY_UPDATE_THRESHOLD = 4


# =====================================================
# FORMAT MESSAGES FOR SUMMARY
# =====================================================

def format_messages_for_summary(
    messages: list[dict]
) -> str:
    """
    Conversation message-терді summary жасауға
    ыңғайлы мәтінге айналдырады.
    """

    if not messages:
        return ""

    parts = []

    for message in messages:

        role = message["role"]
        content = message["content"]

        if role == "user":
            parts.append(
                f"Пайдаланушы: {content}"
            )

        elif role == "assistant":
            parts.append(
                f"ERKEK AI: {content}"
            )

    return "\n".join(parts)


# =====================================================
# UPDATE CONVERSATION SUMMARY
# =====================================================

def update_conversation_summary(
    user_id: str,
    force: bool = False,
    session_id: int | None = None
) -> str:
    """
    Conversation summary-ді incremental түрде жаңартады.

    session_id берілсе:
    - тек сол conversation session summary жаңартылады;
    - басқа session хабарламалары араласпайды;
    - archive те тек сол session бойынша орындалады.

    session_id берілмесе:
    - legacy user-level режим жұмыс істейді.

    Логика:
    - бұрынғы summary алады;
    - last_message_id алады;
    - тек жаңа хабарламаларды алады;
    - threshold жетсе summary жаңартады;
    - жаңа last_message_id сақтайды;
    - summary-ге кірген ескі хабарламаларды archive-ке жібереді.
    """

    # =================================================
    # 1. ҚАЗІРГІ SUMMARY STATE
    # =================================================

    state = get_summary_state(
        user_id=user_id,
        session_id=session_id
    )

    old_summary = state["summary"]
    last_message_id = state["last_message_id"]

    # =================================================
    # 2. SUMMARY-ДЕН КЕЙІНГІ ЖАҢА ХАБАРЛАМАЛАР
    # =================================================

    new_messages = get_messages_after(
        user_id=user_id,
        last_message_id=last_message_id,
        limit=20,
        session_id=session_id
    )

    # =================================================
    # 3. ЖАҢА MESSAGE ЖОҚ
    # =================================================

    if not new_messages:

        if old_summary:
            return old_summary

        return "Әңгіме summary жоқ."

    # =================================================
    # 4. THRESHOLD ЖЕТПЕСЕ
    # =================================================

    if (
        not force
        and len(new_messages) < SUMMARY_UPDATE_THRESHOLD
    ):

        if old_summary:
            return old_summary

        return "Әңгіме summary жоқ."

    # =================================================
    # 5. ЖАҢА MESSAGE-ТЕРДІ FORMAT ЖАСАУ
    # =================================================

    new_history = format_messages_for_summary(
        new_messages
    )

    # =================================================
    # 6. SUMMARY INPUT
    # =================================================

    if old_summary:

        summary_input = (
            "БҰРЫНҒЫ SUMMARY:\n"
            + old_summary
            + "\n\n"
            + "ЖАҢА ХАБАРЛАМАЛАР:\n"
            + new_history
        )

    else:

        summary_input = new_history

    # =================================================
    # 7. ЖАҢА SUMMARY
    # =================================================

    new_summary = summarize_conversation(
        summary_input
    )

    # =================================================
    # 8. SUMMARY VALIDATION
    # =================================================

    if not new_summary:
        return old_summary or "Әңгіме summary жоқ."

    if new_summary in [
        "Әңгіме summary жоқ.",
        "Әңгіме summary жасау кезінде қате шықты."
    ]:
        return old_summary or "Әңгіме summary жоқ."

    # =================================================
    # 9. СОҢҒЫ MESSAGE ID
    # =================================================

    newest_message_id = new_messages[-1]["id"]

    # =================================================
    # 10. SUMMARY STATE САҚТАУ
    # =================================================

    save_summary(
        user_id=user_id,
        summary=new_summary,
        last_message_id=newest_message_id,
        session_id=session_id
    )

    # =================================================
    # 11. AUTO ARCHIVE
    # =================================================

    try:

        archive_summarized_messages(
            user_id=user_id,
            session_id=session_id
        )

    except Exception as archive_error:

        # Archive істемей қалса да
        # summary pipeline тоқтамауы тиіс.

        print(
            f"[SUMMARY ARCHIVE ERROR] "
            f"user_id={user_id} "
            f"session_id={session_id} "
            f"error={archive_error}"
        )

    # =================================================
    # 12. RESULT
    # =================================================

    return new_summary


# =====================================================
# DEBUG STATE
# =====================================================

def get_summary_debug_state(
    user_id: str,
    session_id: int | None = None
) -> dict:
    """
    Debug үшін summary күйін көрсетеді.

    session_id берілсе,
    тек сол conversation session тексеріледі.
    """

    state = get_summary_state(
        user_id=user_id,
        session_id=session_id
    )

    latest_message_id = get_latest_message_id(
        user_id=user_id,
        session_id=session_id
    )

    pending_messages = get_messages_after(
        user_id=user_id,
        last_message_id=state["last_message_id"],
        limit=100,
        session_id=session_id
    )

    return {
        "session_id": session_id,
        "summary_exists": bool(
            state["summary"]
        ),
        "last_summarized_message_id": state[
            "last_message_id"
        ],
        "latest_message_id": latest_message_id,
        "pending_message_count": len(
            pending_messages
        )
    }