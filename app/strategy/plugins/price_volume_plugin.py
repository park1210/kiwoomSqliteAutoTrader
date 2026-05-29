from app.strategy.base_strategy import BaseStrategy
from app.strategy.strategy_signal import StrategySignal


class PriceVolumePlugin(BaseStrategy):
    """
    v12 예시 전략.

    현재가/거래량 조건만 보고 BUY/HOLD를 판단한다.
    나중에 전략 연구 프로젝트에서 만든 전략도 이 형태만 맞추면 된다.
    """

    def generate_signal(self, snapshot):
        code = snapshot.get("code")
        name = snapshot.get("name")
        price = snapshot.get("current_price")
        volume = snapshot.get("volume")

        min_price = self.params.get("min_price", 1000)
        max_price = self.params.get("max_price", 500000)
        min_volume = self.params.get("min_volume", 100000)
        buy_confidence = self.params.get("buy_confidence", 0.7)
        hold_confidence = self.params.get("hold_confidence", 0.5)

        features = {
            "price": price,
            "volume": volume,
            "min_price": min_price,
            "max_price": max_price,
            "min_volume": min_volume,
        }

        if price is None:
            return StrategySignal(
                strategy_name=self.name,
                code=code,
                name=name,
                signal="HOLD",
                confidence=0.0,
                price=price,
                volume=volume,
                reason="현재가 정보가 없어 HOLD",
                features=features,
            )

        if volume is None:
            return StrategySignal(
                strategy_name=self.name,
                code=code,
                name=name,
                signal="HOLD",
                confidence=0.0,
                price=price,
                volume=volume,
                reason="거래량 정보가 없어 HOLD",
                features=features,
            )

        if min_price <= price <= max_price and volume >= min_volume:
            return StrategySignal(
                strategy_name=self.name,
                code=code,
                name=name,
                signal="BUY",
                confidence=buy_confidence,
                price=price,
                volume=volume,
                reason=(
                    f"가격/거래량 조건 통과: "
                    f"{min_price} <= {price} <= {max_price}, "
                    f"volume={volume} >= {min_volume}"
                ),
                features=features,
            )

        return StrategySignal(
            strategy_name=self.name,
            code=code,
            name=name,
            signal="HOLD",
            confidence=hold_confidence,
            price=price,
            volume=volume,
            reason=(
                f"가격/거래량 조건 미충족: "
                f"price={price}, volume={volume}"
            ),
            features=features,
        )