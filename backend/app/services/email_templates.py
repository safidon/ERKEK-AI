"""
ERKEK AI хаттарының шаблоны (қара + алтын).

Почта бағдарламалары (Gmail, Outlook, iPhone Mail) заманауи CSS-ті
нашар түсінеді, сондықтан:
- макет кестелермен (table) жасалған;
- барлық стиль inline жазылған;
- қаріптер — кез келген құрылғыда бар Georgia / Arial;
- суреттер жоқ (көп почта суретті әдепкі бойынша бұғаттайды) —
  логотип мәтінмен және фон түсімен жасалған.

Оператор деректері frontend/lib/legal.ts-пен бірдей болуы керек.
"""

import html

from app.core.config import FRONTEND_URL


# Түстер (сайттағы globals.css-пен бірдей)
BG = "#0c0b09"
CARD = "#14120f"
CARD_BORDER = "#3a2d16"
TEXT = "#f5efe3"
MUTED = "#ada391"
FAINT = "#5e564a"
GOLD = "#c9a45c"
GOLD_LIGHT = "#e6cc8f"
BUTTON_TEXT = "#1a1408"

OPERATOR_NAME = "ЖК Рысбаев"
OPERATOR_CITY = "Ақтау қаласы"
CONTACT_EMAIL = "info@erkekai.kz"

SERIF = "Georgia, 'Times New Roman', serif"
SANS = "Arial, Helvetica, sans-serif"


def _site(path: str = "") -> str:
    return f"{FRONTEND_URL.rstrip('/')}{path}"


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def paragraph(text: str, *, muted: bool = False, size: int = 16) -> str:
    """Бір абзац. text — дайын HTML (esc() арқылы қорғалған болуы керек)."""

    color = MUTED if muted else TEXT
    return (
        f'<p style="margin:0 0 16px 0;font-family:{SANS};font-size:{size}px;'
        f'line-height:1.6;color:{color};">{text}</p>'
    )


def button(label: str, url: str) -> str:
    """Барлық почтада жұмыс істейтін батырма (кестемен жасалған)."""

    safe_url = esc(url)
    return f"""\
<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:28px 0 24px 0;">
  <tr>
    <td align="center" bgcolor="{GOLD}" style="border-radius:999px;background:{GOLD};background-image:linear-gradient(135deg,{GOLD_LIGHT},{GOLD} 55%,#a8853f);">
      <a href="{safe_url}" target="_blank" style="display:inline-block;padding:15px 34px;font-family:{SANS};font-size:16px;font-weight:bold;color:{BUTTON_TEXT};text-decoration:none;border-radius:999px;">{esc(label)}</a>
    </td>
  </tr>
</table>"""


def note(text: str, icon: str = "◆") -> str:
    """Алтын жиекті ескерту блогы."""

    return f"""\
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 24px 0;">
  <tr>
    <td style="padding:14px 16px;border:1px solid {CARD_BORDER};border-left:3px solid {GOLD};border-radius:12px;background:#1c1915;font-family:{SANS};font-size:14px;line-height:1.55;color:{GOLD_LIGHT};">
      <span style="color:{GOLD};">{esc(icon)}</span>&nbsp; {text}
    </td>
  </tr>
</table>"""


def fallback_link(url: str, language: str = "kk") -> str:
    """Батырма ашылмаса — сілтеменің өзі."""

    safe_url = esc(url)
    return (
        paragraph(
            "Если кнопка не открывается, скопируй ссылку в браузер:"
            if language == "ru"
            else "Батырма ашылмаса, мына сілтемені көшіріп, браузерге қой:",
            muted=True,
            size=13,
        )
        + f'<p style="margin:0 0 8px 0;font-family:{SANS};font-size:12px;'
        f'line-height:1.5;word-break:break-all;">'
        f'<a href="{safe_url}" target="_blank" style="color:{GOLD};'
        f'text-decoration:underline;">{safe_url}</a></p>'
    )


FOOTER_TEXTS = {
    "kk": {
        "tagline": "ERKEK AI — ер адамдарға арналған цифрлық ментор",
        "privacy": "Құпиялылық",
        "terms": "Шарттар",
        "auto": "Бұл хат автоматты түрде жіберілді — оған жауап берудің қажеті жоқ.",
    },
    "ru": {
        "tagline": "ERKEK AI — цифровой наставник для мужчин",
        "privacy": "Конфиденциальность",
        "terms": "Условия",
        "auto": "Письмо отправлено автоматически — отвечать на него не нужно.",
    },
}


