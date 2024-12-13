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
        btn1 = QPushButton("일봉데이터 print", self)
        btn1.resize(200, 100)
        btn1.clicked.connect(self.btn1_clicked)
        self.show()
        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self._set_signal_slots()
        self.login_event_loop = QEventLoop()
        self.kiwoom.dynamicCall("CommConnect()")
        self.login_event_loop.exec_()
        self.request_opt10081("039490", date = datetime.datetime.now().strftime('%Y%m%d'))


    def btn1_clicked(self):
        print(self.daily_data_df)

    def _set_signal_slots(self):
        self.kiwoom.OnEventConnect.connect(self._event_connect)
        self.kiwoom.OnReceiveTrData.connect(self._receive_tr_data)



    def event_connect(self, err_code):
        if err_code == 0:
            print("로그인 성공!")
        else:
            print("로그린 실패!")
        self.login_event_loop.exit()


    def comm_rq_data(self, rqname, trcode, next, screen_no):
        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen_no)


    def set_input_value(self, id, value):
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", id, value)

    def request_opt10081(self, code, date = datetime.datetime.now().strftime('%Y%m%d')):
        self.set_input_value("종목코드", code)
        self.set_input_value("기준일자", date)
        self.set_input_value("수정주가구분", 1) # 수정주가 사용
        self.comm_rq_data("opt10081_req", "opt10081", 0, "5000")


    def _receive_tr_data(self, screen_no, rqname, trcode, recode_name, next, unused1, unused2, unused3, unused4):
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
            self.daily_data_df.loc[i]=  {
                '시간':date,
                '시가':int(open),
                '고가':int(high),
                '저가':int(low),
                '종가':int(close),
                '거래량':int(volume),
            }


if __name__ == '__main__':
    app = QApplication(sys.argv)
    kiwoom_api = KiwoomAPI()
    kiwoom_api.show()
    sys.exit(app.exec_())