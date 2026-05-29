import json
import os
import urllib.parse
import urllib.request

from config import TELEGRAM_BOT_TOKEN_ENV, TELEGRAM_CHAT_ID_ENV


class TelegramNotifier:
    def __init__(self):
        self.bot_token = os.getenv(TELEGRAM_BOT_TOKEN_ENV)
        self.chat_id = os.getenv(TELEGRAM_CHAT_ID_ENV)

    def is_configured(self):
        return bool(self.bot_token and self.chat_id)

    def send(self, title, message):
        if not self.is_configured():
            raise RuntimeError(
                "TelegramNotifier 환경변수가 설정되지 않았습니다. "
                "KSA_TELEGRAM_BOT_TOKEN, KSA_TELEGRAM_CHAT_ID를 확인하세요."
            )

        text = f"[KiwoomAutoTrader]\n{title}\n\n{message}"

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

        payload = urllib.parse.urlencode(
            {
                "chat_id": self.chat_id,
                "text": text,
            }
        ).encode("utf-8")

        request = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read().decode("utf-8")

        result = json.loads(body)

        if not result.get("ok"):
            raise RuntimeError(f"Telegram 전송 실패: {result}")

        return True