import os
import smtplib
from email.mime.text import MIMEText

from config import (
    EMAIL_FROM_ENV,
    EMAIL_PASSWORD_ENV,
    EMAIL_SMTP_HOST_ENV,
    EMAIL_SMTP_PORT_ENV,
    EMAIL_TO_ENV,
    EMAIL_USERNAME_ENV,
)


class EmailNotifier:
    def __init__(self):
        self.smtp_host = os.getenv(EMAIL_SMTP_HOST_ENV)
        self.smtp_port = int(os.getenv(EMAIL_SMTP_PORT_ENV, "587"))
        self.username = os.getenv(EMAIL_USERNAME_ENV)
        self.password = os.getenv(EMAIL_PASSWORD_ENV)
        self.email_from = os.getenv(EMAIL_FROM_ENV) or self.username
        self.email_to = os.getenv(EMAIL_TO_ENV)

    def is_configured(self):
        required = [
            self.smtp_host,
            self.smtp_port,
            self.username,
            self.password,
            self.email_from,
            self.email_to,
        ]
        return all(required)

    def send(self, title, message):
        if not self.is_configured():
            raise RuntimeError(
                "EmailNotifier 환경변수가 설정되지 않았습니다. "
                "KSA_EMAIL_* 환경변수를 확인하세요."
            )

        msg = MIMEText(str(message), _charset="utf-8")
        msg["Subject"] = f"[KiwoomAutoTrader] {title}"
        msg["From"] = self.email_from
        msg["To"] = self.email_to

        with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)

        return True