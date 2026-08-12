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
    timeout=90.0,
    connect=20.0,
    read=90.0,
    write=30.0,
    pool=20.0,
)

STREAM_TIMEOUT = httpx.Timeout(
    timeout=180.0,
    connect=20.0,
    read=180.0,
    write=30.0,
    pool=20.0,
)

STREAM_MAX_ATTEMPTS = 3

STREAM_RETRY_DELAYS = {
    1: 1.5,
    2: 3.0,
}


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
        get_fallback_response(
            language
        )
    )

    started_at = time.monotonic()

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

        elapsed = (
            time.monotonic()
            - started_at
        )

        logger.info(
            (
                "OpenAI non-stream response completed | "
                "latency=%.2fs"
            ),
            elapsed,
        )

        if not response.output_text:

            logger.warning(
                "OpenAI returned empty output"
            )

            return fallback_response

        return response.output_text

    except openai.APITimeoutError as error:

        logger.warning(
            (
                "OpenAI timeout | "
                "latency=%.2fs | error=%s"
            ),
            time.monotonic() - started_at,
            str(error),
        )

    except openai.APIConnectionError as error:

        logger.error(
            (
                "OpenAI connection error | "
                "latency=%.2fs | error=%s"
            ),
            time.monotonic() - started_at,
            str(error),
        )

    except openai.RateLimitError as error:

        logger.warning(
            (
                "OpenAI rate limit | "
                "latency=%.2fs | error=%s"
            ),
            time.monotonic() - started_at,
            str(error),
        )

    except openai.APIStatusError as error:

        logger.error(
            (
                "OpenAI API status error | "
                "status=%s | request_id=%s | "
                "latency=%.2fs"
            ),
            error.status_code,
            getattr(
                error,
                "request_id",
                None,
            ),
            time.monotonic() - started_at,
        )

    except openai.APIError as error:

        logger.error(
            (
                "OpenAI API error | "
                "latency=%.2fs | error=%s"
            ),
            time.monotonic() - started_at,
            str(error),
        )

    except Exception:

        logger.exception(
            (
                "Unexpected OpenAI error | "
                "latency=%.2fs"
            ),
            time.monotonic() - started_at,
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
        get_fallback_response(
            language
        )
    )

    for attempt in range(
        1,
        STREAM_MAX_ATTEMPTS + 1
    ):

        has_output = False
        first_token_logged = False

        attempt_started_at = (
            time.monotonic()
        )

        try:
            logger.info(
                (
                    "OpenAI stream attempt started | "
                    "attempt=%s"
                ),
                attempt,
            )

            stream = (
                client.with_options(
                    timeout=STREAM_TIMEOUT,

                    # Streaming retry is controlled manually
                    # to avoid duplicate partial answers.
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

                    if not delta:
                        continue

                    if not first_token_logged:

                        first_token_latency = (
                            time.monotonic()
                            - attempt_started_at
                        )

                        logger.info(
                            (
                                "OpenAI first token | "
                                "attempt=%s | "
                                "latency=%.2fs"
                            ),
                            attempt,
                            first_token_latency,
                        )

                        first_token_logged = True

                    has_output = True

                    yield delta

            total_latency = (
                time.monotonic()
                - attempt_started_at
            )

            if has_output:

                logger.info(
                    (
                        "OpenAI stream finished | "
                        "attempt=%s | "
                        "total=%.2fs"
                    ),
                    attempt,
                    total_latency,
                )

                return

            logger.warning(
                (
                    "OpenAI stream returned empty output | "
                    "attempt=%s | total=%.2fs"
                ),
                attempt,
                total_latency,
            )

    # =================================================
    # TIMEOUT
    # =================================================

        except openai.APITimeoutError as error:

            elapsed = (
                time.monotonic()
                - attempt_started_at
            )

            logger.warning(
                (
                    "OpenAI streaming timeout | "
                    "attempt=%s | "
                    "elapsed=%.2fs | "
                    "error=%s"
                ),
                attempt,
                elapsed,
                str(error),
            )

    # =================================================
    # CONNECTION ERROR
    # =================================================

        except openai.APIConnectionError as error:

            elapsed = (
                time.monotonic()
                - attempt_started_at
            )

            logger.error(
                (
                    "OpenAI streaming connection error | "
                    "attempt=%s | "
                    "elapsed=%.2fs | "
                    "error=%s"
                ),
                attempt,
                elapsed,
                str(error),
            )

    # =================================================
    # RATE LIMIT
    # =================================================

        except openai.RateLimitError as error:

            elapsed = (
                time.monotonic()
                - attempt_started_at
            )

            logger.warning(
                (
                    "OpenAI streaming rate limit | "
                    "attempt=%s | "
                    "elapsed=%.2fs | "
                    "error=%s"
                ),
                attempt,
                elapsed,
                str(error),
            )

    # =================================================
    # API STATUS ERROR
    # =================================================

        except openai.APIStatusError as error:

            elapsed = (
                time.monotonic()
                - attempt_started_at
            )

            logger.error(
                (
                    "OpenAI streaming API status error | "
                    "attempt=%s | "
                    "status=%s | "
                    "request_id=%s | "
                    "elapsed=%.2fs"
                ),
                attempt,
                error.status_code,
                getattr(
                    error,
                    "request_id",
                    None,
                ),
                elapsed,
            )

            # Permanent 4xx error:
            # retrying usually will not help.
            if (
                error.status_code
                and error.status_code < 500
                and error.status_code != 429
            ):
                break

    # =================================================
    # GENERIC OPENAI ERROR
    # =================================================

        except openai.APIError as error:

            elapsed = (
                time.monotonic()
                - attempt_started_at
            )

            logger.error(
                (
                    "OpenAI streaming API error | "
                    "attempt=%s | "
                    "elapsed=%.2fs | "
                    "error=%s"
                ),
                attempt,
                elapsed,
                str(error),
            )

    # =================================================
    # UNEXPECTED ERROR
    # =================================================

        except Exception:

            elapsed = (
                time.monotonic()
                - attempt_started_at
            )

            logger.exception(
                (
                    "Unexpected OpenAI streaming error | "
                    "attempt=%s | "
                    "elapsed=%.2fs"
                ),
                attempt,
                elapsed,
            )

        # =================================================
        # DO NOT RETRY AFTER PARTIAL OUTPUT
        # =================================================

        if has_output:

            logger.warning(
                (
                    "OpenAI stream interrupted after output | "
                    "attempt=%s | retry_skipped=true"
                ),
                attempt,
            )

            return

        # =================================================
        # RETRY
        # =================================================

        if attempt < STREAM_MAX_ATTEMPTS:

            delay = (
                STREAM_RETRY_DELAYS.get(
                    attempt,
                    3.0,
                )
            )

            logger.info(
                (
                    "Retrying OpenAI stream | "
                    "next_attempt=%s | "
                    "delay=%.1fs"
                ),
                attempt + 1,
                delay,
            )

            time.sleep(
                delay
            )

    # =====================================================
    # FINAL FALLBACK
    # =====================================================

    logger.error(
        (
            "OpenAI stream failed after all attempts | "
            "attempts=%s"
        ),
        STREAM_MAX_ATTEMPTS,
    )

    yield fallback_response