def render_email(
    *,
    title: str,
    preheader: str,
    heading: str,
    body_html: str,
    language: str = "kk",
) -> str:
    """
    Толық хат.
    preheader — почта тізімінде тақырыптан кейін көрінетін қысқа мәтін.
    body_html — paragraph()/button()/note() арқылы жасалған мазмұн.
    """

    privacy = esc(_site("/privacy"))
    terms = esc(_site("/terms"))
    home = esc(_site("/"))
    html_lang = language if language in FOOTER_TEXTS else "kk"
    f = FOOTER_TEXTS[html_lang]

    return f"""\
<!DOCTYPE html>
<html lang="{html_lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark light">
<meta name="supported-color-schemes" content="dark light">
<title>{esc(title)}</title>
</head>
<body style="margin:0;padding:0;background:{BG};" bgcolor="{BG}">

<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:{BG};font-size:1px;line-height:1px;">{esc(preheader)}&#8203;&nbsp;&#8203;&nbsp;&#8203;&nbsp;&#8203;&nbsp;</div>

<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="{BG}" style="background:{BG};">
  <tr>
    <td align="center" style="padding:36px 16px 40px 16px;">

      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:520px;">

        <!-- LOGO -->
        <tr>
          <td align="center" style="padding:0 0 28px 0;">
            <a href="{home}" target="_blank" style="text-decoration:none;">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td width="44" height="44" align="center" valign="middle" bgcolor="{GOLD}" style="width:44px;height:44px;border-radius:12px;background:{GOLD};background-image:linear-gradient(135deg,{GOLD_LIGHT},{GOLD} 55%,#a8853f);font-family:{SERIF};font-size:24px;font-weight:bold;color:{BUTTON_TEXT};">E</td>
                  <td style="padding-left:12px;text-align:left;">
                    <div style="font-family:{SANS};font-size:15px;font-weight:bold;letter-spacing:3px;color:{TEXT};">ERKEK AI</div>
                    <div style="font-family:{SANS};font-size:10px;letter-spacing:3px;color:{GOLD};">DIGITAL MENTOR</div>
                  </td>
                </tr>
              </table>
            </a>
          </td>
        </tr>

        <!-- CARD -->
        <tr>
          <td bgcolor="{CARD}" style="background:{CARD};border:1px solid {CARD_BORDER};border-radius:24px;padding:38px 34px 30px 34px;">

            <div style="height:2px;width:48px;background:{GOLD};margin:0 0 22px 0;font-size:0;line-height:0;">&nbsp;</div>

            <h1 style="margin:0 0 20px 0;font-family:{SERIF};font-size:30px;line-height:1.2;font-weight:bold;color:{TEXT};">{esc(heading)}</h1>

            {body_html}

          </td>
        </tr>

        <!-- FOOTER -->
        <tr>
          <td align="center" style="padding:28px 12px 0 12px;font-family:{SANS};font-size:12px;line-height:1.7;color:{FAINT};">
            <div style="color:{GOLD};font-size:10px;margin-bottom:10px;">◆</div>
            {f["tagline"]}<br>
            <a href="{privacy}" target="_blank" style="color:{MUTED};text-decoration:underline;">{f["privacy"]}</a>
            &nbsp;·&nbsp;
            <a href="{terms}" target="_blank" style="color:{MUTED};text-decoration:underline;">{f["terms"]}</a>
            &nbsp;·&nbsp;
            <a href="mailto:{CONTACT_EMAIL}" style="color:{MUTED};text-decoration:underline;">{CONTACT_EMAIL}</a><br>
            {esc(OPERATOR_NAME)}, {esc(OPERATOR_CITY)}<br>
            {f["auto"]}
          </td>
        </tr>

      </table>

    </td>
  </tr>
</table>

</body>
</html>"""


# =====================================================
# ҚҰПИЯСӨЗДІ ҚАЛПЫНА КЕЛТІРУ
# =====================================================

RESET_TEXTS = {
    "kk": {
        "subject": "Құпиясөзді қалпына келтіру — ERKEK AI",
        "hello": "Сәлем, {name}!",
        "hello_plain": "Сәлем!",
        "asked": "ERKEK AI аккаунтыңның құпиясөзін қалпына келтіру сұралды.",
        "open_link": "Жаңа құпиясөз қою үшін мына сілтемені аш:",
        "press_button": "Жаңа құпиясөз қою үшін төмендегі батырманы бас.",
        "valid": "Сілтеме {minutes} минут жарамды және бір рет қана қолданылады.",
        "valid_html": "Сілтеме <strong>{minutes} минут</strong> жарамды "
                      "және бір рет қана қолданылады.",
        "ignore": "Бұл сұранысты сен жібермеген болсаң — хатты елеме, "
                  "құпиясөзің өзгермейді. Сілтемені ешкімге берме.",
        "button": "Жаңа құпиясөз қою",
        "preheader": "Жаңа құпиясөз қоюға арналған сілтеме — {minutes} минут жарамды.",
    },
    "ru": {
        "subject": "Восстановление пароля — ERKEK AI",
        "hello": "Привет, {name}!",
        "hello_plain": "Привет!",
        "asked": "Для твоего аккаунта ERKEK AI запрошено восстановление пароля.",
        "open_link": "Чтобы задать новый пароль, открой ссылку:",
        "press_button": "Чтобы задать новый пароль, нажми на кнопку ниже.",
        "valid": "Ссылка действует {minutes} минут и срабатывает только один раз.",
        "valid_html": "Ссылка действует <strong>{minutes} минут</strong> "
                      "и срабатывает только один раз.",
        "ignore": "Если ты не отправлял этот запрос — просто проигнорируй письмо, "
                  "пароль не изменится. Никому не передавай ссылку.",
        "button": "Задать новый пароль",
        "preheader": "Ссылка для нового пароля — действует {minutes} минут.",
    },
}


