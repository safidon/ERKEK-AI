"""
Telegram бот логикасы: бір update-ті өңдейді.

Командалар: /start, /new, /mode, /help, /delete, /unlink.
Батырмалар (callback_data):
  accept          — шарттарға келісу
  mode:<persona>  — мінез таңдау
  fb:<id>:<r>     — жауапқа баға (1 / -1)
  del:yes|no      — аккаунтты жоюды растау
"""

import os
import threading
from collections import OrderedDict
from html import escape as html_escape

from fastapi import HTTPException

from app.auth.account import delete_account
from app.auth.service import get_user_by_id, set_user_persona
from app.brain.conversation_sessions import create_session, get_session
from app.core.i18n import translate
from app.core.logger import logger
from app.database import adapt_query, get_connection
from app.prompts.personas import PERSONAS, normalize_persona
from app.services.feedback import get_feedback_map, set_feedback
from app.services.usage import enforce_chat_quota, record_telegram_message
from app.telegram import accounts, api
from app.telegram.format import markdown_to_telegram_html, split_message


MAX_MESSAGE_LENGTH = 4000


def _site_url(path: str = "") -> str:
    return os.getenv("FRONTEND_URL", "https://erkekai.kz").rstrip("/") + path


# =====================================================
# TEXTS
# =====================================================

