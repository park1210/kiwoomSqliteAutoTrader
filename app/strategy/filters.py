from config import (
    CODE_CONDITION_MAX_PRICE,
    CODE_CONDITION_MIN_PRICE,
    CODE_CONDITION_MIN_VOLUME,
)


class BasicPriceVolumeFilter:
    def evaluate(self, snapshot):
        code = snapshot.get("code")
        name = snapshot.get("name")
        current_price = snapshot.get("current_price")
        volume = snapshot.get("volume")

        reasons = []

        if current_price is None:
            reasons.append("현재가 없음")
            return False, "; ".join(reasons)

        if volume is None:
            reasons.append("거래량 없음")
            return False, "; ".join(reasons)

        if current_price < CODE_CONDITION_MIN_PRICE:
            reasons.append(
                f"현재가가 최소 가격보다 낮음: {current_price} < {CODE_CONDITION_MIN_PRICE}"
            )

        if current_price > CODE_CONDITION_MAX_PRICE:
            reasons.append(
                f"현재가가 최대 가격보다 높음: {current_price} > {CODE_CONDITION_MAX_PRICE}"
            )

        if volume < CODE_CONDITION_MIN_VOLUME:
            reasons.append(
                f"거래량이 최소 거래량보다 낮음: {volume} < {CODE_CONDITION_MIN_VOLUME}"
            )

        if reasons:
            return False, "; ".join(reasons)

        return (
            True,
            (
                f"조건 통과: {code} {name}, "
                f"price={current_price}, volume={volume}"
            ),
        )