import sys
import datetime
from collections import deque
from loguru import logger
from queue import Queue

from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton
from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QTimer

class KiwoomAPI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.show()  # UI를 보여줍니다 (빈 화면)
        self.now_time: datetime.datetime = datetime.datetime.now()
        self.tr_req_scrnum: int = 5150  # 화면번호
        self.max_send_per_sec: int = 4  # 초당 TR 호출 최대 4번
        self.max_send_per_minute: int = 55 # 분당 TR 호출 최대 55번
        self.max_send_per_hour: int = 950  # 시간당 TR 호출 최대 950번
        self.last_tr_send_times: deque = deque(maxlen = self.max_send_per_hour)
        self.tr_req_queue: Queue = Queue()

        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self._set_signal_slots()    # 키움증권 API와 내부 메소드를 연동
        self.account_num = None

        self._login()

        self.req_opt10019_timer = QTimer()
        self.req_opt10019_timer.timeout.connect(self.get_tmp_high_volatility_info)
        self.tr_req_check_timer = QTimer()
        self.tr_req_check_timer.timeout.connect(self._send_tr_request)
        self.tr_req_check_timer.start(100)  # 0.1초마다 한번 Execute


    def _send_tr_request(self):
        self.now_time = datetime.datetime.now()
        if self._is_check_tr_req_condition() and not self.tr_req_queue.empty():
            request_func, *func_args = self.tr_req_queue.get()
            logger.info(f"Executing TR request function: {request_func}")
            request_func(*func_args) if func_args else request_func()
            self.last_tr_send_times.append(self.now_time)

    def _set_signal_slots(self):
        self.kiwoom.OnEventConnect.connect(self._event_connect)
        self.kiwoom.OnReceiveTrData.connect(self._receive_tr_data)


    def _login(self):
        ret = self.kiwoom.dynamicCall("CommConnect()")
        if ret == 0:
            logger.info("로그인 창 열기 성공!")
    
    def _event_connect(self, err_code):
        if err_code == 0:
            logger.info("로그인 성공!")
            self._after_login() # 현재 계좌 정보 요청
        else:
            raise Exception("로그인 실패!")
    
    def _after_login(self):
        self.get_account_num()
        self.req_opt10019_timer.start(200)  # 0.2초마다 한번 Execute


    def _set_input_value(self, id, value):
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", id, value)

    def _comm_rq_data(self, rqname, trcode, next, screen_no):
        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen_no)

    def _comm_get_data(self, code, real_type, field_name, index, item_name):
        ret = self.kiwoom.dynamicCall("CommGetData(QString, QString, QString, int, QString)", code, real_type, field_name, index, item_name)
        return ret

    def _get_repeat_cnt(self, trcode, rqname):
        ret = self.kiwoom.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        return ret


    def _on_opt10019_req(self, rqname, trcode):
        data_cnt = self._get_repeat_cnt(trcode, rqname)
        for i in range(data_cnt):
            종목코드 = self._comm_get_data(trcode, "", rqname, i, "종목코드")
            종목분류 = self._comm_get_data(trcode, "", rqname, i, "종목분류")
            종목명 = self._comm_get_data(trcode, "", rqname, i, "종목명")
            전일대비기호 = self._comm_get_data(trcode, "", rqname, i, "전일대비기호")
            전일대비 = self._comm_get_data(trcode, "", rqname, i, "전일대비")
            등락률 = self._comm_get_data(trcode, "", rqname, i, "등락률")
            기준가 = self._comm_get_data(trcode, "", rqname, i, "기준가")
            현재가 = self._comm_get_data(trcode, "", rqname, i, "현재가")
            기준대비 = self._comm_get_data(trcode, "", rqname, i, "기준대비")
            거래량 = self._comm_get_data(trcode, "", rqname, i, "거래량")
            급등률 = self._comm_get_data(trcode, "", rqname, i, "급등률")
            logger.info(f"종목코드: {종목코드}, 종목분류: {종목분류}, 종목명: {종목명}")


    def _receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        logger.info(f"Received TR data, rqname: {rqname}")
        if rqname == "opw00018_req":
            self._on_opw00018_req(rqname, trcode)
        elif rqname == "opt10019_req":
            self._on_opt10019_req(rqname, trcode)


    def request_opt10019(self, target_market = "000", is_upside = True):
        self._set_input_value("시장구분", target_market)    # KOSPI, KOSDAQ, 전체
        self._set_input_value("등락구분", "1" if is_upside else "2")    # 급등 기준
        self._set_input_value("시간구분", "1")    # 1분전
        self._set_input_value("시간", "분")    # 분
        self._set_input_value("거래량구분", "1" "00100")    # 10만주
        self._set_input_value("종목조건", "0")    # 전체조회
        self._set_input_value("신용조건", "0")    # 전체조회
        self._set_input_value("가격조건", "0")    # 전체조회
        self._set_input_value("상하한포함", "0")    # 미포함
        self._comm_rq_data("opt10019_req", "opt10019", 0, self._get_tr_req_screen_num())
        

    def request_opw00018(self):
        self._set_input_value("계좌번호", self.account_num)
        self._set_input_value("비밀번호", "")
        self._set_input_value("비밀번호입력매체구분", "00")
        self._comm_rq_data("opw00018_req", "opw00018", 0, self._get_tr_req_screen_num())


    def _on_opw00018_req(self, rqname, trcode):
        현재평가잔고 = int(self._comm_get_data(trcode, "", rqname, 0, "추정예탁자산"))
        총수익률 = float(self._comm_get_data(trcode, "", rqname, 0, "총수익률(%)"))
        총평가손익금액 = int(self._comm_get_data(trcode, "", rqname, 0, "총평가손익금액"))
        logger.info(f"현재평가잔고: {현재평가잔고}, 총수익률: {총수익률}, 총평가손익금액: {총평가손익금액}")
        data_cnt = self._get_repeat_cnt(trcode, rqname)
        for i in range(data_cnt):
            종목코드 = self._comm_get_data(trcode, "", rqname, i, "종목번호").replace("A", "").strip()
            매매가능수량 = int(self._comm_get_data(trcode, "", rqname, i, "매매가능수량"))
            보유수량 = int(self._comm_get_data(trcode, "", rqname, i, "보유수량"))
            매입가 = int(self._comm_get_data(trcode, "", rqname, i, "매입가"))
            수익률 = float(self._comm_get_data(trcode, "", rqname, i, "수익률(%)"))
            logger.info(f"종목코드: {종목코드}, 보유수량: {보유수량}, 매입가: {매입가}, 수익률: {수익률}")


    def _is_check_tr_req_condition(self):
        self.now_time = datetime.datetime.now()
        if len(self.last_tr_send_times) >= self.max_send_per_sec and \
            self.now_time - self.last_tr_send_times[-self.max_send_per_sec] < datetime.timedelta(milliseconds = 1000):
            logger.info(f"초 단위 TR 요청 제한! Wait for time to send!")
            return False
        elif len(self.last_tr_send_times) >= self.max_send_per_minute and \
            self.now_time - self.last_tr_send_times[-self.max_send_per_minute] < datetime.timedelta(minutes = 1):
            logger.info(f"분 단위 TR 요청 제한! Wait for time to send!")
            return False
        elif len(self.last_tr_send_times) >= self.max_send_per_hour and \
            self.now_time - self.last_tr_send_times[-self.max_send_per_hour] < datetime.timedelta(minutes = 60):
            logger.info(f"시간 단위 TR 요청 제한! Wait for time to send!")
            return False
        else:
            return True

    def _get_tr_req_screen_num(self):
        self.tr_req_scrnum += 1
        if self.tr_req_scrnum > 5200:
            self.tr_req_scrnum = 5150
        return str(self.tr_req_scrnum)
    
    def get_account_num(self):
        account_nums = str(self.kiwoom.dynamicCall("GetLoginInfo(QString)", ["ACCNO"]).rstrip(';'))
        logger.info(f"계좌번호 리스트: {account_nums}")
        self.account_num = account_nums.split(';')[0]
        logger.info(f"사용 계좌 번호: {self.account_num}")






    def get_tmp_high_volatility_info(self):
        self.tr_req_queue([self.request_opw10019, "001", True])

if __name__ == '__main__':
    app = QApplication(sys.argv)
    kiwoom_api = KiwoomAPI()
    sys.exit(app.exec_())