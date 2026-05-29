from datetime import datetime, timedelta


class BaseScenario:
    def __init__(self, repository, notifier):
        self.repository = repository
        self.notifier = notifier

    def run(self):
        raise NotImplementedError

    def notify_login_start(self):
        self.notifier.send(
            title="키움 로그인 시작",
            message=(
                "키움 OpenAPI+ 로그인 창이 뜨면 로그인하세요.\n"
                "모의투자를 사용할 경우 로그인 창에서 모의투자 서버를 선택하세요."
            ),
        )

    def get_first_account(self, kiwoom_api):
        accounts = kiwoom_api.get_account_list()

        if not accounts:
            raise RuntimeError("계좌번호를 가져오지 못했습니다.")

        return accounts[0]

    def notify_account_server(self, kiwoom_api, account_no):
        server_gubun = kiwoom_api.get_server_gubun()

        self.notifier.send(
            title="계좌/서버 확인",
            message=(
                f"계좌번호: {account_no}\n"
                f"server_gubun: {server_gubun!r}\n"
                "server_gubun이 '1'이면 일반적으로 모의투자 서버입니다."
            ),
        )

    def save_snapshot_and_notify(self, snapshot):
        self.repository.upsert_stock(
            code=snapshot["code"],
            name=snapshot["name"],
            market="KOSPI",
        )

        snapshot_id = self.repository.save_price_snapshot(
            code=snapshot["code"],
            name=snapshot["name"],
            current_price=snapshot["current_price"],
            volume=snapshot["volume"],
            raw_current_price=snapshot["raw_current_price"],
            raw_volume=snapshot["raw_volume"],
        )

        self.notifier.send(
            title=f"{snapshot['name']} 현재가 조회 완료",
            message=(
                f"종목코드: {snapshot['code']}\n"
                f"종목명: {snapshot['name']}\n"
                f"현재가: {snapshot['current_price']}\n"
                f"거래량: {snapshot['volume']}\n"
                f"원본 현재가: {snapshot['raw_current_price']}\n"
                f"원본 거래량: {snapshot['raw_volume']}\n"
                f"DB snapshot_id: {snapshot_id}"
            ),
        )

        return snapshot_id

    def create_sample_minute_data(self):
        start_time = datetime(2026, 5, 8, 9, 0, 0)

        closes = [
            70000, 69900, 69800, 69700, 69600,
            69500, 69400, 69300, 69200, 69100,
            69000, 68900, 68800, 68700, 68600,
            68500, 68400, 68300, 68200, 68100,
            68200, 68400, 68700, 69100, 69600,
            70200, 70900, 71700, 72600, 73600,
        ]

        rows = []

        for i, close_price in enumerate(closes):
            current_time = start_time + timedelta(minutes=5 * i)

            rows.append(
                {
                    "datetime": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "open": close_price - 100,
                    "high": close_price + 200,
                    "low": close_price - 200,
                    "close": close_price,
                    "volume": 100000 + i * 1000,
                }
            )

        return rows

