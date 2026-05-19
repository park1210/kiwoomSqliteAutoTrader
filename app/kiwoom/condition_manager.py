import json

from config import (
    CONDITION_INDEX,
    CONDITION_MAX_INITIAL_CODES,
    CONDITION_NAME,
    CONDITION_SCREEN_NO,
    CONDITION_SEARCH_TYPE,
    CONDITION_WATCH_SECONDS,
)


class ConditionManager:
    def __init__(self, repository, notifier):
        self.repository = repository
        self.notifier = notifier

    def load_and_select_condition(self, kiwoom_api):
        """
        조건식 목록을 불러오고 사용할 조건식을 선택한다.
        CONDITION_INDEX / CONDITION_NAME이 None이면 첫 번째 조건식을 사용한다.
        """
        kiwoom_api.load_conditions()
        conditions = kiwoom_api.get_condition_list()

        if not conditions:
            raise RuntimeError(
                "조건검색식이 없습니다. 키움 HTS에서 조건식을 먼저 저장하세요."
            )

        condition_list_text = "\n".join(
            [
                f"{c['index']} | {c['name']}"
                for c in conditions
            ]
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
        """
        조건검색 실행 후 일정 시간 실시간 이벤트를 감시한다.
        """
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