"""
Интерфейс тілі (kk / ru) және серверлік хабарламалардың аудармасы.

Тіл қалай анықталады:
- `X-Lang` header (бар болса);
- әйтпесе `erkek_lang` cookie (frontend тіл ауыстырғанда қояды;
  production-да API сол доменде болғандықтан cookie өзі жіберіледі).
Әдепкі тіл — қазақша.

Хабарламалар кодта қазақша жазылады. Орысша интерфейсте
TranslateDetailMiddleware JSON жауаптағы "detail" мәтінін
төмендегі сөздік бойынша аударады.
"""

import json
import re
from http.cookies import SimpleCookie

DEFAULT_LANGUAGE = "kk"
SUPPORTED_LANGUAGES = ("kk", "ru")
LANG_COOKIE = "erkek_lang"


# Қазақша -> орысша (дәл сәйкестік)
RU_MESSAGES = {
    "Жарамсыз немесе мерзімі өткен token.":
        "Недействительный или просроченный токен.",
    "Пайдаланушы табылмады.":
        "Пользователь не найден.",
    "Аккаунт белсенді емес.":
        "Аккаунт неактивен.",
    "Бұл бетке кіруге рұқсат жоқ.":
        "Нет доступа к этой странице.",
    "Тіркелу үшін пайдалану шарттары мен құпиялылық саясатына келісу керек.":
        "Для регистрации нужно принять условия использования "
        "и политику конфиденциальности.",
    "Бұл email бұрын тіркелген.":
        "Этот email уже зарегистрирован.",
    "Бұл username бұрын тіркелген.":
        "Это имя пользователя уже занято.",
    "Тіркелу кезінде сервер қатесі пайда болды.":
        "Ошибка сервера при регистрации.",
    "Email немесе пароль қате.":
        "Неверный email или пароль.",
    "Кіру кезінде сервер қатесі пайда болды.":
        "Ошибка сервера при входе.",
    "Егер бұл email тіркелген болса, құпиясөзді қалпына келтіру сілтемесі жіберілді.":
        "Если этот email зарегистрирован, мы отправили ссылку "
        "для восстановления пароля.",
    "Сілтеме жарамсыз немесе мерзімі өтіп кеткен. Қалпына келтіруді қайта сұра.":
        "Ссылка недействительна или устарела. Запроси восстановление заново.",
    "Құпиясөзді ауыстыру кезінде сервер қатесі пайда болды.":
        "Ошибка сервера при смене пароля.",
    "Құпиясөз ауыстырылды. Енді жаңа құпиясөзбен кір.":
        "Пароль изменён. Теперь войди с новым паролем.",
    "Сессияны жаңарту кезінде сервер қатесі пайда болды.":
        "Ошибка сервера при обновлении сессии.",
    "Сессия аяқталды. Қайта кір.":
        "Сессия завершена. Войди снова.",
    "Шықтың.":
        "Ты вышел из аккаунта.",
    "Құпиясөз қате.":
        "Неверный пароль.",
    "Аккаунтты жою кезінде сервер қатесі пайда болды.":
        "Ошибка сервера при удалении аккаунта.",
    "Аккаунтың және барлық деректерің жойылды.":
        "Твой аккаунт и все данные удалены.",
    "Әңгіме табылмады.":
        "Разговор не найден.",
    "Хабарлама табылмады.":
        "Сообщение не найдено.",
    "Email әлі расталмаған. Почтаңа келген сілтемені аш немесе хатты қайта жібер.":
        "Email ещё не подтверждён. Открой ссылку из письма или отправь письмо повторно.",
    "Сілтеме жарамсыз немесе мерзімі өткен. Растау хатын қайта сұра.":
        "Ссылка недействительна или устарела. Запроси письмо подтверждения заново.",
    "Егер аккаунт растауды күтіп тұрса, жаңа сілтеме жіберілді.":
        "Если аккаунт ждёт подтверждения, мы отправили новую ссылку.",
    "Google арқылы кіру қосылмаған.":
        "Вход через Google не подключён.",
    "Google арқылы кіру сәтсіз аяқталды. Қайталап көр.":
        "Не удалось войти через Google. Попробуй ещё раз.",
    "Сервер қатесі. Біраз уақыттан кейін қайталап көр.":
        "Ошибка сервера. Попробуй чуть позже.",
    "Telegram бот әзірге қосылмаған.":
        "Telegram-бот пока не подключён.",
    "Жаңа жауап алынбады.":
        "Не удалось получить новый ответ.",
    "Қайта жауап беруге жарамды соңғы сұрақ табылмады.":
        "Не найден последний вопрос, на который можно ответить заново.",
    "Алдыңғы жауапты ауыстыру мүмкін болмады.":
        "Не удалось заменить предыдущий ответ.",
    "Белгісіз memory field табылды.":
        "Найдено неизвестное поле памяти.",
    "ERKEK AI бүгін тым көп сұраныс алды. Ертең қайта келіп жаз — кешірім сұраймыз.":
        "Сегодня ERKEK AI получил слишком много запросов. "
        "Возвращайся завтра — приносим извинения.",
    "Сұраныс тым көп. Біраз уақыттан кейін қайталап көр.":
        "Слишком много запросов. Попробуй чуть позже.",
}

