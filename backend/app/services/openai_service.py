import time
import openai
import httpx

from collections.abc import Generator
from openai import OpenAI

from app.core.config import OPENAI_API_KEY
from app.core.logger import logger


# =====================================================
# SETTINGS
# =====================================================

MODEL = "gpt-5-mini"

NON_STREAM_TIMEOUT = httpx.Timeout(
    60.0,
    connect=10.0,
    read=60.0,
    write=20.0,
)

STREAM_TIMEOUT = httpx.Timeout(
    90.0,
    connect=10.0,
    read=90.0,
    write=20.0,
)

STREAM_MAX_ATTEMPTS = 2
STREAM_RETRY_DELAY = 1.5


# =====================================================
# OPENAI CLIENT
# =====================================================

client = OpenAI(
    api_key=OPENAI_API_KEY,
    timeout=NON_STREAM_TIMEOUT,
    max_retries=2,
)


# =====================================================
# FALLBACK RESPONSES
# =====================================================

FALLBACK_RESPONSES = {
    "kk": (
        "Қазір AI сервисімен байланыста уақытша мәселе пайда болды. "
        "Біраз уақыттан кейін қайта жіберіп көр."
    ),

    "ru": (
        "Сейчас возникла временная проблема со связью с AI-сервисом. "
        "Попробуйте отправить сообщение немного позже."
    ),

    "default": (
        "The AI service is temporarily unavailable. "
        "Please try again shortly."
    ),
}


# =====================================================
# GET FALLBACK
# =====================================================

def get_fallback_response(
    language: str
) -> str:

    return FALLBACK_RESPONSES.get(
        language,
        FALLBACK_RESPONSES["default"],
    )


# =====================================================
# NORMAL AI RESPONSE
# =====================================================

def ask_ai(
    system_prompt: str,
    user_message: str,
    language: str = "kk",
) -> str:

    fallback_response = (
        get_fallback_response(language)
    )

    try:
        response = (
            client.with_options(
                timeout=NON_STREAM_TIMEOUT,
                max_retries=2,
            )
            .responses.create(
                model=MODEL,

                input=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_message,
                    },
                ],
            )
        )

        if not response.output_text:

            logger.warning(
                "OpenAI returned empty output"
            )

            return fallback_response

        return response.output_text

    except openai.APITimeoutError as error:

        logger.warning(
            "OpenAI timeout: %s",
            str(error),
        )

    except openai.APIConnectionError as error:

        logger.error(
            "OpenAI connection error: %s",
            str(error),
        )

    except openai.RateLimitError as error:

        logger.warning(
            "OpenAI rate limit: %s",
            str(error),
        )

    except openai.APIStatusError as error:

        logger.error(
            (
                "OpenAI API status error | "
                "status=%s | request_id=%s"
            ),
            error.status_code,
            getattr(
                error,
                "request_id",
                None,
            ),
        )

    except openai.APIError as error:

        logger.error(
            "OpenAI API error: %s",
            str(error),
        )

    except Exception:

        logger.exception(
            "Unexpected OpenAI error"
        )

    return fallback_response


# =====================================================
# STREAMING AI RESPONSE
# =====================================================

def stream_ai(
    system_prompt: str,
    user_message: str,
    language: str = "kk",
) -> Generator[str, None, None]:

    fallback_response = (
        get_fallback_response(language)
    )

    for attempt in range(
        1,
        STREAM_MAX_ATTEMPTS + 1
    ):

        has_output = False

        try:
            stream = (
                client.with_options(
                    timeout=STREAM_TIMEOUT,

                    # Retry-ды өзіміз басқарамыз.
                    max_retries=0,
                )
                .responses.create(
                    model=MODEL,

                    input=[
                        {
                            "role": "system",
                            "content": system_prompt,
                        },
                        {
                            "role": "user",
                            "content": user_message,
                        },
                    ],

                    stream=True,
                )
            )

            for event in stream:

                event_type = getattr(
                    event,
                    "type",
                    "",
                )

                if (
                    event_type
                    == "response.output_text.delta"
                ):
                    delta = getattr(
                        event,
                        "delta",
                        "",
                    )

                    if delta:

                        has_output = True

                        yield delta

            if has_output:
                return

            logger.warning(
                (
                    "OpenAI stream returned "
                    "empty output | attempt=%s"
                ),
                attempt,
            )

        except openai.APITimeoutError as error:

            logger.warning(
                (
                    "OpenAI streaming timeout | "
                    "attempt=%s | error=%s"
                ),
                attempt,
                str(error),
            )

        except openai.APIConnectionError as error:

            logger.error(
                (
                    "OpenAI streaming connection error | "
                    "attempt=%s | error=%s"
                ),
                attempt,
                str(error),
            )

        except openai.RateLimitError as error:

            logger.warning(
                (
                    "OpenAI streaming rate limit | "
                    "attempt=%s | error=%s"
                ),
                attempt,
                str(error),
            )

        except openai.APIStatusError as error:

            logger.error(
                (
                    "OpenAI streaming API status error | "
                    "attempt=%s | status=%s | "
                    "request_id=%s"
                ),
                attempt,
                error.status_code,
                getattr(
                    error,
                    "request_id",
                    None,
                ),
            )

            # 4xx сияқты permanent error болса
            # қайта retry жасаудың қажеті жоқ.
            if (
                error.status_code
                and error.status_code < 500
                and error.status_code != 429
            ):
                break

        except openai.APIError as error:

            logger.error(
                (
                    "OpenAI streaming API error | "
                    "attempt=%s | error=%s"
                ),
                attempt,
                str(error),
            )

        except Exception:

            logger.exception(
                (
                    "Unexpected OpenAI "
                    "streaming error | attempt=%s"
                ),
                attempt,
            )

        # Егер мәтіннің бір бөлігі келіп қойған болса,
        # қайта бастауға болмайды.
        if has_output:
            return

        if attempt < STREAM_MAX_ATTEMPTS:

            logger.info(
                (
                    "Retrying OpenAI stream | "
                    "next_attempt=%s"
                ),
                attempt + 1,
            )

            time.sleep(
                STREAM_RETRY_DELAY
            )

    yield fallback_response