import traceback

from app.notifier.console_notifier import ConsoleNotifier
from app.notifier.email_notifier import EmailNotifier
from app.notifier.telegram_notifier import TelegramNotifier
from config import (
    ENABLE_CONSOLE_NOTIFICATION,
    ENABLE_EMAIL_NOTIFICATION,
    ENABLE_TELEGRAM_NOTIFICATION,
)


class NotificationService:
    def __init__(self, repository=None):
        self.repository = repository
        self.notifiers = []

        if ENABLE_CONSOLE_NOTIFICATION:
            self.notifiers.append(("ConsoleNotifier", ConsoleNotifier()))

        if ENABLE_EMAIL_NOTIFICATION:
            self.notifiers.append(("EmailNotifier", EmailNotifier()))

        if ENABLE_TELEGRAM_NOTIFICATION:
            self.notifiers.append(("TelegramNotifier", TelegramNotifier()))

    def send(self, title, message):
        success_count = 0

        if not self.notifiers:
            print("=" * 60)
            print("[알림 비활성화]")
            print("-" * 60)
            print(title)
            print(message)
            print("=" * 60)
            return False

        for channel_name, notifier in self.notifiers:
            try:
                notifier.send(title, message)
                success_count += 1

                if self.repository is not None:
                    self.repository.save_notification(
                        channel=channel_name,
                        title=title,
                        message=str(message),
                        status="SENT",
                    )

            except Exception as e:
                detail = traceback.format_exc()

                print("=" * 60)
                print(f"[알림 실패] {channel_name}")
                print("-" * 60)
                print(f"title={title}")
                print(f"error={e}")
                print(detail)
                print("=" * 60)

                if self.repository is not None:
                    self.repository.save_notification(
                        channel=channel_name,
                        title=title,
                        message=f"{message}\n\nERROR: {e}\n{detail}",
                        status="FAILED",
                    )

        return success_count > 0