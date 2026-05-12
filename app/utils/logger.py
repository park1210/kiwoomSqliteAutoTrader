import logging

from config import LOG_DIR


def setup_logger():
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    log_file = LOG_DIR / "app.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    return logging.getLogger("kiwoom_sqlite_auto_trader")