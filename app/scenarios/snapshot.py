from app.scenarios.base import BaseScenario


class SnapshotScenario(BaseScenario):
    def run(self):
        from app.kiwoom.kiwoom_api import KiwoomAPI

        code = "005930"

        self.notify_login_start()

        kiwoom_api = KiwoomAPI()
        kiwoom_api.login()

        snapshot = kiwoom_api.get_current_price(code)
        self.save_snapshot_and_notify(snapshot)

