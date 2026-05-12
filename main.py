from app.database.db import init_db
from app.trading.trading_engine import TradingEngine
from app.utils.logger import setup_logger


def main():
    logger = setup_logger()
    logger.info("프로그램 시작")

    try:
        init_db()

        engine = TradingEngine()
        engine.run_v1_simulation()

        logger.info("v1 시뮬레이션 정상 종료")

    except Exception as e:
        logger.exception(f"프로그램 실행 중 오류 발생: {e}")


if __name__ == "__main__":
    main()