TEXTS = {
    "welcome": {
        "kk": (
            "Сәлем! Мен <b>ERKEK AI</b> — ер адамдарға арналған цифрлық ментормын. "
            "Жұмыс, ақша, отбасы, мақсат — не мазалап жүрсе, жаз, бірге талдаймыз.\n\n"
            "Бастамас бұрын: маған 18 жастан асқан адамдар ғана жаза алады. "
            "Хабарламаларың жауап дайындау үшін OpenAI (АҚШ) қызметіне жіберіледі.\n\n"
            "<a href=\"{terms}\">Пайдалану шарттары</a> · "
            "<a href=\"{privacy}\">Құпиялылық саясаты</a>"
        ),
        "ru": (
            "Привет! Я <b>ERKEK AI</b> — цифровой наставник для мужчин. "
            "Работа, деньги, семья, цели — пиши, что беспокоит, разберём вместе.\n\n"
            "Перед началом: писать мне могут только лица старше 18 лет. "
            "Твои сообщения передаются сервису OpenAI (США) для подготовки ответов.\n\n"
            "<a href=\"{terms}\">Условия использования</a> · "
            "<a href=\"{privacy}\">Политика конфиденциальности</a>"
        ),
    },
    "choose_lang": {
        "kk": "Тілді таңда / Выбери язык 👇",
        "ru": "Тілді таңда / Выбери язык 👇",
    },
    "lang_saved": {
        "kk": "Тіл: 🇰🇿 Қазақша ✓",
        "ru": "Язык: 🇷🇺 Русский ✓",
    },
    "ask_name": {
        "kk": "Танысайық 🤝 Атың кім? Саған қалай атайын?",
        "ru": "Давай знакомиться 🤝 Как тебя зовут? Как к тебе обращаться?",
    },
    "skip_name": {"kk": "Өткізіп жіберу", "ru": "Пропустить"},
    "name_saved": {
        "kk": "Танысқаныма қуаныштымын, <b>{name}</b>! 🤝\n\nНе ойландырып жүр? Жай ғана жаз.",
        "ru": "Рад знакомству, <b>{name}</b>! 🤝\n\nЧто тебя беспокоит? Просто напиши.",
    },
    "name_skipped": {
        "kk": "Жарайды. Не ойландырып жүр? Жай ғана жаз.",
        "ru": "Хорошо. Что тебя беспокоит? Просто напиши.",
    },
    "accept_button": {
        "kk": "✅ Келісемін, 18 жастан асқанмын",
        "ru": "✅ Согласен, мне больше 18 лет",
    },
    "need_accept": {
        "kk": "Жазу үшін алдымен шарттарға келісу керек 👇",
        "ru": "Чтобы писать, сначала нужно принять условия 👇",
    },
    "accepted": {
        "kk": "Жарайды, бастадық 🤝\n\nНе ойландырып жүр? Жай ғана жаз.",
        "ru": "Отлично, начинаем 🤝\n\nЧто тебя беспокоит? Просто напиши.",
    },
    "linked": {
        "kk": "✅ Telegram сайттағы аккаунтыңа байланысты. Енді жады мен әңгімелер ортақ.",
        "ru": "✅ Telegram привязан к твоему аккаунту на сайте. Теперь память и разговоры общие.",
    },
    "linked_moved": {
        "kk": "Telegram-дағы бұрынғы әңгімелерің сайт аккаунтына көшірілді.",
        "ru": "Прежние разговоры из Telegram перенесены в аккаунт на сайте.",
    },
    "link_invalid": {
        "kk": "Сілтеме жарамсыз немесе мерзімі өтіп кеткен. Сайттағы Баптаулардан жаңасын ал.",
        "ru": "Ссылка недействительна или устарела. Получи новую в Настройках на сайте.",
    },
    "already_linked": {
        "kk": "Бұл Telegram осы аккаунтқа бұрыннан байланған.",
        "ru": "Этот Telegram уже привязан к этому аккаунту.",
    },
    "new_chat": {
        "kk": "🆕 Жаңа әңгіме басталды. Не туралы сөйлесеміз?",
        "ru": "🆕 Начат новый разговор. О чём поговорим?",
    },
    "mode_title": {
        "kk": "ERKEK AI мінезін таңда:",
        "ru": "Выбери характер ERKEK AI:",
    },
    "mode_saved": {
        "kk": "Мінез сақталды: <b>{name}</b>",
        "ru": "Характер сохранён: <b>{name}</b>",
    },
    "help": {
        "kk": (
            "Маған жай ғана жаз — жауап беремін.\n\n"
            "/new — жаңа әңгіме\n"
            "/mode — мінезді таңдау\n"
            "/lang — тілді ауыстыру\n"
            "/name — атыңды өзгерту\n"
            "/delete — аккаунтты жою\n"
            "/help — көмек\n\n"
            "Сайттағы аккаунтыңмен байланыстыру: {site}/settings → Telegram."
        ),
        "ru": (
            "Просто напиши мне — я отвечу.\n\n"
            "/new — новый разговор\n"
            "/mode — выбрать характер\n"
            "/lang — сменить язык\n"
            "/name — изменить имя\n"
            "/delete — удалить аккаунт\n"
            "/help — помощь\n\n"
            "Привязать аккаунт с сайта: {site}/settings → Telegram."
        ),
    },
    "only_text": {
        "kk": "Әзірге тек мәтінмен жаза аламын ✍️",
        "ru": "Пока я понимаю только текст ✍️",
    },
    "too_long": {
        "kk": "Хабарлама тым ұзын (ең көбі 4000 таңба). Қысқартып жібер.",
        "ru": "Сообщение слишком длинное (максимум 4000 символов). Сократи, пожалуйста.",
    },
    "error": {
        "kk": "Кешір, жауап дайындау кезінде қате шықты. Сәлден кейін қайталап көр.",
        "ru": "Извини, при подготовке ответа произошла ошибка. Попробуй чуть позже.",
    },
    "inactive": {
        "kk": "Аккаунт белсенді емес.",
        "ru": "Аккаунт неактивен.",
    },
    "delete_confirm": {
        "kk": (
            "Аккаунтың, барлық әңгімелерің және ERKEK AI жадындағы мәліметтер "
            "біржола өшіріледі. Жалғастырамыз ба?"
        ),
        "ru": (
            "Твой аккаунт, все разговоры и сведения в памяти ERKEK AI "
            "будут удалены навсегда. Продолжить?"
        ),
    },
    "delete_yes": {"kk": "Иә, біржола жою", "ru": "Да, удалить навсегда"},
    "delete_no": {"kk": "Бас тарту", "ru": "Отмена"},
    "deleted": {
        "kk": "Аккаунт пен деректер жойылды. Сау бол, брат. Қайта оралсаң — /start.",
        "ru": "Аккаунт и данные удалены. Береги себя, брат. Захочешь вернуться — /start.",
    },
    "delete_cancelled": {"kk": "Жарайды, ештеңе өшірілмеді.", "ru": "Хорошо, ничего не удалено."},
    "delete_site_account": {
        "kk": (
            "Бұл Telegram сайттағы аккаунтқа байланған. Аккаунтты сайттағы "
            "Баптаулар бетінен жоюға болады: {site}/settings\n\n"
            "Тек Telegram байланысын алып тастау үшін — /unlink"
        ),
        "ru": (
            "Этот Telegram привязан к аккаунту на сайте. Удалить аккаунт можно "
            "на странице Настройки: {site}/settings\n\n"
            "Чтобы только отвязать Telegram — /unlink"
        ),
    },
    "unlinked": {
        "kk": "Telegram аккаунттан ажыратылды. Қайта бастау үшін — /start.",
        "ru": "Telegram отвязан от аккаунта. Чтобы начать заново — /start.",
    },
    "not_linked": {
        "kk": "Бұл Telegram сайттағы аккаунтқа байланбаған.",
        "ru": "Этот Telegram не привязан к аккаунту на сайте.",
    },
    "thanks": {"kk": "Рақмет!", "ru": "Спасибо!"},
}

