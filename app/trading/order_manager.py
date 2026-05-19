import json

from app.trading.risk_manager import RiskManager
from config import (
    BLOCK_IF_ALREADY_HOLDING,
    BLOCK_IF_UNFILLED_ORDER_EXISTS,
    MODE,
)


class OrderManager:
    def __init__(self, repository, notifier, position_manager=None):
        self.repository = repository
        self.notifier = notifier
        self.position_manager = position_manager
        self.risk_manager = RiskManager()

    def paper_market_buy(
        self,
        kiwoom_api,
        account_no,
        code,
        name,
        quantity,
        current_price,
    ):
        server_gubun = kiwoom_api.get_server_gubun()

        ok, reason = self.risk_manager.validate_order_environment(
            mode=MODE,
            server_gubun=server_gubun,
        )

        if not ok:
            return self._blocked(code, name, reason)

        ok, reason = self.risk_manager.validate_buy_amount(
            quantity=quantity,
            current_price=current_price,
        )

        if not ok:
            return self._blocked(code, name, reason)

        if self.position_manager is not None and BLOCK_IF_ALREADY_HOLDING:
            is_holding, position = self.position_manager.is_holding(code)

            if is_holding:
                return self._blocked(
                    code,
                    name,
                    f"이미 보유 중인 종목이므로 중복 매수 차단: {position}",
                )

        if self.position_manager is not None and BLOCK_IF_UNFILLED_ORDER_EXISTS:
            has_unfilled, unfilled = self.position_manager.has_unfilled_order(
                account_no=account_no,
                code=code,
            )

            if has_unfilled:
                return self._blocked(
                    code,
                    name,
                    f"미체결 주문이 존재하여 추가 주문 차단: {unfilled}",
                )

        order_id = self.repository.save_order(
            code=code,
            name=name,
            account_no=account_no,
            order_type="BUY",
            quantity=quantity,
            price=0,
            hoga_gb="03",
            reason="v4 모의투자 시장가 매수 테스트",
            status="REQUESTED",
        )

        send_result = kiwoom_api.send_market_buy_order(
            account_no=account_no,
            code=code,
            quantity=quantity,
        )

        if not send_result["success"]:
            self.repository.update_order_status(
                order_id=order_id,
                status="FAILED",
            )

            self.notifier.send(
                title="주문 실패",
                message=(
                    f"종목코드: {code}\n"
                    f"종목명: {name}\n"
                    f"사유: {send_result['message']}"
                ),
            )

            return {
                "ordered": False,
                "reason": send_result["message"],
                "order_id": order_id,
                "send_result": send_result,
            }

        chejan = send_result.get("chejan", {})
        kiwoom_order_no = chejan.get("주문번호")

        self.repository.update_order_status(
            order_id=order_id,
            status="SUBMITTED",
            kiwoom_order_no=kiwoom_order_no,
        )

        if chejan:
            execution_id = self.repository.save_execution(
                order_id=order_id,
                code=chejan.get("종목코드") or code,
                name=chejan.get("종목명") or name,
                kiwoom_order_no=chejan.get("주문번호"),
                order_status="CHEJAN_RECEIVED",
                order_type_raw=chejan.get("주문구분"),
                quantity=chejan.get("주문수량"),
                price=chejan.get("주문가격"),
                unfilled_quantity=chejan.get("미체결수량"),
                execution_price=chejan.get("체결가"),
                execution_quantity=chejan.get("체결량"),
                execution_time=chejan.get("주문체결시간"),
                raw_data=json.dumps(chejan, ensure_ascii=False),
            )
        else:
            execution_id = None

        self.notifier.send(
            title="모의투자 매수 주문 요청 완료",
            message=(
                f"종목코드: {code}\n"
                f"종목명: {name}\n"
                f"수량: {quantity}\n"
                f"주문방식: 시장가\n"
                f"주문ID: {order_id}\n"
                f"키움주문번호: {kiwoom_order_no}\n"
                f"체결이벤트ID: {execution_id}\n"
                f"SendOrder 결과: {send_result['message']}"
            ),
        )

        return {
            "ordered": True,
            "reason": "주문 요청 완료",
            "order_id": order_id,
            "send_result": send_result,
        }
    
    def paper_market_sell(
        self,
        kiwoom_api,
        account_no,
        code,
        name,
        quantity,
        reason,
    ):
        server_gubun = kiwoom_api.get_server_gubun()

        ok, env_reason = self.risk_manager.validate_order_environment(
            mode=MODE,
            server_gubun=server_gubun,
        )

        if not ok:
            return self._blocked(code, name, env_reason)

        if quantity <= 0:
            return self._blocked(code, name, f"매도 수량이 올바르지 않습니다: {quantity}")

        order_id = self.repository.save_order(
            code=code,
            name=name,
            account_no=account_no,
            order_type="SELL",
            quantity=quantity,
            price=0,
            hoga_gb="03",
            reason=reason,
            status="REQUESTED",
        )

        send_result = kiwoom_api.send_market_sell_order(
            account_no=account_no,
            code=code,
            quantity=quantity,
        )

        if not send_result["success"]:
            self.repository.update_order_status(
                order_id=order_id,
                status="FAILED",
            )

            self.notifier.send(
                title="매도 주문 실패",
                message=(
                    f"종목코드: {code}\n"
                    f"종목명: {name}\n"
                    f"수량: {quantity}\n"
                    f"사유: {send_result['message']}"
                ),
            )

            return {
                "ordered": False,
                "reason": send_result["message"],
                "order_id": order_id,
                "send_result": send_result,
            }

        chejan = send_result.get("chejan", {})
        kiwoom_order_no = chejan.get("주문번호")

        self.repository.update_order_status(
            order_id=order_id,
            status="SUBMITTED",
            kiwoom_order_no=kiwoom_order_no,
        )

        if chejan:
            execution_id = self.repository.save_execution(
                order_id=order_id,
                code=chejan.get("종목코드") or code,
                name=chejan.get("종목명") or name,
                kiwoom_order_no=chejan.get("주문번호"),
                order_status="CHEJAN_RECEIVED",
                order_type_raw=chejan.get("주문구분"),
                quantity=chejan.get("주문수량"),
                price=chejan.get("주문가격"),
                unfilled_quantity=chejan.get("미체결수량"),
                execution_price=chejan.get("체결가"),
                execution_quantity=chejan.get("체결량"),
                execution_time=chejan.get("주문체결시간"),
                raw_data=json.dumps(chejan, ensure_ascii=False),
            )
        else:
            execution_id = None

        self.notifier.send(
            title="모의투자 매도 주문 요청 완료",
            message=(
                f"종목코드: {code}\n"
                f"종목명: {name}\n"
                f"수량: {quantity}\n"
                f"주문방식: 시장가\n"
                f"주문ID: {order_id}\n"
                f"키움주문번호: {kiwoom_order_no}\n"
                f"체결이벤트ID: {execution_id}\n"
                f"SendOrder 결과: {send_result['message']}"
            ),
        )

        return {
            "ordered": True,
            "reason": "매도 주문 요청 완료",
            "order_id": order_id,
            "send_result": send_result,
        }

    def _blocked(self, code, name, reason):
        self.notifier.send(
            title="주문 차단",
            message=(
                f"종목코드: {code}\n"
                f"종목명: {name}\n"
                f"차단 사유: {reason}"
            ),
        )

        return {
            "ordered": False,
            "reason": reason,
            "order_id": None,
            "send_result": None,
        }