# Ішінде айнымалы бар хабарламалар
RU_PATTERNS = [
    (
        re.compile(r"^Бүгінгі (\d+) хабарлама лимиті бітті\. Ертең қайта жалғастырамыз\.$"),
        r"Дневной лимит в \1 сообщений исчерпан. Продолжим завтра.",
    ),
    (
        re.compile(r"^'(.+)' memory field ретінде қолдау көрсетілмейді\.$"),
        r"Поле памяти '\1' не поддерживается.",
    ),
]


def normalize_language(value: str | None) -> str:
    if not value:
        return DEFAULT_LANGUAGE

    value = value.strip().lower()[:2]
    return value if value in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def language_from_headers(headers: dict[str, str]) -> str:
    """headers — кілттері кіші әріппен жазылған dict."""

    if headers.get("x-lang"):
        return normalize_language(headers["x-lang"])

    cookie_header = headers.get("cookie")

    if cookie_header:
        cookie = SimpleCookie()
        try:
            cookie.load(cookie_header)
        except Exception:
            return DEFAULT_LANGUAGE

        if LANG_COOKIE in cookie:
            return normalize_language(cookie[LANG_COOKIE].value)

    return DEFAULT_LANGUAGE


def language_from_request(request) -> str:
    """FastAPI Request объектісінен тілді алады."""

    return language_from_headers(
        {key.lower(): value for key, value in request.headers.items()}
    )


def translate(message: str, language: str) -> str:
    if language != "ru" or not isinstance(message, str):
        return message

    if message in RU_MESSAGES:
        return RU_MESSAGES[message]

    for pattern, replacement in RU_PATTERNS:
        if pattern.match(message):
            return pattern.sub(replacement, message)

    return message


def _translate_payload(payload, language: str):
    if not isinstance(payload, dict) or "detail" not in payload:
        return payload

    detail = payload["detail"]

    if isinstance(detail, str):
        payload["detail"] = translate(detail, language)

    elif isinstance(detail, dict) and isinstance(detail.get("message"), str):
        detail["message"] = translate(detail["message"], language)

    return payload


class TranslateDetailMiddleware:
    """
    Орысша интерфейсте JSON жауаптардағы "detail" мәтінін аударады.
    Stream (чат) жауаптарына тиіспейді.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }

        language = language_from_headers(headers)

        if language == DEFAULT_LANGUAGE:
            await self.app(scope, receive, send)
            return

        start_message = None
        body_parts: list[bytes] = []
        passthrough = False

        async def send_wrapper(message):
            nonlocal start_message, passthrough

            if passthrough:
                await send(message)
                return

            if message["type"] == "http.response.start":
                content_type = ""
                for key, value in message.get("headers", []):
                    if key.lower() == b"content-type":
                        content_type = value.decode("latin-1").lower()

                if "application/json" not in content_type:
                    passthrough = True
                    await send(message)
                    return

                start_message = message
                return

            if message["type"] == "http.response.body":
                body_parts.append(message.get("body", b""))

                if message.get("more_body", False):
                    return

                body = b"".join(body_parts)

                try:
                    payload = json.loads(body)
                    payload = _translate_payload(payload, language)
                    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                except (ValueError, TypeError):
                    pass

                new_headers = [
                    (key, value)
                    for key, value in start_message.get("headers", [])
                    if key.lower() != b"content-length"
                ]
                new_headers.append((b"content-length", str(len(body)).encode()))

                await send({**start_message, "headers": new_headers})
                await send({"type": "http.response.body", "body": body})
                return

            await send(message)

        await self.app(scope, receive, send_wrapper)