REASON_NAMES = {
    "not_understood": {"kk": "Түсінбеді", "ru": "Не понял меня"},
    "too_long": {"kk": "Тым ұзақ", "ru": "Слишком длинно"},
    "not_useful": {"kk": "Пайдасыз", "ru": "Бесполезно"},
    "tone": {"kk": "Сөйлеу мәнері", "ru": "Не тот тон"},
}

PERSONA_NAMES = {
    "brother": {"kk": "Аға / Брат", "ru": "Брат"},
    "hardcore": {"kk": "Қатал", "ru": "Жёсткий"},
    "strategist": {"kk": "Стратег", "ru": "Стратег"},
}


def t(key: str, lang: str, **kwargs) -> str:
    text = TEXTS[key].get(lang) or TEXTS[key]["kk"]
    return text.format(**kwargs) if kwargs else text


def detect_lang(language_code: str | None) -> str:
    return "ru" if (language_code or "").lower().startswith("ru") else "kk"


# =====================================================
# KEYBOARDS
# =====================================================

def lang_keyboard() -> dict:
    return {
        "inline_keyboard": [[
            {"text": "🇰🇿 Қазақша", "callback_data": "lang:kk"},
            {"text": "🇷🇺 Русский", "callback_data": "lang:ru"},
        ]]
    }


def skip_name_keyboard(lang: str) -> dict:
    return {"inline_keyboard": [[{"text": t("skip_name", lang), "callback_data": "name:skip"}]]}


def accept_keyboard(lang: str) -> dict:
    return {"inline_keyboard": [[{"text": t("accept_button", lang), "callback_data": "accept"}]]}


def feedback_keyboard(message_id: int, rating: int) -> dict:
    return {
        "inline_keyboard": [[
            {"text": "👍" + (" ✓" if rating == 1 else ""), "callback_data": f"fb:{message_id}:1"},
            {"text": "👎" + (" ✓" if rating == -1 else ""), "callback_data": f"fb:{message_id}:-1"},
        ]]
    }


def reason_keyboard(message_id: int, lang: str) -> dict:
    """👎 басқаннан кейін: себебін таңдау (міндетті емес)."""

    names = list(REASON_NAMES.items())
    rows = [
        [
            {"text": names[i][1][lang], "callback_data": f"fbr:{message_id}:{names[i][0]}"},
            {"text": names[i + 1][1][lang], "callback_data": f"fbr:{message_id}:{names[i + 1][0]}"},
        ]
        for i in range(0, len(names), 2)
    ]
    return {"inline_keyboard": feedback_keyboard(message_id, -1)["inline_keyboard"] + rows}


