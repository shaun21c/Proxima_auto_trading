import sys
from loguru import logger
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QAxContainer import QAxWidget


class KiwoomAPI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.realtime_data_scrnum = 5000
        self.using_condition_name = ""
        self.realtime_registered_codes = []
        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        # self._set_signal_slots()  # 키움증권 API의 내부 메서드 연결
        self._login()

    def _set_signal_slots(self):
        self.kiwoom.OnEventConnect.connect(self._event_connect)
        # self.kiwoom.OnReceiveRealData.connect(self._receive_realdata)
        # self.kiwoom.OnReceiveConditionVer.connect(self._receive_condition)
        # self.kiwoom.OnReceiveRealCondition.connect(self._receive_real_condition)
        # self.kiwoom.OnReceiveTrCondition.connect(self._receive_tr_condition)
    
    def _login(self):
        ret = self.kiwoom.dynamicCall("CommConnect()")
        if ret == 0:
            logger.info("로그인 성공")
        else:
            raise Exception("로그인 실패")
    
    def _event_connect(self, err_code):
        if err_code == 0:
            logger.info("이벤트 연결 성공")
        else:
            raise Exception(f"이벤트 연결 실패: {err_code}")
        
    def _after_login(self):
        logger.info("조건 검색 정보 요청")
        self.kiwoom.dynamicCall("GetConditionLoad()")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    kiwoom_api = KiwoomAPI()
    sys.exit(app.exec_())