import sys

from PyQt5.QtWidgets import QApplication

from app.database.db import init_db
from app.trading.trading_engine import TradingEngine
from app.utils.logger import setup_logger
from config import RUN_VERSION


def main():
    qt_app = QApplication(sys.argv)

    logger = setup_logger()
    logger.info("프로그램 시작")

    try:
        init_db()

        engine = TradingEngine()
        engine.run(RUN_VERSION)

        logger.info(f"{RUN_VERSION} 실행 정상 종료")

    except Exception as e:
        logger.exception(f"프로그램 실행 중 오류 발생: {e}")

    qt_app.quit()


if __name__ == "__main__":
    main()
