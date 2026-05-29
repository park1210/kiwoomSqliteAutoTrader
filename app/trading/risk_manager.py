from config import ALLOW_LIVE_ORDER, ENABLE_ORDER, MAX_BUY_AMOUNT_PER_STOCK


class RiskManager:
    def validate_order_environment(self, mode, server_gubun):
        """
        server_gubun:
        - 키움 모의투자 서버는 보통 '1'
        - 실전 서버는 빈 문자열 또는 다른 값일 수 있음
        """

        if not ENABLE_ORDER:
            return False, "ENABLE_ORDER=False 상태이므로 실제 주문을 차단합니다."

        if mode == "paper":
            if server_gubun != "1":
                return False, (
                    "MODE=paper인데 현재 접속 서버가 모의투자 서버가 아닙니다. "
                    f"server_gubun={server_gubun!r}"
                )

        if mode == "live":
            if not ALLOW_LIVE_ORDER:
                return False, "ALLOW_LIVE_ORDER=False 상태이므로 실전 주문을 차단합니다."

        return True, "주문 환경 확인 완료"

    def validate_buy_amount(self, quantity, current_price):
        if current_price is None:
            return False, "현재가를 확인할 수 없어 주문을 차단합니다."

        estimated_amount = quantity * current_price

        if estimated_amount > MAX_BUY_AMOUNT_PER_STOCK:
            return False, (
                f"종목당 최대 매수 금액 초과: "
                f"{estimated_amount} > {MAX_BUY_AMOUNT_PER_STOCK}"
            )

        return True, f"예상 주문금액 확인 완료: {estimated_amount}"