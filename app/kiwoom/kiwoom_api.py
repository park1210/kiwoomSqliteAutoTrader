import json

from PyQt5.QtCore import QEventLoop, QTimer
from PyQt5.QAxContainer import QAxWidget


class KiwoomAPI:
    def __init__(self):
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")

        if self.ocx.isNull():
            raise RuntimeError(
                "키움 OpenAPI+ ActiveX 컨트롤 생성 실패.\n"
                "확인할 것:\n"
                "1. 현재 Python이 32bit인지 확인\n"
                "2. 키움 OpenAPI+가 설치되어 있는지 확인\n"
                "3. OpenAPISetup.exe 재설치 후 PC 재부팅"
            )

        self.login_loop = None
        self.tr_loop = None
        self.order_loop = None

        self.tr_data = {}
        self.last_chejan_data = {}

        self.ocx.OnEventConnect.connect(self._on_event_connect)
        self.ocx.OnReceiveTrData.connect(self._on_receive_tr_data)
        self.ocx.OnReceiveChejanData.connect(self._on_receive_chejan_data)

    def login(self):
        self.login_loop = QEventLoop()

        result = self.ocx.dynamicCall("CommConnect()")

        if result != 0:
            raise RuntimeError(f"CommConnect 호출 실패: result={result}")

        self.login_loop.exec_()

    def _on_event_connect(self, err_code):
        if err_code == 0:
            print("[Kiwoom] 로그인 성공")
        else:
            print(f"[Kiwoom] 로그인 실패: err_code={err_code}")

        if self.login_loop is not None:
            self.login_loop.exit()

    def get_login_info(self, tag):
        value = self.ocx.dynamicCall("GetLoginInfo(QString)", tag)
        return str(value).strip()

    def get_account_list(self):
        raw = self.get_login_info("ACCNO")
        return [acc for acc in raw.split(";") if acc]

    def get_server_gubun(self):
        return self.get_login_info("GetServerGubun")

    def show_account_password_window(self):
        self.ocx.dynamicCall(
            "KOA_Functions(QString, QString)",
            "ShowAccountWindow",
            "",
        )

    def get_stock_name(self, code):
        name = self.ocx.dynamicCall("GetMasterCodeName(QString)", code)
        return str(name).strip()

    def get_current_price(self, code):
        self.tr_data = {}

        self.ocx.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)

        self.tr_loop = QEventLoop()

        result = self.ocx.dynamicCall(
            "CommRqData(QString, QString, int, QString)",
            "주식기본정보요청",
            "opt10001",
            0,
            "0101",
        )

        if result != 0:
            raise RuntimeError(f"CommRqData 호출 실패: result={result}")

        self.tr_loop.exec_()

        name = self.get_stock_name(code)

        raw_current_price = self.tr_data.get("현재가", "")
        raw_volume = self.tr_data.get("거래량", "")

        return {
            "code": code,
            "name": name,
            "current_price": self._to_positive_int(raw_current_price),
            "volume": self._to_positive_int(raw_volume),
            "raw_current_price": raw_current_price,
            "raw_volume": raw_volume,
        }

    def get_account_balance(self, account_no):
        """
        opw00018: 계좌평가잔고내역요청
        """
        self.tr_data = {}

        self.ocx.dynamicCall("SetInputValue(QString, QString)", "계좌번호", account_no)
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "")
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "조회구분", "2")

        self.tr_loop = QEventLoop()

        result = self.ocx.dynamicCall(
            "CommRqData(QString, QString, int, QString)",
            "계좌평가잔고내역요청",
            "opw00018",
            0,
            "2001",
        )

        if result != 0:
            raise RuntimeError(f"계좌평가잔고내역요청 실패: result={result}")

        self.tr_loop.exec_()

        return self.tr_data

    def get_unfilled_orders(self, account_no):
        """
        opt10075: 미체결요청
        """
        self.tr_data = {}

        self.ocx.dynamicCall("SetInputValue(QString, QString)", "계좌번호", account_no)
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "전체종목구분", "0")
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "매매구분", "0")
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "종목코드", "")
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "체결구분", "1")

        self.tr_loop = QEventLoop()

        result = self.ocx.dynamicCall(
            "CommRqData(QString, QString, int, QString)",
            "미체결요청",
            "opt10075",
            0,
            "2002",
        )

        if result != 0:
            raise RuntimeError(f"미체결요청 실패: result={result}")

        self.tr_loop.exec_()

        return self.tr_data.get("unfilled_orders", [])

    def send_market_buy_order(self, account_no, code, quantity):
        return self.send_order(
            rqname="v4_시장가매수",
            screen_no="3000",
            account_no=account_no,
            order_type=1,
            code=code,
            quantity=quantity,
            price=0,
            hoga_gb="03",
            org_order_no="",
        )

    def send_order(
        self,
        rqname,
        screen_no,
        account_no,
        order_type,
        code,
        quantity,
        price,
        hoga_gb,
        org_order_no="",
        wait_ms=10000,
    ):
        self.last_chejan_data = {}

        result = self.ocx.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            [
                rqname,
                screen_no,
                account_no,
                order_type,
                code,
                quantity,
                price,
                hoga_gb,
                org_order_no,
            ],
        )

        if result != 0:
            return {
                "success": False,
                "result_code": result,
                "message": (
                    f"SendOrder 호출 실패: result={result}, "
                    f"reason={self._get_order_error_message(result)}"
                ),
                "chejan": {},
            }

        self.order_loop = QEventLoop()

        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(self.order_loop.exit)
        timer.start(wait_ms)

        self.order_loop.exec_()

        return {
            "success": True,
            "result_code": result,
            "message": "SendOrder 호출 성공",
            "chejan": self.last_chejan_data,
        }

    def _on_receive_tr_data(
        self,
        screen_no,
        rqname,
        trcode,
        record_name,
        prev_next,
        data_len,
        error_code,
        message,
        splm_msg,
    ):
        if rqname == "주식기본정보요청":
            current_price = self._get_comm_data(trcode, rqname, 0, "현재가")
            volume = self._get_comm_data(trcode, rqname, 0, "거래량")

            self.tr_data = {
                "현재가": current_price,
                "거래량": volume,
            }

        elif rqname == "계좌평가잔고내역요청":
            self.tr_data = self._parse_account_balance(trcode, rqname)

        elif rqname == "미체결요청":
            self.tr_data = {
                "unfilled_orders": self._parse_unfilled_orders(trcode, rqname)
            }

        if self.tr_loop is not None:
            self.tr_loop.exit()

    def _parse_account_balance(self, trcode, rqname):
        summary = {
            "cash": None,
            "total_buy_amount": self._to_signed_int(
                self._get_comm_data(trcode, rqname, 0, "총매입금액")
            ),
            "total_eval_amount": self._to_signed_int(
                self._get_comm_data(trcode, rqname, 0, "총평가금액")
            ),
            "total_profit_loss": self._to_signed_int(
                self._get_comm_data(trcode, rqname, 0, "총평가손익금액")
            ),
            "total_profit_rate": self._to_float(
                self._get_comm_data(trcode, rqname, 0, "총수익률(%)")
            ),
        }

        count = self.ocx.dynamicCall(
            "GetRepeatCnt(QString, QString)",
            trcode,
            rqname,
        )

        positions = []

        for i in range(count):
            code = self._clean_code(self._get_comm_data(trcode, rqname, i, "종목번호"))
            name = self._get_comm_data(trcode, rqname, i, "종목명")
            quantity = self._to_signed_int(self._get_comm_data(trcode, rqname, i, "보유수량"))
            avg_price = self._to_signed_int(self._get_comm_data(trcode, rqname, i, "매입가"))
            current_price = self._to_positive_int(self._get_comm_data(trcode, rqname, i, "현재가"))
            eval_amount = self._to_signed_int(self._get_comm_data(trcode, rqname, i, "평가금액"))
            profit_loss = self._to_signed_int(self._get_comm_data(trcode, rqname, i, "평가손익"))
            profit_rate = self._to_float(self._get_comm_data(trcode, rqname, i, "수익률(%)"))

            if code:
                positions.append(
                    {
                        "code": code,
                        "name": name,
                        "quantity": quantity,
                        "avg_price": avg_price,
                        "current_price": current_price,
                        "eval_amount": eval_amount,
                        "profit_loss": profit_loss,
                        "profit_rate": profit_rate,
                    }
                )

        return {
            "summary": summary,
            "positions": positions,
        }

    def _parse_unfilled_orders(self, trcode, rqname):
        count = self.ocx.dynamicCall(
            "GetRepeatCnt(QString, QString)",
            trcode,
            rqname,
        )

        orders = []

        for i in range(count):
            code = self._clean_code(self._get_comm_data(trcode, rqname, i, "종목코드"))
            name = self._get_comm_data(trcode, rqname, i, "종목명")
            kiwoom_order_no = self._get_comm_data(trcode, rqname, i, "주문번호")
            order_type = self._get_comm_data(trcode, rqname, i, "주문구분")
            order_price = self._to_positive_int(self._get_comm_data(trcode, rqname, i, "주문가격"))
            order_quantity = self._to_positive_int(self._get_comm_data(trcode, rqname, i, "주문수량"))
            unfilled_quantity = self._to_positive_int(self._get_comm_data(trcode, rqname, i, "미체결수량"))
            current_price = self._to_positive_int(self._get_comm_data(trcode, rqname, i, "현재가"))

            if code:
                orders.append(
                    {
                        "code": code,
                        "name": name,
                        "kiwoom_order_no": kiwoom_order_no,
                        "order_type": order_type,
                        "order_price": order_price,
                        "order_quantity": order_quantity,
                        "unfilled_quantity": unfilled_quantity,
                        "current_price": current_price,
                    }
                )

        return orders

    def _on_receive_chejan_data(self, gubun, item_cnt, fid_list):
        data = {
            "gubun": str(gubun),
            "item_cnt": str(item_cnt),
            "fid_list": str(fid_list),
            "주문번호": self._get_chejan_data(9203),
            "종목코드": self._clean_code(self._get_chejan_data(9001)),
            "종목명": self._get_chejan_data(302),
            "주문수량": self._to_positive_int(self._get_chejan_data(900)),
            "주문가격": self._to_positive_int(self._get_chejan_data(901)),
            "미체결수량": self._to_positive_int(self._get_chejan_data(902)),
            "주문구분": self._get_chejan_data(905),
            "주문체결시간": self._get_chejan_data(908),
            "체결가": self._to_positive_int(self._get_chejan_data(910)),
            "체결량": self._to_positive_int(self._get_chejan_data(911)),
        }

        self.last_chejan_data = data

        print("[Kiwoom] Chejan 수신")
        print(json.dumps(data, ensure_ascii=False, indent=2))

        if self.order_loop is not None:
            self.order_loop.exit()

    def _get_comm_data(self, trcode, rqname, index, item):
        value = self.ocx.dynamicCall(
            "GetCommData(QString, QString, int, QString)",
            trcode,
            rqname,
            index,
            item,
        )
        return str(value).strip()

    def _get_chejan_data(self, fid):
        value = self.ocx.dynamicCall("GetChejanData(int)", fid)
        return str(value).strip()

    def _clean_code(self, code):
        if code is None:
            return None
        return str(code).strip().replace("A", "")

    def _to_positive_int(self, value):
        number = self._to_signed_int(value)
        if number is None:
            return None
        return abs(number)

    def _to_signed_int(self, value):
        if value is None:
            return None

        text = str(value).strip()
        text = text.replace(",", "")
        text = text.replace("+", "")

        if text == "":
            return None

        try:
            return int(text)
        except ValueError:
            return None

    def _to_float(self, value):
        if value is None:
            return None

        text = str(value).strip()
        text = text.replace(",", "")
        text = text.replace("+", "")

        if text == "":
            return None

        try:
            return float(text)
        except ValueError:
            return None

    def _get_order_error_message(self, result_code):
        messages = {
            0: "정상",
            -10: "실패",
            -100: "사용자정보교환 실패",
            -101: "서버 접속 실패",
            -102: "버전처리 실패",
            -200: "시세조회 과부하",
            -201: "전문작성 초기화 실패",
            -300: "입력값 오류",
            -301: "계좌비밀번호 미등록 또는 입력 필요",
            -302: "타인계좌 사용 오류",
            -308: "주문전송 과부하",
        }

        return messages.get(result_code, f"알 수 없는 오류 코드: {result_code}")