def password_reset_email(
    *,
    username: str,
    link: str,
    minutes: int,
    language: str = "kk",
) -> tuple[str, str, str]:
    """(subject, text, html) қайтарады."""

    t = RESET_TEXTS.get(language, RESET_TEXTS["kk"])

    subject = t["subject"]

    greeting = t["hello"].format(name=username) if username else t["hello_plain"]

    text = (
        f"{greeting}\n\n"
        f"{t['asked']}\n"
        f"{t['open_link']}\n\n"
        f"{link}\n\n"
        f"{t['valid'].format(minutes=minutes)}\n\n"
        f"{t['ignore']}\n\n"
        "—\n"
        "ERKEK AI\n"
        f"{CONTACT_EMAIL}"
    )

    body = (
        paragraph(esc(greeting))
        + paragraph(f"{t['asked']} {t['press_button']}")
        + button(t["button"], link)
        + note(t["valid_html"].format(minutes=minutes), icon="⏱")
        + paragraph(t["ignore"], muted=True, size=14)
        + '<div style="height:1px;background:#2a2620;margin:8px 0 18px 0;'
        'font-size:0;line-height:0;">&nbsp;</div>'
        + fallback_link(link, language=language)
    )

    html_body = render_email(
        title=subject,
        preheader=t["preheader"].format(minutes=minutes),
        heading=t["button"],
        body_html=body,
        language=language,
    )

    return subject, text, html_body


# =====================================================
# ҚОШ КЕЛДІҢІЗ ХАТЫ
# =====================================================

WELCOME_TEXTS = {
    "kk": {
        "subject": "ERKEK AI-ға қош келдің",
        "preheader": "Аккаунтың дайын. Бірінші әңгімені баста.",
        "heading": "Қош келдің, {name}",
        "intro": (
            "ERKEK AI — жұмыс, ақша, отбасы және мақсат туралы ақылдасатын "
            "жеке ментор. Жалған мақтау емес — тура сөз және нақты келесі қадам."
        ),
        "tips_title": "Қалай бастауға болады:",
        "tips": [
            "Не мазалап жүргенін жай ғана жаз — ұзақ дайындықтың қажеті жоқ.",
            "Әр тақырыпқа жеке чат аш: жұмыс бөлек, отбасы бөлек.",
            "Баптаулардан ERKEK AI мінезін таңда: Аға, Қатал немесе Стратег.",
        ],
        "button": "Әңгімені бастау",
        "telegram": "Telegram-да жазу ыңғайлы болса: {url}",
        "help": (
            "Ауыр сәтте жалғыз қалма: 112 — жедел көмек, 111 — тегін әрі "
            "анонимді көмек желісі, екеуі де тәулік бойы."
        ),
    },
    "ru": {
        "subject": "Добро пожаловать в ERKEK AI",
        "preheader": "Аккаунт готов. Начни первый разговор.",
        "heading": "Добро пожаловать, {name}",
        "intro": (
            "ERKEK AI — личный наставник, с которым можно посоветоваться о работе, "
            "деньгах, семье и целях. Без пустой лести — прямо и с конкретным следующим шагом."
        ),
        "tips_title": "С чего начать:",
        "tips": [
            "Просто напиши, что беспокоит, — долго готовиться не нужно.",
            "Под каждую тему открывай отдельный чат: работа отдельно, семья отдельно.",
            "В настройках выбери характер ERKEK AI: Брат, Жёсткий или Стратег.",
        ],
        "button": "Начать разговор",
        "telegram": "Если удобнее писать в Telegram: {url}",
        "help": (
            "В тяжёлый момент не оставайся один: 112 — экстренная помощь, "
            "111 — бесплатная анонимная линия поддержки, обе круглосуточно."
        ),
    },
}


