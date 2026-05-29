import json
import time
import traceback

from app.kiwoom.condition_manager import ConditionManager
from app.strategy.code_condition_engine import CodeConditionEngine
from app.trading.code_condition_order_service import CodeConditionOrderService
from app.trading.market_time import MarketTimeChecker
from app.trading.order_manager import OrderManager
from app.trading.position_manager import PositionManager
from app.trading.sell_manager import SellManager
from config import (
    ENABLE_LOOP_ACCOUNT_SYNC,
    ENABLE_LOOP_CONDITION_BUY,
    ENABLE_LOOP_SELL_CHECK,
    LOOP_CONDITION_SOURCE,
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

        # 키움 HTS 조건검색
        self.condition_manager = ConditionManager(
            repository=self.repository,
            notifier=self.notifier,
        )

        # 코드/YAML 기반 조건검색
        self.code_condition_engine = CodeConditionEngine(
            repository=self.repository,
            notifier=self.notifier,
        )

        self.code_condition_order_service = CodeConditionOrderService(
            repository=self.repository,
            notifier=self.notifier,
        )

        self.selected_condition = None
        self.evaluated_condition_codes = set()
        self.evaluated_code_condition_codes = set()

    def run(self):
        self.notifier.send(
            title="v8.2 자동 운영 루프 시작",
            message=(
                f"MAX_LOOP_COUNT={MAX_LOOP_COUNT}\n"
                f"LOOP_INTERVAL_SECONDS={LOOP_INTERVAL_SECONDS}\n"
                f"ENABLE_LOOP_ACCOUNT_SYNC={ENABLE_LOOP_ACCOUNT_SYNC}\n"
                f"ENABLE_LOOP_SELL_CHECK={ENABLE_LOOP_SELL_CHECK}\n"
                f"ENABLE_LOOP_CONDITION_BUY={ENABLE_LOOP_CONDITION_BUY}\n"
                f"RUN_CONDITION_EACH_LOOP={RUN_CONDITION_EACH_LOOP}\n"
                f"SKIP_ALREADY_EVALUATED_CONDITION_CODES="
                f"{SKIP_ALREADY_EVALUATED_CONDITION_CODES}\n"
                f"LOOP_CONDITION_SOURCE={LOOP_CONDITION_SOURCE}"
            ),
        )

        if (
            ENABLE_LOOP_CONDITION_BUY
            and LOOP_CONDITION_SOURCE in ["kiwoom", "both"]
            and not RUN_CONDITION_EACH_LOOP
        ):
            self.selected_condition = self.condition_manager.load_and_select_condition(
                self.kiwoom_api
            )

        loop_no = 0

        while True:
            loop_no += 1

            if MAX_LOOP_COUNT is not None and loop_no > MAX_LOOP_COUNT:
                self.notifier.send(
                    title="v8.2 자동 운영 루프 종료",
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
                    message=f"v8.2 loop error: {e}",
                    detail=error_detail,
                )

                self.notifier.send(
                    title="v8.2 루프 오류 발생",
                    message=(
                        f"loop_no={loop_no}\n"
                        f"error={e}\n"
                        "오류는 저장했고 다음 루프로 진행합니다."
                    ),
                )

            if MAX_LOOP_COUNT is not None and loop_no >= MAX_LOOP_COUNT:
                self.notifier.send(
                    title="v8.2 자동 운영 루프 종료",
                    message=f"loop_no={loop_no}, MAX_LOOP_COUNT={MAX_LOOP_COUNT}",
                )
                break

            time.sleep(LOOP_INTERVAL_SECONDS)

    def _run_once(self, loop_no):
        self.notifier.send(
            title="v8.2 루프 실행",
            message=f"loop_no={loop_no}",
        )

        result = {
            "loop_no": loop_no,
            "account_sync": None,
            "sell_results": None,
            "condition_source": LOOP_CONDITION_SOURCE,
            "kiwoom_condition": None,
            "code_condition": None,
        }

        account_state = None
        unfilled_orders = None

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

        if ENABLE_LOOP_SELL_CHECK:
            result["sell_results"] = self._run_sell_check(account_state)

        if ENABLE_LOOP_CONDITION_BUY:
            if LOOP_CONDITION_SOURCE == "kiwoom":
                result["kiwoom_condition"] = self._run_kiwoom_condition_buy_check()

            elif LOOP_CONDITION_SOURCE == "code":
                result["code_condition"] = self._run_code_condition_buy_check()

            elif LOOP_CONDITION_SOURCE == "both":
                result["kiwoom_condition"] = self._run_kiwoom_condition_buy_check()
                result["code_condition"] = self._run_code_condition_buy_check()

            else:
                raise ValueError(
                    "지원하지 않는 trading_loop.condition_source입니다: "
                    f"{LOOP_CONDITION_SOURCE}. "
                    "사용 가능 값: kiwoom, code, both"
                )

        self.notifier.send(
            title="v8.2 루프 완료",
            message=json.dumps(result, ensure_ascii=False, indent=2),
        )

        return result

    def _run_sell_check(self, account_state=None):
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

    def _run_kiwoom_condition_buy_check(self):
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
                title="키움 조건검색 후보 중복 평가 스킵",
                message=(
                    f"이미 평가한 종목 수: {len(skipped_codes)}\n"
                    f"스킵 종목: {skipped_codes}"
                ),
            )

        if not filtered_candidates:
            self.notifier.send(
                title="키움 조건검색 주문 후보 없음",
                message="새로 평가할 키움 조건검색 후보가 없습니다.",
            )

            return {
                "condition_result": {
                    "condition": condition_result.get("condition"),
                    "initial_count": len(condition_result.get("initial_codes", [])),
                    "realtime_count": len(condition_result.get("realtime_events", [])),
                },
                "candidates": candidates,
                "decisions": [],
                "skipped_codes": skipped_codes,
            }

        decisions = self.condition_manager.evaluate_and_order_candidates(
            kiwoom_api=self.kiwoom_api,
            account_no=self.account_no,
            candidates=filtered_candidates,
            order_manager=self.order_manager,
            position_manager=self.position_manager,
        )

        for candidate in filtered_candidates:
            self.evaluated_condition_codes.add(candidate["code"])

        return {
            "condition_result": {
                "condition": condition_result.get("condition"),
                "initial_count": len(condition_result.get("initial_codes", [])),
                "realtime_count": len(condition_result.get("realtime_events", [])),
            },
            "candidates": filtered_candidates,
            "decisions": decisions,
            "skipped_codes": skipped_codes,
        }

    def _run_code_condition_buy_check(self):
        code_condition_result = self.code_condition_engine.run(
            kiwoom_api=self.kiwoom_api,
            account_no=self.account_no,
            position_manager=self.position_manager,
        )

        candidates = self.code_condition_order_service.build_order_candidates(
            code_condition_result
        )

        filtered_candidates = []
        skipped_codes = []

        if SKIP_ALREADY_EVALUATED_CONDITION_CODES:
            for candidate in candidates:
                code = candidate["code"]

                if code in self.evaluated_code_condition_codes:
                    skipped_codes.append(code)
                    continue

                filtered_candidates.append(candidate)
        else:
            filtered_candidates = candidates

        if skipped_codes:
            self.notifier.send(
                title="코드 조건검색 후보 중복 평가 스킵",
                message=(
                    f"이미 평가한 종목 수: {len(skipped_codes)}\n"
                    f"스킵 종목: {skipped_codes}"
                ),
            )

        if not filtered_candidates:
            self.notifier.send(
                title="코드 조건검색 주문 후보 없음",
                message="새로 평가할 코드 조건검색 후보가 없습니다.",
            )

            return {
                "code_condition_result": {
                    "condition_name": code_condition_result.get("condition_name"),
                    "total_checked": code_condition_result.get("total_checked"),
                    "passed_count": len(
                        code_condition_result.get("passed_candidates", [])
                    ),
                },
                "candidates": candidates,
                "decisions": [],
                "skipped_codes": skipped_codes,
            }

        decisions = self.code_condition_order_service.evaluate_and_order_candidates(
            kiwoom_api=self.kiwoom_api,
            account_no=self.account_no,
            candidates=filtered_candidates,
            order_manager=self.order_manager,
            position_manager=self.position_manager,
        )

        for candidate in filtered_candidates:
            self.evaluated_code_condition_codes.add(candidate["code"])

        return {
            "code_condition_result": {
                "condition_name": code_condition_result.get("condition_name"),
                "total_checked": code_condition_result.get("total_checked"),
                "passed_count": len(code_condition_result.get("passed_candidates", [])),
            },
            "candidates": filtered_candidates,
            "decisions": decisions,
            "skipped_codes": skipped_codes,
        }