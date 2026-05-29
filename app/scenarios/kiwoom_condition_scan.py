from app.scenarios.base import BaseScenario


class KiwoomConditionScanScenario(BaseScenario):
    def run(self):
        from app.kiwoom.condition_manager import ConditionManager
        from app.kiwoom.kiwoom_api import KiwoomAPI

        self.notifier.send(
            title="v5 조건검색 테스트 시작",
            message=(
                "키움 OpenAPI+ 로그인 창이 뜨면 로그인하세요.\n"
                "조건검색식은 키움 HTS에서 미리 저장되어 있어야 합니다.\n"
                "v5 기본 설정은 주문하지 않고 조건검색 이벤트만 저장합니다."
            ),
        )

        kiwoom_api = KiwoomAPI()
        kiwoom_api.login()

        account_no = self.get_first_account(kiwoom_api)
        self.notify_account_server(kiwoom_api, account_no)

        condition_manager = ConditionManager(
            repository=self.repository,
            notifier=self.notifier,
        )

        condition = condition_manager.load_and_select_condition(kiwoom_api)
        result = condition_manager.run_condition_watch(
            kiwoom_api=kiwoom_api,
            condition=condition,
        )

        self.repository.save_system_log(
            level="INFO",
            message="v5 condition search test finished",
            detail=str(result),
        )

