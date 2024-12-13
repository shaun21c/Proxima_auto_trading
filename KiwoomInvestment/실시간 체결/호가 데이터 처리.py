import sys
from loguru import logger

from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QAxContainer import QAxWidget

class KiwoomAPI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.realtime_data_scrnum = 5000
        self.realtime_registered_codes = []

        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self._set_signal_slots()    # 키움증권 API와 내부 메소드를 연동
        self._login()

    def _set_signal_slots(self):
        self.kiwoom.OnEventConnect.connect(self._event_connect)
        self.kiwoom.OnReceiveRealData.connect(self._receive_realdata)

    def _login(self):
        ret = self.kiwoom.dynamicCall("CommConnect()")
        if ret == 0:
            print("로그인 창 열기 성공")

    def _event_connect(self, err_code):
        if err_code == 0:
            print("로그인 성공!")
            self._after_login()
        else:
            raise Exception("로그인 실패!")
        
    def _after_login(self):
        print("실시간 등록 요청")
        self.register_code_to_realtime_list("039490")
        self.register_code_to_realtime_list("005930")
        self.register_code_to_realtime_list("068270")

    def set_real(self, scrNum, strCodeList, strFidList, strRealType):
        self.kiwoom.dynamicCall("SetRealReg(QString, QString, QString, QString)", scrNum, strCodeList, strFidList, strRealType)
    
    def register_code_to_realtime_list(self, code):
        fid_list = "10;12;20;41;51;61;71"
        if len(code) != 0:
            self.set_real(self._get_realtime_data_screen_num(), code, fid_list, "1")
            print(f"{code}, 실시간 등록 완료")
            self.realtime_registered_codes.append(code)

    def _get_realtime_data_screen_num(self):
        self.realtime_data_scrnum += 1
        if self.realtime_data_scrnum > 5150:
            self.realtime_data_scrnum = 5000
        return str(self.realtime_data_scrnum)
    
    def _get_comm_realdata(self, strCode, nFid):
        return self.kiwoom.dynamicCall("GetCommRealData(Qstring, int)", strCode, nFid)
    
    def _receive_realdata(self, sJongmokCode, sRealType, sRealData):
        if sRealType == "주식체결":
            현재가 = int(self._get_comm_realdata(sRealType, 10).replace('-', ''))   # 현재가
            등락률 = float(self._get_comm_realdata(sRealType, 12))
            체결시간 = self._get_comm_realdata(sRealType, 20)
            print(f"종목코드: {sJongmokCode}, 체결시간: {체결시간}, 현재가: {현재가}, 등락률: {등락률} ")
        elif sRealType == "주식호가잔량":
            시간 = self._get_comm_realdata(sRealType, 20)
            매도호가1 = int(self._get_comm_realdata(sRealType, 41).replace('-', ''))
            매수호가1 = int(self._get_comm_realdata(sRealType, 51).replace('-', ''))
            매수호가잔량1 = int(self._get_comm_realdata(sRealType, 61).replace('-', ''))
            매도호가잔량1 = int(self._get_comm_realdata(sRealType, 71).replace('-', ''))
            print(
                f"종목코드: {sJongmokCode}, 시간: {시간}, 매도호가1: {매도호가1}, 매수호가1: {매수호가1}, "
                f"매도호가잔량1: {매도호가잔량1}, 매수호가잔량1: {매수호가잔량1}"
            )


if __name__ == '__main__':
    app = QApplication(sys.argv)
    kiwoom_api = KiwoomAPI()
    sys.exit(app.exec_())