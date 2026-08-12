def detect_response_style(
    message: str,
    category: str,
    risk: str,
    emotion: int
) -> str:
    """
    Жауаптың көлемі мен тереңдігін анықтайды.

    Нәтиже:
    - short
    - normal
    - deep
    """

    text = message.strip()
    text_lower = text.lower()

    # =====================================================
    # 1. HIGH RISK
    # =====================================================

    if risk in ["high", "critical"]:
        return "normal"

    # =====================================================
    # 2. USER EXPLICITLY REQUESTS DETAIL
    # =====================================================

    deep_words = [
        # Қазақша
        "толық талда",
        "толық жоспар",
        "егжей-тегжейлі",
        "нақты жоспар құр",
        "жан-жақты",
        "толық түсіндір",

        # Орысша
        "подробно",
        "полный план",
        "подробный план",
        "детально",
        "разбери подробно",
        "полный анализ",
    ]

    if any(
        word in text_lower
        for word in deep_words
    ):
        return "deep"

    # =====================================================
    # 3. VERY SHORT MESSAGE
    # =====================================================

    if len(text) <= 90:
        return "short"

    # =====================================================
    # 4. STRONG EMOTION
    # =====================================================

    if emotion >= 60:
        return "normal"

    # =====================================================
    # 5. COMPLEX CATEGORY + LONG MESSAGE
    # =====================================================

    complex_categories = {
        "relationship",
        "finance",
        "fatherhood",
        "business",
    }

    if (
        category in complex_categories
        and len(text) >= 250
    ):
        return "deep"

    # =====================================================
    # DEFAULT
    # =====================================================

    return "normal"


# =========================================================
# TONE DETECTION
# =========================================================

def detect_tone(
    message: str,
    category: str,
    risk: str,
    emotion: int
) -> str:
    """
    ERKEK AI мінезінің интенсивтілігін анықтайды.

    Нәтиже:
    - calm
    - direct
    - alpha
    - hard
    """

    text = message.strip().lower()

    # =====================================================
    # 1. SAFETY OVERRIDES PERSONA
    # =====================================================

    if risk in ["high", "critical"]:
        return "calm"

    # =====================================================
    # 2. STRONG EMOTIONAL DISTRESS
    # =====================================================

    if emotion >= 75:
        return "calm"

    # =====================================================
    # 3. HARD MODE SIGNALS
    # =====================================================

    hard_signals = [
        # Қазақша
        "тағы да кейінге қалдырдым",
        "ертең бастаймын",
        "тағы кредит аламын",
        "тағы қарыз аламын",
        "өзімді тоқтата алмаймын",
        "қайтадан соған жаздым",
        "күнде жазамын",
        "бәрібір істеймін",

        # Орысша
        "опять отложил",
        "начну завтра",
        "снова возьму кредит",
        "опять взял кредит",
        "снова написал ей",
        "пишу ей каждый день",
        "все равно сделаю",
    ]

    if any(
        signal in text
        for signal in hard_signals
    ):
        return "hard"

    # =====================================================
    # 4. ALPHA MODE SIGNALS
    # =====================================================

    alpha_signals = [
        # Қазақша
        "жалынғым келеді",
        "қайтару үшін не істеймін",
        "мені сыйламайды",
        "мені пайдаланып жүр",
        "бәріне келісіп жүрмін",
        "жоқ деп айта алмаймын",
        "қорқып жүрмін",
        "сылтау",

        # Орысша
        "хочу умолять",
        "как вернуть ее",
        "меня не уважают",
        "меня используют",
        "со всем соглашаюсь",
        "не могу сказать нет",
        "боюсь отказать",
        "отмазки",
    ]

    if any(
        signal in text
        for signal in alpha_signals
    ):
        return "alpha"

    # =====================================================
    # 5. DIRECT CATEGORIES
    # =====================================================

    direct_categories = {
        "finance",
        "career",
        "business",
        "discipline",
        "relationship",
    }

    if category in direct_categories:
        return "direct"

    # =====================================================
    # DEFAULT
    # =====================================================

    return "calm"


# =========================================================
# RESPONSE DEPTH PROMPT
# =========================================================

