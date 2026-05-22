from datetime import datetime


class ReportGenerator:
    def generate_markdown(self, analysis):
        lines = []

        report_date = analysis.get("report_date")
        lookback_days = analysis.get("lookback_days")
        start_datetime = analysis.get("start_datetime")

        lines.append("# Kiwoom SQLite AutoTrader Daily Report")
        lines.append("")
        lines.append("## 1. Report Info")
        lines.append("")
        lines.append(f"- Generated At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"- Report Date: {report_date}")
        lines.append(f"- Lookback Days: {lookback_days}")
        lines.append(f"- Start Datetime: {start_datetime}")
        lines.append("")

        self._append_account_summary(lines, analysis.get("account_summary"))
        self._append_sell_decisions(lines, analysis.get("sell_decisions", []))
        self._append_condition_trade_decisions(
            lines,
            analysis.get("condition_trade_decisions", []),
        )
        self._append_code_condition_events(
            lines,
            analysis.get("code_condition_events", []),
        )
        self._append_loop_runs(lines, analysis.get("loop_runs", []))
        self._append_notification_summary(
            lines,
            analysis.get("notification_summary", []),
        )
        self._append_recent_notifications(
            lines,
            analysis.get("notification_recent", []),
        )

        return "\n".join(lines)

    def _append_account_summary(self, lines, summary):
        lines.append("## 2. Latest Account Summary")
        lines.append("")

        if not summary:
            lines.append("- No account snapshot data.")
            lines.append("")
            return

        if "error" in summary:
            lines.append(f"- Error: {summary.get('error')}")
            lines.append("")
            return

        lines.append(f"- Account No: {summary.get('account_no')}")
        lines.append(
            f"- Total Buy Amount: {self._fmt_int(summary.get('total_buy_amount'))}"
        )
        lines.append(
            f"- Total Evaluation Amount: {self._fmt_int(summary.get('total_eval_amount'))}"
        )
        lines.append(
            f"- Total Profit/Loss: {self._fmt_int(summary.get('total_profit_loss'))}"
        )
        lines.append(f"- Total Profit Rate: {summary.get('total_profit_rate')}%")
        lines.append(f"- Captured At: {summary.get('captured_at')}")
        lines.append("")

    def _append_sell_decisions(self, lines, rows):
        lines.append("## 3. Sell Decisions")
        lines.append("")

        headers = [
            "ID",
            "Code",
            "Name",
            "Qty",
            "Current",
            "Profit Rate",
            "Decision",
            "Ordered",
            "Created",
        ]
        keys = [
            "id",
            "code",
            "name",
            "quantity",
            "current_price",
            "profit_rate",
            "decision",
            "ordered",
            "created_at",
        ]

        self._append_table(lines, headers, keys, rows)

    def _append_condition_trade_decisions(self, lines, rows):
        lines.append("## 4. Condition Trade Decisions")
        lines.append("")

        headers = [
            "ID",
            "Condition",
            "Code",
            "Name",
            "Price",
            "Qty",
            "Decision",
            "Ordered",
            "Created",
        ]
        keys = [
            "id",
            "condition_name",
            "code",
            "name",
            "current_price",
            "quantity",
            "decision",
            "ordered",
            "created_at",
        ]

        self._append_table(lines, headers, keys, rows)

    def _append_code_condition_events(self, lines, rows):
        lines.append("## 5. Code Condition Events")
        lines.append("")

        headers = [
            "ID",
            "Condition",
            "Code",
            "Name",
            "Price",
            "Volume",
            "Passed",
            "Created",
        ]
        keys = [
            "id",
            "condition_name",
            "code",
            "name",
            "current_price",
            "volume",
            "passed",
            "created_at",
        ]

        self._append_table(lines, headers, keys, rows)

    def _append_loop_runs(self, lines, rows):
        lines.append("## 6. Loop Runs")
        lines.append("")

        headers = [
            "ID",
            "Loop",
            "Status",
            "Started",
            "Finished",
        ]
        keys = [
            "id",
            "loop_no",
            "status",
            "started_at",
            "finished_at",
        ]

        self._append_table(lines, headers, keys, rows)

    def _append_notification_summary(self, lines, rows):
        lines.append("## 7. Notification Summary")
        lines.append("")

        headers = ["Channel", "Status", "Count"]
        keys = ["channel", "status", "count"]

        self._append_table(lines, headers, keys, rows)

    def _append_recent_notifications(self, lines, rows):
        lines.append("## 8. Recent Notifications")
        lines.append("")

        headers = ["ID", "Channel", "Title", "Status", "Created"]
        keys = ["id", "channel", "title", "status", "created_at"]

        self._append_table(lines, headers, keys, rows)

    def _append_table(self, lines, headers, keys, rows):
        if not rows:
            lines.append("- No data.")
            lines.append("")
            return

        if len(rows) == 1 and "error" in rows[0]:
            lines.append(f"- Error: {rows[0].get('error')}")
            lines.append(f"- Message: {rows[0].get('message')}")
            lines.append("")
            return

        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

        for row in rows:
            values = [self._fmt_cell(row.get(key)) for key in keys]
            lines.append("| " + " | ".join(values) + " |")

        lines.append("")

    def _fmt_cell(self, value):
        if value is None:
            return ""

        text = str(value)
        text = text.replace("\n", " ")
        text = text.replace("|", "/")
        return text

    def _fmt_int(self, value):
        if value is None:
            return ""

        try:
            return f"{int(value):,}"
        except (TypeError, ValueError):
            return str(value)