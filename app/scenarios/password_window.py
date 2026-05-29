from app.scenarios.base import BaseScenario


class PasswordWindowScenario(BaseScenario):
    def run(self):
        from app.kiwoom.kiwoom_api import KiwoomAPI

        self.notifier.send(
            title="계좌비밀번호 입력창 열기",
            message="로그인 후 계좌비밀번호 입력창이 열립니다.",
        )

        kiwoom_api = KiwoomAPI()
        kiwoom_api.login()
        kiwoom_api.show_account_password_window()

        self.notifier.send(
            title="계좌비밀번호 입력창 확인",
            message="창이 열리면 계좌비밀번호를 입력하고 등록/AUTO 체크 후 닫으세요.",
        )

