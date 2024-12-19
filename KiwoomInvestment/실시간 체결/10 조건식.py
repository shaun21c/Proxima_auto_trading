import sys

from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QAxContainer import QAxWidget

class KiwoomAPI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.realtime_data_scrnum = 5000
        self.using_condition_name = "조건식샘플"
        self.realtime_registered_codes = []

        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self._set_signal_slots()    # 키움증권 API와 내부 메소드를 연동
        self._login()

    def _set_signal_slots(self):
        self.kiwoom.OnEventConnect.connect(self._event_connect) # 로그인 결과 수신 이벤트
        self.kiwoom.OnReceiveRealData.connect(self._receive_realdata) # 실시간 데이터 수신 이벤트
        self.kiwoom.OnReceiveConditionVer.connect(self._receive_condition) # 조건식 수신 이벤트
        self.kiwoom.OnReceiveRealCondition.connect(self._receive_real_condition) # 실시간 조건검색 이벤트
        self.kiwoom.OnReceiveTrCondition.connect(self._receive_tr_condition) # 실시간 아닌 조건검색 이벤트

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
        """ 로그인 성공 후 실행할 코드 """
        print("조건 검색 정보 요청")
        self.kiwoom.dynamicCall("GetConditionLoad()")   # 조건 검색 정보 요청


    def _set_input_value(self, id, value):
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", id, value)

    def _comm_rq_data(self, rqname, trcode, next, screen_no):
        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen_no)

    def _comm_get_data(self, code, real_type, field_name, index, item_name):
        ret = self.kiwoom.dynamicCall(
            "CommGetData(QString, QString, QString, int, QString)", code, real_type, field_name, index, item_name

        )
        return ret.strip()
    
    def _receive_real_condition(self, strCode, strType, strConditionName, strConditionIndex):
        # strType: 이벤트 종류, "I": 종목편입, "D", 종목이탈
        # strConditionName: 조건식 이름
        # strConditionIndex: 조건명 인덱스
        print(f"Received real condition, {strCode}, {strType}, {strConditionName}, {strConditionIndex}")
        if strType == "I" and strCode not in self.realtime_registered_codes:
            self.register_code_to_realtime_List(strCode)

    def _receive_tr_condition(self, scrNum, strCodeList, strConditionName, nIndex, nNext) -> None:
        """조건검색 결과 수신 이벤트"""
        print(f"Received TR Condition, strCodeList: {strCodeList}, strConditionName: {strConditionName}, "
              f"nIndex: {nIndex}, nNext: {nNext}, scrNum: {scrNum}")
        for stock_code in strCodeList.split(';'):
            if len(stock_code) == 6:
                self. register_code_to_realtime_list(stock_code)

    def _get_realtime_data_screen_num(self):
        self.realtime_data_scrnum += 1
        if self.realtime_data_scrnum > 5150:
            self.realtime_data_scrnum = 5000
        return str(self.realtime_data_scrnum)
    

    def _receive_condition(self):
        condition_info = self.kiwoom.dynamicCall("GetConditionNameList()").split(';')
        for condition_name_idx_str in condition_info:
            if len(condition_name_idx_str) == 0:
                continue
            condition_idx, condition_name = condition_name_idx_str.split('^')
            if condition_name == self.using_condition_name:
                self.send_condition(self._get_realtime_data_screen_num(), condition_name, condition_idx, 1)

    def send_condition(self, scrNum, condition_name, nidx, nsearch):
        # nSearch: 조회구분, 0: 조건검색, 1: 조건검색 + 실시간 조건검색
        result = self.kiwoom.dynamicCall("SendCondition(QString, QString, int, int)", scrNum, condition_name, nidx, nsearch)
        if result == 1:
            print(f"{condition_name} 조건검색 등록")

    def set_real(self, scrNum, strCodeList, strFidList, strRealType):
        self.kiwoom.dynamicCall("SetRealReg(QString, QString, QString, QString, QString)", scrNum, strCodeList, strFidList, strRealType)

    def register_code_to_realtime_List(self, code):
        fid_list = "10;12;20;41;51;61;71"
        if len(code) != 0:
            self.set_real(self._get_realtime_data_screen_num(), code, fid_list, '1')
            print(f"{code}, 실시간 등록 완료!")
            self.realtime_registered_codes.append(code)

    def _get_comm_realdata(self, strCode, nFid):
        return self.kiwoom.dynamicCall("GetCommRealData(OString, int)", strCode, nFid)
    
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
            매도호가잔량1 = int(self._get_comm_realdata(sRealType, 61).replace('-', ''))
            매수호가잔량1 = int(self._get_comm_realdata(sRealType, 71).replace('-', ''))
            print(
                f"종목코드: {sJongmokCode}, 시간: {시간}, 매도호가1: {매도호가1}, 매수호가1: {매수호가1}, "
                f"매도호가잔량1: {매도호가잔량1}, 매수호가잔량: {매수호가잔량1}"
            )


if __name__ == '__main__':
    app = QApplication(sys.argv)
    kiwoom_api = KiwoomAPI()
    sys.exit(app.exec_())