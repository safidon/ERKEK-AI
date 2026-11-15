"""
Email жіберу (SMTP, стандартты кітапхана).

SMTP_HOST бапталмаса хат жіберілмейді:
- development: хаттың мәтіні логқа жазылады (сілтемені сол жерден алуға болады);
- production: қате логқа жазылады.
"""

import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr

from app.core.config import (
    IS_PRODUCTION,
    SMTP_FROM,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_SECURITY,
    SMTP_USER,
)
from app.core.logger import logger


def is_email_configured() -> bool:
    return bool(SMTP_HOST and SMTP_FROM)


def send_email(
    to: str,
    subject: str,
    text: str,
    html: str | None = None,
) -> bool:
    """
    Хат жібереді. Сәтті болса True қайтарады.
    Exception шығармайды — қатені логқа жазады.
    """

    if not is_email_configured():
        if IS_PRODUCTION:
            logger.error(
                "Email not sent: SMTP is not configured | subject=%s",
                subject,
            )
        else:
            logger.warning(
                "SMTP is not configured (dev): email printed to log\n"
                "To: %s\nSubject: %s\n\n%s",
                to,
                subject,
                text,
            )

        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = formataddr(("ERKEK AI", SMTP_FROM))
    message["To"] = to
    message.set_content(text)

    if html:
        message.add_alternative(html, subtype="html")

    try:
        context = ssl.create_default_context()

        if SMTP_SECURITY == "ssl":
            server = smtplib.SMTP_SSL(
                SMTP_HOST, SMTP_PORT, timeout=20, context=context
            )
        else:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20)

        with server:
            if SMTP_SECURITY == "starttls":
                server.starttls(context=context)

            if SMTP_USER:
                server.login(SMTP_USER, SMTP_PASSWORD)

            server.send_message(message)

        logger.info("Email sent | subject=%s", subject)
        return True

    except Exception:
        logger.exception("Email sending failed | subject=%s", subject)
        return False
