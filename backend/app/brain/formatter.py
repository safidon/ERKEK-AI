import re


# Бұрынғы нұсқа жауапты "━━━ 🧠 ERKEK AI ━━━" жолдарымен
# қоршайтын. Ол чатта артық көрінеді және stream кезіндегі
# мәтіннен өзгеше болады, сондықтан енді сақталмайды.
# Ескі хабарламалардан да осы безендіру алынып тасталады.

_DECORATION_LINE = re.compile(
    r"^\s*(━{3,}|🧠\s*ERKEK AI)\s*$",
    re.MULTILINE,
)


def strip_decorations(text: str) -> str:
    cleaned = _DECORATION_LINE.sub("", text)

    # Безендіру алынғаннан кейін қалған бос жолдарды қысқартамыз.
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()


def format_answer(answer: str) -> str:
    """
    Модель жауабын сақтауға дайындайды:
    stream кезінде көрсетілген мәтінмен бірдей болады.
    """

    return strip_decorations(answer)
