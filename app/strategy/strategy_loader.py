from app.strategy.plugins.price_volume_plugin import PriceVolumePlugin


class StrategyLoader:
    """
    settings.yaml의 strategy_plugin.name 값을 보고 전략 클래스를 선택한다.
    """

    def load(self, strategy_name, params=None):
        if strategy_name == "price_volume_plugin":
            return PriceVolumePlugin(
                name=strategy_name,
                params=params,
            )

        raise ValueError(
            f"지원하지 않는 전략 플러그인입니다: {strategy_name}"
        )