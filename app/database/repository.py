from app.database.db import get_connection


class TradingRepository:
    def upsert_stock(self, code, name, market="KOSPI"):
        sql = """
        INSERT INTO stocks (code, name, market)
        VALUES (?, ?, ?)
        ON CONFLICT(code)
        DO UPDATE SET
            name = excluded.name,
            market = excluded.market,
            is_active = 1
        """

        with get_connection() as conn:
            conn.execute(sql, (code, name, market))
            conn.commit()

    def save_price_minute(self, code, price_rows):
        sql = """
        INSERT INTO price_minute (
            code, datetime, open, high, low, close, volume
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(code, datetime)
        DO UPDATE SET
            open = excluded.open,
            high = excluded.high,
            low = excluded.low,
            close = excluded.close,
            volume = excluded.volume
        """

        values = [
            (
                code,
                row["datetime"],
                row["open"],
                row["high"],
                row["low"],
                row["close"],
                row["volume"],
            )
            for row in price_rows
        ]

        with get_connection() as conn:
            conn.executemany(sql, values)
            conn.commit()

    def get_price_minute(self, code, limit=100):
        sql = """
        SELECT datetime, open, high, low, close, volume
        FROM price_minute
        WHERE code = ?
        ORDER BY datetime DESC
        LIMIT ?
        """

        with get_connection() as conn:
            rows = conn.execute(sql, (code, limit)).fetchall()

        return [dict(row) for row in rows][::-1]

    def save_price_snapshot(
        self,
        code,
        name,
        current_price,
        volume=None,
        raw_current_price=None,
        raw_volume=None,
    ):
        sql = """
        INSERT INTO price_snapshot (
            code, name, current_price, volume, raw_current_price, raw_volume
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """

        with get_connection() as conn:
            cursor = conn.execute(
                sql,
                (
                    code,
                    name,
                    current_price,
                    volume,
                    raw_current_price,
                    raw_volume,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def save_signal(self, code, signal_type, strategy_name, price, reason):
        sql = """
        INSERT INTO signals (
            code, signal_type, strategy_name, price, reason
        )
        VALUES (?, ?, ?, ?, ?)
        """

        with get_connection() as conn:
            cursor = conn.execute(
                sql,
                (code, signal_type, strategy_name, price, reason),
            )
            conn.commit()
            return cursor.lastrowid

    def save_order(
        self,
        code,
        name,
        account_no,
        order_type,
        quantity,
        price,
        hoga_gb,
        reason,
        status="REQUESTED",
    ):
        sql = """
        INSERT INTO orders (
            code, name, account_no, order_type, quantity,
            price, hoga_gb, status, reason
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        with get_connection() as conn:
            cursor = conn.execute(
                sql,
                (
                    code,
                    name,
                    account_no,
                    order_type,
                    quantity,
                    price,
                    hoga_gb,
                    status,
                    reason,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def update_order_status(
        self,
        order_id,
        status,
        kiwoom_order_no=None,
    ):
        sql = """
        UPDATE orders
        SET status = ?,
            kiwoom_order_no = COALESCE(?, kiwoom_order_no),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """

        with get_connection() as conn:
            conn.execute(sql, (status, kiwoom_order_no, order_id))
            conn.commit()

    def save_execution(
        self,
        order_id,
        code,
        name,
        kiwoom_order_no,
        order_status,
        order_type_raw,
        quantity,
        price,
        unfilled_quantity,
        execution_price,
        execution_quantity,
        execution_time,
        raw_data,
    ):
        sql = """
        INSERT INTO executions (
            order_id, code, name, kiwoom_order_no, order_status,
            order_type_raw, quantity, price, unfilled_quantity,
            execution_price, execution_quantity, execution_time, raw_data
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        with get_connection() as conn:
            cursor = conn.execute(
                sql,
                (
                    order_id,
                    code,
                    name,
                    kiwoom_order_no,
                    order_status,
                    order_type_raw,
                    quantity,
                    price,
                    unfilled_quantity,
                    execution_price,
                    execution_quantity,
                    execution_time,
                    raw_data,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def save_notification(self, channel, title, message, status="PENDING"):
        sql = """
        INSERT INTO notifications (channel, title, message, status)
        VALUES (?, ?, ?, ?)
        """

        with get_connection() as conn:
            cursor = conn.execute(sql, (channel, title, message, status))
            conn.commit()
            return cursor.lastrowid

    def save_system_log(self, level, message, detail=None):
        sql = """
        INSERT INTO system_logs (level, message, detail)
        VALUES (?, ?, ?)
        """

        with get_connection() as conn:
            conn.execute(sql, (level, message, detail))
            conn.commit()