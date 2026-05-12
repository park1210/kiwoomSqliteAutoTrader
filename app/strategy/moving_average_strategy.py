import pandas as pd

from app.strategy.base_strategy import BaseStrategy


class MovingAverageStrategy(BaseStrategy):
    def __init__(self, short_window=5, long_window=20):
        if short_window >= long_window:
            raise ValueError("short_window은 long_window보다 작아야 합니다.")

        self.short_window = short_window
        self.long_window = long_window
        self.name = "MovingAverageStrategy"

    def generate_signal(self, code, price_data):
        if len(price_data) < self.long_window + 1:
            return {
                "signal_type": "HOLD",
                "price": None,
                "reason": f"데이터 부족: 최소 {self.long_window + 1}개 필요",
            }

        df = pd.DataFrame(price_data)
        df["close"] = df["close"].astype(int)

        df["ma_short"] = df["close"].rolling(window=self.short_window).mean()
        df["ma_long"] = df["close"].rolling(window=self.long_window).mean()

        prev = df.iloc[-2]
        curr = df.iloc[-1]

        current_price = int(curr["close"])

        prev_short = prev["ma_short"]
        prev_long = prev["ma_long"]
        curr_short = curr["ma_short"]
        curr_long = curr["ma_long"]

        if (
            pd.isna(prev_short)
            or pd.isna(prev_long)
            or pd.isna(curr_short)
            or pd.isna(curr_long)
        ):
            return {
                "signal_type": "HOLD",
                "price": current_price,
                "reason": "이동평균 계산 불가",
            }

        if prev_short <= prev_long and curr_short > curr_long:
            return {
                "signal_type": "BUY",
                "price": current_price,
                "reason": f"MA{self.short_window}가 MA{self.long_window}을 상향 돌파",
            }

        if prev_short >= prev_long and curr_short < curr_long:
            return {
                "signal_type": "SELL",
                "price": current_price,
                "reason": f"MA{self.short_window}가 MA{self.long_window}을 하향 이탈",
            }

        return {
            "signal_type": "HOLD",
            "price": current_price,
            "reason": "매수/매도 조건 없음",
        }