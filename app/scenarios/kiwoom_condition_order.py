from app.scenarios.base import BaseScenario


class KiwoomConditionOrderScenario(BaseScenario):
    def run(self):
        from app.kiwoom.condition_manager import ConditionManager
        from app.kiwoom.kiwoom_api import KiwoomAPI
        from app.trading.order_manager import OrderManager
        from app.trading.position_manager import PositionManager
        from config import ENABLE_CONDITION_ORDER

        self.notifier.send(
            title="v6 조건검색 기반 주문 테스트 시작",
            message=(
                "키움 OpenAPI+ 로그인 창이 뜨면 로그인하세요.\n"
                "조건검색 편입 종목을 주문 후보로 평가합니다.\n"
                f"현재 ENABLE_CONDITION_ORDER={ENABLE_CONDITION_ORDER}\n"
                "처음에는 False 상태로 평가만 확인하는 것을 권장합니다."
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
        condition_manager = ConditionManager(
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

        condition = condition_manager.load_and_select_condition(kiwoom_api)
        condition_result = condition_manager.run_condition_watch(
            kiwoom_api=kiwoom_api,
            condition=condition,
        )

        candidates = condition_manager.build_order_candidates(condition_result)
        decision_results = condition_manager.evaluate_and_order_candidates(
            kiwoom_api=kiwoom_api,
            account_no=account_no,
            candidates=candidates,
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
            message="v6 condition paper order test finished",
            detail=str(decision_results),
        )

        self.notifier.send(
            title="v6 조건검색 기반 주문 테스트 종료",
            message=f"결과: {decision_results}",
        )

