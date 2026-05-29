class PositionManager:
    def __init__(self, repository, notifier):
        self.repository = repository
        self.notifier = notifier

    def sync_account_state(self, kiwoom_api, account_no):
        """
        키움 계좌평가잔고내역을 조회하여
        account_snapshots, positions 테이블을 갱신한다.
        """
        account_data = kiwoom_api.get_account_balance(account_no)

        summary = account_data.get("summary", {})
        positions = account_data.get("positions", [])

        snapshot_id = self.repository.save_account_snapshot(
            account_no=account_no,
            account_summary=summary,
        )

        self.repository.replace_positions(positions)

        self.notifier.send(
            title="계좌/보유종목 동기화 완료",
            message=(
                f"계좌번호: {account_no}\n"
                f"보유 종목 수: {len(positions)}\n"
                f"총매입금액: {summary.get('total_buy_amount')}\n"
                f"총평가금액: {summary.get('total_eval_amount')}\n"
                f"총평가손익: {summary.get('total_profit_loss')}\n"
                f"총수익률(%): {summary.get('total_profit_rate')}\n"
                f"account_snapshot_id: {snapshot_id}"
            ),
        )

        return {
            "summary": summary,
            "positions": positions,
            "snapshot_id": snapshot_id,
        }

    def sync_unfilled_orders(self, kiwoom_api, account_no):
        """
        키움 미체결요청을 조회하여
        unfilled_orders 테이블을 갱신한다.
        """
        unfilled_orders = kiwoom_api.get_unfilled_orders(account_no)

        self.repository.replace_unfilled_orders(
            account_no=account_no,
            unfilled_orders=unfilled_orders,
        )

        self.notifier.send(
            title="미체결 주문 동기화 완료",
            message=(
                f"계좌번호: {account_no}\n"
                f"미체결 주문 수: {len(unfilled_orders)}"
            ),
        )

        return unfilled_orders

    def is_holding(self, code):
        """
        특정 종목을 현재 보유 중인지 확인한다.
        """
        position = self.repository.get_position_by_code(code)

        if not position:
            return False, None

        quantity = position.get("quantity") or 0

        return quantity > 0, position

    def has_unfilled_order(self, account_no, code):
        """
        특정 종목에 대한 미체결 주문이 있는지 확인한다.
        """
        unfilled = self.repository.get_unfilled_order_by_code(
            account_no=account_no,
            code=code,
        )

        return unfilled is not None, unfilled