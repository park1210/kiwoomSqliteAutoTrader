from app.scenarios.base import BaseScenario


class TradingLoopScenario(BaseScenario):
    def run(self):
        from app.kiwoom.kiwoom_api import KiwoomAPI
        from app.trading.trading_loop import TradingLoop
        from config import ENABLE_TRADING_LOOP

        self.notifier.send(
            title="v8 자동 운영 루프 준비",
            message=(
                "키움 OpenAPI+ 로그인 창이 뜨면 로그인하세요.\n"
                "처음에는 주문 관련 설정을 모두 False로 두고 dry-run으로 테스트하세요.\n"
                f"ENABLE_TRADING_LOOP={ENABLE_TRADING_LOOP}"
            ),
        )

        if not ENABLE_TRADING_LOOP:
            self.notifier.send(
                title="v8 자동 운영 루프 비활성화",
                message="ENABLE_TRADING_LOOP=False 상태입니다.",
            )
            return

        kiwoom_api = KiwoomAPI()
        kiwoom_api.login()

        account_no = self.get_first_account(kiwoom_api)
        self.notify_account_server(kiwoom_api, account_no)

        trading_loop = TradingLoop(
            repository=self.repository,
            notifier=self.notifier,
            kiwoom_api=kiwoom_api,
            account_no=account_no,
        )
        trading_loop.run()

        self.repository.save_system_log(
            level="INFO",
            message="v8 trading loop finished",
            detail=None,
        )

