from app.scenarios.code_condition_order import CodeConditionOrderScenario
from app.scenarios.code_condition_scan import CodeConditionScanScenario
from app.scenarios.kiwoom_condition_order import KiwoomConditionOrderScenario
from app.scenarios.kiwoom_condition_scan import KiwoomConditionScanScenario
from app.scenarios.paper_order_test import PaperOrderTestScenario
from app.scenarios.password_window import PasswordWindowScenario
from app.scenarios.position_tracking import PositionTrackingScenario
from app.scenarios.safety_guard_test import SafetyGuardTestScenario
from app.scenarios.sell_exit_test import SellExitTestScenario
from app.scenarios.simulation import SimulationScenario
from app.scenarios.snapshot import SnapshotScenario
from app.scenarios.strategy_plugin_test import StrategyPluginTestScenario
from app.scenarios.trading_loop import TradingLoopScenario
from app.scenarios.trading_report import TradingReportScenario


SCENARIO_REGISTRY = {
    "password": PasswordWindowScenario,
    "v1": SimulationScenario,
    "v2": SnapshotScenario,
    "v3": PaperOrderTestScenario,
    "v4": PositionTrackingScenario,
    "v5": KiwoomConditionScanScenario,
    "v5.1": CodeConditionScanScenario,
    "v5_1": CodeConditionScanScenario,
    "v6": KiwoomConditionOrderScenario,
    "v6.1": CodeConditionOrderScenario,
    "v6_1": CodeConditionOrderScenario,
    "v7": SellExitTestScenario,
    "v8": TradingLoopScenario,
    "v8.1": TradingLoopScenario,
    "v8_1": TradingLoopScenario,
    "v8.2": TradingLoopScenario,
    "v8_2": TradingLoopScenario,
    "v9": TradingReportScenario,
    "v10": SafetyGuardTestScenario,
}


def get_scenario_class(run_version):
    try:
        return SCENARIO_REGISTRY[run_version]
    except KeyError as exc:
        raise ValueError(f"알 수 없는 RUN_VERSION: {run_version}") from exc
