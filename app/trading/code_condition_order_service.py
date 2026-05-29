import json

from config import (
    CODE_CONDITION_ENABLE_ORDER,
    CODE_CONDITION_ORDER_MAX_CANDIDATES,
    CODE_CONDITION_ORDER_QTY,
)


class CodeConditionOrderService:
    def __init__(self, repository, notifier):
        self.repository = repository
        self.notifier = notifier

    def build_order_candidates(self, code_condition_result):
        """
        v5.1 코드 조건검색 결과 중 passed=True인 종목을
        v6.1 주문 후보로 변환한다.
        """
        passed_candidates = code_condition_result.get("passed_candidates", [])

        candidates = []

        for item in passed_candidates:
            candidates.append(
                {
                    "code": item["code"],
                    "name": item.get("name"),
                    "source": "CODE_CONDITION",
                    "event_type_name": "CODE_CONDITION_PASS",
                    "condition_index": -1,
                    "condition_name": code_condition_result.get(
                        "condition_name",
                        "CodeBasedPriceVolumeCondition",
                    ),
                    "current_price": item.get("current_price"),
                    "volume": item.get("volume"),
                    "reason": item.get("reason"),
                }
            )

            if len(candidates) >= CODE_CONDITION_ORDER_MAX_CANDIDATES:
                break

        self.notifier.send(
            title="v6.1 코드 조건검색 주문 후보 생성 완료",
            message=json.dumps(
                {
                    "candidate_count": len(candidates),
                    "candidates": candidates,
                    "CODE_CONDITION_ENABLE_ORDER": CODE_CONDITION_ENABLE_ORDER,
                },
                ensure_ascii=False,
                indent=2,
            ),
        )

        return candidates

    def evaluate_and_order_candidates(
        self,
        kiwoom_api,
        account_no,
        candidates,
        order_manager,
        position_manager,
    ):
        """
        코드 조건검색 후보를 평가하고,
        CODE_CONDITION_ENABLE_ORDER=True일 때만 실제 모의투자 주문을 실행한다.
        """
        results = []

        for candidate in candidates:
            code = candidate["code"]

            snapshot = kiwoom_api.get_current_price(code)

            self.repository.upsert_stock(
                code=snapshot["code"],
                name=snapshot["name"],
                market="KOSPI",
            )

            self.repository.save_price_snapshot(
                code=snapshot["code"],
                name=snapshot["name"],
                current_price=snapshot["current_price"],
                volume=snapshot["volume"],
                raw_current_price=snapshot["raw_current_price"],
                raw_volume=snapshot["raw_volume"],
            )

            is_holding, position = position_manager.is_holding(snapshot["code"])
            has_unfilled, unfilled = position_manager.has_unfilled_order(
                account_no=account_no,
                code=snapshot["code"],
            )

            if is_holding:
                decision = "BLOCKED_ALREADY_HOLDING"
                reason = f"이미 보유 중: {position}"
                ordered = False
                order_id = None

            elif has_unfilled:
                decision = "BLOCKED_UNFILLED_EXISTS"
                reason = f"미체결 주문 존재: {unfilled}"
                ordered = False
                order_id = None

            elif not CODE_CONDITION_ENABLE_ORDER:
                decision = "DRY_RUN"
                reason = "CODE_CONDITION_ENABLE_ORDER=False이므로 주문하지 않고 평가만 수행"
                ordered = False
                order_id = None

            else:
                order_result = order_manager.paper_market_buy(
                    kiwoom_api=kiwoom_api,
                    account_no=account_no,
                    code=snapshot["code"],
                    name=snapshot["name"],
                    quantity=CODE_CONDITION_ORDER_QTY,
                    current_price=snapshot["current_price"],
                )

                ordered = bool(order_result.get("ordered"))
                order_id = order_result.get("order_id")
                decision = "ORDER_SENT" if ordered else "ORDER_BLOCKED_OR_FAILED"
                reason = order_result.get("reason")

                position_manager.sync_account_state(
                    kiwoom_api=kiwoom_api,
                    account_no=account_no,
                )

                position_manager.sync_unfilled_orders(
                    kiwoom_api=kiwoom_api,
                    account_no=account_no,
                )

            decision_id = self.repository.save_condition_trade_decision(
                condition_index=candidate["condition_index"],
                condition_name=candidate["condition_name"],
                code=snapshot["code"],
                name=snapshot["name"],
                current_price=snapshot["current_price"],
                quantity=CODE_CONDITION_ORDER_QTY,
                decision=decision,
                reason=reason,
                ordered=ordered,
                order_id=order_id,
                raw_data=json.dumps(
                    {
                        "candidate": candidate,
                        "snapshot": snapshot,
                        "is_holding": is_holding,
                        "position": position,
                        "has_unfilled": has_unfilled,
                        "unfilled": unfilled,
                    },
                    ensure_ascii=False,
                ),
            )

            result = {
                "decision_id": decision_id,
                "code": snapshot["code"],
                "name": snapshot["name"],
                "current_price": snapshot["current_price"],
                "decision": decision,
                "reason": reason,
                "ordered": ordered,
                "order_id": order_id,
            }

            results.append(result)

            self.notifier.send(
                title="v6.1 코드 조건검색 주문 후보 평가 완료",
                message=json.dumps(result, ensure_ascii=False, indent=2),
            )

        return results