from app.notifier.base_notifier import BaseNotifier


class ConsoleNotifier(BaseNotifier):
    def send(self, title, message):
        print("=" * 60)
        print(f"[알림] {title}")
        print("-" * 60)
        print(message)
        print("=" * 60)