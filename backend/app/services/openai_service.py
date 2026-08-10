import openai

from openai import OpenAI

from app.core.config import OPENAI_API_KEY
from app.core.logger import logger


# =====================================================
# OPENAI CLIENT
# =====================================================

client = OpenAI(
    api_key=OPENAI_API_KEY,
    timeout=45.0,
    max_retries=2
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
    )
}


def get_fallback_response(language: str) -> str:
    """
    Тілге сәйкес fallback жауап қайтарады.
    """

    return FALLBACK_RESPONSES.get(
        language,
        FALLBACK_RESPONSES["default"]
    )


def ask_ai(
    system_prompt: str,
    user_message: str,
    language: str = "kk"
) -> str:
    """
    OpenAI API-ға сұраныс жібереді.

    Қате болған жағдайда backend құламайды,
    пайдаланушыға fallback жауап береді.
    """

    fallback_response = get_fallback_response(
        language
    )

    try:
        response = client.responses.create(
            model="gpt-5-mini",
            input=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ]
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
            str(error)
        )

        return fallback_response

    # =================================================
    # CONNECTION ERROR
    # =================================================

    except openai.APIConnectionError as error:

        logger.error(
            "OpenAI connection error: %s",
            str(error)
        )

        return fallback_response

    # =================================================
    # RATE LIMIT
    # =================================================

    except openai.RateLimitError as error:

        logger.warning(
            "OpenAI rate limit: %s",
            str(error)
        )

        return fallback_response

    # =================================================
    # API STATUS ERROR
    # =================================================

    except openai.APIStatusError as error:

        logger.error(
            "OpenAI API status error | status=%s | request_id=%s",
            error.status_code,
            getattr(error, "request_id", None)
        )

        return fallback_response

    # =================================================
    # GENERIC OPENAI ERROR
    # =================================================

    except openai.APIError as error:

        logger.error(
            "OpenAI API error: %s",
            str(error)
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