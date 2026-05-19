from datetime import datetime, time

from config import (
    ALLOW_LOOP_OUTSIDE_MARKET,
    MARKET_CLOSE_TIME,
    MARKET_OPEN_TIME,
)


class MarketTimeChecker:
    def __init__(self):
        self.market_open = self._parse_time(MARKET_OPEN_TIME)
        self.market_close = self._parse_time(MARKET_CLOSE_TIME)

    def is_market_time(self):
        if ALLOW_LOOP_OUTSIDE_MARKET:
            return True

        now = datetime.now().time()

        return self.market_open <= now <= self.market_close

    def get_status_message(self):
        now = datetime.now()

        if self.is_market_time():
            return (
                f"시장 운영 가능 시간입니다. "
                f"now={now.strftime('%Y-%m-%d %H:%M:%S')}, "
                f"open={MARKET_OPEN_TIME}, close={MARKET_CLOSE_TIME}"
            )

        return (
            f"시장 운영 시간이 아닙니다. "
            f"now={now.strftime('%Y-%m-%d %H:%M:%S')}, "
            f"open={MARKET_OPEN_TIME}, close={MARKET_CLOSE_TIME}"
        )

    def _parse_time(self, text):
        hour, minute = text.split(":")
        return time(hour=int(hour), minute=int(minute))