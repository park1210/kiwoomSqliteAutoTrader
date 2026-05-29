from app.scenarios.base import BaseScenario


class PositionTrackingScenario(BaseScenario):
    def run(self):
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

        account_no = self.get_first_account(kiwoom_api)
        self.notify_account_server(kiwoom_api, account_no)

        position_manager = PositionManager(
            repository=self.repository,
            notifier=self.notifier,
        )

        position_manager.sync_account_state(
            kiwoom_api=kiwoom_api,
            account_no=account_no,
        )
        position_manager.sync_unfilled_orders(
            kiwoom_api=kiwoom_api,
            account_no=account_no,
        )

        snapshot = kiwoom_api.get_current_price(TEST_ORDER_CODE)
        self.save_snapshot_and_notify(snapshot)

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

