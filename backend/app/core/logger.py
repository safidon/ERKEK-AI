import logging
from pathlib import Path


# =====================================================
# LOG DIRECTORY
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(
    parents=True,
    exist_ok=True
)

LOG_FILE = LOG_DIR / "erkek_ai.log"


# =====================================================
# LOGGER
# =====================================================

logger = logging.getLogger("ERKEK_AI")

logger.setLevel(logging.INFO)


# Handler бірнеше рет қосылып кетпесін
if not logger.handlers:

    # =============================================
    # FORMAT
    # =============================================

    formatter = logging.Formatter(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    )

    # =============================================
    # FILE HANDLER
    # =============================================

    file_handler = logging.FileHandler(
        LOG_FILE,
        encoding="utf-8"
    )

    file_handler.setLevel(
        logging.INFO
    )

    file_handler.setFormatter(
        formatter
    )

    logger.addHandler(
        file_handler
    )

    # =============================================
    # CONSOLE HANDLER
    # =============================================

    console_handler = logging.StreamHandler()

    console_handler.setLevel(
        logging.INFO
    )

    console_handler.setFormatter(
        formatter
    )

    logger.addHandler(
        console_handler
    )