from app.services.openai_service import ask_ai


SUMMARY_PROMPT = """
Сен ERKEK AI жүйесінің Conversation Summarizer модулісің.

Міндетің:
Берілген әңгімеден тек келесі диалогтарға пайдалы қысқа контекст жаса.

Ережелер:
1. Артық детальды алып таста.
2. AI берген ұзын әрекет жоспарларын толық көшірме.
3. Пайдаланушы туралы нақты фактілерді сақта.
4. Пайдаланушының негізгі мәселесін сақта.
5. Пайдаланушының негізгі мақсатын сақта.
6. Соңғы маңызды эмоциялық жағдайды қысқаша сақта.
7. Болжам жасама.
8. Максимум 6 қысқа жол жаз.
9. Тек таза мәтін қайтар.
10. Қазақша контекст болса қазақша, орысша болса орысша жаз.

Мысал:

Пайдаланушы жұмыс тұрақсыз екенін айтты.
Оның 2 баласы бар.
Жұмыстың тұрақсыздығы балалардың болашағына байланысты алаңдатады.
Негізгі мақсаты — тұрақты жұмыс табу.
"""


def summarize_conversation(conversation_text: str) -> str:
    """
    Ұзын conversation history-ді қысқа summary-ге айналдырады.
    """

    if not conversation_text:
        return "Әңгіме summary жоқ."

    if conversation_text.strip() == "Бұрынғы әңгіме жоқ.":
        return "Әңгіме summary жоқ."

    try:
        summary = ask_ai(
            SUMMARY_PROMPT,
            conversation_text
        )

        summary = summary.strip()

        if not summary:
            return "Әңгіме summary жоқ."

        return summary

    except Exception:
        return "Әңгіме summary жасау кезінде қате шықты."