def mode_keyboard(current: str, lang: str) -> dict:
    return {
        "inline_keyboard": [
            [{
                "text": ("✓ " if persona_id == current else "") + PERSONA_NAMES[persona_id][lang],
                "callback_data": f"mode:{persona_id}",
            }]
            for persona_id in PERSONAS
        ]
    }


def delete_keyboard(lang: str) -> dict:
    return {
        "inline_keyboard": [[
            {"text": t("delete_yes", lang), "callback_data": "del:yes"},
            {"text": t("delete_no", lang), "callback_data": "del:no"},
        ]]
    }


# =====================================================
# DUPLICATE UPDATES
# =====================================================
# Telegram жауап кешіксе, сол update-ті қайта жіберуі мүмкін.

_seen_updates: "OrderedDict[int, None]" = OrderedDict()
_seen_lock = threading.Lock()

# Келісім батырмасын баспай тұрып жазған алғашқы хабарлама:
# келіскен бойда соған жауап береміз (қайта жазудың қажеті жоқ).
_pending_first_message: "OrderedDict[str, str]" = OrderedDict()

# Аккаунт ашылмай тұрып таңдалған тіл (келісім батырмасына дейін).
_pending_lang: "OrderedDict[str, str]" = OrderedDict()


def _remember(store: OrderedDict, key, value) -> None:
    with _seen_lock:
        store[str(key)] = value
        while len(store) > 500:
            store.popitem(last=False)


def _take(store: OrderedDict, key):
    with _seen_lock:
        return store.pop(str(key), None)


def _already_seen(update_id: int | None) -> bool:
    if update_id is None:
        return False

    with _seen_lock:
        if update_id in _seen_updates:
            return True
        _seen_updates[update_id] = None
        while len(_seen_updates) > 1000:
            _seen_updates.popitem(last=False)
        return False


# =====================================================
# ENTRY POINT
# =====================================================

def handle_update(update: dict) -> None:
    if _already_seen(update.get("update_id")):
        return

    try:
        if "callback_query" in update:
            _handle_callback(update["callback_query"])
        elif "message" in update:
            _handle_message(update["message"])
    except Exception:
        logger.exception("Telegram update failed | update_id=%s", update.get("update_id"))


# =====================================================
# MESSAGES
# =====================================================

def _handle_message(message: dict) -> None:
    chat = message.get("chat") or {}
    sender = message.get("from") or {}

    # Тек жеке чат (топтарда жұмыс істемейді).
    if chat.get("type") != "private" or not sender.get("id") or sender.get("is_bot"):
        return

    tg_id = sender["id"]
    chat_id = chat["id"]
    account = accounts.get_by_telegram_id(tg_id)
    lang = account["lang"] if account else detect_lang(sender.get("language_code"))

    text = (message.get("text") or "").strip()

    if text.startswith("/"):
        _handle_command(text, tg_id, chat_id, account, lang)
        return

    if not account:
        if text and len(text) <= MAX_MESSAGE_LENGTH:
            _remember(_pending_first_message, tg_id, text)
        _start_onboarding(tg_id, chat_id)
        return

    if account["awaiting"] == "name" and text:
        _receive_name(account, chat_id, text, lang)
        return

    if not text:
        api.send_message(chat_id, t("only_text", lang))
        return

    if len(text) > MAX_MESSAGE_LENGTH:
        api.send_message(chat_id, t("too_long", lang))
        return

    _chat(account, chat_id, text, lang)


