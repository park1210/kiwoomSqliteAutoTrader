from abc import ABC, abstractmethod


class BaseStrategy(ABC):
    """
    모든 전략 플러그인이 따라야 하는 공통 인터페이스.

    전략 프로젝트에서 만든 전략도 이 인터페이스만 맞추면
    자동매매 프로젝트에 쉽게 연결할 수 있다.
    """

    def __init__(self, name, params=None):
        self.name = name
        self.params = params or {}

    @abstractmethod
    def generate_signal(self, snapshot):
        """
        snapshot 예시:
        {
            "code": "005930",
            "name": "삼성전자",
            "current_price": 293750,
            "volume": 1234567,
            "raw_current_price": "+293750",
            "raw_volume": "1234567"
        }

        return:
            StrategySignal
        """
        raise NotImplementedError