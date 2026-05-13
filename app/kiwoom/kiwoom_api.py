from PyQt5.QtCore import QEventLoop
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
        self.tr_data = {}

        self.ocx.OnEventConnect.connect(self._on_event_connect)
        self.ocx.OnReceiveTrData.connect(self._on_receive_tr_data)

    def login(self):
        """
        키움 OpenAPI+ 로그인 창을 띄운다.
        로그인 완료 전까지 이벤트 루프에서 대기한다.
        """
        self.login_loop = QEventLoop()

        result = self.ocx.dynamicCall("CommConnect()")

        if result != 0:
            raise RuntimeError(f"CommConnect 호출 실패: result={result}")

        self.login_loop.exec_()

    def _on_event_connect(self, err_code):
        """
        로그인 결과 이벤트.
        err_code == 0이면 성공.
        """
        if err_code == 0:
            print("[Kiwoom] 로그인 성공")
        else:
            print(f"[Kiwoom] 로그인 실패: err_code={err_code}")

        if self.login_loop is not None:
            self.login_loop.exit()

    def get_stock_name(self, code):
        """
        종목코드로 종목명 조회.
        예: 005930 -> 삼성전자
        """
        name = self.ocx.dynamicCall("GetMasterCodeName(QString)", code)
        return str(name).strip()

    def get_current_price(self, code):
        """
        opt10001: 주식기본정보요청

        반환 예시:
        {
            "code": "005930",
            "name": "삼성전자",
            "current_price": 73600,
            "volume": 12345678,
            "raw_current_price": "+73600",
            "raw_volume": "12345678"
        }
        """
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
        """
        TR 데이터 수신 이벤트.
        """
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

    def _to_positive_int(self, value):
        """
        키움 데이터는 +73600, -73600, 73,600 같은 문자열로 올 수 있다.
        현재가와 거래량 저장용으로 부호와 콤마를 제거한다.
        """
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