def _handle_command(text: str, tg_id, chat_id, account, lang: str) -> None:
    parts = text.split(maxsplit=1)
    command = parts[0].split("@")[0].lower()
    argument = parts[1].strip() if len(parts) > 1 else ""

    if command == "/start":
        if argument.startswith("link_"):
            _link(argument[len("link_"):], tg_id, chat_id, lang)
            return

        if account:
            api.send_message(chat_id, t("accepted", lang))
        else:
            _start_onboarding(tg_id, chat_id)
        return

    if command == "/lang":
        api.send_message(chat_id, t("choose_lang", lang), lang_keyboard())
        return

    if command == "/help":
        api.send_message(chat_id, t("help", lang, site=_site_url()), html=False)
        return

    if not account:
        _start_onboarding(tg_id, chat_id)
        return

    if command == "/name":
        accounts.set_awaiting(tg_id, "name")
        api.send_message(chat_id, t("ask_name", lang), skip_name_keyboard(lang))
        return

    if command == "/new":
        session = create_session(user_id=account["user_id"])
        accounts.set_active_session(tg_id, session["id"])
        api.send_message(chat_id, t("new_chat", lang))
        return

    if command == "/mode":
        user = get_user_by_id(account["user_id"])
        current = normalize_persona(user["persona"] if user else None)
        api.send_message(chat_id, t("mode_title", lang), mode_keyboard(current, lang))
        return

    if command == "/delete":
        user = get_user_by_id(account["user_id"])
        if user and not accounts.is_telegram_only(user):
            api.send_message(chat_id, t("delete_site_account", lang, site=_site_url()), html=False)
        else:
            api.send_message(chat_id, t("delete_confirm", lang), delete_keyboard(lang))
        return

    if command == "/unlink":
        user = get_user_by_id(account["user_id"])
        if user and not accounts.is_telegram_only(user):
            accounts.unlink_user(account["user_id"])
            api.send_message(chat_id, t("unlinked", lang))
        else:
            api.send_message(chat_id, t("not_linked", lang))
        return

    api.send_message(chat_id, t("help", lang, site=_site_url()), html=False)


def _start_onboarding(tg_id, chat_id) -> None:
    """Жаңа адам: алдымен тіл, содан кейін келісім, содан кейін есім."""

    chosen = _pending_lang.get(str(tg_id))

    if chosen:
        _send_welcome(chat_id, chosen)
    else:
        api.send_message(chat_id, t("choose_lang", "kk"), lang_keyboard())


def _clean_name(text: str) -> str | None:
    """Есімге ұқсаса — тазартып қайтарады, сұраққа ұқсаса — None."""

    name = " ".join(text.replace("<", "").replace(">", "").split())

    if not name or len(name) > 40 or len(name.split()) > 3:
        return None

    if any(mark in name for mark in "?!/:@#"):
        return None

    return name[:1].upper() + name[1:]


def _receive_name(account, chat_id, text: str, lang: str) -> None:
    tg_id = account["telegram_user_id"]
    accounts.set_awaiting(tg_id, None)

    name = _clean_name(text)

    if name is None:
        # Есім емес, бірден сұрақ жазды — сұрағына жауап береміз.
        _chat(accounts.get_by_telegram_id(tg_id), chat_id, text, lang)
        return

    accounts.set_display_name(account["user_id"], name)
    _after_onboarding(tg_id, chat_id, lang, t("name_saved", lang, name=html_escape(name)))


def _after_onboarding(tg_id, chat_id, lang: str, greeting: str) -> None:
    pending = _take(_pending_first_message, tg_id)
    account = accounts.get_by_telegram_id(tg_id)

    if pending and account:
        # Алғашқы сұрағына бірден жауап береміз.
        _chat(account, chat_id, pending, lang)
    else:
        api.send_message(chat_id, greeting)


def _send_welcome(chat_id, lang: str) -> None:
    api.send_message(
        chat_id,
        t("welcome", lang, terms=_site_url("/terms"), privacy=_site_url("/privacy")),
        accept_keyboard(lang),
    )


