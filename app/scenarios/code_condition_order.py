import json

from app.scenarios.base import BaseScenario


class CodeConditionOrderScenario(BaseScenario):
    def run(self):
        from app.kiwoom.kiwoom_api import KiwoomAPI
        from app.strategy.code_condition_engine import CodeConditionEngine
        from app.trading.code_condition_order_service import CodeConditionOrderService
        from app.trading.order_manager import OrderManager
        from app.trading.position_manager import PositionManager
        from config import CODE_CONDITION_ENABLE_ORDER

        self.notifier.send(
            title="v6.1 코드 조건검색 기반 주문 평가 시작",
            message=(
                "키움 HTS 조건검색식이 아니라 코드/YAML 기반 조건검색 결과를 "
                "주문 후보로 평가합니다.\n"
                f"CODE_CONDITION_ENABLE_ORDER={CODE_CONDITION_ENABLE_ORDER}\n"
                "처음에는 False 상태로 dry-run 평가만 확인하세요."
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

        position_manager.sync_account_state(
            kiwoom_api=kiwoom_api,
            account_no=account_no,
        )
        position_manager.sync_unfilled_orders(
            kiwoom_api=kiwoom_api,
            account_no=account_no,
        )

        code_condition_engine = CodeConditionEngine(
            repository=self.repository,
            notifier=self.notifier,
        )
        code_condition_result = code_condition_engine.run(
            kiwoom_api=kiwoom_api,
            account_no=account_no,
            position_manager=position_manager,
        )

        code_condition_order_service = CodeConditionOrderService(
            repository=self.repository,
            notifier=self.notifier,
        )

        candidates = code_condition_order_service.build_order_candidates(
            code_condition_result
        )
        decision_results = code_condition_order_service.evaluate_and_order_candidates(
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
            message="v6.1 code condition order test finished",
            detail=str(decision_results),
        )

        self.notifier.send(
            title="v6.1 코드 조건검색 기반 주문 평가 종료",
            message=json.dumps(decision_results, ensure_ascii=False, indent=2),
        )

