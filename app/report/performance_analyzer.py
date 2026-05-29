from datetime import datetime, timedelta
import sqlite3

from app.database.db import get_connection
from config import (
    REPORT_INCLUDE_ACCOUNT_SUMMARY,
    REPORT_INCLUDE_CODE_CONDITION_EVENTS,
    REPORT_INCLUDE_CONDITION_TRADE_DECISIONS,
    REPORT_INCLUDE_LOOP_RUNS,
    REPORT_INCLUDE_NOTIFICATIONS,
    REPORT_INCLUDE_SELL_DECISIONS,
    REPORT_LOOKBACK_DAYS,
    REPORT_MAX_ROWS,
)


class PerformanceAnalyzer:
    def __init__(self):
        self.report_date = datetime.now().date()
        self.start_datetime = datetime.now() - timedelta(days=REPORT_LOOKBACK_DAYS)
        self.start_text = self.start_datetime.strftime("%Y-%m-%d %H:%M:%S")

    def analyze(self):
        return {
            "report_date": str(self.report_date),
            "lookback_days": REPORT_LOOKBACK_DAYS,
            "start_datetime": self.start_text,
            "account_summary": (
                self.get_latest_account_summary()
                if REPORT_INCLUDE_ACCOUNT_SUMMARY
                else None
            ),
            "sell_decisions": (
                self.get_recent_sell_decisions()
                if REPORT_INCLUDE_SELL_DECISIONS
                else []
            ),
            "condition_trade_decisions": (
                self.get_recent_condition_trade_decisions()
                if REPORT_INCLUDE_CONDITION_TRADE_DECISIONS
                else []
            ),
            "code_condition_events": (
                self.get_recent_code_condition_events()
                if REPORT_INCLUDE_CODE_CONDITION_EVENTS
                else []
            ),
            "loop_runs": (
                self.get_recent_loop_runs()
                if REPORT_INCLUDE_LOOP_RUNS
                else []
            ),
            "notification_summary": (
                self.get_notification_summary()
                if REPORT_INCLUDE_NOTIFICATIONS
                else []
            ),
            "notification_recent": (
                self.get_recent_notifications()
                if REPORT_INCLUDE_NOTIFICATIONS
                else []
            ),
        }

    def get_latest_account_summary(self):
        sql = """
        SELECT id, account_no, cash, total_buy_amount, total_eval_amount,
               total_profit_loss, total_profit_rate, captured_at
        FROM account_snapshots
        ORDER BY id DESC
        LIMIT 1
        """
        rows = self._fetch_all_safe(sql)
        return rows[0] if rows else None

    def get_recent_sell_decisions(self):
        sql = """
        SELECT id, code, name, quantity, avg_price, current_price,
               eval_amount, profit_loss, profit_rate, decision,
               reason, ordered, order_id, created_at
        FROM sell_decisions
        WHERE created_at >= ?
        ORDER BY id DESC
        LIMIT ?
        """
        return self._fetch_all_safe(sql, (self.start_text, REPORT_MAX_ROWS))

    def get_recent_condition_trade_decisions(self):
        sql = """
        SELECT id, condition_index, condition_name, code, name,
               current_price, quantity, decision, reason,
               ordered, order_id, created_at
        FROM condition_trade_decisions
        WHERE created_at >= ?
        ORDER BY id DESC
        LIMIT ?
        """
        return self._fetch_all_safe(sql, (self.start_text, REPORT_MAX_ROWS))

    def get_recent_code_condition_events(self):
        sql = """
        SELECT id, condition_name, code, name, current_price,
               volume, passed, reason, created_at
        FROM code_condition_events
        WHERE created_at >= ?
        ORDER BY id DESC
        LIMIT ?
        """
        return self._fetch_all_safe(sql, (self.start_text, REPORT_MAX_ROWS))

    def get_recent_loop_runs(self):
        sql = """
        SELECT id, loop_no, status, message, started_at, finished_at
        FROM loop_runs
        WHERE started_at >= ?
        ORDER BY id DESC
        LIMIT ?
        """
        return self._fetch_all_safe(sql, (self.start_text, REPORT_MAX_ROWS))

    def get_notification_summary(self):
        sql = """
        SELECT channel, status, COUNT(*) AS count
        FROM notifications
        WHERE created_at >= ?
        GROUP BY channel, status
        ORDER BY channel, status
        """
        return self._fetch_all_safe(sql, (self.start_text,))

    def get_recent_notifications(self):
        sql = """
        SELECT id, channel, title, status, created_at
        FROM notifications
        WHERE created_at >= ?
        ORDER BY id DESC
        LIMIT ?
        """
        return self._fetch_all_safe(sql, (self.start_text, REPORT_MAX_ROWS))

    def _fetch_all_safe(self, sql, params=None):
        if params is None:
            params = ()

        try:
            with get_connection() as conn:
                rows = conn.execute(sql, params).fetchall()

            return [dict(row) for row in rows]

        except sqlite3.OperationalError as e:
            return [
                {
                    "error": str(e),
                    "message": "테이블이 없거나 아직 해당 데이터가 없습니다.",
                }
            ]