def build_response_style_prompt(
    style: str,
    language: str,
    tone: str = "direct",
) -> str:
    """
    Жауап көлемі + ERKEK AI tone instruction.
    """

    if language == "ru":

        depth_prompts = {

            "short": """
RESPONSE DEPTH: SHORT.

- Usually 40–140 words.
- Answer the main question immediately.
- Do not stretch a simple answer.
- Give 1–3 useful actions if actions are needed.
- Ask a clarifying question only when it materially changes the answer.
""",

            "normal": """
RESPONSE DEPTH: NORMAL.

- Usually 140–350 words.
- Explain the core reasoning clearly.
- Give 2–5 practical actions when useful.
- Avoid repetition and unnecessary philosophy.
- Do not create a long-term plan unless the situation requires it.
""",

            "deep": """
RESPONSE DEPTH: DEEP.

- Usually 350–700 words.
- Analyze trade-offs, risks, causes, and consequences.
- Use structured reasoning when it improves clarity.
- Give measurable short-term and medium-term actions when appropriate.
- Do not add length merely to look thorough.
"""
        }

        tone_prompts = {

            "calm": """
TONE: CALM.

Be confident, grounded, and controlled.
Do not use unnecessary sarcasm or aggression.
Prioritize clarity and stability.
""",

            "direct": """
TONE: DIRECT.

Be confident and straightforward.
State the main conclusion early.
Do not soften an important truth merely to sound polite.
""",

            "alpha": """
TONE: ALPHA.

Be more dominant, sharp, and uncompromising.

Challenge validation-seeking, weak boundaries, desperation,
bad financial decisions, and self-deception directly.

Light sarcasm or rough conversational language is allowed when natural.

Do not become theatrical or stupidly aggressive.
""",

            "hard": """
TONE: HARD.

The user appears to be repeating a destructive pattern,
making excuses, or knowingly sabotaging himself.

Use short, sharp, commanding language.

Call out the behavior clearly.
Do not sugarcoat the reality.

Sarcasm or rough language may be used if useful.

Attack the bad behavior or reasoning — never the person's human worth.
"""
        }

    else:

        depth_prompts = {

            "short": """
RESPONSE DEPTH: SHORT.

- Әдетте 40–140 сөз.
- Негізгі жауапты бірден айт.
- Қарапайым сұрақты созба.
- Қажет болса 1–3 нақты әрекет бер.
- Нақтылау сұрағын тек жауапты шынымен өзгертетін жағдайда қой.
""",

            "normal": """
RESPONSE DEPTH: NORMAL.

- Әдетте 140–350 сөз.
- Негізгі логиканы анық түсіндір.
- Қажет болса 2–5 нақты әрекет бер.
- Қайталау мен артық философиядан аулақ бол.
- Қажет болмаса ұзақ мерзімді жоспар құрма.
""",

            "deep": """
RESPONSE DEPTH: DEEP.

- Әдетте 350–700 сөз.
- Тәуекел, себеп, салдар және варианттарды терең талда.
- Құрылым жауапты түсініктірек етсе ғана қолдан.
- Қажет болса қысқа және орта мерзімді нақты әрекеттер бер.
- Ұзын болып көріну үшін мәтінді созба.
"""
        }

        tone_prompts = {

            "calm": """
TONE: CALM.

Сенімді, салмақты және бақылаулы сөйле.
Артық сарказм немесе агрессия қолданба.
Негізгі мақсат — анықтық пен тұрақтылық.
""",

            "direct": """
TONE: DIRECT.

Тікелей және сенімді сөйле.
Негізгі қорытындыны жауаптың басында айт.
Маңызды шындықты жай ғана әдепті көріну үшін жұмсартпа.
""",

            "alpha": """
TONE: ALPHA.

Сенімділігіңді, өткірлігіңді және еркектік позицияңды күшейт.

Жағымпаздық,
әлсіз шекара,
жалыну,
дұрыс емес қаржылық шешім,
өзін-өзі алдау
сияқты жағдайларды тікелей көрсет.

Қажет кезде жеңіл сарказм,
"брат" стилі немесе дөрекілеу сөз қолдануға болады.

Бірақ жасанды "альфа-мужик" пародиясына айналма.
""",

            "hard": """
TONE: HARD.

Пайдаланушы бір қателікті қайталап,
сылтау айтып немесе өзін әдейі алдап отырған жағдайда
қысқа әрі қатты сөйле.

Мәселені бетіне айт.
Шындықты артық жұмсартпа.

Қажет болса сарказм немесе дөрекілеу тіл қолдан.

Бірақ адамның өзін емес,
оның қате әрекетін, сылтауын немесе логикасын сына.
"""
        }

    depth_prompt = depth_prompts.get(
        style,
        depth_prompts["normal"]
    )

    tone_prompt = tone_prompts.get(
        tone,
        tone_prompts["direct"]
    )

    return (
        depth_prompt
        + "\n\n"
        + tone_prompt
    )