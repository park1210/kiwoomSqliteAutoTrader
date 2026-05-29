from app.scenarios.base import BaseScenario


class SimulationScenario(BaseScenario):
    def run(self):
        from app.strategy.moving_average_strategy import MovingAverageStrategy
        from config import LONG_WINDOW, SHORT_WINDOW

        strategy = MovingAverageStrategy(
            short_window=SHORT_WINDOW,
            long_window=LONG_WINDOW,
        )

        code = "005930"
        name = "삼성전자"

        self.repository.upsert_stock(code=code, name=name, market="KOSPI")

        price_rows = self.create_sample_minute_data()
        self.repository.save_price_minute(code=code, price_rows=price_rows)

        loaded_price_data = self.repository.get_price_minute(code=code, limit=100)

        signal = strategy.generate_signal(
            code=code,
            price_data=loaded_price_data,
        )

        signal_id = self.repository.save_signal(
            code=code,
            signal_type=signal["signal_type"],
            strategy_name=strategy.name,
            price=signal["price"],
            reason=signal["reason"],
        )

        title = f"{name} 신호 발생: {signal['signal_type']}"
        message = (
            f"종목코드: {code}\n"
            f"종목명: {name}\n"
            f"전략: {strategy.name}\n"
            f"현재가: {signal['price']}\n"
            f"신호: {signal['signal_type']}\n"
            f"이유: {signal['reason']}\n"
            f"DB signal_id: {signal_id}"
        )

        self.notifier.send(title, message)

