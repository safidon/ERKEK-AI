def build_full_prompt(
    system_prompt: str,
    brain_prompt: str,
    response_style_prompt: str,
    memory_context: str,
    conversation_summary: str,
    recent_history: str,
    current_message: str,
    language: str,
    category: str,
    secondary_categories: list[str],
    emotion: int,
    risk: str,
    response_style: str
) -> str:
    """
    ERKEK AI үшін OpenAI-ға жіберілетін
    толық prompt-ты құрастырады.
    """

    secondary_text = (
        ", ".join(secondary_categories)
        if secondary_categories
        else "жоқ"
    )

    return (
        system_prompt
        + "\n\n"

        + brain_prompt
        + "\n\n"

        + response_style_prompt
        + "\n\n"

        + "КОНТЕКСТ:\n"

        + "ҰЗАҚ МЕРЗІМДІ MEMORY:\n"
        + memory_context
        + "\n\n"

        + "ӘҢГІМЕ SUMMARY:\n"
        + conversation_summary
        + "\n\n"

        + "СОҢҒЫ ХАБАРЛАМАЛАР:\n"
        + recent_history
        + "\n\n"

        + "ҚАЗІРГІ ХАБАРЛАМА:\n"
        + current_message
        + "\n\n"

        + "ТЕХНИКАЛЫҚ КОНТЕКСТ:\n"
        + f"language={language}\n"
        + f"primary_category={category}\n"
        + f"secondary_categories={secondary_text}\n"
        + f"emotion={emotion}\n"
        + f"risk={risk}\n"
        + f"response_style={response_style}"
    )