def _link(code: str, tg_id, chat_id, lang: str) -> None:
    site_user_id = accounts.consume_link_code(code)

    if not site_user_id:
        api.send_message(chat_id, t("link_invalid", lang))
        return

    current = accounts.get_by_telegram_id(tg_id)
    if current and current["user_id"] == site_user_id:
        api.send_message(chat_id, t("already_linked", lang))
        return

    moved = accounts.link_to_site_account(tg_id, chat_id, lang, site_user_id)

    text = t("linked", lang)
    if moved:
        text += "\n\n" + t("linked_moved", lang)
    api.send_message(chat_id, text)


# =====================================================
# CHAT
# =====================================================

def _typing_loop(chat_id, stop: threading.Event) -> None:
    # Telegram «жазып жатыр...» белгісі ~5 секунд көрінеді.
    while not stop.is_set():
        api.send_typing(chat_id)
        stop.wait(4.5)


def _active_session_id(account, tg_id) -> int:
    user_id = account["user_id"]
    session_id = account["active_session_id"]

    if session_id and get_session(user_id=user_id, session_id=int(session_id)):
        return int(session_id)

    session = create_session(user_id=user_id)
    accounts.set_active_session(tg_id, session["id"])
    return int(session["id"])


def _last_assistant_message_id(user_id: str, session_id: int) -> int | None:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            adapt_query(
                """
                SELECT id FROM conversations
                WHERE user_id = ? AND session_id = ? AND role = 'assistant'
                ORDER BY id DESC LIMIT 1
                """
            ),
            (user_id, session_id),
        )
        row = cursor.fetchone()
        return int(row["id"]) if row else None
    finally:
        connection.close()


def _chat(account, chat_id, text: str, lang: str) -> None:
    # Цикл болмауы үшін маршрутты осында импорттаймыз.
    from app.routes.chat import ChatRequest, chat

    user = get_user_by_id(account["user_id"])

    if not user or not user["is_active"]:
        api.send_message(chat_id, t("inactive", lang))
        return

    tg_id = account["telegram_user_id"]

    try:
        enforce_chat_quota(current_user=user)
    except HTTPException as error:
        api.send_message(chat_id, translate(str(error.detail), lang), html=False)
        return

    record_telegram_message()

    stop = threading.Event()
    threading.Thread(target=_typing_loop, args=(chat_id, stop), daemon=True).start()

    try:
        session_id = _active_session_id(account, tg_id)
        result = chat(ChatRequest(session_id=session_id, message=text), current_user=user)
        answer = (result.get("answer") or "").strip()
    except Exception:
        logger.exception("Telegram chat failed | user_id=%s", account["user_id"])
        stop.set()
        api.send_message(chat_id, t("error", lang))
        return
    finally:
        stop.set()

    if not answer:
        api.send_message(chat_id, t("error", lang))
        return

    message_id = _last_assistant_message_id(account["user_id"], session_id)
    chunks = split_message(markdown_to_telegram_html(answer))

    for index, chunk in enumerate(chunks):
        is_last = index == len(chunks) - 1
        api.send_message(
            chat_id,
            chunk,
            feedback_keyboard(message_id, 0) if (is_last and message_id) else None,
        )


# =====================================================
# CALLBACKS (батырмалар)
# =====================================================

