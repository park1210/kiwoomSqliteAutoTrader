from app.scenarios.base import BaseScenario


class CodeConditionScanScenario(BaseScenario):
    def run(self):
        from app.kiwoom.kiwoom_api import KiwoomAPI
        from app.strategy.code_condition_engine import CodeConditionEngine
        from app.trading.position_manager import PositionManager
        from config import CODE_CONDITION_ENABLE

        self.notifier.send(
            title="v5.1 코드 기반 조건검색 테스트 시작",
            message=(
                "키움 HTS 조건검색식을 사용하지 않고, "
                "settings.yaml에 정의한 universe와 filter로 후보 종목을 찾습니다.\n"
                f"CODE_CONDITION_ENABLE={CODE_CONDITION_ENABLE}"
            ),
        )

        if not CODE_CONDITION_ENABLE:
            self.notifier.send(
                title="v5.1 코드 기반 조건검색 비활성화",
                message="CODE_CONDITION_ENABLE=False 상태입니다.",
            )
            return

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

        engine = CodeConditionEngine(
            repository=self.repository,
            notifier=self.notifier,
        )

        result = engine.run(
            kiwoom_api=kiwoom_api,
            account_no=account_no,
            position_manager=position_manager,
        )

        self.repository.save_system_log(
            level="INFO",
            message="v5.1 code condition test finished",
            detail=str(result),
        )

