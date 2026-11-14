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
TONE: WARM.
He may be tired, hurting or just checking in.
Be close, steady and calm — like an older brother next to him.
Acknowledge the feeling briefly and normalize it.
Give him something concrete to hold on to.
No sarcasm, no lectures, no therapy-speak.
""",

            "direct": """
TONE: DIRECT.
Speak straight and confidently, as a brother who is on his side.
State the main conclusion early.
Use what you know about his life to make it concrete.
Do not soften an important truth merely to sound polite.
""",

            "alpha": """
TONE: FIRM.
He is chasing, begging, seeking approval, or letting himself be used.
Be firm and clear — he deserves better, and you tell him that.
Show the boundary and give him short words he can actually say.
Light friendly roughness is fine when natural.
Respect him while you say it. Never become an "alpha" parody.
""",

            "hard": """
TONE: STRAIGHT TALK.
He is repeating a destructive pattern or making excuses.
Use short, firm sentences. Call out the behavior clearly.
It must sound like "I say this because I respect you",
not like a critic looking down.
Attack the behavior or excuse — never the man.
End with a clear next move.
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
TONE: WARM.
Ол шаршаған, ауыр күйде немесе жай ғана хал-жайын айтып отыр.
Қасында тұрған аға сияқты жақын, сабырлы сөйле.
Сезімін қысқа мойында және оның қалыпты екенін айт.
Ұстануға болатын нақты бір нәрсе бер.
Сарказм, уағыз, психолог тілі керек емес.
""",

            "direct": """
TONE: DIRECT.
Оның жағындағы аға ретінде тікелей және сенімді сөйле.
Негізгі қорытындыны басында айт.
Оның өмірі туралы білетініңді қолданып, нақты сөйле.
Маңызды шындықты жай әдепті көріну үшін жұмсартпа.
""",

            "alpha": """
TONE: FIRM.
Ол біреудің соңынан жүгіріп, жалынып немесе өзін пайдалануға беріп жүр.
Нық әрі анық сөйле — ол бұдан жақсысына лайық, соны айт.
Шекараны көрсет және ол шынымен айта алатын қысқа сөз бер.
Орынды болса, достық дөрекілеу сөз қолдануға болады.
Сыйлап тұрып айт. "Альфа-мужик" пародиясына айналма.
""",

            "hard": """
TONE: STRAIGHT TALK.
Ол бір қателікті қайталап немесе сылтау айтып отыр.
Қысқа, нық сөйлемдермен мәселені бетіне айт.
Бұл "мен сені сыйлағандықтан айтамын" деген үнмен естілуі керек,
жоғарыдан қарайтын сыншы сияқты емес.
Адамды емес, оның әрекетін немесе сылтауын сына.
Соңында нақты келесі қадамды бер.
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