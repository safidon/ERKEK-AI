import openai

from collections.abc import Generator

from openai import OpenAI

from app.core.config import OPENAI_API_KEY
from app.core.logger import logger


# =====================================================
# OPENAI CLIENT
# =====================================================

client = OpenAI(
    api_key=OPENAI_API_KEY,
    timeout=45.0,
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
    """
    Тілге сәйкес fallback жауап қайтарады.
    """

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
    """
    OpenAI API-ға кәдімгі non-streaming сұраныс жібереді.

    Қате болған жағдайда backend құламайды,
    пайдаланушыға fallback жауап береді.
    """

    fallback_response = (
        get_fallback_response(
            language
        )
    )

    try:
        response = (
            client.responses.create(
                model="gpt-5-mini",

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

    # =================================================
    # TIMEOUT
    # =================================================

    except openai.APITimeoutError as error:

        logger.warning(
            "OpenAI timeout: %s",
            str(error),
        )

        return fallback_response

    # =================================================
    # CONNECTION ERROR
    # =================================================

    except openai.APIConnectionError as error:

        logger.error(
            "OpenAI connection error: %s",
            str(error),
        )

        return fallback_response

    # =================================================
    # RATE LIMIT
    # =================================================

    except openai.RateLimitError as error:

        logger.warning(
            "OpenAI rate limit: %s",
            str(error),
        )

        return fallback_response

    # =================================================
    # API STATUS ERROR
    # =================================================

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

        return fallback_response

    # =================================================
    # GENERIC OPENAI ERROR
    # =================================================

    except openai.APIError as error:

        logger.error(
            "OpenAI API error: %s",
            str(error),
        )

        return fallback_response

    # =================================================
    # UNEXPECTED ERROR
    # =================================================

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
    """
    OpenAI жауабын бөліктермен қайтарады.

    Әр yield — frontend-ке жіберуге болатын
    жаңа мәтін бөлігі.

    Қате шықса fallback response бір рет yield болады.
    """

    fallback_response = (
        get_fallback_response(
            language
        )
    )

    has_output = False

    try:
        stream = client.responses.create(
            model="gpt-5-mini",

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

        for event in stream:

            event_type = getattr(
                event,
                "type",
                "",
            )

            # Responses API text delta event
            if (
                event_type ==
                "response.output_text.delta"
            ):
                delta = getattr(
                    event,
                    "delta",
                    "",
                )

                if delta:
                    has_output = True
                    yield delta

        if not has_output:

            logger.warning(
                "OpenAI stream returned empty output"
            )

            yield fallback_response

    # =================================================
    # TIMEOUT
    # =================================================

    except openai.APITimeoutError as error:

        logger.warning(
            "OpenAI streaming timeout: %s",
            str(error),
        )

        if not has_output:
            yield fallback_response

    # =================================================
    # CONNECTION ERROR
    # =================================================

    except openai.APIConnectionError as error:

        logger.error(
            "OpenAI streaming connection error: %s",
            str(error),
        )

        if not has_output:
            yield fallback_response

    # =================================================
    # RATE LIMIT
    # =================================================

    except openai.RateLimitError as error:

        logger.warning(
            "OpenAI streaming rate limit: %s",
            str(error),
        )

        if not has_output:
            yield fallback_response

    # =================================================
    # API STATUS ERROR
    # =================================================

    except openai.APIStatusError as error:

        logger.error(
            (
                "OpenAI streaming API status error | "
                "status=%s | request_id=%s"
            ),
            error.status_code,
            getattr(
                error,
                "request_id",
                None,
            ),
        )

        if not has_output:
            yield fallback_response

    # =================================================
    # GENERIC OPENAI ERROR
    # =================================================

    except openai.APIError as error:

        logger.error(
            "OpenAI streaming API error: %s",
            str(error),
        )

        if not has_output:
            yield fallback_response

    # =================================================
    # UNEXPECTED ERROR
    # =================================================

    except Exception:

        logger.exception(
            "Unexpected OpenAI streaming error"
        )

        if not has_output:
            yield fallback_response