import json

from config import (
    CONDITION_INDEX,
    CONDITION_MAX_INITIAL_CODES,
    CONDITION_NAME,
    CONDITION_ORDER_MAX_CANDIDATES,
    CONDITION_ORDER_QTY,
    CONDITION_SCREEN_NO,
    CONDITION_SEARCH_TYPE,
    CONDITION_WATCH_SECONDS,
    ENABLE_CONDITION_ORDER,
    USE_INITIAL_CONDITION_CODES_FOR_ORDER,
    USE_REALTIME_CONDITION_IN_FOR_ORDER,
)


class ConditionManager:
    def __init__(self, repository, notifier):
        self.repository = repository
        self.notifier = notifier

    def load_and_select_condition(self, kiwoom_api):
        kiwoom_api.load_conditions()
        conditions = kiwoom_api.get_condition_list()

        if not conditions:
            raise RuntimeError(
                "조건검색식이 없습니다. 키움 HTS에서 조건식을 먼저 저장하세요."
            )

        condition_list_text = "\n".join(
            [f"{c['index']} | {c['name']}" for c in conditions]
        )

        self.notifier.send(
            title="조건검색식 목록 로딩 완료",
            message=condition_list_text,
        )

        selected = None

        if CONDITION_INDEX is not None:
            for condition in conditions:
                if condition["index"] == CONDITION_INDEX:
                    selected = condition
                    break

        if selected is None and CONDITION_NAME is not None:
            for condition in conditions:
                if condition["name"] == CONDITION_NAME:
                    selected = condition
                    break

        if selected is None:
            selected = conditions[0]

        self.notifier.send(
            title="조건검색식 선택 완료",
            message=(
                f"condition_index: {selected['index']}\n"
                f"condition_name: {selected['name']}"
            ),
        )

        return selected

    def run_condition_watch(self, kiwoom_api, condition):
        condition_index = condition["index"]
        condition_name = condition["name"]

        initial_codes = kiwoom_api.send_condition(
            screen_no=CONDITION_SCREEN_NO,
            condition_name=condition_name,
            condition_index=condition_index,
            search_type=CONDITION_SEARCH_TYPE,
        )

        initial_sample = initial_codes[:CONDITION_MAX_INITIAL_CODES]

        self.notifier.send(
            title="조건검색 초기 결과",
            message=(
                f"조건식: {condition_index}^{condition_name}\n"
                f"초기 편입 종목 수: {len(initial_codes)}\n"
                f"저장 대상 종목 일부: {initial_sample}"
            ),
        )

        for code in initial_sample:
            name = kiwoom_api.get_stock_name(code)

            raw = {
                "code": code,
                "name": name,
                "condition_index": condition_index,
                "condition_name": condition_name,
                "source": "INITIAL",
            }

            self.repository.save_condition_event(
                condition_index=condition_index,
                condition_name=condition_name,
                code=code,
                name=name,
                event_type="I",
                event_type_name="CONDITION_INITIAL",
                source="INITIAL",
                raw_data=json.dumps(raw, ensure_ascii=False),
            )

            self.repository.save_signal(
                code=code,
                signal_type="CONDITION_INITIAL",
                strategy_name="KiwoomConditionSearch",
                price=None,
                reason=f"조건검색 초기 편입: {condition_index}^{condition_name}",
            )

        self.notifier.send(
            title="실시간 조건검색 감시 시작",
            message=f"{CONDITION_WATCH_SECONDS}초 동안 편입/이탈 이벤트를 감시합니다.",
        )

        kiwoom_api.wait_seconds(CONDITION_WATCH_SECONDS)

        realtime_events = kiwoom_api.condition_events

        for event in realtime_events:
            self.repository.save_condition_event(
                condition_index=event["condition_index"],
                condition_name=event["condition_name"],
                code=event["code"],
                name=event["name"],
                event_type=event["event_type"],
                event_type_name=event["event_type_name"],
                source=event["source"],
                raw_data=json.dumps(event, ensure_ascii=False),
            )

            self.repository.save_signal(
                code=event["code"],
                signal_type=event["event_type_name"],
                strategy_name="KiwoomConditionSearch",
                price=None,
                reason=(
                    f"실시간 조건검색 이벤트: "
                    f"{event['condition_index']}^{event['condition_name']} "
                    f"{event['event_type_name']}"
                ),
            )

        self.notifier.send(
            title="실시간 조건검색 감시 종료",
            message=(
                f"수신 이벤트 수: {len(realtime_events)}\n"
                f"events: {json.dumps(realtime_events, ensure_ascii=False)}"
            ),
        )

        if CONDITION_SEARCH_TYPE == 1:
            kiwoom_api.stop_condition(
                screen_no=CONDITION_SCREEN_NO,
                condition_name=condition_name,
                condition_index=condition_index,
            )

        return {
            "condition": condition,
            "initial_codes": initial_codes,
            "realtime_events": realtime_events,
        }

    def build_order_candidates(self, condition_result):
        """
        v6 주문 후보 생성.
        기본적으로 너무 많은 종목을 주문하지 않도록 개수를 제한한다.
        """
        condition = condition_result["condition"]
        initial_codes = condition_result.get("initial_codes", [])
        realtime_events = condition_result.get("realtime_events", [])

        candidates = []
        seen = set()

        if USE_INITIAL_CONDITION_CODES_FOR_ORDER:
            for code in initial_codes:
                if code not in seen:
                    candidates.append(
                        {
                            "code": code,
                            "source": "INITIAL",
                            "event_type_name": "CONDITION_INITIAL",
                            "condition_index": condition["index"],
                            "condition_name": condition["name"],
                        }
                    )
                    seen.add(code)

                if len(candidates) >= CONDITION_ORDER_MAX_CANDIDATES:
                    break

        if USE_REALTIME_CONDITION_IN_FOR_ORDER:
            for event in realtime_events:
                if event.get("event_type_name") != "CONDITION_IN":
                    continue

                code = event["code"]

                if code in seen:
                    continue

                candidates.append(
                    {
                        "code": code,
                        "source": "REALTIME",
                        "event_type_name": "CONDITION_IN",
                        "condition_index": event["condition_index"],
                        "condition_name": event["condition_name"],
                    }
                )
                seen.add(code)

                if len(candidates) >= CONDITION_ORDER_MAX_CANDIDATES:
                    break

        self.notifier.send(
            title="조건검색 주문 후보 생성 완료",
            message=(
                f"후보 수: {len(candidates)}\n"
                f"후보: {json.dumps(candidates, ensure_ascii=False)}\n"
                f"ENABLE_CONDITION_ORDER={ENABLE_CONDITION_ORDER}"
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
        조건검색 후보를 평가하고, 설정이 켜져 있을 때만 주문한다.
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

            is_holding, position = position_manager.is_holding(code)
            has_unfilled, unfilled = position_manager.has_unfilled_order(
                account_no=account_no,
                code=code,
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

            elif not ENABLE_CONDITION_ORDER:
                decision = "DRY_RUN"
                reason = "ENABLE_CONDITION_ORDER=False이므로 주문하지 않고 평가만 수행"
                ordered = False
                order_id = None

            else:
                order_result = order_manager.paper_market_buy(
                    kiwoom_api=kiwoom_api,
                    account_no=account_no,
                    code=snapshot["code"],
                    name=snapshot["name"],
                    quantity=CONDITION_ORDER_QTY,
                    current_price=snapshot["current_price"],
                )

                ordered = bool(order_result.get("ordered"))
                order_id = order_result.get("order_id")
                decision = "ORDER_SENT" if ordered else "ORDER_BLOCKED_OR_FAILED"
                reason = order_result.get("reason")

                # 주문 후 상태 재동기화
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
                quantity=CONDITION_ORDER_QTY,
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

            results.append(
                {
                    "decision_id": decision_id,
                    "code": snapshot["code"],
                    "name": snapshot["name"],
                    "current_price": snapshot["current_price"],
                    "decision": decision,
                    "reason": reason,
                    "ordered": ordered,
                    "order_id": order_id,
                }
            )

            self.notifier.send(
                title="조건검색 주문 후보 평가 완료",
                message=json.dumps(results[-1], ensure_ascii=False, indent=2),
            )

        return results