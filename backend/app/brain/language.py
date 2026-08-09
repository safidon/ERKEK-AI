def detect_language(text: str) -> str:
    """
    Пайдаланушының мәтін тілін анықтайды.
    Нәтиже: 'kk', 'ru' немесе 'other'
    """

    kazakh_letters = set("әіңғүұқөһ")
    text_lower = text.lower()

    # Қазақ тіліне тән әріптер кездессе
    if any(letter in text_lower for letter in kazakh_letters):
        return "kk"

    # Қарапайым орысша сөздер арқылы анықтау
    russian_words = {
        "я", "мне", "меня", "моя", "мой", "жена",
        "семья", "развод", "деньги", "работа",
        "сын", "дочь", "дети", "отец", "муж",
        "помоги", "что", "как", "почему"
    }

    words = set(text_lower.split())

    if words.intersection(russian_words):
        return "ru"

    return "other"