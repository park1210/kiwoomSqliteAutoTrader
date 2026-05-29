import json
import time

from app.strategy.strategy_loader import StrategyLoader
from config import (
    CODE_CONDITION_MAX_RETRY,
    CODE_CONDITION_REQUEST_DELAY_SECONDS,
    STRATEGY_PLUGIN_NAME,
    STRATEGY_PLUGIN_PARAMS,
    STRATEGY_PLUGIN_UNIVERSE,
)


class StrategyRunner:
    def __init__(self, repository, notifier):
        self.repository = repository
        self.notifier = notifier
        self.loader = StrategyLoader()

    def run(self, kiwoom_api):
        strategy = self.loader.load(
            strategy_name=STRATEGY_PLUGIN_NAME,
            params=STRATEGY_PLUGIN_PARAMS,
        )

        signals = []

        self.notifier.send(
            title="v12 전략 플러그인 실행 시작",
            message=(
                f"strategy: {STRATEGY_PLUGIN_NAME}\n"
                f"universe: {STRATEGY_PLUGIN_UNIVERSE}\n"
                f"params: {json.dumps(STRATEGY_PLUGIN_PARAMS, ensure_ascii=False)}"
            ),
        )

        for idx, code in enumerate(STRATEGY_PLUGIN_UNIVERSE, start=1):
            if idx > 1:
                time.sleep(CODE_CONDITION_REQUEST_DELAY_SECONDS)

            try:
                snapshot = self._get_current_price_with_retry(kiwoom_api, code)
            except Exception as e:
                self.notifier.send(
                    title="v12 전략 데이터 조회 실패",
                    message=f"code={code}\nerror={e}",
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

            signal = strategy.generate_signal(snapshot)
            signals.append(signal)

            signal_id = self.repository.save_strategy_signal(
                strategy_name=signal.strategy_name,
                code=signal.code,
                name=signal.name,
                signal=signal.signal,
                confidence=signal.confidence,
                price=signal.price,
                volume=signal.volume,
                reason=signal.reason,
                features=signal.features_json(),
                raw_data=signal.raw_json(),
            )

            self.notifier.send(
                title="v12 전략 신호 생성",
                message=(
                    f"signal_id: {signal_id}\n"
                    f"strategy: {signal.strategy_name}\n"
                    f"code: {signal.code}\n"
                    f"name: {signal.name}\n"
                    f"signal: {signal.signal}\n"
                    f"confidence: {signal.confidence}\n"
                    f"price: {signal.price}\n"
                    f"volume: {signal.volume}\n"
                    f"reason: {signal.reason}"
                ),
            )

        result = {
            "strategy_name": STRATEGY_PLUGIN_NAME,
            "signal_count": len(signals),
            "signals": [signal.to_dict() for signal in signals],
        }

        self.notifier.send(
            title="v12 전략 플러그인 실행 완료",
            message=json.dumps(result, ensure_ascii=False, indent=2),
        )

        return result

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
                    title="v12 키움 TR 과부하 감지",
                    message=(
                        f"code={code}\n"
                        f"attempt={attempt}\n"
                        f"error={e}\n"
                        f"{wait_seconds}초 대기 후 재시도합니다."
                    ),
                )

                time.sleep(wait_seconds)

        raise RuntimeError(
            f"현재가 조회 재시도 실패: code={code}, error={last_error}"
        )