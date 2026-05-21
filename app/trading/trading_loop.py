import json
import time
import traceback

from app.kiwoom.condition_manager import ConditionManager
from app.trading.market_time import MarketTimeChecker
from app.trading.order_manager import OrderManager
from app.trading.position_manager import PositionManager
from app.trading.sell_manager import SellManager
from config import (
    ENABLE_LOOP_ACCOUNT_SYNC,
    ENABLE_LOOP_CONDITION_BUY,
    ENABLE_LOOP_SELL_CHECK,
    LOOP_INTERVAL_SECONDS,
    MAX_LOOP_COUNT,
    RUN_CONDITION_EACH_LOOP,
    SKIP_ALREADY_EVALUATED_CONDITION_CODES,
)


class TradingLoop:
    def __init__(self, repository, notifier, kiwoom_api, account_no):
        self.repository = repository
        self.notifier = notifier
        self.kiwoom_api = kiwoom_api
        self.account_no = account_no

        self.market_time_checker = MarketTimeChecker()

        self.position_manager = PositionManager(
            repository=self.repository,
            notifier=self.notifier,
        )

        self.order_manager = OrderManager(
            repository=self.repository,
            notifier=self.notifier,
            position_manager=self.position_manager,
        )

        self.sell_manager = SellManager(
            repository=self.repository,
            notifier=self.notifier,
        )

        self.condition_manager = ConditionManager(
            repository=self.repository,
            notifier=self.notifier,
        )

        # v8.1: 조건식 목록은 최초 1회만 로딩해서 재사용
        self.selected_condition = None

        # v8.1: 같은 실행 세션에서 이미 평가한 조건검색 후보는 재평가하지 않음
        self.evaluated_condition_codes = set()

    def run(self):
        self.notifier.send(
            title="v8.1 자동 운영 루프 시작",
            message=(
                f"MAX_LOOP_COUNT={MAX_LOOP_COUNT}\n"
                f"LOOP_INTERVAL_SECONDS={LOOP_INTERVAL_SECONDS}\n"
                f"ENABLE_LOOP_ACCOUNT_SYNC={ENABLE_LOOP_ACCOUNT_SYNC}\n"
                f"ENABLE_LOOP_SELL_CHECK={ENABLE_LOOP_SELL_CHECK}\n"
                f"ENABLE_LOOP_CONDITION_BUY={ENABLE_LOOP_CONDITION_BUY}\n"
                f"RUN_CONDITION_EACH_LOOP={RUN_CONDITION_EACH_LOOP}\n"
                f"SKIP_ALREADY_EVALUATED_CONDITION_CODES="
                f"{SKIP_ALREADY_EVALUATED_CONDITION_CODES}"
            ),
        )

        # v8.1: 조건식 목록 로딩은 루프 시작 전에 1회만 수행
        if ENABLE_LOOP_CONDITION_BUY and not RUN_CONDITION_EACH_LOOP:
            self.selected_condition = self.condition_manager.load_and_select_condition(
                self.kiwoom_api
            )

        loop_no = 0

        while True:
            loop_no += 1

            if MAX_LOOP_COUNT is not None and loop_no > MAX_LOOP_COUNT:
                self.notifier.send(
                    title="v8.1 자동 운영 루프 종료",
                    message=f"MAX_LOOP_COUNT={MAX_LOOP_COUNT}에 도달하여 종료합니다.",
                )
                break

            market_message = self.market_time_checker.get_status_message()

            if not self.market_time_checker.is_market_time():
                self.notifier.send(
                    title="루프 스킵",
                    message=market_message,
                )
                break

            loop_run_id = self.repository.save_loop_run_start(
                loop_no=loop_no,
                status="STARTED",
                message=market_message,
            )

            try:
                result = self._run_once(loop_no)

                self.repository.update_loop_run_finish(
                    loop_run_id=loop_run_id,
                    status="FINISHED",
                    message="loop finished",
                    raw_data=json.dumps(result, ensure_ascii=False),
                )

            except Exception as e:
                error_detail = traceback.format_exc()

                self.repository.update_loop_run_finish(
                    loop_run_id=loop_run_id,
                    status="ERROR",
                    message=str(e),
                    raw_data=error_detail,
                )

                self.repository.save_system_log(
                    level="ERROR",
                    message=f"v8.1 loop error: {e}",
                    detail=error_detail,
                )

                self.notifier.send(
                    title="v8.1 루프 오류 발생",
                    message=(
                        f"loop_no={loop_no}\n"
                        f"error={e}\n"
                        "오류는 저장했고 다음 루프로 진행합니다."
                    ),
                )

            if MAX_LOOP_COUNT is not None and loop_no >= MAX_LOOP_COUNT:
                self.notifier.send(
                    title="v8.1 자동 운영 루프 종료",
                    message=f"loop_no={loop_no}, MAX_LOOP_COUNT={MAX_LOOP_COUNT}",
                )
                break

            time.sleep(LOOP_INTERVAL_SECONDS)

    def _run_once(self, loop_no):
        self.notifier.send(
            title="v8.1 루프 실행",
            message=f"loop_no={loop_no}",
        )

        result = {
            "loop_no": loop_no,
            "account_sync": None,
            "sell_results": None,
            "condition_result": None,
            "condition_candidates": None,
            "condition_decisions": None,
            "skipped_condition_codes": [],
        }

        account_state = None
        unfilled_orders = None

        # v8.1: 루프 초반에 계좌/미체결을 한 번만 동기화
        if ENABLE_LOOP_ACCOUNT_SYNC:
            account_state = self.position_manager.sync_account_state(
                kiwoom_api=self.kiwoom_api,
                account_no=self.account_no,
            )

            unfilled_orders = self.position_manager.sync_unfilled_orders(
                kiwoom_api=self.kiwoom_api,
                account_no=self.account_no,
            )

            result["account_sync"] = {
                "positions_count": len(account_state.get("positions", [])),
                "unfilled_count": len(unfilled_orders),
            }

        # v8.1: 매도 판단은 이미 조회한 account_state를 재사용
        if ENABLE_LOOP_SELL_CHECK:
            sell_results = self._run_sell_check(account_state)
            result["sell_results"] = sell_results

        if ENABLE_LOOP_CONDITION_BUY:
            condition_result, candidates, decisions, skipped_codes = (
                self._run_condition_buy_check()
            )

            result["condition_result"] = {
                "condition": condition_result.get("condition"),
                "initial_count": len(condition_result.get("initial_codes", [])),
                "realtime_count": len(condition_result.get("realtime_events", [])),
            }
            result["condition_candidates"] = candidates
            result["condition_decisions"] = decisions
            result["skipped_condition_codes"] = skipped_codes

        self.notifier.send(
            title="v8.1 루프 완료",
            message=json.dumps(result, ensure_ascii=False, indent=2),
        )

        return result

    def _run_sell_check(self, account_state=None):
        """
        v8.1 변경:
        기존에는 매도 판단 전에 계좌 동기화를 다시 했지만,
        이제는 _run_once()에서 이미 조회한 account_state를 재사용한다.
        """
        if account_state is None:
            account_state = self.position_manager.sync_account_state(
                kiwoom_api=self.kiwoom_api,
                account_no=self.account_no,
            )

        positions = account_state.get("positions", [])

        if not positions:
            self.notifier.send(
                title="매도 판단 대상 없음",
                message="현재 보유 종목이 없습니다.",
            )
            return []

        sell_decisions = self.sell_manager.evaluate_positions(positions)

        sell_results = self.sell_manager.execute_sell_decisions(
            kiwoom_api=self.kiwoom_api,
            account_no=self.account_no,
            sell_decisions=sell_decisions,
            order_manager=self.order_manager,
            position_manager=self.position_manager,
        )

        return sell_results

    def _run_condition_buy_check(self):
        """
        v8.1 변경:
        1. 조건식 목록은 기본적으로 최초 1회만 로딩한다.
        2. 이미 평가한 후보 종목은 같은 실행 세션에서 다시 평가하지 않는다.
        """
        if self.selected_condition is None or RUN_CONDITION_EACH_LOOP:
            self.selected_condition = self.condition_manager.load_and_select_condition(
                self.kiwoom_api
            )

        condition_result = self.condition_manager.run_condition_watch(
            kiwoom_api=self.kiwoom_api,
            condition=self.selected_condition,
        )

        candidates = self.condition_manager.build_order_candidates(condition_result)

        filtered_candidates = []
        skipped_codes = []

        if SKIP_ALREADY_EVALUATED_CONDITION_CODES:
            for candidate in candidates:
                code = candidate["code"]

                if code in self.evaluated_condition_codes:
                    skipped_codes.append(code)
                    continue

                filtered_candidates.append(candidate)
        else:
            filtered_candidates = candidates

        if skipped_codes:
            self.notifier.send(
                title="조건검색 후보 중복 평가 스킵",
                message=(
                    f"이미 평가한 종목 수: {len(skipped_codes)}\n"
                    f"스킵 종목: {skipped_codes}"
                ),
            )

        if not filtered_candidates:
            self.notifier.send(
                title="조건검색 주문 후보 없음",
                message="새로 평가할 조건검색 후보가 없습니다.",
            )

            return condition_result, candidates, [], skipped_codes

        decisions = self.condition_manager.evaluate_and_order_candidates(
            kiwoom_api=self.kiwoom_api,
            account_no=self.account_no,
            candidates=filtered_candidates,
            order_manager=self.order_manager,
            position_manager=self.position_manager,
        )

        for candidate in filtered_candidates:
            self.evaluated_condition_codes.add(candidate["code"])

        return condition_result, filtered_candidates, decisions, skipped_codes