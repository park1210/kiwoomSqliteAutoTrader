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
        accounts = [acc for acc in raw.split(";") if acc]
        return accounts

    def get_server_gubun(self):
        """
        일반적으로 모의투자 서버는 '1'로 구분된다.
        실전 서버는 빈 문자열 또는 다른 값으로 올 수 있다.
        """
        return self.get_login_info("GetServerGubun")

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

        current_price = self._to_positive_int(raw_current_price)
        volume = self._to_positive_int(raw_volume)

        return {
            "code": code,
            "name": name,
            "current_price": current_price,
            "volume": volume,
            "raw_current_price": raw_current_price,
            "raw_volume": raw_volume,
        }

    def send_market_buy_order(self, account_no, code, quantity):
        """
        시장가 매수 주문.
        order_type=1: 신규매수
        hoga_gb='03': 시장가
        price=0
        """
        return self.send_order(
            rqname="v3_시장가매수",
            screen_no="2000",
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
                "message": f"SendOrder 호출 실패: result={result}",
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
            current_price = self.ocx.dynamicCall(
                "GetCommData(QString, QString, int, QString)",
                trcode,
                rqname,
                0,
                "현재가",
            ).strip()

            volume = self.ocx.dynamicCall(
                "GetCommData(QString, QString, int, QString)",
                trcode,
                rqname,
                0,
                "거래량",
            ).strip()

            self.tr_data = {
                "현재가": current_price,
                "거래량": volume,
            }

        if self.tr_loop is not None:
            self.tr_loop.exit()

    def _on_receive_chejan_data(self, gubun, item_cnt, fid_list):
        """
        주문/체결 이벤트 수신.

        주요 FID:
        9203 주문번호
        9001 종목코드
        302  종목명
        900  주문수량
        901  주문가격
        902  미체결수량
        905  주문구분
        908  주문/체결시간
        910  체결가
        911  체결량
        """
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

    def _get_chejan_data(self, fid):
        value = self.ocx.dynamicCall("GetChejanData(int)", fid)
        return str(value).strip()

    def _clean_code(self, code):
        if code is None:
            return None
        return str(code).strip().replace("A", "")

    def _to_positive_int(self, value):
        if value is None:
            return None

        text = str(value).strip()
        text = text.replace(",", "")
        text = text.replace("+", "")
        text = text.replace("-", "")

        if text == "":
            return None

        try:
            return int(text)
        except ValueError:
            return None