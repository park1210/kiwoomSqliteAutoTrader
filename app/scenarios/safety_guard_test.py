from app.scenarios.base import BaseScenario


class SafetyGuardTestScenario(BaseScenario):
    def run(self):
        from app.kiwoom.kiwoom_api import KiwoomAPI
        from app.trading.safety_guard import SafetyGuard

        self.notifier.send(
            title="v11 안전장치 테스트 시작",
            message=(
                "실제 주문은 보내지 않고 SafetyGuard만 직접 테스트합니다.\n"
                "블랙리스트, 주문 금액, 일일 주문 횟수 등을 확인합니다."
            ),
        )

        kiwoom_api = KiwoomAPI()
        kiwoom_api.login()

        account_no = self.get_first_account(kiwoom_api)
        self.notify_account_server(kiwoom_api, account_no)

        guard = SafetyGuard(
            repository=self.repository,
            notifier=self.notifier,
        )

        test_cases = [
            {
                "code": "900300",
                "name": "오가닉티코스메틱",
                "order_type": "BUY",
                "quantity": 1,
                "price": 100,
                "current_price": 100,
            },
            {
                "code": "005930",
                "name": "삼성전자",
                "order_type": "BUY",
                "quantity": 1,
                "price": 0,
                "current_price": 300000,
            },
        ]

        results = []

        for case in test_cases:
            ok, reason = guard.validate_order(
                kiwoom_api=kiwoom_api,
                code=case["code"],
                name=case["name"],
                order_type=case["order_type"],
                quantity=case["quantity"],
                price=case["price"],
                current_price=case["current_price"],
            )

            results.append(
                {
                    **case,
                    "passed": ok,
                    "reason": reason,
                }
            )

        self.notifier.send(
            title="v11 안전장치 테스트 완료",
            message=str(results),
        )

        self.repository.save_system_log(
            level="INFO",
            message="v11 safety guard test finished",
            detail=str(results),
        )

