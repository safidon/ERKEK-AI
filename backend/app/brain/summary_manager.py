from app.brain.summary_storage import (
    get_summary_state,
    save_summary
)

from app.brain.conversation import (
    get_messages_after
)

from app.brain.conversation_summary import (
    summarize_conversation
)


SUMMARY_UPDATE_THRESHOLD = 4


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


def update_conversation_summary(
    user_id: str,
    force: bool = False
) -> str:
    """
    Conversation summary-ді incremental түрде жаңартады.

    Ескі summary-ді алады.
    Тек одан кейін келген жаңа хабарламаларды қосады.
    Содан кейін жаңартылған summary-ді базаға сақтайды.
    """

    # 1. Қазіргі summary күйі
    state = get_summary_state(
        user_id
    )

    old_summary = state["summary"]
    last_message_id = state["last_message_id"]

    # 2. Summary-ден кейінгі жаңа хабарламалар
    new_messages = get_messages_after(
        user_id,
        last_message_id
    )

    # Жаңа хабарлама жоқ
    if not new_messages:

        if old_summary:
            return old_summary

        return "Әңгіме summary жоқ."

    # 3. Хабарлама аз болса summary-ді әзірге жаңартпаймыз
    if (
        not force
        and old_summary is not None
        and len(new_messages) < SUMMARY_UPDATE_THRESHOLD
    ):
        return old_summary

    # 4. Жаңа хабарламаларды мәтінге айналдыру
    new_history = format_messages_for_summary(
        new_messages
    )

    # 5. Алғашқы summary болса
    if not old_summary:

        summary_input = new_history

    else:

        summary_input = (
            "БҰРЫНҒЫ SUMMARY:\n"
            + old_summary
            + "\n\n"
            + "ЖАҢА ХАБАРЛАМАЛАР:\n"
            + new_history
        )

    # 6. Жаңа summary жасау
    new_summary = summarize_conversation(
        summary_input
    )

    # 7. Summary қай message-ге дейін жеткенін анықтау
    newest_message_id = new_messages[-1]["id"]

    # 8. SQLite-қа сақтау
    save_summary(
        user_id=user_id,
        summary=new_summary,
        last_message_id=newest_message_id
    )

    return new_summary