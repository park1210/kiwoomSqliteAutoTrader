import json
import time

from app.strategy.filters import BasicPriceVolumeFilter
from app.strategy.universe_provider import UniverseProvider
from config import (
    CODE_CONDITION_EXCLUDE_HOLDING,
    CODE_CONDITION_EXCLUDE_UNFILLED,
    CODE_CONDITION_MAX_CANDIDATES,
    CODE_CONDITION_MAX_RETRY,
    CODE_CONDITION_REQUEST_DELAY_SECONDS,
)


class CodeConditionEngine:
    def __init__(self, repository, notifier):
        self.repository = repository
        self.notifier = notifier
        self.universe_provider = UniverseProvider()
        self.filter = BasicPriceVolumeFilter()
        self.condition_name = "CodeBasedPriceVolumeCondition"

    def run(
        self,
        kiwoom_api,
        account_no=None,
        position_manager=None,
    ):
        codes = self.universe_provider.get_codes()

        self.notifier.send(
            title="v5.1 코드 기반 조건검색 시작",
            message=(
                f"universe size: {len(codes)}\n"
                f"codes: {codes}\n"
                f"max_candidates: {CODE_CONDITION_MAX_CANDIDATES}\n"
                f"request_delay_seconds: {CODE_CONDITION_REQUEST_DELAY_SECONDS}"
            ),
        )

        passed_candidates = []
        all_results = []

        for index, code in enumerate(codes, start=1):
            # 너무 빠른 TR 요청 방지
            if index > 1:
                time.sleep(CODE_CONDITION_REQUEST_DELAY_SECONDS)

            try:
                snapshot = self._get_current_price_with_retry(
                    kiwoom_api=kiwoom_api,
                    code=code,
                )
            except Exception as e:
                result = {
                    "event_id": None,
                    "code": code,
                    "name": None,
                    "current_price": None,
                    "volume": None,
                    "passed": False,
                    "reason": f"현재가 조회 실패: {e}",
                }
                all_results.append(result)

                self.notifier.send(
                    title="v5.1 종목 조회 실패",
                    message=json.dumps(result, ensure_ascii=False, indent=2),
                )
                continue

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

            passed, reason = self.filter.evaluate(snapshot)

            if passed and position_manager is not None and CODE_CONDITION_EXCLUDE_HOLDING:
                is_holding, position = position_manager.is_holding(snapshot["code"])

                if is_holding:
                    passed = False
                    reason = f"이미 보유 중이므로 제외: {position}"

            if (
                passed
                and position_manager is not None
                and account_no is not None
                and CODE_CONDITION_EXCLUDE_UNFILLED
            ):
                has_unfilled, unfilled = position_manager.has_unfilled_order(
                    account_no=account_no,
                    code=snapshot["code"],
                )

                if has_unfilled:
                    passed = False
                    reason = f"미체결 주문 존재로 제외: {unfilled}"

            event_id = self.repository.save_code_condition_event(
                condition_name=self.condition_name,
                code=snapshot["code"],
                name=snapshot["name"],
                current_price=snapshot["current_price"],
                volume=snapshot["volume"],
                passed=passed,
                reason=reason,
                raw_data=json.dumps(snapshot, ensure_ascii=False),
            )

            result = {
                "event_id": event_id,
                "code": snapshot["code"],
                "name": snapshot["name"],
                "current_price": snapshot["current_price"],
                "volume": snapshot["volume"],
                "passed": passed,
                "reason": reason,
            }

            all_results.append(result)

            if passed:
                self.repository.save_signal(
                    code=snapshot["code"],
                    signal_type="CODE_CONDITION_PASS",
                    strategy_name=self.condition_name,
                    price=snapshot["current_price"],
                    reason=reason,
                )

                passed_candidates.append(result)

                if len(passed_candidates) >= CODE_CONDITION_MAX_CANDIDATES:
                    break

        self.notifier.send(
            title="v5.1 코드 기반 조건검색 완료",
            message=json.dumps(
                {
                    "total_checked": len(all_results),
                    "passed_count": len(passed_candidates),
                    "passed_candidates": passed_candidates,
                },
                ensure_ascii=False,
                indent=2,
            ),
        )

        return {
            "condition_name": self.condition_name,
            "total_checked": len(all_results),
            "all_results": all_results,
            "passed_candidates": passed_candidates,
        }

    def _get_current_price_with_retry(self, kiwoom_api, code):
        last_error = None

        for attempt in range(1, CODE_CONDITION_MAX_RETRY + 2):
            try:
                return kiwoom_api.get_current_price(code)
            except Exception as e:
                last_error = e
                message = str(e)

                if "result=-200" not in message:
                    raise

                wait_seconds = CODE_CONDITION_REQUEST_DELAY_SECONDS * attempt

                self.notifier.send(
                    title="키움 TR 과부하 감지",
                    message=(
                        f"code={code}\n"
                        f"attempt={attempt}\n"
                        f"error={e}\n"
                        f"{wait_seconds}초 대기 후 재시도합니다."
                    ),
                )

                time.sleep(wait_seconds)

        raise RuntimeError(f"현재가 조회 재시도 실패: code={code}, error={last_error}")