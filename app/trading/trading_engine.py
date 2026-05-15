from datetime import datetime, timedelta

from app.database.repository import TradingRepository
from app.notifier.console_notifier import ConsoleNotifier


class TradingEngine:
    def __init__(self):
        self.repository = TradingRepository()
        self.notifier = ConsoleNotifier()

    def run_v1_simulation(self):
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
        from app.kiwoom.kiwoom_api import KiwoomAPI

        code = "005930"

        self._notify_login_start()

        kiwoom_api = KiwoomAPI()
        kiwoom_api.login()

        snapshot = kiwoom_api.get_current_price(code)

        self._save_snapshot_and_notify(snapshot)

    def run_v3_paper_order_test(self):
        from app.kiwoom.kiwoom_api import KiwoomAPI
        from app.trading.order_manager import OrderManager
        from config import ENABLE_ORDER, TEST_ORDER_CODE, TEST_ORDER_QTY

        self.notifier.send(
            title="v3 모의투자 주문 테스트 시작",
            message=(
                "키움 OpenAPI+ 로그인 창이 뜨면 로그인하세요.\n"
                "반드시 모의투자 서버로 로그인하세요.\n"
                f"현재 ENABLE_ORDER={ENABLE_ORDER}"
            ),
        )

        kiwoom_api = KiwoomAPI()
        kiwoom_api.login()

        account_no = self._get_first_account(kiwoom_api)
        self._notify_account_server(kiwoom_api, account_no)

        snapshot = kiwoom_api.get_current_price(TEST_ORDER_CODE)
        self._save_snapshot_and_notify(snapshot)

        order_manager = OrderManager(
            repository=self.repository,
            notifier=self.notifier,
        )

        result = order_manager.paper_market_buy(
            kiwoom_api=kiwoom_api,
            account_no=account_no,
            code=snapshot["code"],
            name=snapshot["name"],
            quantity=TEST_ORDER_QTY,
            current_price=snapshot["current_price"],
        )

        self.repository.save_system_log(
            level="INFO",
            message="v3 paper order test finished",
            detail=str(result),
        )

    def run_v4_order_position_tracking(self):
        from app.kiwoom.kiwoom_api import KiwoomAPI
        from app.trading.order_manager import OrderManager
        from app.trading.position_manager import PositionManager
        from config import ENABLE_ORDER, TEST_ORDER_CODE, TEST_ORDER_QTY

        self.notifier.send(
            title="v4 주문/잔고 추적 테스트 시작",
            message=(
                "키움 OpenAPI+ 로그인 창이 뜨면 로그인하세요.\n"
                "반드시 모의투자 서버로 로그인하세요.\n"
                f"현재 ENABLE_ORDER={ENABLE_ORDER}"
            ),
        )

        kiwoom_api = KiwoomAPI()
        kiwoom_api.login()

        account_no = self._get_first_account(kiwoom_api)
        self._notify_account_server(kiwoom_api, account_no)

        position_manager = PositionManager(
            repository=self.repository,
            notifier=self.notifier,
        )

        # 1. 주문 전 계좌/보유 종목 동기화
        position_manager.sync_account_state(
            kiwoom_api=kiwoom_api,
            account_no=account_no,
        )

        # 2. 주문 전 미체결 주문 동기화
        position_manager.sync_unfilled_orders(
            kiwoom_api=kiwoom_api,
            account_no=account_no,
        )

        # 3. 현재가 조회 및 저장
        snapshot = kiwoom_api.get_current_price(TEST_ORDER_CODE)
        self._save_snapshot_and_notify(snapshot)

        # 4. 중복 보유/미체결 확인 후 주문
        order_manager = OrderManager(
            repository=self.repository,
            notifier=self.notifier,
            position_manager=position_manager,
        )

        result = order_manager.paper_market_buy(
            kiwoom_api=kiwoom_api,
            account_no=account_no,
            code=snapshot["code"],
            name=snapshot["name"],
            quantity=TEST_ORDER_QTY,
            current_price=snapshot["current_price"],
        )

        # 5. 주문 후 계좌/미체결 재동기화
        position_manager.sync_account_state(
            kiwoom_api=kiwoom_api,
            account_no=account_no,
        )

        position_manager.sync_unfilled_orders(
            kiwoom_api=kiwoom_api,
            account_no=account_no,
        )

        self.repository.save_system_log(
            level="INFO",
            message="v4 order position tracking finished",
            detail=str(result),
        )

    def run_show_account_password_window(self):
        from app.kiwoom.kiwoom_api import KiwoomAPI

        self.notifier.send(
            title="계좌비밀번호 입력창 열기",
            message="로그인 후 계좌비밀번호 입력창이 열립니다.",
        )

        kiwoom_api = KiwoomAPI()
        kiwoom_api.login()
        kiwoom_api.show_account_password_window()

        self.notifier.send(
            title="계좌비밀번호 입력창 확인",
            message="창이 열리면 계좌비밀번호를 입력하고 등록/AUTO 체크 후 닫으세요.",
        )

    def _notify_login_start(self):
        self.notifier.send(
            title="키움 로그인 시작",
            message=(
                "키움 OpenAPI+ 로그인 창이 뜨면 로그인하세요.\n"
                "모의투자를 사용할 경우 로그인 창에서 모의투자 서버를 선택하세요."
            ),
        )

    def _get_first_account(self, kiwoom_api):
        accounts = kiwoom_api.get_account_list()

        if not accounts:
            raise RuntimeError("계좌번호를 가져오지 못했습니다.")

        return accounts[0]

    def _notify_account_server(self, kiwoom_api, account_no):
        server_gubun = kiwoom_api.get_server_gubun()

        self.notifier.send(
            title="계좌/서버 확인",
            message=(
                f"계좌번호: {account_no}\n"
                f"server_gubun: {server_gubun!r}\n"
                "server_gubun이 '1'이면 일반적으로 모의투자 서버입니다."
            ),
        )

    def _save_snapshot_and_notify(self, snapshot):
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

        self.notifier.send(
            title=f"{snapshot['name']} 현재가 조회 완료",
            message=(
                f"종목코드: {snapshot['code']}\n"
                f"종목명: {snapshot['name']}\n"
                f"현재가: {snapshot['current_price']}\n"
                f"거래량: {snapshot['volume']}\n"
                f"원본 현재가: {snapshot['raw_current_price']}\n"
                f"원본 거래량: {snapshot['raw_volume']}\n"
                f"DB snapshot_id: {snapshot_id}"
            ),
        )

        return snapshot_id

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