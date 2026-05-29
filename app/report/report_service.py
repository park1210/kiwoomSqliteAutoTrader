from datetime import datetime
from pathlib import Path

from app.report.performance_analyzer import PerformanceAnalyzer
from app.report.report_generator import ReportGenerator
from config import BASE_DIR, REPORT_OUTPUT_DIR, REPORT_SEND_FULL_REPORT


class ReportService:
    def __init__(self, repository, notifier):
        self.repository = repository
        self.notifier = notifier
        self.analyzer = PerformanceAnalyzer()
        self.generator = ReportGenerator()

    def generate_daily_report(self):
        analysis = self.analyzer.analyze()
        markdown = self.generator.generate_markdown(analysis)

        report_dir = BASE_DIR / REPORT_OUTPUT_DIR
        report_dir.mkdir(parents=True, exist_ok=True)

        report_date = datetime.now().strftime("%Y-%m-%d")
        report_path = report_dir / f"daily_report_{report_date}.md"

        report_path.write_text(markdown, encoding="utf-8")

        self.repository.save_system_log(
            level="INFO",
            message="daily report generated",
            detail=str(report_path),
        )

        return {
            "report_path": str(report_path),
            "markdown": markdown,
            "analysis": analysis,
        }

    def notify_report(self, report_result):
        report_path = report_result["report_path"]
        markdown = report_result["markdown"]

        if REPORT_SEND_FULL_REPORT:
            message = (
                f"Daily report generated.\n"
                f"Path: {report_path}\n\n"
                f"{markdown}"
            )
        else:
            message = f"Daily report generated.\nPath: {report_path}"

        self.notifier.send(
            title="v10 Daily Trading Report",
            message=message,
        )