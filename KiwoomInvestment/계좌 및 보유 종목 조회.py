import sys
import datetime
import pandas as pd
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton
from PyQt5.Qtcore import QEventLoop
from PyQt5.QAxContainer import QAxWidget

class KiwoomAPI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.daily_data_df: pd.DatFrame = pd.DataFrame(columns = ['시간', '시가', '고가', '저가', '종가', '거래량'])
        self.account_num = None
        
        btn1 = QPushButton("일봉데이터 print", self)
        btn1.move(190, 10)
        btn1.resize(200, 100)
        btn1.clicked.connect(self.btn1_clicked)

        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self._set_signal_slots()
        self.login_event_loop = QEventLoop()
        self.kiwoom.dynamicCall("CommConnect()")
        self.login_event_loop.exec_()

        
        self.request_opt10081("039490", date = datetime.datetime.now().strftime("%Y%m%d"))
        self.get_account_balance()
        

    def get_account_info(self):
        account_nums = str(self.kiwoom.dynamicCall("GetLoginInfo(QString)", ["ACCNO"].rstrip(';')))
        print(f"계좌번호 리스트: {account_nums}")
        self.account_num = account_nums.split(';')[0]
        print(f"사용 계좌 번호: {self.account_num}")


    def get_account_balance(self):
        self.set_input_value("계좌번호", self.account_num)
        self.set_input_value("비밀번호", "")
        self.set_input_value("계좌번호", "00")
        self.set_input_value("계좌번호", "2")
        self.comm_rq_data("opw00018_req", "opw00018", 0, "5000")




    def btn1_clicked(self):
        print(self.daily_data_df)

    def _set_signal_slots(self):
        self.kiwoom.OnEventConnect.connect(self._event_connect)
        self.kiwoom.OnReceiveTrData.connect(self._receive_tr_data)



    def _event_connect(self, err_code):
        if err_code == 0:
            print("로그인 성공!")
        else:
            print("로그린 실패!")
        self.login_event_loop.exit()



    def request_remained_data(self):
        if self.is_remained_data:
            print("연속 조회 실행!")
            self.request_opt10081("039490", date = datetime.datetime.now().strftime("%T%m%d"))

        

    def comm_rq_data(self, rqname, trcode, next, screen_no):
        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen_no)


    def set_input_value(self, id, value):
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", id, value)

    def request_opt10081(self, code, date = datetime.datetime.now().strftime('%Y%m%d')):
        self.set_input_value("종목코드", code)
        self.set_input_value("기준일자", date)
        self.set_input_value("수정주가구분", 1) # 수정주가 사용
        self.comm_rq_data("opt10081_req", "opt10081", 2 if self.is_remained_data else 0, "5000")


    def _receive_tr_data(self, screen_no, rqname, trcode, recode_name, next, unused1, unused2, unused3, unused4):
        self.is_remained_data = next == '2'
        print(next)
        if rqname == "opt10081_req":
            self._on_opt10081_req(rqname, trcode)

    def _comm_get_data(self, code, real_type, field_name, index, item_name):
        ret = self.kiwoom.dynamicCall("CommGetData(QString, QString, QString, int, QString)", code, real_type, field_name, index, item_name)
        return ret
    
    def _get_repeat_cnt(self, trcode, rqname):
        ret = self.kiwoom.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        return ret
    
    def _on_opt10081_req(self, rqname, trcode):
        data_cnt = self._get_repeat_cnt(trcode, trcode)
        for i in range(data_cnt):
            date = self._comm_get_data(trcode, "", rqname, i, "일자")
            open = self._comm_get_data(trcode, "", rqname, i, "시가")
            high = self._comm_get_data(trcode, "", rqname, i, "고사")
            low = self._comm_get_data(trcode, "", rqname, i, "저가")
            close = self._comm_get_data(trcode, "", rqname, i, "현재가")
            volume = self._comm_get_data(trcode, "", rqname, i, "거래량")
            self.daily_data_df.loc[len(self.daily_data_df)]=  {
                '시간':date,
                '시가':int(open),
                '고가':int(high),
                '저가':int(low),
                '종가':int(close),
                '거래량':int(volume),
            }


    def _on_opw00018_req(self, rqname, trcode):
        현재평가잔고 = int(self._comm_get_data(trcode, "", rqname, 0, "추정예탁자산"))
        print(f"현재평가잔고: {현재평가잔고}")
        data_cnt = self._get_repeat_cnt(trcode, rqname)
        for i in range(date_cnt):
            종목코드 = self._comm_get_data(trcode, "", rqname, i, "종목번호").replace("A", "").strip()
            매매가능수량 = int(self._comm_get_data(trcode, "", rqname, i, "매매가능수량"))
            보유수량 = int(self._comm_get_data(trcode, "", rqname, i, "보유수량"))
            매입가 = int(self._comm_get_data(trcode, "", rqname, i, "매입가"))
            수익률 = int(self._comm_get_data(trcode, "", rqname, i, "수익률(%)"))
            print(종목코드, 매매가능수량, 보유수량, 매입가, 수익률)

            

if __name__ == '__main__':
    app = QApplication(sys.argv)
    kiwoom_api = KiwoomAPI()
    kiwoom_api.show()
    sys.exit(app.exec_())