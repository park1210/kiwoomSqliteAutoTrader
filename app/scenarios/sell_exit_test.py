from app.scenarios.base import BaseScenario


class SellExitTestScenario(BaseScenario):
    def run(self):
        from app.kiwoom.kiwoom_api import KiwoomAPI
        from app.trading.order_manager import OrderManager
        from app.trading.position_manager import PositionManager
        from app.trading.sell_manager import SellManager
        from config import ENABLE_SELL_ORDER

        self.notifier.send(
            title="v7 매도/청산 로직 테스트 시작",
            message=(
                "키움 OpenAPI+ 로그인 창이 뜨면 로그인하세요.\n"
                "보유 종목의 수익률을 기준으로 익절/손절/보유를 판단합니다.\n"
                f"현재 ENABLE_SELL_ORDER={ENABLE_SELL_ORDER}\n"
                "처음에는 False 상태로 판단만 확인하는 것을 권장합니다."
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
        order_manager = OrderManager(
            repository=self.repository,
            notifier=self.notifier,
            position_manager=position_manager,
        )
        sell_manager = SellManager(
            repository=self.repository,
            notifier=self.notifier,
        )

        account_state = position_manager.sync_account_state(
            kiwoom_api=kiwoom_api,
            account_no=account_no,
        )
        position_manager.sync_unfilled_orders(
            kiwoom_api=kiwoom_api,
            account_no=account_no,
        )

        positions = account_state.get("positions", [])
        if not positions:
            self.notifier.send(
                title="매도 판단 대상 없음",
                message="현재 보유 종목이 없습니다.",
            )
            return

        sell_decisions = sell_manager.evaluate_positions(positions)
        results = sell_manager.execute_sell_decisions(
            kiwoom_api=kiwoom_api,
            account_no=account_no,
            sell_decisions=sell_decisions,
            order_manager=order_manager,
            position_manager=position_manager,
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
            message="v7 sell exit test finished",
            detail=str(results),
        )

        self.notifier.send(
            title="v7 매도/청산 로직 테스트 종료",
            message=f"결과: {results}",
        )

