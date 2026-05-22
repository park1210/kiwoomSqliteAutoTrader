import json
from datetime import datetime, timedelta

from config import (
    MARKET_CLOSE_TIME,
    MARKET_OPEN_TIME,
    MODE,
    SAFETY_BLACKLIST,
    SAFETY_BLOCK_LIVE_SERVER_ORDER,
    SAFETY_BLOCK_NEAR_MARKET_CLOSE,
    SAFETY_BLOCK_NEAR_MARKET_OPEN,
    SAFETY_ENABLE,
    SAFETY_LIVE_ORDER_APPROVAL_TEXT,
    SAFETY_MARKET_CLOSE_BUFFER_MINUTES,
    SAFETY_MARKET_OPEN_BUFFER_MINUTES,
    SAFETY_MAX_DAILY_BUY_AMOUNT,
    SAFETY_MAX_DAILY_BUY_ORDERS,
    SAFETY_MAX_DAILY_ORDERS,
    SAFETY_MAX_DAILY_ORDERS_PER_CODE,
    SAFETY_MAX_DAILY_SELL_ORDERS,
    SAFETY_MAX_SINGLE_ORDER_AMOUNT,
    SAFETY_REQUIRE_LIVE_ORDER_APPROVAL,
    SAFETY_WHITELIST,
)


