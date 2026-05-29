from app.scenarios.base import BaseScenario


class TradingReportScenario(BaseScenario):
    def run(self):
        from app.report.report_service import ReportService
        from config import REPORT_SEND_NOTIFICATION

        self.notifier.send(
            title="v10 거래 리포트 생성 시작",
            message=(
                "DB에 저장된 계좌/조건검색/매도판단/루프/알림 기록을 분석하여 "
                "Markdown 리포트를 생성합니다."
            ),
        )

        report_service = ReportService(
            repository=self.repository,
            notifier=self.notifier,
        )

        report_result = report_service.generate_daily_report()

        if REPORT_SEND_NOTIFICATION:
            report_service.notify_report(report_result)

        self.repository.save_system_log(
            level="INFO",
            message="v10 trading report finished",
            detail=report_result["report_path"],
        )

        self.notifier.send(
            title="v10 거래 리포트 생성 완료",
            message=f"report_path: {report_result['report_path']}",
        )

