import json

from config import (
    ENABLE_SELL_ORDER,
    SELL_MAX_CANDIDATES,
    STOP_LOSS_RATE,
    TAKE_PROFIT_RATE,
)


class SellManager:
    def __init__(self, repository, notifier):
        self.repository = repository
        self.notifier = notifier

    def evaluate_positions(self, positions):
        """
        보유 종목을 평가해서 SELL_TAKE_PROFIT / SELL_STOP_LOSS / HOLD로 분류한다.
        """
        results = []

        for position in positions[:SELL_MAX_CANDIDATES]:
            code = position.get("code")
            name = position.get("name")
            quantity = position.get("quantity") or 0
            profit_rate = position.get("profit_rate")

            if quantity <= 0:
                decision = "SKIP"
                reason = "보유 수량이 0 이하입니다."

            elif profit_rate is None:
                decision = "HOLD"
                reason = "수익률 정보가 없어 보유합니다."

            elif profit_rate >= TAKE_PROFIT_RATE:
                decision = "SELL_TAKE_PROFIT"
                reason = f"익절 기준 도달: {profit_rate}% >= {TAKE_PROFIT_RATE}%"

            elif profit_rate <= STOP_LOSS_RATE:
                decision = "SELL_STOP_LOSS"
                reason = f"손절 기준 도달: {profit_rate}% <= {STOP_LOSS_RATE}%"

            else:
                decision = "HOLD"
                reason = (
                    f"매도 조건 미충족: "
                    f"{STOP_LOSS_RATE}% < {profit_rate}% < {TAKE_PROFIT_RATE}%"
                )

            result = {
                "code": code,
                "name": name,
                "quantity": quantity,
                "avg_price": position.get("avg_price"),
                "current_price": position.get("current_price"),
                "eval_amount": position.get("eval_amount"),
                "profit_loss": position.get("profit_loss"),
                "profit_rate": profit_rate,
                "decision": decision,
                "reason": reason,
                "position": position,
            }

            results.append(result)

        self.notifier.send(
            title="보유 종목 매도 판단 완료",
            message=json.dumps(results, ensure_ascii=False, indent=2),
        )

        return results

    def execute_sell_decisions(
        self,
        kiwoom_api,
        account_no,
        sell_decisions,
        order_manager,
        position_manager,
    ):
        """
        매도 판단 결과를 DB에 저장하고,
        ENABLE_SELL_ORDER=True인 경우에만 실제 모의투자 매도 주문을 실행한다.
        """
        results = []

        for item in sell_decisions:
            decision = item["decision"]
            should_sell = decision in ["SELL_TAKE_PROFIT", "SELL_STOP_LOSS"]

            ordered = False
            order_id = None

            if not should_sell:
                reason = item["reason"]

            elif not ENABLE_SELL_ORDER:
                reason = (
                    f"{item['reason']} "
                    "하지만 ENABLE_SELL_ORDER=False이므로 매도 주문은 실행하지 않습니다."
                )

            else:
                order_result = order_manager.paper_market_sell(
                    kiwoom_api=kiwoom_api,
                    account_no=account_no,
                    code=item["code"],
                    name=item["name"],
                    quantity=item["quantity"],
                    reason=item["reason"],
                )

                ordered = bool(order_result.get("ordered"))
                order_id = order_result.get("order_id")
                reason = order_result.get("reason")

                position_manager.sync_account_state(
                    kiwoom_api=kiwoom_api,
                    account_no=account_no,
                )

                position_manager.sync_unfilled_orders(
                    kiwoom_api=kiwoom_api,
                    account_no=account_no,
                )

            decision_id = self.repository.save_sell_decision(
                code=item["code"],
                name=item["name"],
                quantity=item["quantity"],
                avg_price=item["avg_price"],
                current_price=item["current_price"],
                eval_amount=item["eval_amount"],
                profit_loss=item["profit_loss"],
                profit_rate=item["profit_rate"],
                decision=decision,
                reason=reason,
                ordered=ordered,
                order_id=order_id,
                raw_data=json.dumps(item, ensure_ascii=False),
            )

            result = {
                "decision_id": decision_id,
                "code": item["code"],
                "name": item["name"],
                "decision": decision,
                "reason": reason,
                "ordered": ordered,
                "order_id": order_id,
            }

            results.append(result)

            self.notifier.send(
                title="매도 판단 저장 완료",
                message=json.dumps(result, ensure_ascii=False, indent=2),
            )

        return results