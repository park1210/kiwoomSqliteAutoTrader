from app.scenarios.base import BaseScenario


class PaperOrderTestScenario(BaseScenario):
    def run(self):
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

        account_no = self.get_first_account(kiwoom_api)
        self.notify_account_server(kiwoom_api, account_no)

        snapshot = kiwoom_api.get_current_price(TEST_ORDER_CODE)
        self.save_snapshot_and_notify(snapshot)

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

