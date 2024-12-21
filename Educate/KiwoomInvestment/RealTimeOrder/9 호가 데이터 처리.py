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

    # 키움증권 API와 내부 메소드를 연동
    def _set_signal_slots(self):
        self.kiwoom.OnEventConnect.connect(self._event_connect)
        self.kiwoom.OnReceiveRealData.connect(self._receive_realdata)

    # 로그인
    def _login(self):
        ret = self.kiwoom.dynamicCall("CommConnect()")
        if ret == 0:
            print("로그인 창 열기 성공")

    # 로그인 결과 수신 이벤트
    def _event_connect(self, err_code):
        if err_code == 0:
            print("로그인 성공!")
            self._after_login()
        else:
            raise Exception("로그인 실패!")
    
    # 로그인 성공 후 실행할 코드
    def _after_login(self):
        print("실시간 등록 요청")
        self.register_code_to_realtime_list("039490") # 제일약품, 5001
        self.register_code_to_realtime_list("005930") # 삼성전자, 5002
        self.register_code_to_realtime_list("068270") # 셀트리온, 5003

    # 실시간 등록, SetRealReg 함수 호출
    def set_real(self, scrNum, strCodeList, strFidList, strRealType):
        self.kiwoom.dynamicCall("SetRealReg(QString, QString, QString, QString)", scrNum, strCodeList, strFidList, strRealType)
    
    # 실시간 등록, 10현재가, 12등락률, 20체결시간, 41매도호가1, 51매수호가1, 61매수호가잔량1, 71매도호가잔량1
    def register_code_to_realtime_list(self, code):
        # 굳이 fid_list를 이렇게 지정하지 않은 리스트도 쓸 수 있다. 
        fid_list = "10;12;20;41;51;61;71"
        if len(code) != 0:
            # 등록마다 화면번호가 최대 200개까지 등록 가능하므로 매번 변경하여 등록
            self.set_real(self._get_realtime_data_screen_num(), code, fid_list, "1")
            print(f"{code}, 실시간 등록 완료")
            self.realtime_registered_codes.append(code)

    def _get_realtime_data_screen_num(self):
        self.realtime_data_scrnum += 1
        if self.realtime_data_scrnum > 5150:
            self.realtime_data_scrnum = 5000
        return str(self.realtime_data_scrnum)
    
    def _get_comm_realdata(self, strCode, nFid):
        """GetCommRealData 함수 호출, 현재가, 등락률, 체결시간 등을 얻기 위해 사용"""
        return self.kiwoom.dynamicCall("GetCommRealData(Qstring, int)", strCode, nFid)
    
    def _receive_realdata(self, sJongmokCode, sRealType, sRealData):
        if sRealType == "주식체결":
            현재가 = int(self._get_comm_realdata(sRealType, 10).replace('-', ''))   # 현재가
            등락률 = float(self._get_comm_realdata(sRealType, 12))
            체결시간 = self._get_comm_realdata(sRealType, 20)
            print(f"종목코드: {sJongmokCode}, 체결시간: {체결시간}, 현재가: {현재가}, 등락률: {등락률} ")
        elif sRealType == "주식호가잔량":
            # fid_list에 등록하지 않은 fid도 가져올 수 있음
            시간 = self._get_comm_realdata(sRealType, 21)
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