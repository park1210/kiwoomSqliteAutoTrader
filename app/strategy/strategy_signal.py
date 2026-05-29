import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional


@dataclass
class StrategySignal:
    strategy_name: str
    code: str
    name: Optional[str]
    signal: str  # BUY / SELL / HOLD
    confidence: float
    price: Optional[int]
    volume: Optional[int]
    reason: str
    features: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)

    def features_json(self):
        return json.dumps(self.features, ensure_ascii=False)

    def raw_json(self):
        return json.dumps(self.to_dict(), ensure_ascii=False)