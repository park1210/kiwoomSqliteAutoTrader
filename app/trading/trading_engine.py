from app.database.repository import TradingRepository
from app.notifier.notification_service import NotificationService
from app.scenarios.registry import get_scenario_class


class TradingEngine:
    def __init__(self):
        self.repository = TradingRepository()
        self.notifier = NotificationService(repository=self.repository)

    def run(self, run_version):
        scenario_class = get_scenario_class(run_version)
        scenario = scenario_class(
            repository=self.repository,
            notifier=self.notifier,
        )
        return scenario.run()
