import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton
from PyQt5.QtCore import QEventLoop
from PyQt5.QAxContainer import QAxWidget

class KiwoomAPI(QMainWindow):
    def __init__(self):
        super().__init__() # 부모 클래스 QMainWindow의 __init__ 메서드 호출
        self.account_num = 8093337911
        
        btn1 = QPushButton("시장가매수주문", self)
        btn1.clicked.connect(self.btn1_clicked)
        btn1.setFixedSize(200, 50)
        btn2 = QPushButton("시장가매도주문", self)
        btn2.move(200, 0)
        btn2.setFixedSize(200, 50)
        btn2.clicked.connect(self.btn2_clicked)
        btn3 = QPushButton("지정가매도주문", self)
        btn3.move(0, 50)
        btn3.setFixedSize(200, 50)
        btn3.clicked.connect(self.btn3_clicked)
        btn4 = QPushButton("지정가매수주문", self)
        btn4.move(200, 50)
        btn4.setFixedSize(200, 50)
        btn4.clicked.connect(self.btn4_clicked)

        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self._set_signal_slots()
        self.login_event_loop = QEventLoop()
        self.kiwoom.dynamicCall("CommConnect()")
        self.login_event_loop.exec_()

    def get_account_info(self):
        account_nums = str(self.kiwoom.dynamicCall("GetLoginInfo(QString)", ["ACCNO"].rstrip(';')))
        print(f"계좌번호 리스트: {account_nums}")
        self.account_num = account_nums.split(';')[0]
        print(f"사용 계좌 번호: {self.account_num}")

    def btn1_clicked(self):
        self.send_order(
            "시장가매수주문",    # 사용자 구분명
            "5000",             # 화면번호
            self.account_num,   # 계좌 번호
            1,                  # 주문유형, 1:신규매수, 2:신규매도, 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정
            "039490",           # 종목코드
            15,                 # 주문 수량
            "",                  # 주문 가격, 시장가의 경우 공백
            "03",               # 주문 유형, 00: 지정가, 03: 시장가, 05: 조건부지정가, 06: 최유리지정가, 07: 최우선지정가 등 (KOAStudio 참고)
            "",                 # 주문번호 (정정 주문의 경우 사용, 나머지는 공백)
        )

    def btn2_clicked(self):
        self.send_order(
            "시장가매도도주문",    # 사용자 구분명
            "5000",             # 화면번호
            self.account_num,   # 계좌 번호
            2,                  # 주문유형, 1:신규매수, 2:신규매도, 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정
            "039490",           # 종목코드
            15,                 # 주문 수량
            "",                  # 주문 가격, 시장가의 경우 공백
            "03",               # 주문 유형, 00: 지정가, 03: 시장가, 05: 조건부지정가, 06: 최유리지정가, 07: 최우선지정가 등 (KOAStudio 참고)
            "",                 # 주문번호 (정정 주문의 경우 사용, 나머지는 공백)
        )

    def btn3_clicked(self):
        self.send_order(
            "지정가매수주문",    # 사용자 구분명
            "5000",             # 화면번호
            self.account_num,   # 계좌 번호
            1,                  # 주문유형, 1:신규매수, 2:신규매도, 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정
            "039490",           # 종목코드
            15,                 # 주문 수량
            "130000",           # 주문 가격, 시장가의 경우 공백
            "00",               # 주문 유형, 00: 지정가, 03: 시장가, 05: 조건부지정가, 06: 최유리지정가, 07: 최우선지정가 등 (KOAStudio 참고)
            "",                 # 주문번호 (정정 주문의 경우 사용, 나머지는 공백)
        )

    def btn4_clicked(self):
        self.send_order(
            "지정가매도주문",    # 사용자 구분명
            "5000",             # 화면번호
            self.account_num,   # 계좌 번호
            2,                  # 주문유형, 1:신규매수, 2:신규매도, 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정
            "039490",           # 종목코드
            15,                 # 주문 수량
            "140000",           # 주문 가격, 시장가의 경우 공백
            "00",               # 주문 유형, 00: 지정가, 03: 시장가, 05: 조건부지정가, 06: 최유리지정가, 07: 최우선지정가 등 (KOAStudio 참고)
            ""                  # 주문번호 (정정 주문의 경우 사용, 나머지는 공백)
        )

    def _set_signal_slots(self):
        self.kiwoom.OnEventConnect.connect(self._event_connect)
        self.kiwoom.OnReceiveChejanData.connect(self._receive_chejandata)
        self.kiwoom.OnReceiveMsg.connect(self.receive_msg)

    def _event_connect(self, err_code):
        if err_code == 0:
            print("로그인 성공!")
        else:
            print("로그인 실패!")
        self.login_event_loop.exit()

    def send_order(self, sRQName, sScreenNo, sAccNo, nOrderType, sCode, nQty, nPrice, sHogaGb, sOrgOrderNo):
        print("Sending order")
        return self.kiwoom.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                                       [sRQName, sScreenNo, sAccNo, nOrderType, sCode, nQty, nPrice, sHogaGb, sOrgOrderNo])

    def receive_msg(self, sScrNo, sRQName, sTrCode, sMsg):
        print(f"Received MSG! 화면번호: {sScrNo}, 사용자 구분명: {sRQName}, TR이름: {sTrCode}, 메시지: {sMsg}")

    def get_chejandata(self, nFid):
        ret = self.kiwoom.dynamicCall("GetChejanData(int)", nFid)
        return ret
    
    def _receive_chejandata(self, sGubun, nItemCnt, sFidList):
        #sGubun: 체결구분 접수와 체결시 '0'값, 국내주식 잔고전달은 '1'값, 파생잔고 전달은 '4'
        if sGubun == "0":
            종목코드 = self.get_chejandata(9001).replace("A", "").strip()
            종목명 = self.get_chejandata(302).strip()
            주문체결시간 = self.get_chejandata(908).strip()
            주문수량 = 0 if len(self.get_chejandata(900)) == 0 else int(self.get_chejandata(900))
            주문가격 = 0 if len(self.get_chejandata(901)) == 0 else int(self.get_chejandata(901))
            체결수량 = 0 if len(self.get_chejandata(911)) == 0 else int(self.get_chejandata(911))
            체결가격 = 0 if len(self.get_chejandata(910)) == 0 else int(self.get_chejandata(910))
            미체결수량 = 0 if len(self.get_chejandata(902)) == 0 else int(self.get_chejandata(902))
            주문구분 = self.get_chejandata(905).replace("+", "").replace("-", "").stript()
            매매구분 = self.get_chejandata(906).strip()
            단위체결가 = 0 if len(self.get_chejandata(914)) == 0 else int(self.get_chejandata(914))
            단위체결량 = 0 if len(self.get_chejandata(915)) == 0 else int(self.get_chejandata(915))
            원주문번호 = self.get_chejandata(904).strip()
            주문번호 = self.get_chejandata(9203).strip()
            print(f"Received chejandata! 주문체결시간: {주문체결시간}, 종목코드: {종목코드}, "
                  f"종목명: {종목명}, 주문수량: {주문수량}, 주문가격: {주문가격}, 체결수량: {체결수량}, 체결가격: {체결가격}, "
                  f"주문구분: {주문구분}, 미체결수량: {미체결수량}, 매매구분: {매매구분}, 단위체결가: {단위체결가}, "
                  f"단위체결량: {단위체결량}, 주문번호: {주문번호}, 원주문번호: {원주문번호}")
        
        if sGubun == 1:
            print("잔고동보")

    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    kiwoom_api = KiwoomAPI()
    kiwoom_api.show()
    sys.exit(app.exec_())