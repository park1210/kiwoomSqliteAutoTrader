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

        if RUN_VERSION == "v1":
            engine.run_v1_simulation()
        elif RUN_VERSION == "v2":
            engine.run_v2_kiwoom_snapshot()
        elif RUN_VERSION == "v3":
            engine.run_v3_paper_order_test()
        elif RUN_VERSION == "v4":
            engine.run_v4_order_position_tracking()
        elif RUN_VERSION == "v5":
            engine.run_v5_condition_search_test()
        elif RUN_VERSION == "password":
            engine.run_show_account_password_window()
        else:
            raise ValueError(f"알 수 없는 RUN_VERSION: {RUN_VERSION}")

        logger.info(f"{RUN_VERSION} 실행 정상 종료")

    except Exception as e:
        logger.exception(f"프로그램 실행 중 오류 발생: {e}")

    qt_app.quit()


if __name__ == "__main__":
    main()