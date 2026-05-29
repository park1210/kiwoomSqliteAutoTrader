from app.scenarios.base import BaseScenario


class StrategyPluginTestScenario(BaseScenario):
    def run(self):
        from app.kiwoom.kiwoom_api import KiwoomAPI
        from app.strategy.strategy_runner import StrategyRunner
        from config import STRATEGY_PLUGIN_ENABLE

        self.notifier.send(
            title="v12 전략 플러그인 테스트 시작",
            message=(
                "다른 전략 프로젝트에서 만든 전략을 연결하기 위한 "
                "공통 전략 플러그인 인터페이스를 테스트합니다.\n"
                f"STRATEGY_PLUGIN_ENABLE={STRATEGY_PLUGIN_ENABLE}"
            ),
        )

        if not STRATEGY_PLUGIN_ENABLE:
            self.notifier.send(
                title="v12 전략 플러그인 비활성화",
                message="STRATEGY_PLUGIN_ENABLE=False 상태입니다.",
            )
            return

        kiwoom_api = KiwoomAPI()
        kiwoom_api.login()

        account_no = self.get_first_account(kiwoom_api)
        self.notify_account_server(kiwoom_api, account_no)

        runner = StrategyRunner(
            repository=self.repository,
            notifier=self.notifier,
        )
        result = runner.run(kiwoom_api=kiwoom_api)

        self.repository.save_system_log(
            level="INFO",
            message="v12 strategy plugin test finished",
            detail=str(result),
        )

