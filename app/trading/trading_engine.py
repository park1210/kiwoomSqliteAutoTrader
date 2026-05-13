from datetime import datetime, timedelta

from app.database.repository import TradingRepository
from app.notifier.console_notifier import ConsoleNotifier


class TradingEngine:
    def __init__(self):
        self.repository = TradingRepository()
        self.notifier = ConsoleNotifier()

    def run_v1_simulation(self):
        """
        v1 실행 흐름:
        1. 임시 종목 등록
        2. 임시 5분봉 데이터 생성
        3. DB 저장
        4. DB에서 다시 조회
        5. 이동평균 전략 실행
        6. 신호 저장
        7. 콘솔 알림

        주의:
        v1은 pandas 기반 MovingAverageStrategy를 사용한다.
        현재 v2 환경에서는 pandas를 제거했으므로,
        RUN_VERSION="v1"로 실행하면 pandas가 필요하다.
        """
        from app.strategy.moving_average_strategy import MovingAverageStrategy
        from config import LONG_WINDOW, SHORT_WINDOW

        strategy = MovingAverageStrategy(
            short_window=SHORT_WINDOW,
            long_window=LONG_WINDOW,
        )

        code = "005930"
        name = "삼성전자"

        self.repository.upsert_stock(code=code, name=name, market="KOSPI")

        price_rows = self._create_sample_minute_data()
        self.repository.save_price_minute(code=code, price_rows=price_rows)

        loaded_price_data = self.repository.get_price_minute(code=code, limit=100)

        signal = strategy.generate_signal(
            code=code,
            price_data=loaded_price_data,
        )

        signal_id = self.repository.save_signal(
            code=code,
            signal_type=signal["signal_type"],
            strategy_name=strategy.name,
            price=signal["price"],
            reason=signal["reason"],
        )

        title = f"{name} 신호 발생: {signal['signal_type']}"
        message = (
            f"종목코드: {code}\n"
            f"종목명: {name}\n"
            f"전략: {strategy.name}\n"
            f"현재가: {signal['price']}\n"
            f"신호: {signal['signal_type']}\n"
            f"이유: {signal['reason']}\n"
            f"DB signal_id: {signal_id}"
        )

        self.repository.save_notification(
            channel="ConsoleNotifier",
            title=title,
            message=message,
            status="SENT",
        )

        self.notifier.send(title, message)

    def run_v2_kiwoom_snapshot(self):
        """
        v2 실행 흐름:
        1. 키움 OpenAPI+ ActiveX 생성
        2. 로그인
        3. 삼성전자 종목명 조회
        4. 삼성전자 현재가 조회
        5. stocks 테이블 저장
        6. price_snapshot 테이블 저장
        7. 콘솔 알림
        """
        from app.kiwoom.kiwoom_api import KiwoomAPI

        code = "005930"

        self.notifier.send(
            title="키움 로그인 시작",
            message=(
                "키움 OpenAPI+ 로그인 창이 뜨면 로그인하세요.\n"
                "모의투자를 사용할 경우 로그인 창에서 모의투자 서버를 선택하세요."
            ),
        )

        kiwoom_api = KiwoomAPI()
        kiwoom_api.login()

        snapshot = kiwoom_api.get_current_price(code)

        self.repository.upsert_stock(
            code=snapshot["code"],
            name=snapshot["name"],
            market="KOSPI",
        )

        snapshot_id = self.repository.save_price_snapshot(
            code=snapshot["code"],
            name=snapshot["name"],
            current_price=snapshot["current_price"],
            volume=snapshot["volume"],
            raw_current_price=snapshot["raw_current_price"],
            raw_volume=snapshot["raw_volume"],
        )

        title = f"{snapshot['name']} 현재가 조회 완료"
        message = (
            f"종목코드: {snapshot['code']}\n"
            f"종목명: {snapshot['name']}\n"
            f"현재가: {snapshot['current_price']}\n"
            f"거래량: {snapshot['volume']}\n"
            f"원본 현재가: {snapshot['raw_current_price']}\n"
            f"원본 거래량: {snapshot['raw_volume']}\n"
            f"DB snapshot_id: {snapshot_id}"
        )

        self.repository.save_notification(
            channel="ConsoleNotifier",
            title=title,
            message=message,
            status="SENT",
        )

        self.notifier.send(title, message)

    def _create_sample_minute_data(self):
        start_time = datetime(2026, 5, 8, 9, 0, 0)

        closes = [
            70000, 69900, 69800, 69700, 69600,
            69500, 69400, 69300, 69200, 69100,
            69000, 68900, 68800, 68700, 68600,
            68500, 68400, 68300, 68200, 68100,
            68200, 68400, 68700, 69100, 69600,
            70200, 70900, 71700, 72600, 73600,
        ]

        rows = []

        for i, close_price in enumerate(closes):
            current_time = start_time + timedelta(minutes=5 * i)

            rows.append(
                {
                    "datetime": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "open": close_price - 100,
                    "high": close_price + 200,
                    "low": close_price - 200,
                    "close": close_price,
                    "volume": 100000 + i * 1000,
                }
            )

        return rows