class SafetyGuard:
    def __init__(self, repository, notifier):
        self.repository = repository
        self.notifier = notifier

    def validate_order(
        self,
        kiwoom_api,
        code,
        name,
        order_type,
        quantity,
        price,
        current_price=None,
        live_approval_text=None,
    ):
        """
        주문 직전 최종 안전장치.

        order_type:
        - BUY
        - SELL
        """
        estimated_price = current_price or price or 0
        estimated_amount = int(estimated_price) * int(quantity)

        context = {
            "code": code,
            "name": name,
            "order_type": order_type,
            "quantity": quantity,
            "price": price,
            "current_price": current_price,
            "estimated_price": estimated_price,
            "estimated_amount": estimated_amount,
            "mode": MODE,
            "server_gubun": kiwoom_api.get_server_gubun(),
        }

        if not SAFETY_ENABLE:
            return self._pass(
                code,
                name,
                order_type,
                quantity,
                price,
                estimated_amount,
                "SAFETY_ENABLE=False이므로 안전장치 검사를 건너뜁니다.",
                context,
            )

        checks = [
            self._check_quantity(quantity),
            self._check_blacklist(code),
            self._check_whitelist(code),
            self._check_single_order_amount(estimated_amount),
            self._check_daily_order_count(order_type),
            self._check_daily_order_count_by_code(code),
            self._check_daily_buy_amount(order_type, estimated_amount),
            self._check_market_time_buffer(),
            self._check_live_server(
                server_gubun=context["server_gubun"],
                live_approval_text=live_approval_text,
            ),
        ]

        failed_reasons = [reason for ok, reason in checks if not ok]

        if failed_reasons:
            reason = " / ".join(failed_reasons)

            return self._block(
                code,
                name,
                order_type,
                quantity,
                price,
                estimated_amount,
                reason,
                context,
            )

        return self._pass(
            code,
            name,
            order_type,
            quantity,
            price,
            estimated_amount,
            "모든 안전장치 통과",
            context,
        )

    def _check_quantity(self, quantity):
        if quantity is None or int(quantity) <= 0:
            return False, f"주문 수량 오류: {quantity}"

        return True, "주문 수량 정상"

    def _check_blacklist(self, code):
        if str(code) in [str(item) for item in SAFETY_BLACKLIST]:
            return False, f"블랙리스트 종목 차단: {code}"

        return True, "블랙리스트 아님"

    def _check_whitelist(self, code):
        whitelist = [str(item) for item in SAFETY_WHITELIST]

        if not whitelist:
            return True, "화이트리스트 미사용"

        if str(code) not in whitelist:
            return False, f"화이트리스트에 없는 종목 차단: {code}"

        return True, "화이트리스트 통과"

    def _check_single_order_amount(self, estimated_amount):
        if estimated_amount > SAFETY_MAX_SINGLE_ORDER_AMOUNT:
            return (
                False,
                (
                    "단일 주문 금액 제한 초과: "
                    f"{estimated_amount} > {SAFETY_MAX_SINGLE_ORDER_AMOUNT}"
                ),
            )

        return True, "단일 주문 금액 통과"

    def _check_daily_order_count(self, order_type):
        total_orders = self.repository.count_today_orders()

        if total_orders >= SAFETY_MAX_DAILY_ORDERS:
            return (
                False,
                f"하루 전체 주문 횟수 제한 초과: {total_orders} >= {SAFETY_MAX_DAILY_ORDERS}",
            )

        if order_type == "BUY":
            buy_orders = self.repository.count_today_orders(order_type="BUY")

            if buy_orders >= SAFETY_MAX_DAILY_BUY_ORDERS:
                return (
                    False,
                    f"하루 매수 주문 횟수 제한 초과: {buy_orders} >= {SAFETY_MAX_DAILY_BUY_ORDERS}",
                )

        if order_type == "SELL":
            sell_orders = self.repository.count_today_orders(order_type="SELL")

            if sell_orders >= SAFETY_MAX_DAILY_SELL_ORDERS:
                return (
                    False,
                    f"하루 매도 주문 횟수 제한 초과: {sell_orders} >= {SAFETY_MAX_DAILY_SELL_ORDERS}",
                )

        return True, "하루 주문 횟수 통과"

    def _check_daily_order_count_by_code(self, code):
        count = self.repository.count_today_orders(code=code)

        if count >= SAFETY_MAX_DAILY_ORDERS_PER_CODE:
            return (
                False,
                (
                    "종목별 하루 주문 횟수 제한 초과: "
                    f"{code}, {count} >= {SAFETY_MAX_DAILY_ORDERS_PER_CODE}"
                ),
            )

        return True, "종목별 주문 횟수 통과"

    def _check_daily_buy_amount(self, order_type, estimated_amount):
        if order_type != "BUY":
            return True, "매도 주문은 일일 매수 금액 검사 제외"

        today_buy_amount = self.repository.sum_today_buy_order_amount()
        next_amount = today_buy_amount + estimated_amount

        if next_amount > SAFETY_MAX_DAILY_BUY_AMOUNT:
            return (
                False,
                (
                    "하루 매수 금액 제한 초과: "
                    f"{next_amount} > {SAFETY_MAX_DAILY_BUY_AMOUNT}"
                ),
            )

        return True, "하루 매수 금액 통과"

    def _check_market_time_buffer(self):
        now = datetime.now()

        open_dt = self._today_time(MARKET_OPEN_TIME)
        close_dt = self._today_time(MARKET_CLOSE_TIME)

        if SAFETY_BLOCK_NEAR_MARKET_OPEN:
            open_limit = open_dt + timedelta(minutes=SAFETY_MARKET_OPEN_BUFFER_MINUTES)

            if open_dt <= now <= open_limit:
                return (
                    False,
                    (
                        "장 시작 직후 주문 차단: "
                        f"{SAFETY_MARKET_OPEN_BUFFER_MINUTES}분 buffer"
                    ),
                )

        if SAFETY_BLOCK_NEAR_MARKET_CLOSE:
            close_limit = close_dt - timedelta(minutes=SAFETY_MARKET_CLOSE_BUFFER_MINUTES)

            if close_limit <= now <= close_dt:
                return (
                    False,
                    (
                        "장 종료 직전 주문 차단: "
                        f"{SAFETY_MARKET_CLOSE_BUFFER_MINUTES}분 buffer"
                    ),
                )

        return True, "장 시작/종료 buffer 통과"

    def _check_live_server(self, server_gubun, live_approval_text):
        """
        일반적으로 server_gubun == '1'이면 모의투자로 사용.
        실전 서버는 빈 문자열 또는 다른 값일 수 있으므로 보수적으로 차단.
        """
        is_paper_server = str(server_gubun) == "1"

        if is_paper_server:
            return True, "모의투자 서버"

        if SAFETY_BLOCK_LIVE_SERVER_ORDER:
            return False, f"실전 서버 주문 차단: server_gubun={server_gubun!r}"

        if SAFETY_REQUIRE_LIVE_ORDER_APPROVAL:
            if live_approval_text != SAFETY_LIVE_ORDER_APPROVAL_TEXT:
                return False, "실전 주문 승인 문구 불일치"

        return True, "실전 주문 승인 통과"

    def _today_time(self, text):
        hour, minute = text.split(":")
        now = datetime.now()

        return now.replace(
            hour=int(hour),
            minute=int(minute),
            second=0,
            microsecond=0,
        )

    def _pass(
        self,
        code,
        name,
        order_type,
        quantity,
        price,
        estimated_amount,
        reason,
        context,
    ):
        check_id = self.repository.save_safety_check(
            code=code,
            name=name,
            order_type=order_type,
            quantity=quantity,
            price=price,
            estimated_amount=estimated_amount,
            passed=True,
            reason=reason,
            raw_data=json.dumps(context, ensure_ascii=False),
        )

        self.notifier.send(
            title="안전장치 통과",
            message=(
                f"check_id: {check_id}\n"
                f"code: {code}\n"
                f"name: {name}\n"
                f"order_type: {order_type}\n"
                f"estimated_amount: {estimated_amount}\n"
                f"reason: {reason}"
            ),
        )

        return True, reason

    def _block(
        self,
        code,
        name,
        order_type,
        quantity,
        price,
        estimated_amount,
        reason,
        context,
    ):
        check_id = self.repository.save_safety_check(
            code=code,
            name=name,
            order_type=order_type,
            quantity=quantity,
            price=price,
            estimated_amount=estimated_amount,
            passed=False,
            reason=reason,
            raw_data=json.dumps(context, ensure_ascii=False),
        )

        self.notifier.send(
            title="안전장치 차단",
            message=(
                f"check_id: {check_id}\n"
                f"code: {code}\n"
                f"name: {name}\n"
                f"order_type: {order_type}\n"
                f"estimated_amount: {estimated_amount}\n"
                f"reason: {reason}"
            ),
        )

        return False, reason