def welcome_email(
    *,
    username: str,
    language: str = "kk",
    telegram_url: str | None = None,
) -> tuple[str, str, str]:
    """(subject, text, html) қайтарады."""

    t = WELCOME_TEXTS.get(language, WELCOME_TEXTS["kk"])
    name = username or "брат"
    chat_url = _site("/chat")

    lines = [
        t["heading"].format(name=name) + "!",
        "",
        t["intro"],
        "",
        t["tips_title"],
        *[f"— {tip}" for tip in t["tips"]],
        "",
        f"{t['button']}: {chat_url}",
    ]
    if telegram_url:
        lines.append(t["telegram"].format(url=telegram_url))
    lines += ["", t["help"], "", "—", "ERKEK AI", CONTACT_EMAIL]
    text = "\n".join(lines)

    tips_html = "".join(
        f'<tr><td valign="top" style="padding:0 10px 10px 0;color:{GOLD};'
        f'font-family:{SANS};font-size:14px;">◆</td>'
        f'<td style="padding:0 0 10px 0;font-family:{SANS};font-size:15px;'
        f'line-height:1.6;color:{TEXT};">{esc(tip)}</td></tr>'
        for tip in t["tips"]
    )

    body = (
        paragraph(esc(t["intro"]))
        + paragraph(f"<strong>{esc(t['tips_title'])}</strong>", size=15)
        + '<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
        'style="margin:0 0 18px 0;">' + tips_html + "</table>"
        + button(t["button"], chat_url)
    )

    if telegram_url:
        safe = esc(telegram_url)
        body += paragraph(
            esc(t["telegram"].split("{url}")[0])
            + f'<a href="{safe}" target="_blank" style="color:{GOLD};">{safe}</a>',
            muted=True,
            size=14,
        )

    body += note(esc(t["help"]), icon="☎")

    html_body = render_email(
        title=t["subject"],
        preheader=t["preheader"],
        heading=t["heading"].format(name=name),
        body_html=body,
        language=language,
    )

    return t["subject"], text, html_body


# =====================================================
# EMAIL-ДІ РАСТАУ (БЕЛСЕНДІРУ)
# =====================================================

VERIFY_TEXTS = {
    "kk": {
        "subject": "Email-іңді растау — ERKEK AI",
        "hello": "Сәлем, {name}!",
        "hello_plain": "Сәлем!",
        "intro": "ERKEK AI-да тіркелгенің үшін рақмет. Аккаунтты белсендіру үшін email-іңді растау керек.",
        "press": "Төмендегі батырманы бас — бір рет қана.",
        "open_link": "Аккаунтты белсендіру үшін мына сілтемені аш:",
        "button": "Email-ді растау",
        "valid": "Сілтеме {hours} сағат жарамды.",
        "ignore": "Сен тіркелмеген болсаң — бұл хатты елеме, аккаунт белсенді болмайды.",
        "preheader": "Аккаунтты белсендіру үшін бір рет бас.",
        "heading": "Аккаунтты белсендір",
    },
    "ru": {
        "subject": "Подтверди email — ERKEK AI",
        "hello": "Привет, {name}!",
        "hello_plain": "Привет!",
        "intro": "Спасибо за регистрацию в ERKEK AI. Чтобы активировать аккаунт, подтверди свой email.",
        "press": "Нажми на кнопку ниже — это нужно сделать один раз.",
        "open_link": "Чтобы активировать аккаунт, открой ссылку:",
        "button": "Подтвердить email",
        "valid": "Ссылка действует {hours} часа.",
        "ignore": "Если ты не регистрировался — просто проигнорируй письмо, аккаунт не будет активирован.",
        "preheader": "Один клик — и аккаунт активирован.",
        "heading": "Активируй аккаунт",
    },
}


def verification_email(
    *,
    username: str,
    link: str,
    hours: int,
    language: str = "kk",
) -> tuple[str, str, str]:
    """(subject, text, html) қайтарады."""

    t = VERIFY_TEXTS.get(language, VERIFY_TEXTS["kk"])
    greeting = t["hello"].format(name=username) if username else t["hello_plain"]
    valid = t["valid"].format(hours=hours)

    text = "\n".join([
        greeting,
        "",
        t["intro"],
        t["open_link"],
        "",
        link,
        "",
        valid,
        "",
        t["ignore"],
        "",
        "—",
        "ERKEK AI",
        CONTACT_EMAIL,
    ])

    body = (
        paragraph(esc(greeting))
        + paragraph(f"{esc(t['intro'])} {esc(t['press'])}")
        + button(t["button"], link)
        + note(esc(valid), icon="⏱")
        + paragraph(esc(t["ignore"]), muted=True, size=14)
        + '<div style="height:1px;background:#2a2620;margin:8px 0 18px 0;'
        'font-size:0;line-height:0;">&nbsp;</div>'
        + fallback_link(link, language=language)
    )

    html_body = render_email(
        title=t["subject"],
        preheader=t["preheader"],
        heading=t["heading"],
        body_html=body,
        language=language,
    )

    return t["subject"], text, html_body