def _handle_callback(callback: dict) -> None:
    callback_id = callback.get("id")
    sender = callback.get("from") or {}
    message = callback.get("message") or {}
    chat_id = (message.get("chat") or {}).get("id")
    data = callback.get("data") or ""

    tg_id = sender.get("id")
    if not tg_id or not chat_id:
        return

    account = accounts.get_by_telegram_id(tg_id)
    lang = account["lang"] if account else detect_lang(sender.get("language_code"))

    if data.startswith("lang:"):
        chosen = data.split(":", 1)[1]
        if chosen not in ("kk", "ru"):
            api.answer_callback(callback_id)
            return

        api.answer_callback(callback_id)
        api.edit_text(chat_id, message.get("message_id"), t("lang_saved", chosen))

        if account:
            accounts.set_lang(tg_id, chosen)
        else:
            _remember(_pending_lang, tg_id, chosen)
            _send_welcome(chat_id, chosen)
        return

    if data == "accept":
        api.answer_callback(callback_id)
        api.edit_reply_markup(chat_id, message.get("message_id"), None)

        if account:
            api.send_message(chat_id, t("accepted", lang))
            return

        lang = _take(_pending_lang, tg_id) or lang
        accounts.create_telegram_user(tg_id, chat_id, lang)
        api.send_message(chat_id, t("ask_name", lang), skip_name_keyboard(lang))
        return

    if data == "name:skip":
        api.answer_callback(callback_id)
        api.edit_reply_markup(chat_id, message.get("message_id"), None)
        if account:
            accounts.set_awaiting(tg_id, None)
            _after_onboarding(tg_id, chat_id, lang, t("name_skipped", lang))
        return

    if not account:
        api.answer_callback(callback_id)
        _send_welcome(chat_id, lang)
        return

    user_id = account["user_id"]

    if data.startswith("mode:"):
        persona = data.split(":", 1)[1]
        if persona in PERSONAS:
            set_user_persona(user_id, persona)
            api.answer_callback(callback_id)
            api.edit_text(
                chat_id,
                message.get("message_id"),
                t("mode_saved", lang, name=PERSONA_NAMES[persona][lang]),
            )
        else:
            api.answer_callback(callback_id)
        return

    if data.startswith("fb:"):
        _feedback_callback(callback_id, data, user_id, chat_id, message, lang)
        return

    if data.startswith("fbr:"):
        _reason_callback(callback_id, data, user_id, chat_id, message, lang)
        return

    if data in ("del:yes", "del:no"):
        api.answer_callback(callback_id)
        api.edit_reply_markup(chat_id, message.get("message_id"), None)

        user = get_user_by_id(user_id)
        if data == "del:yes" and user and accounts.is_telegram_only(user):
            delete_account(user_id)
            api.send_message(chat_id, t("deleted", lang))
        else:
            api.send_message(chat_id, t("delete_cancelled", lang))
        return

    api.answer_callback(callback_id)


def _feedback_callback(callback_id, data: str, user_id: str, chat_id, message: dict, lang: str) -> None:
    from app.services.feedback import is_own_assistant_message
    from app.prompts.personas import get_user_persona

    try:
        _, raw_id, raw_rating = data.split(":")
        message_id = int(raw_id)
        rating = int(raw_rating)
    except ValueError:
        api.answer_callback(callback_id)
        return

    if rating not in (1, -1) or not is_own_assistant_message(user_id, message_id):
        api.answer_callback(callback_id)
        return

    current = get_feedback_map(user_id, [message_id]).get(message_id, 0)
    new_rating = 0 if current == rating else rating

    user = get_user_by_id(user_id)
    set_feedback(
        user_id=user_id,
        message_id=message_id,
        rating=new_rating,
        persona=get_user_persona(user) if user else None,
    )

    api.answer_callback(callback_id, t("thanks", lang) if new_rating else None)
    api.edit_reply_markup(
        chat_id,
        message.get("message_id"),
        reason_keyboard(message_id, lang)
        if new_rating == -1
        else feedback_keyboard(message_id, new_rating),
    )


def _reason_callback(callback_id, data: str, user_id: str, chat_id, message: dict, lang: str) -> None:
    from app.prompts.personas import get_user_persona
    from app.services.feedback import is_own_assistant_message

    try:
        _, raw_id, reason = data.split(":")
        message_id = int(raw_id)
    except ValueError:
        api.answer_callback(callback_id)
        return

    if reason not in REASON_NAMES or not is_own_assistant_message(user_id, message_id):
        api.answer_callback(callback_id)
        return

    user = get_user_by_id(user_id)
    set_feedback(
        user_id=user_id,
        message_id=message_id,
        rating=-1,
        persona=get_user_persona(user) if user else None,
        reason=reason,
    )

    api.answer_callback(callback_id, t("thanks", lang))
    api.edit_reply_markup(chat_id, message.get("message_id"), feedback_keyboard(message_id, -1))
